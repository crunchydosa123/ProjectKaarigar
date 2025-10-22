from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
import os
import io
import json
from werkzeug.utils import secure_filename
from gcs_video_editor import GCSVideoEditor, TRENDING_SONGS
import tempfile
import logging
import gc

# ----------------------------
# Flask App & Logging Setup
# ----------------------------
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
port = int(os.environ.get("PORT", 8080))  # Cloud Run PORT

# Allowed file extensions
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'mp3', 'wav', 'aac', 'm4a', 'ogg', 'flac'}

# Initialize the video editor
video_editor = GCSVideoEditor()


# ----------------------------
# Utility Functions
# ----------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def decode_base64_file(file_data):
    """Decode base64 string to bytes and reset stream position"""
    import base64
    if isinstance(file_data, str):
        try:
            decoded = base64.b64decode(file_data)
            logging.info("Decoded base64 file data, size=%d bytes", len(decoded))
            return io.BytesIO(decoded)
        except Exception as e:
            logging.exception("Failed to decode base64 file data")
            raise ValueError("Invalid base64 file data")
    elif isinstance(file_data, bytes):
        return io.BytesIO(file_data)
    else:
        raise ValueError("File data must be bytes or base64 string")


# ----------------------------
# Routes
# ----------------------------
@app.route('/')
def home():
    return jsonify({
        "message": "GCS Video Editor API",
        "version": "1.0.0",
        "endpoints": {
            "POST /upload": "Upload a video file for editing",
            "POST /edit": "Apply edits to a video",
            "GET /trending-songs": "Get list of trending songs",
            "GET /edited-videos": "List all edited videos",
            "POST /video-info": "Get video information",
            "POST /save-video": "Save edited video to GCS",
            "GET /download/<blob_name>": "Download video",
            "GET /health": "Health check"
        }
    })


@app.route('/upload', methods=['POST'])
def upload_video():
    """Upload a video file for editing"""
    try:
        if 'file' not in request.files:
            logging.warning("No file provided in /upload")
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        if file.filename == '':
            logging.warning("Empty filename in /upload")
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            logging.warning("File type not allowed: %s", file.filename)
            return jsonify({"error": "File type not allowed"}), 400

        # Read file
        file_data = file.read()
        logging.info("Received file /upload: %s, size=%d bytes", file.filename, len(file_data))
        video_stream = io.BytesIO(file_data)

        # Get video info
        video_info = video_editor.get_video_info_from_memory(video_stream)
        if not video_info.get("success"):
            return jsonify({"error": f"Could not process video: {video_info.get('error')}"}), 400

        # Generate session ID
        import uuid
        session_id = str(uuid.uuid4())
        logging.info("Generated session_id=%s", session_id)

        return jsonify({
            "success": True,
            "session_id": session_id,
            "filename": secure_filename(file.filename),
            "video_info": video_info,
            "message": "Video uploaded successfully"
        })

    except Exception as e:
        logging.exception("Unhandled error in /upload")
        return jsonify({"error": str(e)}), 500


@app.route('/edit', methods=['POST'])
def edit_video():
    """Apply edits to a video"""
    video_stream = None
    edited_stream = None
    updated_info = None
    saved_url = None

    try:
        data = request.get_json()
        logging.info("Received /edit request, JSON present=%s", bool(data))

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Validate required fields
        for field in ['file', 'edit_prompt']:
            if field not in data:
                logging.error("Missing required field: %s", field)
                return jsonify({"error": f"Missing required field: {field}"}), 400

        file_data = data['file']
        edit_prompt = data['edit_prompt']
        topic = data.get('topic', 'default')
        save_name = data.get('save_name')

        # Decode file
        video_stream = decode_base64_file(file_data)

        # Apply edit
        logging.info("Applying edit prompt: %s", edit_prompt)
        edited_stream = video_editor.apply_edit(video_stream, edit_prompt)
        if not edited_stream:
            logging.error("apply_edit returned None")
            return jsonify({"error": "Edit operation failed"}), 500

        # Get updated info
        edited_stream.seek(0)
        updated_info = video_editor.get_video_info_from_memory(edited_stream)
        logging.info("Edited video info retrieved")

        # Save to GCS if requested
        if save_name:
            blob_name = f"edited_videos/{topic}/{save_name}"
            if not blob_name.endswith(".mp4"):
                blob_name += ".mp4"
            saved_url = video_editor.upload_video_from_memory(blob_name, edited_stream)
            logging.info("Uploaded edited video to GCS: %s", saved_url)

        # Return edited video as base64
        edited_stream.seek(0)
        edited_base64 = base64.b64encode(edited_stream.read()).decode("utf-8")
        logging.info("Returning edited video base64, length=%d", len(edited_base64))

        return jsonify({
            "success": True,
            "video_info": updated_info,
            "saved_url": saved_url,
            "edited_video": edited_base64,
            "message": "Edit applied successfully"
        })

    except Exception as e:
        logging.exception("Unhandled error in /edit")
        return jsonify({"error": str(e)}), 500

    finally:
        # Cleanup memory
        try:
            if video_stream:
                video_stream.close()
                del video_stream
            if edited_stream:
                edited_stream.close()
                del edited_stream
            gc.collect()
            logging.info("Memory cleared after /edit")
        except Exception as cleanup_error:
            logging.warning("Memory cleanup failed: %s", cleanup_error)


@app.route('/trending-songs', methods=['GET'])
def get_trending_songs():
    try:
        return jsonify({
            "success": True,
            "songs": TRENDING_SONGS
        })
    except Exception as e:
        logging.exception("Error in /trending-songs")
        return jsonify({"error": str(e)}), 500


@app.route('/edited-videos', methods=['GET'])
def get_edited_videos():
    try:
        topic = request.args.get('topic')
        videos = video_editor.list_edited_videos(prefix=topic)
        return jsonify({
            "success": True,
            "videos": videos,
            "count": len(videos)
        })
    except Exception as e:
        logging.exception("Error in /edited-videos")
        return jsonify({"error": str(e)}), 500


@app.route('/video-info', methods=['POST'])
def get_video_info():
    try:
        data = request.get_json()
        if not data or 'file' not in data:
            return jsonify({"error": "No file data provided"}), 400

        video_stream = decode_base64_file(data['file'])
        video_info = video_editor.get_video_info_from_memory(video_stream)

        if not video_info.get("success"):
            return jsonify({"error": f"Could not get video info: {video_info.get('error')}"}), 400

        return jsonify({"success": True, "video_info": video_info})

    except Exception as e:
        logging.exception("Error in /video-info")
        return jsonify({"error": str(e)}), 500


@app.route('/save-video', methods=['POST'])
def save_video():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        for field in ['file', 'topic', 'save_name']:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        video_stream = decode_base64_file(data['file'])
        topic = data['topic']
        save_name = data['save_name']

        blob_name = f"edited_videos/{topic}/{save_name}"
        if not blob_name.endswith(".mp4"):
            blob_name += ".mp4"

        saved_url = video_editor.upload_video_from_memory(blob_name, video_stream)
        if not saved_url:
            return jsonify({"error": "Failed to save video to GCS"}), 500

        logging.info("Saved video to GCS: %s", saved_url)
        return jsonify({
            "success": True,
            "saved_url": saved_url,
            "blob_name": blob_name,
            "message": "Video saved successfully"
        })

    except Exception as e:
        logging.exception("Error in /save-video")
        return jsonify({"error": str(e)}), 500


@app.route('/download/<path:blob_name>', methods=['GET'])
def download_video(blob_name):
    try:
        video_stream = video_editor.download_video_to_memory(blob_name)
        if not video_stream:
            return jsonify({"error": "Video not found"}), 404

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        video_stream.seek(0)
        temp_file.write(video_stream.getvalue())
        temp_file.close()

        @after_this_request
        def cleanup_temp_file(response):
            try:
                os.remove(temp_file.name)
            except Exception as e:
                logging.warning("Failed to delete temp file: %s", e)
            return response

        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=blob_name.split('/')[-1],
            mimetype='video/mp4'
        )

    except Exception as e:
        logging.exception("Error in /download")
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "GCS Video Editor API is running"
    })


# ----------------------------
# Error Handlers
# ----------------------------
@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File too large. Maximum size is 500MB."}), 413


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ----------------------------
# Startup
# ----------------------------
if __name__ == '__main__':
    logging.info("🎬 Starting GCS Video Editor Flask API...")
    logging.info("📋 Listening on port %d", port)
    app.run(debug=True, host='0.0.0.0', port=port)
