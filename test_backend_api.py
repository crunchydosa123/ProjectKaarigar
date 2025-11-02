#!/usr/bin/env python3
"""
Quick test script to verify backend API is working
"""

import requests
import json

def test_backend_api():
    """Test the backend API endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Backend API")
    print("=" * 40)
    
    # Test 1: Health check
    print("\n1️⃣ Testing main health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Profile health check
    print("\n2️⃣ Testing profile health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/profile/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Auth health check
    print("\n3️⃣ Testing auth health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/auth/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Try to get profile data (should fail without auth)
    print("\n4️⃣ Testing profile data endpoint (should fail without auth)...")
    try:
        response = requests.get(f"{base_url}/api/profile/get-profile-data")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_backend_api()
