"""
Comprehensive Test Suite for Reel Generation API
Tests all endpoints deployed on Cloud Run: https://reels-editor-298842469563.asia-south1.run.app/
"""

import requests
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
import tempfile

# Cloud Run URL
BASE_URL = "https://reels-editor-557742533869.asia-south1.run.app"

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

def make_request(
    method: str,
    endpoint: str,
    data: Dict = None,
    files: Dict = None,
    timeout: int = 300,
    use_form_data: bool = False,
    json_mode: bool = False
) -> Dict:
    """Make HTTP request to the API"""
    url = f"{BASE_URL}{endpoint}"

    try:
        if method.upper() == 'GET':
            response = requests.get(url, timeout=timeout)
        elif method.upper() == 'POST':
            if files:
                # For multipart form-data file uploads
                response = requests.post(url, data=data, files=files, timeout=timeout)
            elif use_form_data:
                # For normal form-data (application/x-www-form-urlencoded)
                response = requests.post(url, data=data, timeout=timeout)
            elif json_mode:
                # For application/json requests (like image_urls API)
                response = requests.post(url, json=data, timeout=timeout)
            else:
                # Default to JSON if not specified
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
        return {'success': False, 'error': 'Request timeout', 'status_code': 408}
    except requests.exceptions.ConnectionError:
        return {'success': False, 'error': 'Connection error', 'status_code': 503}
    except Exception as e:
        return {'success': False, 'error': str(e), 'status_code': 500}

# ==================== TEST CASES ====================

def test_1_health_check():
    """TEST 1: Health Check Endpoint"""
    print_header("TEST 1: Health Check")
    
    print_info(f"Testing endpoint: GET {BASE_URL}/api/health")
    
    result = make_request('GET', '/api/health')
    
    if result['success']:
        data = result['data']
        print_success("Health check passed", {
            "Status": data.get('status'),
            "Local Storage": data.get('local_storage'),
            "Cloud Bucket": data.get('cloud_bucket'),
            "Brand ID": data.get('brand_id')
        })
        return True
    else:
        print_error("Health check failed", {
            "Status Code": result['status_code'],
            "Error": result.get('error', result.get('data'))
        })
        return False

def test_2_generate_ideas():
    """TEST 2: Generate Reel Ideas"""
    print_header("TEST 2: Generate Reel Ideas")
    
    print_info(f"Testing endpoint: POST {BASE_URL}/api/reel-generation/ideas")
    
    # Test with text only
    data = {
        'initial_prompt': 'A futuristic tech product launch with excitement and innovation'
    }
    
    result = make_request('POST', '/api/reel-generation/ideas', data=data, use_form_data=True)
    
    if result['success']:
        response_data = result['data']
        if response_data.get('success'):
            ideas = response_data.get('ideas', [])
            print_success("Ideas generated successfully", {
                "Total Ideas": response_data.get('count'),
                "Ideas": ideas
            })
            
            print("\n📋 Generated Ideas:")
            for idx, idea in enumerate(ideas, 1):
                word_count = len(idea.split())
                status = "✓" if word_count <= 30 else "⚠"
                print(f"   {idx}. [{status} {word_count} words] {idea}")
            
            return True
        else:
            print_error("API returned error", {"Error": response_data.get('error')})
            return False
    else:
        print_error("Request failed", {
            "Status Code": result['status_code'],
            "Error": result.get('error', result.get('data'))
        })
        return False

def test_3_generate_ideas_with_image():
    """TEST 3: Generate Ideas with Image URL Context"""
    print_header("TEST 3: Generate Ideas with Image URL")

    print_info(f"Testing endpoint: POST {BASE_URL}/api/reel-generation/ideas (with image_url)")

    # Example image URL (replace or extend this list as needed)
    image_url = "https://storage.googleapis.com/all_in_one_bucket/Trash/image/images%20(1).jpeg"

    data = {
        'initial_prompt': 'Create a video showcasing this magical diary',
        'image_url': image_url
    }

    print_info(f"Making request with image URL: {image_url}")

    result = make_request('POST', '/api/reel-generation/ideas', data=data, timeout=300)

    if result['success']:
        response_data = result['data']
        if response_data.get('success'):
            ideas = response_data.get('ideas', [])
            print_success("Ideas with image URL context generated successfully", {
                "Total Ideas": response_data.get('count'),
                "Ideas": ideas
            })
            return True
        else:
            print_error("API returned error", {"Error": response_data.get('error')})
            return False
    else:
        print_error("Request failed", {
            "Status Code": result['status_code'],
            "Error": result.get('error', result.get('data'))
        })
        return False

def test_4_refine_idea():
    """TEST 4: Refine Idea"""
    print_header("TEST 4: Refine Idea")
    
    print_info(f"Testing endpoint: POST {BASE_URL}/api/reel-generation/refine-idea")
    
    data = {
        'chosen_idea': 'A futuristic tech product launch with excitement and innovation',
        'refinement_prompt': 'Make it more dramatic and cinematic with dramatic lighting and slow motion effects'
    }
    
    result = make_request('POST', '/api/reel-generation/refine-idea', data=data)
    
    if result['success']:
        response_data = result['data']
        if response_data.get('success'):
            print_success("Idea refined successfully", {
                "Original Idea": response_data.get('original_idea'),
                "Refined Idea": response_data.get('refined_idea'),
                "Word Count": response_data.get('word_count')
            })
            return True
        else:
            print_error("API returned error", {"Error": response_data.get('error')})
            return False
    else:
        print_error("Request failed", {
            "Status Code": result['status_code'],
            "Error": result.get('error', result.get('data'))
        })
        return False

def test_5_regenerate_ideas():
    """TEST 5: Regenerate Ideas"""
    print_header("TEST 5: Regenerate Ideas")
    
    print_info(f"Testing endpoint: POST {BASE_URL}/api/reel-generation/regenerate-ideas")
    
    data = {
        'regeneration_prompt': 'Generate tech-focused content ideas with innovation and futuristic elements'
    }
    
    result = make_request('POST', '/api/reel-generation/regenerate-ideas', data=data)
    
    if result['success']:
        response_data = result['data']
        if response_data.get('success'):
            ideas = response_data.get('ideas', [])
            print_success("Ideas regenerated successfully", {
                "Total Ideas": response_data.get('count'),
                "Ideas": ideas
            })
            return True
        else:
            print_error("API returned error", {"Error": response_data.get('error')})
            return False
    else:
        print_error("Request failed", {
            "Status Code": result['status_code'],
            "Error": result.get('error', result.get('data'))
        })
        return False

def test_6_generate_video_script():
    """TEST 6: Generate Video Script"""
    print_header("TEST 6: Generate Video Script")
    
    print_info(f"Testing endpoint: POST {BASE_URL}/api/reel-generation/generate-video-script")
    
    data = {
        'reel_idea': 'A futuristic tech product launch with excitement and innovation'
    }
    
    result = make_request('POST', '/api/reel-generation/generate-video-script', data=data)
    
    if result['success']:
        response_data = result['data']
        if response_data.get('success'):
            print_success("Video script generated", {
                "Original Idea": response_data.get('reel_idea'),
                "Word Count": response_data.get('word_count'),
                "Script Preview": response_data.get('script', '')[:100] + "..." if len(response_data.get('script', '')) > 100 else response_data.get('script', '')
            })
            return True
        else:
            print_error("API returned error", {"Error": response_data.get('error')})
            return False
    else:
        print_error("Request failed", {
            "Status Code": result['status_code'],
            "Error": result.get('error', result.get('data'))
        })
        return False

def test_7_generate_video_from_script():
    """TEST 7: Generate Video from Script"""
    print_header("TEST 7: Generate Video from Script")
    
    print_info(f"Testing endpoint: POST {BASE_URL}/api/reel-generation/generate-video")
    print_warning("This test may take several minutes due to video generation...")
    
    data = {
        'script': 'A futuristic tech product launch with excitement and innovation. Show dramatic lighting, slow motion effects, and cinematic camera movements.'
    }
    
    result = make_request('POST', '/api/reel-generation/generate-video', data=data, timeout=600)
    
    if result['success']:
        response_data = result['data']
        if response_data.get('success'):
            print_success("Video generated successfully", {
                "Message": response_data.get('message'),
                "Video URL": response_data.get('generated_video_url'),
                "Cloud Path": response_data.get('cloud_path'),
                "File Size (MB)": response_data.get('file_size_mb')
            })
            return True
        else:
            print_error("API returned error", {"Error": response_data.get('error')})
            return False
    else:
        print_error("Request failed", {
            "Status Code": result['status_code'],
            "Error": result.get('error', result.get('data'))
        })
        return False

def test_8_generate_text_to_video():
    """TEST 8: Generate Text to Video"""
    print_header("TEST 8: Generate Text to Video")
    
    print_info(f"Testing endpoint: POST {BASE_URL}/api/generate-video/text")
    print_warning("This test may take several minutes due to video generation...")
    
    data = {
        'prompt': 'Create a motivational AI-themed short video with a futuristic tone'
    }
    
    result = make_request('POST', '/api/generate-video/text', data=data, timeout=600)
    
    if result['success']:
        response_data = result['data']
        if response_data.get('success'):
            print_success("Text-to-video generated successfully", {
                "Message": response_data.get('message'),
                "Video URL": response_data.get('generated_video_url'),
                "Cloud Path": response_data.get('cloud_path'),
                "File Size (MB)": response_data.get('file_size_mb')
            })
            return True
        else:
            print_error("API returned error", {"Error": response_data.get('error')})
            return False
    else:
        print_error("Request failed", {
            "Status Code": result['status_code'],
            "Error": result.get('error', result.get('data'))
        })
        return False

def test_9_generate_images_to_video():
    """TEST 9: Generate Images to Video (Using Image URLs)"""
    print_header("TEST 9: Generate Images to Video (Image URLs)")

    print_info(f"Testing endpoint: POST {BASE_URL}/api/generate-video/images")
    print_warning("This test may take several minutes due to video generation...")

    # Test 9a: Single image URL
    print_info("Test 9a: Single image URL test...")

    single_image_url = "https://storage.googleapis.com/all_in_one_bucket/Trash/image/images%20(1).jpeg"

    data = {
        "prompt": "Transform this magical diary into an enchanting video",
        "image_urls": [single_image_url]
    }

    print_info(f"Making request with 1 image URL: {single_image_url}")

    result = make_request('POST', '/api/generate-video/images', data=data, timeout=600, json_mode=True)

    if result['success']:
        response_data = result['data']
        if response_data.get('success'):
            print_success("Single image-to-video generated successfully", {
                "Message": response_data.get('message'),
                "Video URL": response_data.get('generated_video_url'),
                "Cloud Path": response_data.get('cloud_path'),
                "File Size (MB)": response_data.get('file_size_mb'),
                "Images Used": 1
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

    # Test 9b: Multiple image URLs
    print_info("\nTest 9b: Multiple image URLs test...")

    multiple_image_urls = [
        "https://storage.googleapis.com/all_in_one_bucket/Trash/image/images%20(1).jpeg",
        "https://storage.googleapis.com/all_in_one_bucket/Trash/image/images%20(2).jpeg"
    ]

    data = {
        "prompt": "Create a magical story video from these images",
        "image_urls": multiple_image_urls
    }

    print_success(f"Using {len(multiple_image_urls)} image URLs for multiple image test")

    result = make_request('POST', '/api/generate-video/images', data=data, timeout=600, json_mode=True)

    if result['success']:
        response_data = result['data']
        if response_data.get('success'):
            print_success("Multiple images-to-video generated successfully", {
                "Message": response_data.get('message'),
                "Video URL": response_data.get('generated_video_url'),
                "Cloud Path": response_data.get('cloud_path'),
                "File Size (MB)": response_data.get('file_size_mb'),
                "Images Used": len(multiple_image_urls)
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

def test_10_list_videos():
    """TEST 10: List Videos"""
    print_header("TEST 10: List Videos")
    
    print_info(f"Testing endpoint: GET {BASE_URL}/api/videos")
    
    result = make_request('GET', '/api/videos')
    
    if result['success']:
        response_data = result['data']
        if response_data.get('success'):
            local_videos = response_data.get('local', {}).get('videos', [])
            cloud_videos = response_data.get('cloud', {}).get('videos', []) if isinstance(response_data.get('cloud'), dict) else []
            
            print_success("Videos listed successfully", {
                "Local Videos": len(local_videos),
                "Cloud Videos": len(cloud_videos),
                "Total Videos": response_data.get('total_all')
            })
            
            if local_videos:
                print("\n📁 Local Videos:")
                for video in local_videos[:3]:  # Show first 3
                    print(f"   • {video.get('name')} ({video.get('size_mb')} MB)")
            
            if cloud_videos:
                print("\n☁️ Cloud Videos:")
                for video in cloud_videos[:3]:  # Show first 3
                    print(f"   • {video.get('name')}")
            
            return True
        else:
            print_error("API returned error", {"Error": response_data.get('error')})
            return False
    else:
        print_error("Request failed", {
            "Status Code": result['status_code'],
            "Error": result.get('error', result.get('data'))
        })
        return False

def test_11_list_cloud_videos():
    """TEST 11: List Cloud Videos Only"""
    print_header("TEST 11: List Cloud Videos")
    
    print_info(f"Testing endpoint: GET {BASE_URL}/api/cloud-videos")
    
    result = make_request('GET', '/api/cloud-videos')
    
    if result['success']:
        response_data = result['data']
        if response_data.get('success'):
            videos = response_data.get('videos', [])
            print_success("Cloud videos listed successfully", {
                "Total Cloud Videos": len(videos)
            })
            
            if videos:
                print("\n☁️ Cloud Videos:")
                for video in videos[:5]:  # Show first 5
                    print(f"   • {video.get('name')}")
            
            return True
        else:
            print_error("API returned error", {"Error": response_data.get('error')})
            return False
    else:
        print_error("Request failed", {
            "Status Code": result['status_code'],
            "Error": result.get('error', result.get('data'))
        })
        return False

def test_12_error_handling():
    """TEST 12: Error Handling"""
    print_header("TEST 12: Error Handling")
    
    test_passed = True
    
    # Test 12a: Empty prompt for ideas
    print_info("Test 12a: Empty prompt for ideas...")
    result = make_request('POST', '/api/reel-generation/ideas', data={'initial_prompt': ''})
    
    if not result['success'] or (result['success'] and not result['data'].get('success')):
        print_success("Empty prompt correctly rejected")
    else:
        print_error("Empty prompt should be rejected")
        test_passed = False
    
    # Test 12b: Missing required fields
    print_info("\nTest 12b: Missing required fields...")
    result = make_request('POST', '/api/reel-generation/refine-idea', data={})
    
    if not result['success'] or (result['success'] and not result['data'].get('success')):
        print_success("Missing fields correctly rejected")
    else:
        print_error("Missing fields should be rejected")
        test_passed = False
    
    # Test 12c: Invalid endpoint
    print_info("\nTest 12c: Invalid endpoint...")
    result = make_request('GET', '/api/invalid-endpoint')
    
    if not result['success']:
        print_success("Invalid endpoint correctly rejected")
    else:
        print_error("Invalid endpoint should be rejected")
        test_passed = False
    
    return test_passed

def test_13_debug_ideas_endpoint():
    """TEST 13: Debug Ideas Endpoint with Detailed Analysis"""
    print_header("TEST 13: Debug Ideas Endpoint")
    
    print_info(f"Testing endpoint: POST {BASE_URL}/api/reel-generation/ideas")
    print_info("Performing detailed debugging analysis...")
    
    # Test with minimal data
    print_info("Test 13a: Minimal prompt...")
    data = {'initial_prompt': 'test'}
    result = make_request('POST', '/api/reel-generation/ideas', data=data)
    
    print(f"Status Code: {result['status_code']}")
    print(f"Success: {result['success']}")
    print(f"Response Data: {result.get('data')}")
    print(f"Error: {result.get('error')}")
    
    # Test with empty data
    print_info("\nTest 13b: Empty data...")
    result = make_request('POST', '/api/reel-generation/ideas', data={})
    
    print(f"Status Code: {result['status_code']}")
    print(f"Success: {result['success']}")
    print(f"Response Data: {result.get('data')}")
    print(f"Error: {result.get('error')}")
    
    # Test with different content types
    print_info("\nTest 13c: Different content type...")
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

def run_all_tests():
    """Run complete test suite"""
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 80)
    print("  🎬 REEL GENERATION API - COMPREHENSIVE TEST SUITE")
    print(f"  🌐 Testing Cloud Run: {BASE_URL}")
    print("=" * 80)
    print(f"{Colors.ENDC}")
    
    start_time = time.time()
    test_results = {}
    
    # Run all tests
    tests = [
        ("Health Check", test_1_health_check),
        ("Generate Ideas", test_2_generate_ideas),
        ("Generate Ideas with Image", test_3_generate_ideas_with_image),
        ("Refine Idea", test_4_refine_idea),
        ("Regenerate Ideas", test_5_regenerate_ideas),
        ("Generate Video Script", test_6_generate_video_script),
        ("Generate Video from Script", test_7_generate_video_from_script),
        ("Generate Text to Video", test_8_generate_text_to_video),
        ("Generate Images to Video", test_9_generate_images_to_video),
        ("List Videos", test_10_list_videos),
        ("List Cloud Videos", test_11_list_cloud_videos),
        ("Error Handling", test_12_error_handling),
        ("Debug Ideas Endpoint", test_13_debug_ideas_endpoint),
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
    
    print_header("TEST SUMMARY")
    
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
    print("\n🚀 Starting Comprehensive API Test Suite...\n")
    print(f"🌐 Testing Cloud Run: {BASE_URL}")
    print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    passed, failed, skipped = run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if failed == 0 else 1
    print(f"🏁 Test suite completed with exit code: {exit_code}")
    
    exit(exit_code)
