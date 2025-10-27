import requests
import json
import os
import time
from datetime import datetime

# Base API URL
BASE_URL = "http://127.0.0.1:5000"

# Test images location
TEST_IMAGES = [
    r"D:\Barclays\ProjectKaarigar\Model\images (1).jpeg",
    r"D:\Barclays\ProjectKaarigar\Model\images (2).jpeg"
]

# ==================== UTILITY FUNCTIONS ====================

def log_test(test_name: str, endpoint: str, method: str = "POST"):
    """Log test start"""
    print(f"\n{'='*80}")
    print(f"🧪 TEST: {test_name}")
    print(f"   Endpoint: {method} {endpoint}")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")

def log_result(success: bool, status_code: int, response_time: float, data: dict = None):
    """Log test result with timing"""
    status_icon = "✅" if success else "❌"
    print(f"\n{status_icon} Status Code: {status_code}")
    print(f"⏱️  Response Time: {response_time:.2f}s")
    if data:
        data_str = json.dumps(data, indent=2)
        if len(data_str) > 1000:
            print(f"\n📄 Response (truncated):\n{data_str[:1000]}...")
        else:
            print(f"\n📄 Response:\n{data_str}")

def verify_image_exists(image_path: str) -> bool:
    """Verify image file exists"""
    if os.path.exists(image_path):
        file_size = os.path.getsize(image_path) / (1024 * 1024)
        print(f"   ✅ Image found: {os.path.basename(image_path)} ({file_size:.2f} MB)")
        return True
    else:
        print(f"   ❌ Image not found: {image_path}")
        return False

# ==================== TEST SINGLE ENDPOINT ONLY ====================

def test_image_to_video_single_endpoint():
    """
    Test ONLY: /api/generate-video/images endpoint with SINGLE image
    
    This is a focused test for the image-to-video generation endpoint
    with auto-prompt generation capability.
    """
    log_test(
        "Image to Video Generation (SINGLE IMAGE)",
        f"{BASE_URL}/api/generate-video/images",
        "POST"
    )
    
    try:
        # Step 1: Verify image exists
        image_path = TEST_IMAGES[0]
        print(f"\n📁 Image File Path: {image_path}")
        
        if not verify_image_exists(image_path):
            print("\n❌ FAILED: Image file not found")
            return False
        
        # Step 2: Prepare request
        print("\n📤 Preparing request...")
        print(f"   - Endpoint: POST /api/generate-video/images")
        print(f"   - Image: {os.path.basename(image_path)}")
        print(f"   - Timeout: 15 minutes (900 seconds)")
        print(f"   - File size: {os.path.getsize(image_path) / (1024*1024):.2f} MB")
        
        # Step 3: Send request
        print("\n⏳ Sending request to server...")
        print("   ⚠️  This may take several minutes while the video is being generated...")
        
        start_time = time.time()
        
        with open(image_path, 'rb') as f:
            files = {'images': f}
            data = {'prompt': 'Transform this image into an engaging social media video'}
            
            response = requests.post(
                f"{BASE_URL}/api/generate-video/images",
                files=files,
                data=data,
                timeout=900  # 15 minutes
            )
        
        response_time = time.time() - start_time
        
        # Step 4: Process response
        print(f"\n✅ Response received!")
        
        try:
            response_data = response.json()
        except:
            response_data = {"raw_response": response.text}
        
        success = response.status_code in [200, 206, 500]
        log_result(success, response.status_code, response_time, response_data)
        
        # Step 5: Analyze results
        print("\n📊 ANALYSIS:")
        print(f"   - Status Code: {response.status_code}")
        print(f"   - Response Time: {response_time:.2f}s ({response_time/60:.2f} minutes)")
        
        if response.status_code == 200:
            print("   - Status: ✅ SUCCESS - Video generated and uploaded")
            if 'generated_video_url' in response_data:
                print(f"   - Video URL: {response_data['generated_video_url']}")
            if 'generated_prompt' in response_data:
                print(f"   - Generated Prompt: {response_data['generated_prompt'][:100]}...")
            if 'file_size_mb' in response_data:
                print(f"   - File Size: {response_data['file_size_mb']} MB")
        
        elif response.status_code == 206:
            print("   - Status: ⚠️  PARTIAL SUCCESS - Video generated, but cloud upload failed")
            if 'file_size_mb' in response_data:
                print(f"   - File Size: {response_data['file_size_mb']} MB")
        
        elif response.status_code == 500:
            print("   - Status: ❌ SERVER ERROR")
            if 'error' in response_data:
                print(f"   - Error: {response_data['error']}")
        
        else:
            print(f"   - Status: ❓ UNEXPECTED ({response.status_code})")
        
        # Step 6: Return result
        print(f"\n{'='*80}")
        if success:
            print("✅ TEST PASSED")
        else:
            print("❌ TEST FAILED")
        print(f"{'='*80}\n")
        
        return success
    
    except requests.exceptions.Timeout:
        response_time = time.time() - start_time
        print(f"\n⚠️  REQUEST TIMEOUT")
        print(f"   - Timeout after: {response_time:.2f}s ({response_time/60:.2f} minutes)")
        print("   - This doesn't mean the request failed!")
        print("   - The server may still be generating the video")
        print("   - Check the server logs for progress")
        print(f"{'='*80}\n")
        return False
    
    except ConnectionError as e:
        print(f"\n❌ CONNECTION ERROR")
        print(f"   - Error: {str(e)}")
        print(f"   - Make sure the Flask server is running:")
        print(f"   - Command: python reel_generation_api.py")
        print(f"{'='*80}\n")
        return False
    
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR")
        print(f"   - Error Type: {type(e).__name__}")
        print(f"   - Error Message: {str(e)}")
        print(f"{'='*80}\n")
        return False


def test_image_to_video_multiple_endpoint():
    """
    Test ONLY: /api/generate-video/images endpoint with MULTIPLE images
    
    This tests the endpoint with multiple images for slideshow generation.
    """
    log_test(
        "Image to Video Generation (MULTIPLE IMAGES)",
        f"{BASE_URL}/api/generate-video/images",
        "POST"
    )
    
    try:
        # Step 1: Verify images exist
        print(f"\n📁 Image Files: {len(TEST_IMAGES)} images")
        
        for img_path in TEST_IMAGES:
            if not verify_image_exists(img_path):
                print(f"\n❌ FAILED: Image file not found - {img_path}")
                return False
        
        # Step 2: Prepare request
        print("\n📤 Preparing request...")
        print(f"   - Endpoint: POST /api/generate-video/images")
        print(f"   - Images: {len(TEST_IMAGES)} files")
        print(f"   - Timeout: 15 minutes (900 seconds)")
        
        total_size = sum(os.path.getsize(p) for p in TEST_IMAGES) / (1024*1024)
        print(f"   - Total size: {total_size:.2f} MB")
        
        # Step 3: Send request
        print("\n⏳ Sending request to server...")
        print("   ⚠️  This may take several minutes while the video is being generated...")
        
        start_time = time.time()
        
        files = []
        for img_path in TEST_IMAGES:
            files.append(('images', open(img_path, 'rb')))
        
        data = {'prompt': 'Create an amazing slideshow with smooth transitions'}
        
        response = requests.post(
            f"{BASE_URL}/api/generate-video/images",
            files=files,
            data=data,
            timeout=900  # 15 minutes
        )
        response_time = time.time() - start_time
        
        # Close files
        for _, f in files:
            f.close()
        
        # Step 4: Process response
        print(f"\n✅ Response received!")
        
        try:
            response_data = response.json()
        except:
            response_data = {"raw_response": response.text}
        
        success = response.status_code in [200, 206, 500]
        log_result(success, response.status_code, response_time, response_data)
        
        # Step 5: Analyze results
        print("\n📊 ANALYSIS:")
        print(f"   - Status Code: {response.status_code}")
        print(f"   - Response Time: {response_time:.2f}s ({response_time/60:.2f} minutes)")
        
        if response.status_code == 200:
            print("   - Status: ✅ SUCCESS - Video generated and uploaded")
            if 'generated_video_url' in response_data:
                print(f"   - Video URL: {response_data['generated_video_url']}")
            if 'generated_prompt' in response_data:
                print(f"   - Generated Prompt: {response_data['generated_prompt'][:100]}...")
            if 'file_size_mb' in response_data:
                print(f"   - File Size: {response_data['file_size_mb']} MB")
        
        elif response.status_code == 206:
            print("   - Status: ⚠️  PARTIAL SUCCESS - Video generated, but cloud upload failed")
            if 'file_size_mb' in response_data:
                print(f"   - File Size: {response_data['file_size_mb']} MB")
        
        elif response.status_code == 500:
            print("   - Status: ❌ SERVER ERROR")
            if 'error' in response_data:
                print(f"   - Error: {response_data['error']}")
        
        else:
            print(f"   - Status: ❓ UNEXPECTED ({response.status_code})")
        
        # Step 6: Return result
        print(f"\n{'='*80}")
        if success:
            print("✅ TEST PASSED")
        else:
            print("❌ TEST FAILED")
        print(f"{'='*80}\n")
        
        return success
    
    except requests.exceptions.Timeout:
        response_time = time.time() - start_time
        print(f"\n⚠️  REQUEST TIMEOUT")
        print(f"   - Timeout after: {response_time:.2f}s ({response_time/60:.2f} minutes)")
        print("   - This doesn't mean the request failed!")
        print("   - The server may still be generating the video")
        print("   - Check the server logs for progress")
        print(f"{'='*80}\n")
        return False
    
    except ConnectionError as e:
        print(f"\n❌ CONNECTION ERROR")
        print(f"   - Error: {str(e)}")
        print(f"   - Make sure the Flask server is running:")
        print(f"   - Command: python reel_generation_api.py")
        print(f"{'='*80}\n")
        return False
    
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR")
        print(f"   - Error Type: {type(e).__name__}")
        print(f"   - Error Message: {str(e)}")
        print(f"{'='*80}\n")
        return False


def test_health_first():
    """Check if server is running before testing"""
    print(f"\n{'='*80}")
    print("🔍 PRE-TEST: Checking Server Health")
    print(f"{'='*80}")
    
    try:
        print(f"\n📡 Connecting to: {BASE_URL}/api/health")
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"\n✅ Server is RUNNING")
            print(f"   - Status: {health_data.get('status')}")
            print(f"   - Local Storage: {health_data.get('local_storage')}")
            print(f"   - Cloud Bucket: {health_data.get('cloud_bucket')}")
            return True
        else:
            print(f"\n❌ Server returned unexpected status: {response.status_code}")
            return False
    
    except ConnectionError:
        print(f"\n❌ Cannot connect to server")
        print(f"   - Make sure Flask API is running:")
        print(f"   - $ python reel_generation_api.py")
        return False
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False


# ==================== MAIN ====================

def main():
    """Main test runner"""
    print(f"\n\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "   🎬 IMAGE TO VIDEO ENDPOINT - SINGLE ENDPOINT TEST".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    print(f"\n📋 Test Configuration:")
    print(f"   - Server: {BASE_URL}")
    print(f"   - Test Images: {len(TEST_IMAGES)}")
    for i, img in enumerate(TEST_IMAGES, 1):
        print(f"     {i}. {img}")
    
    # Check server health
    if not test_health_first():
        print("\n⛔ Cannot proceed - server is not running")
        return
    
    print("\n" + "="*80)
    print("🚀 STARTING TESTS")
    print("="*80)
    
    # Test 1: Single Image
    test1_result = test_image_to_video_single_endpoint()
    
    print("\n")
    time.sleep(2)  # Brief pause between tests
    
    # Test 2: Multiple Images
    test2_result = test_image_to_video_multiple_endpoint()
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    total_tests = 2
    passed_tests = sum([test1_result, test2_result])
    failed_tests = total_tests - passed_tests
    
    print(f"\n   Total Tests: {total_tests}")
    print(f"   ✅ Passed: {passed_tests}")
    print(f"   ❌ Failed: {failed_tests}")
    
    if total_tests > 0:
        success_rate = (passed_tests / total_tests) * 100
        print(f"   📊 Success Rate: {success_rate:.1f}%")
    
    print(f"\n   Test Details:")
    print(f"   1. Single Image:   {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"   2. Multiple Images: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    print(f"\n{'='*80}")
    print(f"Test execution completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()