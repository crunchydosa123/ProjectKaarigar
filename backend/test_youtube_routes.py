"""
Test YouTube Routes
Quick test to verify YouTube endpoints are accessible
"""

import requests

BASE_URL = "http://localhost:5000"

print("🧪 Testing YouTube Routes")
print("=" * 50)

# Test 1: Auth Status (without login)
print("\n1. Testing /api/youtube/auth/status")
try:
    response = requests.get(f"{BASE_URL}/api/youtube/auth/status")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Auth Start (without login)
print("\n2. Testing /api/youtube/auth/start")
try:
    response = requests.get(f"{BASE_URL}/api/youtube/auth/start")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Check if route exists at all
print("\n3. Testing if /api/youtube route exists")
try:
    response = requests.get(f"{BASE_URL}/api/youtube/")
    print(f"   Status: {response.status_code}")
    if response.status_code == 404:
        print("   ⚠️  Route not found - blueprint may not be registered")
    else:
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 50)
print("✅ Test complete!")
