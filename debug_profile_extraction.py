#!/usr/bin/env python3
"""
Debug script for profile extraction issues

This script helps debug why profile data is not being extracted
from the Cloud Storage JSON files.
"""

import requests
import json
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_profile_extraction_debug():
    """Test the profile extraction with detailed debugging"""
    print("🔍 Debugging Profile Extraction Issue")
    print("=" * 60)
    
    # Test the backend API directly
    base_url = "http://localhost:5000"
    
    # First, let's test if the backend is running
    print("\n1️⃣ Testing backend health...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend is not running: {e}")
        print("Please start the backend with: cd backend && python app.py")
        return False
    
    # Test profile API health
    print("\n2️⃣ Testing profile API health...")
    try:
        response = requests.get(f"{base_url}/api/profile/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Profile API is healthy")
            print(f"   Firestore: {data.get('firestore_available')}")
            print(f"   Storage: {data.get('storage_available')}")
            print(f"   Gemini: {data.get('gemini_available')}")
        else:
            print(f"❌ Profile API health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Profile API error: {e}")
    
    # Test profile data extraction (this will fail without auth, but we can see the error)
    print("\n3️⃣ Testing profile data extraction (without auth)...")
    try:
        response = requests.get(f"{base_url}/api/profile/get-profile-data")
        print(f"Status: {response.status_code}")
        if response.status_code == 401:
            print("✅ Authentication required (expected)")
        else:
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("📋 DEBUGGING STEPS")
    print("=" * 60)
    print("🔧 To debug the profile extraction issue:")
    print("   1. Make sure you're logged in to the frontend")
    print("   2. Navigate to the profile page")
    print("   3. Click the 'Debug User Data' button")
    print("   4. Check the browser console for detailed logs")
    print("   5. Look for these specific log messages:")
    print("      - '🔍 Looking for profile data for user: user11'")
    print("      - '📄 User document data keys: [...]'")
    print("      - '📄 Cloud URLs structure: {...}'")
    print("      - '🔗 Found profile URL: ...'")
    print("      - '✅ Successfully loaded profile from Cloud Storage: {...}'")
    print("\n💡 The issue is likely one of these:")
    print("   - Profile URL not found in the expected structure")
    print("   - Cloud Storage file doesn't exist at the URL")
    print("   - JSON parsing error")
    print("   - Authentication/session issue")

def test_direct_extraction():
    """Test the extraction function directly with sample data"""
    print("\n🔧 Testing Direct Extraction Function")
    print("=" * 50)
    
    try:
        from routes.profile_management import extract_profile_from_json, extract_occupation_with_gemini
        
        # Sample profile JSON from Cloud Storage (as shown by user)
        sample_profile_json = {
            "Full Name": "Anuj",
            "Location": "",
            "Bio": "Continuing a 50-year family tradition of handloom weaving.",
            "Tagline": "Anuj continues his family's 50-year tradition of handloom weaving, focusing on hand-woven, Indian-made products. His biggest challenge is reaching customers, and he believes a vibrant brand logo would help. His brand name is Kaarigar.",
            "Materials Used": "Hand woven, all made in India",
            "Aspiration": "Reaching out to customers",
            "Conversation Summary": "Anuj is a dedicated handloom artisan upholding a 50-year-old family tradition. He passionately creates entirely hand-woven textiles, proudly boycotting machines and factory-made alternatives, committed to authentic Indian craftsmanship. His brand, Kaarigar, faces the challenge of reaching a wider customer base, and he envisions a vibrant brand logo to help overcome this obstacle and further promote his unique, handcrafted creations."
        }
        
        # Sample user data
        sample_user_data = {
            "name": "Anuj",
            "email": "anuj@gmail.com",
            "user_id": "user11"
        }
        
        print("📄 Testing with sample data:")
        print(f"Profile JSON: {json.dumps(sample_profile_json, indent=2)}")
        print(f"User Data: {json.dumps(sample_user_data, indent=2)}")
        
        # Test occupation extraction
        print("\n🔍 Testing occupation extraction...")
        occupation = extract_occupation_with_gemini(sample_profile_json)
        print(f"✅ Extracted Occupation: {occupation}")
        
        # Test full profile extraction
        print("\n🔍 Testing full profile extraction...")
        extracted_profile = extract_profile_from_json(sample_profile_json, sample_user_data)
        
        print("\n✅ Extracted Profile Data:")
        print(json.dumps(extracted_profile, indent=2))
        
        # Verify key fields
        print("\n🔍 Verification:")
        print(f"Name: {extracted_profile.get('name')} (Expected: Anuj)")
        print(f"Occupation: {extracted_profile.get('occupation')} (Expected: Handloom-related)")
        print(f"Bio: {extracted_profile.get('bio')[:50]}... (Expected: Continuing a 50-year family tradition...)")
        print(f"Materials: {extracted_profile.get('materials_used')} (Expected: Hand woven, all made in India)")
        print(f"Aspirations: {extracted_profile.get('aspirations')} (Expected: Reaching out to customers)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Could not import profile_management module: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all debug tests"""
    print("🔍 Profile Extraction Debug Suite")
    print("=" * 70)
    
    # Test 1: Backend API
    test_profile_extraction_debug()
    
    # Test 2: Direct extraction function
    success = test_direct_extraction()
    
    print("\n" + "=" * 70)
    print("📋 DEBUG SUMMARY")
    print("=" * 70)
    
    if success:
        print("🎉 Direct extraction function works correctly!")
        print("\n💡 The issue is likely in the Cloud Storage URL extraction.")
        print("   Check the browser console logs when you click 'Debug User Data'")
        print("   to see exactly what's happening with the Cloud Storage URL.")
    else:
        print("❌ Direct extraction function has issues.")
        print("   Check the error messages above for details.")

if __name__ == "__main__":
    main()
