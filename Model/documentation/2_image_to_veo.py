#!/usr/bin/env python3
"""
Simple Image to Veo Video Converter
Takes an image path from terminal and converts it to a Veo video
"""

import os
import sys
import time
from pathlib import Path
from google import genai
from google.genai import types

# Configuration
PROJECT_ID = "karigar-475215"
LOCATION = "us-central1"

# Initialize client
client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

def optimize_prompt_with_gemini(user_prompt: str, image_path: str) -> str:
    """
    Use Gemini to optimize the user's prompt for Veo video generation
    
    Args:
        user_prompt: User's text prompt
        image_path: Path to the image for context
        
    Returns:
        Optimized prompt for Veo
    """
    try:
        # Read image for context
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        # Determine MIME type
        file_ext = Path(image_path).suffix.lower()
        mime_type = "image/jpeg" if file_ext in ['.jpg', '.jpeg'] else "image/png"
        
        gemini_prompt = f"""
        You are an expert video prompt engineer for Google's Veo 3.1 model. 
        
        The user wants to create a video from an image with this prompt: "{user_prompt}"
        
        Analyze the provided image and create an optimized prompt for Veo video generation that:
        1. Incorporates the user's request
        2. Adds cinematic motion and camera movements
        3. Includes visual effects and atmosphere
        4. Specifies camera angles and movements
        5. Adds temporal elements (slow motion, time effects, etc.)
        6. Is optimized for 9:16 vertical video format
        
        Focus on:
        - Camera movements (zoom, pan, tilt, dolly, etc.)
        - Subject animation and motion
        - Environmental effects (lighting, atmosphere, weather)
        - Cinematic style and mood
        - Visual storytelling elements
        
        Output ONLY the optimized prompt, no explanations or additional text.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[gemini_prompt, types.Part.from_bytes(data=image_bytes, mime_type=mime_type)],
        )
        
        optimized_prompt = response.text.strip()
        print(f"🤖 Gemini optimized prompt: {optimized_prompt}")
        return optimized_prompt
        
    except Exception as e:
        print(f"⚠️  Gemini optimization failed: {e}")
        # Fallback to enhanced user prompt
        fallback_prompt = f"{user_prompt}. Add cinematic motion, camera movement, and atmospheric effects to bring the image to life."
        print(f"🔄 Using fallback prompt: {fallback_prompt}")
        return fallback_prompt

def convert_image_to_video(image_path: str, user_prompt: str, output_name: str = None):
    """
    Convert local image to Veo video with user's text prompt
    
    Args:
        image_path: Path to the local image file
        user_prompt: User's text description for the video
        output_name: Name for output video (optional)
    """
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"❌ Image file not found: {image_path}")
        return False
    
    # Get image info
    image_name = Path(image_path).stem
    image_ext = Path(image_path).suffix.lower()
    
    # Determine MIME type
    mime_type = "image/jpeg" if image_ext in ['.jpg', '.jpeg'] else "image/png"
    
    # Set output name
    if not output_name:
        output_name = f"{image_name}_veo_video.mp4"
    
    print(f"🎬 Converting image to video...")
    print(f"📁 Input: {image_path}")
    print(f"📁 Output: {output_name}")
    print(f"📊 MIME Type: {mime_type}")
    print(f"💭 User prompt: {user_prompt}")
    
    try:
        # Read image file
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        
        print(f"📥 Image loaded: {len(image_bytes) / 1024:.1f} KB")
        
        # Optimize prompt with Gemini
        print(f"🤖 Optimizing prompt with Gemini...")
        optimized_prompt = optimize_prompt_with_gemini(user_prompt, image_path)
        
        # Create video generation request using the most reliable method
        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=optimized_prompt,
            image=types.Image.from_file(location=image_path),
            config=types.GenerateVideosConfig(
                aspect_ratio="9:16",  # Vertical for reels
                number_of_videos=1,
                duration_seconds=6,
                resolution="1080p",
                person_generation="allow_adult",
                enhance_prompt=True,
                generate_audio=True,
            ),
        )
        
        print(f"⏳ Video generation started...")
        print(f"🔄 This may take 2-5 minutes...")
        
        # Wait for completion
        while not operation.done:
            time.sleep(15)
            operation = client.operations.get(operation)
            print(f"⏳ Still generating... (checking every 15 seconds)")
        
        if operation.response:
            result = operation.result
            video_bytes = result.generated_videos[0].video.video_bytes
            
            # Save video to current directory
            with open(output_name, "wb") as f:
                f.write(video_bytes)
            
            print(f"✅ Video generated successfully!")
            print(f"📁 Saved as: {output_name}")
            print(f"📊 Video size: {len(video_bytes) / (1024*1024):.1f} MB")
            
            return True
        else:
            print(f"❌ Video generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    print("🎬 Image to Veo Video Converter with AI Prompt Optimization")
    print("=" * 60)
    
    # Get image path from command line or user input
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = input("Enter path to image file: ").strip()
    
    if not image_path:
        print("❌ No image path provided")
        return
    
    # Get text prompt from command line or user input
    if len(sys.argv) > 2:
        user_prompt = sys.argv[2]
    else:
        user_prompt = input("Enter your text prompt for the video: ").strip()
    
    if not user_prompt:
        print("❌ No text prompt provided")
        return
    
    # Get output name (optional)
    output_name = None
    if len(sys.argv) > 3:
        output_name = sys.argv[3]
    
    # Convert image to video with optimized prompt
    success = convert_image_to_video(image_path, user_prompt, output_name)
    
    if success:
        print("\n🎉 Conversion completed successfully!")
    else:
        print("\n❌ Conversion failed!")

if __name__ == "__main__":
    main()
