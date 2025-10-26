from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from reel_model import convert_images_to_reel, optimize_prompt_with_gemini
from werkzeug.utils import secure_filename
import tempfile
import json

app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), "video_generation_uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def analyze_content_for_segments(prompt: str, image_paths: list = None) -> tuple:
    """
    Return (segments_per_image, clip_duration_seconds, captions_list)

    Important:
      - convert_images_to_reel expects `segments` to mean "segments per image".
        For text-only mode convert_images_to_reel treats `segments` as total segments.
      - To get exactly one clip per image, return segments_per_image = 1.
    """
    try:
        # TEXT-ONLY (no images)
        if not image_paths:
            caption = ""
            if prompt:
                c = prompt.strip()
                caption = c if len(c) <= 120 else (c[:117].rstrip() + "...")
            segments_per_image = 1        # for text-only this becomes total segments = 1
            duration = 6                 # 5-6s requested; using 6s
            captions = [caption] if caption else []
            print(f"[analyze] text-only -> segments_per_image={segments_per_image}, duration={duration}, captions={captions}")
            return segments_per_image, duration, captions

        # Normalize and count images
        num_images = len(image_paths)
        if num_images == 0:
            # fallback to text-only behavior
            caption = ""
            if prompt:
                c = prompt.strip()
                caption = c if len(c) <= 120 else (c[:117].rstrip() + "...")
            segments_per_image = 1
            duration = 6
            captions = [caption] if caption else []
            print(f"[analyze] empty image list -> segments_per_image={segments_per_image}, duration={duration}, captions={captions}")
            return segments_per_image, duration, captions

        # SINGLE IMAGE -> 1 segment of 4s
        if num_images == 1:
            filename = os.path.basename(image_paths[0]) if image_paths[0] else ""
            segments_per_image = 1
            duration = 4
            captions = [filename] if filename else []
            print(f"[analyze] single image -> segments_per_image={segments_per_image}, duration={duration}, captions={captions}")
            return segments_per_image, duration, captions

        # MULTIPLE IMAGES -> 1 segment per image, 4s each
        segments_per_image = 1
        duration = 4
        captions = [os.path.basename(p) if p else "" for p in image_paths]
        print(f"[analyze] multiple images -> segments_per_image={segments_per_image}, duration={duration}, captions={captions}")
        return segments_per_image, duration, captions

    except Exception as e:
        print(f"Error in content analysis: {e}")
        # fallback: 1 segment per image of 4s, or text fallback
        if image_paths:
            return 1, 4, []
        return 1, 6, []

@app.route('/api/generate-video/text', methods=['POST'])
def generate_text_to_video():
    try:
        data = request.get_json()
        
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Prompt is required'}), 400
            
        prompt = data['prompt']
        
        # Analyze content to determine structure
        segments, duration, captions = analyze_content_for_segments(prompt)
        
        # Generate output filename
        output_name = os.path.join(UPLOAD_FOLDER, f"text_video_{os.urandom(8).hex()}.mp4")
        
        # Call the conversion function with text-only mode
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
            return jsonify({
                'success': True,
                'video_path': output_name,
                'message': 'Video generated successfully',
                'segments': segments,
                'duration': duration,
                'captions': captions
            })
        else:
            return jsonify({'error': 'Failed to generate video'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-video/images', methods=['POST'])
def generate_images_to_video():
    try:
        # Check if files were uploaded
        if 'images' not in request.files:
            return jsonify({'error': 'No images provided'}), 400
            
        files = request.files.getlist('images')
        if not files or not any(f for f in files if f.filename):
            return jsonify({'error': 'No selected files'}), 400
            
        # Get prompt
        prompt = request.form.get('prompt')
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400
            
        # Save uploaded files to temporary location
        image_paths = []
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                # make filename unique to avoid clobbering
                unique_filename = f"{os.urandom(6).hex()}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(filepath)
                image_paths.append(filepath)
                
        if not image_paths:
            return jsonify({'error': 'No valid images uploaded'}), 400
            
        # Analyze content to determine structure
        segments, duration, captions = analyze_content_for_segments(prompt, image_paths)
            
        # Generate output filename
        output_name = os.path.join(UPLOAD_FOLDER, f"image_video_{os.urandom(8).hex()}.mp4")
        
        # Call the conversion function
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
            except:
                pass
                
        if success and os.path.exists(output_name):
            return jsonify({
                'success': True,
                'video_path': output_name,
                'message': 'Video generated successfully',
                'segments': segments,
                'duration': duration,
                'captions': captions
            })
        else:
            return jsonify({'error': 'Failed to generate video'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cleanup', methods=['POST'])
def cleanup_video():
    try:
        data = request.get_json()
        video_path = data.get('video_path')
        
        if not video_path or not os.path.exists(video_path):
            return jsonify({'error': 'Invalid video path'}), 400
            
        # Only allow deletion of files in our upload folder
        if not video_path.startswith(UPLOAD_FOLDER):
            return jsonify({'error': 'Invalid video path'}), 400
            
        os.remove(video_path)
        return jsonify({'success': True, 'message': 'Video cleaned up successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
