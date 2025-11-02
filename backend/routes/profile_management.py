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
profile_bp = Blueprint('profile_bp', __name__)

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

def ensure_authenticated():
    """Ensure user is authenticated - check session or restore from header"""
    is_authenticated = session.get('is_authenticated', False)
    user_id_header = request.headers.get('X-User-ID')
    
    # If authenticated in session, return True
    if is_authenticated:
        return True
    
    # If not authenticated in session, try to restore from header
    if user_id_header:
        print(f"⚠️ Session not authenticated, trying X-User-ID header: {user_id_header}")
        
        # If Firestore is not available, trust the header (for offline/development)
        if not FIRESTORE_AVAILABLE:
            print(f"⚠️ Firestore not available, trusting X-User-ID header")
            session['user_id'] = user_id_header
            session['is_authenticated'] = True
            session.permanent = True
            return True
        
        try:
            user_doc = db.collection("users").document(user_id_header).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                # Restore session
                session['user_id'] = user_id_header
                session['email'] = user_data.get('email', '')
                session['name'] = user_data.get('name', '')
                session['is_authenticated'] = True
                session.permanent = True
                print(f"✅ Session restored from X-User-ID header")
                return True
            else:
                print(f"❌ User not found in database: {user_id_header}")
                return False
        except Exception as e:
            print(f"⚠️ Could not restore session from header: {e}")
            # If we can't verify but have a header, still allow (fallback)
            print(f"⚠️ Allowing authentication based on header despite error")
            session['user_id'] = user_id_header
            session['is_authenticated'] = True
            session.permanent = True
            return True
    
    return False

def get_user_from_session():
    """Get user ID from session or X-User-ID header"""
    # First try session (works for same-origin)
    user_id = session.get('user_id')
    
    # Fallback to header (works for cross-origin when cookies are blocked)
    if not user_id:
        user_id = request.headers.get('X-User-ID')
        if user_id:
            print(f"⚠️ Session cookie not found, using X-User-ID header: {user_id}")
            # Try to restore session from header
            try:
                user_doc = db.collection("users").document(user_id).get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    # Restore session for future requests
                    session['user_id'] = user_id
                    session['email'] = user_data.get('email', '')
                    session['name'] = user_data.get('name', '')
                    session['is_authenticated'] = True
                    session.permanent = True
                    print(f"✅ Session restored from X-User-ID header")
            except Exception as e:
                print(f"⚠️ Could not restore session from header: {e}")
    
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

def get_user_conversation_data(user_id: str) -> str:
    """Get user's conversation data from Firestore and Cloud Storage"""
    try:
        # Get kaarigar data
        kaarigar_id = f"KR_{user_id.upper()}"
        kaarigar_doc = db.collection("kaarigars").document(kaarigar_id).get()
        
        conversation_data = ""
        
        if kaarigar_doc.exists:
            kaarigar_data = kaarigar_doc.to_dict()
            
            # Get conversation history from Firestore
            conversation_history = kaarigar_data.get("conversation_history", [])
            if conversation_history:
                for msg in conversation_history:
                    if msg.get("sender") == "user":
                        conversation_data += f"User: {msg.get('text', '')}\n"
                    elif msg.get("sender") == "ai":
                        conversation_data += f"AI: {msg.get('text', '')}\n"
            
            # Try to get conversation data from Cloud Storage
            try:
                conversation_path = f"kaarigar/{kaarigar_id}/conversation/user_responses.txt"
                blob = bucket.blob(conversation_path)
                if blob.exists():
                    storage_data = blob.download_as_text()
                    conversation_data += f"\nStorage Data: {storage_data}"
            except Exception as e:
                print(f"⚠️ Could not fetch from storage: {e}")
        
        return conversation_data
    except Exception as e:
        print(f"❌ Error getting conversation data: {e}")
        return ""

def get_user_profile_from_storage(user_id: str) -> dict:
    """Get user's profile data from Cloud Storage JSON files"""
    try:
        print(f"🔍 Looking for profile data for user: {user_id}")
        
        # First, check the users collection for Cloud Storage URLs
        user_doc = db.collection("users").document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            print(f"📄 User document data keys: {list(user_data.keys())}")
            
            # Check for different possible structures
            profile_url = None
            
            # Try different possible structures
            if "cloud_storage_urls" in user_data:
                cloud_storage_urls = user_data.get("cloud_storage_urls", {})
                print(f"📄 Cloud Storage URLs structure: {cloud_storage_urls}")
                profile_url = cloud_storage_urls.get("profile")
            
            # Also try the old cloud_urls structure for backward compatibility
            if not profile_url and "cloud_urls" in user_data:
                cloud_urls = user_data.get("cloud_urls", {})
                print(f"📄 Cloud URLs structure: {cloud_urls}")
                profile_url = cloud_urls.get("profile")
            
            # Also check if profile URL is directly in user_data
            if not profile_url and "profile_url" in user_data:
                profile_url = user_data.get("profile_url")
                print(f"📄 Found profile_url directly: {profile_url}")
            
            # Check if there's a profile object with URL
            if not profile_url and "profile" in user_data:
                profile_obj = user_data.get("profile", {})
                if isinstance(profile_obj, dict):
                    profile_url = profile_obj.get("url") or profile_obj.get("cloud_url")
                    print(f"📄 Found profile object: {profile_obj}")
            
            if profile_url:
                print(f"🔗 Found profile URL: {profile_url}")
                try:
                    # Extract the path from the Cloud Storage URL
                    # URL format: https://storage.googleapis.com/bucket-name/path/to/file.json
                    if "storage.googleapis.com" in profile_url:
                        # Extract path after bucket name
                        url_parts = profile_url.split("/")
                        bucket_index = -1
                        for i, part in enumerate(url_parts):
                            if part == BUCKET_NAME:
                                bucket_index = i
                                break
                        
                        if bucket_index != -1 and bucket_index + 1 < len(url_parts):
                            profile_path = "/".join(url_parts[bucket_index + 1:])
                            print(f"📁 Extracted profile path: {profile_path}")
                            
                            # Fetch the JSON from Cloud Storage
                            blob = bucket.blob(profile_path)
                            if blob.exists():
                                profile_json = blob.download_as_text()
                                profile_data = json.loads(profile_json)
                                print(f"✅ Successfully loaded profile from Cloud Storage: {profile_data}")
                                return profile_data
                            else:
                                print(f"⚠️ Profile file not found at path: {profile_path}")
                        else:
                            print(f"⚠️ Could not extract path from URL: {profile_url}")
                    else:
                        print(f"⚠️ Invalid Cloud Storage URL format: {profile_url}")
                except Exception as e:
                    print(f"❌ Error fetching profile from Cloud Storage URL: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("⚠️ No profile URL found in any structure")
                print(f"📄 Available keys in user_data: {list(user_data.keys())}")
        else:
            print(f"⚠️ User document not found: {user_id}")
        
        # Fallback: Try to get profile data from kaarigar document
        kaarigar_id = f"KR_{user_id.upper()}"
        kaarigar_doc = db.collection("kaarigars").document(kaarigar_id).get()
        if kaarigar_doc.exists:
            kaarigar_data = kaarigar_doc.to_dict()
            print(f"📄 Kaarigar document keys: {list(kaarigar_data.keys())}")
            profile_data = kaarigar_data.get("profile", {})
            if profile_data:
                print(f"✅ Found profile data in kaarigar document as fallback: {profile_data}")
                return profile_data
        
        # Final fallback: Try common Cloud Storage paths
        profile_paths = [
            f"kaarigar/{kaarigar_id}/profile/profile.json",  # This is the correct path based on the URL
            f"kaarigar/{kaarigar_id}/profiles/profile.json",
            f"kaarigar/{kaarigar_id}/profile.json",
            f"profiles/{kaarigar_id}/profile.json"
        ]
        
        print(f"🔍 Trying fallback paths for kaarigar_id: {kaarigar_id}")
        for profile_path in profile_paths:
            try:
                print(f"📁 Checking path: {profile_path}")
                blob = bucket.blob(profile_path)
                if blob.exists():
                    print(f"✅ File exists at: {profile_path}")
                    profile_json = blob.download_as_text()
                    profile_data = json.loads(profile_json)
                    print(f"✅ Found profile data at fallback path: {profile_path}")
                    return profile_data
                else:
                    print(f"⚠️ File does not exist at: {profile_path}")
            except Exception as e:
                print(f"❌ Error fetching profile from {profile_path}: {e}")
                continue
        
        print("⚠️ No profile data found anywhere")
        return {}
        
    except Exception as e:
        print(f"❌ Error getting profile from storage: {e}")
        import traceback
        traceback.print_exc()
        return {}

def get_user_basic_info(user_id: str) -> dict:
    """Get basic user information from users collection"""
    try:
        user_doc = db.collection("users").document(user_id).get()
        if user_doc.exists:
            return user_doc.to_dict()
        return {}
    except Exception as e:
        print(f"❌ Error getting user info: {e}")
        return {}

def extract_occupation_with_gemini(profile_json: dict) -> str:
    """Use Gemini to extract occupation from conversation data"""
    try:
        # Prepare conversation data for occupation extraction
        conversation_data = ""
        
        # Combine all relevant text for occupation extraction
        if profile_json.get("Conversation Summary"):
            conversation_data += f"Conversation: {profile_json.get('Conversation Summary')}\n"
        if profile_json.get("Tagline"):
            conversation_data += f"Tagline: {profile_json.get('Tagline')}\n"
        if profile_json.get("Bio"):
            conversation_data += f"Bio: {profile_json.get('Bio')}\n"
        if profile_json.get("Materials Used"):
            conversation_data += f"Materials: {profile_json.get('Materials Used')}\n"
        
        if not conversation_data.strip():
            return "Artisan"  # Default fallback
        
        prompt = f"""
        Based on the following conversation and profile data, extract the person's specific occupation or craft.

        Data:
        {conversation_data}

        Rules:
        1. Look for specific craft types mentioned (handloom, pottery, woodwork, metalwork, etc.)
        2. If handloom is mentioned, return "Handloom Craftsman" or "Handloom Weaver"
        3. If pottery is mentioned, return "Potter" or "Ceramic Artist"
        4. If woodwork is mentioned, return "Woodworker" or "Carpenter"
        5. If metalwork is mentioned, return "Metalworker" or "Blacksmith"
        6. If textiles are mentioned, return "Textile Artist" or "Weaver"
        7. If no specific craft is mentioned, return "Artisan"
        8. Return ONLY the occupation name, no explanations

        Occupation:
        """

        response = call_gemini_raw(prompt, GEMINI_API_KEY, GEMINI_MODEL_NAME, max_output_tokens=50, temperature=0.1)
        
        if response and response.strip():
            occupation = response.strip()
            print(f"✅ Gemini extracted occupation: {occupation}")
            return occupation
        else:
            print("⚠️ Gemini failed to extract occupation, using default")
            return "Artisan"
            
    except Exception as e:
        print(f"❌ Error extracting occupation with Gemini: {e}")
        return "Artisan"

def extract_profile_from_json(profile_json: dict, user_data: dict) -> dict:
    """Extract profile data directly from the JSON structure with Gemini for occupation"""
    try:
        print(f"🔧 Extracting profile from JSON: {profile_json}")
        
        # Extract occupation using Gemini
        occupation = extract_occupation_with_gemini(profile_json)
        
        # Extract challenges from conversation summary if available
        challenges = ""
        conversation_summary = profile_json.get("Conversation Summary", "")
        if conversation_summary:
            # Try to extract challenges from the conversation summary
            if "challenge" in conversation_summary.lower():
                # Simple extraction - look for sentences with "challenge"
                sentences = conversation_summary.split(".")
                for sentence in sentences:
                    if "challenge" in sentence.lower():
                        challenges = sentence.strip()
                        break
        
        extracted_data = {
            "name": profile_json.get("Full Name", user_data.get("name", "")),
            "email": user_data.get("email", ""),
            "occupation": occupation,  # Now extracted with Gemini
            "bio": profile_json.get("Bio", ""),
            "location": profile_json.get("Location", ""),
            "languages": ["en", "hi"],  # Default, can be enhanced
            "craft_details": profile_json.get("Tagline", ""),
            "materials_used": profile_json.get("Materials Used", ""),
            "experience_years": "",  # Can be extracted from conversation
            "aspirations": profile_json.get("Aspiration", ""),
            "challenges": challenges
        }
        
        print(f"✅ Extracted profile data: {extracted_data}")
        return extracted_data
        
    except Exception as e:
        print(f"❌ Error extracting profile from JSON: {e}")
        return {}

def generate_profile_with_gemini(user_data: dict, conversation_data: str, profile_data: dict = None) -> dict:
    """Use Gemini to generate comprehensive profile from user data, conversation, and existing profile"""
    try:
        # Prepare input data
        user_info = json.dumps(user_data, indent=2)
        profile_info = json.dumps(profile_data, indent=2) if profile_data else "No existing profile data"
        
        prompt = f"""
        You are a profile data extraction assistant. Based on the user's basic information, conversation history, and existing profile data, extract and generate a comprehensive profile.

        User Basic Information:
        {user_info}

        Existing Profile Data (if available):
        {profile_info}

        Conversation History:
        {conversation_data}

        Please extract and return ONLY a JSON object with the following structure:
        {{
            "name": "Full name of the person",
            "email": "Email address",
            "occupation": "Primary occupation or craft",
            "bio": "Brief bio or description (2-3 sentences)",
            "location": "City, State, Country if mentioned",
            "languages": ["list", "of", "languages", "spoken"],
            "craft_details": "Details about their craft or work",
            "materials_used": "Materials or techniques they use",
            "experience_years": "Years of experience if mentioned",
            "aspirations": "Their goals or aspirations",
            "challenges": "Challenges they face"
        }}

        Rules:
        1. Prioritize existing profile data if available and valid
        2. Extract information from user data and conversation history
        3. If information is not available, use reasonable defaults or leave empty
        4. For name, use "Full Name" from profile data if available, otherwise from user data
        5. For bio, use "Bio" from profile data if available, otherwise generate from conversation
        6. For materials, use "Materials Used" from profile data if available
        7. For aspirations, use "Aspiration" from profile data if available
        8. For challenges, extract from conversation or use existing data
        9. Return ONLY valid JSON, no explanations
        """

        response = call_gemini_raw(prompt, GEMINI_API_KEY, GEMINI_MODEL_NAME, max_output_tokens=1024, temperature=0.3)
        extracted_data = extract_json_from_text(response)
        
        if extracted_data:
            return extracted_data
        else:
            # Fallback to existing profile data or basic user data
            if profile_data:
                return {
                    "name": profile_data.get("Full Name", user_data.get("name", "")),
                    "email": user_data.get("email", ""),
                    "occupation": "Artisan",
                    "bio": profile_data.get("Bio", f"Welcome! I'm {profile_data.get('Full Name', 'an artisan')}."),
                    "location": profile_data.get("Location", ""),
                    "languages": ["en", "hi"],
                    "craft_details": profile_data.get("Tagline", ""),
                    "materials_used": profile_data.get("Materials Used", ""),
                    "experience_years": "",
                    "aspirations": profile_data.get("Aspiration", ""),
                    "challenges": ""
                }
            else:
                return {
                    "name": user_data.get("name", ""),
                    "email": user_data.get("email", ""),
                    "occupation": "Artisan",
                    "bio": f"Welcome! I'm {user_data.get('name', 'an artisan')}.",
                    "location": "",
                    "languages": ["en", "hi"],
                    "craft_details": "",
                    "materials_used": "",
                    "experience_years": "",
                    "aspirations": "",
                    "challenges": ""
                }
    except Exception as e:
        print(f"❌ Error generating profile with Gemini: {e}")
        # Fallback to existing profile data or basic user data
        if profile_data:
            # Extract occupation using Gemini for fallback too
            occupation = extract_occupation_with_gemini(profile_data)
            return {
                "name": profile_data.get("Full Name", user_data.get("name", "")),
                "email": user_data.get("email", ""),
                "occupation": occupation,
                "bio": profile_data.get("Bio", f"Welcome! I'm {profile_data.get('Full Name', 'an artisan')}."),
                "location": profile_data.get("Location", ""),
                "languages": ["en", "hi"],
                "craft_details": profile_data.get("Tagline", ""),
                "materials_used": profile_data.get("Materials Used", ""),
                "experience_years": "",
                "aspirations": profile_data.get("Aspiration", ""),
                "challenges": ""
            }
        else:
            return {
                "name": user_data.get("name", ""),
                "email": user_data.get("email", ""),
                "occupation": "Artisan",
                "bio": f"Welcome! I'm {user_data.get('name', 'an artisan')}.",
                "location": "",
                "languages": ["en", "hi"],
                "craft_details": "",
                "materials_used": "",
                "experience_years": "",
                "aspirations": "",
                "challenges": ""
            }

@profile_bp.route('/get-profile-data', methods=['GET'])
def get_profile_data():
    """Get and generate profile data for the current user"""
    print("👤 GET PROFILE DATA REQUEST")
    try:
        if not ensure_authenticated():
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        print(f"👤 Getting profile data for user: {user_id}")
        
        if not FIRESTORE_AVAILABLE:
            return jsonify({"error": "Database not available"}), 500
        
        # Get basic user information
        user_data = get_user_basic_info(user_id)
        print(f"📋 User data: {user_data}")
        
        # Get existing profile data from Cloud Storage
        existing_profile = get_user_profile_from_storage(user_id)
        print(f"📄 Existing profile data: {existing_profile}")
        
        # If we have existing profile data, extract directly from JSON
        if existing_profile and existing_profile.get("Full Name"):
            profile_data = extract_profile_from_json(existing_profile, user_data)
            print(f"✅ Extracted profile from JSON: {profile_data}")
            
            # Save the extracted profile to the profiles collection for future use
            try:
                profile_id = f"profile_{user_id}"
                profile_ref = db.collection("profiles").document(profile_id)
                
                # Extract brand information from the Cloud Storage JSON
                brand_name = existing_profile.get("Brand Name", existing_profile.get("brand_name", ""))
                if not brand_name:
                    # Try to extract from conversation summary or other fields
                    conversation_summary = existing_profile.get("Conversation Summary", "")
                    if "brand" in conversation_summary.lower() and "kaarigar" in conversation_summary.lower():
                        brand_name = "Kaarigar"
                    else:
                        brand_name = profile_data.get("name", "Your Brand")
                
                # Check if there's a logo URL in the Cloud Storage JSON
                logo_url = existing_profile.get("Logo URL", existing_profile.get("logo_url", ""))
                if not logo_url:
                    # Try to construct logo URL from the known path pattern
                    kaarigar_id = f"KR_{user_id.upper()}"
                    # Look for logo files in the logos directory
                    try:
                        from google.cloud import storage
                        storage_client = storage.Client(project=PROJECT_ID)
                        bucket = storage_client.bucket(BUCKET_NAME)
                        
                        # List files in the logos directory
                        logo_prefix = f"kaarigar/{kaarigar_id}/logos/"
                        blobs = bucket.list_blobs(prefix=logo_prefix)
                        
                        # Find the most recent logo file
                        logo_files = [blob.name for blob in blobs if blob.name.endswith('.png')]
                        if logo_files:
                            # Sort by name (which includes timestamp) to get the most recent
                            logo_files.sort(reverse=True)
                            latest_logo = logo_files[0]
                            logo_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{latest_logo}"
                            print(f"🔗 Found logo URL: {logo_url}")
                        else:
                            print("⚠️ No logo files found in Cloud Storage")
                    except Exception as e:
                        print(f"⚠️ Error finding logo URL: {e}")
                        logo_url = "/ai_gen_logo.jpeg"  # Default fallback
                
                # Prepare profile data for saving
                save_data = {
                    "userId": user_id,
                    "name": profile_data.get("name", ""),
                    "email": profile_data.get("email", ""),
                    "occupation": profile_data.get("occupation", ""),
                    "bio": profile_data.get("bio", ""),
                    "location": profile_data.get("location", ""),
                    "languages": profile_data.get("languages", ["en"]),
                    "craft_details": profile_data.get("craft_details", ""),
                    "materials_used": profile_data.get("materials_used", ""),
                    "experience_years": profile_data.get("experience_years", ""),
                    "aspirations": profile_data.get("aspirations", ""),
                    "challenges": profile_data.get("challenges", ""),
                    # Brand information with actual logo URL
                    "brandName": brand_name,
                    "brandLogo": logo_url,  # Use the actual logo URL from Cloud Storage
                    "logoPrompt": f"Logo for {brand_name} - {profile_data.get('occupation', 'artisan')} brand",
                    "logoGeneratedAt": datetime.utcnow().isoformat(),
                    "lastUpdated": datetime.utcnow().isoformat(),
                    "isActive": True,
                    "source": "cloud_storage_extraction"
                }
                
                print(f"💾 Saving profile with logo URL: {logo_url}")
                print(f"🏷️ Brand name: {brand_name}")
                
                profile_ref.set(save_data)
                print(f"✅ Saved extracted profile to profiles collection: {profile_id}")
                
            except Exception as e:
                print(f"⚠️ Failed to save profile to profiles collection: {e}")
        else:
            # Get conversation data for Gemini processing
            conversation_data = get_user_conversation_data(user_id)
            print(f"💬 Conversation data length: {len(conversation_data)}")
            
            # Generate comprehensive profile using Gemini with existing profile data
            profile_data = generate_profile_with_gemini(user_data, conversation_data, existing_profile)
            print(f"✅ Generated profile with Gemini: {profile_data}")
        
        # Extract brand information for response
        brand_name = "Your Brand"  # Default
        logo_url = "/ai_gen_logo.jpeg"  # Default
        
        # Try to get brand name from existing profile data
        if existing_profile and existing_profile.get("Full Name"):
            brand_name = existing_profile.get("Brand Name", existing_profile.get("brand_name", ""))
            if not brand_name:
                # Try to extract from conversation summary
                conversation_summary = existing_profile.get("Conversation Summary", "")
                if "brand" in conversation_summary.lower() and "kaarigar" in conversation_summary.lower():
                    brand_name = "Kaarigar"
                else:
                    brand_name = profile_data.get("name", "Your Brand")
            
            # Try to get logo URL from Cloud Storage
            try:
                from google.cloud import storage
                storage_client = storage.Client(project=PROJECT_ID)
                bucket = storage_client.bucket(BUCKET_NAME)
                
                kaarigar_id = f"KR_{user_id.upper()}"
                logo_prefix = f"kaarigar/{kaarigar_id}/logos/"
                blobs = bucket.list_blobs(prefix=logo_prefix)
                
                logo_files = [blob.name for blob in blobs if blob.name.endswith('.png')]
                if logo_files:
                    logo_files.sort(reverse=True)
                    latest_logo = logo_files[0]
                    logo_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{latest_logo}"
                    print(f"🔗 Found logo URL for response: {logo_url}")
            except Exception as e:
                print(f"⚠️ Error finding logo URL for response: {e}")
        
        # Include brand information in the response
        brand_info = {
            "brand_name": brand_name,
            "logo_url": logo_url
        }
        
        print(f"📤 Sending brand info to frontend: {brand_info}")
        
        return jsonify({
            "success": True,
            "profile_data": profile_data,
            "user_id": user_id,
            "brand_info": brand_info
        })
        
    except ValueError as e:
        print(f"❌ Authentication error: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Error getting profile data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@profile_bp.route('/save-profile', methods=['POST'])
def save_profile():
    """Save profile data to Firestore"""
    print("💾 SAVE PROFILE REQUEST")
    try:
        if not ensure_authenticated():
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        print(f"👤 Saving profile for user: {user_id}")
        print(f"📋 Profile data: {data}")
        
        if not FIRESTORE_AVAILABLE:
            return jsonify({"error": "Database not available"}), 500
        
        # Get existing profile to preserve brand information
        profile_id = f"profile_{user_id}"
        profile_ref = db.collection("profiles").document(profile_id)
        existing_profile_doc = profile_ref.get()
        existing_brand_data = {}
        if existing_profile_doc.exists:
            existing_data = existing_profile_doc.to_dict()
            existing_brand_data = {
                "brandName": existing_data.get("brandName", ""),
                "brandLogo": existing_data.get("brandLogo", ""),
                "logoPrompt": existing_data.get("logoPrompt", ""),
                "logoGeneratedAt": existing_data.get("logoGeneratedAt", "")
            }
            print(f"📄 Preserving existing brand data: {existing_brand_data}")
        
        # Prepare profile data
        profile_data = {
            "userId": user_id,
            "name": data.get("name", ""),
            "email": data.get("email", ""),
            "occupation": data.get("occupation", ""),
            "bio": data.get("bio", ""),
            "location": data.get("location", ""),
            "languages": data.get("languages", ["en"]),
            "craft_details": data.get("craft_details", ""),
            "materials_used": data.get("materials_used", ""),
            "experience_years": data.get("experience_years", ""),
            "aspirations": data.get("aspirations", ""),
            "challenges": data.get("challenges", ""),
            "social_media": {
                "instagram": data.get("instagram", ""),
                "facebook": data.get("facebook", ""),
                "twitter": data.get("twitter", "")
            },
            "lastUpdated": datetime.utcnow().isoformat(),
            "isActive": True,
            # Preserve existing brand information
            **existing_brand_data
        }
        
        # Save to profiles collection
        profile_id = f"profile_{user_id}"
        profile_ref = db.collection("profiles").document(profile_id)
        
        print(f"💾 Saving profile data to Firestore...")
        print(f"   Profile ID: {profile_id}")
        print(f"   Data keys: {list(profile_data.keys())}")
        print(f"   Name: {profile_data.get('name', 'N/A')}")
        print(f"   Email: {profile_data.get('email', 'N/A')}")
        print(f"   Occupation: {profile_data.get('occupation', 'N/A')}")
        
        profile_ref.set(profile_data)
        print(f"✅ Profile saved to Firestore: {profile_id}")
        
        # Verify the save by reading it back
        verify_doc = profile_ref.get()
        if verify_doc.exists:
            verify_data = verify_doc.to_dict()
            print(f"✅ Profile verification successful: {verify_data.get('name', 'N/A')}")
        else:
            print("❌ Profile verification failed - document not found after save")
        
        # Also update kaarigar collection if exists
        kaarigar_id = f"KR_{user_id.upper()}"
        kaarigar_ref = db.collection("kaarigars").document(kaarigar_id)
        kaarigar_doc = kaarigar_ref.get()
        
        if kaarigar_doc.exists:
            kaarigar_data = kaarigar_doc.to_dict()
            kaarigar_data.update({
                "profile": profile_data,
                "lastUpdated": datetime.utcnow().isoformat()
            })
            kaarigar_ref.set(kaarigar_data)
            print(f"✅ Kaarigar profile updated: {kaarigar_id}")
        
        return jsonify({
            "success": True,
            "message": "Profile saved successfully",
            "profile_id": profile_id
        })
        
    except ValueError as e:
        print(f"❌ Authentication error: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Error saving profile: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@profile_bp.route('/get-saved-profile', methods=['GET'])
def get_saved_profile():
    """Get saved profile data for the current user"""
    print("🔍 GET SAVED PROFILE REQUEST")
    try:
        if not ensure_authenticated():
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        print(f"👤 Getting saved profile for user: {user_id}")
        
        if not FIRESTORE_AVAILABLE:
            return jsonify({"error": "Database not available"}), 500
        
        # Get profile from profiles collection
        profile_id = f"profile_{user_id}"
        profile_doc = db.collection("profiles").document(profile_id).get()
        
        if profile_doc.exists:
            profile_data = profile_doc.to_dict()
            print(f"✅ Found saved profile: {profile_id}")
            return jsonify({
                "success": True,
                "profile_data": profile_data
            })
        else:
            print(f"⚠️ No saved profile found for: {profile_id}")
            return jsonify({
                "success": False,
                "message": "No saved profile found"
            })
        
    except ValueError as e:
        print(f"❌ Authentication error: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Error getting saved profile: {e}")
        return jsonify({"error": "Internal server error"}), 500

@profile_bp.route('/update-brand', methods=['POST'])
def update_brand():
    """Update brand name and logo information"""
    print("🏷️ UPDATE BRAND REQUEST")
    try:
        if not ensure_authenticated():
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        brand_name = data.get("brand_name", "")
        brand_logo = data.get("brand_logo", "")
        
        print(f"👤 Updating brand for user: {user_id}")
        print(f"🏷️ Brand name: {brand_name}")
        print(f"🖼️ Brand logo: {brand_logo}")
        
        if not FIRESTORE_AVAILABLE:
            return jsonify({"error": "Database not available"}), 500
        
        # Update profile with brand information
        profile_id = f"profile_{user_id}"
        profile_ref = db.collection("profiles").document(profile_id)
        
        # Get existing profile data
        profile_doc = profile_ref.get()
        if profile_doc.exists:
            profile_data = profile_doc.to_dict()
        else:
            # Create new profile if it doesn't exist
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
                "source": "brand_update"
            }
        
        # Update brand information
        if brand_name:
            profile_data["brandName"] = brand_name
        if brand_logo:
            profile_data["brandLogo"] = brand_logo
        
        profile_data["lastUpdated"] = datetime.utcnow().isoformat()
        
        # Save updated profile
        profile_ref.set(profile_data)
        print(f"✅ Updated brand information for profile: {profile_id}")
        
        return jsonify({
            "success": True,
            "message": "Brand information updated successfully",
            "brand_name": brand_name,
            "brand_logo": brand_logo
        })
        
    except ValueError as e:
        print(f"❌ Authentication error: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Failed to update brand: {e}")
        return jsonify({"error": "Internal server error"}), 500

@profile_bp.route('/update-logo-from-storage', methods=['POST'])
def update_logo_from_storage():
    """Update logo URL from Cloud Storage for existing user"""
    print("🔄 UPDATE LOGO FROM STORAGE REQUEST")
    try:
        if not ensure_authenticated():
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        print(f"👤 Updating logo for user: {user_id}")
        
        if not FIRESTORE_AVAILABLE:
            return jsonify({"error": "Database not available"}), 500
        
        # Look for logo files in Cloud Storage
        kaarigar_id = f"KR_{user_id.upper()}"
        logo_url = None
        
        try:
            from google.cloud import storage
            storage_client = storage.Client(project=PROJECT_ID)
            bucket = storage_client.bucket(BUCKET_NAME)
            
            # List files in the logos directory
            logo_prefix = f"kaarigar/{kaarigar_id}/logos/"
            blobs = bucket.list_blobs(prefix=logo_prefix)
            
            # Find the most recent logo file
            logo_files = [blob.name for blob in blobs if blob.name.endswith('.png')]
            if logo_files:
                # Sort by name (which includes timestamp) to get the most recent
                logo_files.sort(reverse=True)
                latest_logo = logo_files[0]
                logo_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{latest_logo}"
                print(f"🔗 Found logo URL: {logo_url}")
            else:
                print("⚠️ No logo files found in Cloud Storage")
                return jsonify({"error": "No logo files found in Cloud Storage"}), 404
                
        except Exception as e:
            print(f"❌ Error finding logo URL: {e}")
            return jsonify({"error": f"Error accessing Cloud Storage: {e}"}), 500
        
        # Update the profile with the logo URL
        profile_id = f"profile_{user_id}"
        profile_ref = db.collection("profiles").document(profile_id)
        
        # Get existing profile data
        profile_doc = profile_ref.get()
        if not profile_doc.exists:
            return jsonify({"error": "Profile not found"}), 404
        
        profile_data = profile_doc.to_dict()
        
        # Update with logo information
        profile_data.update({
            "brandLogo": logo_url,
            "lastUpdated": datetime.utcnow().isoformat()
        })
        
        # Save updated profile
        profile_ref.set(profile_data)
        print(f"✅ Updated profile {profile_id} with logo URL: {logo_url}")
        
        return jsonify({
            "success": True,
            "message": "Logo URL updated successfully",
            "logo_url": logo_url,
            "profile_id": profile_id
        })
        
    except ValueError as e:
        print(f"❌ Authentication error: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Failed to update logo: {e}")
        return jsonify({"error": "Internal server error"}), 500

@profile_bp.route('/debug-user-data', methods=['GET'])
def debug_user_data():
    """Debug endpoint to show user data and Cloud Storage URLs"""
    print("🔍 DEBUG USER DATA REQUEST")
    try:
        if not ensure_authenticated():
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        print(f"👤 Debugging user data for: {user_id}")
        
        if not FIRESTORE_AVAILABLE:
            return jsonify({"error": "Database not available"}), 500
        
        # Get user document
        user_doc = db.collection("users").document(user_id).get()
        if not user_doc.exists:
            return jsonify({"error": "User not found"}), 404
        
        user_data = user_doc.to_dict()
        
        # Get kaarigar document
        kaarigar_id = f"KR_{user_id.upper()}"
        kaarigar_doc = db.collection("kaarigars").document(kaarigar_id).get()
        kaarigar_data = kaarigar_doc.to_dict() if kaarigar_doc.exists else {}
        
        # Try to get profile from Cloud Storage
        existing_profile = get_user_profile_from_storage(user_id)
        
        # Check for different possible profile URL structures
        profile_urls = {
            "cloud_storage_urls.profile": user_data.get("cloud_storage_urls", {}).get("profile"),
            "cloud_urls.profile": user_data.get("cloud_urls", {}).get("profile"),
            "profile_url": user_data.get("profile_url"),
            "profile.url": user_data.get("profile", {}).get("url") if isinstance(user_data.get("profile"), dict) else None,
            "profile.cloud_url": user_data.get("profile", {}).get("cloud_url") if isinstance(user_data.get("profile"), dict) else None
        }
        
        return jsonify({
            "success": True,
            "user_id": user_id,
            "kaarigar_id": kaarigar_id,
            "user_data_keys": list(user_data.keys()),
            "kaarigar_data_keys": list(kaarigar_data.keys()) if kaarigar_data else [],
            "cloud_storage_profile": existing_profile,
            "profile_urls": profile_urls,
            "user_data_sample": {k: str(v)[:100] + "..." if len(str(v)) > 100 else v for k, v in user_data.items()}
        })
        
    except ValueError as e:
        print(f"❌ Authentication error: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Error in debug endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@profile_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for profile management service"""
    return jsonify({
        "status": "healthy",
        "service": "Profile Management Service",
        "firestore_available": FIRESTORE_AVAILABLE,
        "storage_available": STORAGE_AVAILABLE,
        "gemini_available": bool(GEMINI_API_KEY),
        "timestamp": datetime.utcnow().isoformat()
    })
