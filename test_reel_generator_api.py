"""
Test script for the new Reel Generator API
Tests the backend route for reel generation
"""

import requests
import os
from pathlib import Path

# Backend URL
BASE_URL = "http://localhost:5000"

def test_health_check():
    """Test health check endpoint"""
    print("🔍 Testing Health Check...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/reel-generator/health")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check Passed")
            print(f"   Status: {data.get('status')}")
            print(f"   Service: {data.get('service')}")
            print(f"   Bucket: {data.get('bucket')}")
            return True
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
        return False

def test_generate_reel():
    """Test reel generation with images"""
    print("\n🎬 Testing Reel Generation...")
    
    # Test image paths
    image_paths = [
        r"D:\projects\Project_Kaarigar\3rd_Times_Thecharm\ProjectKaarigar\edited_diary_magical.png",
        r"D:\projects\Project_Kaarigar\3rd_Times_Thecharm\ProjectKaarigar\Model\images (2).jpeg"
    ]
    
    # Check if images exist
    existing_images = [path for path in image_paths if os.path.exists(path)]
    
    if not existing_images:
        print("❌ No test images found")
        return False
    
    print(f"📸 Using {len(existing_images)} images")
    
    # Prepare form data
    data = {
        'prompt': 'Create a magical story video from these images',
        'user_id': 'user11'  # Using test user ID
    }
    
    # Prepare files
    files = []
    for img_path in existing_images:
        files.append(('images', open(img_path, 'rb')))
    
    try:
        response = requests.post(f"{BASE_URL}/api/reel-generator", data=data, files=files)
        
        # Close files
        for _, file_handle in files:
            file_handle.close()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Reel Generation Successful")
            print(f"   Reel ID: {result.get('reel_id')}")
            print(f"   Title: {result.get('title')}")
            print(f"   Public URL: {result.get('public_url')}")
            print(f"   File Size: {result.get('file_size_mb')} MB")
            print(f"   Images Used: {result.get('images_used')}")
            return True
        else:
            print(f"❌ Reel Generation Failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Reel Generation Error: {e}")
        return False

def test_get_user_reels():
    """Test getting user reels"""
    print("\n📋 Testing Get User Reels...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/reel-generator/user-reels?user_id=user11")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Get User Reels Successful")
            print(f"   Total Reels: {result.get('total')}")
            
            reels = result.get('reels', [])
            for i, reel in enumerate(reels[:3]):  # Show first 3
                print(f"   Reel {i+1}: {reel.get('title')}")
            
            return True
        else:
            print(f"❌ Get User Reels Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Get User Reels Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Reel Generator API")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Generate Reel", test_generate_reel),
        ("Get User Reels", test_get_user_reels),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status} - {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️ Some tests failed")

if __name__ == "__main__":
    main()
