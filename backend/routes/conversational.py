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
PROJECT_ID = "useful-figure-475210-g7"
BUCKET_NAME = "all_in_one_bucket"
COLLECTION_NAME = "kaarigar"

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

def generate_kaarigar_id():
    """Generate a unique kaarigar ID"""
    return f"KR_{uuid.uuid4().hex[:8].upper()}"

def generate_brand_id():
    """Generate a unique brand ID"""
    return f"BRAND_{uuid.uuid4().hex[:8].upper()}"

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
    """Upload data to Cloud Storage"""
    if not STORAGE_AVAILABLE:
        print("⚠️ Cloud Storage not available")
        return None
    
    try:
        blob = bucket.blob(path)
        blob.upload_from_string(data, content_type=content_type)
        print(f"✅ Uploaded to Cloud Storage: {path}")
        return f"gs://{BUCKET_NAME}/{path}"
    except Exception as e:
        print(f"❌ Cloud Storage upload failed: {e}")
        return None

def save_conversation_to_storage(conversation_data: dict, kaarigar_id: str) -> str:
    """Save conversation data to Cloud Storage"""
    try:
        # Save conversation history
        conversation_path = f"kaarigar/{kaarigar_id}/conversation/history.json"
        conversation_json = json.dumps(conversation_data, ensure_ascii=False, indent=2)
        upload_to_cloud_storage(conversation_json, conversation_path, "application/json")
        
        # Save user responses as text
        user_responses = [turn["text"] for turn in conversation_data.get("history", []) if turn.get("role") == "user"]
        responses_text = "\n".join([f"User Response {i+1}: {resp}" for i, resp in enumerate(user_responses)])
        responses_path = f"kaarigar/{kaarigar_id}/conversation/user_responses.txt"
        upload_to_cloud_storage(responses_text, responses_path, "text/plain")
        
        return conversation_path
    except Exception as e:
        print(f"❌ Failed to save conversation to storage: {e}")
        return None

def generate_profile_from_responses(user_responses: list, gemini_api_key: str = None, 
                                  gemini_model_name: str = None, input_language_iso: str = None) -> dict:
    """Generate profile from user responses using Gemini"""
    gemini_api_key = gemini_api_key or GEMINI_API_KEY
    gemini_model_name = gemini_model_name or GEMINI_MODEL_NAME

    if not gemini_api_key:
        print("⚠️ Gemini API key not available")
        return {}

    # Create conversation text
    convo_text = "\n".join([f"User Response {i+1}: {resp}" for i, resp in enumerate(user_responses)])
    
    prompt = (
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
    
    try:
        gemini_out = call_gemini_raw(prompt=prompt, api_key=gemini_api_key, model_name=gemini_model_name, max_output_tokens=512, temperature=0.0)
        
        # Extract JSON from response
        try:
            start = gemini_out.find("{")
            end = gemini_out.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = gemini_out[start:end+1]
                parsed = json.loads(candidate)
            else:
                parsed = json.loads(gemini_out)
        except Exception:
            parsed = {}
    except Exception as e:
        print(f"❌ Profile generation failed: {e}")
        parsed = {}

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
        "Aspiration": aspiration or ""
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
        kaarigar_id = generate_kaarigar_id()
        brand_id = generate_brand_id()
        
        # Create initial conversation data
        conversation_data = {
            "kaarigar_id": kaarigar_id,
            "brand_id": brand_id,
            "user_id": user_id,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "history": [],
            "user_responses": [],
            "preferred_language": "en"
        }
        
        # Save to Firestore
        if FIRESTORE_AVAILABLE:
            try:
                create_document(conversation_data, kaarigar_id)
                print(f"✅ Conversation started: {kaarigar_id}")
            except Exception as e:
                print(f"❌ Failed to save conversation to Firestore: {e}")
                return jsonify({"error": "Failed to start conversation"}), 500
        
        # Generate initial AI message
        initial_prompt = f"{SYSTEM_PROMPT}\n\nPreferred_language: en\n\nNew user message:\nHello\n\nAs the assistant, provide the first greeting in English. Keep it short and welcoming."
        ai_response = call_gemini_raw(initial_prompt, GEMINI_API_KEY, GEMINI_MODEL_NAME, temperature=0.6)
        
        # Add initial AI message to history
        conversation_data["history"].append({
            "role": "assistant",
            "text": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Update Firestore
        if FIRESTORE_AVAILABLE:
            try:
                from Database_Setup.firestore_nosql_storage import update_document
                update_document(kaarigar_id, conversation_data)
            except Exception as e:
                print(f"⚠️ Failed to update conversation: {e}")
        
        return jsonify({
            "success": True,
            "kaarigar_id": kaarigar_id,
            "brand_id": brand_id,
            "ai_message": ai_response,
            "conversation_data": conversation_data
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
        
        # Get conversation from Firestore
        if FIRESTORE_AVAILABLE:
            try:
                conversation = get_document(kaarigar_id)
                if not conversation:
                    return jsonify({"error": "Conversation not found"}), 404
            except Exception as e:
                print(f"❌ Failed to get conversation: {e}")
                return jsonify({"error": "Database error"}), 500
        else:
            return jsonify({"error": "Database not available"}), 500
        
        # Add user message to history
        conversation["history"].append({
            "role": "user",
            "text": user_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Detect language
        preferred_language = detect_preferred_language_from_text(user_message)
        conversation["preferred_language"] = preferred_language
        
        # Generate AI response
        prompt = build_prompt_from_history(
            SYSTEM_PROMPT, 
            conversation["history"], 
            user_message, 
            preferred_language
        )
        
        ai_response = call_gemini_raw(prompt, GEMINI_API_KEY, GEMINI_MODEL_NAME, temperature=0.6)
        
        # Add AI response to history
        conversation["history"].append({
            "role": "assistant",
            "text": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Update conversation in Firestore
        if FIRESTORE_AVAILABLE:
            try:
                from Database_Setup.firestore_nosql_storage import update_document
                update_document(kaarigar_id, conversation)
            except Exception as e:
                print(f"❌ Failed to update conversation: {e}")
        
        # Check if conversation is complete (6+ user responses)
        user_responses = [turn["text"] for turn in conversation["history"] if turn.get("role") == "user"]
        is_complete = len(user_responses) >= 6
        
        response_data = {
            "success": True,
            "ai_message": ai_response,
            "is_complete": is_complete,
            "user_response_count": len(user_responses)
        }
        
        # If conversation is complete, generate profile
        if is_complete:
            print("✅ Conversation complete - generating profile")
            try:
                profile = generate_profile_from_responses(user_responses, GEMINI_API_KEY, GEMINI_MODEL_NAME, preferred_language)
                
                # Save profile to Cloud Storage
                if STORAGE_AVAILABLE:
                    profile_path = f"kaarigar/{kaarigar_id}/profile/profile.json"
                    profile_json = json.dumps(profile, ensure_ascii=False, indent=2)
                    upload_to_cloud_storage(profile_json, profile_path, "application/json")
                    
                    # Save conversation to storage
                    save_conversation_to_storage(conversation, kaarigar_id)
                
                # Update conversation status
                conversation["status"] = "completed"
                conversation["profile"] = profile
                conversation["completed_at"] = datetime.utcnow().isoformat()
                
                if FIRESTORE_AVAILABLE:
                    try:
                        update_document(kaarigar_id, conversation)
                    except Exception as e:
                        print(f"⚠️ Failed to update completed conversation: {e}")
                
                response_data["profile"] = profile
                response_data["profile_saved"] = True
                
            except Exception as e:
                print(f"❌ Profile generation failed: {e}")
                response_data["profile_error"] = str(e)
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"❌ Send message error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@conversational_bp.route('/status/<kaarigar_id>', methods=['GET'])
def get_conversation_status(kaarigar_id):
    """Get conversation status and data"""
    print(f"🔍 GET CONVERSATION STATUS: {kaarigar_id}")
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        if FIRESTORE_AVAILABLE:
            try:
                conversation = get_document(kaarigar_id)
                if not conversation:
                    return jsonify({"error": "Conversation not found"}), 404
                
                user_responses = [turn["text"] for turn in conversation.get("history", []) if turn.get("role") == "user"]
                
                return jsonify({
                    "success": True,
                    "kaarigar_id": kaarigar_id,
                    "status": conversation.get("status", "active"),
                    "user_response_count": len(user_responses),
                    "is_complete": len(user_responses) >= 6,
                    "preferred_language": conversation.get("preferred_language", "en"),
                    "created_at": conversation.get("created_at"),
                    "completed_at": conversation.get("completed_at"),
                    "profile": conversation.get("profile")
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
    """List all conversations for the current user"""
    print("📋 LIST CONVERSATIONS REQUEST")
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = session.get('user_id')
        
        if FIRESTORE_AVAILABLE:
            try:
                conversations = query_documents("user_id", "==", user_id)
                
                conversation_list = []
                for conv in conversations:
                    user_responses = [turn["text"] for turn in conv.get("history", []) if turn.get("role") == "user"]
                    conversation_list.append({
                        "kaarigar_id": conv.get("kaarigar_id"),
                        "brand_id": conv.get("brand_id"),
                        "status": conv.get("status", "active"),
                        "user_response_count": len(user_responses),
                        "is_complete": len(user_responses) >= 6,
                        "created_at": conv.get("created_at"),
                        "completed_at": conv.get("completed_at")
                    })
                
                return jsonify({
                    "success": True,
                    "conversations": conversation_list
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
