import os
import tempfile
import json
from flask import Blueprint, request, send_file, current_app, jsonify
from werkzeug.utils import secure_filename
from video_edit.core import process_with_gemini, process_with_manual_edits

edit_bp = Blueprint('edit', __name__)


@edit_bp.route('/edit', methods=['POST'])
def edit_video():
    """
    POST /api/edit
    Form fields (multipart/form-data):
      - video: file blob (required)
      - user_prompt: natural language instruction (optional)
      - edits_json: JSON array of edits (optional; when provided, Gemini is skipped)
      - use_gemini: 'true' or 'false' (optional; default true if GOOGLE_API_KEY present)

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
    edits_json = request.form.get('edits_json')
    use_gemini_flag = request.form.get('use_gemini')

    # Decide whether to call Gemini (requires GOOGLE_API_KEY env variable)
    google_api_key = os.environ.get('GOOGLE_API_KEY')
    use_gemini = False
    if edits_json:
        use_gemini = False
    else:
        if use_gemini_flag is not None:
            use_gemini = use_gemini_flag.lower() in ('1', 'true', 'yes')
        else:
            use_gemini = bool(google_api_key and user_prompt)

    if not edits_json and not user_prompt:
        os.remove(input_tmp)
        return jsonify({"error": "Either 'edits_json' (manual JSON) or 'user_prompt' must be provided."}), 400

    # Temporary output file
    out_fd, out_tmp = tempfile.mkstemp(suffix='.mp4')
    os.close(out_fd)

    try:
        if edits_json:
            # Manual edits path - edits_json must be valid JSON
            try:
                _ = json.loads(edits_json)
            except Exception as e:
                raise ValueError(f"edits_json is not valid JSON: {e}")
            process_with_manual_edits(input_tmp, edits_json, out_tmp)
        else:
            # Gemini path
            if use_gemini:
                if not google_api_key:
                    raise RuntimeError("Gemini requested but GOOGLE_API_KEY not configured in environment.")
                process_with_gemini(input_tmp, user_prompt, out_tmp, api_key=google_api_key)
            else:
                # If user_prompt provided but Gemini not used, treat prompt as a simple "add music throughout" example
                # For safety we require edits_json or Gemini -- reject otherwise
                raise RuntimeError("No edits_json provided and Gemini usage disabled or not configured.")

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