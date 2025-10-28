"""
Reel Generator Backend Route
Handles reel generation with image selection and prompts
"""

from flask import Blueprint, request, jsonify, Response
from flask_cors import cross_origin
import os
import tempfile
import requests
from google.cloud import storage
from google.cloud import firestore
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
from io import BytesIO
import json

# Initialize blueprint
reel_gen_bp = Blueprint('reel_gen', __name__)

# Initialize Google Cloud clients
storage_client = storage.Client()
db = firestore.Client()

# Configuration
BUCKET_NAME = "all_in_one_bucket"
BRAND_ID = "BRAND_123"

def upload_to_gcs(file_path, cloud_path):
    """Upload file to Google Cloud Storage"""
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(cloud_path)
        blob.upload_from_filename(file_path)
        
        # Make blob publicly accessible
        blob.make_public()
        
        return blob.public_url
    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        return None

def save_reel_metadata_to_firestore(user_id, reel_data):
    """Save reel metadata to Firestore"""
    try:
        doc_ref = db.collection("media").document(user_id).collection("uploadmedia").collection("media_data").document("created_reel")
        
        # Get existing data or create new
        doc = doc_ref.get()
        if doc.exists:
            existing_data = doc.to_dict()
            reels = existing_data.get('reels', [])
        else:
            reels = []
        
        # Add new reel
        reels.append(reel_data)
        
        # Update document
        doc_ref.set({
            'reels': reels,
            'last_updated': datetime.now().isoformat(),
            'total_reels': len(reels)
        })
        
        return True
    except Exception as e:
        print(f"Error saving to Firestore: {e}")
        return False

def save_generated_video_to_firestore(user_id, video_data):
    """Save generated video metadata under media/{user_id}/generated_video collection"""
    try:
        collection_ref = db.collection("media").document(user_id).collection("generated_video")
        # Use auto-id document for each generated video
        collection_ref.add({
            **video_data,
            'created_at': video_data.get('created_at') or datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        })
        return True
    except Exception as e:
        print(f"Error saving generated video to Firestore: {e}")
        return False

@reel_gen_bp.route('/api/reel-generator', methods=['POST'])
@cross_origin()
def generate_reel():
    """Generate reel from selected images and prompt"""
    print(f"\n🎬 ===== REEL GENERATION REQUEST RECEIVED =====")
    print(f"📡 Method: {request.method}")
    print(f"📡 Headers: {dict(request.headers)}")
    print(f"📡 Content-Type: {request.content_type}")
    print(f"📡 Form Data: {dict(request.form)}")
    print(f"📡 Files: {list(request.files.keys())}")
    print(f"📡 Remote Address: {request.remote_addr}")
    print(f"📡 User Agent: {request.headers.get('User-Agent', 'Unknown')}")
    
    try:
        # Get user ID from session or request
        user_id = request.form.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Get prompt
        prompt = request.form.get('prompt', '').strip()
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        # Get selected images (can be files or URLs)
        image_urls = []
        files = []
        
        # Check for uploaded files
        if 'images' in request.files:
            uploaded_files = request.files.getlist('images')
            for file in uploaded_files:
                if file and file.filename:
                    files.append(file)
        
        # Check for image URLs in form data
        if 'image_urls' in request.form:
            try:
                image_urls = json.loads(request.form.get('image_urls', '[]'))
            except:
                image_urls = []
        
        # If no files and no URLs, return error
        if not files and not image_urls:
            return jsonify({'error': 'No images provided (files or URLs)'}), 400
        
        print(f"🎬 Generating reel for user {user_id}")
        print(f"📝 Prompt: {prompt}")
        print(f"📸 Files: {len(files)} files")
        print(f"🔗 Image URLs: {len(image_urls)} URLs")
        
        # Process images using BytesIO for in-memory handling
        image_data = {
            'files': [],  # BytesIO objects for uploaded files
            'urls': image_urls,  # Direct URLs
            'bytes_objects': []  # BytesIO objects for URL downloads
        }
        
        if files:
            try:
                # Process uploaded files using BytesIO
                for file in files:
                    if file and file.filename:
                        # Read file content into BytesIO
                        file_bytes = BytesIO()
                        file.save(file_bytes)
                        file_bytes.seek(0)  # Reset pointer
                        
                        image_data['files'].append({
                            'bytes': file_bytes,
                            'filename': secure_filename(file.filename),
                            'content_type': file.content_type or 'image/jpeg'
                        })
                        print(f"📸 Processed uploaded file: {file.filename} ({len(file_bytes.getvalue())} bytes)")
            except Exception as e:
                print(f"❌ Error processing uploaded files: {e}")
                return jsonify({'error': 'Failed to process uploaded files'}), 500
        
        # Process image URLs using BytesIO
        if image_urls:
            try:
                for i, url in enumerate(image_urls):
                    print(f"📥 Downloading image {i+1} from URL: {url}")
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        url_bytes = BytesIO(response.content)
                        url_bytes.seek(0)
                        
                        image_data['bytes_objects'].append({
                            'bytes': url_bytes,
                            'filename': f'url_image_{i+1}.jpg',
                            'content_type': response.headers.get('content-type', 'image/jpeg'),
                            'url': url
                        })
                        print(f"✅ Downloaded image {i+1}: {len(url_bytes.getvalue())} bytes")
                    else:
                        print(f"❌ Failed to download image {i+1}: {response.status_code}")
            except Exception as e:
                print(f"❌ Error downloading image URLs: {e}")
                return jsonify({'error': 'Failed to download image URLs'}), 500
        
        # Validate we have at least some images
        total_images = len(image_data['files']) + len(image_data['bytes_objects'])
        if total_images == 0:
            return jsonify({'error': 'No valid images provided'}), 400
            
        print(f"🎬 Processing {len(image_data['files'])} uploaded files and {len(image_data['bytes_objects'])} URL downloads")
        print(f"📊 Total images in memory: {total_images}")
        
        # Create output filename
        output_filename = f"reel_{uuid.uuid4().hex[:8]}.mp4"
        
        # For now, create a placeholder file
        # In production, this would be replaced with actual reel generation
        if image_data['files']:
            # Use first file's directory for output
            output_path = os.path.join(os.path.dirname(image_data['files'][0]), output_filename)
        else:
            # Create temp directory for URL-only processing
            temp_dir = tempfile.mkdtemp(prefix="reel_output_")
            output_path = os.path.join(temp_dir, output_filename)
        
        print(f"🎬 Creating placeholder reel: {output_filename}")
        
        # Create placeholder video file
        with open(output_path, 'wb') as f:
            f.write(b'placeholder video content')
        
        # Upload to Cloud Storage with user-specific path
        cloud_path = f"media/{user_id}/generated_video/{output_filename}"
        public_url = upload_to_gcs(output_path, cloud_path)
        
        if not public_url:
            return jsonify({'error': 'Failed to upload reel to cloud storage'}), 500
        
        # Prepare metadata
        reel_metadata = {
            'id': str(uuid.uuid4()),
            'title': f"Reel - {prompt[:50]}...",
            'prompt': prompt,
            'filename': output_filename,
            'cloud_path': cloud_path,
            'public_url': public_url,
            'images_count': total_images,
            'uploaded_files_count': len(image_data['files']),
            'url_downloads_count': len(image_data['bytes_objects']),
            'image_urls': image_urls,  # Store original URLs for reference
            'created_at': datetime.now().isoformat(),
            'file_size_mb': round(os.path.getsize(output_path) / (1024 * 1024), 2),
            'status': 'completed',
            'processing_method': 'BytesIO_in_memory'
        }
        
        # Save to Firestore (legacy list + new generated_video collection)
        if save_reel_metadata_to_firestore(user_id, reel_metadata):
            print(f"✅ Reel metadata saved to Firestore (legacy created_reel)")
        else:
            print(f"⚠️ Failed to save metadata to Firestore (legacy created_reel)")

        if save_generated_video_to_firestore(user_id, reel_metadata):
            print(f"✅ Generated video saved to Firestore (generated_video collection)")
        else:
            print(f"⚠️ Failed to save generated video to Firestore (generated_video collection)")
        
        return jsonify({
            'success': True,
            'message': 'Reel generated successfully using BytesIO',
            'reel_id': reel_metadata['id'],
            'title': reel_metadata['title'],
            'generated_video_url': public_url,
            'cloud_path': cloud_path,
            'file_size_mb': reel_metadata['file_size_mb'],
            'images_used': total_images,
            'uploaded_files_processed': len(image_data['files']),
            'url_downloads_processed': len(image_data['bytes_objects']),
            'processing_method': 'BytesIO_in_memory',
            'memory_efficient': True
        })
        
        # Clean up BytesIO objects (automatic garbage collection)
        print(f"🧹 BytesIO objects will be automatically garbage collected")
        print(f"✅ No temporary files to clean up - all processing done in memory")
                
    except Exception as e:
        print(f"❌ Error generating reel: {e}")
        return jsonify({'error': f'Reel generation failed: {str(e)}'}), 500

@reel_gen_bp.route('/api/generate-video/images', methods=['POST'])
@cross_origin()
def generate_video_from_images_urls():
    """Generate video from image URLs (JSON body: { prompt, image_urls, user_id? })"""
    try:
        data = request.get_json(silent=True) or {}
        prompt = (data.get('prompt') or '').strip()
        image_urls = data.get('image_urls') or []
        user_id = (data.get('user_id') or '').strip() or 'anonymous'

        if not prompt:
            return jsonify({'success': False, 'error': 'Prompt is required'}), 400
        if not isinstance(image_urls, list) or len(image_urls) == 0:
            return jsonify({'success': False, 'error': 'image_urls must be a non-empty list'}), 400

        # Download images into memory to validate accessibility (optional)
        bytes_objects = []
        for i, url in enumerate(image_urls):
            try:
                resp = requests.get(url, timeout=30)
                if resp.status_code == 200:
                    b = BytesIO(resp.content)
                    b.seek(0)
                    bytes_objects.append(b)
                else:
                    print(f"Failed to fetch image {i+1}: {resp.status_code}")
            except Exception as e:
                print(f"Error fetching image {i+1}: {e}")

        if len(bytes_objects) == 0:
            return jsonify({'success': False, 'error': 'No valid image URLs provided'}), 400

        # Create a placeholder output (replace with real generation)
        temp_dir = tempfile.mkdtemp(prefix="reel_output_")
        output_filename = f"reel_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(temp_dir, output_filename)
        with open(output_path, 'wb') as f:
            f.write(b'placeholder video content')

        # Upload to GCS under media/{user_id}/generated_video/
        cloud_path = f"media/{user_id}/generated_video/{output_filename}"
        public_url = upload_to_gcs(output_path, cloud_path)
        if not public_url:
            return jsonify({'success': False, 'error': 'Failed to upload video to cloud storage'}), 500

        reel_metadata = {
            'id': str(uuid.uuid4()),
            'title': f"Reel - {prompt[:50]}...",
            'prompt': prompt,
            'filename': output_filename,
            'cloud_path': cloud_path,
            'public_url': public_url,
            'images_count': len(bytes_objects),
            'image_urls': image_urls,
            'created_at': datetime.now().isoformat(),
            'file_size_mb': round(os.path.getsize(output_path) / (1024 * 1024), 2),
            'status': 'completed',
            'processing_method': 'urls_json'
        }

        # Save metadata to Firestore collection
        save_generated_video_to_firestore(user_id, reel_metadata)

        return jsonify({
            'success': True,
            'message': 'Video generated successfully',
            'generated_video_url': public_url,
            'cloud_path': cloud_path,
            'file_size_mb': reel_metadata['file_size_mb']
        })
    except Exception as e:
        print(f"❌ Error in generate_video_from_images_urls: {e}")
        return jsonify({'success': False, 'error': f'Generation failed: {str(e)}'}), 500

@reel_gen_bp.route('/api/reel-generator/user-reels', methods=['GET'])
@cross_origin()
def get_user_reels():
    """Get all reels for a specific user"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        print(f"📋 Fetching reels for user: {user_id}")
        
        # Get reels from Firestore
        doc_ref = db.collection("media").document(user_id).collection("uploadmedia").collection("media_data").document("created_reel")
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            reels = data.get('reels', [])
            print(f"✅ Found {len(reels)} reels")
            
            return jsonify({
                'success': True,
                'reels': reels,
                'total': len(reels)
            })
        else:
            print(f"📭 No reels found for user {user_id}")
            return jsonify({
                'success': True,
                'reels': [],
                'total': 0
            })
            
    except Exception as e:
        print(f"❌ Error fetching reels: {e}")
        return jsonify({'error': f'Failed to fetch reels: {str(e)}'}), 500

@reel_gen_bp.route('/api/reel-generator/suggest-script', methods=['POST'])
@cross_origin()
def suggest_script():
    """Generate AI script suggestions based on prompt and images"""
    print(f"\n🤖 ===== SCRIPT SUGGESTION REQUEST RECEIVED =====")
    print(f"📡 Method: {request.method}")
    print(f"📡 Headers: {dict(request.headers)}")
    print(f"📡 Content-Type: {request.content_type}")
    print(f"📡 Form Data: {dict(request.form)}")
    print(f"📡 Files: {list(request.files.keys())}")
    print(f"📡 Remote Address: {request.remote_addr}")
    print(f"📡 User Agent: {request.headers.get('User-Agent', 'Unknown')}")
    
    try:
        # Get user ID from session or request
        user_id = request.form.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Get prompt
        prompt = request.form.get('prompt', '').strip()
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
        
        print(f"🤖 Generating script suggestions for user {user_id}")
        print(f"📝 Prompt: {prompt}")
        
        # Get images if provided (files or URLs)
        image_paths = []
        image_urls = []
        
        # Check for uploaded files
        if 'images' in request.files:
            files = request.files.getlist('images')
            if files and any(f for f in files if f.filename):
                # Create temporary directory for processing
                temp_dir = tempfile.mkdtemp(prefix="script_gen_")
                
                try:
                    # Save uploaded images
                    for file in files:
                        if file and file.filename:
                            filename = secure_filename(file.filename)
                            unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
                            filepath = os.path.join(temp_dir, unique_filename)
                            file.save(filepath)
                            image_paths.append(filepath)
                            print(f"📸 Saved uploaded image: {filename}")
                except Exception as e:
                    print(f"❌ Error saving images: {e}")
                    return jsonify({'error': 'Failed to process images'}), 500
        
        # Check for image URLs
        if 'image_urls' in request.form:
            try:
                import json
                image_urls = json.loads(request.form.get('image_urls', '[]'))
                print(f"🔗 Received {len(image_urls)} image URLs")
            except Exception as e:
                print(f"❌ Error parsing image URLs: {e}")
                image_urls = []
        
        # Generate script suggestions using AI
        # For now, we'll create placeholder suggestions
        # In production, this would integrate with Gemini or similar AI service
        # The service would receive:
        # - image_paths: list of local file paths (if any)
        # - image_urls: list of image URLs (if any)
        # - prompt: user's text prompt
        
        suggestions = []
        
        if image_paths or image_urls:
            # If images are provided (files or URLs), generate image-aware suggestions
            total_images = len(image_paths) + len(image_urls)
            suggestions = [
                f"Create a dynamic video showcasing the visual elements from the {total_images} provided image(s) with the theme: {prompt}. Focus on smooth transitions and engaging visuals.",
                f"Transform the provided image(s) into a storytelling video about {prompt}. Use cinematic effects and dramatic lighting to enhance the narrative.",
                f"Generate an artistic video interpretation of {prompt} using the uploaded image(s). Emphasize creative composition and visual flow with modern editing techniques."
            ]
        else:
            # Text-only suggestions
            suggestions = [
                f"Create an engaging video about {prompt} with dynamic text animations and modern visual effects.",
                f"Produce a cinematic video exploring {prompt} with dramatic lighting and smooth camera movements.",
                f"Generate an artistic video interpretation of {prompt} with creative transitions and visual storytelling."
            ]
        
        # Clean up temporary files
        try:
            for path in image_paths:
                if os.path.exists(path):
                    os.remove(path)
            if image_paths and os.path.exists(os.path.dirname(image_paths[0])):
                os.rmdir(os.path.dirname(image_paths[0]))
        except Exception as e:
            print(f"⚠️ Error cleaning up temp files: {e}")
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'count': len(suggestions),
            'has_images': len(image_paths) > 0 or len(image_urls) > 0,
            'images_count': len(image_paths) + len(image_urls),
            'files_count': len(image_paths),
            'urls_count': len(image_urls)
        })
        
    except Exception as e:
        print(f"❌ Error generating script suggestions: {e}")
        return jsonify({'error': f'Script suggestion failed: {str(e)}'}), 500

@reel_gen_bp.route('/proxy-image', methods=['GET'])
@cross_origin()
def proxy_image():
    """Proxy endpoint to download images from GCS URLs and return them using BytesIO"""
    try:
        image_url = request.args.get('url')
        if not image_url:
            return jsonify({'error': 'URL parameter is required'}), 400
        
        print(f"🔄 Proxying image download: {image_url}")
        
        # Download the image directly to BytesIO
        response = requests.get(image_url, timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to download image: {response.status_code}")
            return jsonify({'error': f'Failed to download image: {response.status_code}'}), 400
        
        # Use BytesIO for in-memory handling
        image_bytes = BytesIO(response.content)
        image_bytes.seek(0)  # Reset pointer to beginning
        
        print(f"✅ Downloaded {len(response.content)} bytes to BytesIO")
        
        # Return the image data with proper headers
        return Response(
            image_bytes.getvalue(),
            mimetype=response.headers.get('content-type', 'image/jpeg'),
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Cache-Control': 'public, max-age=3600'
            }
        )
        
    except Exception as e:
        print(f"❌ Error proxying image: {str(e)}")
        return jsonify({'error': f'Error proxying image: {str(e)}'}), 500

@reel_gen_bp.route('/api/reel-generator/health', methods=['GET'])
@cross_origin()
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'reel-generator',
        'bucket': BUCKET_NAME,
        'brand_id': BRAND_ID
    })
