from flask import Flask
from routes.edit_routes import edit_bp
import os




def create_app():
    app = Flask(__name__)
    # config: optional
    app.config.from_mapping({
    "MAX_CONTENT_LENGTH": 1024 * 1024 * 1024, # 1GB max upload by default
    })


    # Register blueprints
    app.register_blueprint(edit_bp, url_prefix="/api")


    @app.route("/", methods=["GET"])
    def idx():
        return "Flask Video Editor API. Use POST /api/edit to upload video and user_prompt."


    return app




if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)