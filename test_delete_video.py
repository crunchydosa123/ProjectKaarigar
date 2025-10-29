"""
Test script to debug video deletion functionality
"""

import requests
import json

BASE_URL = "https://reels-editor-298842469563.asia-south1.run.app"

def test_delete_video():
    """Test the delete video endpoint"""
    print("🧪 Testing Video Delete Functionality...")
    print(f"🌐 URL: {BASE_URL}/api/reel-generator/delete-video")
    
    # Test data - you'll need to replace with actual video ID and user ID
    test_data = {
        "video_id": "test-video-123",
        "user_id": "test-user-456", 
        "cloud_path": "media/test-user-456/generated_video/test_video.mp4"
    }
    
    try:
        response = requests.delete(
            f"{BASE_URL}/api/reel-generator/delete-video",
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            try:
                error_result = response.json()
                print(f"Error Response: {json.dumps(error_result, indent=2)}")
            except:
                print(f"Raw Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_health_check():
    """Test if the service is running"""
    print("\n🏥 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/api/reel-generator/health", timeout=10)
        print(f"Health Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Health Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"Health check error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Video Delete Test")
    print("=" * 50)
    
    # First check if service is running
    health_ok = test_health_check()
    
    if health_ok:
        print("\n" + "=" * 50)
        # Test delete functionality
        delete_ok = test_delete_video()
        
        print("=" * 50)
        if delete_ok:
            print("🎉 Delete endpoint is working!")
        else:
            print("💥 Delete endpoint has issues.")
    else:
        print("💥 Service is not running or health check failed.")

