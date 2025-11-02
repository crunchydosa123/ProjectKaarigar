#!/usr/bin/env python3
"""
Reel Generation API Test Script
Tests all scenarios with short durations and limited segments
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api/reel"

# Test images (using Picsum for reliable public images)
TEST_IMAGES = [
    "https://picsum.photos/800/600?random=1",
    "https://picsum.photos/800/600?random=2", 
    "https://picsum.photos/800/600?random=3",
    "https://picsum.photos/800/600?random=4",
    "https://picsum.photos/800/600?random=5"
]

# Session for maintaining cookies
session = requests.Session()

def log(message, level="INFO"):
    """Log with timestamp and level"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def make_request(method, endpoint, data=None, expected_status=200):
    """Make HTTP request with error handling"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        log(f"Making {method} request to {endpoint}")
        if data:
            log(f"Request data: {json.dumps(data, indent=2)}")
        
        if method.upper() == "GET":
            response = session.get(url)
        elif method.upper() == "POST":
            response = session.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        log(f"Response status: {response.status_code}")
        
        if response.status_code != expected_status:
            log(f"❌ Expected status {expected_status}, got {response.status_code}", "ERROR")
            log(f"Response: {response.text}", "ERROR")
            return None
        
        try:
            response_data = response.json()
            log(f"✅ Response: {json.dumps(response_data, indent=2)}")
            return response_data
        except json.JSONDecodeError:
            log(f"Response text: {response.text}")
            return {"text": response.text}
            
    except Exception as e:
        log(f"❌ Request failed: {str(e)}", "ERROR")
        return None

def test_health_check():
    """Test health check endpoint"""
    log("=" * 60)
    log("🏥 TESTING HEALTH CHECK")
    log("=" * 60)
    
    result = make_request("GET", "/health")
    if result:
        log("✅ Health check passed")
    else:
        log("❌ Health check failed")
    return result is not None

def test_text_to_video():
    """Test text-to-video generation (no images)"""
    log("=" * 60)
    log("📝 TESTING TEXT-TO-VIDEO")
    log("=" * 60)
    
    # Test 1: Basic text-to-video
    log("Test 1: Basic text-to-video")
    data1 = {
        "prompt": "A quick cinematic video about a sunset",
        "title": "Sunset Video",
        "image_urls": []
    }
    result1 = make_request("POST", "/generate-reel", data1)
    
    # Test 2: Text-to-video with custom settings
    log("Test 2: Text-to-video with custom settings")
    data2 = {
        "prompt": "A professional intro video",
        "title": "Intro Video",
        "image_urls": [],
        "duration": 3,
        "segments": 1
    }
    result2 = make_request("POST", "/generate-reel", data2)
    
    return result1 is not None and result2 is not None

def test_single_image():
    """Test single image to video"""
    log("=" * 60)
    log("🖼️ TESTING SINGLE IMAGE TO VIDEO")
    log("=" * 60)
    
    # Test 1: Single image with auto settings
    log("Test 1: Single image with auto settings")
    data1 = {
        "prompt": "Create a dynamic video with zoom effects",
        "title": "Single Image Auto",
        "image_urls": [TEST_IMAGES[0]]
    }
    result1 = make_request("POST", "/generate-reel", data1)
    
    # Test 2: Single image with custom settings
    log("Test 2: Single image with custom settings")
    data2 = {
        "prompt": "Create a professional product video",
        "title": "Single Image Custom",
        "image_urls": [TEST_IMAGES[1]],
        "duration": 4,
        "segments": 2
    }
    result2 = make_request("POST", "/generate-reel", data2)
    
    return result1 is not None and result2 is not None

def test_multiple_images():
    """Test multiple images to video"""
    log("=" * 60)
    log("🖼️🖼️ TESTING MULTIPLE IMAGES TO VIDEO")
    log("=" * 60)
    
    # Test 1: Two images with auto settings
    log("Test 1: Two images with auto settings")
    data1 = {
        "prompt": "Create a slideshow with smooth transitions",
        "title": "Two Images Auto",
        "image_urls": TEST_IMAGES[:2]
    }
    result1 = make_request("POST", "/generate-reel", data1)
    
    # Test 2: Three images with custom settings
    log("Test 2: Three images with custom settings")
    data2 = {
        "prompt": "Create a fast montage with quick cuts",
        "title": "Three Images Custom",
        "image_urls": TEST_IMAGES[:3],
        "duration": 6,
        "segments": 2
    }
    result2 = make_request("POST", "/generate-reel", data2)
    
    # Test 3: Many images with custom settings
    log("Test 3: Many images with custom settings")
    data3 = {
        "prompt": "Create a portfolio showcase",
        "title": "Portfolio Showcase",
        "image_urls": TEST_IMAGES,
        "duration": 8,
        "segments": 2
    }
    result3 = make_request("POST", "/generate-reel", data3)
    
    return result1 is not None and result2 is not None and result3 is not None

def test_edge_cases():
    """Test edge cases and error scenarios"""
    log("=" * 60)
    log("⚠️ TESTING EDGE CASES")
    log("=" * 60)
    
    # Test 1: Very short duration
    log("Test 1: Very short duration (2 seconds)")
    data1 = {
        "prompt": "A very quick video",
        "title": "Quick Video",
        "image_urls": [],
        "duration": 2,
        "segments": 1
    }
    result1 = make_request("POST", "/generate-reel", data1)
    
    # Test 2: Single segment with multiple images
    log("Test 2: Single segment with multiple images")
    data2 = {
        "prompt": "Create a single segment montage",
        "title": "Single Segment Montage",
        "image_urls": TEST_IMAGES[:3],
        "duration": 5,
        "segments": 1
    }
    result2 = make_request("POST", "/generate-reel", data2)
    
    # Test 3: Maximum segments (2) with single image
    log("Test 3: Maximum segments (2) with single image")
    data3 = {
        "prompt": "Create a dynamic single image video",
        "title": "Max Segments Single Image",
        "image_urls": [TEST_IMAGES[0]],
        "duration": 6,
        "segments": 2
    }
    result3 = make_request("POST", "/generate-reel", data3)
    
    return result1 is not None and result2 is not None and result3 is not None

def test_get_reels():
    """Test getting generated reels"""
    log("=" * 60)
    log("📋 TESTING GET GENERATED REELS")
    log("=" * 60)
    
    result = make_request("GET", "/get-generated-reels")
    if result and result.get("success"):
        reels = result.get("reels", [])
        log(f"✅ Retrieved {len(reels)} generated reels")
        for i, reel in enumerate(reels[:3]):  # Show first 3 reels
            log(f"  Reel {i+1}: {reel.get('title', 'No title')} - {reel.get('generation_type', 'Unknown type')}")
        return True
    else:
        log("❌ Failed to retrieve reels")
        return False

def test_error_scenarios():
    """Test error scenarios"""
    log("=" * 60)
    log("❌ TESTING ERROR SCENARIOS")
    log("=" * 60)
    
    # Test 1: Missing prompt
    log("Test 1: Missing prompt")
    data1 = {
        "title": "No Prompt Test",
        "image_urls": []
    }
    result1 = make_request("POST", "/generate-reel", data1, expected_status=400)
    
    # Test 2: Missing title
    log("Test 2: Missing title")
    data2 = {
        "prompt": "Test prompt",
        "image_urls": []
    }
    result2 = make_request("POST", "/generate-reel", data2, expected_status=400)
    
    # Test 3: Invalid image URL
    log("Test 3: Invalid image URL")
    data3 = {
        "prompt": "Test with invalid image",
        "title": "Invalid Image Test",
        "image_urls": ["https://invalid-url-that-does-not-exist.com/image.jpg"]
    }
    result3 = make_request("POST", "/generate-reel", data3)
    
    return True  # Error tests are expected to fail

def run_all_tests():
    """Run all test scenarios"""
    log("🚀 STARTING REEL GENERATION API TESTS")
    log("=" * 80)
    
    start_time = time.time()
    test_results = []
    
    # Run all tests
    tests = [
        ("Health Check", test_health_check),
        ("Text-to-Video", test_text_to_video),
        ("Single Image", test_single_image),
        ("Multiple Images", test_multiple_images),
        ("Edge Cases", test_edge_cases),
        ("Get Reels", test_get_reels),
        ("Error Scenarios", test_error_scenarios)
    ]
    
    for test_name, test_func in tests:
        log(f"\n🧪 Running {test_name} tests...")
        try:
            result = test_func()
            test_results.append((test_name, result))
            if result:
                log(f"✅ {test_name} tests PASSED")
            else:
                log(f"❌ {test_name} tests FAILED")
        except Exception as e:
            log(f"❌ {test_name} tests ERROR: {str(e)}", "ERROR")
            test_results.append((test_name, False))
        
        # Small delay between test groups
        time.sleep(1)
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    log("\n" + "=" * 80)
    log("📊 TEST SUMMARY")
    log("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        log(f"{status} {test_name}")
    
    log(f"\n📈 Results: {passed}/{total} test groups passed")
    log(f"⏱️ Total time: {duration:.1f} seconds")
    
    if passed == total:
        log("🎉 ALL TESTS PASSED!")
    else:
        log(f"⚠️ {total - passed} test groups failed")
    
    return passed == total

if __name__ == "__main__":
    log("🎬 Reel Generation API Test Suite")
    log("=" * 50)
    log("Configuration:")
    log(f"  Base URL: {BASE_URL}")
    log(f"  API Base: {API_BASE}")
    log(f"  Test Images: {len(TEST_IMAGES)}")
    log("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        log("✅ Server is running")
    except requests.exceptions.RequestException:
        log("❌ Server is not running. Please start the Flask server first.", "ERROR")
        sys.exit(1)
    
    # Run tests
    success = run_all_tests()
    sys.exit(0 if success else 1)
