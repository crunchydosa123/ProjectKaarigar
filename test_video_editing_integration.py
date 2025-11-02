#!/usr/bin/env python3
"""
Test script for video editing integration
Tests the video editing endpoints to ensure they work correctly
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:5000"
FFMPEG_SERVICE_URL = "https://video-editor-298842469563.asia-south1.run.app"

def test_video_editing_endpoints():
    """Test all video editing endpoints"""
    
    print("🎬 Testing Video Editing Integration")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n1. Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/api/video-edit/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Get User Videos (requires authentication)
    print("\n2. Testing Get User Videos...")
    try:
        # This will fail without authentication, but we can check the endpoint exists
        response = requests.get(f"{BASE_URL}/api/video-edit/get-user-videos")
        if response.status_code == 401:
            print("✅ Endpoint exists (requires authentication)")
        elif response.status_code == 200:
            data = response.json()
            print("✅ User videos retrieved successfully")
            print(f"   Videos found: {len(data.get('videos', []))}")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Get user videos error: {e}")
    
    # Test 3: Get Trending Songs
    print("\n3. Testing Get Trending Songs...")
    try:
        response = requests.get(f"{BASE_URL}/api/video-edit/get-trending-songs")
        if response.status_code == 200:
            data = response.json()
            print("✅ Trending songs retrieved successfully")
            print(f"   Songs found: {len(data.get('songs', []))}")
            if data.get('songs'):
                print(f"   First song: {data['songs'][0]}")
        else:
            print(f"❌ Get trending songs failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Get trending songs error: {e}")
    
    # Test 4: Test FFmpeg Service Directly
    print("\n4. Testing FFmpeg Service Directly...")
    try:
        response = requests.get(f"{FFMPEG_SERVICE_URL}/health")
        if response.status_code == 200:
            print("✅ FFmpeg service is accessible")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ FFmpeg service error: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ FFmpeg service error: {e}")
    
    # Test 5: Test Trending Songs from FFmpeg Service
    print("\n5. Testing Trending Songs from FFmpeg Service...")
    try:
        response = requests.get(f"{FFMPEG_SERVICE_URL}/trending-songs")
        if response.status_code == 200:
            data = response.json()
            print("✅ FFmpeg trending songs retrieved")
            print(f"   Songs found: {len(data.get('songs', []))}")
            if data.get('songs'):
                print(f"   First song: {data['songs'][0]}")
        else:
            print(f"❌ FFmpeg trending songs failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ FFmpeg trending songs error: {e}")
    
    print("\n" + "=" * 50)
    print("🎬 Video Editing Integration Test Complete")
    print("\nTo test with authentication:")
    print("1. Start the backend: cd ProjectKaarigar/backend && python app.py")
    print("2. Login through the frontend to get session cookies")
    print("3. The video editing should work in the frontend interface")

if __name__ == "__main__":
    test_video_editing_endpoints()