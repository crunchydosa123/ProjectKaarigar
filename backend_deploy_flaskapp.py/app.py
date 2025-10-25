from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import io
import json
from werkzeug.utils import secure_filename
from gcs_video_editor import GCSVideoEditor
import tempfile
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize the video editor
video_editor = GCSVideoEditor()

# Allowed file extensions
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'mp3', 'wav', 'aac', 'm4a', 'ogg', 'flac'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    """Home endpoint with API documentation"""
    return jsonify({
        "message": "GCS Video Editor API",
        "version": "1.0.0",
        "endpoints": {
            "POST /upload": "Upload a video file for editing",
            "POST /edit": "Apply edits to a video",
            "GET /trending-songs": "Get list of trending songs",
            "GET /edited-videos": "List all edited videos",
            "GET /video-info": "Get video information",
            "POST /save-video": "Save edited video to GCS"
        }
    })

@app.route('/upload', methods=['POST'])
def upload_video():
    """Upload a video file for editing"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed"}), 400
        
        # Read file into memory
        file_data = file.read()
        video_stream = io.BytesIO(file_data)
        
        # Get video info
        video_info = video_editor.get_video_info_from_memory(video_stream)
        
        if not video_info.get("success"):
            return jsonify({"error": f"Could not process video: {video_info.get('error')}"}), 400
        
        # Generate a unique session ID
        import uuid
        session_id = str(uuid.uuid4())
        
        # Store video stream in memory (in production, you'd use Redis or similar)
        # For now, we'll return the video info and expect the client to re-upload for editing
        return jsonify({
            "success": True,
            "session_id": session_id,
            "filename": secure_filename(file.filename),
            "video_info": video_info,
            "message": "Video uploaded successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/edit', methods=['POST'])
def edit_video():
    """Apply edits to a video"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Required fields
        required_fields = ['file', 'edit_prompt']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Get file data (base64 encoded or file content)
        file_data = data['file']
        edit_prompt = data['edit_prompt']
        
        # Optional fields
        topic = data.get('topic', 'default')
        save_name = data.get('save_name')
        
        # Convert base64 to bytes if needed
        if isinstance(file_data, str):
            import base64
            try:
                file_data = base64.b64decode(file_data)
            except:
                return jsonify({"error": "Invalid base64 file data"}), 400
        
        # Create video stream
        video_stream = io.BytesIO(file_data)
        
        # Apply the edit
        edited_stream = video_editor.apply_edit(video_stream, edit_prompt)
        
        if not edited_stream:
            return jsonify({"error": "Edit operation failed"}), 500
        
        # Get updated video info
        updated_info = video_editor.get_video_info_from_memory(edited_stream)
        
        # Save to GCS if requested
        saved_url = None
        if save_name:
            blob_name = f"edited_videos/{topic}/{save_name}"
            if not blob_name.endswith('.mp4'):
                blob_name += '.mp4'
            
            saved_url = video_editor.upload_video_from_memory(blob_name, edited_stream)
        
        # Convert edited video to base64 for response
        edited_stream.seek(0)
        edited_data = edited_stream.getvalue()
        import base64
        edited_base64 = base64.b64encode(edited_data).decode('utf-8')
        
        return jsonify({
            "success": True,
            "edited_video": edited_base64,
            "video_info": updated_info,
            "saved_url": saved_url,
            "message": "Edit applied successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/trending-songs', methods=['GET'])
def get_trending_songs():
    """Get list of trending songs"""
    try:
        from gcs_video_editor import TRENDING_SONGS
        return jsonify({
            "success": True,
            "songs": TRENDING_SONGS
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/edited-videos', methods=['GET'])
def get_edited_videos():
    """List all edited videos from GCS"""
    try:
        topic = request.args.get('topic')
        videos = video_editor.list_edited_videos(prefix=topic)
        
        return jsonify({
            "success": True,
            "videos": videos,
            "count": len(videos)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/video-info', methods=['POST'])
def get_video_info():
    """Get video information"""
    try:
        data = request.get_json()
        
        if not data or 'file' not in data:
            return jsonify({"error": "No file data provided"}), 400
        
        file_data = data['file']
        
        # Convert base64 to bytes if needed
        if isinstance(file_data, str):
            import base64
            try:
                file_data = base64.b64decode(file_data)
            except:
                return jsonify({"error": "Invalid base64 file data"}), 400
        
        # Create video stream
        video_stream = io.BytesIO(file_data)
        
        # Get video info
        video_info = video_editor.get_video_info_from_memory(video_stream)
        
        if not video_info.get("success"):
            return jsonify({"error": f"Could not get video info: {video_info.get('error')}"}), 400
        
        return jsonify({
            "success": True,
            "video_info": video_info
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/save-video', methods=['POST'])
def save_video():
    """Save edited video to GCS"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        required_fields = ['file', 'topic', 'save_name']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        file_data = data['file']
        topic = data['topic']
        save_name = data['save_name']
        
        # Convert base64 to bytes if needed
        if isinstance(file_data, str):
            import base64
            try:
                file_data = base64.b64decode(file_data)
            except:
                return jsonify({"error": "Invalid base64 file data"}), 400
        
        # Create video stream
        video_stream = io.BytesIO(file_data)
        
        # Create blob name
        blob_name = f"edited_videos/{topic}/{save_name}"
        if not blob_name.endswith('.mp4'):
            blob_name += '.mp4'
        
        # Upload to GCS
        saved_url = video_editor.upload_video_from_memory(blob_name, video_stream)
        
        if not saved_url:
            return jsonify({"error": "Failed to save video to GCS"}), 500
        
        return jsonify({
            "success": True,
            "saved_url": saved_url,
            "blob_name": blob_name,
            "message": "Video saved successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<path:blob_name>', methods=['GET'])
def download_video(blob_name):
    """Download a video from GCS"""
    try:
        # Download video from GCS
        video_stream = video_editor.download_video_to_memory(blob_name)
        
        if not video_stream:
            return jsonify({"error": "Video not found"}), 404
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        video_stream.seek(0)
        temp_file.write(video_stream.getvalue())
        temp_file.close()
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=blob_name.split('/')[-1],
            mimetype='video/mp4'
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "GCS Video Editor API is running"
    })

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum size is 500MB."}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("🎬 Starting GCS Video Editor Flask API...")
    print("📋 Available endpoints:")
    print("  POST /upload - Upload video file")
    print("  POST /edit - Apply edits to video")
    print("  GET /trending-songs - Get trending songs")
    print("  GET /edited-videos - List edited videos")
    print("  POST /video-info - Get video information")
    print("  POST /save-video - Save video to GCS")
    print("  GET /download/<blob_name> - Download video")
    print("  GET /health - Health check")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
