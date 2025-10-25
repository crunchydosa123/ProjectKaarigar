#!/usr/bin/env python3
"""
Cleanup script to fix database structure
Separates user data and profile data into different collections
"""

import os
import sys

# Add the parent directory to the path to import Database_Setup modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from google.cloud import firestore
    from Database_Setup.firestore_nosql_storage import db
    print("✅ Successfully imported Firestore modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)

def cleanup_database():
    """Clean up the database structure"""
    print("🧹 Starting database cleanup...")
    
    try:
        # Get all documents from users collection
        users_collection = db.collection("users")
        docs = users_collection.stream()
        
        user_docs = []
        profile_docs = []
        
        for doc in docs:
            doc_data = doc.to_dict()
            print(f"📄 Found document: {doc.id}")
            print(f"   Data: {doc_data}")
            
            # Check if this is a user document (has password) or profile document
            if 'password' in doc_data:
                user_docs.append((doc.id, doc_data))
                print(f"   ✅ User document")
            else:
                profile_docs.append((doc.id, doc_data))
                print(f"   📋 Profile document")
        
        print(f"\n📊 Found {len(user_docs)} user documents and {len(profile_docs)} profile documents")
        
        # Move profile documents to profiles collection
        if profile_docs:
            print("\n🔄 Moving profile documents to profiles collection...")
            profiles_collection = db.collection("profiles")
            
            for doc_id, doc_data in profile_docs:
                print(f"📋 Moving profile document: {doc_id}")
                profiles_collection.document(doc_id).set(doc_data)
                # Delete from users collection
                users_collection.document(doc_id).delete()
                print(f"✅ Moved and deleted: {doc_id}")
        
        print(f"\n✅ Cleanup completed!")
        print(f"📊 User documents in users collection: {len(user_docs)}")
        print(f"📊 Profile documents in profiles collection: {len(profile_docs)}")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()

def test_database_structure():
    """Test the new database structure"""
    print("\n🧪 Testing new database structure...")
    
    try:
        # Test users collection
        users_collection = db.collection("users")
        user_docs = list(users_collection.stream())
        print(f"👤 Users collection has {len(user_docs)} documents")
        
        for doc in user_docs:
            doc_data = doc.to_dict()
            print(f"   📄 {doc.id}: {doc_data.get('email', 'No email')} - Password: {'Yes' if 'password' in doc_data else 'No'}")
        
        # Test profiles collection
        profiles_collection = db.collection("profiles")
        profile_docs = list(profiles_collection.stream())
        print(f"📋 Profiles collection has {len(profile_docs)} documents")
        
        for doc in profile_docs:
            doc_data = doc.to_dict()
            print(f"   📄 {doc.id}: {doc_data.get('email', 'No email')} - Password: {'Yes' if 'password' in doc_data else 'No'}")
        
        print("✅ Database structure test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Database Cleanup and Structure Fix")
    print("=" * 50)
    
    cleanup_database()
    test_database_structure()
    
    print("\n🎯 Next steps:")
    print("1. Restart your backend server")
    print("2. Try signing up with a new account")
    print("3. Try logging in with existing credentials")
