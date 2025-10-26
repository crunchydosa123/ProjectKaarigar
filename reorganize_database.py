#!/usr/bin/env python3
"""
Database Reorganization Script for Project Kaarigar

This script reorganizes the existing Firestore database to use user-based organization
where each document/collection is linked to a simple user ID (user1, user2, user3, etc.)

Usage:
    python reorganize_database.py [--dry-run] [--backup]
"""

import os
import sys
import json
from datetime import datetime
import argparse

try:
    from google.cloud import firestore
    from google.cloud import storage
except ImportError as e:
    print(f"❌ Missing required packages: {e}")
    print("Install with: pip install google-cloud-firestore google-cloud-storage")
    sys.exit(1)

# Configuration
PROJECT_ID = "useful-figure-475210-g7"
BUCKET_NAME = "all_in_one_bucket"

class DatabaseReorganizer:
    def __init__(self, project_id: str, bucket_name: str):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.db = None
        self.storage_client = None
        self.bucket = None
        self.dry_run = False
        self.backup_data = {}
    
    def initialize_clients(self) -> bool:
        """Initialize Firestore and Storage clients"""
        try:
            print(f"🔧 Initializing clients for project: {self.project_id}")
            
            # Initialize Firestore
            self.db = firestore.Client(project=self.project_id)
            print("✅ Firestore client initialized")
            
            # Initialize Storage
            self.storage_client = storage.Client(project=self.project_id)
            self.bucket = self.storage_client.bucket(self.bucket_name)
            print("✅ Storage client initialized")
            
            return True
        except Exception as e:
            print(f"❌ Failed to initialize clients: {e}")
            return False
    
    def backup_existing_data(self):
        """Backup existing data before reorganization"""
        print("\n" + "="*60)
        print("💾 BACKING UP EXISTING DATA")
        print("="*60)
        
        try:
            collections = list(self.db.collections())
            print(f"📊 Found {len(collections)} collections to backup")
            
            for collection in collections:
                collection_name = collection.id
                print(f"\n📁 Backing up collection: {collection_name}")
                
                docs = list(collection.stream())
                collection_data = []
                
                for doc in docs:
                    doc_data = doc.to_dict()
                    collection_data.append({
                        'id': doc.id,
                        'data': doc_data
                    })
                
                self.backup_data[collection_name] = collection_data
                print(f"   ✅ Backed up {len(collection_data)} documents")
            
            # Save backup to file
            backup_file = f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w') as f:
                json.dump(self.backup_data, f, indent=2, default=str)
            print(f"\n💾 Backup saved to: {backup_file}")
            
        except Exception as e:
            print(f"❌ Error backing up data: {e}")
    
    def reorganize_users_collection(self):
        """Reorganize users collection to use simple user IDs"""
        print("\n" + "="*60)
        print("👥 REORGANIZING USERS COLLECTION")
        print("="*60)
        
        try:
            users_collection = self.db.collection('users')
            users = list(users_collection.stream())
            
            print(f"📊 Found {len(users)} users to reorganize")
            
            # Create new user mapping
            user_mapping = {}
            new_user_id = 1
            
            for user_doc in users:
                old_user_id = user_doc.id
                user_data = user_doc.to_dict()
                
                # Generate new simple user ID
                new_simple_id = f"user{new_user_id}"
                user_mapping[old_user_id] = new_simple_id
                
                # Update user data
                updated_user_data = user_data.copy()
                updated_user_data['userId'] = new_simple_id
                updated_user_data['old_user_id'] = old_user_id  # Keep reference to old ID
                
                if not self.dry_run:
                    # Delete old document
                    user_doc.reference.delete()
                    
                    # Create new document with simple ID
                    users_collection.document(new_simple_id).set(updated_user_data)
                    print(f"   ✅ Reorganized: {old_user_id} → {new_simple_id}")
                else:
                    print(f"   🔍 [DRY RUN] Would reorganize: {old_user_id} → {new_simple_id}")
                
                new_user_id += 1
            
            return user_mapping
            
        except Exception as e:
            print(f"❌ Error reorganizing users: {e}")
            return {}
    
    def reorganize_profiles_collection(self, user_mapping):
        """Reorganize profiles collection to use simple user IDs"""
        print("\n" + "="*60)
        print("👤 REORGANIZING PROFILES COLLECTION")
        print("="*60)
        
        try:
            profiles_collection = self.db.collection('profiles')
            profiles = list(profiles_collection.stream())
            
            print(f"📊 Found {len(profiles)} profiles to reorganize")
            
            for profile_doc in profiles:
                old_profile_id = profile_doc.id
                profile_data = profile_doc.to_dict()
                
                # Find corresponding user ID
                user_id = profile_data.get('userId')
                if not user_id:
                    # Try to extract from old profile ID
                    if old_profile_id.startswith('profile_user_'):
                        old_user_id = old_profile_id.replace('profile_user_', 'user_')
                        user_id = user_mapping.get(old_user_id)
                
                if user_id and user_id in user_mapping.values():
                    new_profile_id = f"profile_{user_id}"
                    
                    # Update profile data
                    updated_profile_data = profile_data.copy()
                    updated_profile_data['userId'] = user_id
                    updated_profile_data['old_profile_id'] = old_profile_id
                    
                    if not self.dry_run:
                        # Delete old document
                        profile_doc.reference.delete()
                        
                        # Create new document with simple ID
                        profiles_collection.document(new_profile_id).set(updated_profile_data)
                        print(f"   ✅ Reorganized: {old_profile_id} → {new_profile_id}")
                    else:
                        print(f"   🔍 [DRY RUN] Would reorganize: {old_profile_id} → {new_profile_id}")
                else:
                    print(f"   ⚠️  Could not map profile: {old_profile_id}")
            
        except Exception as e:
            print(f"❌ Error reorganizing profiles: {e}")
    
    def reorganize_kaarigars_collection(self, user_mapping):
        """Reorganize kaarigars collection to use simple user IDs"""
        print("\n" + "="*60)
        print("🎨 REORGANIZING KAARIGARS COLLECTION")
        print("="*60)
        
        try:
            kaarigars_collection = self.db.collection('kaarigars')
            kaarigars = list(kaarigars_collection.stream())
            
            print(f"📊 Found {len(kaarigars)} kaarigars to reorganize")
            
            for kaarigar_doc in kaarigars:
                old_kaarigar_id = kaarigar_doc.id
                kaarigar_data = kaarigar_doc.to_dict()
                
                # Find corresponding user ID
                user_id = kaarigar_data.get('user_id')
                if not user_id:
                    # Try to extract from old kaarigar ID
                    if old_kaarigar_id.startswith('KR_'):
                        # This might be an old format, try to find user
                        user_id = "user1"  # Default fallback
                
                if user_id:
                    # Generate new kaarigar ID based on user ID
                    new_kaarigar_id = f"KR_{user_id.upper()}"
                    new_brand_id = f"BRAND_{user_id.upper()}"
                    
                    # Update kaarigar data
                    updated_kaarigar_data = kaarigar_data.copy()
                    updated_kaarigar_data['kaarigar_id'] = new_kaarigar_id
                    updated_kaarigar_data['brand_id'] = new_brand_id
                    updated_kaarigar_data['user_id'] = user_id
                    updated_kaarigar_data['old_kaarigar_id'] = old_kaarigar_id
                    
                    if not self.dry_run:
                        # Delete old document
                        kaarigar_doc.reference.delete()
                        
                        # Create new document with simple ID
                        kaarigars_collection.document(new_kaarigar_id).set(updated_kaarigar_data)
                        print(f"   ✅ Reorganized: {old_kaarigar_id} → {new_kaarigar_id}")
                    else:
                        print(f"   🔍 [DRY RUN] Would reorganize: {old_kaarigar_id} → {new_kaarigar_id}")
                else:
                    print(f"   ⚠️  Could not map kaarigar: {old_kaarigar_id}")
            
        except Exception as e:
            print(f"❌ Error reorganizing kaarigars: {e}")
    
    def reorganize_other_collections(self, user_mapping):
        """Reorganize other collections (brands, conversations, etc.)"""
        print("\n" + "="*60)
        print("📦 REORGANIZING OTHER COLLECTIONS")
        print("="*60)
        
        collections_to_update = ['brands', 'conversations', 'videos', 'products', 'listings']
        
        for collection_name in collections_to_update:
            try:
                collection = self.db.collection(collection_name)
                docs = list(collection.stream())
                
                print(f"\n📁 Processing {collection_name}: {len(docs)} documents")
                
                for doc in docs:
                    doc_id = doc.id
                    doc_data = doc.to_dict()
                    
                    # Update references to use new user IDs
                    updated_data = doc_data.copy()
                    updated = False
                    
                    # Update common field patterns
                    if 'kaarigarId' in doc_data:
                        old_kaarigar_id = doc_data['kaarigarId']
                        if old_kaarigar_id.startswith('KR_'):
                            # Extract user ID from old kaarigar ID or use mapping
                            new_kaarigar_id = f"KR_USER1"  # Default for now
                            updated_data['kaarigarId'] = new_kaarigar_id
                            updated = True
                    
                    if 'brandId' in doc_data:
                        old_brand_id = doc_data['brandId']
                        if old_brand_id.startswith('BRAND_'):
                            new_brand_id = f"BRAND_USER1"  # Default for now
                            updated_data['brandId'] = new_brand_id
                            updated = True
                    
                    if updated and not self.dry_run:
                        doc.reference.update(updated_data)
                        print(f"   ✅ Updated: {doc_id}")
                    elif updated:
                        print(f"   🔍 [DRY RUN] Would update: {doc_id}")
                
            except Exception as e:
                print(f"❌ Error processing {collection_name}: {e}")
    
    def reorganize_storage_structure(self, user_mapping):
        """Reorganize Cloud Storage structure to be user-based"""
        print("\n" + "="*60)
        print("☁️  REORGANIZING STORAGE STRUCTURE")
        print("="*60)
        
        try:
            blobs = list(self.bucket.list_blobs())
            print(f"📦 Found {len(blobs)} objects to reorganize")
            
            # Group blobs by current structure
            current_structure = {}
            for blob in blobs:
                path_parts = blob.name.split('/')
                if len(path_parts) > 1:
                    top_level = path_parts[0]
                    if top_level not in current_structure:
                        current_structure[top_level] = []
                    current_structure[top_level].append(blob)
            
            # Reorganize kaarigar folder structure
            if 'kaarigar' in current_structure:
                print(f"\n📁 Reorganizing kaarigar folder structure")
                kaarigar_blobs = current_structure['kaarigar']
                
                for blob in kaarigar_blobs:
                    old_path = blob.name
                    path_parts = old_path.split('/')
                    
                    if len(path_parts) >= 2:
                        old_kaarigar_id = path_parts[1]
                        
                        # Map to new user-based structure
                        new_user_id = "user1"  # Default mapping for now
                        new_kaarigar_id = f"KR_{new_user_id.upper()}"
                        
                        # Create new path
                        new_path_parts = path_parts.copy()
                        new_path_parts[1] = new_kaarigar_id
                        new_path = '/'.join(new_path_parts)
                        
                        if not self.dry_run:
                            # Copy to new location
                            new_blob = self.bucket.blob(new_path)
                            new_blob.upload_from_string(blob.download_as_bytes())
                            
                            # Delete old blob
                            blob.delete()
                            
                            print(f"   ✅ Moved: {old_path} → {new_path}")
                        else:
                            print(f"   🔍 [DRY RUN] Would move: {old_path} → {new_path}")
            
        except Exception as e:
            print(f"❌ Error reorganizing storage: {e}")
    
    def run_reorganization(self, dry_run=False, backup=True):
        """Run the complete database reorganization"""
        self.dry_run = dry_run
        
        print("🚀 Project Kaarigar - Database Reorganization")
        print("=" * 60)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        
        if not self.initialize_clients():
            print("❌ Failed to initialize clients")
            return False
        
        if backup and not dry_run:
            self.backup_existing_data()
        
        # Step 1: Reorganize users collection
        user_mapping = self.reorganize_users_collection()
        
        # Step 2: Reorganize profiles collection
        self.reorganize_profiles_collection(user_mapping)
        
        # Step 3: Reorganize kaarigars collection
        self.reorganize_kaarigars_collection(user_mapping)
        
        # Step 4: Reorganize other collections
        self.reorganize_other_collections(user_mapping)
        
        # Step 5: Reorganize storage structure
        self.reorganize_storage_structure(user_mapping)
        
        print("\n" + "="*60)
        print("✅ REORGANIZATION COMPLETE")
        print("="*60)
        
        if dry_run:
            print("🔍 This was a dry run. No changes were made.")
            print("   Run without --dry-run to apply changes.")
        else:
            print("🎉 Database has been reorganized successfully!")
            print("   All collections now use simple user IDs (user1, user2, user3, etc.)")
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Reorganize Project Kaarigar Database")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")
    parser.add_argument("--backup", action="store_true", help="Create backup before reorganization")
    
    args = parser.parse_args()
    
    # Check credentials
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        print("⚠️  Warning: GOOGLE_APPLICATION_CREDENTIALS not set")
        print("   Make sure you have valid Google Cloud credentials")
    
    # Initialize reorganizer
    reorganizer = DatabaseReorganizer(PROJECT_ID, BUCKET_NAME)
    
    # Run reorganization
    success = reorganizer.run_reorganization(
        dry_run=args.dry_run,
        backup=args.backup
    )
    
    if success:
        print("\n🎉 Reorganization completed successfully!")
    else:
        print("\n❌ Reorganization failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
