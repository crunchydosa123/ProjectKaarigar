"""
API Route Test Suite for Reel Generation Flask API
Tests all Flask endpoints with actual HTTP requests
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, Any


# Configuration
BASE_URL = "http://localhost:5000"  # Change to your server URL
IMAGE_URLS = [
    "https://storage.googleapis.com/all_in_one_bucket/Trash/image/images%20(1).jpeg",
    "https://storage.googleapis.com/all_in_one_bucket/Trash/image/images%20(2).jpeg"
]


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
        print(f"Response: {response.text[:200]}")


# ==================== TESTS ====================

def test_health_check():
    """Test /api/health endpoint"""
    print_test("TEST 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print_response(response)
        
        if response.status_code == 200:
            print_pass("Health check endpoint working")
            return True
        else:
            print_fail(f"Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Request failed: {str(e)}")
        return False


def test_generate_reel_ideas_text():
    """Test /api/reel-generation/ideas with text prompt"""
    print_test("TEST 2: Generate Reel Ideas - Text Only")
    
    payload = {
        "initial_prompt": "Create a product launch video with excitement and innovation"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/reel-generation/ideas", json=payload)
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and len(data.get('ideas', [])) > 0:
                print_pass(f"Generated {len(data['ideas'])} ideas")
                return True
            else:
                print_fail("No ideas generated")
                return False
        else:
            print_fail(f"Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Request failed: {str(e)}")
        return False


def test_generate_reel_ideas_with_images():
    """Test /api/reel-generation/ideas with image URLs"""
    print_test("TEST 3: Generate Reel Ideas - With Image URLs")
    
    payload = {
        "initial_prompt": "Create a promotional video showcasing these products",
        "image_urls": IMAGE_URLS
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/reel-generation/ideas", json=payload)
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and len(data.get('ideas', [])) > 0:
                print_pass(f"Generated {len(data['ideas'])} ideas with image context")
                return True
            else:
                print_fail("No ideas generated")
                return False
        else:
            print_fail(f"Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Request failed: {str(e)}")
        return False


def test_refine_reel_idea():
    """Test /api/reel-generation/refine-idea"""
    print_test("TEST 4: Refine Reel Idea")
    
    payload = {
        "chosen_idea": "A dynamic product showcase with modern aesthetics and smooth transitions",
        "refinement_prompt": "Make it more focused on luxury and premium feel"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/reel-generation/refine-idea", json=payload)
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('refined_idea'):
                print_pass("Idea refined successfully")
                return True
            else:
                print_fail("No refined idea returned")
                return False
        else:
            print_fail(f"Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Request failed: {str(e)}")
        return False


def test_regenerate_ideas():
    """Test /api/reel-generation/regenerate-ideas"""
    print_test("TEST 5: Regenerate Ideas")
    
    payload = {
        "regeneration_prompt": "Generate tech-focused content with futuristic elements"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/reel-generation/regenerate-ideas", json=payload)
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and len(data.get('ideas', [])) > 0:
                print_pass(f"Regenerated {len(data['ideas'])} ideas")
                return True
            else:
                print_fail("No ideas generated")
                return False
        else:
            print_fail(f"Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Request failed: {str(e)}")
        return False


def test_generate_video_script():
    """Test /api/reel-generation/generate-video-script"""
    print_test("TEST 6: Generate Video Script")
    
    payload = {
        "reel_idea": "A cinematic journey through urban landscapes with dramatic lighting and smooth camera movements"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/reel-generation/generate-video-script", json=payload)
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('script'):
                print_pass(f"Script generated ({data.get('word_count')} words)")
                return True
            else:
                print_fail("No script returned")
                return False
        else:
            print_fail(f"Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Request failed: {str(e)}")
        return False


def test_generate_video_from_script():
    """Test /api/reel-generation/generate-video"""
    print_test("TEST 7: Generate Video from Script")
    
    payload = {
        "script": "A breathtaking sunset over mountains with golden light rays and peaceful atmosphere"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/reel-generation/generate-video", json=payload)
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('generated_video_url'):
                print_pass(f"Video generated: {data.get('generated_video_url')}")
                return True
            else:
                print_fail("No video URL returned")
                return False
        else:
            print_fail(f"Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Request failed: {str(e)}")
        return False


def test_generate_text_to_video():
    """Test /api/generate-video/text"""
    print_test("TEST 8: Generate Video from Text")
    
    payload = {
        "prompt": "A serene beach scene with waves gently crashing on shore at sunset"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/generate-video/text", json=payload)
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('generated_video_url'):
                print_pass(f"Text-to-video generated: {data.get('generated_video_url')}")
                return True
            else:
                print_fail("No video URL returned")
                return False
        else:
            print_fail(f"Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Request failed: {str(e)}")
        return False


def test_generate_images_to_video():
    """Test /api/generate-video/images with image URLs"""
    print_test("TEST 9: Generate Video from Images")
    
    payload = {
        "image_urls": IMAGE_URLS,
        "prompt": "Transform these images into a dynamic product showcase"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/generate-video/images", json=payload)
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('generated_video_url'):
                print_pass(f"Images-to-video generated: {data.get('generated_video_url')}")
                return True
            else:
                print_fail("No video URL returned")
                return False
        else:
            print_fail(f"Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Request failed: {str(e)}")
        return False


def test_list_videos():
    """Test /api/videos"""
    print_test("TEST 10: List All Videos")
    
    try:
        response = requests.get(f"{BASE_URL}/api/videos")
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_pass(f"Retrieved video list (Total: {data.get('total_all', 0)})")
                return True
            else:
                print_fail("No success flag in response")
                return False
        else:
            print_fail(f"Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Request failed: {str(e)}")
        return False


def test_list_cloud_videos():
    """Test /api/cloud-videos"""
    print_test("TEST 11: List Cloud Videos")
    
    try:
        response = requests.get(f"{BASE_URL}/api/cloud-videos")
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            print_pass(f"Retrieved cloud videos ({len(data.get('videos', []))} videos)")
            return True
        else:
            print_fail(f"Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Request failed: {str(e)}")
        return False


# ==================== RUN ALL TESTS ====================

def run_all_tests():
    """Execute all tests"""
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 80)
    print("  🧪 FLASK API ROUTE TEST SUITE")
    print(f"  Server: {BASE_URL}")
    print("=" * 80)
    print(f"{Colors.ENDC}")
    
    tests = [
        ("Health Check", test_health_check),
        ("Generate Ideas - Text", test_generate_reel_ideas_text),
        ("Generate Ideas - With Images", test_generate_reel_ideas_with_images),
        ("Refine Idea", test_refine_reel_idea),
        ("Regenerate Ideas", test_regenerate_ideas),
        ("Generate Video Script", test_generate_video_script),
        ("Generate Video from Script", test_generate_video_from_script),
        ("Text to Video", test_generate_text_to_video),
        ("Images to Video", test_generate_images_to_video),
        ("List Videos", test_list_videos),
        ("List Cloud Videos", test_list_cloud_videos),
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
    print("\n🚀 Starting API Route Tests...\n")
    print(f"{Colors.WARNING}⚠️  Make sure Flask server is running at {BASE_URL}{Colors.ENDC}\n")
    
    passed, failed = run_all_tests()
    
    exit(0 if failed == 0 else 1)