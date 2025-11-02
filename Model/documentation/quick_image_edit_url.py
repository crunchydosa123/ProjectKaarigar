"""
Quick Image-to-Image Generator from URL
Simple script to edit images from URLs using Gemini
"""

import os
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import requests

# Initialize Gemini
client = genai.Client(api_key=os.environ.get("GENAI_API_KEY"))

# ============================================================================
# YOUR INPUTS - MODIFY THESE
# ============================================================================

# Image URL (can be from Google Cloud Storage, any public URL, etc.)
IMAGE_URL = "https://storage.googleapis.com/all_in_one_bucket1/kaarigar/KR_USER1/generated_images/edited_c0f8c71c-c87e-47d7-aee4-588c4686312d.png"

# What do you want to do with the image?
EDIT_PROMPT = "Add a McDonald's logo in the top-right corner, make it look natural"

# Output filename
OUTPUT_FILE = "edited_output.png"

# ============================================================================
# SCRIPT
# ============================================================================

print("🎨 Gemini Image-to-Image Editor (URL Input)")
print("=" * 60)

# Download image from URL
print(f"\n📥 Downloading image from URL...")
print(f"   {IMAGE_URL[:80]}...")

try:
    response = requests.get(IMAGE_URL, timeout=30)
    response.raise_for_status()  # Raise error for bad status codes
    
    print(f"✅ Response received:")
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.headers.get('Content-Type', 'unknown')}")
    print(f"   Content-Length: {len(response.content)} bytes")
    
    # Check if it's actually an image
    content_type = response.headers.get('Content-Type', '').lower()
    if 'image' not in content_type and 'octet-stream' not in content_type:
        print(f"⚠️ Warning: Content-Type is not an image: {content_type}")
        # Print first 200 chars to see what we got
        print(f"📄 Content preview: {response.content[:200]}")
    
    # Try to open as image
    image = Image.open(BytesIO(response.content))
    print(f"✅ Image loaded: {image.size[0]}x{image.size[1]} pixels, format: {image.format}")
    
except requests.exceptions.RequestException as e:
    print(f"❌ Failed to download image: {e}")
    exit(1)
except Exception as e:
    print(f"❌ Failed to load image: {e}")
    print(f"   Content-Type: {response.headers.get('Content-Type')}")
    print(f"   First 500 bytes: {response.content[:500]}")
    exit(1)

# Edit with Gemini
print(f"\n🤖 Editing with Gemini...")
print(f"   Prompt: {EDIT_PROMPT}")

result = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[EDIT_PROMPT, image],
    config=types.GenerateContentConfig(max_output_tokens=1000)
)

# Save result
print(f"\n💾 Saving result...")

for part in result.candidates[0].content.parts:
    if part.inline_data is not None:
        edited = Image.open(BytesIO(part.inline_data.data))
        edited.save(OUTPUT_FILE)
        print(f"✅ Saved to: {OUTPUT_FILE}")
        print(f"   Size: {edited.size[0]}x{edited.size[1]} pixels")
        break
else:
    print("❌ No image in response")

print("\n" + "=" * 60)
print("✅ DONE!")
