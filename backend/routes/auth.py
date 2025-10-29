from flask import Blueprint, request, jsonify, session
from flask_cors import CORS
import uuid
import json
from datetime import datetime
import os
import sys

# Add the parent directory to the path to import Database_Setup modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from google.cloud import firestore
    from Database_Setup.firestore_nosql_storage import create_document, get_document, query_documents
    print("✅ Successfully imported Firestore modules")
    FIRESTORE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Warning: Firestore not available: {e}")
    print(f"❌ Import error details: {e}")
    FIRESTORE_AVAILABLE = False

# Create blueprint
auth_bp = Blueprint('auth_bp', __name__)

# Configuration
PROJECT_ID = "karigar-475215"
COLLECTION_NAME = "users"

# Initialize Firestore client
if FIRESTORE_AVAILABLE:
    try:
        print(f"🔧 Initializing Firestore client for project: {PROJECT_ID}")
        db = firestore.Client(project=PROJECT_ID)
        print("✅ Firestore client initialized successfully")
        print(f"📊 Project: {db.project}")
    except Exception as e:
        print(f"❌ Firestore initialization failed: {e}")
        import traceback
        traceback.print_exc()
        FIRESTORE_AVAILABLE = False
else:
    print("⚠️ Firestore not available - running in fallback mode")

def generate_user_id():
    """Generate a simple sequential user ID (user1, user2, user3, etc.)"""
    if not FIRESTORE_AVAILABLE:
        return "user1"  # Fallback for testing
    
    try:
        # Get the current highest user number
        users_ref = db.collection(COLLECTION_NAME)
        docs = users_ref.stream()
        
        max_user_num = 0
        for doc in docs:
            doc_id = doc.id
            if doc_id.startswith('user') and doc_id[4:].isdigit():
                user_num = int(doc_id[4:])
                max_user_num = max(max_user_num, user_num)
        
        # Return next user ID
        next_user_num = max_user_num + 1
        return f"user{next_user_num}"
        
    except Exception as e:
        print(f"❌ Error generating user ID: {e}")
        # Fallback to timestamp-based ID
        return f"user_{int(datetime.utcnow().timestamp())}"

def create_mock_profile(user_id, email, name=None):
    """Create mock profile data for new users"""
    if not name:
        name = email.split('@')[0].title()
    
    return {
        "userId": user_id,
        "name": name,
        "email": email,
        "occupation": "Artisan",
        "languages": ["en", "hi"],
        "bio": f"Welcome to Project Kaarigar! I'm {name}, a passionate artisan.",
        "username": email.split('@')[0].lower(),
        "brandId": f"BRAND_{user_id.upper()}",
        "profileImage": f"https://ui-avatars.com/api/?name={name}&background=random",
        "createdAt": datetime.utcnow().isoformat(),
        "lastLogin": datetime.utcnow().isoformat(),
        "isActive": True,
        "preferences": {
            "language": "en",
            "notifications": True,
            "theme": "light"
        },
        "stats": {
            "videosCreated": 0,
            "productsListed": 0,
            "totalViews": 0
        }
    }

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """User signup endpoint"""
    print("🚀 SIGNUP REQUEST RECEIVED")
    try:
        data = request.get_json()
        print(f"📥 Request data: {data}")
        
        if not data:
            print("❌ No data provided")
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        name = data.get('name', '').strip()
        
        print(f"📧 Email: {email}")
        print(f"👤 Name: {name}")
        print(f"🔑 Password: {password}")
        
        # Validation
        if not email or not password:
            print("❌ Missing email or password")
            return jsonify({"error": "Email and password are required"}), 400
        
        if len(password) < 6:
            print("❌ Password too short")
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        if '@' not in email:
            print("❌ Invalid email format")
            return jsonify({"error": "Invalid email format"}), 400
        
        # Check if user already exists
        if FIRESTORE_AVAILABLE:
            try:
                print("🔍 Checking if user already exists...")
                existing_users = query_documents("email", "==", email)
                print(f"🔍 Existing users found: {len(existing_users) if existing_users else 0}")
                if existing_users:
                    print("❌ User already exists")
                    return jsonify({"error": "User already exists with this email"}), 409
            except Exception as e:
                print(f"❌ Error checking existing user: {e}")
                return jsonify({"error": "Database error"}), 500
        else:
            print("⚠️ Firestore not available, skipping user check")
        
        # Create user data (no password hashing for simplicity)
        user_id = generate_user_id()
        print(f"🆔 Generated user ID: {user_id}")
        
        user_data = {
            "userId": user_id,
            "email": email,
            "password": password,  # Store password as plain text for simplicity
            "name": name or email.split('@')[0].title(),
            "createdAt": datetime.utcnow().isoformat(),
            "lastLogin": datetime.utcnow().isoformat(),
            "isActive": True
        }
        
        print(f"👤 User data to save: {user_data}")
        
        # Create mock profile
        profile_data = create_mock_profile(user_id, email, name)
        print(f"📋 Profile data to save: {profile_data}")
        
        # Save to Firestore
        if FIRESTORE_AVAILABLE:
            try:
                print("💾 Saving user to Firestore...")
                # Save user credentials to users collection
                user_doc_id = create_document(user_data, user_id)
                print(f"✅ User saved with ID: {user_doc_id}")
                
                # Save profile data to profiles collection (separate collection)
                print("💾 Saving profile to Firestore...")
                # Import the profile creation function with different collection
                from Database_Setup.firestore_nosql_storage import db
                profile_collection = db.collection("profiles")
                profile_doc_ref = profile_collection.document(f"profile_{user_id}")
                profile_doc_ref.set(profile_data)
                print(f"✅ Profile saved with ID: profile_{user_id}")
                
                print(f"✅ User created successfully: {user_id}")
            except Exception as e:
                print(f"❌ Error saving to Firestore: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({"error": "Failed to create user"}), 500
        else:
            print("⚠️ Firestore not available, skipping database save")
        
        # Create session
        print("🔐 Creating session...")
        session['user_id'] = user_id
        session['email'] = email
        session['name'] = user_data['name']
        session['is_authenticated'] = True
        print(f"✅ Session created: {session}")
        
        response_data = {
            "success": True,
            "message": "User created successfully",
            "user": {
                "userId": user_id,
                "email": email,
                "name": user_data['name']
            },
            "profile": profile_data
        }
        
        print(f"📤 Sending response: {response_data}")
        return jsonify(response_data), 201
        
    except Exception as e:
        print(f"❌ Signup error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    print("🚀 LOGIN REQUEST RECEIVED")
    try:
        data = request.get_json()
        print(f"📥 Request data: {data}")
        
        if not data:
            print("❌ No data provided")
            return jsonify({"error": "No data provided"}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
        
        # Validation
        if not email or not password:
            print("❌ Missing email or password")
            return jsonify({"error": "Email and password are required"}), 400
        
        # Check user credentials
        if FIRESTORE_AVAILABLE:
            try:
                print("🔍 Looking up user in database...")
                users = query_documents("email", "==", email)
                print(f"🔍 Users found: {len(users) if users else 0}")
                
                if not users:
                    print("❌ No user found with this email")
                    return jsonify({"error": "Invalid email or password"}), 401
                
                # Filter to get only user documents (not profile documents)
                user_documents = []
                for doc in users:
                    print(f"📄 Checking document: {doc}")
                    # Check if this is a user document (has password field)
                    if 'password' in doc:
                        user_documents.append(doc)
                        print(f"✅ Found user document: {doc}")
                    else:
                        print(f"⚠️ Skipping profile document: {doc}")
                
                if not user_documents:
                    print("❌ No user document found (only profile documents)")
                    return jsonify({"error": "Invalid email or password"}), 401
                
                user = user_documents[0]
                print(f"👤 Using user document: {user}")
                
                # Simple password comparison (no hashing)
                stored_password = user.get('password')
                print(f"🔑 Stored password: {stored_password}")
                print(f"🔑 Provided password: {password}")
                
                if stored_password != password:
                    print("❌ Password mismatch")
                    return jsonify({"error": "Invalid email or password"}), 401
                
                if not user.get('isActive', True):
                    print("❌ Account is deactivated")
                    return jsonify({"error": "Account is deactivated"}), 401
                
                user_id = user.get('userId')
                print(f"🆔 User ID: {user_id}")
                
                # Get profile data from profiles collection
                try:
                    print("📋 Getting user profile...")
                    from Database_Setup.firestore_nosql_storage import db
                    profile_collection = db.collection("profiles")
                    profile_doc = profile_collection.document(f"profile_{user_id}").get()
                    
                    if profile_doc.exists:
                        profile = profile_doc.to_dict()
                        print(f"✅ Profile found: {profile}")
                    else:
                        print("⚠️ Profile not found, creating new one...")
                        # Create profile if it doesn't exist
                        profile = create_mock_profile(email, user.get('name'))
                        profile["userId"] = user_id
                        profile_collection.document(f"profile_{user_id}").set(profile)
                        print(f"✅ New profile created: {profile}")
                except Exception as e:
                    print(f"⚠️ Warning: Could not get profile: {e}")
                    profile = create_mock_profile(email, user.get('name'))
                
                # Update last login
                try:
                    print("🕒 Updating last login...")
                    from Database_Setup.firestore_nosql_storage import update_document
                    update_document(user_id, {"lastLogin": datetime.utcnow().isoformat()})
                    print("✅ Last login updated")
                except Exception as e:
                    print(f"⚠️ Warning: Could not update last login: {e}")
                
            except Exception as e:
                print(f"❌ Login error: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({"error": "Database error"}), 500
        else:
            print("⚠️ Firestore not available, using fallback")
            # Fallback for development (no Firestore)
            user_id = f"dev_user_{hash(email)}"
            profile = create_mock_profile(email)
            # Create a mock user object for the fallback
            user = {
                'userId': user_id,
                'email': email,
                'name': email.split('@')[0].title(),
                'isActive': True
            }
        
        # Create session
        print("🔐 Creating session...")
        session['user_id'] = user_id
        session['email'] = email
        session['name'] = user.get('name', email.split('@')[0].title())
        session['is_authenticated'] = True
        print(f"✅ Session created: {session}")
        
        response_data = {
            "success": True,
            "message": "Login successful",
            "user": {
                "userId": user_id,
                "email": email,
                "name": session['name']
            },
            "profile": profile
        }
        
        print(f"📤 Sending response: {response_data}")
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    try:
        # Clear session
        session.clear()
        
        return jsonify({
            "success": True,
            "message": "Logout successful"
        }), 200
        
    except Exception as e:
        print(f"❌ Logout error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """Get user profile endpoint"""
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = session.get('user_id')
        
        if FIRESTORE_AVAILABLE:
            try:
                from Database_Setup.firestore_nosql_storage import db
                profile_collection = db.collection("profiles")
                profile_doc = profile_collection.document(f"profile_{user_id}").get()
                
                if profile_doc.exists:
                    profile = profile_doc.to_dict()
                    return jsonify({
                        "success": True,
                        "profile": profile
                    }), 200
                else:
                    return jsonify({"error": "Profile not found"}), 404
                
            except Exception as e:
                print(f"❌ Profile fetch error: {e}")
                return jsonify({"error": "Database error"}), 500
        else:
            # Fallback for development
            profile = create_mock_profile(session.get('email'))
            return jsonify({
                "success": True,
                "profile": profile
            }), 200
        
    except Exception as e:
        print(f"❌ Profile error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/session', methods=['GET'])
def check_session():
    """Check if user is authenticated"""
    print("🔍 SESSION CHECK REQUEST")
    try:
        print(f"📋 Current session: {dict(session)}")
        
        if session.get('is_authenticated'):
            user_data = {
                "userId": session.get('user_id'),
                "email": session.get('email'),
                "name": session.get('name')
            }
            print(f"✅ User is authenticated: {user_data}")
            
            return jsonify({
                "success": True,
                "authenticated": True,
                "user": user_data
            }), 200
        else:
            print("❌ User is not authenticated")
            return jsonify({
                "success": True,
                "authenticated": False
            }), 200
        
    except Exception as e:
        print(f"❌ Session check error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "authentication",
        "firestore_available": FIRESTORE_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat()
    }), 200

@auth_bp.route('/test-db', methods=['GET'])
def test_database():
    """Test database connection endpoint"""
    print("🧪 Testing database connection...")
    
    if not FIRESTORE_AVAILABLE:
        return jsonify({
            "status": "error",
            "message": "Firestore not available",
            "firestore_available": False
        }), 500
    
    try:
        # Test creating a simple document
        test_data = {
            "test": True,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Database test"
        }
        
        print("💾 Creating test document...")
        doc_id = create_document(test_data, "test_doc")
        print(f"✅ Test document created with ID: {doc_id}")
        
        # Test retrieving the document
        print("📖 Retrieving test document...")
        retrieved_data = get_document("test_doc")
        print(f"✅ Test document retrieved: {retrieved_data}")
        
        return jsonify({
            "status": "success",
            "message": "Database test successful",
            "firestore_available": True,
            "test_doc_id": doc_id,
            "retrieved_data": retrieved_data
        }), 200
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Database test failed: {str(e)}",
            "firestore_available": FIRESTORE_AVAILABLE
        }), 500
