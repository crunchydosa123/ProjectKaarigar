from flask import Blueprint, request, jsonify, session
import os
import uuid
from datetime import datetime
from google.cloud import storage
from google.cloud import firestore
import mimetypes

# Initialize Flask Blueprint
media_bp = Blueprint('media', __name__)

# Google Cloud Configuration
BUCKET_NAME = "all_in_one_bucket"
FIRESTORE_AVAILABLE = True

# Initialize Google Cloud clients
try:
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    db = firestore.Client()
    print("✅ Google Cloud Storage and Firestore initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize Google Cloud services: {e}")
    FIRESTORE_AVAILABLE = False
    storage_client = None
    bucket = None
    db = None

def get_user_from_session():
    """Get user ID from session"""
    if not session.get('is_authenticated'):
        raise ValueError("User not authenticated")
    
    user_id = session.get('user_id')
    if not user_id:
        raise ValueError("User ID not found in session")
    
    return user_id

def upload_file_to_storage(file, user_id, media_type, filename):
    """Upload file to Google Cloud Storage"""
    try:
        # Generate unique filename
        file_extension = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create path: kaarigar/KR_USER11/media/images/ or kaarigar/KR_USER11/media/videos/
        kaarigar_id = f"KR_{user_id.upper()}"
        folder = "images" if media_type == "image" else "videos"
        blob_path = f"kaarigar/{kaarigar_id}/media/{folder}/{unique_filename}"
        
        # Upload file
        blob = bucket.blob(blob_path)
        blob.upload_from_file(file, content_type=file.content_type)
        
        # Make blob publicly accessible
        blob.make_public()
        
        # Get public URL
        public_url = blob.public_url
        
        print(f"✅ File uploaded successfully: {blob_path}")
        print(f"🔗 Public URL: {public_url}")
        
        return {
            "success": True,
            "blob_path": blob_path,
            "public_url": public_url,
            "filename": unique_filename,
            "original_filename": filename
        }
        
    except Exception as e:
        print(f"❌ Failed to upload file to storage: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def save_media_metadata(user_id, media_data):
    """Save media metadata to Firestore with hierarchical structure in media collection"""
    try:
        print(f"🔧 Starting save_media_metadata for user: {user_id}")
        print(f"🔧 Media data keys: {list(media_data.keys())}")
        
        kaarigar_id = f"KR_{user_id.upper()}"
        
        # Create media document
        media_doc = {
            "user_id": user_id,
            "kaarigar_id": kaarigar_id,
            "media_type": media_data["media_type"],
            "filename": media_data["filename"],
            "original_filename": media_data["original_filename"],
            "blob_path": media_data["blob_path"],
            "public_url": media_data["public_url"],
            "file_size": media_data.get("file_size", 0),
            "content_type": media_data.get("content_type", ""),
            "title": media_data.get("title", ""),
            "description": media_data.get("description", ""),
            "uploaded_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        print(f"🔧 Created media document with {len(media_doc)} fields")
        
        # Save to hierarchical structure in media collection:
        # media/user11/uploadmedia/images/ or media/user11/uploadmedia/videos/
        media_type_collection = "images" if media_data["media_type"] == "image" else "videos"
        print(f"🔧 Media type collection: {media_type_collection}")
        
        # Create the hierarchical path step by step
        print(f"🔧 Creating Firestore path step by step...")
        
        # Step 1: Get media collection
        media_collection = db.collection("media")
        print(f"🔧 Step 1 - media collection: {type(media_collection)}")
        
        # Step 2: Get user document reference
        user_doc_ref = media_collection.document(user_id)
        print(f"🔧 Step 2 - user doc ref: {type(user_doc_ref)}")
        
        # Step 3: Get uploadmedia subcollection
        uploadmedia_collection = user_doc_ref.collection("uploadmedia")
        print(f"🔧 Step 3 - uploadmedia collection: {type(uploadmedia_collection)}")
        
        # Step 4: Get specific media type collection (images or videos)
        # We need to create a document reference first, then get its subcollection
        uploadmedia_doc_ref = uploadmedia_collection.document("media_data")
        print(f"🔧 Step 4a - uploadmedia doc ref: {type(uploadmedia_doc_ref)}")
        
        media_type_collection_ref = uploadmedia_doc_ref.collection(media_type_collection)
        print(f"🔧 Step 4b - {media_type_collection} collection: {type(media_type_collection_ref)}")
        
        # Step 5: Create document reference
        media_ref = media_type_collection_ref.document()
        print(f"🔧 Step 5 - document ref: {type(media_ref)}")
        print(f"🔧 Document ID: {media_ref.id}")
        
        # Step 6: Save the document
        print(f"🔧 Saving document to Firestore...")
        media_ref.set(media_doc)
        print(f"🔧 Document saved successfully!")
        
        print(f"✅ Media metadata saved to Firestore:")
        print(f"   - Path: media/{user_id}/uploadmedia/{media_type_collection}/{media_ref.id}")
        
        return {
            "success": True,
            "media_id": media_ref.id,
            "message": "Media uploaded and saved successfully"
        }
        
    except Exception as e:
        print(f"❌ Failed to save media metadata: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e)
        }

@media_bp.route('/upload', methods=['POST'])
def upload_media():
    """Upload media file to Cloud Storage and save metadata to Firestore"""
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Get media type from form data
        media_type = request.form.get('media_type', 'image')
        if media_type not in ['image', 'video']:
            return jsonify({"error": "Invalid media type. Must be 'image' or 'video'"}), 400
        
        # Get additional metadata
        title = request.form.get('title', file.filename)
        description = request.form.get('description', '')
        
        print(f"📤 Uploading media for user: {user_id}")
        print(f"📁 File: {file.filename}")
        print(f"🎬 Media type: {media_type}")
        print(f"📝 Title: {title}")
        
        # Upload file to Cloud Storage
        upload_result = upload_file_to_storage(file, user_id, media_type, file.filename)
        
        if not upload_result["success"]:
            return jsonify({"error": f"Upload failed: {upload_result['error']}"}), 500
        
        # Prepare metadata for Firestore
        media_data = {
            "media_type": media_type,
            "filename": upload_result["filename"],
            "original_filename": upload_result["original_filename"],
            "blob_path": upload_result["blob_path"],
            "public_url": upload_result["public_url"],
            "file_size": request.content_length or 0,
            "content_type": file.content_type or mimetypes.guess_type(file.filename)[0],
            "title": title,
            "description": description
        }
        
        # Save metadata to Firestore
        save_result = save_media_metadata(user_id, media_data)
        
        if not save_result["success"]:
            return jsonify({"error": f"Failed to save metadata: {save_result['error']}"}), 500
        
        return jsonify({
            "success": True,
            "message": "Media uploaded successfully",
            "media_id": save_result["media_id"],
            "public_url": upload_result["public_url"],
            "blob_path": upload_result["blob_path"]
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@media_bp.route('/list', methods=['GET'])
def list_media():
    """List user's uploaded media from hierarchical structure in media collection"""
    try:
        print(f"🔧 Starting list_media function")
        
        if not session.get('is_authenticated'):
            print(f"❌ User not authenticated")
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        print(f"🔧 User ID: {user_id}")
        
        # Get media from hierarchical structure in media collection
        all_media = []
        
        print(f"🔧 Fetching images from media/{user_id}/uploadmedia/images/")
        try:
            # Get images from media/user11/uploadmedia/media_data/images/
            images_ref = db.collection("media").document(user_id).collection("uploadmedia").document("media_data").collection("images")
            print(f"🔧 Images ref type: {type(images_ref)}")
            
            # First try with filter and sort (requires index)
            try:
                images_docs = images_ref.where("is_active", "==", True).order_by("uploaded_at", direction=firestore.Query.DESCENDING).get()
                print(f"🔧 Found {len(images_docs)} image documents (with index)")
            except Exception as index_error:
                print(f"⚠️ Index error for images, falling back to simple query: {index_error}")
                # Fallback: get all documents and filter/sort in memory
                images_docs = images_ref.get()
                print(f"🔧 Found {len(images_docs)} total image documents (fallback)")
            
            for doc in images_docs:
                media_data = doc.to_dict()
                # Filter active documents in memory if needed
                if media_data.get("is_active", True):  # Default to True if not set
                    media_data["id"] = doc.id
                    media_data["collection_path"] = f"media/{user_id}/uploadmedia/media_data/images/{doc.id}"
                    all_media.append(media_data)
                    print(f"🔧 Added image: {media_data.get('title', 'No title')} - {media_data.get('filename', 'No filename')}")
        except Exception as e:
            print(f"❌ Error fetching images: {e}")
            print(f"❌ Images error type: {type(e)}")
            import traceback
            print(f"❌ Images traceback: {traceback.format_exc()}")
        
        print(f"🔧 Fetching videos from media/{user_id}/uploadmedia/videos/")
        try:
            # Get videos from media/user11/uploadmedia/media_data/videos/
            videos_ref = db.collection("media").document(user_id).collection("uploadmedia").document("media_data").collection("videos")
            print(f"🔧 Videos ref type: {type(videos_ref)}")
            
            # First try with filter and sort (requires index)
            try:
                videos_docs = videos_ref.where("is_active", "==", True).order_by("uploaded_at", direction=firestore.Query.DESCENDING).get()
                print(f"🔧 Found {len(videos_docs)} video documents (with index)")
            except Exception as index_error:
                print(f"⚠️ Index error for videos, falling back to simple query: {index_error}")
                # Fallback: get all documents and filter/sort in memory
                videos_docs = videos_ref.get()
                print(f"🔧 Found {len(videos_docs)} total video documents (fallback)")
            
            for doc in videos_docs:
                media_data = doc.to_dict()
                # Filter active documents in memory if needed
                if media_data.get("is_active", True):  # Default to True if not set
                    media_data["id"] = doc.id
                    media_data["collection_path"] = f"media/{user_id}/uploadmedia/media_data/videos/{doc.id}"
                    all_media.append(media_data)
                    print(f"🔧 Added video: {media_data.get('title', 'No title')} - {media_data.get('filename', 'No filename')}")
        except Exception as e:
            print(f"❌ Error fetching videos: {e}")
            print(f"❌ Videos error type: {type(e)}")
            import traceback
            print(f"❌ Videos traceback: {traceback.format_exc()}")
        
        # Sort all media by upload date
        all_media.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
        
        # Separate by type for organized response
        images = [m for m in all_media if m["media_type"] == "image"]
        videos = [m for m in all_media if m["media_type"] == "video"]
        
        print(f"📁 Retrieved media for user {user_id} from media collection:")
        print(f"   - Images: {len(images)}")
        print(f"   - Videos: {len(videos)}")
        print(f"   - Total: {len(all_media)}")
        
        return jsonify({
            "success": True,
            "media": all_media,
            "images": images,
            "videos": videos,
            "count": len(all_media),
            "images_count": len(images),
            "videos_count": len(videos)
        })
        
    except ValueError as e:
        print(f"❌ ValueError in list_media: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ List media error: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

@media_bp.route('/list/<media_type>', methods=['GET'])
def list_media_by_type(media_type):
    """List user's media by type (images or videos) from media collection"""
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        if media_type not in ['images', 'videos']:
            return jsonify({"error": "Invalid media type. Must be 'images' or 'videos'"}), 400
        
        user_id = get_user_from_session()
        
        # Get media from specific type collection in media collection
        media_ref = db.collection("media").document(user_id).collection("uploadmedia").document("media_data").collection(media_type)
        
        # First try with filter and sort (requires index)
        try:
            media_docs = media_ref.where("is_active", "==", True).order_by("uploaded_at", direction=firestore.Query.DESCENDING).get()
            print(f"🔧 Found {len(media_docs)} {media_type} documents (with index)")
        except Exception as index_error:
            print(f"⚠️ Index error for {media_type}, falling back to simple query: {index_error}")
            # Fallback: get all documents and filter/sort in memory
            media_docs = media_ref.get()
            print(f"🔧 Found {len(media_docs)} total {media_type} documents (fallback)")
        
        media_list = []
        for doc in media_docs:
            media_data = doc.to_dict()
            # Filter active documents in memory if needed
            if media_data.get("is_active", True):  # Default to True if not set
                media_data["id"] = doc.id
                media_data["collection_path"] = f"media/{user_id}/uploadmedia/media_data/{media_type}/{doc.id}"
                media_list.append(media_data)
        
        # Sort by upload date if we used fallback
        if len(media_list) > 1:
            media_list.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
        
        print(f"📁 Retrieved {media_type} for user {user_id} from media collection: {len(media_list)} items")
        
        return jsonify({
            "success": True,
            "media_type": media_type,
            "media": media_list,
            "count": len(media_list)
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ List {media_type} error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@media_bp.route('/delete/<media_id>', methods=['DELETE'])
def delete_media(media_id):
    """Delete media by ID"""
    try:
        print(f"🔧 Starting delete_media for media_id: {media_id}")
        
        if not session.get('is_authenticated'):
            print(f"❌ User not authenticated")
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        print(f"🔧 User ID: {user_id}")
        
        # Try to find and delete the media document
        # We need to search through both images and videos collections
        deleted = False
        deleted_path = None
        
        # Try images collection first
        try:
            images_ref = db.collection("media").document(user_id).collection("uploadmedia").document("media_data").collection("images")
            doc_ref = images_ref.document(media_id)
            doc = doc_ref.get()
            
            if doc.exists:
                doc_data = doc.to_dict()
                print(f"🔧 Found media in images collection: {doc_data.get('title', 'No title')}")
                
                # Delete from Firestore
                doc_ref.delete()
                print(f"🔧 Deleted from Firestore: images/{media_id}")
                
                # Try to delete from Cloud Storage
                try:
                    blob_path = doc_data.get('blob_path')
                    if blob_path:
                        blob = bucket.blob(blob_path)
                        blob.delete()
                        print(f"🔧 Deleted from Cloud Storage: {blob_path}")
                    else:
                        print(f"⚠️ No blob_path found in document")
                except Exception as storage_error:
                    print(f"⚠️ Failed to delete from Cloud Storage: {storage_error}")
                
                deleted = True
                deleted_path = f"media/{user_id}/uploadmedia/media_data/images/{media_id}"
                
        except Exception as e:
            print(f"🔧 Not found in images collection: {e}")
        
        # Try videos collection if not found in images
        if not deleted:
            try:
                videos_ref = db.collection("media").document(user_id).collection("uploadmedia").document("media_data").collection("videos")
                doc_ref = videos_ref.document(media_id)
                doc = doc_ref.get()
                
                if doc.exists:
                    doc_data = doc.to_dict()
                    print(f"🔧 Found media in videos collection: {doc_data.get('title', 'No title')}")
                    
                    # Delete from Firestore
                    doc_ref.delete()
                    print(f"🔧 Deleted from Firestore: videos/{media_id}")
                    
                    # Try to delete from Cloud Storage
                    try:
                        blob_path = doc_data.get('blob_path')
                        if blob_path:
                            blob = bucket.blob(blob_path)
                            blob.delete()
                            print(f"🔧 Deleted from Cloud Storage: {blob_path}")
                        else:
                            print(f"⚠️ No blob_path found in document")
                    except Exception as storage_error:
                        print(f"⚠️ Failed to delete from Cloud Storage: {storage_error}")
                    
                    deleted = True
                    deleted_path = f"media/{user_id}/uploadmedia/media_data/videos/{media_id}"
                    
            except Exception as e:
                print(f"🔧 Not found in videos collection: {e}")
        
        if deleted:
            print(f"✅ Media deleted successfully from: {deleted_path}")
            return jsonify({
                "success": True,
                "message": "Media deleted successfully",
                "deleted_path": deleted_path
            })
        else:
            print(f"❌ Media not found: {media_id}")
            return jsonify({
                "success": False,
                "error": "Media not found"
            }), 404
        
    except ValueError as e:
        print(f"❌ ValueError in delete_media: {e}")
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Delete media error: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

@media_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for media upload service"""
    return jsonify({
        "status": "ok",
        "service": "media_upload",
        "firestore_available": FIRESTORE_AVAILABLE,
        "storage_available": storage_client is not None,
        "bucket_name": BUCKET_NAME
    })
