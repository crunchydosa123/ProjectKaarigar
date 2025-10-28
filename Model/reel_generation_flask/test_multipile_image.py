"""
Separate Test Suite for Images to Video Route
Tests /api/generate-video/images with single and multiple images
"""

import requests
import json
from datetime import datetime


# Configuration
BASE_URL = "http://localhost:5000"


class Colors:
    """ANSI color codes"""
    HEADER = '\033[95m'
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_test(name: str):
    """Print test header"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}")
    print(f"  {name}")
    print(f"{'='*80}{Colors.ENDC}\n")


def print_pass(message: str):
    """Print success"""
    print(f"{Colors.OKGREEN}✅ PASS: {message}{Colors.ENDC}")


def print_fail(message: str):
    """Print failure"""
    print(f"{Colors.FAIL}❌ FAIL: {message}{Colors.ENDC}")


def print_response(response: requests.Response):
    """Print response details"""
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text[:500]}")


# ==================== TESTS ====================

def test_single_image_to_video():
    """Test /api/generate-video/images with single image URL"""
    print_test("TEST 1: Single Image to Video")
    
    payload = {
        "image_urls": [
            "https://storage.googleapis.com/all_in_one_bucket/Trash/image/images%20(1).jpeg"
        ],
        "prompt": "Transform this image into a cinematic video with smooth transitions"
    }
    
    try:
        print(f"📤 Sending request to {BASE_URL}/api/generate-video/images")
        print(f"📸 Image count: {len(payload['image_urls'])}")
        print(f"💬 Prompt: {payload['prompt']}")
        
        response = requests.post(
            f"{BASE_URL}/api/generate-video/images",
            json=payload,
            timeout=300  # 5 minutes timeout for video generation
        )
        
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('generated_video_url'):
                print_pass(f"✅ Single image video generated successfully!")
                print(f"🎥 Video URL: {data.get('generated_video_url')}")
                print(f"☁️  Cloud Path: {data.get('cloud_path')}")
                print(f"📦 File Size: {data.get('file_size_mb')} MB")
                
                # Save response to JSON
                with open('single_image_video_response.json', 'w') as f:
                    json.dump(data, f, indent=4)
                print(f"💾 Response saved to single_image_video_response.json")
                
                return True
            else:
                print_fail("❌ No video URL in response")
                return False
        else:
            print_fail(f"❌ Expected 200, got {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print_fail("❌ Request timeout (video generation took too long)")
        return False
    except Exception as e:
        print_fail(f"❌ Request failed: {str(e)}")
        return False


def test_multiple_images_to_video():
    """Test /api/generate-video/images with multiple image URLs"""
    print_test("TEST 2: Multiple Images to Video")
    
    payload = {
        "image_urls": [
            "https://storage.googleapis.com/all_in_one_bucket/Trash/image/images%20(1).jpeg",
            "https://storage.googleapis.com/all_in_one_bucket/Trash/image/images%20(2).jpeg"
        ],
        "prompt": "Create a dynamic product showcase with these images"
    }
    
    try:
        print(f"📤 Sending request to {BASE_URL}/api/generate-video/images")
        print(f"📸 Image count: {len(payload['image_urls'])}")
        for idx, url in enumerate(payload['image_urls'], 1):
            print(f"   Image {idx}: {url}")
        print(f"💬 Prompt: {payload['prompt']}")
        
        response = requests.post(
            f"{BASE_URL}/api/generate-video/images",
            json=payload,
            timeout=300  # 5 minutes timeout for video generation
        )
        
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('generated_video_url'):
                print_pass(f"✅ Multiple images video generated successfully!")
                print(f"🎥 Video URL: {data.get('generated_video_url')}")
                print(f"☁️  Cloud Path: {data.get('cloud_path')}")
                print(f"📦 File Size: {data.get('file_size_mb')} MB")
                
                # Save response to JSON
                with open('multiple_images_video_response.json', 'w') as f:
                    json.dump(data, f, indent=4)
                print(f"💾 Response saved to multiple_images_video_response.json")
                
                return True
            else:
                print_fail("❌ No video URL in response")
                return False
        else:
            print_fail(f"❌ Expected 200, got {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print_fail("❌ Request timeout (video generation took too long)")
        return False
    except Exception as e:
        print_fail(f"❌ Request failed: {str(e)}")
        return False


def test_images_to_video_error_cases():
    """Test error handling for /api/generate-video/images"""
    print_test("TEST 3: Error Cases for Images to Video")
    
    test_cases = [
        {
            "name": "Empty image_urls array",
            "payload": {
                "image_urls": [],
                "prompt": "Test prompt"
            },
            "expected_status": 400
        },
        {
            "name": "Missing image_urls field",
            "payload": {
                "prompt": "Test prompt"
            },
            "expected_status": 400
        },
        {
            "name": "Missing prompt field",
            "payload": {
                "image_urls": ["https://storage.googleapis.com/all_in_one_bucket/Trash/image/images%20(1).jpeg"]
            },
            "expected_status": 400
        },
        {
            "name": "Invalid image URL",
            "payload": {
                "image_urls": ["not_a_valid_url"],
                "prompt": "Test prompt"
            },
            "expected_status": 400
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/generate-video/images",
                json=test_case['payload'],
                timeout=30
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == test_case['expected_status']:
                print_pass(f"✅ {test_case['name']} - Correct error status")
            else:
                print_fail(f"❌ {test_case['name']} - Expected {test_case['expected_status']}, got {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print_fail(f"❌ {test_case['name']} - Request failed: {str(e)}")
            all_passed = False
    
    return all_passed


# ==================== RUN ALL TESTS ====================

def run_all_tests():
    """Execute all image-to-video tests"""
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 80)
    print("  🎬 IMAGES TO VIDEO - DETAILED TEST SUITE")
    print(f"  Server: {BASE_URL}")
    print("=" * 80)
    print(f"{Colors.ENDC}")
    
    tests = [
        ("Single Image to Video", test_single_image_to_video),
        ("Multiple Images to Video", test_multiple_images_to_video),
        ("Error Cases", test_images_to_video_error_cases),
    ]
    
    results = {}
    start_time = datetime.now()
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_fail(f"Test crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}")
    print("  TEST SUMMARY")
    print(f"{'='*80}{Colors.ENDC}\n")
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    
    for test_name, result in results.items():
        status = f"{Colors.OKGREEN}PASS{Colors.ENDC}" if result else f"{Colors.FAIL}FAIL{Colors.ENDC}"
        print(f"  {status} - {test_name}")
    
    print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
    print(f"  Total Tests: {len(tests)}")
    print(f"  {Colors.OKGREEN}Passed: {passed}{Colors.ENDC}")
    print(f"  {Colors.FAIL}Failed: {failed}{Colors.ENDC}")
    print(f"  Duration: {duration:.2f}s")
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    return passed, failed


if __name__ == "__main__":
    print("\n🚀 Starting Images to Video Tests...\n")
    print(f"{Colors.WARNING}⚠️  Make sure Flask server is running at {BASE_URL}{Colors.ENDC}")
    print(f"{Colors.WARNING}⚠️  Video generation may take several minutes per test{Colors.ENDC}\n")
    
    passed, failed = run_all_tests()
    
    exit(0 if failed == 0 else 1)