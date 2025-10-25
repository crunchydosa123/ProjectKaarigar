#!/usr/bin/env python3
"""
Startup script for GCS Video Editor Flask API
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'flask',
        'flask_cors',
        'ffmpeg',
        'google.generativeai',
        'google.cloud.storage',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install them using:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def check_gcs_setup():
    """Check if Google Cloud Storage is properly configured"""
    try:
        from google.cloud import storage
        client = storage.Client()
        # Try to list buckets to verify credentials
        list(client.list_buckets())
        print("✅ Google Cloud Storage is properly configured")
        return True
    except Exception as e:
        print(f"⚠️  Google Cloud Storage setup issue: {e}")
        print("💡 Make sure you have:")
        print("   1. Google Cloud credentials configured")
        print("   2. Service account with Storage permissions")
        print("   3. GOOGLE_APPLICATION_CREDENTIALS environment variable set")
        return False

def main():
    """Main startup function"""
    print("🎬 GCS Video Editor Flask API")
    print("=" * 40)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    # Check GCS setup
    print("☁️  Checking Google Cloud Storage setup...")
    gcs_ok = check_gcs_setup()
    
    if not gcs_ok:
        print("\n⚠️  Warning: GCS setup issues detected. The API may not work properly.")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            sys.exit(1)
    
    # Start the Flask app
    print("\n🚀 Starting Flask API server...")
    print("📋 Available endpoints:")
    print("   GET  /health - Health check")
    print("   POST /upload - Upload video file")
    print("   POST /edit - Apply edits to video")
    print("   GET  /trending-songs - Get trending songs")
    print("   GET  /edited-videos - List edited videos")
    print("   POST /video-info - Get video information")
    print("   POST /save-video - Save video to GCS")
    print("   GET  /download/<blob_name> - Download video")
    print("\n🌐 API will be available at: http://localhost:5000")
    print("📖 API Documentation: API_DOCUMENTATION.md")
    print("🧪 Test the API: python test_api.py")
    print("\n" + "=" * 40)
    
    # Import and run the Flask app
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
    except Exception as e:
        print(f"\n❌ Error starting Flask app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

