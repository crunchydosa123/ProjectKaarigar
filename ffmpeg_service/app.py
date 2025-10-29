from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
import os, io, json, tempfile, logging, base64, requests, gc, uuid
from werkzeug.utils import secure_filename
from gcs_video_editor import GCSVideoEditor, TRENDING_SONGS

# ----------------------------
# Flask Setup
# ----------------------------
app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max
port = int(os.environ.get("PORT", 8080))

video_editor = GCSVideoEditor()
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'mp3', 'wav', 'aac', 'm4a', 'ogg', 'flac'}

# ----------------------------
# Utilities
# ----------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def decode_base64_file(file_data):
    """Decode base64 string to BytesIO stream"""
    try:
        decoded = base64.b64decode(file_data)
        return io.BytesIO(decoded)
    except Exception as e:
        raise ValueError("Invalid base64 file data")

def get_video_stream_from_input(data):
    """Handle both base64 and video_url inputs"""
    if 'file' in data:
        logging.info("📦 Decoding video from base64 data")
        return decode_base64_file(data['file'])
    elif 'video_url' in data:
        video_url = data['video_url']
        logging.info(f"🌐 Downloading video from URL: {video_url}")
        response = requests.get(video_url, stream=True)
        if response.status_code != 200:
            raise ValueError(f"Failed to download video (HTTP {response.status_code})")
        return io.BytesIO(response.content)
    else:
        raise ValueError("Either 'file' or 'video_url' must be provided")

# ----------------------------
# Routes
# ----------------------------
@app.route('/')
def home():
    return jsonify({
        "message": "GCS Video Editor API (URL-Compatible)",
        "version": "2.0.0",
        "endpoints": {
            "POST /upload": "Get video info using file or URL",
            "POST /edit": "Edit video (file or URL)",
            "POST /add-trending-audio": "Add trending audio (file or URL)",
            "POST /video-info": "Get video metadata (file or URL)",
            "POST /save-video": "Save edited video to GCS",
            "GET /trending-songs": "List trending songs",
            "GET /edited-videos": "List all edited videos",
            "GET /download/<blob_name>": "Download a GCS video",
            "GET /health": "Health check"
        }
    })

# ----------------------------
# Upload
# ----------------------------
@app.route('/upload', methods=['POST'])
def upload_video():
    """Upload or fetch a video for metadata extraction"""
    try:
        if request.files.get('file'):
            # traditional upload
            file = request.files['file']
            if file.filename == '' or not allowed_file(file.filename):
                return jsonify({"error": "Invalid file"}), 400
            video_stream = io.BytesIO(file.read())
            filename = secure_filename(file.filename)
        else:
            # new URL-based method
            data = request.get_json()
            if not data or 'video_url' not in data:
                return jsonify({"error": "Missing video_url"}), 400
            video_stream = get_video_stream_from_input(data)
            filename = data['video_url'].split('/')[-1]

        video_info = video_editor.get_video_info_from_memory(video_stream)
        if not video_info.get("success"):
            return jsonify({"error": "Failed to process video"}), 400

        session_id = str(uuid.uuid4())
        return jsonify({
            "success": True,
            "session_id": session_id,
            "filename": filename,
            "video_info": video_info
        })

    except Exception as e:
        logging.exception("Error in /upload")
        return jsonify({"error": str(e)}), 500

# ----------------------------
# Edit
# ----------------------------
@app.route('/edit', methods=['POST'])
def edit_video():
    """Apply edit prompt to video (supports file or URL)"""
    try:
        data = request.get_json()
        if not data or 'edit_prompt' not in data:
            return jsonify({"error": "Missing edit_prompt"}), 400

        video_stream = get_video_stream_from_input(data)
        edited_stream = video_editor.apply_edit(video_stream, data['edit_prompt'])
        if not edited_stream:
            return jsonify({"error": "Edit operation failed"}), 500

        updated_info = video_editor.get_video_info_from_memory(edited_stream)
        save_name = data.get('save_name')
        saved_url = None
        if save_name:
            topic = data.get('topic', 'default')
            blob_name = f"edited_videos/{topic}/{save_name}.mp4"
            saved_url = video_editor.upload_video_from_memory(blob_name, edited_stream)

        edited_stream.seek(0)
        edited_base64 = base64.b64encode(edited_stream.read()).decode("utf-8")

        return jsonify({
            "success": True,
            "video_info": updated_info,
            "saved_url": saved_url,
        })

    except Exception as e:
        logging.exception("Error in /edit")
        return jsonify({"error": str(e)}), 500

# ----------------------------
# Add Trending Audio
# ----------------------------
@app.route('/add-trending-audio', methods=['POST'])
def add_trending_audio():
    """Add trending audio to video (file or URL)"""
    try:
        data = request.get_json()
        if not data or 'song_id' not in data:
            return jsonify({"error": "Missing song_id"}), 400

        video_stream = get_video_stream_from_input(data)
        edited_stream = video_editor.add_trending_audio(video_stream, data['song_id'])
        if not edited_stream:
            return jsonify({"error": "Audio addition failed"}), 500

        updated_info = video_editor.get_video_info_from_memory(edited_stream)
        save_name = data.get('save_name')
        saved_url = None
        if save_name:
            topic = data.get('topic', 'default')
            blob_name = f"edited_videos/{topic}/{save_name}.mp4"
            saved_url = video_editor.upload_video_from_memory(blob_name, edited_stream)

        edited_stream.seek(0)
        encoded = base64.b64encode(edited_stream.read()).decode("utf-8")

        return jsonify({
            "success": True,
            "video_info": updated_info,
            "saved_url": saved_url,
        })

    except Exception as e:
        logging.exception("Error in /add-trending-audio")
        return jsonify({"error": str(e)}), 500

# ----------------------------
# Video Info
# ----------------------------
@app.route('/video-info', methods=['POST'])
def get_video_info():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON data"}), 400
        video_stream = get_video_stream_from_input(data)
        video_info = video_editor.get_video_info_from_memory(video_stream)
        return jsonify({"success": True, "video_info": video_info})
    except Exception as e:
        logging.exception("Error in /video-info")
        return jsonify({"error": str(e)}), 500

# ----------------------------
# Save Video
# ----------------------------
@app.route('/save-video', methods=['POST'])
def save_video():
    try:
        data = request.get_json()
        if not data or 'save_name' not in data:
            return jsonify({"error": "Missing save_name"}), 400

        video_stream = get_video_stream_from_input(data)
        topic = data.get('topic', 'default')
        blob_name = f"edited_videos/{topic}/{data['save_name']}.mp4"

        saved_url = video_editor.upload_video_from_memory(blob_name, video_stream)
        return jsonify({"success": True, "saved_url": saved_url, "blob_name": blob_name})
    except Exception as e:
        logging.exception("Error in /save-video")
        return jsonify({"error": str(e)}), 500

# ----------------------------
# Misc
# ----------------------------
@app.route('/trending-songs', methods=['GET'])
def trending_songs():
    return jsonify({"success": True, "songs": TRENDING_SONGS})

@app.route('/edited-videos', methods=['GET'])
def get_edited_videos():
    try:
        topic = request.args.get('topic')
        videos = video_editor.list_edited_videos(prefix=topic)
        return jsonify({"success": True, "videos": videos})
    except Exception as e:
        logging.exception("Error in /edited-videos")
        return jsonify({"error": str(e)}), 500

@app.route('/download/<path:blob_name>', methods=['GET'])
def download_video(blob_name):
    try:
        video_stream = video_editor.download_video_to_memory(blob_name)
        if not video_stream:
            return jsonify({"error": "Not found"}), 404
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        video_stream.seek(0)
        temp_file.write(video_stream.read())
        temp_file.close()

        @after_this_request
        def cleanup(response):
            os.remove(temp_file.name)
            return response

        return send_file(temp_file.name, as_attachment=True, download_name=os.path.basename(blob_name))
    except Exception as e:
        logging.exception("Error in /download")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

# ----------------------------
# Startup
# ----------------------------
if __name__ == '__main__':
    logging.info("🚀 Starting GCS Video Editor API (URL-Compatible)")
    app.run(debug=True, host='0.0.0.0', port=port)
