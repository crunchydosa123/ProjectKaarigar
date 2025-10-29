#!/usr/bin/env python3
"""
Test the video editing endpoint to see if it's loading videos correctly
"""

import requests
import json

def test_video_endpoint():
    base_url = "http://localhost:5000"
    
    print("Testing video editing endpoint...")
    
    # Test get user videos endpoint
    try:
        response = requests.get(f"{base_url}/api/video-edit/get-user-videos")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data.get('count', 0)} videos")
            videos = data.get('videos', [])
            for i, video in enumerate(videos):
                print(f"  Video {i+1}: {video.get('title', 'No title')} ({video.get('type', 'unknown')})")
                print(f"    URL: {video.get('public_url', 'No URL')[:60]}...")
        elif response.status_code == 401:
            print("❌ Authentication required - make sure you're logged in")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_video_endpoint()



