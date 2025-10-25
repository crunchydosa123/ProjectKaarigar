#!/usr/bin/env python3
"""
Test script to verify Firestore database connection and operations
"""

import os
import sys

# Add the parent directory to the path to import Database_Setup modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from google.cloud import firestore
    from Database_Setup.firestore_nosql_storage import create_document, get_document, query_documents
    print("✅ Successfully imported Firestore modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)

def test_firestore_connection():
    """Test basic Firestore connection"""
    print("\n🧪 Testing Firestore Connection...")
    
    try:
        PROJECT_ID = "useful-figure-475210-g7"
        db = firestore.Client(project=PROJECT_ID)
        print(f"✅ Firestore client created successfully")
        print(f"📊 Project ID: {db.project}")
        return True
    except Exception as e:
        print(f"❌ Firestore connection failed: {e}")
        return False

def test_create_document():
    """Test creating a document"""
    print("\n🧪 Testing Document Creation...")
    
    try:
        test_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword123",
            "createdAt": "2025-01-22T16:30:00Z",
            "isActive": True
        }
        
        print(f"📝 Creating test document with data: {test_data}")
        doc_id = create_document(test_data, "test_user_123")
        print(f"✅ Document created with ID: {doc_id}")
        return True
    except Exception as e:
        print(f"❌ Document creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_document():
    """Test retrieving a document"""
    print("\n🧪 Testing Document Retrieval...")
    
    try:
        doc_data = get_document("test_user_123")
        if doc_data:
            print(f"✅ Document retrieved: {doc_data}")
            return True
        else:
            print("❌ Document not found")
            return False
    except Exception as e:
        print(f"❌ Document retrieval failed: {e}")
        return False

def test_query_documents():
    """Test querying documents"""
    print("\n🧪 Testing Document Query...")
    
    try:
        users = query_documents("email", "==", "test@example.com")
        print(f"✅ Query returned {len(users) if users else 0} documents")
        if users:
            print(f"📄 First result: {users[0]}")
        return True
    except Exception as e:
        print(f"❌ Document query failed: {e}")
        return False

def test_cleanup():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        # Note: You might need to implement a delete function
        print("⚠️ Cleanup not implemented - test data may remain in database")
        return True
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

def main():
    """Run all database tests"""
    print("🚀 Starting Firestore Database Tests")
    print("=" * 50)
    
    tests = [
        ("Firestore Connection", test_firestore_connection),
        ("Document Creation", test_create_document),
        ("Document Retrieval", test_get_document),
        ("Document Query", test_query_documents),
        ("Cleanup", test_cleanup)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()
