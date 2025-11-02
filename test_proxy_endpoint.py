#!/usr/bin/env python3
"""
Test script to verify the proxy endpoint is working correctly
"""

import requests
import json

def test_proxy_endpoint():
    """Test the proxy endpoint with a sample image URL"""
    
    # Test image URL (the one from the error)
    image_url = "https://storage.googleapis.com/all_in_one_bucket/kaarigar/KR_USER11/generated_images/edited_6ecb0994-dfb7-490f-9d57-f2a4ad22ae27.png"
    
    # Proxy endpoint
    proxy_url = f"http://localhost:5000/api/reel-generator/proxy-image?url={requests.utils.quote(image_url)}"
    
    print("🧪 Testing Proxy Endpoint")
    print(f"📥 Original URL: {image_url}")
    print(f"🔄 Proxy URL: {proxy_url}")
    print()
    
    try:
        # Test the proxy endpoint
        response = requests.get(proxy_url, timeout=30)
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📊 Content Length: {len(response.content)} bytes")
        print(f"📄 Content Type: {response.headers.get('content-type', 'Unknown')}")
        print(f"🌐 CORS Headers:")
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
            'Cache-Control': response.headers.get('Cache-Control')
        }
        
        for header, value in cors_headers.items():
            print(f"   {header}: {value}")
        
        if response.status_code == 200:
            print("\n✅ Proxy endpoint is working correctly!")
            print("🔧 The issue is likely browser caching in the frontend.")
            print("💡 Solution: Hard refresh the browser (Ctrl+Shift+R) or clear cache.")
        else:
            print(f"\n❌ Proxy endpoint returned error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error testing proxy endpoint: {e}")
        print("🔧 Make sure the backend server is running on localhost:5000")

if __name__ == "__main__":
    test_proxy_endpoint()


