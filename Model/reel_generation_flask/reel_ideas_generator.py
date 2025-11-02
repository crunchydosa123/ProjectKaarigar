"""
Reel Ideas Generator Module
Generates creative ideas for reels using Gemini AI
"""

"""
Reel Ideas Generator Module
Generates creative ideas for reels using Gemini AI
"""

import re
import json
import logging
from google import genai
from google.genai import types
from typing import List, Dict, Optional
from pathlib import Path
import requests
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = "karigar-475215"
LOCATION = "us-central1"

# Initialize client
client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)


class ReelIdeasGenerator:
    """Generate and refine reel ideas using Gemini"""
    
    def __init__(self):
        self.model = "gemini-2.5-flash"
        logger.info(f"🤖 ReelIdeasGenerator initialized with model: {self.model}")
    
    def generate_ideas(self, initial_prompt: str, image_path: Optional[str] = None, 
                      num_ideas: int = 3) -> Dict:
        """
        Generate creative reel ideas based on prompt and optional image
        
        Args:
            initial_prompt: User's initial prompt/description
            image_path: Optional local path or URL to image for context
            num_ideas: Number of ideas to generate (default: 3)
            
        Returns:
            Dict with 'ideas' list, each idea ≤30 words
        """
        try:
            if not initial_prompt or not initial_prompt.strip():
                return {
                    "success": False,
                    "error": "initial_prompt cannot be empty",
                    "ideas": []
                }
            
            contents = []
            
            gemini_prompt = f"""
            You are a creative director for vertical video content (9:16 reels).
            
            User's prompt: "{initial_prompt}"
            
            Generate {num_ideas} unique, creative reel ideas based on this prompt.
            Each idea should:
            - Be 30 words or less
            - Include the main scene, mood, and action
            - Be suitable for a 4-6 second vertical video
            - Be distinct from each other
            
            Format your response as a JSON array:
            {{"ideas": ["idea1", "idea2", "idea3"]}}
            
            ONLY return valid JSON, no other text.
            """
            
            contents.append(gemini_prompt)
            
            # Attach image if provided (support both local files and URLs)
            if image_path:
                image_part = self._process_image(image_path)
                if image_part:
                    contents.append(image_part)
                    logger.info(f"📸 Image attached for context")
                else:
                    logger.warning(f"⚠️  Failed to process image: {image_path}")
            
            # Generate ideas
            response = client.models.generate_content(
                model=self.model,
                contents=contents,
            )
            
            response_text = response.text.strip()
            
            # Parse JSON response with improved error handling
            ideas = self._parse_json_ideas(response_text)
            
            if not ideas:
                logger.warning(f"⚠️  Failed to parse JSON response, using fallback parsing")
                ideas = [line.strip().strip('"\'') for line in response_text.split('\n') if line.strip()]
            
            logger.info(f"✅ Generated {len(ideas)} ideas")
            
            return {
                "success": True,
                "ideas": ideas[:num_ideas],
                "count": len(ideas[:num_ideas]),
                "prompt": initial_prompt
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating ideas: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "ideas": []
            }
    
    def refine_idea(self, chosen_idea: str, refinement_prompt: str) -> Dict:
        """
        Refine a chosen idea based on user feedback
        
        Args:
            chosen_idea: The idea user selected
            refinement_prompt: User's refinement/improvement request
            
        Returns:
            Dict with 'refined_idea' ≤40 words
        """
        try:
            if not chosen_idea or not chosen_idea.strip():
                return {
                    "success": False,
                    "error": "chosen_idea cannot be empty"
                }
            
            if not refinement_prompt or not refinement_prompt.strip():
                return {
                    "success": False,
                    "error": "refinement_prompt cannot be empty"
                }
            
            gemini_prompt = f"""
            You are a creative director refining reel concepts.
            
            Original idea: "{chosen_idea}"
            User refinement request: "{refinement_prompt}"
            
            Refine and improve the idea based on the user's request.
            
            Requirements:
            - Keep it 40 words or less
            - Maintain the core concept but enhance it
            - Make it more specific and cinematic
            - Suitable for 4-6 second vertical video
            
            Return ONLY the refined idea text, no additional commentary.
            """
            
            response = client.models.generate_content(
                model=self.model,
                contents=[gemini_prompt],
            )
            
            refined_idea = response.text.strip()
            word_count = len(refined_idea.split())
            
            logger.info(f"✅ Idea refined successfully ({word_count} words)")
            
            return {
                "success": True,
                "original_idea": chosen_idea,
                "refined_idea": refined_idea,
                "word_count": word_count,
                "refinement_applied": refinement_prompt
            }
            
        except Exception as e:
            logger.error(f"❌ Error refining idea: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def regenerate_ideas(self, regeneration_prompt: str, 
                        num_ideas: int = 3) -> Dict:
        """
        Regenerate ideas with new context/constraints
        
        Args:
            regeneration_prompt: New prompt or feedback for regeneration
            num_ideas: Number of ideas to generate
            
        Returns:
            Dict with 'ideas' list, each idea ≤30 words
        """
        try:
            if not regeneration_prompt or not regeneration_prompt.strip():
                return {
                    "success": False,
                    "error": "regeneration_prompt cannot be empty",
                    "ideas": []
                }
            
            gemini_prompt = f"""
            You are a creative director for vertical video content (9:16 reels).
            
            User feedback/new direction: "{regeneration_prompt}"
            
            Generate {num_ideas} completely NEW and different reel ideas.
            Each idea should:
            - Be 30 words or less
            - Be creative and engaging
            - Incorporate the user's feedback
            - Be suitable for a 4-6 second vertical video
            - Be completely different from previous ideas (if any)
            
            Format your response as a JSON array:
            {{"ideas": ["idea1", "idea2", "idea3"]}}
            
            ONLY return valid JSON, no other text.
            """
            
            response = client.models.generate_content(
                model=self.model,
                contents=[gemini_prompt],
            )
            
            response_text = response.text.strip()
            
            # Parse JSON response with improved error handling
            ideas = self._parse_json_ideas(response_text)
            
            if not ideas:
                logger.warning(f"⚠️  Failed to parse JSON response, using fallback parsing")
                ideas = [line.strip().strip('"\'') for line in response_text.split('\n') if line.strip()]
            
            logger.info(f"✅ Regenerated {len(ideas)} new ideas")
            
            return {
                "success": True,
                "ideas": ideas[:num_ideas],
                "count": len(ideas[:num_ideas]),
                "regeneration_context": regeneration_prompt
            }
            
        except Exception as e:
            logger.error(f"❌ Error regenerating ideas: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "ideas": []
            }
    
    def generate_video_script(self, reel_idea: str) -> Dict:
        """
        Convert reel idea into detailed video generation script/prompt
        
        Args:
            reel_idea: The chosen and finalized reel idea
            
        Returns:
            Dict with 'script' that's optimized for Veo video generation
        """
        try:
            if not reel_idea or not reel_idea.strip():
                return {
                    "success": False,
                    "error": "reel_idea cannot be empty"
                }
            
            gemini_prompt = f"""
            You are an expert video prompt engineer for Google's Veo 3.1 video generation model.
            
            Reel Idea: "{reel_idea}"
            
            Create a detailed, cinematic prompt for generating a 9:16 vertical reel video.
            
            The prompt should:
            - Include specific visual descriptions
            - Mention camera movements (zoom, pan, dolly, tracking)
            - Describe lighting, mood, and atmosphere
            - Include timing/pacing suggestions
            - Be optimized for AI video generation
            - Be a single paragraph
            - NOT exceed 150 words
            - Be specific and actionable
            
            Return ONLY the optimized script/prompt, no additional commentary.
            """
            
            response = client.models.generate_content(
                model=self.model,
                contents=[gemini_prompt],
            )
            
            script = response.text.strip()
            word_count = len(script.split())
            
            logger.info(f"✅ Video script generated successfully ({word_count} words)")
            
            return {
                "success": True,
                "reel_idea": reel_idea,
                "script": script,
                "word_count": word_count,
                "model": "veo-3.1-generate-preview"
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating script: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def batch_generate_ideas(self, prompts: List[str], num_ideas: int = 3) -> Dict:
        """
        Generate ideas for multiple prompts in batch
        
        Args:
            prompts: List of prompts to generate ideas for
            num_ideas: Number of ideas per prompt
            
        Returns:
            Dict with results for each prompt
        """
        try:
            if not prompts or len(prompts) == 0:
                return {
                    "success": False,
                    "error": "prompts list cannot be empty",
                    "results": []
                }
            
            results = []
            for idx, prompt in enumerate(prompts, 1):
                logger.info(f"🔄 Processing prompt {idx}/{len(prompts)}")
                idea_result = self.generate_ideas(prompt, num_ideas=num_ideas)
                results.append({
                    "prompt": prompt,
                    "ideas": idea_result.get("ideas", []),
                    "success": idea_result.get("success", False)
                })
            
            return {
                "success": True,
                "total_prompts": len(prompts),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"❌ Error in batch generation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    # -------------------- Helper Methods --------------------
    
    def _process_image(self, image_input: str) -> Optional[types.Part]:
        """
        Process image from local file path or URL
        
        Args:
            image_input: Local file path or HTTP(S) URL
            
        Returns:
            types.Part object or None if failed
        """
        try:
            # Check if it's a URL
            if image_input.startswith('http://') or image_input.startswith('https://'):
                return self._process_image_from_url(image_input)
            else:
                return self._process_image_from_file(image_input)
        except Exception as e:
            logger.error(f"❌ Error processing image: {str(e)}")
            return None
    
    def _process_image_from_url(self, url: str) -> Optional[types.Part]:
        """
        Download and process image from URL
        
        Args:
            url: HTTP(S) URL of the image
            
        Returns:
            types.Part object or None if failed
        """
        try:
            logger.info(f"📥 Downloading image from URL: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            image_bytes = response.content
            
            # Detect mime type from URL or content
            content_type = response.headers.get('content-type', '').lower()
            if 'jpeg' in content_type or 'jpg' in content_type:
                mime_type = "image/jpeg"
            elif 'png' in content_type:
                mime_type = "image/png"
            elif 'webp' in content_type:
                mime_type = "image/webp"
            else:
                # Fallback based on URL extension
                if url.lower().endswith(('.jpg', '.jpeg')):
                    mime_type = "image/jpeg"
                elif url.lower().endswith('.png'):
                    mime_type = "image/png"
                elif url.lower().endswith('.webp'):
                    mime_type = "image/webp"
                else:
                    mime_type = "image/jpeg"  # Default
            
            logger.info(f"✅ Image downloaded successfully ({len(image_bytes)} bytes, {mime_type})")
            return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            
        except requests.RequestException as e:
            logger.error(f"❌ Failed to download image from URL: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Error processing image from URL: {str(e)}")
            return None
    
    def _process_image_from_file(self, file_path: str) -> Optional[types.Part]:
        """
        Process image from local file path
        
        Args:
            file_path: Path to local image file
            
        Returns:
            types.Part object or None if failed
        """
        try:
            image_file = Path(file_path)
            if not image_file.exists():
                logger.error(f"❌ Image file not found: {file_path}")
                return None
            
            with open(file_path, "rb") as f:
                image_bytes = f.read()
            
            file_ext = image_file.suffix.lower()
            if file_ext in ['.jpg', '.jpeg']:
                mime_type = "image/jpeg"
            elif file_ext == '.png':
                mime_type = "image/png"
            elif file_ext == '.webp':
                mime_type = "image/webp"
            else:
                mime_type = "image/jpeg"  # Default
            
            logger.info(f"✅ Image loaded from file: {image_file.name} ({mime_type})")
            return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            
        except Exception as e:
            logger.error(f"❌ Error processing image from file: {str(e)}")
            return None
    
    def _parse_json_ideas(self, response_text: str) -> List[str]:
        """
        Parse JSON ideas from response text with robust error handling
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            List of ideas or empty list if parsing fails
        """
        try:
            # Remove markdown code blocks if present
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```'):
                cleaned_text = re.sub(r'^```(?:json)?\s*', '', cleaned_text)
                cleaned_text = re.sub(r'\s*```$', '', cleaned_text)
            
            # Try to find JSON object in response
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                ideas = result.get('ideas', [])
                
                # Validate ideas
                if isinstance(ideas, list) and all(isinstance(idea, str) for idea in ideas):
                    return ideas
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️  JSON parse error: {str(e)}")
        except Exception as e:
            logger.warning(f"⚠️  Unexpected error in JSON parsing: {str(e)}")
        
        return []
    
    def _validate_prompt(self, prompt: str) -> bool:
        """Validate prompt is not empty or too short"""
        return prompt and len(prompt.strip()) > 3