# backend/routes/converse_routes.py
import os
import base64
import tempfile
import json
import requests
from flask import Blueprint, request, jsonify
from elevenlabs.client import ElevenLabs
from elevenlabs import AgentConfig, ConversationSimulationSpecification
from dotenv import load_dotenv

load_dotenv()  # load .env if present

conv_bp = Blueprint("converse", __name__)

ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY") or os.environ.get("ELEVENLABS_API_KEY")
DEFAULT_AGENT_ID = os.getenv("AGENT_ID") or os.environ.get("AGENT_ID") or "agent_6701k435cqn6f9k8r6krwnd7ym92"
DEFAULT_VOICE_ID = os.getenv("VOICE_ID") or os.environ.get("VOICE_ID") or None

if not ELEVEN_API_KEY:
    print("Warning: ELEVENLABS_API_KEY not set. Set it in environment or .env file.")

ELEVEN_STT_REST_URL = "https://api.elevenlabs.io/v1/speech-to-text"

def get_client():
    return ElevenLabs(api_key=ELEVEN_API_KEY)


@conv_bp.route("/agent/info", methods=["GET"])
def agent_info():
    return jsonify({"agent_id": DEFAULT_AGENT_ID, "voice_id": DEFAULT_VOICE_ID})


@conv_bp.route("/agent/create", methods=["POST"])
def create_agent():
    if not ELEVEN_API_KEY:
        return jsonify({"error": "ELEVENLABS_API_KEY not set on server"}), 500

    data = request.json or {}
    name = data.get("name", "Web conversational agent")
    system_prompt = data.get("system_prompt", "You are a helpful assistant that can answer questions and help with tasks.")

    client = get_client()
    conversation_config = {"agent": {"prompt": {"prompt": system_prompt}}}

    try:
        agent = client.conversational_ai.agents.create(
            name=name,
            conversation_config=conversation_config
        )
    except Exception as e:
        return jsonify({"error": "Agent creation failed", "details": str(e)}), 500

    return jsonify({"agent": agent}), 201


def _extract_agent_reply(sim_resp):
    try:
        if isinstance(sim_resp, dict) and "simulated_conversation" in sim_resp:
            conv = sim_resp.get("simulated_conversation") or []
            for turn in conv:
                role = (turn.get("role") or turn.get("speaker") or "").lower()
                msg = turn.get("message") or turn.get("text") or turn.get("content")
                if role == "assistant" and msg:
                    return msg
            for turn in reversed(conv):
                msg = turn.get("message") or turn.get("text") or turn.get("content")
                if msg:
                    return msg
            return None

        if hasattr(sim_resp, "simulated_conversation"):
            conv = getattr(sim_resp, "simulated_conversation")
            for turn in conv:
                try:
                    role = (turn.get("role") or turn.get("speaker") or "").lower()
                    msg = turn.get("message") or turn.get("text") or turn.get("content")
                except Exception:
                    role = getattr(turn, "role", "").lower() if hasattr(turn, "role") else ""
                    msg = getattr(turn, "message", None) or getattr(turn, "text", None) or getattr(turn, "content", None)
                if role == "assistant" and msg:
                    return msg
            for turn in reversed(conv):
                try:
                    msg = turn.get("message") or turn.get("text") or turn.get("content")
                except Exception:
                    msg = getattr(turn, "message", None) or getattr(turn, "text", None) or getattr(turn, "content", None)
                if msg:
                    return msg
            return None
    except Exception:
        pass

    try:
        return str(sim_resp)
    except Exception:
        return None


def _stt_rest_call(temp_path, model_id="scribe_v1"):
    headers = {"xi-api-key": ELEVEN_API_KEY}
    # send multipart/form-data with file and model_id
    with open(temp_path, "rb") as fh:
        files = {"file": fh}
        data = {"model_id": model_id}
        resp = requests.post(ELEVEN_STT_REST_URL, headers=headers, files=files, data=data, timeout=120)
    if resp.status_code >= 400:
        raise Exception(f"ElevenLabs STT REST error {resp.status_code}: {resp.text}")
    return resp.json()


def _try_speech_to_text(client, temp_path):
    last_exc = None
    # Try common SDK signatures (best-effort); if all fail fall back to REST
    try:
        with open(temp_path, "rb") as f:
            return client.speech_to_text.convert(file=f)
    except TypeError as te:
        last_exc = te
    except Exception as e:
        raise

    try:
        with open(temp_path, "rb") as f:
            return client.speech_to_text.convert(audio=f)
    except TypeError as te:
        last_exc = te
    except Exception as e:
        raise

    try:
        with open(temp_path, "rb") as f:
            return client.speech_to_text.convert(input_audio=f)
    except TypeError as te:
        last_exc = te
    except Exception as e:
        raise

    try:
        return client.speech_to_text.convert(file_path=temp_path)
    except TypeError as te:
        last_exc = te
    except Exception as e:
        raise

    try:
        with open(temp_path, "rb") as f:
            return client.speech_to_text.convert(f)
    except TypeError as te:
        last_exc = te
    except Exception as e:
        raise

    try:
        if hasattr(client.speech_to_text, "transcribe"):
            with open(temp_path, "rb") as f:
                return client.speech_to_text.transcribe(f)
    except TypeError as te:
        last_exc = te
    except Exception as e:
        raise

    try:
        if hasattr(client.speech_to_text, "from_file"):
            return client.speech_to_text.from_file(temp_path)
    except TypeError as te:
        last_exc = te
    except Exception as e:
        raise

    # SDK didn't work -> try REST
    try:
        rest_resp = _stt_rest_call(temp_path, model_id="scribe_v1")
        return rest_resp
    except Exception as e:
        raise TypeError(f"STT invocation failed for SDK and REST fallback. Last SDK error: {last_exc}. REST error: {e}")


@conv_bp.route("/text", methods=["POST"])
def converse_text():
    if not ELEVEN_API_KEY:
        return jsonify({"error": "ELEVENLABS_API_KEY not set on server"}), 500

    data = request.json or {}
    text = data.get("text")
    agent_id = data.get("agent_id") or DEFAULT_AGENT_ID
    voice_id = data.get("voice_id") or DEFAULT_VOICE_ID

    if not text:
        return jsonify({"error": "text is required"}), 400
    if not agent_id:
        return jsonify({"error": "agent_id is required (set AGENT_ID env or pass agent_id)"}), 400

    client = get_client()
    sim_spec = ConversationSimulationSpecification(
        simulated_user_config=AgentConfig(
            first_message=text,
        )
    )

    try:
        sim_resp = client.conversational_ai.agents.simulate_conversation(
            agent_id=agent_id,
            simulation_specification=sim_spec
        )
    except Exception as e:
        return jsonify({"error": "Agent simulation call failed", "details": str(e)}), 500

    agent_reply_text = _extract_agent_reply(sim_resp) or "Sorry — I couldn't generate a response."

    if not voice_id:
        return jsonify({
            "transcript": text,
            "reply_text": agent_reply_text,
            "audio_base64": None,
            "note": "No voice_id provided. Set VOICE_ID on server or pass voice_id in request to receive audio."
        })

    try:
        tts_audio_bytes = client.text_to_speech.convert(
            voice_id=voice_id,
            text=agent_reply_text
        )
    except Exception as e:
        return jsonify({"error": "TTS conversion failed", "details": str(e)}), 500

    if isinstance(tts_audio_bytes, (bytes, bytearray)):
        b64 = base64.b64encode(tts_audio_bytes).decode("utf-8")
    else:
        audio_bytes = bytes(tts_audio_bytes)
        b64 = base64.b64encode(audio_bytes).decode("utf-8")

    return jsonify({
        "transcript": text,
        "reply_text": agent_reply_text,
        "audio_base64": b64
    })


@conv_bp.route("/audio", methods=["POST"])
def converse_audio():
    if not ELEVEN_API_KEY:
        return jsonify({"error": "ELEVENLABS_API_KEY not set on server"}), 500

    if "audio" not in request.files:
        return jsonify({"error": "No audio file sent. Use form field 'audio'."}), 400

    audio_file = request.files["audio"]
    agent_id = request.form.get("agent_id") or DEFAULT_AGENT_ID
    voice_id = request.form.get("voice_id") or DEFAULT_VOICE_ID

    if not agent_id:
        return jsonify({"error": "agent_id is required (set AGENT_ID env or pass agent_id)"}), 400

    # Read all bytes from the uploaded file to validate
    try:
        file_bytes = audio_file.read()
    except Exception as e:
        return jsonify({"error": "Failed reading uploaded file", "details": str(e)}), 400

    # Diagnostics for debugging client uploads
    filename = getattr(audio_file, "filename", None)
    mimetype = getattr(audio_file, "mimetype", None)
    content_length = len(file_bytes) if file_bytes is not None else 0

    if not file_bytes or content_length == 0:
        return jsonify({
            "error": "Uploaded file is empty or zero-bytes",
            "details": {
                "filename": filename,
                "mimetype": mimetype,
                "size_bytes": content_length,
                "hint": "Client recorded file appears empty. Ensure MediaRecorder produced data, call mediaRecorder.requestData() before stop, and verify blob size on client."
            }
        }), 400

    # Save to temp path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        temp_path = tmp.name
        try:
            tmp.write(file_bytes)
            tmp.flush()
        except Exception as e:
            try:
                os.unlink(temp_path)
            except Exception:
                pass
            return jsonify({"error": "Failed writing temp audio file", "details": str(e)}), 500

    client = get_client()

    # 1) Speech-to-text (try SDK signatures and REST fallback)
    try:
        stt_result = _try_speech_to_text(client, temp_path)
        if isinstance(stt_result, dict) and "text" in stt_result:
            transcript = stt_result["text"]
        elif isinstance(stt_result, dict) and "transcript" in stt_result:
            transcript = stt_result["transcript"]
        elif isinstance(stt_result, str):
            transcript = stt_result
        elif hasattr(stt_result, "get") and stt_result.get("text"):
            transcript = stt_result.get("text")
        else:
            transcript = str(stt_result)
    except Exception as e:
        try:
            os.unlink(temp_path)
        except Exception:
            pass
        return jsonify({"error": "STT failed", "details": str(e)}), 500

    # 2) Simulate conversation
    try:
        sim_spec = ConversationSimulationSpecification(
            simulated_user_config=AgentConfig(
                first_message=transcript,
            )
        )
        sim_resp = client.conversational_ai.agents.simulate_conversation(
            agent_id=agent_id,
            simulation_specification=sim_spec
        )

        agent_reply_text = _extract_agent_reply(sim_resp)
        if not agent_reply_text:
            agent_reply_text = "Sorry — I couldn't figure out a response."
    except Exception as e:
        try:
            os.unlink(temp_path)
        except Exception:
            pass
        return jsonify({"error": "Agent simulation failed", "details": str(e)}), 500

    # 3) TTS
    try:
        if not voice_id:
            audio_b64 = None
        else:
            tts_audio = client.text_to_speech.convert(
            voice_id=voice_id,
            text=agent_reply_text
        )

        # Normalize output
        if isinstance(tts_audio, (bytes, bytearray)):
            final_audio = tts_audio
        elif isinstance(tts_audio, (list, tuple)):
            # list of bytes chunks
            final_audio = b"".join(tts_audio)
        elif hasattr(tts_audio, "__iter__"):  
            # generator of bytes chunks
            final_audio = b"".join(tts_audio)
        elif hasattr(tts_audio, "read"):  
            # file-like object
            final_audio = tts_audio.read()
        else:
            raise TypeError(f"Unexpected TTS output type: {type(tts_audio)}")

        audio_b64 = base64.b64encode(final_audio).decode("utf-8")

    except Exception as e:
        try:
            os.unlink(temp_path)
        except Exception:
            pass
        return jsonify({"error": "TTS failed", "details": str(e)}), 500

    # cleanup
    try:
        os.unlink(temp_path)
    except Exception:
        pass

    return jsonify({
        "transcript": transcript,
        "reply_text": agent_reply_text,
        "audio_base64": audio_b64,
        "uploaded_file": {"filename": filename, "mimetype": mimetype, "size_bytes": content_length}
    })
