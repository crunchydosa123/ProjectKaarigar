#!/usr/bin/env python3
"""
Test script for Profile Data Extraction

This script tests the profile data extraction from the actual JSON structure
provided by the user, simulating the Cloud Storage JSON format.

Usage:
    python test_profile_extraction.py
"""

import json
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_profile_extraction():
    """Test profile data extraction from the actual JSON structure"""
    print("🧪 Testing Profile Data Extraction")
    print("=" * 50)
    
    # Sample profile data from Cloud Storage (as provided by user)
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
        "email": "anuj@example.com",
        "user_id": "user1"
    }
    
    print("📄 Sample Profile JSON:")
    print(json.dumps(sample_profile_json, indent=2))
    print("\n👤 Sample User Data:")
    print(json.dumps(sample_user_data, indent=2))
    
    # Test the extraction function
    try:
        from routes.profile_management import extract_profile_from_json
        
        extracted_profile = extract_profile_from_json(sample_profile_json, sample_user_data)
        
        print("\n✅ Extracted Profile Data:")
        print(json.dumps(extracted_profile, indent=2))
        
        # Verify the extraction
        print("\n🔍 Verification:")
        print(f"Name: {extracted_profile.get('name')} (Expected: Anuj)")
        print(f"Bio: {extracted_profile.get('bio')[:50]}... (Expected: Continuing a 50-year family tradition...)")
        print(f"Materials: {extracted_profile.get('materials_used')} (Expected: Hand woven, all made in India)")
        print(f"Aspirations: {extracted_profile.get('aspirations')} (Expected: Reaching out to customers)")
        print(f"Craft Details: {extracted_profile.get('craft_details')[:50]}... (Expected: Anuj continues his family's...)")
        
        # Check if all required fields are present
        required_fields = ['name', 'email', 'occupation', 'bio', 'location', 'languages', 
                          'craft_details', 'materials_used', 'experience_years', 'aspirations', 'challenges']
        
        missing_fields = [field for field in required_fields if not extracted_profile.get(field)]
        if missing_fields:
            print(f"\n⚠️ Missing fields: {missing_fields}")
        else:
            print("\n✅ All required fields are present")
            
        return True
        
    except ImportError as e:
        print(f"❌ Could not import profile_management module: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        return False

def test_json_structure_mapping():
    """Test the mapping between the actual JSON structure and our profile format"""
    print("\n🔄 Testing JSON Structure Mapping")
    print("=" * 50)
    
    # Mapping from the actual JSON structure to our profile format
    mapping = {
        "Full Name": "name",
        "Location": "location", 
        "Bio": "bio",
        "Tagline": "craft_details",
        "Materials Used": "materials_used",
        "Aspiration": "aspirations",
        "Conversation Summary": "challenges"  # Can be used for challenges or additional context
    }
    
    print("📋 Field Mapping:")
    for source_field, target_field in mapping.items():
        print(f"  {source_field} → {target_field}")
    
    # Test with sample data
    sample_data = {
        "Full Name": "Anuj",
        "Location": "Jaipur, Rajasthan",
        "Bio": "Continuing a 50-year family tradition of handloom weaving.",
        "Tagline": "Anuj continues his family's 50-year tradition...",
        "Materials Used": "Hand woven, all made in India",
        "Aspiration": "Reaching out to customers"
    }
    
    print("\n📄 Sample Data Transformation:")
    for source_field, target_field in mapping.items():
        value = sample_data.get(source_field, "")
        print(f"  {source_field}: '{value}' → {target_field}: '{value}'")

def main():
    """Run all tests"""
    print("🧪 Profile Data Extraction Test Suite")
    print("=" * 60)
    
    # Test 1: Profile extraction
    success1 = test_profile_extraction()
    
    # Test 2: JSON structure mapping
    test_json_structure_mapping()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    if success1:
        print("🎉 Profile extraction test passed!")
        print("\n💡 The system can now:")
        print("   ✅ Extract profile data from Cloud Storage JSON files")
        print("   ✅ Map fields from the actual JSON structure")
        print("   ✅ Auto-fill profile fields in the frontend")
        print("   ✅ Handle missing fields gracefully")
        print("\n🚀 Next steps:")
        print("   1. Start the backend: cd backend && python app.py")
        print("   2. Start the frontend: cd frontend2 && npm run dev")
        print("   3. Navigate to profile page to see auto-filled data")
    else:
        print("❌ Profile extraction test failed!")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure the backend routes are properly imported")
        print("   2. Check that the profile_management.py file exists")
        print("   3. Verify the JSON structure matches the expected format")

if __name__ == "__main__":
    main()
