"""
Focused Test Suite for Reel Generation API
Tests only the failed and skipped endpoints from the main test suite
Using Cloud Run: https://reels-editor-298842469563.asia-south1.run.app/
"""

import requests
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
import tempfile

# Cloud Run URL
BASE_URL = "https://reels-editor-298842469563.asia-south1.run.app"

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(title: str):
    """Print formatted test header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}{Colors.ENDC}\n")

def print_success(message: str, details: Dict = None):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")
    if details:
        for key, value in details.items():
            if isinstance(value, list):
                print(f"   {key}:")
                for item in value:
                    print(f"     • {item}")
            else:
                print(f"   {key}: {value}")

def print_error(message: str, details: Dict = None):
    """Print error message"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")
    if details:
        for key, value in details.items():
            print(f"   {key}: {value}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")

def make_request(method: str, endpoint: str, data: Dict = None, files: Dict = None, timeout: int = 300, use_form_data: bool = False) -> Dict:
    """Make HTTP request to the API"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, timeout=timeout)
        elif method.upper() == 'POST':
            if files:
                response = requests.post(url, data=data, files=files, timeout=timeout)
            elif use_form_data:
                response = requests.post(url, data=data, timeout=timeout)
            else:
                response = requests.post(url, json=data, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return {
            'success': response.status_code == 200,
            'status_code': response.status_code,
            'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            'headers': dict(response.headers)
        }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request timeout',
            'status_code': 408
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Connection error',
            'status_code': 503
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'status_code': 500
        }

# ==================== FOCUSED TEST CASES ====================

def test_1_generate_ideas():
    """TEST 1: Generate Reel Ideas (Previously Failed)"""
    print_header("TEST 1: Generate Reel Ideas (Retry)")
    
    print_info(f"Testing endpoint: POST {BASE_URL}/api/reel-generation/ideas")
    
    # Test with different prompts to see if it's a specific prompt issue
    test_prompts = [
        'A futuristic tech product launch with excitement and innovation',
        'Create a motivational video about AI and technology',
        'Showcase a new product with dramatic lighting',
        'A simple product demonstration video'
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print_info(f"Attempt {i}: Testing with prompt: '{prompt}'")
        
        data = {'initial_prompt': prompt}
        result = make_request('POST', '/api/reel-generation/ideas', data=data, use_form_data=True)
        
        if result['success']:
            response_data = result['data']
            if response_data.get('success'):
                ideas = response_data.get('ideas', [])
                print_success(f"Attempt {i} - Ideas generated successfully", {
                    "Total Ideas": response_data.get('count'),
                    "Prompt Used": prompt
                })
                
                print("\n📋 Generated Ideas:")
                for idx, idea in enumerate(ideas, 1):
                    word_count = len(idea.split())
                    status = "✓" if word_count <= 30 else "⚠"
                    print(f"   {idx}. [{status} {word_count} words] {idea}")
                
                return True
            else:
                print_error(f"Attempt {i} - API returned error", {"Error": response_data.get('error')})
        else:
            print_error(f"Attempt {i} - Request failed", {
                "Status Code": result['status_code'],
                "Error": result.get('error', result.get('data'))
            })
        
        print(f"{Colors.OKCYAN}{'─'*40}{Colors.ENDC}")
    
    print_error("All attempts failed - Ideas generation endpoint has issues")
    return False

def test_2_generate_ideas_with_image():
    """TEST 2: Generate Ideas with Image Context (Previously Skipped)"""
    print_header("TEST 2: Generate Ideas with Image Context")
    
    print_info(f"Testing endpoint: POST {BASE_URL}/api/reel-generation/ideas (with image)")
    
    # Use the provided image URL
    image_url = "https://storage.googleapis.com/all_in_one_bucket1/Trash/image/images%20(1).jpeg"
    
    # Test with different prompts
    test_prompts = [
        'Create a video showcasing this magical diary',
        'Transform this image into an engaging video',
        'Make a creative video from this magical scene',
        'Show the magic and wonder of this diary'
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print_info(f"Attempt {i}: Testing with prompt: '{prompt}'")
        
        # Send request with JSON format including image URL
        data = {
            'initial_prompt': prompt,
            'image_urls': [image_url]
        }
        
        result = make_request('POST', '/api/reel-generation/ideas', data=data)
        
        if result['success']:
            response_data = result['data']
            if response_data.get('success'):
                ideas = response_data.get('ideas', [])
                print_success(f"Attempt {i} - Ideas with image context generated", {
                    "Total Ideas": response_data.get('count'),
                    "Image URL": image_url,
                    "Prompt": prompt
                })
                
                print("\n📋 Generated Ideas:")
                for idx, idea in enumerate(ideas, 1):
                    word_count = len(idea.split())
                    print(f"   {idx}. [{word_count} words] {idea}")
                
                return True
            else:
                print_error(f"Attempt {i} - API returned error", {"Error": response_data.get('error')})
        else:
            print_error(f"Attempt {i} - Request failed", {
                "Status Code": result['status_code'],
                "Error": result.get('error', result.get('data'))
            })
        
        print(f"{Colors.OKCYAN}{'─'*40}{Colors.ENDC}")
    
    print_error("All attempts failed - Image-based ideas generation has issues")
    return False

def test_3_generate_images_to_video():
    """TEST 3: Generate Images to Video (Single & Multiple Images)"""
    print_header("TEST 3: Generate Images to Video")
    
    print_info(f"Testing endpoint: POST {BASE_URL}/api/generate-video/images")
    print_warning("This test may take several minutes due to video generation...")
    
    # Test with single image first
    print_info("Test 3a: Single image test...")
    image_url = "https://storage.googleapis.com/all_in_one_bucket1/Trash/image/images%20(1).jpeg"
    
    data = {
        'prompt': 'Transform this magical diary into an enchanting video',
        'image_urls': [image_url]
    }
    
    print_info(f"Making request with image URL: {image_url}")
    
    result = make_request('POST', '/api/generate-video/images', data=data, timeout=600)
    
    if result['success']:
        response_data = result['data']
        if response_data.get('success'):
            print_success("Single image-to-video generated successfully", {
                "Message": response_data.get('message'),
                "Video URL": response_data.get('generated_video_url'),
                "Cloud Path": response_data.get('cloud_path'),
                "File Size (MB)": response_data.get('file_size_mb'),
                "Image URL": image_url
            })
        else:
            print_error("Single image API returned error", {"Error": response_data.get('error')})
            return False
    else:
        print_error("Single image request failed", {
            "Status Code": result['status_code'],
            "Error": result.get('error', result.get('data'))
        })
        return False
    
    # Test with multiple images
    print_info("\nTest 3b: Multiple images test...")
    
    # Using multiple image URLs
    image_urls = [
        "https://storage.googleapis.com/all_in_one_bucket1/Trash/image/images%20(1).jpeg",
        "https://storage.googleapis.com/all_in_one_bucket1/Trash/image/images%20(2).jpeg"
    ]
    
    print_success(f"Using {len(image_urls)} image URLs for multiple image test")
    
    data = {
        'prompt': 'Create a magical story video from these images',
        'image_urls': image_urls
    }
    
    try:
        result = make_request('POST', '/api/generate-video/images', data=data, timeout=600)
        
        if result['success']:
            response_data = result['data']
            if response_data.get('success'):
                print_success("Multiple images-to-video generated successfully", {
                    "Message": response_data.get('message'),
                    "Video URL": response_data.get('generated_video_url'),
                    "Cloud Path": response_data.get('cloud_path'),
                    "File Size (MB)": response_data.get('file_size_mb'),
                    "Images Used": len(image_urls)
                })
                return True
            else:
                print_error("Multiple images API returned error", {"Error": response_data.get('error')})
                return False
        else:
            print_error("Multiple images request failed", {
                "Status Code": result['status_code'],
                "Error": result.get('error', result.get('data'))
            })
            return False
            
    except Exception as e:
        print_error(f"Multiple images test failed: {e}")
        return False

def test_3b_specific_two_images_reel():
    """TEST 3b: Generate Reel from Two Specific Images"""
    print_header("TEST 3b: Two Images Reel Generation")
    
    print_info(f"Testing endpoint: POST {BASE_URL}/api/generate-video/images")
    print_warning("This test may take several minutes due to video generation...")
    
    # Using the two specific image URLs
    image_urls = [
        "https://storage.googleapis.com/all_in_one_bucket1/Trash/image/images%20(2).jpeg",
        "https://storage.googleapis.com/all_in_one_bucket1/Trash/image/images%20(1).jpeg"
    ]
    
    data = {
        'prompt': 'Create an engaging transition between these two magical images',
        'image_urls': image_urls
    }
    
    print_info(f"Making request with {len(image_urls)} image URLs")
    
    result = make_request('POST', '/api/generate-video/images', data=data, timeout=600)
    
    if result['success']:
        response_data = result['data']
        if response_data.get('success'):
            print_success("Two images reel generated successfully", {
                "Message": response_data.get('message'),
                "Video URL": response_data.get('generated_video_url'),
                "Cloud Path": response_data.get('cloud_path'),
                "File Size (MB)": response_data.get('file_size_mb'),
                "Images Used": len(image_urls)
            })
            return True
        else:
            print_error("Two images API returned error", {"Error": response_data.get('error')})
            return False
    else:
        print_error("Two images request failed", {
            "Status Code": result['status_code'],
            "Error": result.get('error', result.get('data'))
        })
        return False

def test_4_debug_ideas_endpoint():
    """TEST 4: Debug Ideas Endpoint with Detailed Analysis"""
    print_header("TEST 4: Debug Ideas Endpoint")
    
    print_info(f"Testing endpoint: POST {BASE_URL}/api/reel-generation/ideas")
    print_info("Performing detailed debugging analysis...")
    
    # Test with minimal data
    print_info("Test 4a: Minimal prompt...")
    data = {'initial_prompt': 'test'}
    result = make_request('POST', '/api/reel-generation/ideas', data=data)
    
    print(f"Status Code: {result['status_code']}")
    print(f"Success: {result['success']}")
    print(f"Response Data: {result.get('data')}")
    print(f"Error: {result.get('error')}")
    
    # Test with empty data
    print_info("\nTest 4b: Empty data...")
    result = make_request('POST', '/api/reel-generation/ideas', data={})
    
    print(f"Status Code: {result['status_code']}")
    print(f"Success: {result['success']}")
    print(f"Response Data: {result.get('data')}")
    print(f"Error: {result.get('error')}")
    
    # Test with different content types
    print_info("\nTest 4c: Different content type...")
    try:
        url = f"{BASE_URL}/api/reel-generation/ideas"
        response = requests.post(url, data={'initial_prompt': 'test prompt'}, 
                               headers={'Content-Type': 'application/x-www-form-urlencoded'}, 
                               timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"Error: {e}")
    
    return True

# ==================== TEST SUITE RUNNER ====================

def run_focused_tests():
    """Run focused test suite for failed/skipped endpoints"""
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 80)
    print("  🎬 REEL GENERATION API - FOCUSED TEST SUITE")
    print("  🔍 Testing Previously Failed/Skipped Endpoints")
    print(f"  🌐 Testing Cloud Run: {BASE_URL}")
    print("=" * 80)
    print(f"{Colors.ENDC}")
    
    start_time = time.time()
    test_results = {}
    
    # Run focused tests
    tests = [
        ("Generate Ideas (Retry)", test_1_generate_ideas),
        ("Generate Ideas with Image", test_2_generate_ideas_with_image),
        ("Generate Images to Video", test_3_generate_images_to_video),
        ("Debug Ideas Endpoint", test_4_debug_ideas_endpoint),
    ]
    
    for test_name, test_func in tests:
        try:
            print_info(f"Running: {test_name}")
            result = test_func()
            test_results[test_name] = result
            print(f"{Colors.OKCYAN}{'─'*60}{Colors.ENDC}")
        except Exception as e:
            print_error(f"Test crashed: {str(e)}")
            test_results[test_name] = False
            print(f"{Colors.OKCYAN}{'─'*60}{Colors.ENDC}")
    
    # Print summary
    end_time = time.time()
    duration = end_time - start_time
    
    print_header("FOCUSED TEST SUMMARY")
    
    passed = sum(1 for v in test_results.values() if v is True)
    failed = sum(1 for v in test_results.values() if v is False)
    skipped = sum(1 for v in test_results.values() if v is None)
    
    print(f"{Colors.BOLD}Results:{Colors.ENDC}")
    for test_name, result in test_results.items():
        if result is True:
            status = f"{Colors.OKGREEN}PASSED{Colors.ENDC}"
        elif result is False:
            status = f"{Colors.FAIL}FAILED{Colors.ENDC}"
        else:
            status = f"{Colors.WARNING}SKIPPED{Colors.ENDC}"
        
        print(f"  {status} - {test_name}")
    
    print(f"\n{Colors.BOLD}Summary:{Colors.ENDC}")
    print(f"  Total Tests: {len(tests)}")
    print(f"  {Colors.OKGREEN}Passed: {passed}{Colors.ENDC}")
    print(f"  {Colors.FAIL}Failed: {failed}{Colors.ENDC}")
    print(f"  {Colors.WARNING}Skipped: {skipped}{Colors.ENDC}")
    print(f"  Duration: {duration:.2f}s")
    print(f"  Base URL: {BASE_URL}")
    
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    return passed, failed, skipped

if __name__ == "__main__":
    print("\n🚀 Starting Focused API Test Suite...\n")
    print(f"🌐 Testing Cloud Run: {BASE_URL}")
    print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📸 Using image: edited_diary_magical.png")
    print()
    
    passed, failed, skipped = run_focused_tests()
    
    # Exit with appropriate code
    exit_code = 0 if failed == 0 else 1
    print(f"🏁 Focused test suite completed with exit code: {exit_code}")
    
    exit(exit_code)
