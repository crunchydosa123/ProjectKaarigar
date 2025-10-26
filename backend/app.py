from flask import Flask, session
from flask_cors import CORS
from routes.testing import testing_bp
from routes.auth import auth_bp
from routes.conversational import conversational_bp
from routes.logo_generation import logo_bp
from routes.profile_management import profile_bp
from routes.media_upload import media_bp
from routes.reel_generation import reel_bp
from routes.image_generation import image_gen_bp
from routes.image_editing import image_edit_bp

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'http://localhost:5173', 'http://127.0.0.1:3000', 'http://127.0.0.1:5173'], supports_credentials=True)

# Simple configuration - no secrets or encryption
app.config['SECRET_KEY'] = 'project-kaarigar-simple-key-2025'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = False  # Allow frontend access
app.config['SESSION_COOKIE_SAMESITE'] = None  # Remove SameSite restrictions
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# Register blueprints
app.register_blueprint(testing_bp, url_prefix="/testing")
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(conversational_bp, url_prefix="/api/conversational")
app.register_blueprint(logo_bp, url_prefix="/api/logo")
app.register_blueprint(profile_bp, url_prefix="/api/profile")
app.register_blueprint(media_bp, url_prefix="/api/media")
app.register_blueprint(reel_bp, url_prefix="/api/reel")
app.register_blueprint(image_gen_bp, url_prefix="/api/image-gen")
app.register_blueprint(image_edit_bp, url_prefix="/api/image-edit")

@app.route('/')
def home():
    return {
        "message": "Project Kaarigar Backend API",
        "version": "1.0.0",
        "endpoints": {
            "authentication": {
                "POST /api/auth/signup": "User signup",
                "POST /api/auth/login": "User login", 
                "POST /api/auth/logout": "User logout",
                "GET /api/auth/profile": "Get user profile",
                "GET /api/auth/session": "Check session status",
                "GET /api/auth/health": "Auth service health check"
            },
            "conversational": {
                "POST /api/conversational/start": "Start conversational onboarding",
                "POST /api/conversational/message": "Send text message in conversation",
                "POST /api/conversational/audio-message": "Send audio message in conversation",
                "GET /api/conversational/status/<kaarigar_id>": "Get conversation status",
                "GET /api/conversational/list": "List user conversations",
                "GET /api/conversational/health": "Conversational service health check"
            },
            "logo_generation": {
                "POST /api/logo/generate": "Generate logo from conversation data",
                "GET /api/logo/get-logo": "Get user's current logo",
                "GET /api/logo/health": "Logo generation service health check"
            },
            "profile_management": {
                "GET /api/profile/get-profile-data": "Get and generate profile data using Gemini",
                "POST /api/profile/save-profile": "Save profile data to Firestore",
                "GET /api/profile/get-saved-profile": "Get saved profile data",
                "GET /api/profile/health": "Profile management service health check"
            },
            "media_upload": {
                "POST /api/media/upload": "Upload media files to Cloud Storage",
                "GET /api/media/list": "List user's uploaded media (all types)",
                "GET /api/media/list/images": "List user's uploaded images only",
                "GET /api/media/list/videos": "List user's uploaded videos only",
                "DELETE /api/media/delete/<media_id>": "Delete media by ID from both Firestore and Cloud Storage",
                "GET /api/media/health": "Media upload service health check"
            },
            "reel_generation": {
                "POST /api/reel/generate-reel": "Generate reel from selected images using Veo 3.1",
                "GET /api/reel/get-generated-reels": "List user's generated reels",
                "GET /api/reel/health": "Reel generation service health check"
            },
            "image_generation": {
                "POST /api/image-gen/generate-image": "Generate image from text prompt or reference image using Imagen/Gemini",
                "GET /api/image-gen/get-generated-images": "List user's generated images",
                "GET /api/image-gen/health": "Image generation service health check"
            },
            "image_editing": {
                "POST /api/image-edit/analyze-image": "Analyze image and generate creative editing suggestions using Gemini",
                "POST /api/image-edit/edit-image": "Edit image using AI-generated or custom prompt using Gemini",
                "GET /api/image-edit/health": "Image editing service health check"
            },
            "testing": {
                "GET /testing/": "Testing route",
                "POST /testing/data": "Testing data endpoint"
            }
        }
    }

@app.route('/health')
def health_check():
    return {
        "status": "healthy",
        "service": "Project Kaarigar Backend",
        "timestamp": "2025-01-22T16:30:00Z"
    }

if __name__ == '__main__':
    print("🚀 Starting Project Kaarigar Backend...")
    print("📋 Available endpoints:")
    print("  🔐 Authentication: /api/auth/*")
    print("  💬 Conversational: /api/conversational/*")
    print("  🎨 Logo Generation: /api/logo/*")
    print("  👤 Profile Management: /api/profile/*")
    print("  📁 Media Upload: /api/media/*")
    print("  🎬 Reel Generation: /api/reel/*")
    print("  🎨 Image Generation: /api/image-gen/*")
    print("  ✏️ Image Editing: /api/image-edit/*")
    print("  🧪 Testing: /testing/*")
    print("  📊 Health: /health")
    app.run(debug=True, host='0.0.0.0', port=5000)
