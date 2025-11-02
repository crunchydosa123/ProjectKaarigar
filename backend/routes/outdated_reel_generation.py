from flask import Blueprint, request, jsonify, session
import os
import uuid
import tempfile
import shutil
from datetime import datetime
from google.cloud import storage
from google.cloud import firestore
import mimetypes
import sys
from pathlib import Path

# Import the reel generation model
# sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Model'))
# try:
#     from reel_model import convert_images_to_reel, optimize_prompt_with_gemini
# except ImportError:
#     print("WARNING: Could not import reel_model. Reel generation will not work.")
#     convert_images_to_reel = None
#     optimize_prompt_with_gemini = None

# Placeholder functions for when reel_model is not available
convert_images_to_reel = None
optimize_prompt_with_gemini = None

# Initialize Flask Blueprint
reel_bp = Blueprint('reel', __name__)

# Google Cloud Configuration
BUCKET_NAME = "all_in_one_bucket1"
FIRESTORE_AVAILABLE = True

# Configuration for reel generation
PROJECT_ID = "karigar-475215"
LOCATION = "us-central1"

# Initialize Google Cloud clients
try:
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    db = firestore.Client()
    print("SUCCESS: Google Cloud Storage and Firestore initialized successfully for reel generation")
except Exception as e:
    print(f"ERROR: Failed to initialize Google Cloud services for reel generation: {e}")
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

def upload_reel_to_storage(video_path, user_id, title, prompt):
    """Upload generated reel to Google Cloud Storage"""
    try:
        # Generate unique filename
        unique_filename = f"reel_{uuid.uuid4()}.mp4"
        
        # Create path: kaarigar/KR_USER11/generated_reels/
        kaarigar_id = f"KR_{user_id.upper()}"
        blob_path = f"kaarigar/{kaarigar_id}/generated_reels/{unique_filename}"
        
        # Upload file
        blob = bucket.blob(blob_path)
        blob.upload_from_filename(video_path, content_type="video/mp4")
        
        # Make blob publicly accessible
        blob.make_public()
        
        # Get public URL
        public_url = blob.public_url
        
        print(f"SUCCESS: Reel uploaded successfully: {blob_path}")
        print(f"URL: {public_url}")
        
        return {
            "success": True,
            "blob_path": blob_path,
            "public_url": public_url,
            "filename": unique_filename
        }
        
    except Exception as e:
        print(f"ERROR: Failed to upload reel to storage: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def save_reel_metadata(user_id, reel_data):
    """Save reel metadata to Firestore"""
    try:
        print(f"INFO: Saving reel metadata for user: {user_id}")
        
        kaarigar_id = f"KR_{user_id.upper()}"
        
        # Create reel document
        reel_doc = {
            "user_id": user_id,
            "kaarigar_id": kaarigar_id,
            "title": reel_data["title"],
            "prompt": reel_data["prompt"],
            "filename": reel_data["filename"],
            "blob_path": reel_data["blob_path"],
            "public_url": reel_data["public_url"],
            "file_size": reel_data.get("file_size", 0),
            "duration": reel_data.get("duration", 0),
            "segments": reel_data.get("segments", 1),
            "captions": reel_data.get("captions", []),
            "generated_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        print(f"INFO: Created reel document with {len(reel_doc)} fields")
        
        # Save to generated_reels collection
        reels_ref = db.collection("media").document(user_id).collection("uploadmedia").document("media_data").collection("_generated_reels")
        
        # Create document reference
        reel_ref = reels_ref.document()
        print(f"INFO: Document ID: {reel_ref.id}")
        
        # Save the document
        print(f"INFO: Saving reel document to Firestore...")
        reel_ref.set(reel_doc)
        print(f"INFO: Reel document saved successfully!")
        
        print(f"SUCCESS: Reel metadata saved to Firestore:")
        print(f"   - Path: media/{user_id}/uploadmedia/media_data/_generated_reels/{reel_ref.id}")
        
        return {
            "success": True,
            "reel_id": reel_ref.id,
            "message": "Reel saved successfully"
        }
        
    except Exception as e:
        print(f"ERROR: Failed to save reel metadata: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def analyze_content_for_segments(prompt: str, image_paths: list = None) -> tuple:
    """
    Return (segments_per_image, clip_duration_seconds, captions_list)
    Analyzes content and determines optimal reel structure
    """
    try:
        # TEXT-ONLY (no images) - Create cinematic text-to-video
        if not image_paths or len(image_paths) == 0:
            caption = ""
            if prompt:
                c = prompt.strip()
                caption = c if len(c) <= 120 else (c[:117].rstrip() + "...")
            segments_per_image = 1  # For text-only, this becomes total segments = 1
            duration = 8  # Longer duration for text-to-video
            captions = [caption] if caption else ["AI Generated Video"]
            print(f"[analyze] text-only -> segments_per_image={segments_per_image}, duration={duration}, captions={captions}")
            return segments_per_image, duration, captions

        # Normalize and count images
        num_images = len(image_paths)
        
        # SINGLE IMAGE -> Multiple segments for dynamic effect
        if num_images == 1:
            filename = os.path.basename(image_paths[0]) if image_paths[0] else "image"
            segments_per_image = 3  # 3 segments for single image (zoom, pan, effect)
            duration = 6  # 6 seconds total (2s per segment)
            captions = [f"{filename} - Part {i+1}" for i in range(segments_per_image)]
            print(f"[analyze] single image -> segments_per_image={segments_per_image}, duration={duration}, captions={captions}")
            return segments_per_image, duration, captions

        # MULTIPLE IMAGES -> 1 segment per image with transitions
        segments_per_image = 1
        duration = 4  # 4 seconds per image
        captions = []
        for i, path in enumerate(image_paths):
            filename = os.path.basename(path) if path else f"image_{i+1}"
            captions.append(f"{filename}")
        
        print(f"[analyze] multiple images ({num_images}) -> segments_per_image={segments_per_image}, duration={duration}, captions={captions}")
        return segments_per_image, duration, captions

    except Exception as e:
        print(f"Error in content analysis: {e}")
        # Fallback based on content type
        if image_paths and len(image_paths) > 0:
            return 1, 4, [f"Image {i+1}" for i in range(len(image_paths))]
        return 1, 6, ["AI Generated Video"]

@reel_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for reel generation service"""
    return jsonify({
        "status": "ok",
        "service": "reel_generation",
        "message": "Reel generation service is running"
    })

@reel_bp.route('/generate-reel', methods=['POST'])
def generate_reel():
    """Generate reel from selected images and upload to Google Cloud Storage"""
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get required parameters
        prompt = data.get('prompt', '')
        title = data.get('title', '')
        image_urls = data.get('image_urls', [])
        duration = data.get('duration', None)  # Optional custom duration in seconds
        segments = data.get('segments', None)  # Optional custom segments
        
        if not prompt.strip():
            return jsonify({"error": "Prompt is required"}), 400
        
        if not title.strip():
            return jsonify({"error": "Title is required"}), 400
        
        if not convert_images_to_reel:
            return jsonify({"error": "Reel generation model not available"}), 500
        
        print(f"INFO: Starting reel generation for user: {user_id}")
        print(f"INFO: Prompt: {prompt}")
        print(f"INFO: Title: {title}")
        print(f"INFO: Images: {len(image_urls)} images")
        print(f"INFO: Custom Duration: {duration} seconds" if duration else "INFO: Auto Duration")
        print(f"INFO: Custom Segments: {segments}" if segments else "INFO: Auto Segments")
        
        # Process everything in memory - no temp folders
        kaarigar_id = f"KR_{user_id.upper()}"
        
        try:
            # Download images to memory if provided
            image_paths = []
            if image_urls:
                import requests
                for i, image_url in enumerate(image_urls):
                    try:
                        response = requests.get(image_url, stream=True)
                        response.raise_for_status()
                        
                        # Create temporary file for processing (required by reel_model)
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                        temp_file.write(response.content)
                        temp_file.close()
                        
                        image_paths.append(temp_file.name)
                        print(f"SUCCESS: Downloaded image {i+1} to temp file: {temp_file.name}")
                    except Exception as e:
                        print(f"WARNING: Failed to download image {i+1}: {e}")
                        continue
            
            # Determine reel structure
            if duration and segments:
                # Use custom duration and segments
                final_duration = duration
                final_segments = segments
                captions = [f"Segment {i+1}" for i in range(segments)]
                print(f"INFO: Using custom settings: {final_segments} segments, {final_duration}s duration")
            else:
                # Auto-analyze content to determine structure
                final_segments, final_duration, captions = analyze_content_for_segments(prompt, image_paths)
                print(f"INFO: Auto-analyzed: {final_segments} segments, {final_duration}s duration")
            
            # Create temporary output file
            temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_output.close()
            local_output_path = temp_output.name
            
            # Call the conversion function
            success = convert_images_to_reel(
                image_inputs=image_paths,
                user_prompt=prompt,
                output_name=local_output_path,
                clip_duration=final_duration,
                segments=final_segments,
                captions=captions if captions else None,
                text_only=len(image_paths) == 0
            )
            
            if not success or not os.path.exists(local_output_path):
                return jsonify({"error": "Failed to generate reel"}), 500
            
            # Get file size
            file_size = os.path.getsize(local_output_path)
            print(f"INFO: Generated reel size: {file_size / 1024 / 1024:.1f} MB")
            
            # Upload directly to final location
            final_filename = f"reel_{uuid.uuid4()}.mp4"
            final_path = f"kaarigar/{kaarigar_id}/generated_reels/{final_filename}"
            
            # Upload to final location
            final_blob = bucket.blob(final_path)
            final_blob.upload_from_filename(local_output_path, content_type="video/mp4")
            
            # Make final blob publicly accessible
            final_blob.make_public()
            public_url = final_blob.public_url
            
            print(f"SUCCESS: Uploaded reel to final location: {final_path}")
            print(f"URL: {public_url}")
            
            # Prepare metadata for Firestore
            reel_metadata = {
                "title": title,
                "prompt": prompt,
                "filename": final_filename,
                "blob_path": final_path,
                "public_url": public_url,
                "file_size": file_size,
                "duration": final_duration,
                "segments": final_segments,
                "captions": captions,
                "image_count": len(image_paths),
                "generation_type": "text_only" if len(image_paths) == 0 else f"images_{len(image_paths)}"
            }
            
            # Save metadata to Firestore
            save_result = save_reel_metadata(user_id, reel_metadata)
            
            if not save_result["success"]:
                return jsonify({"error": f"Failed to save reel metadata: {save_result['error']}"}), 500
            
            print(f"🎉 Reel generation completed successfully!")
            print(f"   - Reel ID: {save_result['reel_id']}")
            print(f"   - Public URL: {public_url}")
            
            return jsonify({
                "success": True,
                "message": "Reel generated successfully",
                "reel_id": save_result["reel_id"],
                "public_url": public_url,
                "title": title,
                "file_size": file_size,
                "duration": final_duration,
                "segments": final_segments,
                "captions": captions,
                "image_count": len(image_paths),
                "generation_type": "text_only" if len(image_paths) == 0 else f"images_{len(image_paths)}"
            })
            
        finally:
            # Clean up all temporary files immediately
            try:
                # Clean up output file
                if 'local_output_path' in locals() and os.path.exists(local_output_path):
                    os.unlink(local_output_path)
                    print(f"🧹 Cleaned up output file: {local_output_path}")
                
                # Clean up image files
                if 'image_paths' in locals():
                    for path in image_paths:
                        if os.path.exists(path):
                            os.unlink(path)
                            print(f"🧹 Cleaned up image file: {path}")
            except Exception as e:
                print(f"⚠️ Failed to clean up temp files: {e}")
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Reel generation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@reel_bp.route('/get-generated-reels', methods=['GET'])
def get_generated_reels():
    """List user's generated reels from Firestore"""
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        
        print(f"📋 Retrieving generated reels for user: {user_id}")
        
        # Get reels from Firestore
        reels_ref = db.collection("media").document(user_id).collection("uploadmedia").document("media_data").collection("_generated_reels")
        reels_docs = reels_ref.get()
        
        reels_list = []
        for doc in reels_docs:
            reel_data = doc.to_dict()
            reels_list.append({**reel_data, "id": doc.id})
        
        # Sort by generation date (newest first)
        if len(reels_list) > 1:
            reels_list.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
        
        print(f"✅ Retrieved {len(reels_list)} generated reels")
        
        return jsonify({
            "success": True,
            "reels": reels_list,
            "count": len(reels_list)
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Error retrieving reels: {e}")
        return jsonify({"error": "Internal server error"}), 500