#!/usr/bin/env python3
"""
Test script for GCS Video Editor Flask API
This script demonstrates how to use the API endpoints
"""

import requests
import base64
import json
import os
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:5000"

def test_health():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_upload_video(video_path):
    """Test video upload endpoint"""
    print(f"📤 Testing video upload: {video_path}")
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return None
    
    with open(video_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/upload", files=files)
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    print()
    
    return result

def test_video_info(video_path):
    """Test video info endpoint"""
    print(f"📊 Testing video info: {video_path}")
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return None
    
    # Read video file and encode to base64
    with open(video_path, 'rb') as f:
        video_data = base64.b64encode(f.read()).decode('utf-8')
    
    payload = {
        "file": video_data
    }
    
    response = requests.post(f"{BASE_URL}/video-info", json=payload)
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    print()
    
    return result

def test_edit_video(video_path, edit_prompt, topic="test_project", save_name="edited_video"):
    """Test video editing endpoint"""
    print(f"🎬 Testing video edit: {edit_prompt}")
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return None
    
    # Read video file and encode to base64
    with open(video_path, 'rb') as f:
        video_data = base64.b64encode(f.read()).decode('utf-8')
    
    payload = {
        "file": video_data,
        "edit_prompt": edit_prompt,
        "topic": topic,
        "save_name": save_name
    }
    
    response = requests.post(f"{BASE_URL}/edit", json=payload)
    
    print(f"Status: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        print(f"✅ Edit successful!")
        print(f"📊 Video info: {json.dumps(result.get('video_info', {}), indent=2)}")
        if result.get('saved_url'):
            print(f"🔗 Saved URL: {result['saved_url']}")
        
        # Save edited video locally
        if result.get('edited_video'):
            edited_data = base64.b64decode(result['edited_video'])
            output_path = f"edited_{Path(video_path).stem}_{save_name}.mp4"
            with open(output_path, 'wb') as f:
                f.write(edited_data)
            print(f"💾 Edited video saved locally: {output_path}")
    else:
        print(f"❌ Edit failed: {result.get('error')}")
    
    print()
    return result

def test_trending_songs():
    """Test trending songs endpoint"""
    print("🎵 Testing trending songs...")
    response = requests.get(f"{BASE_URL}/trending-songs")
    
    print(f"Status: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        songs = result.get('songs', [])
        print(f"Found {len(songs)} trending songs:")
        for song in songs:
            print(f"  - {song['title']} by {song['artist']} ({song['duration']}s)")
    else:
        print(f"❌ Failed: {result.get('error')}")
    
    print()
    return result

def test_edited_videos(topic=None):
    """Test edited videos listing endpoint"""
    print(f"📋 Testing edited videos listing (topic: {topic or 'all'})...")
    
    url = f"{BASE_URL}/edited-videos"
    if topic:
        url += f"?topic={topic}"
    
    response = requests.get(url)
    
    print(f"Status: {response.status_code}")
    result = response.json()
    
    if result.get('success'):
        videos = result.get('videos', [])
        print(f"Found {len(videos)} edited videos:")
        for video in videos:
            print(f"  - {video['filename']} ({video['size_mb']:.2f} MB, {video['created']})")
    else:
        print(f"❌ Failed: {result.get('error')}")
    
    print()
    return result

def main():
    """Main test function"""
    print("🎬 GCS Video Editor API Test Suite")
    print("=" * 50)
    
    # Test health check
    test_health()
    
    # Test trending songs
    test_trending_songs()
    
    # Test edited videos listing
    test_edited_videos()
    
    # You need to provide a video file path for these tests
    video_path = input("Enter path to a video file for testing (or press Enter to skip): ").strip()
    
    if video_path and os.path.exists(video_path):
        # Test video info
        test_video_info(video_path)
        
        # Test various edits
        test_edits = [
            "make it black and white",
            "increase brightness",
            "trim first 5 seconds",
            "crop to square (1:1)",
            "speed up 2x"
        ]
        
        for i, edit_prompt in enumerate(test_edits):
            test_edit_video(video_path, edit_prompt, f"test_project", f"edit_{i+1}")
        
        # Test edited videos listing for our test project
        test_edited_videos("test_project")
    else:
        print("⚠️  Skipping video tests - no valid video file provided")
    
    print("✅ Test suite completed!")

if __name__ == "__main__":
    main()
