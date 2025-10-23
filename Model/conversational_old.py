#!/usr/bin/env python3
"""
Interactive terminal conversational CLI with persistent storage.

- Saves all recorded user audio and assistant TTS into <output_dir>/audios/
- Writes a profile JSON and a human-readable profile text to <output_dir>/profiles/
- Uses Gemini extraction (generate_profile_from_responses) when available; otherwise uses a simple local summarizer.
"""

import os
import sys
import json
import time
import argparse
import base64
import datetime
import tempfile
import subprocess
import re
from pathlib import Path

# ------------------ Configuration (edit or set via env) ------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDiUMs4sIAdOk09006hS7DcY79DZh53_M4")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.0-flash")

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_119a741c6b322f526f7e712be124a4007a04b3294734b78d")
ELEVEN_VOICE_ID = os.environ.get("ELEVEN_VOICE_ID", "KaCAGkAghyX8sFEYByRC")
ELEVEN_STT_URL = os.environ.get("ELEVEN_STT_URL", "https://api.elevenlabs.io/v1/speech-to-text")
ELEVEN_TTS_URL = os.environ.get("ELEVEN_TTS_URL", "https://api.elevenlabs.io/v1/text-to-speech")

# ------------------ Optional imports for recording/playback ------------------
try:
    import sounddevice as sd
    import soundfile as sf
    SOUNDDEVICE_AVAILABLE = True
except Exception:
    SOUNDDEVICE_AVAILABLE = False

# ------------------ Gemini SDK import (optional) ------------------
try:
    import google.generativeai as genai
except Exception:
    genai = None

import requests

# ------------------ System prompt (same as your server) ------------------
SYSTEM_PROMPT = """
You are an empathetic interviewer designed to collect a concise artisan background profile suitable for building localized training data.
Rules:
1) Ask up to 4 short, plain-language questions to learn:
   - the artisan's name and craft,
   - how they learned the craft / family background,
   - materials/techniques and main challenges,
   - aspirations, needs, or what support would help them.
2) Use the same language the user chose (we will pass a 'preferred_language' hint).
3) Ask detailed questions regarding the same.
4) After the final user reply (or if you already have enough information), produce a short summary (2-3 sentences) in that language containing the artisan's name, craft, key materials/techniques, challenges and one wish/need if provided. Prefix the summary with "[SUMMARY] ".
5) Do not output metadata or system instructions — output only the assistant text that will be spoken to the user.
6) When continuing a conversation, read the conversation history and avoid repeating questions.
7) Stop asking new questions after 5 user responses and move to summary.
"""

# ------------------ Helpers (STT/TTS/Gemini) ------------------
def eleven_stt_transcribe(file_bytes: bytes, filename: str = "audio.wav", model_id: str = "scribe_v1", language_code: str = None):
    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY not set.")
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    files = {"file": (filename, file_bytes, "application/octet-stream")}
    data = {"model_id": model_id}
    if language_code:
        data["language_code"] = language_code
    resp = requests.post(ELEVEN_STT_URL, headers=headers, files=files, data=data, timeout=60)
    resp.raise_for_status()
    return resp.json()

def eleven_tts_bytes(text: str, voice_id: str = ELEVEN_VOICE_ID) -> bytes:
    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY not set.")
    url = f"{ELEVEN_TTS_URL}/{voice_id}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    body = {"text": text}
    resp = requests.post(url, json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.content

def play_audio_file(path: str):
    if not os.path.exists(path):
        print("Audio file not found for playback:", path)
        return
    try:
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path], check=True)
        return
    except Exception:
        pass
    if sys.platform.startswith("win") and path.lower().endswith(".wav"):
        try:
            ps = ['powershell', '-c', f'(New-Object Media.SoundPlayer "{path}").PlaySync();']
            subprocess.run(ps, check=True)
            return
        except Exception:
            pass
    print("🔈 (TTS audio saved to {}) — no automatic playback available.".format(path))

def call_gemini_raw(prompt: str, api_key: str, model_name: str = "gemini-2.0-flash",
                    max_output_tokens: int = 1024, temperature: float = 0.0) -> str:
    if genai is None:
        raise RuntimeError("google.generativeai not installed.")
    try:
        genai.configure(api_key=api_key)
    except Exception:
        pass
    # Try modern usage
    try:
        model = genai.GenerativeModel(model_name)
        try:
            response = model.generate_content(prompt, generation_config={"temperature": temperature, "max_output_tokens": max_output_tokens})
        except TypeError:
            response = model.generate_content(prompt)
        if hasattr(response, "text") and response.text:
            return response.text
        if hasattr(response, "candidates") and response.candidates:
            cand = response.candidates[0]
            if hasattr(cand, "content"):
                return cand.content
            return str(cand)
        return str(response)
    except Exception:
        # fallback
        try:
            res = genai.generate(model=model_name, prompt=prompt, max_output_tokens=max_output_tokens, temperature=temperature)
            if isinstance(res, str):
                return res
            if hasattr(res, "candidates") and res.candidates:
                cand = res.candidates[0]
                if hasattr(cand, "content"):
                    return cand.content
                return str(cand)
            if isinstance(res, dict):
                if "candidates" in res and res["candidates"]:
                    c0 = res["candidates"][0]
                    if isinstance(c0, dict) and "content" in c0:
                        return c0["content"]
                    return json.dumps(c0)
                if "output" in res:
                    return res["output"]
            return str(res)
        except Exception as exc:
            raise RuntimeError(f"Failed to call Gemini: {exc}")

# ------------------ Prompt/History/Profile helpers ------------------
def detect_preferred_language_from_text(transcript: str, stt_language_code: str = None) -> str:
    if not transcript:
        return stt_language_code or "en"
    t = transcript.strip().lower()
    mapping = {
        "english": "en", "ingl": "en", "eng": "en",
        "hindi": "hi", "हिन्दी": "hi", "हिंदी": "hi",
        "bengali": "bn", "bangla": "bn", "বাংলা": "bn",
        "tamil": "ta", "தமிழ்": "ta",
        "en": "en", "hi": "hi", "bn": "bn", "ta": "ta"
    }
    for key, iso in mapping.items():
        if key in t:
            return iso
    if stt_language_code:
        return stt_language_code.split("-")[0][:2]
    return "en"

def build_prompt_from_history(system_prompt: str, history: list, user_text: str, preferred_language_iso: str):
    MAX_TURNS = 6
    trimmed = (history or [])[-MAX_TURNS:]
    history_lines = []
    for turn in trimmed:
        role = turn.get("role", "user")
        txt = turn.get("text", "")
        if role.lower().startswith("user"):
            history_lines.append(f"User: {txt}")
        else:
            history_lines.append(f"Assistant: {txt}")
    history_block = "\n".join(history_lines) if history_lines else "(no prior conversation)"
    prompt = (
        f"{system_prompt.strip()}\n\n"
        f"Preferred_language: {preferred_language_iso}\n\n"
        f"Conversation history (most recent last):\n{history_block}\n\n"
        f"New user message:\n{user_text.strip()}\n\n"
        "As the assistant, provide the next reply in the preferred language. Keep responses short and simple."
    )
    return prompt

def slugify(value: str) -> str:
    v = value or "artisan"
    v = v.strip().lower()
    out = []
    prev_dash = False
    for ch in v:
        if ch.isalnum():
            out.append(ch)
            prev_dash = False
        else:
            if not prev_dash:
                out.append("-")
                prev_dash = True
    s = "".join(out).strip("-")
    if not s:
        s = f"artisan-{int(datetime.datetime.utcnow().timestamp())}"
    return s[:64]

def extract_json_from_text(text: str) -> dict:
    if not text:
        return {}
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start:end+1]
            return json.loads(candidate)
    except Exception:
        pass
    try:
        return json.loads(text)
    except Exception:
        return {}

def generate_profile_from_responses(file_path: str, gemini_api_key: str = None, gemini_model_name: str = None) -> str:
    """
    Wraps existing generator: returns out_path to saved JSON (relative path as string),
    or None on failure.
    """
    gemini_api_key = gemini_api_key or GEMINI_API_KEY
    gemini_model_name = gemini_model_name or GEMINI_MODEL_NAME

    # If GEMINI configured, try to use your earlier implementation to extract structured JSON
    if gemini_api_key:
        # Re-use the prompt + extraction logic from your earlier script.
        with open(file_path, "r", encoding="utf-8") as f:
            convo_text = f.read()
        prompt = (
            "You are a helpful assistant. The following is an interview transcript (may be in Hindi). "
            "Extract the artisan's facts and output valid JSON ONLY. The JSON should include any of these keys if available:\n"
            "full_name, name, location, brief_bio, bio, craft, tagline, materials_and_techniques, materials, "
            "aspirations_needs, aspiration, suggested_support, short_summary\n\n"
            "We will map those into this final profile schema (English):\n"
            "- Full Name\n"
            "- Location\n"
            "- Bio\n"
            "- Tagline\n"
            "- Materials Used\n"
            "- Aspiration\n\n"
            "If a piece of information is not present, set the value to an empty string. Make sure your output is STRICT JSON.\n\n"
            "Interview:\n" + convo_text + "\n\nOutput strictly a single JSON object and nothing else. Even if the input is in Hindi, respond in English.Your entire output should be purely in English and no use of Hindi in your output json strictly"
        )
        try:
            gemini_out = call_gemini_raw(prompt=prompt, api_key=gemini_api_key, model_name=gemini_model_name, max_output_tokens=512, temperature=0.0)
            parsed = extract_json_from_text(gemini_out or "")
        except Exception:
            parsed = {}
    else:
        parsed = {}

    # fallback heuristic summary (if keys missing)
    def get_any(d, keys, fallback=""):
        for k in keys:
            if k in d and d[k]:
                return d[k]
        return fallback

    with open(file_path, "r", encoding="utf-8") as f:
        convo_text = f.read()

    # Try to fill fields from parsed or heuristics
    full_name = get_any(parsed, ["full_name", "name"]) or ""
    location = get_any(parsed, ["location", "place", "village", "city"]) or ""
    bio = get_any(parsed, ["brief_bio", "bio", "short_summary"]) or ""
    tagline = get_any(parsed, ["tagline", "short_summary"]) or ""
    materials = get_any(parsed, ["materials_and_techniques", "materials", "materials_used"]) or ""
    aspiration = get_any(parsed, ["aspirations_needs", "aspiration", "aspirations", "needs"]) or ""

    # Heuristic: try to find name patterns in raw text if missing
    if not full_name:
        m = re.search(r"(?:my name is|I am|नाम\s*[:\-]?\s*)([A-Z][a-zA-Z\s]{2,30}|[^\n।,]+)", convo_text, re.I)
        if m:
            full_name = m.group(1).strip()

    # Build friendly bio if none found
    if not bio:
        # Take first few user responses or the whole transcript trimmed
        snippet = convo_text.strip().splitlines()
        bio_candidate = " ".join(snippet)[:600]
        bio = bio_candidate

    final_profile = {
        "Full Name": full_name or "",
        "Location": location or "",
        "Bio": bio or "",
        "Tagline": tagline or (parsed.get("craft","").strip() + " artisan" if parsed.get("craft") else ""),
        "Materials Used": materials or "",
        "Aspiration": aspiration or ""
    }

    # Persist profile JSON and a readable TXT
    profiles_dir = Path("uploads") / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    slug_base = full_name or parsed.get("craft") or "artisan"
    slug = slugify(slug_base)
    out_json = profiles_dir / f"{slug}.json"
    out_txt = profiles_dir / f"{slug}.txt"
    try:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(final_profile, f, ensure_ascii=False, indent=2)
        # write readable summary
        with open(out_txt, "w", encoding="utf-8") as f:
            f.write(f"Full Name: {final_profile['Full Name']}\n")
            f.write(f"Location: {final_profile['Location']}\n\n")
            f.write("Bio:\n")
            f.write(final_profile["Bio"] + "\n\n")
            f.write(f"Tagline: {final_profile['Tagline']}\n")
            f.write(f"Materials Used: {final_profile['Materials Used']}\n")
            f.write(f"Aspiration: {final_profile['Aspiration']}\n")
    except Exception as e:
        print("⚠️  Failed to write profile files:", e)
        return None

    return str(out_json)

# ------------------ Recording utilities ------------------
def record_with_sounddevice(out_path: Path):
    if not SOUNDDEVICE_AVAILABLE:
        raise RuntimeError("sounddevice/soundfile not available")
    samplerate = 48000
    channels = 1
    print("Recording... Press Enter to stop recording.")
    with sf.SoundFile(str(out_path), mode='w', samplerate=samplerate, channels=channels, subtype='PCM_16') as f:
        def callback(indata, frames, time_info, status):
            f.write(indata.copy())
        with sd.InputStream(samplerate=samplerate, channels=channels, callback=callback):
            try:
                input()  # wait for Enter
            except KeyboardInterrupt:
                pass
    return out_path

def record_with_ffmpeg(out_path: Path):
    if sys.platform.startswith("win"):
        device_arg = ["-f", "dshow", "-i", "audio=default"]
    elif sys.platform.startswith("linux"):
        device_arg = ["-f", "pulse", "-i", "default"]
    elif sys.platform.startswith("darwin"):
        device_arg = ["-f", "avfoundation", "-i", ":0"]
    else:
        device_arg = ["-f", "pulse", "-i", "default"]
    cmd = ["ffmpeg", "-y"] + device_arg + ["-ar", "48000", "-ac", "1", str(out_path)]
    print("Recording via ffmpeg... Press Enter to stop.")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        input()
    except KeyboardInterrupt:
        pass
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
    return out_path

# ------------------ CLI / interactive loop ------------------
def parse_args():
    p = argparse.ArgumentParser(description="Interactive conversational CLI with storage")
    p.add_argument("--text-mode", action="store_true", help="Type your replies instead of speaking")
    p.add_argument("--no-tts-play", action="store_true", help="Do not attempt to play TTS audio (only save)")
    p.add_argument("--save-profile", action="store_true", help="Save generated profile after collecting 5 user replies (auto-saves by default at session end)")
    p.add_argument("--output-dir", "-o", default="uploads", help="Where to save transcripts, audio, profiles")
    return p.parse_args()

def ensure_dir(d: Path):
    d.mkdir(parents=True, exist_ok=True)

def main():
    args = parse_args()
    out_dir = Path(args.output_dir)
    ensure_dir(out_dir)
    audios_dir = out_dir / "audios"
    profiles_dir = out_dir / "profiles"
    ensure_dir(audios_dir)
    ensure_dir(profiles_dir)

    history = []

    # 1) Ask preferred language (TTS + print)
    language_prompt = "Which language do you prefer? Say English or Hindi."
    try:
        tts_bytes = eleven_tts_bytes(language_prompt)
        lang_audio_path = audios_dir / f"lang_prompt_{int(time.time())}.mp3"
        with open(lang_audio_path, "wb") as f:
            f.write(tts_bytes)
        print("\nAssistant (spoken):", language_prompt)
        if not args.no_tts_play:
            try:
                play_audio_file(str(lang_audio_path))
            except Exception:
                pass
    except Exception as e:
        print("⚠️  TTS failed for language prompt:", e)
        print("Assistant:", language_prompt)

    user_responses = []
    turn = 0
    while True:
        turn += 1
        print("\n--- TURN", turn, "---")
        if args.text_mode:
            user_input = input("You (type, or 'quit' to exit): ").strip()
            if user_input.lower() in ("quit", "exit"):
                print("Quitting by user request.")
                break
            transcript = user_input
            stt_lang_code = None
            # save typed transcript as a small text file for record
            tpath = audios_dir / f"user_text_{int(time.time())}.txt"
            with open(tpath, "w", encoding="utf-8") as f:
                f.write(transcript)
        else:
            tmp_audio = audios_dir / f"user_record_{int(time.time())}.wav"
            try:
                if SOUNDDEVICE_AVAILABLE:
                    record_with_sounddevice(tmp_audio)
                else:
                    print("sounddevice not available — falling back to ffmpeg recording.")
                    record_with_ffmpeg(tmp_audio)
            except Exception as e:
                print("🔻 Recording failed:", e)
                print("You can run with --text-mode to type your response instead.")
                return
            with open(tmp_audio, "rb") as f:
                file_bytes = f.read()
            try:
                stt_resp = eleven_stt_transcribe(file_bytes, filename=tmp_audio.name)
                transcript = stt_resp.get("text") or ""
                stt_lang_code = stt_resp.get("language_code") or None
                print("\nYou (transcript):", transcript)
            except Exception as e:
                print("❌ STT failed:", e)
                print("You can run with --text-mode to type your response instead.")
                return

        if not transcript:
            print("ℹ️  No transcript detected. Please respond again (or use --text-mode).")
            continue

        # Update history and user_responses
        history.append({"role": "user", "text": transcript})
        user_responses = [turn["text"] for turn in history if turn.get("role","").lower().startswith("user")]

        # Build prompt and call Gemini
        preferred_lang = detect_preferred_language_from_text(transcript, stt_lang_code)
        prompt = build_prompt_from_history(SYSTEM_PROMPT, history, transcript, preferred_lang)
        if not GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY not set. Set GEMINI_API_KEY env var or edit script.")
            return
        try:
            assistant_text = call_gemini_raw(prompt=prompt, api_key=GEMINI_API_KEY, model_name=GEMINI_MODEL_NAME, max_output_tokens=512, temperature=0.6)
            if not isinstance(assistant_text, str):
                assistant_text = str(assistant_text)
            assistant_text = assistant_text.strip()
        except Exception as e:
            print("❌ Gemini call failed:", e)
            return

        # Prepare text for TTS (remove [SUMMARY] prefix for speech)
        speak_text = assistant_text
        if speak_text.startswith("[SUMMARY] "):
            speak_text = speak_text[len("[SUMMARY] "):].strip()

        # Print assistant text, save history
        print("\nAssistant (text):", assistant_text)
        history.append({"role": "assistant", "text": assistant_text})

        # TTS and playback (save under audios_dir)
        try:
            tts_bytes = eleven_tts_bytes(speak_text)
            tts_file = audios_dir / f"assistant_{int(time.time())}.mp3"
            with open(tts_file, "wb") as f:
                f.write(tts_bytes)
            if not args.no_tts_play:
                try:
                    play_audio_file(str(tts_file))
                except Exception:
                    print("⚠️  Could not play audio (ffplay/powershell missing). TTS saved to", tts_file)
            else:
                print("TTS saved to", tts_file)
        except Exception as e:
            print("⚠️  TTS generation failed:", e)

        # Exit/summary check
        if len(user_responses) >= 5:
            print("\n✅ Collected >=5 user responses — preparing profile.")
            # write temporary transcript file similar to server flow
            user_file = out_dir / f"user_responses_{int(time.time())}.txt"
            with open(user_file, "w", encoding="utf-8") as f:
                for i, resp in enumerate(user_responses):
                    f.write(f"User Response {i+1}: {resp}\n")

            # Always try to generate a profile file (JSON + TXT). Use Gemini if configured; fallback if not.
            try:
                profile_json_path = generate_profile_from_responses(str(user_file), gemini_api_key=GEMINI_API_KEY, gemini_model_name=GEMINI_MODEL_NAME)
                if profile_json_path:
                    print("✅ Profile JSON created at:", profile_json_path)
                else:
                    print("⚠️  Profile generation returned None")
            except Exception as e:
                print("⚠️  Profile generation failed:", e)
            break

        cont = input("\nContinue? Press Enter to continue (or type 'quit' to exit): ").strip()
        if cont.lower() in ("quit", "exit"):
            print("Exiting by user request.")
            break

    # save final history
    ts = int(time.time())
    hpath = out_dir / f"history_{ts}.json"
    with open(hpath, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print("\nSession finished.")
    print("Saved files:")
    print(" - Audios folder:", audios_dir)
    print(" - Profiles folder:", profiles_dir)
    print(" - History:", hpath)
    print("Goodbye 👋")

if __name__ == "__main__":
    main()
