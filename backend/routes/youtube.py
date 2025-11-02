"""
YouTube Integration Routes
Handles video uploads and analytics fetching
ALL USERS SHARE THE SAME YOUTUBE CHANNEL
"""

import os
import pickle
import tempfile
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import requests
import sys

# Add parent directory to path for auth_helper
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth_helper import get_user_from_session

youtube_bp = Blueprint('youtube', __name__)

print("✅ YouTube blueprint created successfully")

# YouTube API Configuration
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]

# Get the correct path to client_secrets.json
import os as _os
_current_dir = _os.path.dirname(_os.path.abspath(__file__))
_backend_dir = _os.path.dirname(_current_dir)
CLIENT_SECRETS_FILE = _os.path.join(_backend_dir, "client_secrets.json")
print(f"📁 Client secrets file path: {CLIENT_SECRETS_FILE}")
print(f"   File exists: {_os.path.exists(CLIENT_SECRETS_FILE)}")

# Shared YouTube token path - ALL USERS USE user_user1's TOKEN
SHARED_TOKEN_FILE = _os.path.join(_backend_dir, "youtube_tokens", "user_user1_token.pickle")
print(f"📺 Shared YouTube token (user_user1): {SHARED_TOKEN_FILE}")
print(f"   Token exists: {_os.path.exists(SHARED_TOKEN_FILE)}")

def get_user_token_file(user_id):
    """Get token file path - returns user_user1's token for ALL users"""
    # Create tokens directory if it doesn't exist
    tokens_dir = _os.path.join(_backend_dir, "youtube_tokens")
    _os.makedirs(tokens_dir, exist_ok=True)
    
    # Return user_user1's token file for all users
    return SHARED_TOKEN_FILE

def get_youtube_service(user_id=None):
    """Get authenticated YouTube service - uses user_user1's token for ALL users"""
    token_file = SHARED_TOKEN_FILE
    credentials = None
    
    if os.path.exists(token_file):
        with open(token_file, "rb") as token:
            credentials = pickle.load(token)
    
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(GoogleRequest())
            with open(token_file, "wb") as token:
                pickle.dump(credentials, token)
        else:
            return None
    
    return build("youtube", "v3", credentials=credentials)

def get_analytics_service(user_id=None):
    """Get authenticated YouTube Analytics service - uses user_user1's token for ALL users"""
    token_file = SHARED_TOKEN_FILE
    credentials = None
    
    if os.path.exists(token_file):
        with open(token_file, "rb") as token:
            credentials = pickle.load(token)
    
    if not credentials or not credentials.valid:
        return None
    
    return build("youtubeAnalytics", "v2", credentials=credentials)

@youtube_bp.route('/auth/start', methods=['GET'])
def start_auth():
    """Start OAuth flow for YouTube - saves to user_user1's token (shared for all users)"""
    print("\n🔵 [YouTube] /auth/start called")
    
    try:
        user_id = get_user_from_session()
        print(f"   User ID from session: {user_id}")
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        print(f"   📁 Using client secrets: {CLIENT_SECRETS_FILE}")
        print(f"   📺 Will use user_user1's token: {SHARED_TOKEN_FILE}")
        
        # Disable HTTPS requirement for local development
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        
        # Determine redirect URI based on environment
        is_production = os.environ.get('ENV') == 'production'
        if is_production:
            redirect_uri = 'https://backend-557742533869.asia-south1.run.app/api/youtube/auth/callback'
        else:
            redirect_uri = 'http://localhost:5000/api/youtube/auth/callback'
        
        print(f"   🔗 Redirect URI: {redirect_uri}")
        
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        session['oauth_state'] = state
        print(f"   ✅ OAuth URL generated: {authorization_url[:50]}...")
        
        return jsonify({
            'success': True,
            'authorization_url': authorization_url
        })
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@youtube_bp.route('/auth/callback', methods=['GET'])
def auth_callback():
    """Handle OAuth callback - saves to user_user1's token (shared for all users)"""
    try:
        user_id = get_user_from_session()
    except Exception as e:
        return f"Error: Not authenticated - {str(e)}", 401
    
    try:
        state = session.get('oauth_state')
        
        # Disable HTTPS requirement for local development
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        
        # Determine redirect URI based on environment
        is_production = _os.environ.get('ENV') == 'production'
        if is_production:
            redirect_uri = 'https://backend-557742533869.asia-south1.run.app/api/youtube/auth/callback'
        else:
            redirect_uri = 'http://localhost:5000/api/youtube/auth/callback'
        
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            state=state,
            redirect_uri=redirect_uri
        )
        
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        
        # Save credentials to user_user1's token file (all users use same channel)
        os.makedirs(os.path.dirname(SHARED_TOKEN_FILE), exist_ok=True)
        with open(SHARED_TOKEN_FILE, "wb") as token:
            pickle.dump(credentials, token)
        
        print(f"✅ YouTube token saved to user_user1's token: {SHARED_TOKEN_FILE}")
        
        return """
        <html>
            <body>
                <h2>✅ YouTube Connected Successfully!</h2>
                <p>You can close this window and return to the app.</p>
                <script>window.close();</script>
            </body>
        </html>
        """
    except Exception as e:
        return f"Error: {str(e)}", 500

@youtube_bp.route('/auth/status', methods=['GET'])
def auth_status():
    """Check if YouTube is connected - all users use user_user1's channel"""
    print("\n🔵 [YouTube] /auth/status called")
    
    try:
        user_id = get_user_from_session()
        print(f"   User ID from session: {user_id}")
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    # Check if user_user1's token exists
    connected = os.path.exists(SHARED_TOKEN_FILE)
    print(f"   Using user_user1's token: {SHARED_TOKEN_FILE}")
    print(f"   Connected: {connected}")
    
    channel_info = None
    if connected:
        try:
            print("   🔍 Fetching channel info (user_user1's channel)...")
            youtube = get_youtube_service()
            if youtube:
                response = youtube.channels().list(part="snippet,statistics", mine=True).execute()
                if response.get("items"):
                    channel = response["items"][0]
                    channel_info = {
                        'id': channel['id'],
                        'title': channel['snippet']['title'],
                        'thumbnail': channel['snippet']['thumbnails']['default']['url'],
                        'subscribers': channel['statistics'].get('subscriberCount', 0),
                        'videos': channel['statistics'].get('videoCount', 0),
                        'views': channel['statistics'].get('viewCount', 0),
                        'shared': True  # Indicate this is a shared channel (user_user1's)
                    }
                    print(f"   ✅ Channel (user_user1): {channel_info['title']}")
        except Exception as e:
            print(f"   ⚠️  Error fetching channel: {str(e)}")
    
    return jsonify({
        'success': True,
        'connected': connected,
        'channel': channel_info
    })

@youtube_bp.route('/upload', methods=['POST'])
def upload_video():
    """Upload video to YouTube - all users upload using user_user1's channel"""
    print("\n🔵 [YouTube] /upload called")
    
    try:
        user_id = get_user_from_session()
        print(f"   User ID: {user_id}")
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        video_url = data.get('video_url')
        title = data.get('title', 'Untitled Video')
        description = data.get('description', '')
        tags = data.get('tags', [])
        privacy = data.get('privacy', 'unlisted')
        is_short = data.get('is_short', True)
        
        print(f"   📹 Video URL: {video_url}")
        print(f"   📝 Title: {title}")
        print(f"   🔒 Privacy: {privacy}")
        
        if not video_url:
            print("   ❌ No video URL provided")
            return jsonify({'success': False, 'error': 'Video URL required'}), 400
        
        youtube = get_youtube_service(user_id)
        if not youtube:
            print("   ❌ YouTube not connected for this user")
            return jsonify({'success': False, 'error': 'YouTube not connected'}), 401
        
        # Download video to temp file
        print(f"   ⬇️  Downloading video from: {video_url}")
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        with open(temp_file.name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Add #Shorts for YouTube Shorts
        if is_short:
            if "#shorts" not in title.lower():
                title = f"{title} #Shorts"
            if "#shorts" not in description.lower():
                description = f"{description}\n\n#Shorts"
            if "shorts" not in [t.lower() for t in tags]:
                tags.append("shorts")
        
        # Upload to YouTube
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "22"  # People & Blogs
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False
            }
        }
        
        media = MediaFileUpload(
            temp_file.name,
            chunksize=-1,
            resumable=True,
            mimetype='video/*'
        )
        
        request_obj = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )
        
        print("   ⬆️  Uploading to YouTube...")
        response_obj = None
        while response_obj is None:
            status, response_obj = request_obj.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"   📊 Upload progress: {progress}%")
        
        video_id = response_obj.get('id')
        print(f"   ✅ Upload complete! Video ID: {video_id}")
        
        # Clean up temp file
        try:
            os.unlink(temp_file.name)
            print("   🗑️  Temp file cleaned up")
        except Exception as cleanup_error:
            print(f"   ⚠️  Cleanup warning: {cleanup_error}")
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'url': f"https://youtube.com/shorts/{video_id}" if is_short else f"https://www.youtube.com/watch?v={video_id}",
            'studio_url': f"https://studio.youtube.com/video/{video_id}/edit"
        })
        
    except Exception as e:
        print(f"   ❌ Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@youtube_bp.route('/videos', methods=['GET'])
def get_videos():
    """Get videos from YouTube - all users see user_user1's channel videos"""
    print("\n🔵 [YouTube] /videos called")
    
    try:
        user_id = get_user_from_session()
        print(f"   User ID: {user_id}")
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        youtube = get_youtube_service()
        if not youtube:
            print("   ❌ YouTube not connected")
            return jsonify({'success': False, 'error': 'YouTube not connected'}), 401
        
        # Get uploads playlist
        print("   🔍 Fetching uploads playlist...")
        channel_response = youtube.channels().list(part="contentDetails", mine=True).execute()
        if not channel_response.get("items"):
            print("   ℹ️  No channel found")
            return jsonify({'success': True, 'videos': []})
        
        uploads_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        
        # Get videos
        playlist_response = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_id,
            maxResults=20
        ).execute()
        
        videos = []
        for item in playlist_response.get("items", []):
            video_id = item["contentDetails"]["videoId"]
            
            # Get video statistics
            video_response = youtube.videos().list(
                part="statistics,contentDetails",
                id=video_id
            ).execute()
            
            if video_response.get("items"):
                stats = video_response["items"][0]["statistics"]
                duration = video_response["items"][0]["contentDetails"]["duration"]
                
                videos.append({
                    'id': video_id,
                    'title': item["snippet"]["title"],
                    'thumbnail': item["snippet"]["thumbnails"]["medium"]["url"],
                    'published_at': item["snippet"]["publishedAt"],
                    'views': int(stats.get("viewCount", 0)),
                    'likes': int(stats.get("likeCount", 0)),
                    'comments': int(stats.get("commentCount", 0)),
                    'duration': duration,
                    'url': f"https://www.youtube.com/watch?v={video_id}"
                })
        
        print(f"   ✅ Fetched {len(videos)} videos")
        return jsonify({
            'success': True,
            'videos': videos
        })
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@youtube_bp.route('/analytics/channel', methods=['GET'])
def get_channel_analytics():
    """Get analytics from YouTube - all users see user_user1's channel analytics"""
    print("\n🔵 [YouTube] /analytics/channel called")
    
    try:
        user_id = get_user_from_session()
        print(f"   User ID: {user_id}")
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        days = int(request.args.get('days', 30))
        print(f"   📊 Fetching analytics for last {days} days")
        
        youtube = get_youtube_service()
        analytics = get_analytics_service()
        
        if not youtube or not analytics:
            return jsonify({'success': False, 'error': 'YouTube not connected'}), 401
        
        # Get channel ID
        channel_response = youtube.channels().list(part="id", mine=True).execute()
        if not channel_response.get("items"):
            return jsonify({'success': False, 'error': 'No channel found'}), 404
        
        channel_id = channel_response["items"][0]["id"]
        
        # Get analytics
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        analytics_response = analytics.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start_date,
            endDate=end_date,
            metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost,likes,comments",
            dimensions="day",
            sort="day"
        ).execute()
        
        # Process data
        daily_data = []
        total_views = 0
        total_watch_time = 0
        total_subs_gained = 0
        total_subs_lost = 0
        total_likes = 0
        total_comments = 0
        
        if "rows" in analytics_response:
            for row in analytics_response["rows"]:
                daily_data.append({
                    'date': row[0],
                    'views': row[1],
                    'watch_time': row[2],
                    'avg_duration': row[3],
                    'subs_gained': row[4],
                    'subs_lost': row[5],
                    'likes': row[6],
                    'comments': row[7]
                })
                
                total_views += row[1]
                total_watch_time += row[2]
                total_subs_gained += row[4]
                total_subs_lost += row[5]
                total_likes += row[6]
                total_comments += row[7]
        
        print(f"   ✅ Analytics: {total_views} views, {total_watch_time} min watch time")
        return jsonify({
            'success': True,
            'period': f"{start_date} to {end_date}",
            'summary': {
                'views': total_views,
                'watch_time_minutes': total_watch_time,
                'watch_time_hours': round(total_watch_time / 60, 1),
                'subscribers_gained': total_subs_gained,
                'subscribers_lost': total_subs_lost,
                'net_subscribers': total_subs_gained - total_subs_lost,
                'likes': total_likes,
                'comments': total_comments
            },
            'daily': daily_data
        })
        
    except HttpError as e:
        print(f"   ❌ HTTP Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
