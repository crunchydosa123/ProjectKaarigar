from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from reel_model import convert_images_to_reel, optimize_prompt_with_gemini
from reel_ideas_generator import ReelIdeasGenerator
from image_anlayzes import ImageToPromptGenerator
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
    bucket_name="all_in_one_bucket",
    brand_id="BRAND_123"
)

ideas_generator = ReelIdeasGenerator()
image_analyzer = ImageToPromptGenerator()

print(f"📁 Video storage folder: {UPLOAD_FOLDER}")

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


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


# ==================== IMAGE ANALYSIS & PROMPT GENERATION ENDPOINTS ====================

@app.route('/api/image-analysis/analyze', methods=['POST'])
def analyze_image_endpoint():
    """
    Analyze image and extract visual elements
    
    Request:
    {
        "image": file (multipart/form-data)
    }
    
    Response:
    {
        "success": true,
        "analysis": {
            "objects": [...],
            "colors": [...],
            "mood": "...",
            "lighting": "...",
            ...
        }
    }
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        if not file or not file.filename:
            return jsonify({'error': 'No selected file'}), 400
        
        logging.info(f"📸 Analyzing image: {file.filename}")
        
        temp_dir = tempfile.mkdtemp(prefix="img_analysis_")
        filename = secure_filename(file.filename)
        image_path = os.path.join(temp_dir, filename)
        file.save(image_path)
        
        result = image_analyzer.analyze_image_content(image_path)
        
        # Cleanup temp file
        try:
            os.remove(image_path)
            os.rmdir(temp_dir)
        except:
            pass
        
        if result['success']:
            return jsonify({
                'success': True,
                'analysis': result['analysis'],
                'image_file': filename
            })
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logging.error(f"Image analysis failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/image-analysis/generate-prompt', methods=['POST'])
def generate_prompt_from_image():
    """
    Analyze image and generate optimized video prompt
    Returns ONLY the optimized video prompt (no detailed analysis)
    
    Request:
    {
        "image": file (multipart/form-data),
        "user_intent": "optional creative direction"
    }
    
    Response:
    {
        "success": true,
        "prompt": "cinematic video prompt optimized for video generation",
        "image_file": "filename"
    }
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        if not file or not file.filename:
            return jsonify({'error': 'No selected file'}), 400
        
        user_intent = request.form.get('user_intent', None)
        
        logging.info(f"🎬 Generating video prompt for: {file.filename}")
        
        temp_dir = tempfile.mkdtemp(prefix="img_prompt_")
        filename = secure_filename(file.filename)
        image_path = os.path.join(temp_dir, filename)
        file.save(image_path)
        
        # Generate optimized prompt directly
        result = image_analyzer.generate_video_prompt_direct(image_path, user_intent)
        
        # Cleanup temp file
        try:
            os.remove(image_path)
            os.rmdir(temp_dir)
        except:
            pass
        
        if result.get('success'):
            logging.info(f"✅ Video prompt generated successfully")
            return jsonify({
                'success': True,
                'prompt': result.get('prompt'),
                'image_file': filename
            })
        else:
            logging.error(f"Failed to generate prompt: {result.get('error')}")
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to generate prompt')
            }), 500
            
    except Exception as e:
        logging.error(f"Prompt generation failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/image-analysis/segmentation-plan', methods=['POST'])
def segmentation_plan_endpoint():
    """
    Generate multi-segment video plan from single image
    
    Request:
    {
        "image": file (multipart/form-data),
        "num_segments": 3 (optional, default: 3)
    }
    
    Response:
    {
        "success": true,
        "segmentation_plan": {
            "segments": [...],
            "transitions": [...],
            "overall_pacing": "fast/moderate/slow",
            "total_duration": 12
        }
    }
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        if not file or not file.filename:
            return jsonify({'error': 'No selected file'}), 400
        
        num_segments = int(request.form.get('num_segments', 3))
        if num_segments < 1 or num_segments > 10:
            return jsonify({'error': 'num_segments must be between 1 and 10'}), 400
        
        logging.info(f"📐 Creating segmentation plan: {file.filename} ({num_segments} segments)")
        
        temp_dir = tempfile.mkdtemp(prefix="img_segment_")
        filename = secure_filename(file.filename)
        image_path = os.path.join(temp_dir, filename)
        file.save(image_path)
        
        result = image_analyzer.generate_segmentation_plan(image_path, num_segments)
        
        # Cleanup temp file
        try:
            os.remove(image_path)
            os.rmdir(temp_dir)
        except:
            pass
        
        if result['success']:
            return jsonify({
                'success': True,
                'segmentation_plan': result['segmentation_plan'],
                'image_file': filename,
                'recommendation': f"Total video duration: {result['segmentation_plan'].get('total_duration', 'N/A')} seconds"
            })
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logging.error(f"Segmentation planning failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/image-analysis/multi-angle', methods=['POST'])
def multi_angle_endpoint():
    """
    Generate multiple creative prompts from single image
    
    Request:
    {
        "image": file (multipart/form-data),
        "variations": 3 (optional, default: 3)
    }
    
    Response:
    {
        "success": true,
        "multi_angle_prompts": {
            "prompts": [
                {
                    "perspective": "name",
                    "description": "...",
                    "prompt": "...",
                    "duration": 4,
                    "intensity": "low/medium/high",
                    "camera_style": "..."
                },
                ...
            ]
        }
    }
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        if not file or not file.filename:
            return jsonify({'error': 'No selected file'}), 400
        
        num_variations = int(request.form.get('variations', 3))
        if num_variations < 1 or num_variations > 5:
            return jsonify({'error': 'variations must be between 1 and 5'}), 400
        
        logging.info(f"🎨 Generating multi-angle prompts: {file.filename} ({num_variations} variations)")
        
        temp_dir = tempfile.mkdtemp(prefix="img_multiangle_")
        filename = secure_filename(file.filename)
        image_path = os.path.join(temp_dir, filename)
        file.save(image_path)
        
        result = image_analyzer.generate_multi_angle_prompts(image_path, num_variations)
        
        # Cleanup temp file
        try:
            os.remove(image_path)
            os.rmdir(temp_dir)
        except:
            pass
        
        if result['success']:
            return jsonify({
                'success': True,
                'multi_angle_prompts': result['multi_angle_prompts'],
                'image_file': filename,
                'variations_count': len(result['multi_angle_prompts'].get('prompts', []))
            })
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logging.error(f"Multi-angle generation failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/image-analysis/process', methods=['POST'])
def process_images_endpoint():
    """
    Intelligent image processing - handles single or multiple images
    Returns only optimized video prompts (simplified workflow)
    
    Request (Form Data):
    {
        "images": file or files (multipart/form-data),
        "user_intent": "optional creative direction"
    }
    
    Response for Single Image:
    {
        "success": true,
        "workflow": "single_image",
        "image_count": 1,
        "image_file": "filename.jpg",
        "prompt": "optimized video prompt"
    }
    
    Response for Multiple Images:
    {
        "success": true,
        "workflow": "multiple_images",
        "image_count": 3,
        "processed": 3,
        "prompts": [
            {
                "index": 1,
                "image": "filename.jpg",
                "prompt": "optimized video prompt"
            },
            ...
        ]
    }
    """
    try:
        if 'images' not in request.files:
            return jsonify({'error': 'No images provided'}), 400
        
        files = request.files.getlist('images')
        if not files or not any(f for f in files if f.filename):
            return jsonify({'error': 'No selected files'}), 400
        
        user_intent = request.form.get('user_intent', None)
        
        logging.info(f"🖼️  Processing {len(files)} image(s)")
        
        # Save temp images
        temp_dir = tempfile.mkdtemp(prefix="img_process_")
        image_paths = []
        
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                unique_filename = f"{os.urandom(6).hex()}_{filename}"
                filepath = os.path.join(temp_dir, unique_filename)
                file.save(filepath)
                image_paths.append((filepath, filename))
                logging.info(f"  📸 Saved: {filename}")
        
        if not image_paths:
            return jsonify({'error': 'No valid images saved'}), 400
        
        # Process images using new simplified workflow
        result = image_analyzer.process_images([p[0] for p in image_paths], user_intent)
        
        # Cleanup temp files
        try:
            for path, _ in image_paths:
                os.remove(path)
            os.rmdir(temp_dir)
        except Exception as e:
            logging.warning(f"Cleanup warning: {e}")
        
        if result.get('success'):
            return jsonify(result)
        else:
            logging.error(f"Image processing failed: {result.get('error')}")
            return jsonify(result), 500
            
    except Exception as e:
        logging.error(f"Image processing failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/image-analysis/logs', methods=['GET'])
def get_analysis_logs():
    """
    Get analysis operation logs
    
    Response:
    {
        "success": true,
        "logs": [
            "[timestamp] [EVENT_TYPE] message",
            ...
        ],
        "total_entries": 25
    }
    """
    try:
        logs = image_analyzer.get_logs()
        return jsonify({
            'success': True,
            'logs': logs,
            'total_entries': len(logs)
        })
    except Exception as e:
        logging.error(f"Failed to get logs: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/image-analysis/clear-logs', methods=['POST'])
def clear_analysis_logs():
    """
    Clear analysis operation logs
    
    Response:
    {
        "success": true,
        "message": "Logs cleared"
    }
    """
    try:
        image_analyzer.clear_logs()
        return jsonify({
            'success': True,
            'message': 'Analysis logs cleared successfully'
        })
    except Exception as e:
        logging.error(f"Failed to clear logs: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==================== REEL IDEAS WORKFLOW ENDPOINTS ====================

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
    """Generate video from script and upload to cloud storage"""
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


# ==================== VIDEO GENERATION ENDPOINTS ====================

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
                # Delete the local file after successful upload
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
    Generate video from images and upload to cloud storage
    Uses optimized prompts from image analysis
    """
    try:
        if 'images' not in request.files:
            return jsonify({'error': 'No images provided'}), 400
            
        files = request.files.getlist('images')
        if not files or not any(f for f in files if f.filename):
            return jsonify({'error': 'No selected files'}), 400
            
        custom_prompt = request.form.get('prompt', '').strip()
        logging.info(f"📸 Processing {len(files)} image(s)")
        
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
        
        # Generate prompts from images if no custom prompt provided
        if not custom_prompt:
            logging.info("🎯 Generating video prompts from images...")
            result = image_analyzer.process_images(image_paths)
            
            if result.get('success'):
                # Extract prompts based on workflow
                if result.get('workflow') == 'single_image':
                    prompt = result.get('prompt', '')
                else:  # multiple_images
                    # Combine all prompts for sequence
                    prompts = [p.get('prompt', '') for p in result.get('prompts', [])]
                    prompt = ' '.join(prompts) if prompts else ''
            else:
                logging.error("Failed to generate prompts from images")
                return jsonify({
                    'error': 'Failed to analyze images and generate prompts'
                }), 500
        else:
            prompt = custom_prompt
            logging.info(f"Using custom prompt: {prompt[:100]}...")
        
        if not prompt:
            return jsonify({'error': 'Could not generate prompt from images'}), 400
        
        logging.info(f"🎬 Generating video with prompt: {prompt[:100]}...")
        
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
        
        # Cleanup uploaded images
        for path in image_paths:
            try:
                os.remove(path)
                logging.info(f"Deleted uploaded image: {path}")
            except Exception as e:
                logging.warning(f"Failed to delete uploaded image: {path}. Error: {e}")

        try:
            os.rmdir(temp_upload_dir)
            logging.info(f"Deleted temporary upload directory: {temp_upload_dir}")
        except Exception as e:
            logging.warning(f"Failed to delete temporary upload directory: {temp_upload_dir}. Error: {e}")

        if success and os.path.exists(output_name):
            file_size = os.path.getsize(output_name) / (1024 * 1024)
            print(f"✅ Video saved locally: {output_name} ({file_size:.2f} MB)")
            
            print(f"☁️  Uploading to Cloud Storage...")
            cloud_info = cloud_manager.upload_video(output_name, video_type="image")
            
            if cloud_info:
                # Delete the local file after successful upload
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
                    'file_size_mb': round(file_size, 2),
                    'generated_prompt': prompt
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


# ==================== VIDEO MANAGEMENT ENDPOINTS ====================

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
    import os
    import sys

    port = int(os.environ.get("PORT", 5000))
    
    # Startup logging
    logging.info("=" * 80)
    logging.info("🚀 Starting Flask Video Generation API with Image Analysis")
    logging.info("=" * 80)
    logging.info(f"Current directory: {CURRENT_DIR}")
    logging.info(f"Local videos folder: {UPLOAD_FOLDER}")
    logging.info(f"Cloud bucket: {cloud_manager.bucket_name}")
    logging.info(f"Brand ID: {cloud_manager.brand_id}")
    logging.info(f"Server starting at http://0.0.0.0:{port}")
    logging.info("=" * 80)
    
    logging.info("\n📋 Available API Endpoints:\n")
    
    logging.info("   🖼️  IMAGE ANALYSIS & PROMPT GENERATION:")
    logging.info("   - POST /api/image-analysis/analyze (detailed analysis)")
    logging.info("   - POST /api/image-analysis/generate-prompt (optimized prompt only)")
    logging.info("   - POST /api/image-analysis/segmentation-plan")
    logging.info("   - POST /api/image-analysis/multi-angle")
    logging.info("   - POST /api/image-analysis/process (simplified workflow)")
    logging.info("   - GET  /api/image-analysis/logs")
    logging.info("   - POST /api/image-analysis/clear-logs")
    
    logging.info("\n   💡 REEL IDEAS WORKFLOW:")
    logging.info("   - POST /api/reel-generation/ideas")
    logging.info("   - POST /api/reel-generation/refine-idea")
    logging.info("   - POST /api/reel-generation/regenerate-ideas")
    logging.info("   - POST /api/reel-generation/generate-video-script")
    logging.info("   - POST /api/reel-generation/generate-video")
    
    logging.info("\n   🎥 VIDEO GENERATION:")
    logging.info("   - POST /api/generate-video/text")
    logging.info("   - POST /api/generate-video/images (auto-generates prompts from images)")
    
    logging.info("\n   📁 VIDEO MANAGEMENT:")
    logging.info("   - GET  /api/videos")
    logging.info("   - GET  /api/cloud-videos")
    logging.info("   - POST /api/cleanup")
    logging.info("   - GET  /api/health")
    
    logging.info("\n" + "=" * 80 + "\n")
    
    try:
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)
    except OSError as e:
        if "Address already in use" in str(e):
            logging.error(f"❌ Port {port} is already in use!")
            logging.info(f"Try setting a different port: PORT=5001 python reel_generation_api.py")
            sys.exit(1)
        else:
            logging.error(f"❌ Error: {str(e)}")
            sys.exit(1)