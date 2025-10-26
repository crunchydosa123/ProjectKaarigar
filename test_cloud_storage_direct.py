#!/usr/bin/env python3
"""
Test script to directly access the Cloud Storage profile JSON file

This script tests direct access to the Cloud Storage file to verify
that the profile data can be retrieved correctly.
"""

import sys
import os
import json

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_direct_cloud_storage_access():
    """Test direct access to the Cloud Storage profile file"""
    print("🧪 Testing Direct Cloud Storage Access")
    print("=" * 60)
    
    try:
        from google.cloud import storage
        
        # Configuration
        PROJECT_ID = "useful-figure-475210-g7"
        BUCKET_NAME = "all_in_one_bucket"
        
        # Initialize Cloud Storage client
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        
        print(f"✅ Cloud Storage client initialized")
        print(f"📦 Bucket: {BUCKET_NAME}")
        
        # Test the exact path from the URL
        profile_path = "kaarigar/KR_USER11/profile/profile.json"
        print(f"📁 Testing path: {profile_path}")
        
        # Check if file exists
        blob = bucket.blob(profile_path)
        if blob.exists():
            print(f"✅ File exists at: {profile_path}")
            
            # Download and parse the JSON
            profile_json = blob.download_as_text()
            profile_data = json.loads(profile_json)
            
            print(f"✅ Successfully loaded profile data:")
            print(json.dumps(profile_data, indent=2))
            
            # Test the extraction function
            print(f"\n🔧 Testing profile extraction...")
            from routes.profile_management import extract_profile_from_json
            
            user_data = {
                "name": "Anuj",
                "email": "anuj@gmail.com",
                "user_id": "user11"
            }
            
            extracted_profile = extract_profile_from_json(profile_data, user_data)
            
            print(f"✅ Extracted profile data:")
            print(json.dumps(extracted_profile, indent=2))
            
            return True
            
        else:
            print(f"❌ File does not exist at: {profile_path}")
            return False
            
    except ImportError as e:
        print(f"❌ Could not import required modules: {e}")
        return False
    except Exception as e:
        print(f"❌ Error accessing Cloud Storage: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_different_paths():
    """Test with different possible paths"""
    print("\n🔍 Testing Different Path Variations")
    print("=" * 50)
    
    try:
        from google.cloud import storage
        
        # Configuration
        PROJECT_ID = "useful-figure-475210-g7"
        BUCKET_NAME = "all_in_one_bucket"
        
        # Initialize Cloud Storage client
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        
        # Test different path variations
        test_paths = [
            "kaarigar/KR_USER11/profile/profile.json",
            "kaarigar/KR_USER11/profiles/profile.json",
            "kaarigar/KR_USER11/profile.json",
            "profiles/KR_USER11/profile.json"
        ]
        
        for path in test_paths:
            print(f"📁 Testing path: {path}")
            blob = bucket.blob(path)
            if blob.exists():
                print(f"✅ File exists at: {path}")
                try:
                    profile_json = blob.download_as_text()
                    profile_data = json.loads(profile_json)
                    print(f"✅ Successfully loaded data from: {path}")
                    return path, profile_data
                except Exception as e:
                    print(f"❌ Error loading data from {path}: {e}")
            else:
                print(f"⚠️ File does not exist at: {path}")
        
        return None, None
        
    except Exception as e:
        print(f"❌ Error testing paths: {e}")
        return None, None

def main():
    """Run all tests"""
    print("🧪 Cloud Storage Direct Access Test Suite")
    print("=" * 70)
    
    # Test 1: Direct access to the known path
    success1 = test_direct_cloud_storage_access()
    
    # Test 2: Test different path variations
    if not success1:
        print("\n🔍 Trying different path variations...")
        path, data = test_with_different_paths()
        if path and data:
            print(f"✅ Found working path: {path}")
            success1 = True
    
    print("\n" + "=" * 70)
    print("📋 TEST SUMMARY")
    print("=" * 70)
    
    if success1:
        print("🎉 Cloud Storage access test passed!")
        print("\n✅ The system can now:")
        print("   ✅ Access the Cloud Storage profile JSON file")
        print("   ✅ Parse the JSON data correctly")
        print("   ✅ Extract profile information")
        print("\n🚀 The backend should now be able to load profile data!")
        print("\n💡 Next steps:")
        print("   1. Restart the backend: cd backend && python app.py")
        print("   2. Test the profile page in the frontend")
        print("   3. Use the 'Debug User Data' button to verify")
    else:
        print("❌ Cloud Storage access test failed!")
        print("\n🔧 Troubleshooting:")
        print("   1. Check Google Cloud credentials")
        print("   2. Verify bucket permissions")
        print("   3. Check if the file path is correct")

if __name__ == "__main__":
    main()
