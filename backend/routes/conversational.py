from flask import Blueprint, request, jsonify, session
from flask_cors import CORS
import uuid
import json
import io
import base64
from datetime import datetime
import os
import sys
import re
import tempfile
import requests

# Add the parent directory to the path to import Database_Setup modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from google.cloud import firestore
    from google.cloud import storage
    from Database_Setup.firestore_nosql_storage import create_document, get_document, query_documents
    FIRESTORE_AVAILABLE = True
    STORAGE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Google Cloud services not available: {e}")
    FIRESTORE_AVAILABLE = False
    STORAGE_AVAILABLE = False

# Create blueprint
conversational_bp = Blueprint('conversational_bp', __name__)

# Configuration
PROJECT_ID = "karigar-475215"
BUCKET_NAME = "all_in_one_bucket1"
COLLECTION_NAME = "kaarigars"  # Changed to match user requirement

# Initialize clients
if FIRESTORE_AVAILABLE:
    try:
        db = firestore.Client(project=PROJECT_ID)
        print("✅ Firestore client initialized successfully")
    except Exception as e:
        print(f"❌ Firestore initialization failed: {e}")
        FIRESTORE_AVAILABLE = False

if STORAGE_AVAILABLE:
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        print("✅ Cloud Storage client initialized successfully")
    except Exception as e:
        print(f"❌ Cloud Storage initialization failed: {e}")
        STORAGE_AVAILABLE = False

# Gemini API configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDiUMs4sIAdOk09006hS7DcY79DZh53_M4")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.0-flash")

# ElevenLabs API configuration for STT and TTS
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "sk_b346f8c1a3001388c671ebbea7f54c349f953cf827dd4dec")
ELEVEN_STT_URL = os.environ.get("ELEVEN_STT_URL", "https://api.elevenlabs.io/v1/speech-to-text")
ELEVEN_TTS_URL = os.environ.get("ELEVEN_TTS_URL", "https://api.elevenlabs.io/v1/text-to-speech")
ELEVEN_VOICE_ID = os.environ.get("ELEVEN_VOICE_ID", "KaCAGkAghyX8sFEYByRC")

# System prompt for conversational onboarding
SYSTEM_PROMPT = """
You are an empathetic interviewer designed to collect a concise artisan background profile suitable for building localized training data.
Rules:
1) Ask up to 6 short, plain-language questions (ask only what's necessary). Do NOT hardcode exact question scripts in the client — generate them naturally here.
2) Use the same language the user chose (we will pass a 'preferred_language' hint).
3) Make sure among the sequence of questions you ask:
   - one question that collects the person's brand name (or what they would like their brand to be called),
   - and one question that asks clear logo specifications / preferences (style, colors, motifs, whether they want wordmark/icon, desired uses like app icon, print, etc.).
   These should be asked as part of your conversational flow (you may include both in one question or separate questions) — don't require the client to present the exact phrasing.
4) Ask about: the artisan's name and craft, how they learned the craft/family background, materials/techniques and main challenges, aspirations/needs/support, and brand/logo specs as noted above. Keep questions short.
5) After the final user reply (or if you already have enough information), produce a short summary (2-3 sentences) in that language containing the artisan's name, craft, key materials/techniques, challenges and one wish/need if provided. Prefix the summary with "[SUMMARY] ".
6) Do not output metadata or system instructions — output only the assistant text that will be spoken to the user.
7) When continuing a conversation, read the conversation history and avoid repeating questions.
8) Stop asking new questions after 6 user responses and move to summary.
"""

def generate_kaarigar_id(user_id):
    """Generate a kaarigar ID based on user ID"""
    return f"KR_{user_id.upper()}"

def generate_brand_id(user_id):
    """Generate a brand ID based on user ID"""
    return f"BRAND_{user_id.upper()}"

def get_user_from_session():
    """Get user ID from session"""
    user_id = session.get('user_id')
    if not user_id:
        raise ValueError("No user session found. Please login first.")
    return user_id

def detect_preferred_language_from_text(transcript: str) -> str:
    """Detect preferred language from text"""
    if not transcript:
        return "en"
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
    return "en"

def build_prompt_from_history(system_prompt: str, history: list, user_text: str, preferred_language_iso: str):
    """Build prompt from conversation history"""
    MAX_TURNS = 8
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

def eleven_stt_transcribe(audio_bytes: bytes, filename: str = "audio.wav", model_id: str = "scribe_v1", language_code: str = None):
    """Transcribe audio using ElevenLabs STT"""
    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY not set.")
    
    print(f"🎤 STT Request - File: {filename}, Size: {len(audio_bytes)} bytes, Model: {model_id}")
    
    # Try different content types based on filename
    content_type = "application/octet-stream"
    if filename.endswith('.webm'):
        content_type = "audio/webm"
    elif filename.endswith('.wav'):
        content_type = "audio/wav"
    elif filename.endswith('.mp3'):
        content_type = "audio/mpeg"
    elif filename.endswith('.ogg'):
        content_type = "audio/ogg"
    
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    files = {"file": (filename, audio_bytes, content_type)}
    data = {"model_id": model_id}
    if language_code:
        data["language_code"] = language_code
    
    try:
        resp = requests.post(ELEVEN_STT_URL, headers=headers, files=files, data=data, timeout=60)
        print(f"📡 STT Response Status: {resp.status_code}")
        
        if resp.status_code == 200:
            result = resp.json()
            print(f"📝 STT Result: {result}")
            return result
        else:
            print(f"❌ STT API Error: {resp.status_code} - {resp.text}")
            return {"text": "", "error": f"STT API returned {resp.status_code}"}
            
    except requests.exceptions.Timeout:
        print("❌ STT request timed out")
        return {"text": "", "error": "STT request timed out"}
    except Exception as e:
        print(f"❌ STT transcription failed: {e}")
        return {"text": "", "error": str(e)}

def eleven_tts_generate(text: str, voice_id: str = ELEVEN_VOICE_ID) -> bytes:
    """Generate speech using ElevenLabs TTS"""
    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY not set.")
    
    url = f"{ELEVEN_TTS_URL}/{voice_id}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    body = {"text": text}
    
    try:
        resp = requests.post(url, json=body, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        print(f"❌ TTS generation failed: {e}")
        raise RuntimeError(f"TTS generation failed: {e}")

def call_gemini_raw(prompt: str, api_key: str, model_name: str = "gemini-2.0-flash",
                    max_output_tokens: int = 1024, temperature: float = 0.0) -> str:
    """Call Gemini API"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt, generation_config={"temperature": temperature, "max_output_tokens": max_output_tokens})
        if hasattr(response, "text") and response.text:
            return response.text
        return str(response)
    except Exception as e:
        print(f"❌ Gemini call failed: {e}")
        return "I'm sorry, I'm having trouble processing your request right now. Please try again."

def upload_to_cloud_storage(data: str, path: str, content_type: str = "text/plain") -> str:
    """Upload data to Cloud Storage and return public URL"""
    if not STORAGE_AVAILABLE:
        print("⚠️ Cloud Storage not available")
        return None
    
    try:
        blob = bucket.blob(path)
        blob.upload_from_string(data, content_type=content_type)
        
        # Make the blob publicly accessible
        blob.make_public()
        
        # Generate public URL
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{path}"
        print(f"✅ Uploaded to Cloud Storage: {path}")
        print(f"🌐 Public URL: {public_url}")
        return public_url
    except Exception as e:
        print(f"❌ Cloud Storage upload failed: {e}")
        return None

def save_conversation_summary_to_storage(conversation_summary: str, kaarigar_id: str) -> str:
    """Save conversation summary to Cloud Storage"""
    try:
        # Save conversation summary as single text file
        summary_path = f"kaarigar/{kaarigar_id}/conversation_summary.txt"
        public_url = upload_to_cloud_storage(conversation_summary, summary_path, "text/plain")
        print(f"✅ Conversation summary saved to: {summary_path}")
        return public_url
    except Exception as e:
        print(f"❌ Failed to save conversation summary to storage: {e}")
        return None

def save_profile_to_storage(profile_data: dict, kaarigar_id: str) -> str:
    """Save profile data as JSON to Cloud Storage"""
    try:
        # Save profile as JSON file
        profile_path = f"kaarigar/{kaarigar_id}/profile/profile.json"
        profile_json = json.dumps(profile_data, indent=2, ensure_ascii=False)
        public_url = upload_to_cloud_storage(profile_json, profile_path, "application/json")
        print(f"✅ Profile JSON saved to: {profile_path}")
        return public_url
    except Exception as e:
        print(f"❌ Failed to save profile to storage: {e}")
        return None

def cleanup_old_conversations(user_id, keep_kaarigar_id):
    """Delete old kaarigar profiles for a user, keeping only the latest successful one"""
    try:
        from Database_Setup.firestore_nosql_storage import delete_document
        
        # Get all kaarigar profiles for the user
        all_kaarigars = query_documents("user_id", "==", user_id)
        
        if len(all_kaarigars) <= 1:
            print(f"📝 No old conversations to clean up (only {len(all_kaarigars)} profile)")
            return
        
        deleted_count = 0
        for kaarigar in all_kaarigars:
            kaarigar_id = kaarigar.get("kaarigar_id")
            if kaarigar_id != keep_kaarigar_id:
                try:
                    delete_document(kaarigar_id)
                    deleted_count += 1
                    print(f"🗑️ Deleted old conversation: {kaarigar_id}")
                except Exception as e:
                    print(f"⚠️ Failed to delete {kaarigar_id}: {e}")
        
        print(f"✅ Cleaned up {deleted_count} old conversations, kept: {keep_kaarigar_id}")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

def generate_comprehensive_profile_and_summary(user_responses: list, gemini_api_key: str = None, 
                                              gemini_model_name: str = None, input_language_iso: str = None) -> dict:
    """Generate comprehensive profile and conversation summary using Gemini"""
    gemini_api_key = gemini_api_key or GEMINI_API_KEY
    gemini_model_name = gemini_model_name or GEMINI_MODEL_NAME

    if not gemini_api_key:
        print("⚠️ Gemini API key not available")
        return {}

    # Create conversation text
    convo_text = "\n".join([f"User Response {i+1}: {resp}" for i, resp in enumerate(user_responses)])
    
    # Generate profile
    profile_prompt = (
        "You are a helpful assistant. The following is an interview transcript (may be in any language). "
        "Extract the artisan's facts and output valid JSON ONLY. The JSON should include any of these keys if available:\n"
        "full_name, name, location, brief_bio, bio, craft, tagline, materials_and_techniques, materials, "
        "aspirations_needs, aspiration, suggested_support, short_summary\n\n"
        "We will map those into this final profile schema (English):\n"
        "- Full Name\n- Location\n- Bio\n- Tagline\n- Materials Used\n- Aspiration\n\n"
        "If a piece of information is not present, set the value to an empty string. Make sure your output is STRICT JSON.\n\n"
        "Interview:\n" + convo_text + "\n\n"
        f"NOTE: The interview input language ISO: {input_language_iso or 'unknown'}. Prefer to extract the data using the input language's terms, but output JSON keys/values in English where possible.\n\n"
        "Output strictly a single JSON object and nothing else."
    )
    
    # Generate conversation summary
    summary_prompt = (
        "You are a helpful assistant. Create a comprehensive summary of the following artisan interview conversation. "
        "The summary should be in paragraph form, capturing all the key information about the artisan including their name, craft, background, materials, challenges, and aspirations. "
        "Make it engaging and informative, suitable for a profile description. "
        "Keep it in the same language as the conversation if possible, otherwise use English.\n\n"
        "Conversation:\n" + convo_text + "\n\n"
        "Output only the summary text, no additional formatting or explanations."
    )
    
    try:
        # Generate profile
        profile_out = call_gemini_raw(prompt=profile_prompt, api_key=gemini_api_key, model_name=gemini_model_name, max_output_tokens=512, temperature=0.0)
        
        # Generate summary
        summary_out = call_gemini_raw(prompt=summary_prompt, api_key=gemini_api_key, model_name=gemini_model_name, max_output_tokens=1024, temperature=0.3)
        
        # Extract JSON from profile response
        try:
            start = profile_out.find("{")
            end = profile_out.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = profile_out[start:end+1]
                parsed = json.loads(candidate)
            else:
                parsed = json.loads(profile_out)
        except Exception:
            parsed = {}
            
    except Exception as e:
        print(f"❌ Profile/summary generation failed: {e}")
        parsed = {}
        summary_out = ""

    def get_any(d, keys, fallback=""):
        for k in keys:
            if k in d and d[k]:
                return d[k]
        return fallback

    full_name = get_any(parsed, ["full_name", "name"]) or ""
    location = get_any(parsed, ["location", "place", "village", "city"]) or ""
    bio = get_any(parsed, ["brief_bio", "bio", "short_summary"]) or ""
    tagline = get_any(parsed, ["tagline", "short_summary"]) or (parsed.get("craft","").strip() + " artisan" if parsed.get("craft") else "")
    materials = get_any(parsed, ["materials_and_techniques", "materials", "materials_used"]) or ""
    aspiration = get_any(parsed, ["aspirations_needs", "aspiration", "aspirations", "needs"]) or ""

    # Fallback name extraction
    if not full_name and user_responses:
        first_response = user_responses[0]
        m = re.search(r"(?:my name is|I am|नाम\s*[:\-]?\s*)([A-Z][a-zA-Z\s]{2,30}|[^\n।,]+)", first_response, re.I)
        if m:
            full_name = m.group(1).strip()

    # Fallback bio
    if not bio and user_responses:
        bio = " ".join(user_responses)[:600]

    final_profile = {
        "Full Name": full_name or "",
        "Location": location or "",
        "Bio": bio or "",
        "Tagline": tagline or "",
        "Materials Used": materials or "",
        "Aspiration": aspiration or "",
        "Conversation Summary": summary_out.strip() or bio
    }

    return final_profile

@conversational_bp.route('/start', methods=['POST'])
def start_conversation():
    """Start a new conversational onboarding session"""
    print("🚀 CONVERSATIONAL START REQUEST")
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = session.get('user_id')
        
        # Check if user already has a kaarigar profile
        if FIRESTORE_AVAILABLE:
            try:
                existing_kaarigars = query_documents("user_id", "==", user_id)
                if existing_kaarigars:
                    # Use the most recent kaarigar profile (last one in the list)
                    kaarigar_data = existing_kaarigars[-1]  # Get the latest one
                    kaarigar_id = kaarigar_data.get("kaarigar_id")
                    brand_id = kaarigar_data.get("brand_id")
                    print(f"✅ Using existing kaarigar profile: {kaarigar_id} (Total profiles: {len(existing_kaarigars)})")
                    
                    # Clear conversation history to start fresh (prevent duplicate greetings)
                    kaarigar_data["conversation_history"] = []
                    print(f"🧹 Cleared conversation history for fresh start")
                    
                    # Show only the most recent 2 profiles instead of all
                    recent_profiles = existing_kaarigars[-2:] if len(existing_kaarigars) > 2 else existing_kaarigars
                    for i, profile in enumerate(recent_profiles):
                        status = profile.get("status", "active")
                        created = profile.get("created_at", "unknown")[:10]  # Just the date
                        print(f"   Profile {i+1}: {profile.get('kaarigar_id', 'unknown')} - {status} ({created})")
                else:
                    # Create new kaarigar profile
                    kaarigar_id = generate_kaarigar_id(user_id)
                    brand_id = generate_brand_id(user_id)
                    
                    # Create kaarigar profile
                    kaarigar_data = {
                        "kaarigar_id": kaarigar_id,
                        "brand_id": brand_id,
                        "user_id": user_id,
                        "status": "active",
                        "created_at": datetime.utcnow().isoformat(),
                        "conversation_count": 0,
                        "cloud_storage_urls": {},
                        "profile": {},
                        "preferred_language": "en",
                        "conversation_history": []
                    }
                    
                    create_document(kaarigar_data, kaarigar_id)
                    print(f"✅ New kaarigar profile created: {kaarigar_id}")
            except Exception as e:
                print(f"❌ Failed to get/create kaarigar profile: {e}")
                return jsonify({"error": "Failed to start conversation"}), 500
        else:
            return jsonify({"error": "Database not available"}), 500
        
        # Generate initial AI message
        initial_prompt = f"{SYSTEM_PROMPT}\n\nPreferred_language: en\n\nNew user message:\nHello\n\nAs the assistant, provide the first greeting in English. Keep it short and welcoming."
        print(f"🎤 GENERATING INITIAL GREETING - Prompt: {initial_prompt[:100]}...")
        ai_response = call_gemini_raw(initial_prompt, GEMINI_API_KEY, GEMINI_MODEL_NAME, temperature=0.6)
        print(f"🎤 INITIAL GREETING GENERATED: {ai_response[:100]}...")
        
        # Skip TTS audio for initial greeting to prevent multiple greetings
        ai_audio_base64 = None
        print("🔇 Skipping initial greeting audio to prevent duplicates")
        
        # Update kaarigar profile with conversation start (no greeting stored)
        if FIRESTORE_AVAILABLE:
            try:
                from Database_Setup.firestore_nosql_storage import update_document
                
                # Get current kaarigar data
                current_data = get_document(kaarigar_id)
                if current_data:
                    # Initialize conversation history if not exists
                    if "conversation_history" not in current_data:
                        current_data["conversation_history"] = []
                        print(f"📝 INITIALIZED EMPTY CONVERSATION HISTORY")
                    else:
                        print(f"📝 EXISTING CONVERSATION HISTORY FOUND: {len(current_data['conversation_history'])} messages")
                        for i, msg in enumerate(current_data['conversation_history']):
                            print(f"   Message {i+1}: {msg.get('role', 'unknown')} - {msg.get('text', '')[:50]}...")
                    
                    # Update with conversation start data (no greeting stored in history)
                    current_data.update({
                        "last_conversation_start": datetime.utcnow().isoformat(),
                        "current_conversation_active": True,
                        "conversation_history": []  # Ensure history is cleared
                    })
                    
                    update_document(kaarigar_id, current_data)
                    print(f"✅ Conversation started (greeting NOT stored in history) - History length: {len(current_data['conversation_history'])}")
            except Exception as e:
                print(f"⚠️ Failed to update kaarigar profile: {e}")
        
        return jsonify({
            "success": True,
            "kaarigar_id": kaarigar_id,
            "brand_id": brand_id,
            "ai_message": ai_response,
            "ai_audio": ai_audio_base64
        }), 200
        
    except Exception as e:
        print(f"❌ Start conversation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@conversational_bp.route('/message', methods=['POST'])
def send_message():
    """Send a message in the conversation"""
    print("🚀 CONVERSATIONAL MESSAGE REQUEST")
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        data = request.get_json()
        kaarigar_id = data.get('kaarigar_id')
        user_message = data.get('message', '').strip()
        
        if not kaarigar_id or not user_message:
            return jsonify({"error": "kaarigar_id and message are required"}), 400
        
        # Get kaarigar profile from Firestore
        if FIRESTORE_AVAILABLE:
            try:
                kaarigar_data = get_document(kaarigar_id)
                if not kaarigar_data:
                    return jsonify({"error": "Kaarigar profile not found"}), 404
            except Exception as e:
                print(f"❌ Failed to get kaarigar profile: {e}")
                return jsonify({"error": "Database error"}), 500
        else:
            return jsonify({"error": "Database not available"}), 500
        
        # Initialize conversation history if not exists
        if "conversation_history" not in kaarigar_data:
            kaarigar_data["conversation_history"] = []
        
        # Add user message to history
        user_message_data = {
            "role": "user",
            "text": user_message,
            "timestamp": datetime.utcnow().isoformat(),
            "input_type": "text"
        }
        kaarigar_data["conversation_history"].append(user_message_data)
        print(f"📝 ADDED USER MESSAGE TO HISTORY: {user_message[:50]}... (Total messages: {len(kaarigar_data['conversation_history'])})")
        
        # Detect language
        preferred_language = detect_preferred_language_from_text(user_message)
        kaarigar_data["preferred_language"] = preferred_language
        
        # Update kaarigar profile with user message first
        if FIRESTORE_AVAILABLE:
            try:
                from Database_Setup.firestore_nosql_storage import update_document
                update_document(kaarigar_id, kaarigar_data)
                print(f"✅ User message stored: {user_message[:50]}...")
            except Exception as e:
                print(f"❌ Failed to update kaarigar profile with user message: {e}")
        
        # Generate AI response
        prompt = build_prompt_from_history(
            SYSTEM_PROMPT, 
            kaarigar_data["conversation_history"], 
            user_message, 
            preferred_language
        )
        
        ai_response = call_gemini_raw(prompt, GEMINI_API_KEY, GEMINI_MODEL_NAME, temperature=0.6)
        
        # Add AI response to history
        ai_message_data = {
            "role": "assistant",
            "text": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        }
        kaarigar_data["conversation_history"].append(ai_message_data)
        print(f"📝 ADDED AI RESPONSE TO HISTORY: {ai_response[:50]}... (Total messages: {len(kaarigar_data['conversation_history'])})")
        
        # Update kaarigar profile with AI response
        if FIRESTORE_AVAILABLE:
            try:
                from Database_Setup.firestore_nosql_storage import update_document
                update_document(kaarigar_id, kaarigar_data)
                print(f"✅ AI response stored: {ai_response[:50]}...")
            except Exception as e:
                print(f"❌ Failed to update kaarigar profile with AI response: {e}")
        
        # Check if conversation is complete (6+ user responses)
        user_responses = [turn["text"] for turn in kaarigar_data["conversation_history"] if turn.get("role") == "user"]
        is_complete = len(user_responses) >= 6
        
        # Generate TTS audio for AI response
        ai_audio_base64 = None
        try:
            print("🔊 Generating TTS audio for AI response...")
            ai_audio_bytes = eleven_tts_generate(ai_response)
            ai_audio_base64 = base64.b64encode(ai_audio_bytes).decode('utf-8')
            print("✅ TTS audio generated successfully")
        except Exception as e:
            print(f"⚠️ TTS generation failed: {e}")
            # Continue without audio - not critical

        response_data = {
            "success": True,
            "ai_message": ai_response,
            "ai_audio": ai_audio_base64,
            "is_complete": is_complete,
            "user_response_count": len(user_responses)
        }
        
        # If conversation is complete, generate profile and summary
        if is_complete:
            print("✅ Conversation complete - generating profile and summary")
            try:
                # Generate comprehensive profile and summary
                profile_data = generate_comprehensive_profile_and_summary(user_responses, GEMINI_API_KEY, GEMINI_MODEL_NAME, preferred_language)
                
                # Save conversation summary and profile to Cloud Storage
                summary_url = None
                profile_url = None
                if STORAGE_AVAILABLE:
                    summary_url = save_conversation_summary_to_storage(profile_data.get("Conversation Summary", ""), kaarigar_id)
                    profile_url = save_profile_to_storage(profile_data, kaarigar_id)
                
                # Update kaarigar profile with final data
                kaarigar_data["status"] = "completed"
                kaarigar_data["profile"] = profile_data
                kaarigar_data["completed_at"] = datetime.utcnow().isoformat()
                kaarigar_data["conversation_count"] = kaarigar_data.get("conversation_count", 0) + 1
                kaarigar_data["current_conversation_active"] = False
                
                # Store Cloud Storage URLs
                if "cloud_storage_urls" not in kaarigar_data:
                    kaarigar_data["cloud_storage_urls"] = {}
                
                if summary_url:
                    kaarigar_data["cloud_storage_urls"]["conversation_summary"] = summary_url
                
                if profile_url:
                    kaarigar_data["cloud_storage_urls"]["profile"] = profile_url
                
                if FIRESTORE_AVAILABLE:
                    try:
                        update_document(kaarigar_id, kaarigar_data)
                        print(f"✅ Kaarigar profile updated with completion data")
                        
                        # Clean up old conversations only after successful profile generation
                        cleanup_old_conversations(session.get('user_id'), kaarigar_id)
                    except Exception as e:
                        print(f"⚠️ Failed to update completed kaarigar profile: {e}")
                
                response_data["profile"] = profile_data
                response_data["profile_saved"] = True
                response_data["summary_url"] = summary_url
                response_data["profile_url"] = profile_url
                
            except Exception as e:
                print(f"❌ Profile/summary generation failed")
                response_data["profile_error"] = "Profile generation failed"
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"❌ Send message error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@conversational_bp.route('/audio-message', methods=['POST'])
def send_audio_message():
    """Send an audio message in the conversation"""
    print("🚀 CONVERSATIONAL AUDIO MESSAGE REQUEST")
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        data = request.get_json()
        kaarigar_id = data.get('kaarigar_id')
        audio_base64 = data.get('audio')
        language_code = data.get('language_code', 'en')
        
        if not kaarigar_id or not audio_base64:
            return jsonify({"error": "kaarigar_id and audio are required"}), 400
        
        # Decode base64 audio
        try:
            audio_bytes = base64.b64decode(audio_base64)
        except Exception as e:
            print(f"❌ Failed to decode audio: {e}")
            return jsonify({"error": "Invalid audio data"}), 400
        
        # Transcribe audio using ElevenLabs STT
        print("🎤 Transcribing audio...")
        print(f"📊 Audio size: {len(audio_bytes)} bytes")
        
        # Try different audio formats for better compatibility
        stt_result = None
        audio_formats = [
            ("audio.webm", "audio/webm"),
            ("audio.wav", "audio/wav"), 
            ("audio.ogg", "audio/ogg")
        ]
        
        for filename, content_type in audio_formats:
            print(f"🔄 Trying format: {filename}")
            stt_result = eleven_stt_transcribe(audio_bytes, filename, "scribe_v1", language_code)
            
            if not stt_result.get("error") and stt_result.get("text", "").strip():
                print(f"✅ STT successful with format: {filename}")
                break
            else:
                print(f"❌ STT failed with format: {filename} - {stt_result.get('error', 'No text')}")
        
        if stt_result.get("error") or not stt_result.get("text", "").strip():
            print(f"❌ All STT attempts failed")
            return jsonify({"error": "Speech recognition failed. Please try speaking more clearly or use text input."}), 500
        
        user_message = stt_result.get("text", "").strip()
        
        print(f"📝 Transcribed text: {user_message}")
        
        # Get kaarigar profile from Firestore
        if FIRESTORE_AVAILABLE:
            try:
                kaarigar_data = get_document(kaarigar_id)
                if not kaarigar_data:
                    return jsonify({"error": "Kaarigar profile not found"}), 404
            except Exception as e:
                print(f"❌ Failed to get kaarigar profile: {e}")
                return jsonify({"error": "Database error"}), 500
        else:
            return jsonify({"error": "Database not available"}), 500
        
        # Initialize conversation history if not exists
        if "conversation_history" not in kaarigar_data:
            kaarigar_data["conversation_history"] = []
        
        # Add user message to history
        user_message_data = {
            "role": "user",
            "text": user_message,
            "timestamp": datetime.utcnow().isoformat(),
            "input_type": "audio"
        }
        kaarigar_data["conversation_history"].append(user_message_data)
        
        # Detect language
        preferred_language = detect_preferred_language_from_text(user_message)
        kaarigar_data["preferred_language"] = preferred_language
        
        # Update kaarigar profile with user message first
        if FIRESTORE_AVAILABLE:
            try:
                from Database_Setup.firestore_nosql_storage import update_document
                update_document(kaarigar_id, kaarigar_data)
                print(f"✅ User audio message stored: {user_message[:50]}...")
            except Exception as e:
                print(f"❌ Failed to update kaarigar profile with user audio message: {e}")
        
        # Generate AI response
        prompt = build_prompt_from_history(
            SYSTEM_PROMPT, 
            kaarigar_data["conversation_history"], 
            user_message, 
            preferred_language
        )
        
        ai_response = call_gemini_raw(prompt, GEMINI_API_KEY, GEMINI_MODEL_NAME, temperature=0.6)
        
        # Add AI response to history
        ai_message_data = {
            "role": "assistant",
            "text": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        }
        kaarigar_data["conversation_history"].append(ai_message_data)
        print(f"📝 ADDED AI RESPONSE TO HISTORY: {ai_response[:50]}... (Total messages: {len(kaarigar_data['conversation_history'])})")
        
        # Update kaarigar profile with AI response
        if FIRESTORE_AVAILABLE:
            try:
                from Database_Setup.firestore_nosql_storage import update_document
                update_document(kaarigar_id, kaarigar_data)
                print(f"✅ AI response stored: {ai_response[:50]}...")
            except Exception as e:
                print(f"❌ Failed to update kaarigar profile with AI response: {e}")
        
        # Check if conversation is complete (6+ user responses)
        user_responses = [turn["text"] for turn in kaarigar_data["conversation_history"] if turn.get("role") == "user"]
        is_complete = len(user_responses) >= 6
        
        # Generate TTS audio for AI response
        ai_audio_base64 = None
        try:
            print("🔊 Generating TTS audio for AI response...")
            ai_audio_bytes = eleven_tts_generate(ai_response)
            ai_audio_base64 = base64.b64encode(ai_audio_bytes).decode('utf-8')
            print("✅ TTS audio generated successfully")
        except Exception as e:
            print(f"⚠️ TTS generation failed: {e}")
            # Continue without audio - not critical

        response_data = {
            "success": True,
            "transcribed_text": user_message,
            "ai_message": ai_response,
            "ai_audio": ai_audio_base64,
            "is_complete": is_complete,
            "user_response_count": len(user_responses)
        }
        
        # If conversation is complete, generate profile and summary
        if is_complete:
            print("✅ Conversation complete - generating profile and summary")
            try:
                # Generate comprehensive profile and summary
                profile_data = generate_comprehensive_profile_and_summary(user_responses, GEMINI_API_KEY, GEMINI_MODEL_NAME, preferred_language)
                
                # Save conversation summary and profile to Cloud Storage
                summary_url = None
                profile_url = None
                if STORAGE_AVAILABLE:
                    summary_url = save_conversation_summary_to_storage(profile_data.get("Conversation Summary", ""), kaarigar_id)
                    profile_url = save_profile_to_storage(profile_data, kaarigar_id)
                
                # Update kaarigar profile with final data
                kaarigar_data["status"] = "completed"
                kaarigar_data["profile"] = profile_data
                kaarigar_data["completed_at"] = datetime.utcnow().isoformat()
                kaarigar_data["conversation_count"] = kaarigar_data.get("conversation_count", 0) + 1
                kaarigar_data["current_conversation_active"] = False
                
                # Store Cloud Storage URLs
                if "cloud_storage_urls" not in kaarigar_data:
                    kaarigar_data["cloud_storage_urls"] = {}
                
                if summary_url:
                    kaarigar_data["cloud_storage_urls"]["conversation_summary"] = summary_url
                
                if profile_url:
                    kaarigar_data["cloud_storage_urls"]["profile"] = profile_url
                
                if FIRESTORE_AVAILABLE:
                    try:
                        update_document(kaarigar_id, kaarigar_data)
                        print(f"✅ Kaarigar profile updated with completion data")
                        
                        # Clean up old conversations only after successful profile generation
                        cleanup_old_conversations(session.get('user_id'), kaarigar_id)
                    except Exception as e:
                        print(f"⚠️ Failed to update completed kaarigar profile: {e}")
                
                response_data["profile"] = profile_data
                response_data["profile_saved"] = True
                response_data["summary_url"] = summary_url
                response_data["profile_url"] = profile_url
                
            except Exception as e:
                print(f"❌ Profile/summary generation failed")
                response_data["profile_error"] = "Profile generation failed"
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"❌ Send audio message error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@conversational_bp.route('/status/<kaarigar_id>', methods=['GET'])
def get_conversation_status(kaarigar_id):
    """Get kaarigar profile status and data"""
    print(f"🔍 GET KAARIGAR STATUS: {kaarigar_id}")
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        if FIRESTORE_AVAILABLE:
            try:
                kaarigar_data = get_document(kaarigar_id)
                if not kaarigar_data:
                    return jsonify({"error": "Kaarigar profile not found"}), 404
                
                # Get user responses from conversation history
                user_responses = []
                if "conversation_history" in kaarigar_data:
                    user_responses = [turn["text"] for turn in kaarigar_data["conversation_history"] if turn.get("role") == "user"]
                
                return jsonify({
                    "success": True,
                    "kaarigar_id": kaarigar_id,
                    "brand_id": kaarigar_data.get("brand_id"),
                    "user_id": kaarigar_data.get("user_id"),
                    "status": kaarigar_data.get("status", "active"),
                    "user_response_count": len(user_responses),
                    "is_complete": len(user_responses) >= 6,
                    "preferred_language": kaarigar_data.get("preferred_language", "en"),
                    "profile": kaarigar_data.get("profile", {}),
                    "cloud_storage_urls": kaarigar_data.get("cloud_storage_urls", {}),
                    "conversation_count": kaarigar_data.get("conversation_count", 0),
                    "current_conversation_active": kaarigar_data.get("current_conversation_active", False),
                    "created_at": kaarigar_data.get("created_at"),
                    "completed_at": kaarigar_data.get("completed_at"),
                    "conversation_history": kaarigar_data.get("conversation_history", [])
                }), 200
                
            except Exception as e:
                print(f"❌ Failed to get conversation: {e}")
                return jsonify({"error": "Database error"}), 500
        else:
            return jsonify({"error": "Database not available"}), 500
        
    except Exception as e:
        print(f"❌ Get status error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@conversational_bp.route('/list', methods=['GET'])
def list_conversations():
    """List all kaarigar profiles for the current user"""
    print("📋 LIST KAARIGAR PROFILES REQUEST")
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = session.get('user_id')
        
        if FIRESTORE_AVAILABLE:
            try:
                kaarigar_profiles = query_documents("user_id", "==", user_id)
                
                profile_list = []
                for profile in kaarigar_profiles:
                    # Get user responses from conversation history
                    user_responses = []
                    if "conversation_history" in profile:
                        user_responses = [turn["text"] for turn in profile["conversation_history"] if turn.get("role") == "user"]
                    
                    profile_list.append({
                        "kaarigar_id": profile.get("kaarigar_id"),
                        "brand_id": profile.get("brand_id"),
                        "status": profile.get("status", "active"),
                        "user_response_count": len(user_responses),
                        "is_complete": len(user_responses) >= 6,
                        "conversation_count": profile.get("conversation_count", 0),
                        "current_conversation_active": profile.get("current_conversation_active", False),
                        "profile": profile.get("profile", {}),
                        "cloud_storage_urls": profile.get("cloud_storage_urls", {}),
                        "created_at": profile.get("created_at"),
                        "completed_at": profile.get("completed_at")
                    })
                
                return jsonify({
                    "success": True,
                    "kaarigar_profiles": profile_list
                }), 200
                
            except Exception as e:
                print(f"❌ Failed to list conversations: {e}")
                return jsonify({"error": "Database error"}), 500
        else:
            return jsonify({"error": "Database not available"}), 500
        
    except Exception as e:
        print(f"❌ List conversations error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@conversational_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "conversational",
        "firestore_available": FIRESTORE_AVAILABLE,
        "storage_available": STORAGE_AVAILABLE,
        "gemini_available": bool(GEMINI_API_KEY),
        "timestamp": datetime.utcnow().isoformat()
    }), 200
