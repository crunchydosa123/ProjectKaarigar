#!/usr/bin/env python3
"""
Interactive terminal conversational CLI with persistent storage + Imagen logo generation.

How it works (brief):
- Runs the same interview loop as before and saves user responses into uploads/user_responses_*.txt
- After collecting >=5 user replies it generates a profile (JSON + TXT) as before
- NEW: it will now also try to create a brand/logo image using Vertex AI / Imagen (google.genai)
  by reading the same user_responses_*.txt file and heuristically extracting a brand name
  and descriptive words from the transcript.

This file includes a new function `generate_logo_prompt_with_gemini` which asks Gemini (text->text)
to extract a brand name and craft a concise Imagen-ready prompt. If Gemini fails or is unavailable,
local heuristics (existing functions) are used as a fallback.
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

# Vertex / Imagen defaults (override with env vars)
VERTEX_PROJECT = os.environ.get("VERTEX_PROJECT", "useful-figure-475210-g7")
VERTEX_LOCATION = os.environ.get("VERTEX_LOCATION", "us-central1")
IMAGEN_MODEL = os.environ.get("IMAGEN_MODEL", "imagen-4.0-generate-001")

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

# Try to import image types (may fail if google-genai not installed)
try:
    from google.genai.types import GenerateImagesConfig
except Exception:
    GenerateImagesConfig = None

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

# ------------------ New: Gemini-assisted logo prompt generator ------------------
def generate_logo_prompt_with_gemini(responses_input, gemini_api_key: str = None,
                                     gemini_model_name: str = None,
                                     temperature: float = 0.0,
                                     max_output_tokens: int = 512) -> dict:
    """
    Use Gemini (text->text) to extract a good brand name and produce an Imagen-ready logo prompt.

    Input:
      - responses_input: dict, list, or string containing user responses (JSON or raw transcript).
      - gemini_api_key, gemini_model_name: override globals if needed.
    Output: dict with keys:
      - brand_name (string)
      - candidates (list of strings)  # optional
      - short_description (string)
      - descriptors (list of words)
      - style_adjectives (list)
      - color_palette (list)
      - final_prompt (string)  # Imagen-ready prompt
    If Gemini fails or returns invalid JSON, this function returns a fallback dictionary
    constructed via local heuristics.
    """
    gemini_api_key = gemini_api_key or GEMINI_API_KEY
    gemini_model_name = gemini_model_name or GEMINI_MODEL_NAME

    # Normalize input to string for prompt context
    if isinstance(responses_input, (dict, list)):
        try:
            input_text = json.dumps(responses_input, ensure_ascii=False)
        except Exception:
            input_text = str(responses_input)
    else:
        input_text = str(responses_input or "")

    # A strict instruction asking Gemini to return ONLY JSON
    instruction = (
        "You are a prompt-engineer for image-generation. "
        "Input: a user interview transcript or JSON of user responses. "
        "Task: extract a single clear brand name (or propose a short ranked list) "
        "and produce a short, polished image-generation prompt optimized for a "
        "logo (vector, wordmark + icon, square aspect ratio).\n\n"
        "REQUIREMENTS:\n"
        " - Output ONLY a single valid JSON object and nothing else (no explanation).\n"
        " - Keys required where possible: brand_name, final_prompt.\n"
        " - Also include if available: candidates (list), short_description (one sentence), "
        "descriptors (list of short nouns/words), style_adjectives (list), color_palette (list).\n"
        " - The final_prompt must be concise (preferably <= 70 words), in English, and suitable for "
        "a vector-style, minimal logo: mention 'square', 'vector', 'wordmark' if appropriate and include "
        "visual motifs derived from the descriptors (do not include long paragraphs or system commentary).\n"
        " - If the input is not in English, produce the JSON and final_prompt in English.\n"
        " - If the transcript contains multiple possible brand names, pick the single most likely one for brand_name "
        "and return other options in candidates.\n\n"
        "Now parse the following interview content and return the requested JSON (only JSON):\n\n"
        f"INPUT:\n{input_text}\n\n"
        "End of input."
    )

    # Try to call Gemini
    gemini_out = None
    parsed = {}
    try:
        if not gemini_api_key:
            raise RuntimeError("Gemini API key not set; skipping Gemini step.")
        raw = call_gemini_raw(prompt=instruction, api_key=gemini_api_key,
                              model_name=gemini_model_name,
                              max_output_tokens=max_output_tokens, temperature=temperature)
        gemini_out = raw or ""
        parsed = extract_json_from_text(gemini_out)
    except Exception:
        parsed = {}

    # If parsed JSON is usable and has final_prompt and brand_name, normalize and return it
    if isinstance(parsed, dict) and parsed.get("final_prompt") and parsed.get("brand_name"):
        for k in ("candidates", "descriptors", "style_adjectives", "color_palette"):
            if k in parsed and isinstance(parsed[k], str):
                parsed[k] = [s.strip() for s in re.split(r"[,\n;/]+", parsed[k]) if s.strip()]
        return parsed

    # --- Fallback: Use local heuristics if Gemini failed or returned invalid JSON ---
    heur_brand = guess_brand_name_from_text(input_text)
    heur_prompt = build_logo_prompt(heur_brand, input_text)

    fallback = {
        "brand_name": heur_brand,
        "candidates": [heur_brand],
        "short_description": (input_text.strip().splitlines()[0][:200] if input_text else ""),
        "descriptors": [],
        "style_adjectives": ["minimal", "modern", "vector", "flat"],
        "color_palette": [],
        "final_prompt": heur_prompt
    }

    # derive a few descriptors heuristically (simple token filtering)
    try:
        words = re.findall(r"\b[\w']{3,20}\b", input_text)
        stop = set(["the","and","or","a","an","is","are","to","of","in","for","with","on","my","i","we","our","handmade"])
        descriptors = []
        for w in words:
            lw = w.lower()
            if lw in stop or lw.isdigit():
                continue
            if lw not in descriptors:
                descriptors.append(lw)
            if len(descriptors) >= 8:
                break
        fallback["descriptors"] = descriptors[:8]
    except Exception:
        pass

    return fallback

# ------------------ Imagen / logo helpers ------------------

def guess_brand_name_from_text(text: str) -> str:
    """Heuristically find a brand name in the transcript. Falls back to first significant token."""
    if not text:
        return "brand"
    # common patterns
    patterns = [
        r"brand name is\s*[:\-]?\s*([A-Z0-9][A-Za-z0-9 &\-]{1,40})",
        r"brand is\s*[:\-]?\s*([A-Z0-9][A-Za-z0-9 &\-]{1,40})",
        r"my brand is\s*[:\-]?\s*([A-Z0-9][A-Za-z0-9 &\-]{1,40})",
        r"the brand is\s*[:\-]?\s*([A-Z0-9][A-Za-z0-9 &\-]{1,40})",
        r"name is\s*[:\-]?\s*([A-Z][a-zA-Z]{2,30})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            return m.group(1).strip()
    # fallback: try to find a capitalized word sequence of 1-3 words
    m = re.search(r"([A-Z][a-z]{2,30}(?:\s+[A-Z][a-z]{2,30}){0,2})", text)
    if m:
        return m.group(1).strip()
    # final fallback: first token that's >2 chars
    for token in re.split(r"\s+", text.strip()):
        tk = re.sub(r"[^A-Za-z0-9]", "", token)
        if len(tk) > 2:
            return tk
    return "brand"


def build_logo_prompt(brand_name: str, transcript: str) -> str:
    """Create a compact, descriptive prompt for Imagen based on transcript and brand name."""
    # Extract adjectives / descriptors: short heuristic - common words excluding stopwords
    stopwords = set(["the","and","or","a","an","is","are","to","of","in","for","with","on","my","i","we","our"])
    words = re.findall(r"\b[\w']{3,20}\b", transcript)
    descriptors = []
    for w in words:
        lw = w.lower()
        if lw in stopwords:
            continue
        if lw.isdigit():
            continue
        if lw not in descriptors:
            descriptors.append(lw)
        if len(descriptors) >= 12:
            break
    desc_sample = ", ".join(descriptors[:8]) if descriptors else "handmade, artisanal"

    prompt = (
        f"Logo design for a brand named '{brand_name}'. "
        f"Use a clean, scalable, vector-style logo suitable for printing and digital use. "
        f"Visual style: minimal, modern, flat colors, simple icon that reflects: {desc_sample}. "
        "Include the brand name as a wordmark (prefer a readable sans-serif style). "
        "Produce a square image for use as an app icon and favicon. Provide multiple variations if possible."
    )
    return prompt


def create_logo_from_responses(response_file: str, output_dir: str = "uploads", image_basename: str = None,
                               model: str = None, aspect_ratio: str = "1:1", n_images: int = 1):
    """Reads the user responses text file, constructs an imagen prompt, and attempts to generate and save an image.
    Returns path to generated image or None on failure."""
    response_path = Path(response_file)
    if not response_path.exists():
        print("Logo generation skipped — responses file not found:", response_file)
        return None

    text = response_path.read_text(encoding="utf-8")

    # Prefer Gemini-generated prompt/spec if possible
    logo_spec = None
    try:
        if GEMINI_API_KEY:
            logo_spec = generate_logo_prompt_with_gemini(text, gemini_api_key=GEMINI_API_KEY, gemini_model_name=GEMINI_MODEL_NAME)
    except Exception as exc:
        print("⚠️  Gemini logo prompt generation failed:", exc)
        logo_spec = None

    if logo_spec and isinstance(logo_spec, dict) and logo_spec.get("final_prompt") and logo_spec.get("brand_name"):
        brand_name = logo_spec.get("brand_name") or guess_brand_name_from_text(text)
        prompt = logo_spec.get("final_prompt")
        # Provide some helpful logging for the user
        print("✅ Gemini provided logo prompt and brand name.")
        if logo_spec.get("candidates"):
            print("Brand candidates:", logo_spec.get("candidates"))
        if logo_spec.get("descriptors"):
            print("Descriptors:", logo_spec.get("descriptors")[:8])
    else:
        # fallback to existing local heuristics
        brand_name = guess_brand_name_from_text(text)
        prompt = build_logo_prompt(brand_name, text)
        print("ℹ️  Using heuristic logo prompt (Gemini unavailable or returned invalid JSON).")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not image_basename:
        image_basename = slugify(brand_name) or f"{int(time.time())}"
    output_file = out_dir / f"{image_basename}.png"

    # Ensure google.genai is available
    try:
        import google.genai as genai_local
        from google.genai.types import GenerateImagesConfig as _GIC
    except Exception as exc:
        print("⚠️  google.genai not available — cannot generate logo. Install the google-genai package and ensure Vertex access.")
        print("Prompt that would have been used:\n", prompt)
        return None

    # Create client for Vertex usage — this uses ADC for credentials or Vertex config
    try:
        client = genai_local.Client(vertexai=True, project=VERTEX_PROJECT, location=VERTEX_LOCATION)
    except Exception:
        # try bare client
        try:
            client = genai_local.Client()
        except Exception as e:
            print("⚠️  Failed to create google.genai Client:", e)
            print("Prompt that would have been used:\n", prompt)
            return None

    model_to_use = model or os.environ.get("IMAGEN_MODEL") or IMAGEN_MODEL

    try:
        cfg = _GIC(number_of_images=n_images, aspect_ratio=aspect_ratio)
        image = client.models.generate_images(
            model=model_to_use,
            prompt=prompt,
            config=cfg,
        )
        # Save first generated image
        gi = image.generated_images[0]
        # `gi.image` is a PIL-like wrapper in some clients. Try `.image.save` then fallback to bytes.
        try:
            gi.image.save(str(output_file))
        except Exception:
            # try raw bytes attribute
            try:
                with open(output_file, "wb") as f:
                    f.write(gi.image.image_bytes)
            except Exception as e:
                print("⚠️  Failed to write image file:", e)
                return None

        print(f"✅ Created logo: {output_file}")
        print(f"Prompt used: {prompt}")
        return str(output_file)
    except Exception as exc:
        print("⚠️  Logo generation failed:", exc)
        print("Prompt used:\n", prompt)
        return None

# ------------------ Existing profile generation logic ------------------
def generate_profile_from_responses(file_path: str, gemini_api_key: str = None, gemini_model_name: str = None) -> str:
    gemini_api_key = gemini_api_key or GEMINI_API_KEY
    gemini_model_name = gemini_model_name or GEMINI_MODEL_NAME

    if gemini_api_key:
        with open(file_path, "r", encoding="utf-8") as f:
            convo_text = f.read()
        prompt = (
            "You are a helpful assistant. The following is an interview transcript (may be in Hindi). "
            "Extract the artisan's facts and output valid JSON ONLY. The JSON should include any of these keys if available:\n"
            "full_name, name, location, brief_bio, bio, craft, tagline, materials_and_techniques, materials, "
            "aspirations_needs, aspiration, suggested_support, short_summary\n\n"
            "We will map those into this final profile schema (English):\n"
            "- Full Name\n- Location\n- Bio\n- Tagline\n- Materials Used\n- Aspiration\n\n"
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

    def get_any(d, keys, fallback=""):
        for k in keys:
            if k in d and d[k]:
                return d[k]
        return fallback

    with open(file_path, "r", encoding="utf-8") as f:
        convo_text = f.read()

    full_name = get_any(parsed, ["full_name", "name"]) or ""
    location = get_any(parsed, ["location", "place", "village", "city"]) or ""
    bio = get_any(parsed, ["brief_bio", "bio", "short_summary"]) or ""
    tagline = get_any(parsed, ["tagline", "short_summary"]) or (parsed.get("craft","").strip() + " artisan" if parsed.get("craft") else "")
    materials = get_any(parsed, ["materials_and_techniques", "materials", "materials_used"]) or ""
    aspiration = get_any(parsed, ["aspirations_needs", "aspiration", "aspirations", "needs"]) or ""

    if not full_name:
        m = re.search(r"(?:my name is|I am|नाम\s*[:\-]?\s*)([A-Z][a-zA-Z\s]{2,30}|[^\n।,]+)", convo_text, re.I)
        if m:
            full_name = m.group(1).strip()

    if not bio:
        snippet = convo_text.strip().splitlines()
        bio_candidate = " ".join(snippet)[:600]
        bio = bio_candidate

    final_profile = {
        "Full Name": full_name or "",
        "Location": location or "",
        "Bio": bio or "",
        "Tagline": tagline or "",
        "Materials Used": materials or "",
        "Aspiration": aspiration or ""
    }

    profiles_dir = Path("uploads") / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    slug_base = full_name or parsed.get("craft") or "artisan"
    slug = slugify(slug_base)
    out_json = profiles_dir / f"{slug}.json"
    out_txt = profiles_dir / f"{slug}.txt"
    try:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(final_profile, f, ensure_ascii=False, indent=2)
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

# ------------------ Recording utilities (unchanged) ------------------

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

# ------------------ CLI / interactive loop (main) ------------------

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

        history.append({"role": "user", "text": transcript})
        user_responses = [turn["text"] for turn in history if turn.get("role","").lower().startswith("user")]

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

        speak_text = assistant_text
        if speak_text.startswith("[SUMMARY] "):
            speak_text = speak_text[len("[SUMMARY] "):].strip()

        print("\nAssistant (text):", assistant_text)
        history.append({"role": "assistant", "text": assistant_text})

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

        if len(user_responses) >= 5:
            print("\n✅ Collected >=5 user responses — preparing profile.")
            user_file = out_dir / f"user_responses_{int(time.time())}.txt"
            with open(user_file, "w", encoding="utf-8") as f:
                for i, resp in enumerate(user_responses):
                    f.write(f"User Response {i+1}: {resp}\n")

            try:
                profile_json_path = generate_profile_from_responses(str(user_file), gemini_api_key=GEMINI_API_KEY, gemini_model_name=GEMINI_MODEL_NAME)
                if profile_json_path:
                    print("✅ Profile JSON created at:", profile_json_path)
                else:
                    print("⚠️  Profile generation returned None")
            except Exception as e:
                print("⚠️  Profile generation failed:", e)

            # NEW: try to create a logo from the responses file (no extra user input)
            try:
                logo_path = create_logo_from_responses(str(user_file), output_dir=str(out_dir))
                if logo_path:
                    print("✅ Logo created at:", logo_path)
                else:
                    print("⚠️  Logo creation skipped or failed. See messages above.")
            except Exception as e:
                print("⚠️  Logo creation failed:", e)

            break

        cont = input("\nContinue? Press Enter to continue (or type 'quit' to exit): ").strip()
        if cont.lower() in ("quit", "exit"):
            print("Exiting by user request.")
            break

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
