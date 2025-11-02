#!/usr/bin/env python3
"""
Test script for Project Kaarigar Authentication API
Tests signup, login, logout, and session management
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api/auth"

def test_signup():
    """Test user signup"""
    print("🧪 Testing User Signup...")
    
    signup_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "name": "Test User"
    }
    
    try:
        response = requests.post(f"{API_BASE}/signup", json=signup_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("✅ Signup successful!")
            return response.cookies
        else:
            print("❌ Signup failed!")
            return None
            
    except Exception as e:
        print(f"❌ Signup error: {e}")
        return None

def test_login():
    """Test user login"""
    print("\n🧪 Testing User Login...")
    
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/login", json=login_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            return response.cookies
        else:
            print("❌ Login failed!")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_session_check(cookies):
    """Test session status check"""
    print("\n🧪 Testing Session Check...")
    
    try:
        response = requests.get(f"{API_BASE}/session", cookies=cookies)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Session check successful!")
            return True
        else:
            print("❌ Session check failed!")
            return False
            
    except Exception as e:
        print(f"❌ Session check error: {e}")
        return False

def test_profile(cookies):
    """Test profile retrieval"""
    print("\n🧪 Testing Profile Retrieval...")
    
    try:
        response = requests.get(f"{API_BASE}/profile", cookies=cookies)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Profile retrieval successful!")
            return True
        else:
            print("❌ Profile retrieval failed!")
            return False
            
    except Exception as e:
        print(f"❌ Profile retrieval error: {e}")
        return False

def test_logout(cookies):
    """Test user logout"""
    print("\n🧪 Testing User Logout...")
    
    try:
        response = requests.post(f"{API_BASE}/logout", cookies=cookies)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Logout successful!")
            return True
        else:
            print("❌ Logout failed!")
            return False
            
    except Exception as e:
        print(f"❌ Logout error: {e}")
        return False

def test_health():
    """Test health check"""
    print("\n🧪 Testing Health Check...")
    
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Health check successful!")
            return True
        else:
            print("❌ Health check failed!")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def main():
    """Run all authentication tests"""
    print("🚀 Starting Project Kaarigar Authentication Tests")
    print("=" * 60)
    
    # Test health check first
    if not test_health():
        print("❌ Health check failed. Make sure the server is running.")
        return
    
    # Test signup
    signup_cookies = test_signup()
    if not signup_cookies:
        print("❌ Signup failed. Cannot continue with other tests.")
        return
    
    # Test login
    login_cookies = test_login()
    if not login_cookies:
        print("❌ Login failed. Cannot continue with other tests.")
        return
    
    # Test session check
    test_session_check(login_cookies)
    
    # Test profile retrieval
    test_profile(login_cookies)
    
    # Test logout
    test_logout(login_cookies)
    
    # Test session after logout
    print("\n🧪 Testing Session After Logout...")
    test_session_check(login_cookies)
    
    print("\n" + "=" * 60)
    print("🎉 Authentication tests completed!")

if __name__ == "__main__":
    main()
