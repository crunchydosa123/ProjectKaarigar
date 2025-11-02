"""
YouTube Analytics Fetcher
Fetches analytics data for your YouTube channel and videos.
"""

import os
import pickle
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# SCOPES for both upload and analytics
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.upload"
]

API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
ANALYTICS_API_SERVICE_NAME = "youtubeAnalytics"
ANALYTICS_API_VERSION = "v2"
CLIENT_SECRETS_FILE = "client_secrets.json"
TOKEN_FILE = "token_analytics.pickle"

def get_authenticated_services():
    """Authenticates the user and returns YouTube and Analytics service objects."""
    credentials = None
    
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("🔄 Refreshing expired credentials...")
            credentials.refresh(Request())
        else:
            print("🔐 Starting authentication flow...")
            print("📱 A browser window will open. Please log in with your YouTube account.")
            print("⚠️  Make sure to allow ALL requested permissions (YouTube + Analytics)")
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(credentials, token)
        print("✅ Authentication successful!")

    youtube = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
    analytics = build(ANALYTICS_API_SERVICE_NAME, ANALYTICS_API_VERSION, credentials=credentials)
    
    return youtube, analytics

def get_channel_info(youtube):
    """Get channel information."""
    try:
        request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            mine=True
        )
        response = request.execute()
        
        if not response.get("items"):
            print("❌ No channel found for this account")
            return None
        
        channel = response["items"][0]
        stats = channel["statistics"]
        snippet = channel["snippet"]
        
        print("\n" + "=" * 70)
        print("📺 CHANNEL INFORMATION")
        print("=" * 70)
        print(f"📛 Channel Name: {snippet['title']}")
        print(f"🆔 Channel ID: {channel['id']}")
        print(f"👥 Subscribers: {int(stats.get('subscriberCount', 0)):,}")
        print(f"🎬 Total Videos: {int(stats.get('videoCount', 0)):,}")
        print(f"👁️  Total Views: {int(stats.get('viewCount', 0)):,}")
        print("=" * 70)
        
        return channel['id']
        
    except HttpError as e:
        print(f"❌ Error fetching channel info: {e}")
        return None

def get_channel_analytics(analytics, channel_id, days=30):
    """Get channel analytics for the last N days."""
    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        print(f"\n📊 Fetching analytics from {start_date} to {end_date}...")
        
        # Channel-level metrics
        request = analytics.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start_date,
            endDate=end_date,
            metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost,likes,dislikes,comments,shares",
            dimensions="day",
            sort="day"
        )
        response = request.execute()
        
        print("\n" + "=" * 70)
        print(f"📈 CHANNEL ANALYTICS (Last {days} Days)")
        print("=" * 70)
        
        if "rows" in response:
            total_views = 0
            total_watch_time = 0
            total_subs_gained = 0
            total_subs_lost = 0
            total_likes = 0
            total_comments = 0
            
            for row in response["rows"]:
                total_views += row[1]
                total_watch_time += row[2]
                total_subs_gained += row[4]
                total_subs_lost += row[5]
                total_likes += row[6]
                total_comments += row[8]
            
            avg_view_duration = total_watch_time * 60 / total_views if total_views > 0 else 0
            net_subscribers = total_subs_gained - total_subs_lost
            
            print(f"👁️  Total Views: {total_views:,}")
            print(f"⏱️  Watch Time: {total_watch_time:,} minutes ({total_watch_time/60:.1f} hours)")
            print(f"⌚ Avg View Duration: {avg_view_duration:.0f} seconds")
            print(f"👥 Subscribers Gained: +{total_subs_gained:,}")
            print(f"👥 Subscribers Lost: -{total_subs_lost:,}")
            print(f"📊 Net Subscribers: {net_subscribers:+,}")
            print(f"👍 Total Likes: {total_likes:,}")
            print(f"💬 Total Comments: {total_comments:,}")
            print("=" * 70)
            
            return response
        else:
            print("ℹ️  No analytics data available for this period")
            return None
            
    except HttpError as e:
        print(f"❌ Error fetching analytics: {e}")
        if "quotaExceeded" in str(e):
            print("⚠️  YouTube Analytics API quota exceeded. Try again tomorrow.")
        return None

def get_recent_videos(youtube, max_results=10):
    """Get recent uploaded videos."""
    try:
        # Get uploads playlist ID
        request = youtube.channels().list(
            part="contentDetails",
            mine=True
        )
        response = request.execute()
        
        if not response.get("items"):
            return []
        
        uploads_playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        
        # Get videos from uploads playlist
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=max_results
        )
        response = request.execute()
        
        print("\n" + "=" * 70)
        print(f"🎬 RECENT VIDEOS (Last {len(response.get('items', []))})")
        print("=" * 70)
        
        videos = []
        for item in response.get("items", []):
            video_id = item["contentDetails"]["videoId"]
            title = item["snippet"]["title"]
            published_at = item["snippet"]["publishedAt"]
            
            # Get video statistics
            stats_request = youtube.videos().list(
                part="statistics",
                id=video_id
            )
            stats_response = stats_request.execute()
            
            if stats_response.get("items"):
                stats = stats_response["items"][0]["statistics"]
                views = int(stats.get("viewCount", 0))
                likes = int(stats.get("likeCount", 0))
                comments = int(stats.get("commentCount", 0))
                
                video_info = {
                    "id": video_id,
                    "title": title,
                    "published": published_at,
                    "views": views,
                    "likes": likes,
                    "comments": comments
                }
                videos.append(video_info)
                
                print(f"\n📹 {title[:50]}...")
                print(f"   🆔 ID: {video_id}")
                print(f"   👁️  Views: {views:,}")
                print(f"   👍 Likes: {likes:,}")
                print(f"   💬 Comments: {comments:,}")
                print(f"   🔗 https://youtube.com/watch?v={video_id}")
        
        print("=" * 70)
        return videos
        
    except HttpError as e:
        print(f"❌ Error fetching videos: {e}")
        return []

def get_video_analytics(analytics, video_id, days=30):
    """Get analytics for a specific video."""
    try:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        request = analytics.reports().query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics="views,estimatedMinutesWatched,averageViewDuration,likes,comments,shares",
            dimensions="day",
            filters=f"video=={video_id}",
            sort="day"
        )
        response = request.execute()
        
        if "rows" in response:
            total_views = sum(row[1] for row in response["rows"])
            total_watch_time = sum(row[2] for row in response["rows"])
            total_likes = sum(row[4] for row in response["rows"])
            total_comments = sum(row[5] for row in response["rows"])
            
            print(f"\n📊 Video Analytics (Last {days} days):")
            print(f"   👁️  Views: {total_views:,}")
            print(f"   ⏱️  Watch Time: {total_watch_time:,} minutes")
            print(f"   👍 Likes: {total_likes:,}")
            print(f"   💬 Comments: {total_comments:,}")
            
            return response
        else:
            print(f"ℹ️  No analytics data for video {video_id}")
            return None
            
    except HttpError as e:
        print(f"❌ Error fetching video analytics: {e}")
        return None

def interactive_analytics():
    """Interactive analytics dashboard."""
    print("=" * 70)
    print("📊 YouTube Analytics Dashboard")
    print("=" * 70)
    print()
    
    # Authenticate
    youtube, analytics = get_authenticated_services()
    
    # Get channel info
    channel_id = get_channel_info(youtube)
    if not channel_id:
        return
    
    print("\n📋 What would you like to see?")
    print("  1. Channel Analytics (Last 30 days)")
    print("  2. Channel Analytics (Last 7 days)")
    print("  3. Channel Analytics (Last 90 days)")
    print("  4. Recent Videos List")
    print("  5. Specific Video Analytics")
    print("  6. Full Report (All of the above)")
    
    choice = input("\nEnter choice (1-6) [default: 6]: ").strip() or "6"
    
    if choice in ["1", "6"]:
        get_channel_analytics(analytics, channel_id, days=30)
    
    if choice in ["2"]:
        get_channel_analytics(analytics, channel_id, days=7)
    
    if choice in ["3"]:
        get_channel_analytics(analytics, channel_id, days=90)
    
    if choice in ["4", "6"]:
        recent_videos = get_recent_videos(youtube, max_results=10)
        
        if choice == "5" or (choice == "6" and recent_videos):
            print("\n📹 Want to see analytics for a specific video?")
            video_id = input("Enter video ID (or press Enter to skip): ").strip()
            
            if video_id:
                get_video_analytics(analytics, video_id, days=30)
    
    print("\n✅ Analytics fetch complete!")

if __name__ == "__main__":
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print("❌ Error: client_secrets.json not found!")
        print("\n📋 Setup Instructions:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Select project: karigar-475215")
        print("3. Go to APIs & Services → Library")
        print("4. Enable 'YouTube Data API v3' and 'YouTube Analytics API'")
        print("5. Go to APIs & Services → Credentials")
        print("6. Create OAuth 2.0 Client ID (Desktop app)")
        print("7. Download JSON and rename to 'client_secrets.json'")
        print("8. Place it in this folder")
        print("\n⚠️  Don't forget to configure OAuth consent screen!")
        exit(1)
    
    interactive_analytics()
