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
import time
from pathlib import Path

# Add the parent directory to the path to import Database_Setup modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from google.cloud import firestore
    from google.cloud import storage
    from Database_Setup.firestore_nosql_storage import create_document, get_document, query_documents, update_document
    FIRESTORE_AVAILABLE = True
    STORAGE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Google Cloud services not available: {e}")
    FIRESTORE_AVAILABLE = False
    STORAGE_AVAILABLE = False

# Create blueprint
logo_bp = Blueprint('logo_bp', __name__)

# Configuration
PROJECT_ID = "karigar-475215"
BUCKET_NAME = "all_in_one_bucket1"

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

# Vertex AI configuration for Imagen
VERTEX_PROJECT = os.environ.get("VERTEX_PROJECT", "karigar-475215")
VERTEX_LOCATION = os.environ.get("VERTEX_LOCATION", "us-central1")
IMAGEN_MODEL = os.environ.get("IMAGEN_MODEL", "imagen-4.0-generate-001")

def get_user_from_session():
    """Get user ID from session"""
    user_id = session.get('user_id')
    if not user_id:
        raise ValueError("No user session found. Please login first.")
    return user_id

def call_gemini_raw(prompt: str, api_key: str, model_name: str = "gemini-2.0-flash", max_output_tokens: int = 1024, temperature: float = 0.0) -> str:
    """Call Gemini API with raw prompt"""
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

def extract_json_from_text(text: str) -> dict:
    """Extract JSON from text response"""
    try:
        # Try to find JSON in the text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        return {}
    except Exception as e:
        print(f"❌ JSON extraction failed: {e}")
        return {}

def slugify(value: str) -> str:
    """Convert string to URL-friendly slug"""
    if not value:
        return ""
    # Remove special characters and convert to lowercase
    slug = re.sub(r'[^\w\s-]', '', value.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def guess_brand_name_from_text(text: str) -> str:
    """Heuristically find a brand name in the transcript"""
    if not text:
        return "brand"
    
    # Common patterns for brand names
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
    
    # Fallback: try to find a capitalized word sequence
    m = re.search(r"([A-Z][a-z]{2,30}(?:\s+[A-Z][a-z]{2,30}){0,2})", text)
    if m:
        return m.group(1).strip()
    
    # Final fallback: first token that's >2 chars
    for token in re.split(r"\s+", text.strip()):
        tk = re.sub(r"[^A-Za-z0-9]", "", token)
        if len(tk) > 2:
            return tk
    return "brand"

def build_logo_prompt(brand_name: str, transcript: str, language: str = "en") -> str:
    """Create a compact, descriptive prompt for logo generation"""
    # Extract descriptors from transcript
    stopwords = set([
        "the", "and", "or", "a", "an", "is", "are", "to", "of", "in", "for",
        "with", "on", "my", "i", "we", "our", "this", "that", "it", "by"
    ])

    words = re.findall(r"\b[\w']{3,20}\b", transcript or "")
    descriptors = []
    for w in words:
        lw = w.lower()
        if lw in stopwords or lw.isdigit():
            continue
        if lw not in descriptors:
            descriptors.append(lw)
        if len(descriptors) >= 12:
            break

    desc_sample = ", ".join(descriptors[:8]) if descriptors else "handmade, artisanal"

    # Language-specific prompts
    if language == "hi":
        prompt = (
            f"ब्रांड '{brand_name}' के लिए लोगो डिज़ाइन। "
            f"साफ़, स्केलेबल, वेक्टर-स्टाइल लोगो बनाएं जो प्रिंट और डिजिटल दोनों के लिए उपयुक्त हो। "
            f"दृश्य शैली: न्यूनतम, आधुनिक, सपाट रंग; सरल आइकन जो दर्शाता है: {desc_sample}। "
            "ब्रांड नाम वर्डमार्क के रूप में शामिल करें (पठनीय sans-serif स्टाइल)। "
            "ब्रांड पहचान में उपयोग के लिए कई वैरिएंट प्रदान करें।"
        )
    else:
        # Default English
        prompt = (
            f"Logo design for a brand named '{brand_name}'. "
            f"Use a clean, scalable, vector-style logo suitable for print and digital use. "
            f"Visual style: minimal, modern, flat colors, simple icon that reflects: {desc_sample}. "
            "Include the brand name as a wordmark (prefer a readable sans-serif style). "
            "Deliver several distinct variations suitable for brand identity applications."
        )

    return prompt

def generate_logo_prompt_with_gemini(responses_input, gemini_api_key: str = None,
                                     gemini_model_name: str = None,
                                     temperature: float = 0.0,
                                     max_output_tokens: int = 512,
                                     input_language_iso: str = None) -> dict:
    """Use Gemini to generate logo prompt and brand name"""
    gemini_api_key = gemini_api_key or GEMINI_API_KEY
    gemini_model_name = gemini_model_name or GEMINI_MODEL_NAME
    language_iso = (input_language_iso or "en").lower()

    # Normalize input to string
    if isinstance(responses_input, (dict, list)):
        try:
            input_text = json.dumps(responses_input, ensure_ascii=False)
        except Exception:
            input_text = str(responses_input)
    else:
        input_text = str(responses_input or "")

    # Gemini instruction
    instruction = (
        "You are a prompt-engineer for image-generation. "
        "Input: a user interview transcript or JSON of user responses. "
        "Task: extract a single clear brand name (or propose a short ranked list) "
        "and produce a short, polished image-generation prompt optimized for a logo (vector, wordmark + icon, square aspect ratio).\n\n"
        "REQUIREMENTS:\n"
        " - Output ONLY a single valid JSON object and nothing else (no explanation).\n"
        " - Keys required where possible: brand_name, final_prompt.\n"
        " - Also include if available: candidates (list), short_description (one sentence), "
        "descriptors (list of short nouns/words), style_adjectives (list), color_palette (list).\n"
        " - The final_prompt must be concise (preferably <= 70 words) and suitable for a vector-style, minimal logo: mention 'square', 'vector', 'wordmark' if appropriate and include "
        "visual motifs derived from the descriptors (do not include long paragraphs or system commentary).\n"
        f" - IMPORTANT: Produce the JSON and the 'final_prompt' in the same language as the INPUT. "
        f"Input language ISO: {language_iso} (if you cannot produce a perfect translation, prefer the input language where possible).\n"
        " - If the transcript contains multiple possible brand names, pick the single most likely one for brand_name "
        "and return other options in candidates.\n\n"
        "Now parse the following interview content and return the requested JSON (only JSON):\n\n"
        f"INPUT (language ISO {language_iso}):\n{input_text}\n\n"
        "End of input."
    )

    try:
        if not gemini_api_key:
            raise RuntimeError("Gemini API key not set")
        
        raw = call_gemini_raw(prompt=instruction, api_key=gemini_api_key,
                              model_name=gemini_model_name,
                              max_output_tokens=max_output_tokens, temperature=temperature)
        parsed = extract_json_from_text(raw or "")
        
        # Normalize lists if strings
        if isinstance(parsed, dict) and parsed.get("final_prompt") and parsed.get("brand_name"):
            for k in ("candidates", "descriptors", "style_adjectives", "color_palette"):
                if k in parsed and isinstance(parsed[k], str):
                    parsed[k] = [s.strip() for s in re.split(r"[,\n;/]+", parsed[k]) if s.strip()]
            return parsed
    except Exception as e:
        print(f"❌ Gemini logo prompt generation failed: {e}")

    # Fallback to local heuristics
    heur_brand = guess_brand_name_from_text(input_text)
    heur_prompt = build_logo_prompt(heur_brand, input_text, language=language_iso)

    fallback = {
        "brand_name": heur_brand,
        "candidates": [heur_brand],
        "short_description": (input_text.strip().splitlines()[0][:200] if input_text else ""),
        "descriptors": [],
        "style_adjectives": ["minimal", "modern", "vector", "flat"],
        "color_palette": [],
        "final_prompt": heur_prompt
    }

    # Derive descriptors heuristically
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

def upload_logo_to_storage(image_data: bytes, user_id: str, brand_name: str) -> str:
    """Upload logo image to Cloud Storage and return public URL"""
    if not STORAGE_AVAILABLE:
        print("⚠️ Cloud Storage not available")
        return None
    
    try:
        # Create filename
        timestamp = int(time.time())
        filename = f"custom_logo_{user_id}_{timestamp}.png"
        storage_path = f"kaarigar/KR_{user_id.upper()}/logos/{filename}"
        
        # Upload to Cloud Storage
        blob = bucket.blob(storage_path)
        blob.upload_from_string(image_data, content_type="image/png")
        
        # Make the blob publicly accessible
        blob.make_public()
        
        # Generate public URL
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{storage_path}"
        print(f"✅ Logo uploaded to Cloud Storage: {storage_path}")
        print(f"🌐 Public URL: {public_url}")
        return public_url
    except Exception as e:
        print(f"❌ Cloud Storage upload failed: {e}")
        return None

def generate_logo_with_imagen(prompt: str, brand_name: str, user_id: str) -> str:
    """Generate logo using Google's Imagen model"""
    try:
        import google.genai as genai_local
        from google.genai.types import GenerateImagesConfig
    except Exception as e:
        print(f"⚠️ google.genai not available: {e}")
        return None

    # Create client for Vertex AI
    try:
        client = genai_local.Client(vertexai=True, project=VERTEX_PROJECT, location=VERTEX_LOCATION)
    except Exception:
        try:
            client = genai_local.Client()
        except Exception as e:
            print(f"⚠️ Failed to create google.genai Client: {e}")
            return None

    try:
        print(f"🎨 Generating image with model: {IMAGEN_MODEL}")
        print(f"📝 Prompt: {prompt[:100]}...")
        
        # Generate image
        cfg = GenerateImagesConfig(number_of_images=1, aspect_ratio="1:1")
        image = client.models.generate_images(
            model=IMAGEN_MODEL,
            prompt=prompt,
            config=cfg,
        )
        
        print(f"✅ Image generation completed, processing...")
        
        # Get first generated image
        gi = image.generated_images[0]
        print(f"📸 Generated image object: {type(gi)}")
        
        # Convert to bytes
        image_data = None
        try:
            # Try PIL-like interface first
            print("🔄 Trying PIL-like interface...")
            img_bytes = io.BytesIO()
            gi.image.save(img_bytes, format='PNG')
            image_data = img_bytes.getvalue()
            print(f"✅ PIL interface successful, image size: {len(image_data)} bytes")
        except Exception as pil_error:
            print(f"⚠️ PIL interface failed: {pil_error}")
            # Try raw bytes
            try:
                print("🔄 Trying raw bytes interface...")
                image_data = gi.image.image_bytes
                print(f"✅ Raw bytes successful, image size: {len(image_data)} bytes")
            except Exception as bytes_error:
                print(f"❌ Raw bytes failed: {bytes_error}")
                return None
        
        if not image_data:
            print("❌ No image data extracted")
            return None
        
        # Upload to Cloud Storage
        print("☁️ Uploading to Cloud Storage...")
        logo_url = upload_logo_to_storage(image_data, user_id, brand_name)
        
        if logo_url:
            print(f"✅ Logo uploaded successfully: {logo_url}")
        else:
            print("❌ Cloud Storage upload failed")
            
        return logo_url
        
    except Exception as e:
        print(f"❌ Logo generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def update_user_profile_with_logo(user_id: str, logo_url: str, brand_name: str, logo_prompt: str):
    """Update user profile in Firestore with logo information"""
    if not FIRESTORE_AVAILABLE:
        print("⚠️ Firestore not available")
        return False
    
    try:
        # Update profile collection
        profile_id = f"profile_{user_id}"
        profile_ref = db.collection("profiles").document(profile_id)
        
        # Get existing profile data
        profile_doc = profile_ref.get()
        if profile_doc.exists:
            profile_data = profile_doc.to_dict()
            print(f"📄 Found existing profile data: {list(profile_data.keys())}")
        else:
            # Create new profile with basic structure
            profile_data = {
                "userId": user_id,
                "name": "",
                "email": "",
                "occupation": "",
                "bio": "",
                "location": "",
                "languages": ["en"],
                "craft_details": "",
                "materials_used": "",
                "experience_years": "",
                "aspirations": "",
                "challenges": "",
                "isActive": True,
                "source": "logo_generation"
            }
            print(f"📄 Creating new profile for user: {user_id}")
        
        # Update with logo information
        profile_data.update({
            "brandLogo": logo_url,
            "brandName": brand_name,
            "logoPrompt": logo_prompt,
            "logoGeneratedAt": datetime.utcnow().isoformat(),
            "lastUpdated": datetime.utcnow().isoformat()
        })
        
        # Save updated profile
        profile_ref.set(profile_data)
        print(f"✅ Updated profile {profile_id} with logo information")
        print(f"   Brand Name: {brand_name}")
        print(f"   Logo URL: {logo_url}")
        print(f"   Profile fields: {list(profile_data.keys())}")
        
        # Also update kaarigar collection if exists
        kaarigar_id = f"KR_{user_id.upper()}"
        kaarigar_ref = db.collection("kaarigars").document(kaarigar_id)
        kaarigar_doc = kaarigar_ref.get()
        
        if kaarigar_doc.exists:
            kaarigar_data = kaarigar_doc.to_dict()
            kaarigar_data.update({
                "brandLogo": logo_url,
                "brandName": brand_name,
                "logoPrompt": logo_prompt,
                "logoGeneratedAt": datetime.utcnow().isoformat()
            })
            kaarigar_ref.set(kaarigar_data)
            print(f"✅ Updated kaarigar {kaarigar_id} with logo information")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to update profile with logo: {e}")
        return False

@logo_bp.route('/generate', methods=['POST'])
def generate_logo():
    """Generate logo for user based on their conversation data"""
    print("🎨 LOGO GENERATION REQUEST")
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        print(f"👤 Generating logo for user: {user_id}")
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get conversation data or text input
        conversation_data = data.get('conversation_data', '')
        brand_name = data.get('brand_name', '')
        language = data.get('language', 'en')
        
        if not conversation_data:
            return jsonify({"error": "No conversation data provided"}), 400
        
        print(f"📝 Processing conversation data: {len(conversation_data)} characters")
        print(f"🏷️ Brand name: {brand_name}")
        print(f"🌐 Language: {language}")
        
        # Generate logo prompt using Gemini
        logo_spec = generate_logo_prompt_with_gemini(
            conversation_data,
            gemini_api_key=GEMINI_API_KEY,
            gemini_model_name=GEMINI_MODEL_NAME,
            input_language_iso=language
        )
        
        if not logo_spec or not isinstance(logo_spec, dict):
            return jsonify({"error": "Failed to generate logo prompt"}), 500
        
        # Extract brand name and prompt
        final_brand_name = logo_spec.get("brand_name") or brand_name or guess_brand_name_from_text(conversation_data)
        final_prompt = logo_spec.get("final_prompt") or build_logo_prompt(final_brand_name, conversation_data, language)
        
        print(f"✅ Generated logo specification:")
        print(f"   Brand: {final_brand_name}")
        print(f"   Prompt: {final_prompt[:100]}...")
        
        # Generate logo using Imagen
        print(f"🎨 Attempting to generate logo with Imagen...")
        logo_url = generate_logo_with_imagen(final_prompt, final_brand_name, user_id)
        
        if not logo_url:
            print("❌ Imagen generation failed, trying fallback...")
            # Fallback: Create a simple logo using a placeholder service or return error
            return jsonify({
                "error": "Logo generation service is currently unavailable. Please try again later.",
                "details": "Imagen API failed to generate logo"
            }), 500
        
        # Update user profile with logo information
        print(f"💾 Updating profile with logo information...")
        print(f"   User ID: {user_id}")
        print(f"   Logo URL: {logo_url}")
        print(f"   Brand Name: {final_brand_name}")
        
        success = update_user_profile_with_logo(user_id, logo_url, final_brand_name, final_prompt)
        
        if success:
            print("✅ Profile updated successfully with logo information")
        else:
            print("⚠️ Logo generated but failed to update profile")
        
        # Return success response
        response_data = {
            "success": True,
            "message": "Logo generated successfully",
            "logo_url": logo_url,
            "brand_name": final_brand_name,
            "logo_prompt": final_prompt,
            "logo_spec": logo_spec
        }
        
        print(f"🎉 Logo generation completed for user {user_id}")
        return jsonify(response_data)
        
    except ValueError as e:
        print(f"❌ Authentication error: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Logo generation failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@logo_bp.route('/get-logo', methods=['GET'])
def get_user_logo():
    """Get user's current logo information"""
    print("🔍 GET LOGO REQUEST")
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        print(f"👤 Getting logo for user: {user_id}")
        
        if not FIRESTORE_AVAILABLE:
            return jsonify({"error": "Database not available"}), 500
        
        # Get profile data
        profile_id = f"profile_{user_id}"
        profile_ref = db.collection("profiles").document(profile_id)
        profile_doc = profile_ref.get()
        
        if not profile_doc.exists:
            return jsonify({"error": "Profile not found"}), 404
        
        profile_data = profile_doc.to_dict()
        
        # Extract logo information
        logo_info = {
            "logo_url": profile_data.get("brandLogo"),
            "brand_name": profile_data.get("brandName"),
            "logo_prompt": profile_data.get("logoPrompt"),
            "logo_generated_at": profile_data.get("logoGeneratedAt"),
            "has_logo": bool(profile_data.get("brandLogo"))
        }
        
        print(f"✅ Retrieved logo info for user {user_id}")
        return jsonify({
            "success": True,
            "logo_info": logo_info
        })
        
    except ValueError as e:
        print(f"❌ Authentication error: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Failed to get logo: {e}")
        return jsonify({"error": "Internal server error"}), 500

@logo_bp.route('/save-logo-url', methods=['POST'])
def save_logo_url():
    """Manually save a logo URL to the profiles collection"""
    print("💾 SAVE LOGO URL REQUEST")
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        logo_url = data.get("logo_url", "")
        brand_name = data.get("brand_name", "")
        
        if not logo_url:
            return jsonify({"error": "Logo URL is required"}), 400
        
        print(f"👤 Saving logo URL for user: {user_id}")
        print(f"🖼️ Logo URL: {logo_url}")
        print(f"🏷️ Brand Name: {brand_name}")
        
        if not FIRESTORE_AVAILABLE:
            return jsonify({"error": "Database not available"}), 500
        
        # Update profile with logo information
        success = update_user_profile_with_logo(user_id, logo_url, brand_name, f"Manual logo for {brand_name}")
        
        if success:
            return jsonify({
                "success": True,
                "message": "Logo URL saved successfully",
                "logo_url": logo_url,
                "brand_name": brand_name
            })
        else:
            return jsonify({"error": "Failed to save logo URL"}), 500
        
    except ValueError as e:
        print(f"❌ Authentication error: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Failed to save logo URL: {e}")
        return jsonify({"error": "Internal server error"}), 500

@logo_bp.route('/test-imagen', methods=['GET'])
def test_imagen():
    """Test if Imagen API is working"""
    try:
        import google.genai as genai_local
        from google.genai.types import GenerateImagesConfig
        print("✅ google.genai imported successfully")
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"google.genai import failed: {e}",
            "imagen_available": False
        }), 500

    try:
        # Test client creation
        client = genai_local.Client(vertexai=True, project=VERTEX_PROJECT, location=VERTEX_LOCATION)
        print("✅ Imagen client created successfully")
        
        return jsonify({
            "status": "success",
            "message": "Imagen API is available",
            "imagen_available": True,
            "model": IMAGEN_MODEL,
            "project": VERTEX_PROJECT,
            "location": VERTEX_LOCATION
        })
    except Exception as e:
        print(f"❌ Imagen client creation failed: {e}")
        return jsonify({
            "status": "error",
            "message": f"Imagen client creation failed: {e}",
            "imagen_available": False
        }), 500

@logo_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for logo generation service"""
    return jsonify({
        "status": "healthy",
        "service": "Logo Generation Service",
        "firestore_available": FIRESTORE_AVAILABLE,
        "storage_available": STORAGE_AVAILABLE,
        "gemini_available": bool(GEMINI_API_KEY),
        "timestamp": datetime.utcnow().isoformat()
    })
