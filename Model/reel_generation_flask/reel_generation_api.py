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

app = Flask(__name__)
CORS(app)

# Configure upload folder
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(CURRENT_DIR, "videos")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize managers
cloud_manager = CloudStorageManager(
    bucket_name="all_in_one_bucket",
    brand_id="BRAND_123"
)

ideas_generator = ReelIdeasGenerator()

print(f"📁 Video storage folder: {UPLOAD_FOLDER}")


def analyze_content_for_segments(prompt: str, image_paths: list = None) -> tuple:
    """
    Return (segments_per_image, clip_duration_seconds, captions_list)
    """
    try:
        # TEXT-ONLY (no images)
        if not image_paths:
            caption = ""
            if prompt:
                c = prompt.strip()
                caption = c if len(c) <= 120 else (c[:117].rstrip() + "...")
            segments_per_image = 1
            duration = 6
            captions = [caption] if caption else []
            print(f"[analyze] text-only -> segments_per_image={segments_per_image}, duration={duration}")
            return segments_per_image, duration, captions

        num_images = len(image_paths)
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
            filename = os.path.basename(image_paths[0]) if image_paths[0] else ""
            segments_per_image = 1
            duration = 4
            captions = [filename] if filename else []
            print(f"[analyze] single image -> segments_per_image={segments_per_image}, duration={duration}")
            return segments_per_image, duration, captions

        segments_per_image = 1
        duration = 4
        captions = [os.path.basename(p) if p else "" for p in image_paths]
        print(f"[analyze] multiple images -> segments_per_image={segments_per_image}, duration={duration}")
        return segments_per_image, duration, captions

    except Exception as e:
        print(f"Error in content analysis: {e}")
        if image_paths:
            return 1, 4, []
        return 1, 6, []


# ==================== NEW ENDPOINTS: Reel Ideas Workflow ====================

@app.route('/api/reel-generation/ideas', methods=['POST'])
def generate_reel_ideas():
    """
    Generate 3 reel ideas based on initial prompt and optional image
    
    Request:
    {
        "initial_prompt": "string",
        "image": "file (optional)"
    }
    
    Response:
    {
        "success": true,
        "ideas": ["idea1", "idea2", "idea3"]
    }
    """
    try:
        initial_prompt = request.form.get('initial_prompt', '').strip()
        
        if not initial_prompt:
            return jsonify({'error': 'initial_prompt is required'}), 400
        
        print(f"🤖 Generating ideas for prompt: {initial_prompt}")
        
        # Handle optional image
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                temp_dir = tempfile.mkdtemp(prefix="veo_ideas_")
                filename = secure_filename(file.filename)
                image_path = os.path.join(temp_dir, filename)
                file.save(image_path)
                print(f"📸 Image uploaded for context: {filename}")
        
        # Generate ideas
        result = ideas_generator.generate_ideas(
            initial_prompt=initial_prompt,
            image_path=image_path,
            num_ideas=3
        )
        
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
    """
    Generate final video from script
    
    Request:
    {
        "script": "string"
    }
    
    Response:
    {
        "success": true,
        "generated_video_url": "https://...",
        "cloud_path": "gs://...",
        "file_size_mb": float
    }
    """
    try:
        data = request.get_json()
        
        script = data.get('script', '').strip()
        
        if not script:
            return jsonify({'error': 'script is required'}), 400
        
        print(f"🎬 Generating video from script...")
        
        # Generate output filename
        output_name = os.path.join(UPLOAD_FOLDER, f"script_video_{os.urandom(8).hex()}.mp4")
        
        # Use reel_model to generate video from script
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
            print(f"✅ Video generated: {file_size:.2f} MB")
            
            # Upload to Cloud Storage
            print(f"☁️  Uploading to Cloud Storage...")
            cloud_info = cloud_manager.upload_video(output_name, video_type="generated")
            
            if cloud_info:
                return jsonify({
                    'success': True,
                    'message': 'Video generated and uploaded successfully',
                    'generated_video_url': cloud_info['public_url'],
                    'cloud_path': cloud_info['cloud_path'],
                    'file_size_mb': cloud_info['file_size_mb'],
                    'local_path': output_name
                })
            else:
                return jsonify({
                    'error': 'Video generated but cloud upload failed',
                    'local_path': output_name
                }), 206
        else:
            return jsonify({'error': 'Failed to generate video'}), 500
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
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
                return jsonify({
                    'success': True,
                    'video_path': output_name,
                    'message': 'Video generated and uploaded to cloud successfully',
                    'generated_video_url': cloud_info['public_url'],
                    'cloud_path': cloud_info['cloud_path'],
                    'file_size_mb': round(file_size, 2)
                })
            else:
                return jsonify({
                    'success': True,
                    'video_path': output_name,
                    'message': 'Video generated but cloud upload failed',
                    'file_size_mb': round(file_size, 2),
                    'cloud_error': 'Upload to cloud storage failed'
                }), 206
        else:
            return jsonify({'error': 'Failed to generate video'}), 500
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-video/images', methods=['POST'])
def generate_images_to_video():
    """Generate video from images and upload to cloud storage"""
    try:
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
        
        print(f"📸 Processing {len(image_paths)} image(s)")
        
        segments, duration, captions = analyze_content_for_segments(prompt, image_paths)
        output_name = os.path.join(UPLOAD_FOLDER, f"image_video_{os.urandom(8).hex()}.mp4")
        
        print(f"🎬 Generating image-to-video: {output_name}")
        
        success = convert_images_to_reel(
            image_inputs=image_paths,
            user_prompt=prompt,
            output_name=output_name,
            clip_duration=duration,
            segments=segments,
            captions=captions if captions else None,
            text_only=False
        )
        
        for path in image_paths:
            try:
                os.remove(path)
            except:
                pass
        
        try:
            os.rmdir(temp_upload_dir)
        except:
            pass
                
        if success and os.path.exists(output_name):
            file_size = os.path.getsize(output_name) / (1024 * 1024)
            print(f"✅ Video saved locally: {output_name} ({file_size:.2f} MB)")
            
            print(f"☁️  Uploading to Cloud Storage...")
            cloud_info = cloud_manager.upload_video(output_name, video_type="image")
            
            if cloud_info:
                return jsonify({
                    'success': True,
                    'video_path': output_name,
                    'message': 'Video generated and uploaded to cloud successfully',
                    'generated_video_url': cloud_info['public_url'],
                    'cloud_path': cloud_info['cloud_path'],
                    'file_size_mb': round(file_size, 2)
                })
            else:
                return jsonify({
                    'success': True,
                    'video_path': output_name,
                    'message': 'Video generated but cloud upload failed',
                    'file_size_mb': round(file_size, 2),
                    'cloud_error': 'Upload to cloud storage failed'
                }), 206
        else:
            return jsonify({'error': 'Failed to generate video'}), 500
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
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
            filename = os.path.basename(video_path)
            print(f"🗑️  Deleted local: {filename}")
            return jsonify({'success': True, 'message': 'Local video deleted successfully (cloud copy preserved)'})
        except Exception as e:
            print(f"❌ Delete error: {e}")
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
    print(f"\n{'='*70}")
    print(f"🚀 Flask Video Generation API with Ideas Workflow")
    print(f"{'='*70}")
    print(f"📁 Current directory: {CURRENT_DIR}")
    print(f"📁 Local videos folder: {UPLOAD_FOLDER}")
    print(f"☁️  Cloud bucket: {cloud_manager.bucket_name}")
    print(f"🏢 Brand ID: {cloud_manager.brand_id}")
    print(f"🌐 Server: http://localhost:5000")
    print(f"{'='*70}\n")
    print("📋 Available Endpoints:")
    print("   Ideas Workflow:")
    print("   - POST /api/reel-generation/ideas")
    print("   - POST /api/reel-generation/refine-idea")
    print("   - POST /api/reel-generation/regenerate-ideas")
    print("   - POST /api/reel-generation/generate-video-script")
    print("   - POST /api/reel-generation/generate-video")
    print("   Video Generation:")
    print("   - POST /api/generate-video/text")
    print("   - POST /api/generate-video/images")
    print(f"{'='*70}\n")
    app.run(debug=True, port=5000, use_reloader=False)