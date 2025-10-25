import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# This scope allows for full read/write access to the
# authenticated user's YouTube videos.
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
CLIENT_SECRETS_FILE = "client_secrets.json"  # Your downloaded credentials file

# --- Authentication Function ---
def get_authenticated_service():
    """Authenticates the user and returns a YouTube service object."""
    credentials = None
    # token.pickle stores the user's access and refresh tokens.
    # It's created automatically when the auth flow completes.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            credentials = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("🔄 Refreshing expired credentials...")
            credentials.refresh(Request())
        else:
            print("🔐 Starting authentication flow...")
            print("📱 A browser window will open. Please log in with your YouTube account.")
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            # This will open a new browser window for the user to log in
            credentials = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(credentials, token)
        print("✅ Authentication successful!")

    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)


# --- Video Upload Function ---
def upload_video(youtube, file_path, title, description, tags, category_id, privacy_status):
    """Uploads a video to YouTube."""
    
    # Validate file
    if not os.path.exists(file_path):
        print(f"❌ Error: Video file not found at '{file_path}'")
        return None
    
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
    print(f"📁 File: {file_path} ({file_size:.2f} MB)")
    
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id  # e.g., '22' for 'People & Blogs'
        },
        "status": {
            "privacyStatus": privacy_status,  # "public", "private", or "unlisted"
            "selfDeclaredMadeForKids": False  # Required field
        }
    }

    # Create a MediaFileUpload object
    media = MediaFileUpload(file_path,
                            chunksize=-1,
                            resumable=True,
                            mimetype='video/*')

    # Call the API's videos.insert method to upload the video
    print(f"\n🚀 Uploading video to YouTube...")
    print(f"📝 Title: {title}")
    print(f"🔒 Privacy: {privacy_status}")
    
    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    # Execute the upload request
    response = None
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"⏳ Uploading: {progress}%", end="\r")
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            return None

    print(f"\n✅ Upload complete!")
    print(f"🎬 Video ID: {response.get('id')}")
    print(f"🔗 URL: https://www.youtube.com/watch?v={response.get('id')}")
    return response.get('id')


# --- Interactive Mode ---
def interactive_upload():
    """Interactive mode to upload videos."""
    print("=" * 70)
    print("🎬 YouTube Video Uploader")
    print("=" * 70)
    print()
    
    # Get video file
    video_file = input("📁 Enter video file path (or press Enter for 'my_video.mp4'): ").strip()
    if not video_file:
        video_file = "my_video.mp4"
    
    if not os.path.exists(video_file):
        print(f"❌ Error: Video file not found at '{video_file}'")
        return
    
    # Get video details
    title = input("📝 Enter video title: ").strip() or "My Test Video"
    description = input("📄 Enter video description: ").strip() or "Uploaded via Python script"
    tags_input = input("🏷️  Enter tags (comma-separated): ").strip()
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
        privacy
    )
    
    if video_id:
        print("\n" + "=" * 70)
        print("🎉 SUCCESS!")
        print(f"🔗 Watch: https://www.youtube.com/watch?v={video_id}")
        print(f"📊 Studio: https://studio.youtube.com/video/{video_id}/edit")
        print("=" * 70)


# --- Main execution ---
if __name__ == "__main__":
    # Check for client_secrets.json
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print("❌ Error: client_secrets.json not found!")
        print("\n📋 Setup Instructions:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Enable YouTube Data API v3")
        print("3. Create OAuth 2.0 credentials (Desktop app)")
        print("4. Download JSON and rename to 'client_secrets.json'")
        print("5. Place it in the same folder as this script")
        exit(1)
    
    # Run interactive mode
    interactive_upload()