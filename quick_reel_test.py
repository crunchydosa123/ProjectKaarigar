#!/usr/bin/env python3
"""
Quick Reel Generation Test Script
Fast testing with minimal scenarios
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api/reel"

# Session for maintaining cookies
session = requests.Session()

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_reel_generation():
    """Quick test of reel generation scenarios"""
    log("🚀 Quick Reel Generation Test")
    log("=" * 40)
    
    # Test scenarios with short durations and limited segments
    test_cases = [
        {
            "name": "Text-to-Video (3s, 1 segment)",
            "data": {
                "prompt": "A quick sunset video",
                "title": "Quick Sunset",
                "image_urls": [],
                "duration": 3,
                "segments": 1
            }
        },
        {
            "name": "Single Image (4s, 2 segments)",
            "data": {
                "prompt": "Create a dynamic video",
                "title": "Single Image Test",
                "image_urls": ["https://picsum.photos/800/600?random=1"],
                "duration": 4,
                "segments": 2
            }
        },
        {
            "name": "Two Images (6s, 2 segments)",
            "data": {
                "prompt": "Create a slideshow",
                "title": "Two Images Test",
                "image_urls": [
                    "https://picsum.photos/800/600?random=2",
                    "https://picsum.photos/800/600?random=3"
                ],
                "duration": 6,
                "segments": 2
            }
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        log(f"\n🧪 Test {i}: {test_case['name']}")
        log(f"Data: {json.dumps(test_case['data'], indent=2)}")
        
        try:
            start_time = time.time()
            response = session.post(f"{API_BASE}/generate-reel", json=test_case['data'])
            end_time = time.time()
            
            duration = end_time - start_time
            log(f"⏱️ Request took {duration:.1f} seconds")
            log(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                log(f"✅ SUCCESS: {result.get('message', 'No message')}")
                log(f"🔗 URL: {result.get('public_url', 'No URL')}")
                log(f"📏 Duration: {result.get('duration', 'Unknown')}s")
                log(f"📊 Segments: {result.get('segments', 'Unknown')}")
                log(f"🖼️ Images: {result.get('image_count', 0)}")
                log(f"📁 Type: {result.get('generation_type', 'Unknown')}")
                results.append(True)
            else:
                log(f"❌ FAILED: {response.text}")
                results.append(False)
                
        except Exception as e:
            log(f"❌ ERROR: {str(e)}")
            results.append(False)
        
        # Small delay between tests
        time.sleep(2)
    
    # Summary
    log("\n" + "=" * 40)
    log("📊 QUICK TEST SUMMARY")
    log("=" * 40)
    
    passed = sum(results)
    total = len(results)
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result else "❌ FAIL"
        log(f"{status} Test {i}")
    
    log(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        log("🎉 ALL QUICK TESTS PASSED!")
    else:
        log(f"⚠️ {total - passed} tests failed")
    
    return passed == total

def test_get_reels():
    """Test getting generated reels"""
    log("\n📋 Testing Get Generated Reels")
    log("-" * 30)
    
    try:
        response = session.get(f"{API_BASE}/get-generated-reels")
        log(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            reels = result.get('reels', [])
            log(f"✅ Retrieved {len(reels)} reels")
            
            for i, reel in enumerate(reels[:3], 1):
                log(f"  {i}. {reel.get('title', 'No title')} - {reel.get('generation_type', 'Unknown')}")
            
            return True
        else:
            log(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        log(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    log("🎬 Quick Reel Generation Test")
    log("=" * 30)
    
    # Check server
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        log("✅ Server is running")
    except:
        log("❌ Server not running. Start Flask server first.")
        exit(1)
    
    # Run tests
    test1_success = test_reel_generation()
    test2_success = test_get_reels()
    
    if test1_success and test2_success:
        log("\n🎉 ALL QUICK TESTS PASSED!")
        exit(0)
    else:
        log("\n⚠️ Some tests failed")
        exit(1)
