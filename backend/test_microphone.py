#!/usr/bin/env python3
"""
Test script to verify microphone and STT functionality.
This script tests the ElevenLabs STT API with a sample audio file.
"""

import os
import requests
import base64

# Configuration
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ELEVEN_STT_URL = os.environ.get("ELEVEN_STT_URL", "https://api.elevenlabs.io/v1/speech-to-text")

def test_stt_with_sample_audio():
    """Test STT with a sample audio file"""
    print("🧪 Testing ElevenLabs STT API")
    print("=" * 50)
    
    # Check if we have a sample audio file
    sample_audio_path = "sample_audio.wav"
    if not os.path.exists(sample_audio_path):
        print(f"❌ Sample audio file not found: {sample_audio_path}")
        print("Please create a sample audio file or use the frontend to record audio.")
        return
    
    try:
        # Read the sample audio file
        with open(sample_audio_path, "rb") as f:
            audio_bytes = f.read()
        
        print(f"📁 Audio file size: {len(audio_bytes)} bytes")
        
        # Test STT API
        headers = {"xi-api-key": ELEVENLABS_API_KEY}
        files = {"file": ("sample_audio.wav", audio_bytes, "application/octet-stream")}
        data = {"model_id": "scribe_v1"}
        
        print("🎤 Sending audio to ElevenLabs STT...")
        response = requests.post(ELEVEN_STT_URL, headers=headers, files=files, data=data, timeout=60)
        
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ STT Success!")
            print(f"📝 Transcribed text: {result.get('text', 'No text found')}")
            print(f"🔍 Full response: {result}")
        else:
            print(f"❌ STT Failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing STT: {e}")

def test_api_connectivity():
    """Test basic API connectivity"""
    print("\n🌐 Testing API Connectivity")
    print("=" * 30)
    
    try:
        # Test basic connectivity
        response = requests.get("https://api.elevenlabs.io/v1/voices", 
                              headers={"xi-api-key": ELEVENLABS_API_KEY}, 
                              timeout=10)
        
        if response.status_code == 200:
            print("✅ ElevenLabs API is accessible")
            voices = response.json()
            print(f"📊 Available voices: {len(voices.get('voices', []))}")
        else:
            print(f"❌ API connectivity issue: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API connectivity error: {e}")

if __name__ == "__main__":
    print("🎤 Microphone and STT Test")
    print("=" * 50)
    
    # Test API connectivity first
    test_api_connectivity()
    
    # Test STT if sample audio exists
    test_stt_with_sample_audio()
    
    print("\n" + "=" * 50)
    print("🎯 Test completed!")
    print("\n💡 Tips for better voice recognition:")
    print("1. Speak clearly and at normal volume")
    print("2. Minimize background noise")
    print("3. Record for at least 1-2 seconds")
    print("4. Use a good quality microphone")
    print("5. Ensure stable internet connection")
