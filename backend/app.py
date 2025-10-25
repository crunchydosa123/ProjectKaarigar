from flask import Flask, session
from flask_cors import CORS
from routes.testing import testing_bp
from routes.auth import auth_bp

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
    print("  🧪 Testing: /testing/*")
    print("  📊 Health: /health")
    app.run(debug=True, host='0.0.0.0', port=5000)
