from flask import Blueprint, request, jsonify, session
import os
import uuid
import tempfile
import shutil
import requests
from datetime import datetime
from google.cloud import storage
from google.cloud import firestore
import mimetypes
import sys
from pathlib import Path
from PIL import Image
from io import BytesIO

# Google GenAI imports for image generation
from google import genai
from google.genai import types
from google.genai.types import GenerateImagesConfig

# Initialize Flask Blueprint
image_gen_bp = Blueprint('image_gen', __name__)

# Google Cloud Configuration
BUCKET_NAME = "all_in_one_bucket"
FIRESTORE_AVAILABLE = True

# Configuration for image generation
PROJECT_ID = "useful-figure-475210-g7"
LOCATION = "us-central1"

# Initialize GenAI client for image generation
genai_client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

# Initialize Google Cloud clients
try:
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    db = firestore.Client()
    print("✅ Google Cloud Storage and Firestore initialized successfully for image generation")
except Exception as e:
    print(f"❌ Failed to initialize Google Cloud services for image generation: {e}")
    FIRESTORE_AVAILABLE = False
    storage_client = None
    bucket = None
    db = None

def get_user_from_session():
    """Get user ID from session"""
    if not session.get('is_authenticated'):
        raise ValueError("User not authenticated")
    
    user_id = session.get('user_id')
    if not user_id:
        raise ValueError("User ID not found in session")
    
    return user_id

def download_image_from_url(image_url, local_path):
    """Download image from URL to local path"""
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Downloaded image: {image_url} -> {local_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to download image {image_url}: {e}")
        return False

def generate_text_to_image(prompt: str, aspect_ratio: str = "1:1", number_of_images: int = 1):
    """Generate image from text prompt using Imagen"""
    try:
        print(f"🎨 Generating image from text prompt: {prompt}")
        
        image = genai_client.models.generate_images(
            model="imagen-3.0-generate-001",
            prompt=prompt,
            config=GenerateImagesConfig(
                number_of_images=number_of_images,
                aspect_ratio=aspect_ratio,
            ),
        )
        
        if not image.generated_images:
            raise RuntimeError("No images generated")
        
        generated_image = image.generated_images[0]
        print(f"✅ Generated image successfully")
        print(f"📊 Size: {len(generated_image.image.image_bytes)} bytes")
        
        return generated_image.image.image_bytes
        
    except Exception as e:
        print(f"❌ Text to image generation failed: {e}")
        raise RuntimeError(f"Failed to generate image from text: {e}")

def generate_image_to_image(prompt: str, reference_image_path: str):
    """Generate image from reference image using Gemini"""
    try:
        print(f"🎨 Generating image from reference image: {reference_image_path}")
        print(f"📝 Prompt: {prompt}")
        
        # Load the reference image
        reference_image = Image.open(reference_image_path)
        print(f"📷 Reference image size: {reference_image.size}")
        
        # Generate image using Gemini
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt, reference_image],
            config=types.GenerateContentConfig(
                max_output_tokens=1000
            )
        )
        
        print("🔄 Processing response...")
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print(f"📝 Text response: {part.text}")
            elif part.inline_data is not None:
                print("💾 Saving generated image...")
                generated_image_bytes = part.inline_data.data
                print(f"✅ Generated image successfully")
                print(f"📊 Size: {len(generated_image_bytes)} bytes")
                return generated_image_bytes
            else:
                print("⚠️ No image data found in response")
        
        raise RuntimeError("No image data found in response")
        
    except Exception as e:
        print(f"❌ Image to image generation failed: {e}")
        raise RuntimeError(f"Failed to generate image from reference: {e}")

def upload_image_to_storage(image_bytes, user_id, title, image_type="generated"):
    """Upload generated image to Google Cloud Storage"""
    try:
        # Generate unique filename
        unique_filename = f"{image_type}_{uuid.uuid4()}.png"
        
        # Create path: kaarigar/KR_USER11/generated_images/ or kaarigar/KR_USER11/edited_images/
        kaarigar_id = f"KR_{user_id.upper()}"
        folder = "generated_images" if image_type == "generated" else "edited_images"
        blob_path = f"kaarigar/{kaarigar_id}/{folder}/{unique_filename}"
        
        # Upload file
        blob = bucket.blob(blob_path)
        blob.upload_from_string(image_bytes, content_type="image/png")
        
        # Make blob publicly accessible
        blob.make_public()
        
        # Get public URL
        public_url = blob.public_url
        
        print(f"✅ Image uploaded successfully: {blob_path}")
        print(f"🔗 Public URL: {public_url}")
        
        return {
            "success": True,
            "blob_path": blob_path,
            "public_url": public_url,
            "filename": unique_filename
        }
        
    except Exception as e:
        print(f"❌ Failed to upload image to storage: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def save_image_metadata(user_id, image_data):
    """Save generated image metadata to Firestore in _generated_images collection"""
    try:
        print(f"🔧 Starting save_image_metadata for user: {user_id}")
        print(f"🔧 Image data keys: {list(image_data.keys())}")
        
        kaarigar_id = f"KR_{user_id.upper()}"
        
        # Create image document
        image_doc = {
            "user_id": user_id,
            "kaarigar_id": kaarigar_id,
            "image_type": image_data["image_type"],
            "title": image_data["title"],
            "description": image_data.get("description", ""),
            "prompt": image_data["prompt"],
            "reference_image_id": image_data.get("reference_image_id", ""),
            "aspect_ratio": image_data.get("aspect_ratio", "1:1"),
            "filename": image_data["filename"],
            "blob_path": image_data["blob_path"],
            "public_url": image_data["public_url"],
            "file_size": image_data.get("file_size", 0),
            "generated_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        print(f"🔧 Created image document with {len(image_doc)} fields")
        
        # Save to hierarchical structure in media collection:
        # media/user11/uploadmedia/media_data/_generated_images/
        print(f"🔧 Creating Firestore path for generated images...")
        
        # Step 1: Get media collection
        media_collection = db.collection("media")
        print(f"🔧 Step 1 - media collection: {type(media_collection)}")
        
        # Step 2: Get user document reference
        user_doc_ref = media_collection.document(user_id)
        print(f"🔧 Step 2 - user doc ref: {type(user_doc_ref)}")
        
        # Step 3: Get uploadmedia subcollection
        uploadmedia_collection = user_doc_ref.collection("uploadmedia")
        print(f"🔧 Step 3 - uploadmedia collection: {type(uploadmedia_collection)}")
        
        # Step 4: Get media_data document reference
        uploadmedia_doc_ref = uploadmedia_collection.document("media_data")
        print(f"🔧 Step 4a - uploadmedia doc ref: {type(uploadmedia_doc_ref)}")
        
        # Step 5: Get _generated_images collection
        generated_images_collection = uploadmedia_doc_ref.collection("_generated_images")
        print(f"🔧 Step 5 - _generated_images collection: {type(generated_images_collection)}")
        
        # Step 6: Create document reference
        image_ref = generated_images_collection.document()
        print(f"🔧 Step 6 - document ref: {type(image_ref)}")
        print(f"🔧 Document ID: {image_ref.id}")
        
        # Step 7: Save the document
        print(f"🔧 Saving image document to Firestore...")
        image_ref.set(image_doc)
        print(f"🔧 Image document saved successfully!")
        
        print(f"✅ Image metadata saved to Firestore:")
        print(f"   - Path: media/{user_id}/uploadmedia/media_data/_generated_images/{image_ref.id}")
        
        return {
            "success": True,
            "image_id": image_ref.id,
            "message": "Image generated and saved successfully"
        }
        
    except Exception as e:
        print(f"❌ Failed to save image metadata: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e)
        }

@image_gen_bp.route('/generate-image', methods=['POST'])
def generate_image():
    """Generate image from text prompt or reference image"""
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get parameters
        prompt = data.get('prompt', '')
        title = data.get('title', '')
        description = data.get('description', '')
        aspect_ratio = data.get('aspect_ratio', '1:1')
        reference_image_id = data.get('reference_image_id', '')
        
        if not prompt.strip():
            return jsonify({"error": "No prompt provided"}), 400
        
        if not title.strip():
            return jsonify({"error": "No title provided"}), 400
        
        print(f"🎨 Starting image generation for user: {user_id}")
        print(f"📝 Prompt: {prompt}")
        print(f"📝 Title: {title}")
        print(f"📐 Aspect ratio: {aspect_ratio}")
        print(f"🖼️ Reference image ID: {reference_image_id or 'None'}")
        
        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp(prefix="image_generation_")
        print(f"🗂️ Temporary working directory: {temp_dir}")
        
        try:
            image_bytes = None
            image_type = "generated"
            
            if reference_image_id:
                # Generate image from reference image
                print("🔄 Generating image from reference image...")
                
                # Fetch reference image from Firestore
                images_ref = db.collection("media").document(user_id).collection("uploadmedia").document("media_data").collection("images")
                doc = images_ref.document(reference_image_id).get()
                
                if not doc.exists:
                    return jsonify({"error": "Reference image not found"}), 400
                
                image_data = doc.to_dict()
                reference_image_url = image_data['public_url']
                
                # Download reference image
                reference_image_path = os.path.join(temp_dir, "reference_image.jpg")
                if not download_image_from_url(reference_image_url, reference_image_path):
                    return jsonify({"error": "Failed to download reference image"}), 500
                
                # Generate image using image-to-image
                image_bytes = generate_image_to_image(prompt, reference_image_path)
                image_type = "edited"
                
            else:
                # Generate image from text prompt
                print("🔄 Generating image from text prompt...")
                image_bytes = generate_text_to_image(prompt, aspect_ratio)
                image_type = "generated"
            
            if not image_bytes:
                return jsonify({"error": "Failed to generate image"}), 500
            
            # Get file size
            file_size = len(image_bytes)
            print(f"📊 Generated image size: {file_size / 1024:.1f} KB")
            
            # Upload image to Cloud Storage
            upload_result = upload_image_to_storage(image_bytes, user_id, title, image_type)
            
            if not upload_result["success"]:
                return jsonify({"error": f"Failed to upload image: {upload_result['error']}"}), 500
            
            # Prepare metadata for Firestore
            image_metadata = {
                "image_type": image_type,
                "title": title,
                "description": description,
                "prompt": prompt,
                "reference_image_id": reference_image_id,
                "aspect_ratio": aspect_ratio,
                "filename": upload_result["filename"],
                "blob_path": upload_result["blob_path"],
                "public_url": upload_result["public_url"],
                "file_size": file_size
            }
            
            # Save metadata to Firestore
            save_result = save_image_metadata(user_id, image_metadata)
            
            if not save_result["success"]:
                return jsonify({"error": f"Failed to save image metadata: {save_result['error']}"}), 500
            
            print(f"🎉 Image generation completed successfully!")
            print(f"   - Image ID: {save_result['image_id']}")
            print(f"   - Public URL: {upload_result['public_url']}")
            
            return jsonify({
                "success": True,
                "message": "Image generated successfully",
                "image_id": save_result["image_id"],
                "public_url": upload_result["public_url"],
                "title": title,
                "image_type": image_type,
                "file_size": file_size
            })
            
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                print(f"🧹 Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                print(f"⚠️ Failed to clean up temporary directory: {e}")
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Image generation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@image_gen_bp.route('/get-generated-images', methods=['GET'])
def get_generated_images():
    """Get user's generated images from _generated_images collection"""
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        print(f"🔧 Getting generated images for user: {user_id}")
        
        # Get images from _generated_images collection
        images_ref = db.collection("media").document(user_id).collection("uploadmedia").document("media_data").collection("_generated_images")
        
        # Get all documents and filter/sort in memory (no index required)
        images_docs = images_ref.get()
        print(f"🔧 Found {len(images_docs)} total image documents")
        
        images_list = []
        for doc in images_docs:
            image_data = doc.to_dict()
            # Filter active documents in memory if needed
            if image_data.get("is_active", True):  # Default to True if not set
                image_data["id"] = doc.id
                image_data["collection_path"] = f"media/{user_id}/uploadmedia/media_data/_generated_images/{doc.id}"
                images_list.append(image_data)
                print(f"🔧 Added image: {image_data.get('title', 'No title')} - {image_data.get('filename', 'No filename')}")
        
        # Sort by generation date if we used fallback
        if len(images_list) > 1:
            images_list.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
        
        print(f"📁 Retrieved generated images for user {user_id}: {len(images_list)} items")
        
        # Debug: Print first image details
        if images_list:
            print(f"🔍 First image details: {images_list[0]}")
        
        return jsonify({
            "success": True,
            "images": images_list,
            "count": len(images_list)
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Get generated images error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@image_gen_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for image generation service"""
    return jsonify({
        "status": "ok",
        "service": "image_generation",
        "firestore_available": FIRESTORE_AVAILABLE,
        "storage_available": storage_client is not None,
        "bucket_name": BUCKET_NAME
    })
