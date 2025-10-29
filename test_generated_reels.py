"""
Test script to check generated reels functionality
"""

import requests
import json

BASE_URL = "https://reels-editor-298842469563.asia-south1.run.app"

def test_generate_reel():
    """Test generating a reel and check if it's saved to Firestore"""
    print("🧪 Testing Reel Generation and Firestore Storage...")
    
    # Test data
    test_data = {
        'prompt': 'A beautiful sunset over mountains',
        'user_id': 'test_user_123',
        'image_urls': json.dumps(['https://picsum.photos/400/300?random=1', 'https://picsum.photos/400/300?random=2'])
    }
    
    try:
        print(f"🌐 URL: {BASE_URL}/api/reel-generator")
        print(f"📝 Test data: {test_data}")
        
        response = requests.post(
            f"{BASE_URL}/api/reel-generator",
            data=test_data,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Generation Response: {json.dumps(result, indent=2)}")
            
            # Now test if we can retrieve the generated reels
            if result.get('success'):
                print("\n🔄 Testing retrieval of generated reels...")
                retrieve_response = requests.get(
                    f"{BASE_URL}/api/reel-generator/generated-reels?user_id=test_user_123",
                    timeout=30
                )
                
                print(f"Retrieve Status Code: {retrieve_response.status_code}")
                if retrieve_response.status_code == 200:
                    retrieve_result = retrieve_response.json()
                    print(f"✅ Retrieved Reels: {json.dumps(retrieve_result, indent=2)}")
                    return True
                else:
                    print(f"❌ Failed to retrieve reels: {retrieve_response.text}")
                    return False
            else:
                print(f"❌ Generation failed: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_health():
    """Test if service is running"""
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
    print("🚀 Generated Reels Test")
    print("=" * 50)
    
    # First check if service is running
    health_ok = test_health()
    
    if health_ok:
        print("\n" + "=" * 50)
        # Test generation and retrieval
        test_ok = test_generate_reel()
        
        print("=" * 50)
        if test_ok:
            print("🎉 Generated reels functionality is working!")
        else:
            print("💥 Generated reels functionality has issues.")
    else:
        print("💥 Service is not running or health check failed.")

