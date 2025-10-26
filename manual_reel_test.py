#!/usr/bin/env python3
"""
Manual Reel Generation Test Script
Run individual test scenarios interactively
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

def test_scenario(name, data):
    """Test a single scenario"""
    log(f"\n🧪 Testing: {name}")
    log(f"Data: {json.dumps(data, indent=2)}")
    
    try:
        start_time = time.time()
        response = session.post(f"{API_BASE}/generate-reel", json=data)
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
            return True
        else:
            log(f"❌ FAILED: {response.text}")
            return False
            
    except Exception as e:
        log(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Interactive test menu"""
    log("🎬 Manual Reel Generation Test")
    log("=" * 40)
    
    # Check server
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        log("✅ Server is running")
    except:
        log("❌ Server not running. Start Flask server first.")
        return
    
    # Test scenarios
    scenarios = {
        "1": {
            "name": "Text-to-Video (3s, 1 segment)",
            "data": {
                "prompt": "A quick sunset video",
                "title": "Quick Sunset",
                "image_urls": [],
                "duration": 3,
                "segments": 1
            }
        },
        "2": {
            "name": "Single Image (4s, 2 segments)",
            "data": {
                "prompt": "Create a dynamic video",
                "title": "Single Image Test",
                "image_urls": ["https://picsum.photos/800/600?random=1"],
                "duration": 4,
                "segments": 2
            }
        },
        "3": {
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
        },
        "4": {
            "name": "Text-to-Video Auto (no custom settings)",
            "data": {
                "prompt": "A cinematic video about mountains",
                "title": "Auto Text Video",
                "image_urls": []
            }
        },
        "5": {
            "name": "Single Image Auto (no custom settings)",
            "data": {
                "prompt": "Create a professional video",
                "title": "Auto Single Image",
                "image_urls": ["https://picsum.photos/800/600?random=4"]
            }
        },
        "6": {
            "name": "Multiple Images Auto (no custom settings)",
            "data": {
                "prompt": "Create a portfolio showcase",
                "title": "Auto Multiple Images",
                "image_urls": [
                    "https://picsum.photos/800/600?random=5",
                    "https://picsum.photos/800/600?random=6",
                    "https://picsum.photos/800/600?random=7"
                ]
            }
        }
    }
    
    while True:
        print("\n" + "=" * 50)
        print("🎬 MANUAL REEL GENERATION TEST MENU")
        print("=" * 50)
        print("1. Text-to-Video (3s, 1 segment)")
        print("2. Single Image (4s, 2 segments)")
        print("3. Two Images (6s, 2 segments)")
        print("4. Text-to-Video Auto")
        print("5. Single Image Auto")
        print("6. Multiple Images Auto")
        print("7. Get Generated Reels")
        print("8. Run All Tests")
        print("0. Exit")
        print("=" * 50)
        
        choice = input("Enter your choice (0-8): ").strip()
        
        if choice == "0":
            log("👋 Goodbye!")
            break
        elif choice == "7":
            # Get generated reels
            log("\n📋 Getting Generated Reels")
            try:
                response = session.get(f"{API_BASE}/get-generated-reels")
                if response.status_code == 200:
                    result = response.json()
                    reels = result.get('reels', [])
                    log(f"✅ Retrieved {len(reels)} reels")
                    for i, reel in enumerate(reels[:5], 1):
                        log(f"  {i}. {reel.get('title', 'No title')} - {reel.get('generation_type', 'Unknown')}")
                else:
                    log(f"❌ Failed: {response.text}")
            except Exception as e:
                log(f"❌ Error: {str(e)}")
        elif choice == "8":
            # Run all tests
            log("\n🚀 Running All Tests")
            results = []
            for key, scenario in scenarios.items():
                if key != "7":  # Skip the get reels option
                    result = test_scenario(scenario["name"], scenario["data"])
                    results.append(result)
                    time.sleep(2)  # Small delay between tests
            
            # Summary
            passed = sum(results)
            total = len(results)
            log(f"\n📊 Results: {passed}/{total} tests passed")
        elif choice in scenarios:
            # Run specific test
            scenario = scenarios[choice]
            test_scenario(scenario["name"], scenario["data"])
        else:
            log("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
