import requests
import json
import os
import time
from pathlib import Path
from datetime import datetime

# Base API URL
BASE_URL = "http://127.0.0.1:5000"

# Test images location
TEST_IMAGES = [
    r"D:\Barclays\ProjectKaarigar\Model\images (1).jpeg",
    r"D:\Barclays\ProjectKaarigar\Model\images (2).jpeg"
]

VERBOSE = True

# Test results tracking
test_results = {
    'total': 0,
    'passed': 0,
    'failed': 0,
    'tests': []
}

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
    print(f"{status_icon} Status: {status_code}")
    print(f"⏱️  Response Time: {response_time:.2f}s")
    if data:
        data_str = json.dumps(data, indent=2)
        if len(data_str) > 500:
            print(f"   Response: {data_str[:500]}...")
        else:
            print(f"   Response: {data_str}")

def verify_image_exists(image_path: str) -> bool:
    """Verify image file exists"""
    if os.path.exists(image_path):
        file_size = os.path.getsize(image_path) / (1024 * 1024)
        print(f"   ✅ Image found: {os.path.basename(image_path)} ({file_size:.2f} MB)")
        return True
    else:
        print(f"   ❌ Image not found: {image_path}")
        return False

def add_test_result(test_name: str, success: bool, status_code: int, response_time: float, endpoint: str):
    """Add test result to tracking"""
    test_results['total'] += 1
    if success:
        test_results['passed'] += 1
    else:
        test_results['failed'] += 1
    
    test_results['tests'].append({
        'name': test_name,
        'success': success,
        'status_code': status_code,
        'response_time': response_time,
        'endpoint': endpoint
    })

# ==================== HEALTH CHECK ====================

def test_health_check():
    """Test health check endpoint"""
    log_test("Health Check", f"{BASE_URL}/api/health", "GET")
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        response_time = time.time() - start_time
        
        success = response.status_code == 200
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("Health Check", success, response.status_code, response_time, "/api/health")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Health Check", False, 0, 0, "/api/health")
        return False

# ==================== IMAGE ANALYSIS ENDPOINTS ====================

def test_analyze_image():
    """Test image analysis endpoint"""
    log_test("Analyze Image", f"{BASE_URL}/api/image-analysis/analyze", "POST")
    try:
        image_path = TEST_IMAGES[0]
        if not verify_image_exists(image_path):
            add_test_result("Analyze Image", False, 0, 0, "/api/image-analysis/analyze")
            return False
        
        start_time = time.time()
        with open(image_path, 'rb') as f:
            files = {'image': f}
            response = requests.post(f"{BASE_URL}/api/image-analysis/analyze", files=files, timeout=60)
        response_time = time.time() - start_time
        
        success = response.status_code in [200, 500]
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("Analyze Image", success, response.status_code, response_time, "/api/image-analysis/analyze")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Analyze Image", False, 0, 0, "/api/image-analysis/analyze")
        return False

def test_generate_prompt_from_image():
    """Test generate prompt from image endpoint"""
    log_test("Generate Prompt from Image", f"{BASE_URL}/api/image-analysis/generate-prompt", "POST")
    try:
        image_path = TEST_IMAGES[0]
        if not verify_image_exists(image_path):
            add_test_result("Generate Prompt from Image", False, 0, 0, "/api/image-analysis/generate-prompt")
            return False
        
        start_time = time.time()
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {'user_intent': 'Create a trending social media video'}
            response = requests.post(
                f"{BASE_URL}/api/image-analysis/generate-prompt",
                files=files,
                data=data,
                timeout=60
            )
        response_time = time.time() - start_time
        
        success = response.status_code in [200, 500]
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("Generate Prompt from Image", success, response.status_code, response_time, "/api/image-analysis/generate-prompt")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Generate Prompt from Image", False, 0, 0, "/api/image-analysis/generate-prompt")
        return False

def test_segmentation_plan():
    """Test segmentation plan endpoint"""
    log_test("Generate Segmentation Plan", f"{BASE_URL}/api/image-analysis/segmentation-plan", "POST")
    try:
        image_path = TEST_IMAGES[0]
        if not verify_image_exists(image_path):
            add_test_result("Segmentation Plan", False, 0, 0, "/api/image-analysis/segmentation-plan")
            return False
        
        start_time = time.time()
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {'num_segments': 3}
            response = requests.post(
                f"{BASE_URL}/api/image-analysis/segmentation-plan",
                files=files,
                data=data,
                timeout=60
            )
        response_time = time.time() - start_time
        
        success = response.status_code in [200, 400, 500]
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("Segmentation Plan", success, response.status_code, response_time, "/api/image-analysis/segmentation-plan")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Segmentation Plan", False, 0, 0, "/api/image-analysis/segmentation-plan")
        return False

def test_multi_angle():
    """Test multi-angle prompt generation endpoint"""
    log_test("Generate Multi-Angle Prompts", f"{BASE_URL}/api/image-analysis/multi-angle", "POST")
    try:
        image_path = TEST_IMAGES[0]
        if not verify_image_exists(image_path):
            add_test_result("Multi-Angle Prompts", False, 0, 0, "/api/image-analysis/multi-angle")
            return False
        
        start_time = time.time()
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {'variations': 3}
            response = requests.post(
                f"{BASE_URL}/api/image-analysis/multi-angle",
                files=files,
                data=data,
                timeout=60
            )
        response_time = time.time() - start_time
        
        success = response.status_code in [200, 500]
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("Multi-Angle Prompts", success, response.status_code, response_time, "/api/image-analysis/multi-angle")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Multi-Angle Prompts", False, 0, 0, "/api/image-analysis/multi-angle")
        return False

def test_process_images_single():
    """Test intelligent image processing - single image"""
    log_test("Process Image (Single)", f"{BASE_URL}/api/image-analysis/process", "POST")
    try:
        image_path = TEST_IMAGES[0]
        if not verify_image_exists(image_path):
            add_test_result("Process Image Single", False, 0, 0, "/api/image-analysis/process")
            return False
        
        start_time = time.time()
        with open(image_path, 'rb') as f:
            files = {'images': f}
            data = {'user_intent': 'Create engaging content'}
            response = requests.post(
                f"{BASE_URL}/api/image-analysis/process",
                files=files,
                data=data,
                timeout=60
            )
        response_time = time.time() - start_time
        
        success = response.status_code in [200, 500]
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("Process Image Single", success, response.status_code, response_time, "/api/image-analysis/process")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Process Image Single", False, 0, 0, "/api/image-analysis/process")
        return False

def test_process_images_multiple():
    """Test intelligent image processing - multiple images"""
    log_test("Process Images (Multiple)", f"{BASE_URL}/api/image-analysis/process", "POST")
    try:
        # Verify both images exist
        for img_path in TEST_IMAGES:
            if not verify_image_exists(img_path):
                add_test_result("Process Images Multiple", False, 0, 0, "/api/image-analysis/process")
                return False
        
        start_time = time.time()
        files = []
        for img_path in TEST_IMAGES:
            files.append(('images', open(img_path, 'rb')))
        
        data = {'user_intent': 'Create a slideshow video'}
        response = requests.post(
            f"{BASE_URL}/api/image-analysis/process",
            files=files,
            data=data,
            timeout=60
        )
        response_time = time.time() - start_time
        
        # Close files
        for _, f in files:
            f.close()
        
        success = response.status_code in [200, 500]
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("Process Images Multiple", success, response.status_code, response_time, "/api/image-analysis/process")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Process Images Multiple", False, 0, 0, "/api/image-analysis/process")
        return False

def test_get_analysis_logs():
    """Test get analysis logs endpoint"""
    log_test("Get Analysis Logs", f"{BASE_URL}/api/image-analysis/logs", "GET")
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/image-analysis/logs", timeout=10)
        response_time = time.time() - start_time
        
        success = response.status_code in [200, 500]
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("Get Analysis Logs", success, response.status_code, response_time, "/api/image-analysis/logs")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Get Analysis Logs", False, 0, 0, "/api/image-analysis/logs")
        return False

def test_clear_analysis_logs():
    """Test clear analysis logs endpoint"""
    log_test("Clear Analysis Logs", f"{BASE_URL}/api/image-analysis/clear-logs", "POST")
    try:
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/image-analysis/clear-logs", timeout=10)
        response_time = time.time() - start_time
        
        success = response.status_code in [200, 500]
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("Clear Analysis Logs", success, response.status_code, response_time, "/api/image-analysis/clear-logs")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Clear Analysis Logs", False, 0, 0, "/api/image-analysis/clear-logs")
        return False

# ==================== REEL IDEAS WORKFLOW ====================

def test_generate_ideas():
    """Test generate reel ideas endpoint"""
    log_test("Generate Reel Ideas", f"{BASE_URL}/api/reel-generation/ideas", "POST")
    try:
        payload = {
            'initial_prompt': 'Create a fun social media reel about coffee culture'
        }
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/reel-generation/ideas",
            data=payload,
            timeout=60
        )
        response_time = time.time() - start_time
        
        success = response.status_code in [200, 500]
        data = response.json()
        log_result(success, response.status_code, response_time, data)
        add_test_result("Generate Reel Ideas", success, response.status_code, response_time, "/api/reel-generation/ideas")
        return success, data.get('ideas', []) if success and response.status_code == 200 else []
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Generate Reel Ideas", False, 0, 0, "/api/reel-generation/ideas")
        return False, []

def test_refine_idea():
    """Test refine reel idea endpoint"""
    log_test("Refine Reel Idea", f"{BASE_URL}/api/reel-generation/refine-idea", "POST")
    try:
        payload = {
            "chosen_idea": "Create a coffee shop tour with trending music",
            "refinement_prompt": "Make it more engaging for Gen Z"
        }
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/reel-generation/refine-idea",
            json=payload,
            timeout=60
        )
        response_time = time.time() - start_time
        
        success = response.status_code in [200, 500]
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("Refine Reel Idea", success, response.status_code, response_time, "/api/reel-generation/refine-idea")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Refine Reel Idea", False, 0, 0, "/api/reel-generation/refine-idea")
        return False

def test_regenerate_ideas():
    """Test regenerate ideas endpoint"""
    log_test("Regenerate Reel Ideas", f"{BASE_URL}/api/reel-generation/regenerate-ideas", "POST")
    try:
        payload = {
            "regeneration_prompt": "Generate ideas focused on productivity and lifestyle"
        }
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/reel-generation/regenerate-ideas",
            json=payload,
            timeout=60
        )
        response_time = time.time() - start_time
        
        success = response.status_code in [200, 500]
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("Regenerate Reel Ideas", success, response.status_code, response_time, "/api/reel-generation/regenerate-ideas")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Regenerate Reel Ideas", False, 0, 0, "/api/reel-generation/regenerate-ideas")
        return False

def test_generate_video_script():
    """Test generate video script endpoint"""
    log_test("Generate Video Script", f"{BASE_URL}/api/reel-generation/generate-video-script", "POST")
    try:
        payload = {
            "reel_idea": "A fast-paced coffee shop tour with trending music and vibrant colors"
        }
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/reel-generation/generate-video-script",
            json=payload,
            timeout=60
        )
        response_time = time.time() - start_time
        
        success = response.status_code in [200, 500]
        data = response.json()
        log_result(success, response.status_code, response_time, data)
        add_test_result("Generate Video Script", success, response.status_code, response_time, "/api/reel-generation/generate-video-script")
        return success, data.get('script', '') if success and response.status_code == 200 else ''
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Generate Video Script", False, 0, 0, "/api/reel-generation/generate-video-script")
        return False, ''

def test_generate_video_from_script():
    """Test generate video from script endpoint"""
    log_test("Generate Video from Script", f"{BASE_URL}/api/reel-generation/generate-video", "POST")
    try:
        payload = {
            "script": "Show a beautiful sunset over the ocean with waves crashing on shore, golden hour lighting"
        }
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/reel-generation/generate-video",
            json=payload,
            timeout=180
        )
        response_time = time.time() - start_time
        
        success = response.status_code in [200, 500]
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("Generate Video from Script", success, response.status_code, response_time, "/api/reel-generation/generate-video")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Generate Video from Script", False, 0, 0, "/api/reel-generation/generate-video")
        return False

# ==================== VIDEO GENERATION ENDPOINTS ====================

def test_text_to_video():
    """Test text to video endpoint"""
    log_test("Text to Video", f"{BASE_URL}/api/generate-video/text", "POST")
    try:
        payload = {
            "prompt": "A beautiful sunset over the ocean with waves crashing"
        }
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/generate-video/text",
            json=payload,
            timeout=180
        )
        response_time = time.time() - start_time
        
        success = response.status_code in [200, 206, 500]
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("Text to Video", success, response.status_code, response_time, "/api/generate-video/text")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Text to Video", False, 0, 0, "/api/generate-video/text")
        return False

def test_image_to_video_single():
    """Test image to video endpoint - single image"""
    log_test("Image to Video (Single)", f"{BASE_URL}/api/generate-video/images", "POST")
    try:
        image_path = TEST_IMAGES[0]
        if not verify_image_exists(image_path):
            add_test_result("Image to Video Single", False, 0, 0, "/api/generate-video/images")
            return False
        
        start_time = time.time()
        with open(image_path, 'rb') as f:
            files = {'images': f}
            data = {'prompt': 'Transform this image into an engaging social media video'}
            response = requests.post(
                f"{BASE_URL}/api/generate-video/images",
                files=files,
                data=data,
                timeout=180
            )
        response_time = time.time() - start_time
        
        success = response.status_code in [200, 206, 500]
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("Image to Video Single", success, response.status_code, response_time, "/api/generate-video/images")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Image to Video Single", False, 0, 0, "/api/generate-video/images")
        return False

def test_image_to_video_multiple():
    """Test image to video endpoint - multiple images"""
    log_test("Image to Video (Multiple)", f"{BASE_URL}/api/generate-video/images", "POST")
    try:
        # Verify both images exist
        for img_path in TEST_IMAGES:
            if not verify_image_exists(img_path):
                add_test_result("Image to Video Multiple", False, 0, 0, "/api/generate-video/images")
                return False
        
        start_time = time.time()
        files = []
        for img_path in TEST_IMAGES:
            files.append(('images', open(img_path, 'rb')))
        
        data = {'prompt': 'Create an amazing slideshow with smooth transitions'}
        response = requests.post(
            f"{BASE_URL}/api/generate-video/images",
            files=files,
            data=data,
            timeout=180
        )
        response_time = time.time() - start_time
        
        # Close files
        for _, f in files:
            f.close()
        
        success = response.status_code in [200, 206, 500]
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("Image to Video Multiple", success, response.status_code, response_time, "/api/generate-video/images")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Image to Video Multiple", False, 0, 0, "/api/generate-video/images")
        return False

# ==================== VIDEO MANAGEMENT ENDPOINTS ====================

def test_list_videos():
    """Test list videos endpoint"""
    log_test("List Videos", f"{BASE_URL}/api/videos", "GET")
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/videos", timeout=10)
        response_time = time.time() - start_time
        
        success = response.status_code == 200
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("List Videos", success, response.status_code, response_time, "/api/videos")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("List Videos", False, 0, 0, "/api/videos")
        return False

def test_list_cloud_videos():
    """Test list cloud videos endpoint"""
    log_test("List Cloud Videos", f"{BASE_URL}/api/cloud-videos", "GET")
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/api/cloud-videos", timeout=10)
        response_time = time.time() - start_time
        
        success = response.status_code in [200, 500]
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("List Cloud Videos", success, response.status_code, response_time, "/api/cloud-videos")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("List Cloud Videos", False, 0, 0, "/api/cloud-videos")
        return False

def test_cleanup_video():
    """Test cleanup video endpoint"""
    log_test("Cleanup Video", f"{BASE_URL}/api/cleanup", "POST")
    try:
        payload = {
            "video_path": r"D:\Barclays\ProjectKaarigar\Model\reel_generation_flask\videos\invalid_video.mp4"
        }
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/cleanup",
            json=payload,
            timeout=10
        )
        response_time = time.time() - start_time
        
        success = response.status_code in [400, 500]  # Expected to fail with invalid path
        log_result(success, response.status_code, response_time, response.json())
        add_test_result("Cleanup Video", success, response.status_code, response_time, "/api/cleanup")
        return success
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        add_test_result("Cleanup Video", False, 0, 0, "/api/cleanup")
        return False

# ==================== MAIN TEST RUNNER ====================

def print_summary():
    """Print comprehensive test summary"""
    print(f"\n{'='*80}")
    print(f"📊 COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*80}")
    print(f"\n📈 Overall Results:")
    print(f"   Total Tests: {test_results['total']}")
    print(f"   ✅ Passed: {test_results['passed']}")
    print(f"   ❌ Failed: {test_results['failed']}")
    
    if test_results['total'] > 0:
        success_rate = (test_results['passed'] / test_results['total']) * 100
        print(f"   📊 Success Rate: {success_rate:.1f}%")
    
    print(f"\n⏱️  Performance Metrics:")
    
    if test_results['tests']:
        total_time = sum(t['response_time'] for t in test_results['tests'])
        avg_time = total_time / len(test_results['tests'])
        max_time = max(t['response_time'] for t in test_results['tests'])
        min_time = min(t['response_time'] for t in test_results['tests'])
        
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Average Response Time: {avg_time:.2f}s")
        print(f"   Fastest Response: {min_time:.2f}s")
        print(f"   Slowest Response: {max_time:.2f}s")
    
    print(f"\n📋 Test Details:")
    print(f"{'Test Name':<40} {'Status':<10} {'Time':<10} {'Code':<10}")
    print(f"{'-'*70}")
    
    for test in test_results['tests']:
        status = "✅ PASS" if test['success'] else "❌ FAIL"
        print(f"{test['name']:<40} {status:<10} {test['response_time']:<10.2f}s {test['status_code']:<10}")
    
    print(f"\n{'='*80}")
    print(f"Test execution completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

def main():
    """Run all tests"""
    print(f"\n{'='*80}")
    print(f"🧪 COMPREHENSIVE API TEST SUITE")
    print(f"Base URL: {BASE_URL}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    print(f"\n📁 Test Images:")
    for img_path in TEST_IMAGES:
        print(f"   {img_path}")
    
    # Check server is running
    print(f"\n🔍 Checking server connection...")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not ready. Health check failed.")
            return
        print(f"✅ Server is running and ready!")
    except Exception as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Error: {str(e)}")
        print(f"   Make sure the Flask API is running:")
        print(f"   $ python reel_generation_api.py")
        return
    
    # Health Check
    print(f"\n\n{'='*80}")
    print(f"🔵 SECTION 1: HEALTH CHECK")
    print(f"{'='*80}")
    test_health_check()
    
    # Image Analysis
    print(f"\n\n{'='*80}")
    print(f"🔵 SECTION 2: IMAGE ANALYSIS & PROMPT GENERATION")
    print(f"{'='*80}")
    test_analyze_image()
    test_generate_prompt_from_image()
    test_segmentation_plan()
    test_multi_angle()
    test_process_images_single()
    test_process_images_multiple()
    test_get_analysis_logs()
    test_clear_analysis_logs()
    
    # Reel Ideas Workflow
    print(f"\n\n{'='*80}")
    print(f"🔵 SECTION 3: REEL IDEAS WORKFLOW")
    print(f"{'='*80}")
    success, ideas = test_generate_ideas()
    test_refine_idea()
    test_regenerate_ideas()
    success, script = test_generate_video_script()
    test_generate_video_from_script()
    
    # Video Generation
    print(f"\n\n{'='*80}")
    print(f"🔵 SECTION 4: VIDEO GENERATION")
    print(f"{'='*80}")
    test_text_to_video()
    test_image_to_video_single()
    test_image_to_video_multiple()
    
    # Video Management
    print(f"\n\n{'='*80}")
    print(f"🔵 SECTION 5: VIDEO MANAGEMENT")
    print(f"{'='*80}")
    test_list_videos()
    test_list_cloud_videos()
    test_cleanup_video()
    
    # Print Summary
    print_summary()

if __name__ == '__main__':
    main()