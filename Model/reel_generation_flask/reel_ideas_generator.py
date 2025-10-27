"""
Reel Ideas Generator Module
Generates creative ideas for reels using Gemini AI
"""

import re
import json
from google import genai
from google.genai import types
from typing import List, Dict, Optional
from pathlib import Path

# Configuration
PROJECT_ID = "useful-figure-475210-g7"
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
    
    def generate_ideas(self, initial_prompt: str, image_path: Optional[str] = None, 
                      num_ideas: int = 3) -> Dict:
        """
        Generate creative reel ideas based on prompt and optional image
        
        Args:
            initial_prompt: User's initial prompt/description
            image_path: Optional path to image for context
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
            
            # Attach image if provided
            if image_path:
                image_file = Path(image_path)
                if image_file.exists():
                    with open(image_path, "rb") as f:
                        image_bytes = f.read()
                    file_ext = image_file.suffix.lower()
                    mime_type = "image/jpeg" if file_ext in ['.jpg', '.jpeg'] else "image/png"
                    contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
                    print(f"📸 Image attached for context: {image_file.name}")
                else:
                    print(f"⚠️  Image not found: {image_path}")
            
            # Generate ideas
            response = client.models.generate_content(
                model=self.model,
                contents=contents,
            )
            
            response_text = response.text.strip()
            
            # Parse JSON response with improved error handling
            ideas = self._parse_json_ideas(response_text)
            
            if not ideas:
                print(f"⚠️  Failed to parse JSON response, using fallback parsing")
                ideas = [line.strip().strip('"\'') for line in response_text.split('\n') if line.strip()]
            
            print(f"✅ Generated {len(ideas)} ideas")
            
            return {
                "success": True,
                "ideas": ideas[:num_ideas],
                "count": len(ideas[:num_ideas]),
                "prompt": initial_prompt
            }
            
        except Exception as e:
            print(f"❌ Error generating ideas: {str(e)}")
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
            
            print(f"✅ Idea refined successfully ({word_count} words)")
            
            return {
                "success": True,
                "original_idea": chosen_idea,
                "refined_idea": refined_idea,
                "word_count": word_count,
                "refinement_applied": refinement_prompt
            }
            
        except Exception as e:
            print(f"❌ Error refining idea: {str(e)}")
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
                print(f"⚠️  Failed to parse JSON response, using fallback parsing")
                ideas = [line.strip().strip('"\'') for line in response_text.split('\n') if line.strip()]
            
            print(f"✅ Regenerated {len(ideas)} new ideas")
            
            return {
                "success": True,
                "ideas": ideas[:num_ideas],
                "count": len(ideas[:num_ideas]),
                "regeneration_context": regeneration_prompt
            }
            
        except Exception as e:
            print(f"❌ Error regenerating ideas: {str(e)}")
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
            - Mention camera movements (zoom, pan, dolly)
            - Describe lighting, mood, and atmosphere
            - Include timing/pacing suggestions
            - Be optimized for AI video generation
            - Be a single paragraph
            - NOT exceed 150 words
            
            Return ONLY the optimized script/prompt, no additional commentary.
            """
            
            response = client.models.generate_content(
                model=self.model,
                contents=[gemini_prompt],
            )
            
            script = response.text.strip()
            word_count = len(script.split())
            
            print(f"✅ Video script generated successfully ({word_count} words)")
            
            return {
                "success": True,
                "reel_idea": reel_idea,
                "script": script,
                "word_count": word_count,
                "model": "veo-3.1-generate-preview"
            }
            
        except Exception as e:
            print(f"❌ Error generating script: {str(e)}")
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
                print(f"\n🔄 Processing prompt {idx}/{len(prompts)}")
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
            print(f"❌ Error in batch generation: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    # -------------------- Helper Methods --------------------
    
    def _parse_json_ideas(self, response_text: str) -> List[str]:
        """
        Parse JSON ideas from response text with robust error handling
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            List of ideas or empty list if parsing fails
        """
        try:
            # Try to find JSON object in response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
                ideas = result.get('ideas', [])
                
                # Validate ideas
                if isinstance(ideas, list) and all(isinstance(idea, str) for idea in ideas):
                    return ideas
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parse error: {str(e)}")
        except Exception as e:
            print(f"⚠️  Unexpected error in JSON parsing: {str(e)}")
        
        return []
    
    def _validate_prompt(self, prompt: str) -> bool:
        """Validate prompt is not empty or too short"""
        return prompt and len(prompt.strip()) > 3