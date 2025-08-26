import os
import tempfile
from flask import Blueprint, request, send_file, current_app, jsonify
from werkzeug.utils import secure_filename
from video_edit.core import process_with_gemini

edit_bp = Blueprint('edit', __name__)


@edit_bp.route('/edit', methods=['POST'])
def edit_video():
    """
    POST /api/edit
    Form fields (multipart/form-data):
      - video: file blob (required)
      - user_prompt: natural language instruction (required)

    Returns the edited video as an attachment (video/mp4) on success.
    """
    
    if 'video' not in request.files:
        return jsonify({"error": "No 'video' file part"}), 400

    vid_file = request.files['video']
    if vid_file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    # Save uploaded file to a temp path
    fd, input_tmp = tempfile.mkstemp(suffix='.' + secure_filename(vid_file.filename).rsplit('.', 1)[-1])
    os.close(fd)
    try:
        vid_file.save(input_tmp)
    except Exception as e:
        try:
            os.remove(input_tmp)
        except Exception:
            pass
        return jsonify({"error": f"Failed to save uploaded file: {e}"}), 500

    user_prompt = request.form.get('user_prompt', '').strip()

    if not user_prompt:
        os.remove(input_tmp)
        return jsonify({"error": "user_prompt must be provided."}), 400

    google_api_key = os.environ.get('GOOGLE_API_KEY')
    if not google_api_key:
        raise RuntimeError("GOOGLE_API_KEY not configured in environment.")

    # Temporary output file
    out_fd, out_tmp = tempfile.mkstemp(suffix='.mp4')
    os.close(out_fd)

    try:
        process_with_gemini(input_tmp, user_prompt, out_tmp, api_key=google_api_key)

        # Stream the resulting file back
        return send_file(out_tmp, as_attachment=True, download_name='edited.mp4', mimetype='video/mp4')

    except Exception as e:
        current_app.logger.exception('Video edit failed')
        return jsonify({"error": str(e)}), 500

    finally:
        # cleanup input file and output file will be removed by the runtime or left for the sending to finish
        try:
            if os.path.exists(input_tmp):
                os.remove(input_tmp)
        except Exception:
            pass
        # Note: out_tmp is returned via send_file; if you want to remove it after send, use file streaming with generator.