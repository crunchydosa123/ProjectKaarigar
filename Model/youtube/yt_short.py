import os
import pickle
import requests
import tempfile
import time
from urllib.parse import urlparse
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
CLIENT_SECRETS_FILE = "client_secrets.json"

def is_url(path):
    """Check if the given path is a URL."""
    try:
        result = urlparse(path)
        return all([result.scheme, result.netloc])
    except:
        return False

def download_video_from_url(url, progress_callback=None):
    """Download video from URL to temporary file."""
    print(f"🌐 Downloading video from URL...")
    print(f"🔗 {url}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Get file size if available
        total_size = int(response.headers.get('content-length', 0))
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_path = temp_file.name
        
        # Download with progress
        downloaded = 0
        chunk_size = 8192
        
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        print(f"⬇️  Downloading: {progress}% ({downloaded / (1024*1024):.2f} MB)", end='\r')
        
        print()  # New line after progress
        file_size = os.path.getsize(temp_path) / (1024 * 1024)
        print(f"✅ Downloaded successfully! ({file_size:.2f} MB)")
        print(f"📁 Temp file: {temp_path}")
        
        return temp_path
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading video: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def get_authenticated_service():
    """Authenticates the user and returns a YouTube service object."""
    credentials = None
    
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("🔄 Refreshing expired credentials...")
            credentials.refresh(Request())
        else:
            print("🔐 Starting authentication flow...")
            print("📱 A browser window will open. Please log in with your YouTube account.")
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0)
        
        with open("token.pickle", "wb") as token:
            pickle.dump(credentials, token)
        print("✅ Authentication successful!")

    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def upload_video(youtube, file_path, title, description, tags, category_id, privacy_status, is_short=False):
    """Uploads a video to YouTube."""
    
    temp_file = None
    original_path = file_path
    
    # Check if it's a URL and download if needed
    if is_url(file_path):
        temp_file = download_video_from_url(file_path)
        if not temp_file:
            return None
        file_path = temp_file
        print(f"📂 Using downloaded file for upload")
    
    if not os.path.exists(file_path):
        print(f"❌ Error: Video file not found at '{file_path}'")
        return None
    
    file_size = os.path.getsize(file_path) / (1024 * 1024)
    print(f"📁 File: {file_path} ({file_size:.2f} MB)")
    
    # Add #Shorts to title/description for YouTube Shorts
    if is_short:
        if "#shorts" not in title.lower():
            title = f"{title} #Shorts"
        if "#shorts" not in description.lower():
            description = f"{description}\n\n#Shorts"
        print("📱 Uploading as YouTube Short")
    
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(file_path,
                            chunksize=-1,
                            resumable=True,
                            mimetype='video/*')

    print(f"\n🚀 Uploading video to YouTube...")
    print(f"📝 Title: {title}")
    print(f"🔒 Privacy: {privacy_status}")
    
    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"⏳ Uploading: {progress}%", end="\r")
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            # Clean up temp file if it exists
            if temp_file and os.path.exists(temp_file):
                try:
                    time.sleep(0.5)
                    os.unlink(temp_file)
                    print(f"🗑️  Cleaned up temporary file")
                except:
                    print(f"⚠️  Temp file will be cleaned up later: {temp_file}")
            return None

    print(f"\n✅ Upload complete!")
    print(f"🎬 Video ID: {response.get('id')}")
    
    if is_short:
        print(f"📱 Short URL: https://youtube.com/shorts/{response.get('id')}")
    else:
        print(f"🔗 URL: https://www.youtube.com/watch?v={response.get('id')}")
    
    # Clean up temp file if it exists
    if temp_file and os.path.exists(temp_file):
        try:
            # Wait a moment for file handle to be released on Windows
            time.sleep(0.5)
            os.unlink(temp_file)
            print(f"🗑️  Cleaned up temporary file")
        except PermissionError:
            # If still locked, try again after a longer delay
            try:
                time.sleep(2)
                os.unlink(temp_file)
                print(f"🗑️  Cleaned up temporary file")
            except Exception as e:
                print(f"⚠️  Could not delete temp file (will be cleaned up later): {temp_file}")
        except Exception as e:
            print(f"⚠️  Error cleaning up temp file: {e}")
    
    return response.get('id')

def interactive_upload():
    """Interactive mode to upload videos."""
    print("=" * 70)
    print("🎬 YouTube Video Uploader")
    print("=" * 70)
    print()
    
    # Choose upload type
    print("📱 Upload Type:")
    print("  1. YouTube Short (vertical, <60s)")
    print("  2. Regular Video")
    upload_type = input("\nChoose type (1/2) [default: 1]: ").strip() or "1"
    is_short = (upload_type == "1")
    
    # Get video file or URL
    print("\n📁 Enter video file path or URL:")
    print("   • Local file: C:\\path\\to\\video.mp4")
    print("   • URL: https://storage.googleapis.com/.../video.mp4")
    video_file = input("\nPath or URL (or press Enter for 'my_video.mp4'): ").strip()
    if not video_file:
        video_file = "my_video.mp4"
    
    # Check if it's a URL or local file
    if not is_url(video_file) and not os.path.exists(video_file):
        print(f"❌ Error: Video file not found at '{video_file}'")
        return
    
    # Validate Short requirements
    if is_short:
        print("\n⚠️  YouTube Shorts Requirements:")
        print("   • Vertical video (9:16 aspect ratio)")
        print("   • Duration: Under 60 seconds")
        print("   • Resolution: 1080x1920 or 720x1280")
    
    # Get video details
    title = input("\n📝 Enter video title: ").strip() or "My Test Video"
    description = input("📄 Enter video description: ").strip() or "Uploaded via Python script"
    tags_input = input("🏷️  Enter tags (comma-separated): ").strip()
    
    if is_short:
        # Add shorts-specific tags
        default_tags = ["shorts", "short"]
        tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else default_tags
        if "shorts" not in [t.lower() for t in tags]:
            tags.append("shorts")
    else:
        tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else ["python", "api"]
    
    print("\n📂 Available Categories:")
    print("  1  - Film & Animation")
    print("  2  - Autos & Vehicles")
    print("  10 - Music")
    print("  15 - Pets & Animals")
    print("  17 - Sports")
    print("  19 - Travel & Events")
    print("  20 - Gaming")
    print("  22 - People & Blogs (default)")
    print("  23 - Comedy")
    print("  24 - Entertainment")
    print("  25 - News & Politics")
    print("  26 - Howto & Style")
    print("  27 - Education")
    print("  28 - Science & Technology")
    category = input("\n🎯 Enter category ID [default: 22]: ").strip() or "22"
    
    print("\n🔒 Privacy Status:")
    print("  1. public   - Anyone can see")
    print("  2. unlisted - Only people with link (recommended for ads)")
    print("  3. private  - Only you can see")
    privacy_choice = input("\nChoose privacy (1/2/3) [default: 2]: ").strip() or "2"
    privacy_map = {"1": "public", "2": "unlisted", "3": "private"}
    privacy = privacy_map.get(privacy_choice, "unlisted")
    
    print("\n" + "=" * 70)
    print("📋 Upload Summary:")
    print(f"  Type: {'YouTube Short 📱' if is_short else 'Regular Video 🎬'}")
    print(f"  File: {video_file}")
    print(f"  Title: {title}")
    print(f"  Description: {description}")
    print(f"  Tags: {', '.join(tags)}")
    print(f"  Category: {category}")
    print(f"  Privacy: {privacy}")
    print("=" * 70)
    
    confirm = input("\n✅ Proceed with upload? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Upload cancelled.")
        return
    
    # Authenticate
    youtube_service = get_authenticated_service()
    
    # Upload
    video_id = upload_video(
        youtube_service,
        video_file,
        title,
        description,
        tags,
        category,
        privacy,
        is_short=is_short
    )
    
    if video_id:
        print("\n" + "=" * 70)
        print("🎉 SUCCESS!")
        if is_short:
            print(f"📱 Short: https://youtube.com/shorts/{video_id}")
        else:
            print(f"🔗 Watch: https://www.youtube.com/watch?v={video_id}")
        print(f"📊 Studio: https://studio.youtube.com/video/{video_id}/edit")
        print("=" * 70)

if __name__ == "__main__":
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print("❌ Error: client_secrets.json not found!")
        print("\n📋 Setup Instructions:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Enable YouTube Data API v3")
        print("3. Create OAuth 2.0 credentials (Desktop app)")
        print("4. Download JSON and rename to 'client_secrets.json'")
        print("5. Place it in the same folder as this script")
        exit(1)
    
    interactive_upload()