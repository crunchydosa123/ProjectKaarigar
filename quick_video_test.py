#!/usr/bin/env python3
"""
Quick test to check if video editing backend is working
"""

import requests
import json

def test_backend():
    base_url = "http://localhost:5000"
    
    print("Testing video editing backend...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/video-edit/health")
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
    
    # Test get user videos (will fail without auth, but we can see the response)
    try:
        response = requests.get(f"{base_url}/api/video-edit/get-user-videos")
        print(f"Get user videos: {response.status_code}")
        if response.status_code == 401:
            print("✅ Endpoint exists but requires authentication")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Get user videos failed: {e}")
    
    # Test trending songs
    try:
        response = requests.get(f"{base_url}/api/video-edit/get-trending-songs")
        print(f"Get trending songs: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Trending songs: {len(data.get('songs', []))} songs")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Get trending songs failed: {e}")

if __name__ == "__main__":
    test_backend()



