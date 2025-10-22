# routes/edit_routes.py
import os
import shutil
import base64
import logging
import requests
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from werkzeug.utils import secure_filename

# Keep your project helper imports (adjust relative path if necessary)
from video_edit.core import process_with_gemini
from video_edit.ffmpeg_utils import make_tmp_file, get_tmp_dir
from video_edit.music import mix_background_music, download_url_to_temp_audio

router = APIRouter()
logger = logging.getLogger("uvicorn.error")

# Prefer reading API keys from env; fallback to existing literal if present
ELEVEN_API_KEY = os.environ.get("ELEVEN_API_KEY", "sk_b5b7b026323972fbcc9f9e83344f948f44eacccb9ecd33d6")
DEFAULT_VOICE_ID = os.environ.get("DEFAULT_VOICE_ID", "KaCAGkAghyX8sFEYByRC")
ELEVEN_TTS_BASE = "https://api.elevenlabs.io/v1/text-to-speech"

TRENDING_SONGS = [
    { "id": "s1", "title": "Sahiba", "artist": "Aditya Rikhari", "duration": 30, "public_url": "https://drive.google.com/uc?export=download&id=1u5k0HPhka_ytUGLt6eyn3awVM3oYSS6b" },
    { "id": "s2", "title": "Saiyaara", "artist": "Tanishk Bagchi", "duration": 28, "public_url": "https://drive.google.com/uc?export=download&id=1CaPk8_CvQdH1FUZiEGVkjpbAff3FMaEz" },
    { "id": "s3", "title": "Dard", "artist": "Kushagra", "duration": 32, "public_url": "https://drive.google.com/uc?export=download&id=1fLXKnSdCmNYztsPTQf6S7Xxbnanw4M5E" },
    { "id": "s4", "title": "Kaanamale", "artist": "Mugen Rao", "duration": 25, "public_url": "https://drive.google.com/uc?export=download&id=1MixJI_YU5S2ORKfrQamOs-TbrmpTZi4m" },
    { "id": "s5", "title": "Pardesiya", "artist": "Sachin-Jigar", "duration": 29, "public_url": "https://drive.google.com/uc?export=download&id=1GC0zEcPp-TYMbCpr-p1u-zaHHsGB_Uuy" },
    { "id": "s6", "title": "Noormahal", "artist": "Chani Nattan", "duration": 27, "public_url": "https://drive.google.com/uc?export=download&id=1XtSSZOeaH1Uu8oBmDKzbFQXxl0EiDe5V" },
    { "id": "s7", "title": "The Night We Met", "artist": "Lord Huron", "duration": 30, "public_url": "https://drive.google.com/uc?export=download&id=1cz0o_si2oIaWKu5a3rgERbWoOCW5r9aS" },
    { "id": "s8", "title": "Yaarum Sollala", "artist": "Shreyas Narasimhan", "duration": 31, "public_url": "https://drive.google.com/uc?export=download&id=1JyncQt2piEU-0VdVCywpYPeGn0fJpID2" },
    { "id": "s9", "title": "Sapphire", "artist": "Ed Sheeran", "duration": 26, "public_url": "https://drive.google.com/uc?export=download&id=16jpFu95nzQy-vAky1U_h0UIsg0gGToPR" },
]


@router.post("/edit")
def edit_video(video: UploadFile = File(...), user_prompt: str = Form(...), request: Request = None):
    """
    POST /api/edit
    multipart/form-data:
      - video: file (required)
      - user_prompt: string (required)

    Returns the edited video as a FileResponse (video/mp4).
    """
    logger.info("Received /api/edit request")
    if not video:
        raise HTTPException(status_code=400, detail="No 'video' file part")

    if not user_prompt or not user_prompt.strip():
        raise HTTPException(status_code=400, detail="user_prompt must be provided.")

    safe_name = secure_filename(video.filename or "upload")
    ext = ".mp4"
    if "." in safe_name:
        ext = "." + safe_name.rsplit(".", 1)[-1]

    input_tmp = make_tmp_file(suffix=ext)
    if not input_tmp:
        raise HTTPException(status_code=500, detail="Failed to create temporary file for upload")

    try:
        # Save uploaded file stream to temporary path (streaming copy)
        with open(input_tmp, "wb") as out_f:
            shutil.copyfileobj(video.file, out_f)
    except Exception as e:
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        logger.exception("Failed to save uploaded file")
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    # get API key (prefer GEMINI_API_KEY)
    google_api_key = "AIzaSyAVSGUozgbc7AQs4xEhP_-xaTGtN78HBFU"
    if not google_api_key:
        # cleanup
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY/GEMINI_API_KEY not configured in environment.")

    out_tmp = make_tmp_file(suffix=".mp4")
    if not out_tmp:
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Failed to create temporary output file")

    try:
        logger.info(f"Processing video with prompt: {user_prompt[:80]}...")
        process_with_gemini(input_tmp, user_prompt, out_tmp, api_key=google_api_key)

        # return file to client
        return FileResponse(out_tmp, filename="edited.mp4", media_type="video/mp4")
    except Exception as e:
        logger.exception("Video edit failed")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # delete input file
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass


@router.post("/tts")
def tts_text(payload: dict):
    """
    POST /api/tts
    JSON body:
      { "text": "Hello", "voice_id": "optional-voice-id" }
    Response:
      { "audio_base64": "...", "mime": "audio/mpeg" }
    """
    if not ELEVEN_API_KEY:
        logger.error("ELEVENLABS_API_KEY is not configured")
        raise HTTPException(status_code=500, detail="Server misconfiguration: ELEVENLABS_API_KEY not configured")

    text = (payload.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Field 'text' is required.")

    voice_id = payload.get("voice_id") or DEFAULT_VOICE_ID
    url = f"{ELEVEN_TTS_BASE}/{voice_id}"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    body = {"text": text}

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        audio_bytes = resp.content

        # optional debug write
        try:
            tmp_debug = make_tmp_file(suffix=".mp3")
            if tmp_debug:
                with open(tmp_debug, "wb") as fh:
                    fh.write(audio_bytes)
                logger.debug(f"ElevenLabs TTS wrote debug audio to {tmp_debug}")
        except Exception:
            pass

        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return JSONResponse({"audio_base64": audio_b64, "mime": "audio/mpeg"})
    except requests.HTTPError as http_err:
        logger.exception("ElevenLabs TTS HTTP error")
        try:
            return JSONResponse({"error": f"ElevenLabs HTTP error: {http_err}; body: {resp.text}"}, status_code=502)
        except Exception:
            return JSONResponse({"error": str(http_err)}, status_code=502)
    except Exception as e:
        logger.exception("ElevenLabs TTS failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending_songs")
def trending_songs_list():
    return JSONResponse({"songs": TRENDING_SONGS}, status_code=200)


@router.post("/add_music")
def add_music_to_video(
    video: UploadFile = File(...),
    song_id: Optional[str] = Form(None),
    song_url: Optional[str] = Form(None),
    music_start: Optional[str] = Form(None),
    music_end: Optional[str] = Form(None),
    music_volume: Optional[str] = Form(None),
    loop: Optional[str] = Form("true"),
):
    """
    POST /api/add_music
    multipart/form-data:
      - video: file (required)
      - song_id or song_url
      - optional form fields: music_start, music_end, music_volume, loop
    """
    if not video:
        raise HTTPException(status_code=400, detail="No 'video' file part")

    safe_name = secure_filename(video.filename or "upload")
    ext = ".mp4"
    if "." in safe_name:
        ext = "." + safe_name.rsplit(".", 1)[-1]

    input_tmp = make_tmp_file(suffix=ext)
    if not input_tmp:
        raise HTTPException(status_code=500, detail="Failed to create temporary file for upload")

    try:
        with open(input_tmp, "wb") as out_f:
            shutil.copyfileobj(video.file, out_f)
    except Exception as e:
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        logger.exception("Failed to save uploaded file")
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    # resolve song_url from song_id if needed
    if not song_url and song_id:
        match = next((s for s in TRENDING_SONGS if s["id"] == song_id), None)
        if match:
            song_url = match.get("public_url")

    if not song_url:
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        raise HTTPException(status_code=400, detail="song_url or valid song_id must be provided")

    # parse optional params
    try:
        music_start_val = float(music_start) if music_start else 0.0
    except Exception:
        music_start_val = 0.0

    try:
        music_end_val = float(music_end) if music_end else None
    except Exception:
        music_end_val = None

    try:
        music_volume_val = float(music_volume) if music_volume else 0.4
    except Exception:
        music_volume_val = 0.4

    music_loop = str(loop).lower() in ("1", "true", "yes")

    out_tmp = make_tmp_file(suffix=".mp4")
    if not out_tmp:
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Failed to create temporary output file")

    try:
        mix_background_music(
            input_video=input_tmp,
            music_source_path=song_url,
            out_video=out_tmp,
            music_duration=None,
            music_volume=music_volume_val,
            loop=music_loop,
            music_start=music_start_val,
            music_end=music_end_val,
            reduce_original_volume=1.0,
            music_loop=music_loop,
            fade=1.0,
        )
        return FileResponse(out_tmp, filename="edited_with_music.mp4", media_type="video/mp4")
    except Exception as e:
        logger.exception("add_music failed")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
