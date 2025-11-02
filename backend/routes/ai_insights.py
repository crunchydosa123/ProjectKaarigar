from flask import Blueprint, request, jsonify, session
from flask_cors import CORS
import sys
import os
import json
import traceback
from datetime import datetime
import tempfile
import subprocess

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from google.cloud import firestore
    from google.cloud import storage
    import google.generativeai as gtext
    from google import genai
    from google.genai.types import GenerateImagesConfig
    import requests
    FIRESTORE_AVAILABLE = True
    STORAGE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Google Cloud services not available: {e}")
    FIRESTORE_AVAILABLE = False
    STORAGE_AVAILABLE = False

# Create blueprint
ai_insights_bp = Blueprint('ai_insights_bp', __name__)

# Enable CORS for this blueprint
CORS(ai_insights_bp, origins='*', supports_credentials=True)

# Configuration
PROJECT_ID = "karigar-475215"
BUCKET_NAME = "all_in_one_bucket1"
GCS_IMAGES_PREFIX = "ai_insights_images"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TEXT_MODEL = "gemini-2.0-flash-exp"

# Google Custom Search configuration
GOOGLE_API_KEY = ""
GOOGLE_CX = ""
MAX_SEARCH_QUERIES = 4
RESULTS_PER_QUERY = 3
REQUEST_TIMEOUT = 10

# Multiple image generation API keys for rate limiting (rotate every 2 images)
IMAGE_API_KEYS = [
    "",
    "",
    ""
]

# Google Custom Search for links
GOOGLE_SEARCH_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_SEARCH_CX = os.environ.get("GOOGLE_CX")

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

# Import the shared auth helper
import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(__file__)))
from auth_helper import get_user_from_session

def get_user_profile_data(user_id: str) -> dict:
    """Get user profile data from Firestore and Cloud Storage including products"""
    try:
        print(f"🔍 Getting profile data for user: {user_id}")
        
        # Get kaarigar data
        kaarigar_id = f"KR_{user_id.upper()}"
        kaarigar_doc = db.collection("kaarigars").document(kaarigar_id).get()
        
        profile_data = {}
        
        if kaarigar_doc.exists:
            data = kaarigar_doc.to_dict()
            
            # Try to get profile from Cloud Storage URL
            if data.get("profile_url"):
                try:
                    blob = bucket.blob(data["profile_url"].replace(f"gs://{BUCKET_NAME}/", ""))
                    profile_json = json.loads(blob.download_as_text())
                    profile_data = profile_json
                except Exception as e:
                    print(f"⚠️ Could not load profile from storage: {e}")
            
            # Fallback to document data
            if not profile_data:
                profile_data = {
                    "name": data.get("name", ""),
                    "craft": data.get("occupation", "artisan"),
                    "location": data.get("location", ""),
                    "bio": data.get("bio", ""),
                    "materials": data.get("materials_used", ""),
                    "experience": data.get("experience_years", ""),
                    "aspirations": data.get("aspirations", "")
                }
        
        # Try to get from users collection as fallback
        if not profile_data or not profile_data.get("name"):
            user_doc = db.collection("users").document(user_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                profile_data["name"] = profile_data.get("name") or user_data.get("name", "Artisan")
                profile_data["email"] = user_data.get("email", "")
        
        # Fetch user's products for more specific insights
        try:
            print(f"🛍️ Fetching products for user: {user_id}")
            products_ref = db.collection("products").where("user_id", "==", user_id).limit(10)
            products_docs = products_ref.stream()
            
            products = []
            for doc in products_docs:
                product_data = doc.to_dict()
                products.append({
                    "name": product_data.get("name", ""),
                    "description": product_data.get("description", ""),
                    "category": product_data.get("category", ""),
                    "price": product_data.get("price", ""),
                    "materials": product_data.get("materials", ""),
                })
            
            profile_data["products"] = products
            print(f"✅ Found {len(products)} products")
        except Exception as e:
            print(f"⚠️ Could not load products: {e}")
            profile_data["products"] = []
        
        return profile_data
        
    except Exception as e:
        print(f"❌ Error getting profile data: {e}")
        traceback.print_exc()
        return {"name": "Artisan", "craft": "handicraft"}

def call_gemini_for_insights(profile: dict) -> dict:
    """Generate 6 AI insights using Gemini"""
    try:
        print(f"📊 Profile data received: {json.dumps(profile, indent=2)}")
        
        gtext.configure(api_key=GEMINI_API_KEY)
        print(f"✅ Gemini API configured with key: {GEMINI_API_KEY[:20]}...")
        
        profile_json = json.dumps(profile, ensure_ascii=False)
        
        system_prompt = (
            "You are an experienced business & craft advisor for local artisans (Kaarigars). "
            "Provide practical, data-driven, and motivating advice. RETURN ONLY A JSON OBJECT and nothing else. "
            "The JSON must have a single key 'insights' whose value is an array of exactly six objects. "
            "Each object must have two keys: 'title' and 'text'. "
            " - 'title' should be a 5-6 word description summarizing the insight (concise phrase). "
            " - 'text' should be 3-5 actionable bullet points (NOT a paragraph). Each bullet point should be on a new line starting with '• '. "
            "   Make each bullet point SPECIFIC to the user's profile, products, location, materials, and craft. "
            "   Include concrete numbers, product names, regional opportunities, material suggestions, etc. "
            "   DO NOT give generic advice - use the actual product names, craft type, and location from the profile.\n"
            "Do NOT include extra keys or commentary outside the JSON.\n"
            "Topics (in order):\n"
            "1) Government schemes or initiatives specific to their craft and location\n"
            "2) Current sales trends and market demand for their specific products\n"
            "3) Opportunities to expand online and offline reach for their products\n"
            "4) Suggestions for improving their specific product quality, design, or branding\n"
            "5) Financial or training programs they can benefit from based on their craft\n"
            "6) Future trends and innovations relevant to their specific craft and products\n"
        )
        
        user_prompt = (
            f"PROFILE: {profile_json}\n\n"
            "Task: Based on the PROFILE produce 6 actionable, motivating advisory entries as described above."
            " CRITICAL: Make each bullet point HIGHLY SPECIFIC using:\n"
            " - Actual product names from the products array\n"
            " - Specific craft type and materials mentioned\n"
            " - Regional location for local schemes/markets\n"
            " - Price ranges and target markets\n"
            " - Experience level for appropriate recommendations\n"
            " Format each 'text' field as 3-5 bullet points starting with '• ' on separate lines.\n"
            " Keep tone encouraging and growth-focused with actionable steps."
        )
        
        print(f"📝 Calling Gemini model: {TEXT_MODEL}")
        model = gtext.GenerativeModel(TEXT_MODEL)
        prompt = f"{system_prompt}\n\n{user_prompt}"
        
        print(f"🚀 Sending prompt to Gemini (length: {len(prompt)} chars)")
        resp = model.generate_content(prompt)
        
        print(f"📥 Gemini response received: {resp}")
        print(f"📥 Response type: {type(resp)}")
        
        # Try to get text from response
        text = None
        if hasattr(resp, "text"):
            text = resp.text
            print(f"✅ Got text from resp.text: {text[:200]}...")
        elif hasattr(resp, "parts"):
            print(f"📦 Response has parts: {resp.parts}")
            if resp.parts:
                text = resp.parts[0].text
                print(f"✅ Got text from parts[0]: {text[:200]}...")
        
        if not text:
            text = str(resp)
            print(f"⚠️ Falling back to str(resp): {text[:200]}...")
        
        print(f"📄 Full response text:\n{text}\n")
        
        # Try to extract JSON from text (in case there's markdown formatting)
        if "```json" in text:
            print("🔧 Extracting JSON from markdown code block")
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            print("🔧 Extracting JSON from generic code block")
            text = text.split("```")[1].split("```")[0].strip()
        
        print(f"🔍 Attempting to parse JSON: {text[:200]}...")
        parsed = json.loads(text)
        print(f"✅ Successfully parsed JSON with {len(parsed.get('insights', []))} insights")
        
        return parsed
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"❌ Text that failed to parse: {text if 'text' in locals() else 'No text available'}")
        traceback.print_exc()
        return {"insights": []}
    except Exception as e:
        print(f"❌ Gemini call failed: {e}")
        print(f"❌ Error type: {type(e)}")
        traceback.print_exc()
        return {"insights": []}

def generate_image_for_insight(title: str, index: int, user_id: str) -> str:
    """Generate image using google.genai library and upload to GCS
    
    Rotates between 3 API keys (2 images per key) to avoid rate limits.
    """
    try:
        # Select API key based on index (rotate every 2 images)
        api_key_index = (index // 2) % len(IMAGE_API_KEYS)
        selected_api_key = IMAGE_API_KEYS[api_key_index]
        print(f"🔑 Using API key {api_key_index + 1} for image {index + 1}")
        
        # Create client with selected API key
        client = genai.Client(api_key=selected_api_key)
        
        prompt = f"High-quality, evocative illustration representing: {title}. Clean composition, clear subject, 1:1 aspect ratio."
        
        response = client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=prompt,
            config=GenerateImagesConfig(
                number_of_images=1,
            ),
        )
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            response.generated_images[0].image.save(tmp.name)
            tmp_path = tmp.name
        
        # Upload to GCS
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        blob_name = f"{GCS_IMAGES_PREFIX}/{user_id}/insight_{index+1}_{timestamp}.png"
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(tmp_path)
        blob.make_public()
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        public_url = blob.public_url
        print(f"✅ Generated and uploaded image: {public_url}")
        return public_url
        
    except Exception as e:
        print(f"⚠️ Image generation failed for '{title}': {e}")
        traceback.print_exc()
        return None

def save_insights_to_firestore(user_id: str, insights_data: dict):
    """Save AI insights to Firestore"""
    try:
        doc_ref = db.collection("ai_insights").document(user_id)
        doc_ref.set({
            "insights": insights_data.get("insights", []),
            "links": insights_data.get("links", {}),
            "generated_at": firestore.SERVER_TIMESTAMP,
            "profile_snapshot": insights_data.get("profile", {})
        })
        print(f"✅ Saved insights to Firestore for user: {user_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to save to Firestore: {e}")
        return False

def get_insights_from_firestore(user_id: str) -> dict:
    """Get existing AI insights from Firestore"""
    try:
        doc_ref = db.collection("ai_insights").document(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            print(f"✅ Found existing insights for user: {user_id}")
            return data
        else:
            print(f"ℹ️ No existing insights for user: {user_id}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to get from Firestore: {e}")
        return None

def google_search(search_term: str, num_results: int = 3) -> list:
    """Perform Google Custom Search"""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": search_term,
        "num": max(1, min(10, num_results))
    }
    try:
        print(f"🔍 Searching Google for: {search_term}")
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        results = []
        for it in items:
            results.append({
                "title": it.get("title"),
                "snippet": it.get("snippet"),
                "link": it.get("link")
            })
        print(f"✅ Found {len(results)} search results")
        return results
    except Exception as e:
        print(f"⚠️ Google search for '{search_term}' failed: {e}")
        return []

def build_search_queries(profile: dict) -> list:
    """Build search queries based on profile data"""
    queries = []
    region = profile.get("region") or profile.get("location") or ""
    skill = profile.get("craft") or profile.get("occupation") or "artisan"
    product = profile.get("product") or "handicraft"
    material = profile.get("materials") or ""
    country = profile.get("country") or ("India" if "India" in (region or "") else "India")

    if region:
        queries.append(f"{region} artisan support schemes")
    if skill:
        queries.append(f"{skill} artisan government schemes {country}".strip())
    queries.append(f"MSME schemes for artisans {country}".strip())
    queries.append(f"handicraft schemes {country}".strip())
    if product:
        queries.append(f"support schemes for {product} artisans {country}".strip())
    if material:
        queries.append(f"{material} {skill} training programs {country}".strip())

    # Remove duplicates
    seen = set()
    out = []
    for q in queries:
        qn = q.lower()
        if qn and qn not in seen:
            out.append(q)
            seen.add(qn)
        if len(out) >= MAX_SEARCH_QUERIES:
            break
    
    print(f"📋 Generated {len(out)} search queries: {out}")
    return out

def fetch_helpful_links(profile: dict) -> dict:
    """Fetch helpful links via Google Custom Search"""
    try:
        if not GOOGLE_API_KEY or not GOOGLE_CX:
            print("⚠️ Google Custom Search credentials not configured")
            return {}
        
        print("\n🔗 Starting web search for helpful links...")
        queries = build_search_queries(profile)
        links_results = {}
        
        for q in queries:
            results = google_search(q, num_results=RESULTS_PER_QUERY)
            links_results[q] = results
        
        print(f"✅ Completed web search - found links for {len(links_results)} queries")
        return links_results
        
    except Exception as e:
        print(f"❌ Error fetching helpful links: {e}")
        traceback.print_exc()
        return {}

@ai_insights_bp.route('/get-insights', methods=['GET'])
def get_insights():
    """Get AI insights for current user (from cache or generate new)"""
    print("🔍 GET AI INSIGHTS REQUEST")
    try:
        if not FIRESTORE_AVAILABLE:
            return jsonify({"success": False, "error": "Firestore not available"}), 500
        
        user_id = get_user_from_session()
        
        # Check if insights already exist
        existing_insights = get_insights_from_firestore(user_id)
        
        if existing_insights:
            return jsonify({
                "success": True,
                "insights": existing_insights.get("insights", []),
                "links": existing_insights.get("links", {}),
                "generated_at": existing_insights.get("generated_at"),
                "from_cache": True
            }), 200
        else:
            return jsonify({
                "success": True,
                "insights": [],
                "from_cache": False,
                "message": "No insights found. Click 'Generate Latest Info' to create."
            }), 200
            
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 401
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@ai_insights_bp.route('/generate-insights', methods=['POST'])
def generate_insights():
    """Generate new AI insights for current user"""
    print("\n" + "="*80)
    print("✨ GENERATE AI INSIGHTS REQUEST")
    print("="*80)
    
    try:
        if not FIRESTORE_AVAILABLE or not STORAGE_AVAILABLE:
            print("❌ Required services not available")
            print(f"   Firestore: {FIRESTORE_AVAILABLE}, Storage: {STORAGE_AVAILABLE}")
            return jsonify({"success": False, "error": "Required services not available"}), 500
        
        user_id = get_user_from_session()
        print(f"👤 User ID from session: {user_id}")
        
        # Get user profile
        print("📋 Fetching user profile...")
        profile = get_user_profile_data(user_id)
        print(f"📋 Profile retrieved: {json.dumps(profile, indent=2)}")
        
        if not profile or not profile.get("name"):
            print("❌ Profile validation failed - missing name")
            return jsonify({
                "success": False,
                "error": "Profile data not found. Please complete your profile first."
            }), 400
        
        # Generate insights using Gemini
        print("\n🤖 Starting Gemini insights generation...")
        insights_response = call_gemini_for_insights(profile)
        print(f"📊 Gemini response: {json.dumps(insights_response, indent=2)[:500]}...")
        
        if not insights_response.get("insights"):
            print("❌ No insights in response")
            return jsonify({
                "success": False,
                "error": "Failed to generate insights"
            }), 500
        
        insights = insights_response["insights"]
        print(f"✅ Generated {len(insights)} insights")
        
        # Generate images for each insight
        print("\n🎨 Starting image generation...")
        for i, insight in enumerate(insights):
            title = insight.get("title", "")
            print(f"   🖼️ Generating image {i+1}/6 for: {title}")
            image_url = generate_image_for_insight(title, i, user_id)
            insight["image_url"] = image_url
            print(f"   {'✅' if image_url else '⚠️'} Image URL: {image_url or 'None'}")
        
        # Fetch helpful links via web search
        print("\n🔗 Fetching helpful links...")
        links_results = fetch_helpful_links(profile)
        print(f"✅ Fetched {len(links_results)} link categories")
        
        # Prepare final data
        final_data = {
            "profile": profile,
            "insights": insights,
            "links": links_results
        }
        
        # Save to Firestore
        print("\n💾 Saving to Firestore...")
        saved = save_insights_to_firestore(user_id, final_data)
        print(f"{'✅' if saved else '❌'} Firestore save: {saved}")
        
        print("\n✅ Successfully generated AI insights")
        print("="*80 + "\n")
        
        return jsonify({
            "success": True,
            "insights": insights,
            "links": {},
            "generated_at": datetime.now().isoformat(),
            "from_cache": False
        }), 200
        
    except ValueError as e:
        print(f"\n❌ ValueError: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 401
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print(f"❌ Error type: {type(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@ai_insights_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "AI Insights API",
        "firestore_available": FIRESTORE_AVAILABLE,
        "storage_available": STORAGE_AVAILABLE
    }), 200
