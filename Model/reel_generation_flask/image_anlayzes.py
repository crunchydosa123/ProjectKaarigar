"""
Image to Video Prompt Generator
Analyzes images and generates optimized prompts for video generation
Handles both single and multiple images
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime
from google import genai
from google.genai import types

# Configuration
PROJECT_ID = "useful-figure-475210-g7"
LOCATION = "us-central1"

# Initialize client
client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)


class ImageToPromptGenerator:
    """Converts images into optimized video generation prompts"""
    
    def __init__(self):
        self.model = "gemini-2.5-flash"
        self.log_history = []
    
    def _log(self, event_type: str, message: str, details: Optional[Dict] = None):
        """Log analysis events"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{event_type}] {message}"
        self.log_history.append(log_entry)
        print(log_entry)
        if details:
            for key, value in details.items():
                print(f"     {key}: {value}")
    
    def _get_mime_type(self, file_path: str) -> str:
        """Determine MIME type based on file extension"""
        ext = Path(file_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return mime_types.get(ext, 'image/jpeg')
    
    def _parse_json_safely(self, text: str) -> Optional[Dict]:
        """Safely parse JSON response from Gemini"""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                if '```json' in text:
                    json_str = text.split('```json')[1].split('```')[0].strip()
                    return json.loads(json_str)
                elif '```' in text:
                    json_str = text.split('```')[1].split('```')[0].strip()
                    return json.loads(json_str)
            except (IndexError, json.JSONDecodeError):
                pass
        return None
    
    def _validate_image_path(self, image_path: str) -> bool:
        """Validate if image path exists and is valid"""
        if not os.path.exists(image_path):
            return False
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        return Path(image_path).suffix.lower() in valid_extensions
    
    def _normalize_image_input(self, image_input: Union[str, List[str]]) -> List[str]:
        """
        Normalize image input to list of paths
        Handles: single path, list of paths, directory path
        """
        image_paths = []
        
        if isinstance(image_input, str):
            # Single path provided
            if os.path.isdir(image_input):
                # Directory provided - get all images
                valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
                for file in sorted(os.listdir(image_input)):
                    if Path(file).suffix.lower() in valid_extensions:
                        full_path = os.path.join(image_input, file)
                        if self._validate_image_path(full_path):
                            image_paths.append(full_path)
            else:
                # Single file
                if self._validate_image_path(image_input):
                    image_paths.append(image_input)
        
        elif isinstance(image_input, list):
            # List of paths provided
            for path in image_input:
                if isinstance(path, str) and self._validate_image_path(path):
                    image_paths.append(path)
        
        return image_paths
    
    def generate_video_prompt_direct(self, image_path: str, user_intent: str = None) -> Dict:
        """
        Directly analyze image and generate video prompt in one step
        Returns ONLY the optimized video prompt
        
        Args:
            image_path: Path to image file
            user_intent: Optional creative direction
            
        Returns:
            Dict with only the optimized video prompt
        """
        try:
            if not self._validate_image_path(image_path):
                self._log("ERROR", f"Invalid image", {"path": image_path})
                return {
                    "success": False,
                    "error": "Image not found or invalid format",
                    "prompt": None
                }
            
            self._log("GENERATE", f"Generating video prompt", {"image": Path(image_path).name})
            
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            mime_type = self._get_mime_type(image_path)
            
            # Direct prompt generation - analyzes and generates in one shot
            prompt_generation_request = """
            Analyze this image and generate a single-line, cinematic video prompt for a 9:16 vertical reel.
            
            The prompt should:
            1. Capture the image's key visual elements and mood
            2. Include specific camera movements (zoom, pan, dolly, track, orbit)
            3. Suggest dynamic motion and engagement
            4. Include atmospheric effects or color grading suggestions
            5. Be suitable for AI video generation
            6. Be concise but vivid and cinematic
            
            Return ONLY the video prompt as a single sentence. No JSON, no explanation, just the prompt.
            """
            
            response = client.models.generate_content(
                model=self.model,
                contents=[
                    prompt_generation_request,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                ]
            )
            
            optimized_prompt = response.text.strip()
            
            if optimized_prompt:
                self._log("SUCCESS", "Video prompt generated")
                return {
                    "success": True,
                    "prompt": optimized_prompt,
                    "image_file": Path(image_path).name,
                    "image_path": image_path
                }
            else:
                self._log("ERROR", "Failed to generate prompt")
                return {
                    "success": False,
                    "error": "Failed to generate video prompt",
                    "prompt": None
                }
            
        except Exception as e:
            self._log("ERROR", f"Prompt generation failed", {"error": str(e)})
            return {
                "success": False,
                "error": str(e),
                "prompt": None
            }
    
    def generate_prompts_batch(self, image_paths: List[str], user_intent: str = None) -> Dict:
        """
        Generate prompts for multiple images
        Returns list of prompts only
        
        Args:
            image_paths: List of image file paths
            user_intent: Optional creative direction
            
        Returns:
            Dict with list of prompts
        """
        try:
            # Normalize input
            normalized_paths = self._normalize_image_input(image_paths)
            
            if not normalized_paths:
                self._log("ERROR", "No valid images provided")
                return {
                    "success": False,
                    "error": "No valid images found",
                    "prompts": [],
                    "count": 0
                }
            
            self._log("BATCH", f"Generating prompts for {len(normalized_paths)} image(s)")
            
            batch_prompts = []
            
            for idx, img_path in enumerate(normalized_paths, 1):
                self._log("BATCH", f"Processing image {idx}/{len(normalized_paths)}")
                
                result = self.generate_video_prompt_direct(img_path, user_intent)
                
                if result.get("success"):
                    batch_prompts.append({
                        "index": idx,
                        "image": Path(img_path).name,
                        "prompt": result["prompt"]
                    })
                else:
                    self._log("WARN", f"Failed to generate prompt for image {idx}")
            
            self._log("SUCCESS", "Batch prompt generation completed", 
                     {"generated": len(batch_prompts), "total": len(normalized_paths)})
            
            return {
                "success": True,
                "prompts": batch_prompts,
                "count": len(batch_prompts),
                "total_images": len(normalized_paths),
                "failed": len(normalized_paths) - len(batch_prompts)
            }
            
        except Exception as e:
            self._log("ERROR", f"Batch prompt generation failed", {"error": str(e)})
            return {
                "success": False,
                "error": str(e),
                "prompts": [],
                "count": 0
            }
    
    # ==================== LEGACY METHODS (kept for compatibility) ====================
    
    def analyze_image_content(self, image_path: str) -> Dict:
        """
        Analyze image content (returns detailed analysis)
        KEPT FOR BACKWARD COMPATIBILITY - Use generate_video_prompt_direct() instead
        """
        try:
            if not self._validate_image_path(image_path):
                self._log("ERROR", f"Invalid image", {"path": image_path})
                return {"success": False, "error": "Image not found or invalid format"}
            
            self._log("ANALYZE", f"Analyzing image", {"image": Path(image_path).name})
            
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            mime_type = self._get_mime_type(image_path)
            
            analysis_prompt = """
            Analyze this image and provide a JSON response with the following structure:
            {
                "objects": ["list of main objects/subjects"],
                "colors": ["dominant colors"],
                "mood": "emotional tone",
                "lighting": "lighting description",
                "composition": "composition style",
                "setting": "setting description"
            }
            
            Return ONLY valid JSON.
            """
            
            response = client.models.generate_content(
                model=self.model,
                contents=[
                    analysis_prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                ]
            )
            
            analysis = self._parse_json_safely(response.text)
            
            if analysis:
                self._log("SUCCESS", "Image analysis completed")
                return {
                    "success": True,
                    "analysis": analysis,
                    "image_path": image_path
                }
            else:
                return {"success": False, "error": "Failed to parse analysis response"}
            
        except Exception as e:
            self._log("ERROR", f"Image analysis failed", {"error": str(e)})
            return {"success": False, "error": str(e)}
    
    def generate_segmentation_plan(self, image_path: str, num_segments: int = 3) -> Dict:
        """Generate segmentation plan (LEGACY - kept for compatibility)"""
        try:
            if not self._validate_image_path(image_path):
                return {"success": False, "error": "Invalid image"}
            
            self._log("ANALYZE", "Generating segmentation plan")
            
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            mime_type = self._get_mime_type(image_path)
            
            segmentation_prompt = f"""
            Create a segmentation plan for {num_segments} video segments from this image.
            Return JSON with segments, transitions, pacing, and total_duration.
            Return ONLY valid JSON.
            """
            
            response = client.models.generate_content(
                model=self.model,
                contents=[
                    segmentation_prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                ]
            )
            
            segmentation_plan = self._parse_json_safely(response.text)
            
            if segmentation_plan:
                self._log("SUCCESS", "Segmentation plan created")
                return {
                    "success": True,
                    "segmentation_plan": segmentation_plan,
                    "image_path": image_path
                }
            else:
                return {"success": False, "error": "Failed to parse segmentation response"}
            
        except Exception as e:
            self._log("ERROR", f"Segmentation planning failed", {"error": str(e)})
            return {"success": False, "error": str(e)}
    
    def generate_multi_angle_prompts(self, image_path: str, num_variations: int = 3) -> Dict:
        """Generate multi-angle prompts (LEGACY - kept for compatibility)"""
        try:
            if not self._validate_image_path(image_path):
                return {"success": False, "error": "Invalid image"}
            
            self._log("ANALYZE", "Generating multi-angle prompts")
            
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            mime_type = self._get_mime_type(image_path)
            
            multi_angle_prompt = f"""
            Create {num_variations} different video prompts from this image.
            Return JSON with array of prompts with perspective, description, and prompt fields.
            Return ONLY valid JSON.
            """
            
            response = client.models.generate_content(
                model=self.model,
                contents=[
                    multi_angle_prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                ]
            )
            
            multi_prompts = self._parse_json_safely(response.text)
            
            if multi_prompts:
                self._log("SUCCESS", "Multi-angle prompts generated")
                return {
                    "success": True,
                    "multi_angle_prompts": multi_prompts,
                    "image_path": image_path
                }
            else:
                return {"success": False, "error": "Failed to parse multi-angle response"}
            
        except Exception as e:
            self._log("ERROR", f"Multi-angle generation failed", {"error": str(e)})
            return {"success": False, "error": str(e)}
    
    def process_images(self, image_input: Union[str, List[str]], 
                      user_intent: str = None) -> Dict:
        """
        Process images and return prompts
        Simplified - returns only prompts
        """
        # Normalize input
        image_paths = self._normalize_image_input(image_input)
        
        if not image_paths:
            self._log("ERROR", "No valid images provided")
            return {
                "success": False,
                "error": "No valid images found",
                "prompts": []
            }
        
        num_images = len(image_paths)
        self._log("INFO", f"Processing {num_images} image(s)")
        
        # Single image
        if num_images == 1:
            result = self.generate_video_prompt_direct(image_paths[0], user_intent)
            return {
                "success": result["success"],
                "workflow": "single_image",
                "image_count": 1,
                "image_file": result.get("image_file"),
                "prompt": result.get("prompt"),
                "error": result.get("error")
            }
        
        # Multiple images
        else:
            return self.generate_prompts_batch(image_paths, user_intent)
    
    def get_logs(self) -> List[str]:
        """Get analysis log history"""
        return self.log_history
    
    def clear_logs(self):
        """Clear log history"""
        self.log_history = []
        self._log("INFO", "Logs cleared")