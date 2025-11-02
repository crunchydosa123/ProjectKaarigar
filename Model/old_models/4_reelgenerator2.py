# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Veo 3 Video Generation Model
Google's cutting-edge video generation with stunning detail and realistic physics.
Supports text-to-video and image-to-video generation with audio.
"""

import os
import time
import base64
import io
from typing import Optional, Dict, Any, List
from pathlib import Path
import requests
from google import genai
from google.genai import types
from google.cloud import storage


class Veo3ReelGenerator:
    """Veo 3 Video Generation Model for creating high-quality videos"""
    
    def __init__(self, project_id: str = None, location: str = "us-central1"):
        """
        Initialize Veo 3 Reel Generator
        
        Args:
            project_id: Google Cloud Project ID
            location: Google Cloud region
        """
        # Use the same project ID as reel_model.py
        self.project_id = project_id or "karigar-475215"
        self.location = location
        
        # Initialize client with same configuration as reel_model.py
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location
        )
        
        # Model configurations
        self.video_model = "veo-3.1-generate-preview"
        self.video_model_fast = "veo-3.1-fast-generate-preview"
        self.gemini_model = "gemini-2.5-flash"
        
        # Initialize GCS client for file operations
        self.storage_client = storage.Client()
        
        # Use same bucket configuration as reel_model.py
        self.video_bucket = "gs://all_in_one_bucket1/reels"
        self.local_dir = "./segments"
        os.makedirs(self.local_dir, exist_ok=True)
    
    def download_from_gcs(self, gcs_uri: str, local_path: str):
        """Download file from GCS to local path"""
        from urllib.parse import urlparse
        parsed = urlparse(gcs_uri)
        bucket_name = parsed.netloc
        blob_name = parsed.path.lstrip("/")

        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.download_to_filename(local_path)
        print(f"Downloaded {gcs_uri} -> {local_path}")
    
    def upload_file_to_gcs(self, local_path: str, dest_bucket_gs_uri_prefix: str) -> str:
        """
        Upload local file to GCS and return gs://... URI.
        dest_bucket_gs_uri_prefix example: 'gs://my-bucket/prefix'
        """
        assert dest_bucket_gs_uri_prefix.startswith("gs://"), "dest_bucket_gs_uri_prefix must start with gs://"
        parts = dest_bucket_gs_uri_prefix[5:].split("/", 1)
        bucket_name = parts[0]
        prefix = parts[1] if len(parts) > 1 else ""
        blob_name = f"{prefix.rstrip('/')}/{Path(local_path).name}".lstrip("/")

        bucket = self.storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_path)
        gs_uri = f"gs://{bucket_name}/{blob_name}"
        print(f"Uploaded {local_path} -> {gs_uri}")
        return gs_uri
        
    def optimize_text_prompt(self, subject: str, action: str, scene: str, 
                           camera_angle: str = "None", camera_movement: str = "None",
                           lens_effects: str = "None", style: str = "None",
                           temporal_elements: str = "None", sound_effects: str = "None",
                           dialogue: str = "") -> str:
        """
        Optimize text prompt using Gemini for better video generation
        
        Args:
            subject: The "who" or "what" of the video
            action: Describe movements, interactions, etc.
            scene: The "where" and "when" of the video
            camera_angle: Camera angle (e.g., "Over-the-Shoulder Shot")
            camera_movement: Camera movement (e.g., "Zoom (In)")
            lens_effects: Lens effects (e.g., "Wide-Angle Lens")
            style: Video style (e.g., "Cinematic")
            temporal_elements: Time effects (e.g., "Slow-motion")
            sound_effects: Audio effects (e.g., "Ticking clock")
            dialogue: Spoken dialogue
            
        Returns:
            Optimized prompt string
        """
        prompt = ""
        
        keywords = [subject, action, scene]
        optional_keywords = [
            camera_angle,
            camera_movement,
            lens_effects,
            style,
            temporal_elements,
            sound_effects,
        ]
        
        for keyword in optional_keywords:
            if keyword != "None":
                keywords.append(keyword)
        
        if dialogue != "":
            keywords.append(dialogue)
        
        gemini_prompt = f"""
        You are an expert video prompt engineer for Google's Veo model. Your task is to construct the most effective and optimal prompt string using the following keywords. Every single keyword MUST be included. Synthesize them into a single, cohesive, and cinematic instruction. Do not add any new core concepts. Output ONLY the final prompt string, without any introduction or explanation. Mandatory Keywords: {",".join(keywords)}
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.gemini_model,
                contents=gemini_prompt,
            )
            prompt = response.text.strip()
            return prompt
        except Exception as e:
            print(f"Error optimizing prompt: {e}")
            # Fallback to simple concatenation
            return f"{subject} {action} {scene}"
    
    def optimize_image_prompt(self, image_path: str, camera_motion: str = "None",
                            subject_animation: str = "None", environmental_animation: str = "None",
                            sound_effects: str = "None", dialogue: str = "") -> str:
        """
        Optimize image-to-video prompt using Gemini with local image
        
        Args:
            image_path: Path to the local image file
            camera_motion: Camera movement
            subject_animation: Subject movement
            environmental_animation: Background movement
            sound_effects: Audio effects
            dialogue: Spoken dialogue
            
        Returns:
            Optimized prompt string
        """
        keywords = []
        optional_keywords = [
            camera_motion,
            subject_animation,
            environmental_animation,
            sound_effects,
        ]
        
        for keyword in optional_keywords:
            if keyword != "None":
                keywords.append(keyword)
        
        if dialogue != "":
            keywords.append(dialogue)
        
        gemini_prompt = f"""
        You are an expert prompt engineer for Google's Veo model. Analyze the provided image and combine its content with the following motion and audio keywords to generate a single, cohesive, and cinematic prompt. Integrate the image's subject and scene with the requested motion and audio effects. The final output must be ONLY the prompt itself, with no preamble. Mandatory Keywords: {",".join(keywords)}
        """
        
        try:
            if not os.path.exists(image_path):
                print(f"Image file not found: {image_path}")
                return "add subtle motion to the image"
            
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            # Determine MIME type based on file extension
            file_ext = Path(image_path).suffix.lower()
            mime_type = "image/jpeg" if file_ext in ['.jpg', '.jpeg'] else "image/png"
            
            response = self.client.models.generate_content(
                model=self.gemini_model,
                contents=[gemini_prompt, types.Part.from_bytes(data=image_bytes, mime_type=mime_type)],
            )
            
            return response.text.strip()
        except Exception as e:
            print(f"Error optimizing image prompt: {e}")
            return "add subtle motion to the image"
    
    def generate_text_to_video(self, prompt: str, aspect_ratio: str = "16:9",
                             number_of_videos: int = 1, duration_seconds: int = 6,
                             resolution: str = "1080p", enhance_prompt: bool = True,
                             generate_audio: bool = True, use_fast_model: bool = False,
                             output_gcs_uri: str = None) -> Dict[str, Any]:
        """
        Generate video from text prompt
        
        Args:
            prompt: Text description of the video
            aspect_ratio: Video aspect ratio ("16:9" or "9:16")
            number_of_videos: Number of videos to generate (1 or 2)
            duration_seconds: Video duration (4, 6, or 8 seconds)
            resolution: Video resolution ("1080p" or "720p")
            enhance_prompt: Whether to enhance the prompt
            generate_audio: Whether to generate audio
            use_fast_model: Whether to use the fast model
            output_gcs_uri: GCS URI for output storage
            
        Returns:
            Dictionary with video generation results
        """
        try:
            model = self.video_model_fast if use_fast_model else self.video_model
            
            config_params = {
                "aspect_ratio": aspect_ratio,
                "number_of_videos": number_of_videos,
                "duration_seconds": duration_seconds,
                "resolution": resolution,
                "person_generation": "allow_adult",
                "enhance_prompt": enhance_prompt,
                "generate_audio": generate_audio,
            }
            
            if output_gcs_uri:
                config_params["output_gcs_uri"] = output_gcs_uri
            
            operation = self.client.models.generate_videos(
                model=model,
                prompt=prompt,
                config=types.GenerateVideosConfig(**config_params),
            )
            
            # Wait for completion
            while not operation.done:
                time.sleep(15)
                operation = self.client.operations.get(operation)
                print(f"Video generation in progress... Status: {operation.metadata}")
            
            if operation.response:
                result = operation.result
                videos = []
                
                for generated_video in result.generated_videos:
                    video_data = {
                        "video_bytes": generated_video.video.video_bytes,
                        "uri": getattr(generated_video.video, 'uri', None),
                        "duration": duration_seconds,
                        "resolution": resolution,
                        "aspect_ratio": aspect_ratio
                    }
                    videos.append(video_data)
                
                return {
                    "success": True,
                    "videos": videos,
                    "operation_id": operation.name,
                    "model_used": model
                }
            else:
                return {
                    "success": False,
                    "error": "Video generation failed",
                    "operation_id": operation.name
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_image_to_video(self, image_path: str, prompt: str = None,
                              aspect_ratio: str = "16:9", number_of_videos: int = 1,
                              duration_seconds: int = 6, resolution: str = "1080p",
                              enhance_prompt: bool = True, generate_audio: bool = True,
                              use_fast_model: bool = False, output_gcs_uri: str = None) -> Dict[str, Any]:
        """
        Generate video from local image file
        
        Args:
            image_path: Path to the local image file
            prompt: Optional text prompt for motion
            aspect_ratio: Video aspect ratio ("16:9" or "9:16")
            number_of_videos: Number of videos to generate (1 or 2)
            duration_seconds: Video duration (4, 6, or 8 seconds)
            resolution: Video resolution ("1080p" or "720p")
            enhance_prompt: Whether to enhance the prompt
            generate_audio: Whether to generate audio
            use_fast_model: Whether to use the fast model
            output_gcs_uri: GCS URI for output storage
            
        Returns:
            Dictionary with video generation results
        """
        try:
            if not os.path.exists(image_path):
                return {
                    "success": False,
                    "error": f"Image file not found: {image_path}"
                }
            
            model = self.video_model_fast if use_fast_model else self.video_model
            
            config_params = {
                "aspect_ratio": aspect_ratio,
                "number_of_videos": number_of_videos,
                "duration_seconds": duration_seconds,
                "resolution": resolution,
                "person_generation": "allow_adult",
                "enhance_prompt": enhance_prompt,
                "generate_audio": generate_audio,
            }
            
            if output_gcs_uri:
                config_params["output_gcs_uri"] = output_gcs_uri
            
            # Use default prompt if none provided
            if not prompt:
                prompt = "add subtle motion to the image"
            
            # Read image file and create Image object from bytes
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            # Determine MIME type based on file extension
            file_ext = Path(image_path).suffix.lower()
            mime_type = "image/jpeg" if file_ext in ['.jpg', '.jpeg'] else "image/png"
            
            operation = self.client.models.generate_videos(
                model=model,
                prompt=prompt,
                image=types.Image.from_bytes(data=image_bytes, mime_type=mime_type),
                config=types.GenerateVideosConfig(**config_params),
            )
            
            # Wait for completion
            while not operation.done:
                time.sleep(15)
                operation = self.client.operations.get(operation)
                print(f"Video generation in progress... Status: {operation.metadata}")
            
            if operation.response:
                result = operation.result
                videos = []
                
                for generated_video in result.generated_videos:
                    video_data = {
                        "video_bytes": generated_video.video.video_bytes,
                        "uri": getattr(generated_video.video, 'uri', None),
                        "duration": duration_seconds,
                        "resolution": resolution,
                        "aspect_ratio": aspect_ratio
                    }
                    videos.append(video_data)
                
                return {
                    "success": True,
                    "videos": videos,
                    "operation_id": operation.name,
                    "model_used": model,
                    "source_image": image_path
                }
            else:
                return {
                    "success": False,
                    "error": "Video generation failed",
                    "operation_id": operation.name
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def save_video_to_file(self, video_bytes: bytes, output_path: str) -> bool:
        """
        Save video bytes to file
        
        Args:
            video_bytes: Video data as bytes
            output_path: Path to save the video
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, "wb") as f:
                f.write(video_bytes)
            
            print(f"Video saved to: {output_path}")
            return True
        except Exception as e:
            print(f"Error saving video: {e}")
            return False
    
    def upload_video_to_gcs(self, video_bytes: bytes, bucket_name: str, blob_name: str) -> str:
        """
        Upload video to Google Cloud Storage
        
        Args:
            video_bytes: Video data as bytes
            bucket_name: GCS bucket name
            blob_name: Blob name in the bucket
            
        Returns:
            GCS URI of the uploaded video
        """
        try:
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            blob.upload_from_string(video_bytes, content_type='video/mp4')
            
            # Try to make it public and get URL
            try:
                blob.make_public()
                return blob.public_url
            except:
                # Fallback to manual URL construction
                return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
                
        except Exception as e:
            print(f"Error uploading to GCS: {e}")
            return None
    
    def download_image_from_url(self, url: str, save_path: str) -> bool:
        """
        Download image from URL
        
        Args:
            url: Image URL
            save_path: Path to save the image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Image downloaded to: {save_path}")
            return True
        except Exception as e:
            print(f"Error downloading image: {e}")
            return False
    
    def create_reel_from_text(self, subject: str, action: str, scene: str,
                            output_path: str = None, **kwargs) -> Dict[str, Any]:
        """
        Create a reel from text description with optimized prompting
        
        Args:
            subject: The "who" or "what" of the video
            action: Describe movements, interactions, etc.
            scene: The "where" and "when" of the video
            output_path: Path to save the video (optional)
            **kwargs: Additional parameters for video generation
            
        Returns:
            Dictionary with video generation results
        """
        # Optimize the prompt
        optimized_prompt = self.optimize_text_prompt(
            subject=subject,
            action=action,
            scene=scene,
            camera_angle=kwargs.get('camera_angle', 'None'),
            camera_movement=kwargs.get('camera_movement', 'None'),
            lens_effects=kwargs.get('lens_effects', 'None'),
            style=kwargs.get('style', 'None'),
            temporal_elements=kwargs.get('temporal_elements', 'None'),
            sound_effects=kwargs.get('sound_effects', 'None'),
            dialogue=kwargs.get('dialogue', '')
        )
        
        print(f"Optimized prompt: {optimized_prompt}")
        
        # Generate video
        result = self.generate_text_to_video(
            prompt=optimized_prompt,
            aspect_ratio=kwargs.get('aspect_ratio', '9:16'),  # Default to vertical for reels
            number_of_videos=kwargs.get('number_of_videos', 1),
            duration_seconds=kwargs.get('duration_seconds', 6),
            resolution=kwargs.get('resolution', '1080p'),
            enhance_prompt=kwargs.get('enhance_prompt', True),
            generate_audio=kwargs.get('generate_audio', True),
            use_fast_model=kwargs.get('use_fast_model', False),
            output_gcs_uri=kwargs.get('output_gcs_uri')
        )
        
        # Save video if output path provided
        if result.get('success') and output_path and result.get('videos'):
            video_bytes = result['videos'][0]['video_bytes']
            self.save_video_to_file(video_bytes, output_path)
            result['saved_path'] = output_path
        
        return result
    
    def create_reel_from_image(self, image_path: str, output_path: str = None, **kwargs) -> Dict[str, Any]:
        """
        Create a reel from image with optimized prompting
        
        Args:
            image_path: Path to the starting image
            output_path: Path to save the video (optional)
            **kwargs: Additional parameters for video generation
            
        Returns:
            Dictionary with video generation results
        """
        # Optimize the prompt
        optimized_prompt = self.optimize_image_prompt(
            image_path=image_path,
            camera_motion=kwargs.get('camera_motion', 'None'),
            subject_animation=kwargs.get('subject_animation', 'None'),
            environmental_animation=kwargs.get('environmental_animation', 'None'),
            sound_effects=kwargs.get('sound_effects', 'None'),
            dialogue=kwargs.get('dialogue', '')
        )
        
        print(f"Optimized prompt: {optimized_prompt}")
        
        # Generate video
        result = self.generate_image_to_video(
            image_path=image_path,
            prompt=optimized_prompt,
            aspect_ratio=kwargs.get('aspect_ratio', '9:16'),  # Default to vertical for reels
            number_of_videos=kwargs.get('number_of_videos', 1),
            duration_seconds=kwargs.get('duration_seconds', 6),
            resolution=kwargs.get('resolution', '1080p'),
            enhance_prompt=kwargs.get('enhance_prompt', True),
            generate_audio=kwargs.get('generate_audio', True),
            use_fast_model=kwargs.get('use_fast_model', False),
            output_gcs_uri=kwargs.get('output_gcs_uri')
        )
        
        # Save video if output path provided
        if result.get('success') and output_path and result.get('videos'):
            video_bytes = result['videos'][0]['video_bytes']
            self.save_video_to_file(video_bytes, output_path)
            result['saved_path'] = output_path
        
        return result


def main():
    """Example usage of Veo3ReelGenerator"""
    
    # Initialize the generator
    generator = Veo3ReelGenerator()
    
    # Example 1: Create a reel from text
    print("Creating reel from text...")
    text_result = generator.create_reel_from_text(
        subject="a detective",
        action="interrogating a rubber duck",
        scene="in a dark interview room",
        camera_angle="Over-the-Shoulder Shot",
        camera_movement="Zoom (In)",
        style="Cinematic",
        sound_effects="Ticking clock",
        dialogue="Where were you last night?",
        output_path="outputs/detective_reel.mp4"
    )
    
    if text_result.get('success'):
        print("✅ Text-to-video reel created successfully!")
        print(f"Model used: {text_result.get('model_used')}")
        print(f"Saved to: {text_result.get('saved_path')}")
    else:
        print(f"❌ Text-to-video failed: {text_result.get('error')}")
    
    # Example 2: Create a reel from local image
    print("\nCreating reel from local image...")
    
    # Use a local image file (you can provide any local image path)
    local_image_path = "path/to/your/local/image.jpg"  # Replace with your image path
    
    # Check if image exists, if not, download a sample
    if not os.path.exists(local_image_path):
        print("Local image not found, downloading sample...")
        sample_image_path = "temp/flowers.png"
        if generator.download_image_from_url(
            "https://storage.googleapis.com/cloud-samples-data/generative-ai/image/flowers.png",
            sample_image_path
        ):
            local_image_path = sample_image_path
        else:
            print("❌ Could not download sample image")
            return
    
    image_result = generator.create_reel_from_image(
        image_path=local_image_path,
        camera_motion="Zoom (In)",
        environmental_animation="Light changes subtly",
        output_path="outputs/local_image_reel.mp4"
    )
    
    if image_result.get('success'):
        print("✅ Image-to-video reel created successfully!")
        print(f"Model used: {image_result.get('model_used')}")
        print(f"Saved to: {image_result.get('saved_path')}")
    else:
        print(f"❌ Image-to-video failed: {image_result.get('error')}")


if __name__ == "__main__":
    main()
