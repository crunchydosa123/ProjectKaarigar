from flask import Blueprint, request, jsonify, session
import requests
import base64
import tempfile
import os
import time
from google.cloud import storage
from google.cloud import firestore

# Initialize Flask Blueprint
video_edit_bp = Blueprint('video_edit', __name__)

# Google Cloud Configuration
BUCKET_NAME = "all_in_one_bucket"
PROJECT_ID = "useful-figure-475210-g7"

# Initialize Google Cloud clients
try:
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    db = firestore.Client()
    print("✅ Google Cloud Storage and Firestore initialized successfully for video editing")
except Exception as e:
    print(f"❌ Failed to initialize Google Cloud services for video editing: {e}")
    storage_client = None
    bucket = None
    db = None

# Your FFmpeg service URL
FFMPEG_SERVICE_URL = "https://video-editor-298842469563.asia-south1.run.app"

def get_user_from_session():
    """Get user ID from session"""
    if not session.get('is_authenticated'):
        raise ValueError("User not authenticated")
    
    user_id = session.get('user_id')
    if not user_id:
        raise ValueError("User ID not found in session")
    
    return user_id

@video_edit_bp.route('/get-user-videos', methods=['GET'])
def get_user_videos():
    """Get all videos/reels for the authenticated user from Firestore"""
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        print(f"📋 Retrieving videos for user: {user_id}")
        
        videos_list = []
        
        # Get uploaded media videos
        try:
            # Videos are stored in: media/user11/uploadmedia/media_data/videos/
            videos_ref = db.collection("media").document(user_id).collection("uploadmedia").document("media_data").collection("videos")
            videos_docs = videos_ref.get()
            
            for doc in videos_docs:
                video_data = doc.to_dict()
                # Check if it's active and has a public URL
                if video_data.get('is_active', True) and video_data.get('public_url'):
                    videos_list.append({
                        "id": doc.id,
                        "title": video_data.get('title', 'Uploaded Video'),
                        "public_url": video_data.get('public_url', ''),
                        "file_size": video_data.get('file_size', 0),
                        "created_at": video_data.get('uploaded_at', ''),
                        "type": "uploaded",
                        "filename": video_data.get('filename', ''),
                        "mime_type": video_data.get('mime_type', 'video/mp4')
                    })
            print(f"✅ Found {len([v for v in videos_list if v['type'] == 'uploaded'])} uploaded videos")
        except Exception as e:
            print(f"⚠️ Error fetching uploaded videos: {e}")
        
        # Get generated reels
        try:
            reels_ref = db.collection("media").document(user_id).collection("uploadmedia").document("media_data").collection("_generated_reels")
            reels_docs = reels_ref.get()
            
            for doc in reels_docs:
                reel_data = doc.to_dict()
                videos_list.append({
                    "id": doc.id,
                    "title": reel_data.get('title', 'Generated Reel'),
                    "public_url": reel_data.get('public_url', ''),
                    "file_size": reel_data.get('file_size', 0),
                    "created_at": reel_data.get('generated_at', ''),
                    "type": "generated_reel",
                    "duration": reel_data.get('duration', 0),
                    "segments": reel_data.get('segments', 1),
                    "generation_type": reel_data.get('generation_type', 'unknown')
                })
        except Exception as e:
            print(f"⚠️ Error fetching generated reels: {e}")
        
        # Sort by creation date (newest first)
        videos_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        print(f"✅ Retrieved {len(videos_list)} videos")
        
        # Debug: Print each video
        for i, video in enumerate(videos_list):
            print(f"   Video {i+1}: {video['title']} - {video['type']} - {video['public_url'][:50]}...")
        
        return jsonify({
            "success": True,
            "videos": videos_list,
            "count": len(videos_list)
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Error retrieving videos: {e}")
        return jsonify({"error": "Internal server error"}), 500

@video_edit_bp.route('/edit-video', methods=['POST'])
def edit_video():
    """Edit video using AI prompts - matches test_req.py structure"""
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        data = request.get_json()
        video_url = data.get('video_url')
        edit_prompt = data.get('edit_prompt')
        topic = data.get('topic', 'kaarigar_project')
        save_name = data.get('save_name')
        
        if not video_url or not edit_prompt:
            return jsonify({"error": "Video URL and edit prompt required"}), 400
        
        print(f"🎬 Starting video edit for prompt: {edit_prompt}")
        
        # Download video from URL
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        
        # Convert to base64 (exactly like your test)
        video_data = base64.b64encode(response.content).decode('utf-8')
        print(f"📊 Video size: {len(video_data)} characters (base64)")
        
        # Generate save name if not provided
        if not save_name:
            save_name = f"edited_video_{int(time.time())}"
        
        # Call FFmpeg service (exactly like your test_req.py)
        ffmpeg_response = requests.post(f"{FFMPEG_SERVICE_URL}/edit", json={
            'file': video_data,
            'edit_prompt': edit_prompt,
            'topic': topic,
            'save_name': save_name
        })
        
        print(f"🔧 FFmpeg service response status: {ffmpeg_response.status_code}")
        
        if ffmpeg_response.status_code == 200:
            result = ffmpeg_response.json()
            print(f"✅ Video edited successfully: {result.get('saved_url')}")
            
            return jsonify({
                "success": True,
                "edited_video_url": result.get('saved_url'),
                "video_info": result.get('video_info'),
                "message": "Video edited successfully",
                "save_name": save_name
            })
        else:
            print(f"❌ FFmpeg service error: {ffmpeg_response.text}")
            return jsonify({"error": "Video editing failed"}), 500
            
    except Exception as e:
        print(f"❌ Video edit error: {e}")
        return jsonify({"error": str(e)}), 500

@video_edit_bp.route('/add-trending-audio', methods=['POST'])
def add_trending_audio():
    """Add trending audio to video - matches test_req_trending_audio.py structure"""
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        data = request.get_json()
        video_url = data.get('video_url')
        song_id = data.get('song_id')
        topic = data.get('topic', 'kaarigar_project')
        save_name = data.get('save_name')
        
        if not video_url or song_id is None:
            return jsonify({"error": "Video URL and song ID required"}), 400
        
        print(f"🎵 Adding trending audio - Song ID: {song_id}")
        
        # Download video from URL
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        
        # Convert to base64 (exactly like your test)
        video_data = base64.b64encode(response.content).decode('utf-8')
        print(f"📊 Video size: {len(video_data)} characters (base64)")
        
        # Generate save name if not provided
        if not save_name:
            save_name = f"trending_audio_added_{int(time.time())}"
        
        # Call FFmpeg service (exactly like your test_req_trending_audio.py)
        ffmpeg_response = requests.post(f"{FFMPEG_SERVICE_URL}/add-trending-audio", json={
            'file': video_data,
            'song_id': song_id,
            'topic': topic,
            'save_name': save_name
        })
        
        print(f"🔧 FFmpeg service response status: {ffmpeg_response.status_code}")
        
        if ffmpeg_response.status_code == 200:
            result = ffmpeg_response.json()
            print(f"✅ Audio added successfully: {result.get('saved_url')}")
            
            return jsonify({
                "success": True,
                "edited_video_url": result.get('saved_url'),
                "video_info": result.get('video_info'),
                "message": "Audio added successfully",
                "save_name": save_name
            })
        else:
            print(f"❌ FFmpeg service error: {ffmpeg_response.text}")
            return jsonify({"error": "Audio addition failed"}), 500
            
    except Exception as e:
        print(f"❌ Audio addition error: {e}")
        return jsonify({"error": str(e)}), 500

@video_edit_bp.route('/get-trending-songs', methods=['GET'])
def get_trending_songs():
    """Get list of trending songs"""
    try:
        response = requests.get(f"{FFMPEG_SERVICE_URL}/trending-songs")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Retrieved {len(result.get('songs', []))} trending songs")
            return jsonify(result)
        else:
            print(f"❌ Failed to get trending songs: {response.status_code}")
            return jsonify({"error": "Failed to get trending songs"}), 500
    except Exception as e:
        print(f"❌ Trending songs error: {e}")
        return jsonify({"error": str(e)}), 500

@video_edit_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for video editing service"""
    return jsonify({
        "status": "ok",
        "service": "video_editing",
        "message": "Video editing service is running"
    })
