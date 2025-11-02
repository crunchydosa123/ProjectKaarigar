"""
Quick Test to Verify the Ideas Generation Fix
Tests the /api/reel-generation/ideas endpoint with form data
"""

import requests
import json

BASE_URL = "https://reels-editor-298842469563.asia-south1.run.app"

def test_ideas_fix():
    """Test the ideas generation endpoint with form data"""
    print("🧪 Testing Ideas Generation Fix...")
    print(f"🌐 URL: {BASE_URL}/api/reel-generation/ideas")
    
    # Test with form data (should work)
    data = {'initial_prompt': 'A magical diary with glowing symbols and mystical energy'}
    
    try:
        response = requests.post(f"{BASE_URL}/api/reel-generation/ideas", data=data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                ideas = result.get('ideas', [])
                print(f"✅ SUCCESS! Generated {len(ideas)} ideas:")
                for i, idea in enumerate(ideas, 1):
                    print(f"   {i}. {idea}")
                return True
            else:
                print(f"❌ API Error: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Quick Ideas Generation Test")
    print("=" * 50)
    
    success = test_ideas_fix()
    
    print("=" * 50)
    if success:
        print("🎉 Fix verified! Ideas generation is working.")
    else:
        print("💥 Fix failed. Still having issues.")


