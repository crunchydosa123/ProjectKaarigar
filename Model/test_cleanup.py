#!/usr/bin/env python3
"""
Test script to verify temporary file cleanup
"""

import os
import tempfile
from pathlib import Path

def test_temp_cleanup():
    """Test that temporary files are properly cleaned up"""
    print("🧪 Testing temporary file cleanup...")
    
    # Create some test temporary files
    temp_files = []
    for i in range(3):
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_file.write(b"test video data")
        temp_file.close()
        temp_files.append(temp_file.name)
        print(f"Created temp file: {os.path.basename(temp_file.name)}")
    
    # Check files exist
    print(f"\n📁 Created {len(temp_files)} temporary files")
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            size = os.path.getsize(temp_file)
            print(f"  ✅ {os.path.basename(temp_file)} exists ({size} bytes)")
    
    # Simulate cleanup
    print(f"\n🗑️  Cleaning up temporary files...")
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                print(f"  ✅ Cleaned up: {os.path.basename(temp_file)}")
        except Exception as e:
            print(f"  ❌ Failed to clean up {temp_file}: {e}")
    
    # Verify cleanup
    print(f"\n🔍 Verifying cleanup...")
    remaining_files = []
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            remaining_files.append(temp_file)
            print(f"  ❌ Still exists: {os.path.basename(temp_file)}")
        else:
            print(f"  ✅ Successfully removed: {os.path.basename(temp_file)}")
    
    if not remaining_files:
        print(f"\n✅ All temporary files successfully cleaned up!")
        return True
    else:
        print(f"\n❌ {len(remaining_files)} files still remain")
        return False

if __name__ == "__main__":
    test_temp_cleanup()
