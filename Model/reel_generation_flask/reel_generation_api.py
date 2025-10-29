from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from reel_model import convert_images_to_reel, optimize_prompt_with_gemini
from reel_ideas_generator import ReelIdeasGenerator
from werkzeug.utils import secure_filename
import tempfile
import json
from pathlib import Path
from cloud_storage_manager import CloudStorageManager
import logging

app = Flask(__name__)
CORS(app)

# Configure upload folder
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(CURRENT_DIR, "videos")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize managers
cloud_manager = CloudStorageManager(
    bucket_name="all_in_one_bucket1",
    brand_id="BRAND_123"
)

ideas_generator = ReelIdeasGenerator()

print(f"📁 Video storage folder: {UPLOAD_FOLDER}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # Only show actual errors, not 200/400 requests

def analyze_content_for_segments(prompt: str, image_inputs: list = None) -> tuple:
    """
    Return (segments_per_image, clip_duration_seconds, captions_list)
    Note: image_inputs can be URLs or file paths
    """
    try:
        # TEXT-ONLY (no images)
        if not image_inputs:
            caption = ""
            if prompt:
                c = prompt.strip()
                caption = c if len(c) <= 120 else (c[:117].rstrip() + "...")
            segments_per_image = 1
            duration = 6
            captions = [caption] if caption else []
            print(f"[analyze] text-only -> segments_per_image={segments_per_image}, duration={duration}")
            return segments_per_image, duration, captions

        num_images = len(image_inputs)
        if num_images == 0:
            caption = ""
            if prompt:
                c = prompt.strip()
                caption = c if len(c) <= 120 else (c[:117].rstrip() + "...")
            segments_per_image = 1
            duration = 6
            captions = [caption] if caption else []
            print(f"[analyze] empty image list -> segments_per_image={segments_per_image}, duration={duration}")
            return segments_per_image, duration, captions

        if num_images == 1:
            # Extract filename from URL or path
            input_item = image_inputs[0]
            if input_item.startswith('http'):
                filename = input_item.split('/')[-1].split('?')[0]
            else:
                filename = os.path.basename(input_item) if input_item else ""
            segments_per_image = 1
            duration = 4
            captions = [filename] if filename else []
            print(f"[analyze] single image -> segments_per_image={segments_per_image}, duration={duration}")
            return segments_per_image, duration, captions

        segments_per_image = 1
        duration = 4
        captions = []
        for input_item in image_inputs:
            if input_item.startswith('http'):
                filename = input_item.split('/')[-1].split('?')[0]
            else:
                filename = os.path.basename(input_item) if input_item else ""
            captions.append(filename)
        print(f"[analyze] multiple images -> segments_per_image={segments_per_image}, duration={duration}")
        return segments_per_image, duration, captions

    except Exception as e:
        print(f"Error in content analysis: {e}")
        if image_inputs:
            return 1, 4, []
        return 1, 6, []


# ==================== NEW ENDPOINTS: Reel Ideas Workflow ====================

@app.route('/api/reel-generation/ideas', methods=['POST'])
def generate_reel_ideas():
    """
    Generate 3 reel ideas based on initial prompt and optional image(s)
    
    Supports two modes:
    1. JSON with image URLs:
       {
           "initial_prompt": "string",
           "image_urls": ["url1", "url2", ...] (optional)
       }
    
    2. Form-data with file uploads:
       - initial_prompt: string
       - images: file(s) (optional, multiple allowed)
    
    Response:
    {
        "success": true,
        "ideas": ["idea1", "idea2", "idea3"]
    }
    """
    try:
        content_type = request.content_type
        image_inputs = []
        initial_prompt = ""
        
        if content_type and 'application/json' in content_type:
            # Handle JSON request with image URLs
            data = request.get_json()
            
            if not data or 'initial_prompt' not in data:
                return jsonify({'error': 'initial_prompt is required'}), 400
            
            initial_prompt = data.get('initial_prompt', '').strip()
            if not initial_prompt:
                return jsonify({'error': 'initial_prompt cannot be empty'}), 400
            
            # Handle optional image URLs
            image_urls = data.get('image_urls', [])
            if image_urls:
                if not isinstance(image_urls, list):
                    return jsonify({'error': 'image_urls must be an array'}), 400
                
                # Validate URLs
                for url in image_urls:
                    if not url.startswith('http'):
                        return jsonify({'error': f'Invalid image URL: {url}'}), 400
                
                image_inputs = image_urls
                print(f"🤖 Generating ideas for prompt: {initial_prompt}")
                print(f"📸 Processing {len(image_urls)} image URL(s)")
                for url in image_urls:
                    print(f"   🔗 {url}")
            else:
                print(f"🤖 Generating ideas for prompt: {initial_prompt} (no images)")
        
        else:
            # Handle multipart/form-data request with file uploads
            initial_prompt = request.form.get('initial_prompt', '').strip()
            
            if not initial_prompt:
                return jsonify({'error': 'initial_prompt is required'}), 400
            
            print(f"🤖 Generating ideas for prompt: {initial_prompt}")
            
            # Handle optional image uploads
            if 'images' in request.files:
                files = request.files.getlist('images')
                if files and any(f for f in files if f.filename):
                    temp_dir = tempfile.mkdtemp(prefix="veo_ideas_")
                    
                    for file in files:
                        if file and file.filename:
                            filename = secure_filename(file.filename)
                            unique_filename = f"{os.urandom(6).hex()}_{filename}"
                            filepath = os.path.join(temp_dir, unique_filename)
                            file.save(filepath)
                            image_inputs.append(filepath)
                            print(f"📸 Image uploaded for context: {filename}")
                    
                    if image_inputs:
                        print(f"📸 Processing {len(image_inputs)} uploaded image(s)")
        
        # Generate ideas (pass first image if multiple provided, or None)
        image_for_context = image_inputs[0] if image_inputs else None
        
        result = ideas_generator.generate_ideas(
            initial_prompt=initial_prompt,
            image_path=image_for_context,
            num_ideas=3
        )
        
        # Cleanup uploaded files if any
        if content_type and 'multipart/form-data' in content_type and image_inputs:
            for path in image_inputs:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                        logging.info(f"Deleted uploaded image: {path}")
                except Exception as e:
                    logging.warning(f"Failed to delete uploaded image: {path}. Error: {e}")
        
        if result['success']:
            return jsonify({
                'success': True,
                'ideas': result['ideas'],
                'count': len(result['ideas'])
            })
        else:
            return jsonify({'error': result.get('error', 'Failed to generate ideas')}), 500
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/reel-generation/refine-idea', methods=['POST'])
def refine_reel_idea():
    """
    Refine a chosen idea based on user feedback
    
    Request:
    {
        "chosen_idea": "string",
        "refinement_prompt": "string"
    }
    
    Response:
    {
        "success": true,
        "refined_idea": "string"
    }
    """
    try:
        data = request.get_json()
        
        chosen_idea = data.get('chosen_idea', '').strip()
        refinement_prompt = data.get('refinement_prompt', '').strip()
        
        if not chosen_idea or not refinement_prompt:
            return jsonify({'error': 'chosen_idea and refinement_prompt are required'}), 400
        
        print(f"✏️ Refining idea: {chosen_idea[:50]}...")
        
        result = ideas_generator.refine_idea(
            chosen_idea=chosen_idea,
            refinement_prompt=refinement_prompt
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'original_idea': result['original_idea'],
                'refined_idea': result['refined_idea'],
                'word_count': result['word_count']
            })
        else:
            return jsonify({'error': result.get('error', 'Failed to refine idea')}), 500
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/reel-generation/regenerate-ideas', methods=['POST'])
def regenerate_reel_ideas():
    """
    Regenerate 3 new ideas with different direction
    
    Request:
    {
        "regeneration_prompt": "string"
    }
    
    Response:
    {
        "success": true,
        "ideas": ["idea1", "idea2", "idea3"]
    }
    """
    try:
        data = request.get_json()
        
        regeneration_prompt = data.get('regeneration_prompt', '').strip()
        
        if not regeneration_prompt:
            return jsonify({'error': 'regeneration_prompt is required'}), 400
        
        print(f"🔄 Regenerating ideas: {regeneration_prompt[:50]}...")
        
        result = ideas_generator.regenerate_ideas(
            regeneration_prompt=regeneration_prompt,
            num_ideas=3
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'ideas': result['ideas'],
                'count': len(result['ideas'])
            })
        else:
            return jsonify({'error': result.get('error', 'Failed to regenerate ideas')}), 500
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/reel-generation/generate-video-script', methods=['POST'])
def generate_video_script():
    """
    Convert reel idea into video generation script
    
    Request:
    {
        "reel_idea": "string"
    }
    
    Response:
    {
        "success": true,
        "script": "string",
        "word_count": integer
    }
    """
    try:
        data = request.get_json()
        
        reel_idea = data.get('reel_idea', '').strip()
        
        if not reel_idea:
            return jsonify({'error': 'reel_idea is required'}), 400
        
        print(f"📝 Generating script for idea: {reel_idea[:50]}...")
        
        result = ideas_generator.generate_video_script(reel_idea)
        
        if result['success']:
            return jsonify({
                'success': True,
                'reel_idea': result['reel_idea'],
                'script': result['script'],
                'word_count': result['word_count']
            })
        else:
            return jsonify({'error': result.get('error', 'Failed to generate script')}), 500
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/reel-generation/generate-video', methods=['POST'])
def generate_video_from_script():
    logging.debug("Received request to generate video from script.")
    try:
        data = request.get_json()
        logging.debug(f"Request data: {data}")

        script = data.get('script', '').strip()
        if not script:
            logging.error("Script is required but not provided.")
            return jsonify({'error': 'script is required'}), 400

        logging.info("Generating video from script...")
        output_name = os.path.join(UPLOAD_FOLDER, f"script_video_{os.urandom(8).hex()}.mp4")
        logging.debug(f"Output file path: {output_name}")

        success = convert_images_to_reel(
            image_inputs=[],
            user_prompt=script,
            output_name=output_name,
            clip_duration=6,
            segments=1,
            captions=None,
            text_only=True
        )

        if success and os.path.exists(output_name):
            file_size = os.path.getsize(output_name) / (1024 * 1024)
            logging.info(f"Video generated successfully: {output_name} ({file_size:.2f} MB)")

            logging.info("Uploading video to Cloud Storage...")
            cloud_info = cloud_manager.upload_video(output_name, video_type="generated")

            if cloud_info:
                try:
                    os.remove(output_name)
                    logging.info(f"Deleted local file after upload: {output_name}")
                except Exception as e:
                    logging.warning(f"Failed to delete local file: {output_name}. Error: {e}")

                return jsonify({
                    'success': True,
                    'message': 'Video generated and uploaded successfully',
                    'generated_video_url': cloud_info['public_url'],
                    'cloud_path': cloud_info['cloud_path'],
                    'file_size_mb': cloud_info['file_size_mb']
                })
            else:
                logging.error("Cloud upload failed.")
                return jsonify({
                    'error': 'Video generated but cloud upload failed',
                    'local_path': output_name
                }), 206
        else:
            logging.error("Video generation failed.")
            return jsonify({'error': 'Failed to generate video'}), 500

    except Exception as e:
        logging.exception("An error occurred during video generation.")
        return jsonify({'error': str(e)}), 500


# ==================== EXISTING ENDPOINTS ====================

@app.route('/api/generate-video/text', methods=['POST'])
def generate_text_to_video():
    """Generate video from text prompt and upload to cloud storage"""
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Prompt is required'}), 400
        
        prompt = data['prompt'].strip() if isinstance(data['prompt'], str) else ""
        
        if not prompt:
            return jsonify({'error': 'Prompt cannot be empty'}), 400
        
        segments, duration, captions = analyze_content_for_segments(prompt)
        output_name = os.path.join(UPLOAD_FOLDER, f"text_video_{os.urandom(8).hex()}.mp4")
        
        print(f"🎬 Generating text-to-video: {output_name}")
        
        success = convert_images_to_reel(
            image_inputs=[],
            user_prompt=prompt,
            output_name=output_name,
            clip_duration=duration,
            segments=segments,
            captions=captions if captions else None,
            text_only=True
        )
        
        if success and os.path.exists(output_name):
            file_size = os.path.getsize(output_name) / (1024 * 1024)
            print(f"✅ Video saved locally: {output_name} ({file_size:.2f} MB)")
            
            print(f"☁️  Uploading to Cloud Storage...")
            cloud_info = cloud_manager.upload_video(output_name, video_type="text")
            
            if cloud_info:
                try:
                    os.remove(output_name)
                    logging.info(f"Deleted local file: {output_name}")
                except Exception as e:
                    logging.warning(f"Failed to delete local file: {output_name}. Error: {e}")
                
                return jsonify({
                    'success': True,
                    'message': 'Video generated and uploaded to cloud successfully',
                    'generated_video_url': cloud_info['public_url'],
                    'cloud_path': cloud_info['cloud_path'],
                    'file_size_mb': round(file_size, 2)
                })
            else:
                return jsonify({
                    'success': True,
                    'message': 'Video generated but cloud upload failed',
                    'file_size_mb': round(file_size, 2),
                    'cloud_error': 'Upload to cloud storage failed'
                }), 206
        else:
            return jsonify({
                'error': 'Failed to generate video'
            }), 500
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-video/images', methods=['POST'])
def generate_images_to_video():
    """
    Generate video from images (files or URLs) and upload to cloud storage
    
    Supports two modes:
    1. JSON with image URLs:
       {
           "image_urls": ["url1", "url2", ...],
           "prompt": "string"
       }
    
    2. Form-data with file uploads:
       - images: file(s) (multiple allowed)
       - prompt: string
    """
    try:
        content_type = request.content_type
        image_inputs = []
        prompt = ""
        temp_upload_dir = None
        
        if content_type and 'application/json' in content_type:
            # Handle JSON request with image URLs
            data = request.get_json()
            
            if not data or 'image_urls' not in data:
                return jsonify({'error': 'image_urls array is required in JSON request'}), 400
            
            image_urls = data.get('image_urls', [])
            if not image_urls or len(image_urls) == 0:
                return jsonify({'error': 'At least one image URL is required'}), 400
            
            if not isinstance(image_urls, list):
                return jsonify({'error': 'image_urls must be an array'}), 400
            
            prompt = data.get('prompt', '').strip()
            if not prompt:
                return jsonify({'error': 'Prompt is required'}), 400
            
            # Validate URLs
            for url in image_urls:
                if not url.startswith('http'):
                    return jsonify({'error': f'Invalid image URL: {url}'}), 400
            
            image_inputs = image_urls
            print(f"📸 Processing {len(image_urls)} image URL(s)")
            for url in image_urls:
                print(f"   🔗 {url}")
            
        else:
            # Handle multipart/form-data request with file uploads
            if 'images' not in request.files:
                return jsonify({'error': 'No images provided'}), 400
                
            files = request.files.getlist('images')
            if not files or not any(f for f in files if f.filename):
                return jsonify({'error': 'No selected files'}), 400
                
            prompt = request.form.get('prompt', '').strip()
            if not prompt:
                return jsonify({'error': 'Prompt is required'}), 400
            
            temp_upload_dir = tempfile.mkdtemp(prefix="veo_uploads_")
            
            image_paths = []
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = f"{os.urandom(6).hex()}_{filename}"
                    filepath = os.path.join(temp_upload_dir, unique_filename)
                    file.save(filepath)
                    image_paths.append(filepath)
                    print(f"📸 Uploaded: {filename}")
                    
            if not image_paths:
                return jsonify({'error': 'No valid images uploaded'}), 400
            
            image_inputs = image_paths
            print(f"📸 Processing {len(image_paths)} uploaded image(s)")
        
        # Generate video
        segments, duration, captions = analyze_content_for_segments(prompt, image_inputs)
        output_name = os.path.join(UPLOAD_FOLDER, f"image_video_{os.urandom(8).hex()}.mp4")
        
        print(f"🎬 Generating image-to-video: {output_name}")
        print(f"   📊 Config: segments={segments}, duration={duration}s, captions={captions}")
        print(f"   🖼️  Images: {image_inputs}")
        
        # ADD DETAILED ERROR HANDLING
        try:
            success = convert_images_to_reel(
                image_inputs=image_inputs,
                user_prompt=prompt,
                output_name=output_name,
                clip_duration=duration,
                segments=segments,
                captions=captions if captions else None,
                text_only=False
            )
            
            print(f"   ✅ convert_images_to_reel returned: {success}")
            print(f"   📁 Output file exists: {os.path.exists(output_name)}")
            
            if os.path.exists(output_name):
                file_size = os.path.getsize(output_name)
                print(f"   📦 File size: {file_size / (1024 * 1024):.2f} MB")
            
        except Exception as convert_error:
            logging.error(f"❌ convert_images_to_reel raised exception: {str(convert_error)}")
            import traceback
            traceback.print_exc()
            
            # Cleanup uploaded files
            if temp_upload_dir and content_type and 'multipart/form-data' in content_type:
                for path in image_inputs:
                    try:
                        if os.path.exists(path):
                            os.remove(path)
                    except Exception as e:
                        logging.warning(f"Failed to delete uploaded image: {path}. Error: {e}")
                try:
                    if os.path.exists(temp_upload_dir):
                        os.rmdir(temp_upload_dir)
                except Exception:
                    pass
            
            return jsonify({'error': f'Video generation error: {str(convert_error)}'}), 500
        
        # Cleanup uploaded files if any (only delete local files, not URLs)
        if temp_upload_dir and content_type and 'multipart/form-data' in content_type:
            for path in image_inputs:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                        logging.info(f"Deleted uploaded image: {path}")
                except Exception as e:
                    logging.warning(f"Failed to delete uploaded image: {path}. Error: {e}")

            try:
                if os.path.exists(temp_upload_dir):
                    os.rmdir(temp_upload_dir)
                    logging.info(f"Deleted temporary upload directory: {temp_upload_dir}")
            except Exception as e:
                logging.warning(f"Failed to delete temporary upload directory: {temp_upload_dir}. Error: {e}")

        # Check if video was actually generated
        if not os.path.exists(output_name):
            logging.error(f"❌ Output file does not exist: {output_name}")
            return jsonify({
                'error': 'Video generation completed but output file was not created',
                'details': 'convert_images_to_reel returned success but no file found'
            }), 500
        
        file_size = os.path.getsize(output_name) / (1024 * 1024)
        
        # Check if file is too small (likely empty or corrupted)
        if file_size < 0.1:  # Less than 100KB
            logging.error(f"❌ Output file is too small: {file_size:.2f} MB")
            return jsonify({
                'error': 'Generated video file is too small (likely corrupted)',
                'file_size_mb': round(file_size, 2)
            }), 500
        
        print(f"✅ Video saved locally: {output_name} ({file_size:.2f} MB)")
        
        print(f"☁️  Uploading to Cloud Storage...")
        cloud_info = cloud_manager.upload_video(output_name, video_type="image")
        
        if cloud_info:
            try:
                os.remove(output_name)
                logging.info(f"Deleted local file: {output_name}")
            except Exception as e:
                logging.warning(f"Failed to delete local file: {output_name}. Error: {e}")
            
            return jsonify({
                'success': True,
                'message': 'Video generated and uploaded to cloud successfully',
                'generated_video_url': cloud_info['public_url'],
                'cloud_path': cloud_info['cloud_path'],
                'file_size_mb': round(file_size, 2)
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Video generated but cloud upload failed',
                'local_path': output_name,
                'file_size_mb': round(file_size, 2),
                'cloud_error': 'Upload to cloud storage failed'
            }), 206
            
    except Exception as e:
        logging.exception("❌ Unexpected error in generate_images_to_video")
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/videos', methods=['GET'])
def list_videos():
    """List all generated videos (local and cloud)"""
    try:
        local_videos = []
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.isfile(filepath) and filename.endswith('.mp4'):
                    file_size = os.path.getsize(filepath) / (1024 * 1024)
                    local_videos.append({
                        'name': filename,
                        'path': filepath,
                        'size_mb': round(file_size, 2),
                        'location': 'local'
                    })
        
        cloud_videos_response = cloud_manager.list_videos()
        cloud_videos = cloud_videos_response.get('videos', []) if cloud_videos_response else []
        
        return jsonify({
            'success': True,
            'local': {
                'videos_folder': UPLOAD_FOLDER,
                'total_videos': len(local_videos),
                'videos': sorted(local_videos, key=lambda x: x['name'])
            },
            'cloud': cloud_videos_response if cloud_videos_response else {'error': 'Failed to fetch cloud videos'},
            'total_all': len(local_videos) + len(cloud_videos)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cloud-videos', methods=['GET'])
def list_cloud_videos():
    """List only cloud storage videos"""
    try:
        result = cloud_manager.list_videos()
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Failed to fetch cloud videos'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cleanup', methods=['POST'])
def cleanup_video():
    """Delete local video (keep in cloud storage)"""
    try:
        data = request.get_json()
        video_path = data.get('video_path')
        
        if not video_path:
            return jsonify({'error': 'Video path is required'}), 400
        
        if not os.path.exists(video_path):
            return jsonify({'error': 'Video file not found'}), 400
            
        if not video_path.startswith(UPLOAD_FOLDER):
            return jsonify({'error': 'Invalid video path - outside allowed directory'}), 400
        
        try:
            os.remove(video_path)
            logging.info(f"Deleted local video file: {video_path}")
            return jsonify({'success': True, 'message': 'Local video deleted successfully (cloud copy preserved)'})
        except Exception as e:
            logging.warning(f"Failed to delete local video file: {video_path}. Error: {e}")
            return jsonify({'error': f'Failed to delete video: {str(e)}'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'local_storage': UPLOAD_FOLDER,
        'cloud_bucket': cloud_manager.bucket_name,
        'brand_id': cloud_manager.brand_id
    })


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Changed from 8080 to 5000
    logging.info("Starting Flask Video Generation API with Ideas Workflow")
    logging.info(f"Current directory: {CURRENT_DIR}")
    logging.info(f"Local videos folder: {UPLOAD_FOLDER}")
    logging.info(f"Cloud bucket: {cloud_manager.bucket_name}")
    logging.info(f"Brand ID: {cloud_manager.brand_id}")
    logging.info(f"Server starting at http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)