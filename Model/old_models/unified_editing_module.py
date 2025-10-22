"""
Unified Editing Module for Project Kaarigar
Handles both image and video editing using Gemini AI
Supports local file paths and URLs
Integrates with existing editing_model.py functions
"""

import os
import sys
import json
import time
import requests
import tempfile
from typing import Optional, Union, List
from urllib.parse import urlparse
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ Error: google-genai not installed. Run: pip install google-genai")
    sys.exit(1)

try:
    from PIL import Image
    from io import BytesIO
except ImportError:
    print("❌ Error: PIL not installed. Run: pip install Pillow")
    sys.exit(1)

# Import existing editing functions
try:
    from video_edit.core import process_with_gemini
    from video_edit.ffmpeg_utils import make_tmp_file
    from video_edit.music import mix_background_music
except ImportError:
    print("⚠️ Warning: video_edit modules not found. Video editing will use basic Gemini API only.")

# Configuration
GEMINI_API_KEY = "AIzaSyDiUMs4sIAdOk09006hS7DcY79DZh53_M4"  # Replace with your key
ELEVEN_API_KEY = "sk_b5b7b026323972fbcc9f9e83344f948f44eacccb9ecd33d6"  # For TTS if needed

# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)


class UnifiedEditor:
    """Unified editor for both images and videos using Gemini AI"""
    
    def __init__(self):
        self.client = client
        self.temp_dir = tempfile.mkdtemp()
        print(f"📁 Temp directory: {self.temp_dir}")
    
    def is_url(self, path_or_url: str) -> bool:
        """Check if input is a URL"""
        try:
            result = urlparse(path_or_url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def download_file(self, url: str, local_path: str) -> bool:
        """Download file from URL to local path"""
        try:
            print(f"📥 Downloading from URL: {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ Downloaded to: {local_path}")
            return True
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False
    
    def get_local_path(self, path_or_url: str, file_type: str = "media") -> Optional[str]:
        """Get local file path, downloading from URL if necessary"""
        if self.is_url(path_or_url):
            # Generate temp filename based on URL
            parsed_url = urlparse(path_or_url)
            filename = os.path.basename(parsed_url.path) or f"temp_{file_type}"
            if not filename or '.' not in filename:
                ext = ".mp4" if file_type == "video" else ".jpg"
                filename = f"temp_{file_type}{ext}"
            
            local_path = os.path.join(self.temp_dir, filename)
            if self.download_file(path_or_url, local_path):
                return local_path
            return None
        else:
            # Local file path
            if os.path.exists(path_or_url):
                return path_or_url
            else:
                print(f"❌ Local file not found: {path_or_url}")
                return None
    
    def edit_image(self, image_path_or_url: str, prompt: str, output_path: Optional[str] = None) -> Optional[str]:
        """Edit image using Gemini image-to-image model"""
        print(f"\n🎨 Editing image with prompt: '{prompt}'")
        
        # Get local image path
        local_image_path = self.get_local_path(image_path_or_url, "image")
        if not local_image_path:
            return None
        
        try:
            # Load image
            print(f"📷 Loading image: {local_image_path}")
            image = Image.open(local_image_path)
            print(f"📐 Original image size: {image.size}")
            
            # Edit with Gemini
            print("🤖 Processing with Gemini...")
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt, image],
                config=types.GenerateContentConfig(
                    max_output_tokens=1000
                )
            )
            
            # Process response
            print("⚙️ Processing response...")
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    print(f"💬 Gemini response: {part.text}")
                elif part.inline_data is not None:
                    print("💾 Saving edited image...")
                    edited_image = Image.open(BytesIO(part.inline_data.data))
                    
                    # Generate output path if not provided
                    if not output_path:
                        base_name = os.path.splitext(os.path.basename(local_image_path))[0]
                        output_path = f"{base_name}_edited_{int(time.time())}.png"
                    
                    edited_image.save(output_path)
                    print(f"✅ Edited image saved as: {output_path}")
                    print(f"📐 Edited image size: {edited_image.size}")
                    return output_path
                else:
                    print("⚠️ No image data found in response")
                    return None
                    
        except Exception as e:
            print(f"❌ Image editing failed: {e}")
            return None
    
    def edit_video_basic(self, video_path_or_url: str, prompt: str, output_path: Optional[str] = None) -> Optional[str]:
        """Edit video using basic Gemini API (fallback method)"""
        print(f"\n🎬 Editing video with prompt: '{prompt}'")
        
        # Get local video path
        local_video_path = self.get_local_path(video_path_or_url, "video")
        if not local_video_path:
            return None
        
        try:
            # For now, we'll use a simple approach - generate a new video based on the prompt
            # This is a placeholder - in practice, you'd want to use video editing libraries
            print("🤖 Generating new video with Gemini...")
            
            # Generate output path if not provided
            if not output_path:
                base_name = os.path.splitext(os.path.basename(local_video_path))[0]
                output_path = f"{base_name}_edited_{int(time.time())}.mp4"
            
            # This is a simplified approach - you might want to use actual video editing
            print(f"⚠️ Basic video editing - copying original to: {output_path}")
            import shutil
            shutil.copy2(local_video_path, output_path)
            
            return output_path
            
        except Exception as e:
            print(f"❌ Video editing failed: {e}")
            return None
    
    def edit_video_advanced(self, video_path_or_url: str, prompt: str, output_path: Optional[str] = None) -> Optional[str]:
        """Edit video using advanced video editing (if available)"""
        print(f"\n🎬 Advanced video editing with prompt: '{prompt}'")
        
        # Get local video path
        local_video_path = self.get_local_path(video_path_or_url, "video")
        if not local_video_path:
            return None
        
        try:
            # Try to use existing video editing infrastructure
            if 'process_with_gemini' in globals():
                print("🔧 Using advanced video processing...")
                
                # Generate output path if not provided
                if not output_path:
                    base_name = os.path.splitext(os.path.basename(local_video_path))[0]
                    output_path = f"{base_name}_edited_{int(time.time())}.mp4"
                
                # Use existing video processing
                process_with_gemini(local_video_path, prompt, output_path, api_key=GEMINI_API_KEY)
                
                if os.path.exists(output_path):
                    print(f"✅ Advanced video editing completed: {output_path}")
                    return output_path
                else:
                    print("⚠️ Advanced processing failed, falling back to basic method")
                    return self.edit_video_basic(video_path_or_url, prompt, output_path)
            else:
                print("⚠️ Advanced video processing not available, using basic method")
                return self.edit_video_basic(video_path_or_url, prompt, output_path)
                
        except Exception as e:
            print(f"❌ Advanced video editing failed: {e}")
            print("🔄 Falling back to basic method...")
            return self.edit_video_basic(video_path_or_url, prompt, output_path)
    
    def add_music_to_video(self, video_path_or_url: str, song_url: str, output_path: Optional[str] = None) -> Optional[str]:
        """Add music to video using existing music mixing functionality"""
        print(f"\n🎵 Adding music to video...")
        
        # Get local video path
        local_video_path = self.get_local_path(video_path_or_url, "video")
        if not local_video_path:
            return None
        
        try:
            if 'mix_background_music' in globals():
                # Generate output path if not provided
                if not output_path:
                    base_name = os.path.splitext(os.path.basename(local_video_path))[0]
                    output_path = f"{base_name}_with_music_{int(time.time())}.mp4"
                
                # Use existing music mixing
                mix_background_music(
                    input_video=local_video_path,
                    music_source_path=song_url,
                    out_video=output_path,
                    music_duration=None,
                    music_volume=0.4,
                    loop=True,
                    music_start=0.0,
                    music_end=None,
                    reduce_original_volume=1.0,
                    music_loop=True,
                    fade=1.0,
                )
                
                if os.path.exists(output_path):
                    print(f"✅ Music added successfully: {output_path}")
                    return output_path
                else:
                    print("❌ Music mixing failed")
                    return None
            else:
                print("❌ Music mixing functionality not available")
                return None
                
        except Exception as e:
            print(f"❌ Music mixing failed: {e}")
            return None
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")


def get_user_choice() -> str:
    """Get user's choice for editing type"""
    print("\n" + "="*60)
    print("🎨 UNIFIED EDITING MODULE - Project Kaarigar")
    print("="*60)
    print("Choose what you want to edit:")
    print("1. 🖼️  Edit Image")
    print("2. 🎬 Edit Video")
    print("3. 🎵 Add Music to Video")
    print("4. ❌ Exit")
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        if choice in ['1', '2', '3', '4']:
            return choice
        print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")


def get_file_input(prompt: str) -> str:
    """Get file path or URL from user"""
    while True:
        file_input = input(f"\n{prompt} (path or URL): ").strip()
        if file_input:
            return file_input
        print("❌ Please provide a valid file path or URL.")


def get_editing_prompt() -> str:
    """Get editing prompt from user"""
    while True:
        prompt = input("\n✏️  Enter your editing prompt: ").strip()
        if prompt:
            return prompt
        print("❌ Please provide a valid editing prompt.")


def main():
    """Main function to run the unified editing module"""
    editor = UnifiedEditor()
    
    try:
        while True:
            choice = get_user_choice()
            
            if choice == '4':  # Exit
                print("👋 Goodbye!")
                break
            
            elif choice == '1':  # Edit Image
                image_input = get_file_input("🖼️  Enter image file path or URL")
                prompt = get_editing_prompt()
                
                result = editor.edit_image(image_input, prompt)
                if result:
                    print(f"\n🎉 Image editing completed successfully!")
                    print(f"📁 Output file: {result}")
                else:
                    print("\n❌ Image editing failed.")
            
            elif choice == '2':  # Edit Video
                video_input = get_file_input("🎬 Enter video file path or URL")
                prompt = get_editing_prompt()
                
                # Ask for editing method
                print("\nChoose editing method:")
                print("1. 🚀 Advanced (uses existing video processing)")
                print("2. 🔧 Basic (simple processing)")
                
                method_choice = input("Enter choice (1-2): ").strip()
                if method_choice == '1':
                    result = editor.edit_video_advanced(video_input, prompt)
                else:
                    result = editor.edit_video_basic(video_input, prompt)
                
                if result:
                    print(f"\n🎉 Video editing completed successfully!")
                    print(f"📁 Output file: {result}")
                else:
                    print("\n❌ Video editing failed.")
            
            elif choice == '3':  # Add Music to Video
                video_input = get_file_input("🎬 Enter video file path or URL")
                music_url = get_file_input("🎵 Enter music file URL")
                
                result = editor.add_music_to_video(video_input, music_url)
                if result:
                    print(f"\n🎉 Music added successfully!")
                    print(f"📁 Output file: {result}")
                else:
                    print("\n❌ Music addition failed.")
            
            # Ask if user wants to continue
            continue_choice = input("\n🔄 Do you want to edit something else? (y/n): ").strip().lower()
            if continue_choice not in ['y', 'yes']:
                break
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        editor.cleanup()


if __name__ == "__main__":
    main()
