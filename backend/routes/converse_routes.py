import os
import base64
import json
import requests
from flask import Blueprint, request, jsonify, current_app
import datetime

import json


# attempt to import Gemini client if available
try:
    import google.generativeai as genai  # optional
except Exception:
    genai = None

conv_bp = Blueprint("converse", __name__)


# Environment variables expected:
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.0-flash")

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
# Default voice id (replace with one from your ElevenLabs account)
ELEVEN_VOICE_ID = os.environ.get("VOICE_ID")

# ElevenLabs STT endpoint (see docs). We use the documented path /v1/speech-to-text.
ELEVEN_STT_URL = os.environ.get("ELEVEN_STT_URL", "https://api.elevenlabs.io/v1/speech-to-text")
ELEVEN_TTS_URL = os.environ.get("ELEVEN_TTS_URL", "https://api.elevenlabs.io/v1/text-to-speech")

# System prompt for Gemini (tailored to artisans)
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
"""

# ---------- Utilities ----------

def call_gemini_raw(prompt: str, api_key: str, model_name: str = "gemini-2.0-flash",
                    max_output_tokens: int = 1024, temperature: float = 0.0) -> str:
    if genai is None:
        raise RuntimeError("google.generativeai package not installed. pip install google-generativeai")
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        if hasattr(response, "text") and response.text:
            return response.text
        if hasattr(response, "candidates") and response.candidates:
            c0 = response.candidates[0]
            if hasattr(c0, "content") and c0.content:
                return c0.content
            return str(c0)
        return str(response)
    except Exception:
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
                if "candidates" in res and len(res["candidates"]) > 0:
                    c0 = res["candidates"][0]
                    if isinstance(c0, dict) and "content" in c0:
                        return c0["content"]
                    return json.dumps(c0)
                if "output" in res:
                    return res["output"]
            return str(res)
        except Exception as exc:
            raise RuntimeError(f"Failed to call Gemini: {exc}") from exc

def eleven_tts_bytes(text: str, voice_id: str = ELEVEN_VOICE_ID) -> bytes:
    """
    Call ElevenLabs Text-to-Speech and return raw audio bytes.
    (Uses POST /v1/text-to-speech/{voice_id} as a common endpoint shape.)
    """
    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY not set on server")

    url = f"{ELEVEN_TTS_URL}/{voice_id}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "text": text,
        # optional: model_id, voice_settings, language_code etc.
    }
    resp = requests.post(url, json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.content


def eleven_stt_transcribe(file_bytes: bytes, filename: str = "audio.webm", model_id: str = "scribe_v1", language_code: str = None):
    """
    Sends the audio bytes as a multipart/form-data upload to ElevenLabs STT endpoint.
    Returns dict response parsed from ElevenLabs (we look for .get('text')).
    See ElevenLabs docs: POST /v1/speech-to-text. :contentReference[oaicite:2]{index=2}
    """
    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY not set on server")

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
    }
    files = {
        "file": (filename, file_bytes, "application/octet-stream"),
    }
    data = {
        "model_id": model_id,
    }
    if language_code:
        data["language_code"] = language_code

    resp = requests.post(ELEVEN_STT_URL, headers=headers, files=files, data=data, timeout=60)
    resp.raise_for_status()
    return resp.json()


def detect_preferred_language_from_text(transcript: str, stt_language_code: str = None) -> str:
    """
    Try to map the short user reply (they are expected to speak a language name) to an ISO code.
    Accepts English names and native script tokens.
    Returns an ISO 639-1 code (e.g. 'en','hi','bn','ta') or falls back to stt_language_code or 'en'.
    """
    if not transcript:
        return stt_language_code or "en"
    t = transcript.strip().lower()
    mapping = {
        "english": "en", "ingl": "en", "eng": "en",
        "hindi": "hi", "हिन्दी": "hi", "हिंदी": "hi", "हिन्दी.": "hi",
        "bengali": "bn", "bangla": "bn", "বাংলা": "bn", "bangla.": "bn",
        "bengali.": "bn",
        "tamil": "ta", "தமிழ்": "ta",
        # some common alternatives
        "en": "en", "hi": "hi", "bn": "bn", "ta": "ta"
    }
    # try exact tokens in transcript (split words and whole text)
    for key, iso in mapping.items():
        if key in t:
            return iso
    # fallback use STT detected language code (first two chars)
    if stt_language_code:
        return stt_language_code.split("-")[0][:2]
    return "en"


def build_prompt_from_history(system_prompt: str, history: list, user_text: str, preferred_language_iso: str):
    """
    Build a plain text prompt fed to call_gemini_raw: system prompt + short conversational history + new user utterance.
    We include preferred language hint so Gemini knows which language to use.
    """
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

# ---------- Endpoints ----------

@conv_bp.route("/converse/start_language", methods=["GET"])
def start_language():
    """
    GET /api/converse/start_language
    Returns a short multilingual audio prompt (base64) asking the user to say their preferred language.
    The audio contains short sentences in English, Hindi, Bengali and Tamil.
    Response:
    {
      "prompt_text": "...",
      "audio_base64": "...",
      "mime": "audio/mpeg"
    }
    """
    try:
        # Compose the multilingual prompt (short lines)
        prompt_lines = [
            "Which language do you prefer? Say: English or Hindi.",
            # Hindi
            "आप किस भाषा को पसंद करते हैं? अंग्रेज़ी, या हिन्दी कहें।",


        ]
        prompt_text = " ".join(prompt_lines)

        audio_bytes = eleven_tts_bytes(prompt_text, voice_id=ELEVEN_VOICE_ID)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return jsonify({
            "prompt_text": prompt_text,
            "audio_base64": audio_b64,
            "mime": "audio/mpeg"
        })
    except Exception as e:
        current_app.logger.exception("Error in start_language")
        return jsonify({"error": str(e)}), 500


@conv_bp.route("/converse/submit_audio", methods=["POST"])
def submit_audio():
    """
    POST /api/converse/submit_audio
    Content-Type: multipart/form-data
    Fields:
      - audio: file (recorded user audio blob)
      - history: optional JSON string of conversation history (array of {role,text})
      - stt_language_hint: optional language_code hint (e.g. 'en' or 'hi') to improve STT
    Response:
    {
      "transcript": "...",            # STT text
      "stt_language_code": "en",
      "assistant_text": "...",        # Gemini reply text
      "audio_base64": "...",          # Gemini reply as TTS via ElevenLabs
      "mime": "audio/mpeg"
    }
    """
    if call_gemini_raw is None:
        current_app.logger.error("Gemini helper not imported")
        return jsonify({"error": "server misconfiguration: Gemini helper not available"}), 500

    if "audio" not in request.files:
        return jsonify({"error": "audio file is required (multipart form field 'audio')"}), 400

    try:
        file = request.files["audio"]
        file_bytes = file.read()
        history_raw = request.form.get("history", "[]")
        try:
            history = json.loads(history_raw)
        except Exception:
            history = []

        stt_language_hint = request.form.get("stt_language_hint")  # optional

        # 1) Send audio to ElevenLabs STT
        stt_resp = eleven_stt_transcribe(file_bytes, filename=file.filename or "audio.webm", language_code=stt_language_hint)
        # According to ElevenLabs docs, response contains 'text' and 'language_code' fields. :contentReference[oaicite:3]{index=3}
        transcript = stt_resp.get("text") or ""
        stt_lang_code = stt_resp.get("language_code") or stt_language_hint or None

        # 2) Try to detect preferred language if the user simply said a language name.
        preferred_lang = detect_preferred_language_from_text(transcript, stt_lang_code)

        # 3) Build Gemini prompt and call Gemini
        prompt = build_prompt_from_history(SYSTEM_PROMPT, history, transcript, preferred_lang)

        if not GEMINI_API_KEY:
            return jsonify({"error": "GEMINI_API_KEY not configured on server"}), 500

        assistant_text = call_gemini_raw(prompt=prompt, api_key=GEMINI_API_KEY, model_name=GEMINI_MODEL_NAME, max_output_tokens=512, temperature=0.6)
        if not isinstance(assistant_text, str):
            assistant_text = str(assistant_text)
        assistant_text = assistant_text.strip()

        updated_history = history + [{"role": "user", "text": transcript}, {"role": "assistant", "text": assistant_text}]

        # Check if this is the summary response
        if assistant_text.startswith("[SUMMARY] "):
            clean_assistant_text = assistant_text[len("[SUMMARY] "):].strip()
            assistant_text = clean_assistant_text

            # Extract user's responses
            user_responses = [turn['text'] for turn in updated_history if turn['role'] == 'user']

            # Create document content
            document = ""
            for i, resp in enumerate(user_responses, 1):
                document += f"User Response {i}: {resp}\n\n"

            # Save to uploads folder
            uploads_dir = os.path.join(current_app.root_path, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(uploads_dir, f"user_responses_{timestamp}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(document)

        # 4) Convert assistant_text to speech (ElevenLabs TTS)
        assistant_audio = eleven_tts_bytes(assistant_text, voice_id=ELEVEN_VOICE_ID)
        assistant_b64 = base64.b64encode(assistant_audio).decode("utf-8")

        return jsonify({
            "transcript": transcript,
            "stt_language_code": stt_lang_code,
            "preferred_language": preferred_lang,
            "assistant_text": assistant_text,
            "audio_base64": assistant_b64,
            "mime": "audio/mpeg"
        })
    except requests.HTTPError as http_err:
        current_app.logger.exception("HTTP error in submit_audio")
        return jsonify({"error": f"HTTP error contacting external API: {http_err}"}), 502
    except Exception as e:
        current_app.logger.exception("Error in submit_audio")
        return jsonify({"error": str(e)}), 500