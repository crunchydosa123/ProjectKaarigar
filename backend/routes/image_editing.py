from flask import Blueprint, request, jsonify, session
import os
import uuid
import tempfile
import shutil
import requests
from datetime import datetime
from google.cloud import storage
from google.cloud import firestore
import mimetypes
import sys
from pathlib import Path
from PIL import Image
from io import BytesIO

# Google GenAI imports for image analysis and editing
from google import genai
from google.genai import types

# Initialize Flask Blueprint
image_edit_bp = Blueprint('image_edit', __name__)

# Google Cloud Configuration
BUCKET_NAME = "all_in_one_bucket1"
FIRESTORE_AVAILABLE = True

# Configuration for image editing
PROJECT_ID = "karigar-475215"
LOCATION = "us-central1"

# Initialize GenAI client for image analysis and editing
genai_client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

# Initialize Google Cloud clients
try:
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    db = firestore.Client()
    print("✅ Google Cloud Storage and Firestore initialized successfully for image editing")
except Exception as e:
    print(f"❌ Failed to initialize Google Cloud services for image editing: {e}")
    FIRESTORE_AVAILABLE = False
    storage_client = None
    bucket = None
    db = None

def get_user_from_session():
    """Get user ID from session"""
    if not session.get('is_authenticated'):
        raise ValueError("User not authenticated")
    
    user_id = session.get('user_id')
    if not user_id:
        raise ValueError("User ID not found in session")
    
    return user_id

def download_image_from_url(image_url, local_path):
    """Download image from URL to local path"""
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Downloaded image: {image_url} -> {local_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to download image {image_url}: {e}")
        return False

def analyze_image_for_suggestions(image_path):
    """Analyze image using Gemini and generate creative suggestions"""
    try:
        print(f"🔍 Analyzing image for creative suggestions: {image_path}")
        
        # Load the image
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        print(f"📊 Image size: {len(image_bytes)} bytes")
        
        # Create image part for Gemini
        image = types.Part.from_bytes(
            data=image_bytes,
            mime_type='image/jpeg'
        )
        
        print(f"✅ Image part created successfully for Gemini")
        
        # Create analysis prompt for creative editing suggestions
        analysis_prompt = """Analyze this image and provide exactly 3 creative editing suggestions to enhance the photo.

First, identify what's in the image:
- If it contains a person/people: suggest portrait enhancements, professional touches, or creative effects
- If it's an inanimate object/product: suggest product photography improvements, branding elements, or artistic effects
- If it's a landscape/scene: suggest atmospheric improvements, color enhancements, or artistic filters

For each suggestion, provide:
- A specific, actionable editing instruction
- A brief explanation of the enhancement
- Category (branding/artisanal/creative)

IMPORTANT: Respond ONLY with valid JSON in this exact format:
{
    "suggestions": [
        {
            "prompt": "Specific editing instruction based on image content",
            "description": "Brief explanation of what this enhancement achieves",
            "category": "branding"
        },
        {
            "prompt": "Another specific editing instruction",
            "description": "Brief explanation of this enhancement",
            "category": "artisanal"
        },
        {
            "prompt": "Third specific editing instruction",
            "description": "Brief explanation of this enhancement",
            "category": "creative"
        }
    ]
}

Make sure to provide exactly 3 suggestions with valid JSON syntax."""
        
        # Generate analysis using Gemini
        print(f"🤖 Sending request to Gemini...")
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[analysis_prompt, image],
            config=types.GenerateContentConfig(
                max_output_tokens=2000,
                temperature=0.7
            )
        )
        
        print(f"🤖 Gemini response received")
        print(f"📊 Response candidates: {len(response.candidates) if response.candidates else 0}")
        
        if response.candidates and response.candidates[0].content.parts:
            analysis_text = response.candidates[0].content.parts[0].text
            print(f"✅ Image analysis completed")
            print(f"📝 Analysis result length: {len(analysis_text)} characters")
            print(f"📝 Analysis result preview: {analysis_text[:300]}...")
            
            # Try to parse JSON response
            try:
                import json
                import re
                
                print(f"🔍 Full analysis text: {analysis_text}")
                
                # Extract JSON from response (might be wrapped in markdown)
                json_text = None
                
                # Try different JSON extraction methods
                if "```json" in analysis_text:
                    json_start = analysis_text.find("```json") + 7
                    json_end = analysis_text.find("```", json_start)
                    json_text = analysis_text[json_start:json_end].strip()
                    print(f"📝 Extracted JSON from markdown: {json_text[:100]}...")
                elif "```" in analysis_text and "{" in analysis_text:
                    # Look for JSON within code blocks
                    json_match = re.search(r'```[^`]*?(\{.*?\})[^`]*?```', analysis_text, re.DOTALL)
                    if json_match:
                        json_text = json_match.group(1).strip()
                        print(f"📝 Extracted JSON from code block: {json_text[:100]}...")
                elif "{" in analysis_text and "}" in analysis_text:
                    # Find the first complete JSON object
                    json_start = analysis_text.find("{")
                    json_end = analysis_text.rfind("}") + 1
                    json_text = analysis_text[json_start:json_end]
                    print(f"📝 Extracted JSON from braces: {json_text[:100]}...")
                else:
                    json_text = analysis_text
                    print(f"📝 Using full text as JSON: {json_text[:100]}...")
                
                if json_text:
                    suggestions_data = json.loads(json_text)
                    suggestions = suggestions_data.get("suggestions", [])
                    print(f"✅ Successfully parsed JSON with {len(suggestions)} suggestions")
                    
                    return {
                        "success": True,
                        "suggestions": suggestions,
                        "raw_analysis": analysis_text
                    }
                else:
                    raise ValueError("No JSON found in response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ JSON parsing failed: {e}")
                print(f"📝 Falling back to text parsing...")
                
                # Fallback: create suggestions from text
                suggestions = []
                lines = analysis_text.split('\n')
                current_suggestion = {}
                
                for line in lines:
                    line = line.strip()
                    # Look for numbered suggestions or bullet points
                    if (line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or 
                        line.startswith('4.') or line.startswith('5.') or 
                        line.startswith('- ') or line.startswith('• ')):
                        
                        if current_suggestion:
                            suggestions.append(current_suggestion)
                        
                        # Extract the suggestion text
                        suggestion_text = line
                        if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                            suggestion_text = line[3:].strip()
                        elif line.startswith(('- ', '• ')):
                            suggestion_text = line[2:].strip()
                        
                        current_suggestion = {
                            "prompt": suggestion_text, 
                            "description": f"AI-generated suggestion: {suggestion_text}", 
                            "category": "creative"
                        }
                    elif line and current_suggestion and not line.startswith('{') and not line.startswith('}'):
                        # Add description if we have a current suggestion
                        if not current_suggestion.get("description") or current_suggestion["description"] == f"AI-generated suggestion: {current_suggestion['prompt']}":
                            current_suggestion["description"] = line
                
                if current_suggestion:
                    suggestions.append(current_suggestion)
                
                print(f"📝 Text parsing created {len(suggestions)} suggestions")
                
                return {
                    "success": True,
                    "suggestions": suggestions[:3],  # Limit to 3 suggestions
                    "raw_analysis": analysis_text
                }
        else:
            print("❌ No analysis generated")
            return {
                "success": False,
                "error": "No analysis generated from image"
            }
            
    except Exception as e:
        print(f"❌ Image analysis failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def edit_image_with_prompt(image_path, prompt):
    """Edit image using Gemini with the provided prompt"""
    try:
        print(f"🎨 Editing image with prompt: {prompt}")
        
        # Load the image
        image = Image.open(image_path)
        print(f"📷 Image size: {image.size}")
        
        # Generate edited image using Gemini
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt, image],
            config=types.GenerateContentConfig(
                max_output_tokens=1000
            )
        )
        
        print("🔄 Processing response...")
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print(f"📝 Text response: {part.text}")
            elif part.inline_data is not None:
                print("💾 Saving edited image...")
                edited_image_bytes = part.inline_data.data
                print(f"✅ Image edited successfully")
                print(f"📊 Size: {len(edited_image_bytes)} bytes")
                return edited_image_bytes
            else:
                print("⚠️ No image data found in response")
        
        raise RuntimeError("No image data found in response")
        
    except Exception as e:
        print(f"❌ Image editing failed: {e}")
        raise RuntimeError(f"Failed to edit image: {e}")

def edit_image_with_reference(image_path, reference_image_path, prompt):
    """Edit image using Gemini with reference image and prompt"""
    try:
        print(f"🎨 Editing image with reference image and prompt: {prompt}")
        
        # Load both images
        main_image = Image.open(image_path)
        reference_image = Image.open(reference_image_path)
        print(f"📷 Main image size: {main_image.size}")
        print(f"📷 Reference image size: {reference_image.size}")
        
        # Create enhanced prompt that includes reference image context
        enhanced_prompt = f"{prompt}. Use the reference image (which is a brand logo or branding element) to enhance the main image while maintaining the overall composition and style."
        
        # Generate edited image using Gemini with both images
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[enhanced_prompt, main_image, reference_image],
            config=types.GenerateContentConfig(
                max_output_tokens=1000
            )
        )
        
        print("🔄 Processing response...")
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print(f"📝 Text response: {part.text}")
            elif part.inline_data is not None:
                print("💾 Saving edited image...")
                edited_image_bytes = part.inline_data.data
                print(f"✅ Image edited successfully with reference")
                print(f"📊 Size: {len(edited_image_bytes)} bytes")
                return edited_image_bytes
            else:
                print("⚠️ No image data found in response")
        
        raise RuntimeError("No image data found in response")
        
    except Exception as e:
        print(f"❌ Image editing with reference failed: {e}")
        raise RuntimeError(f"Failed to edit image with reference: {e}")

def upload_edited_image_to_storage(image_bytes, user_id, title, original_image_id):
    """Upload edited image to Google Cloud Storage"""
    try:
        # Generate unique filename
        unique_filename = f"edited_{uuid.uuid4()}.png"
        
        # Create path: kaarigar/KR_USER11/generated_images/ (same as generated images)
        kaarigar_id = f"KR_{user_id.upper()}"
        blob_path = f"kaarigar/{kaarigar_id}/generated_images/{unique_filename}"
        
        # Upload file
        blob = bucket.blob(blob_path)
        blob.upload_from_string(image_bytes, content_type="image/png")
        
        # Make blob publicly accessible
        blob.make_public()
        
        # Get public URL
        public_url = blob.public_url
        
        print(f"✅ Edited image uploaded successfully: {blob_path}")
        print(f"🔗 Public URL: {public_url}")
        
        return {
            "success": True,
            "blob_path": blob_path,
            "public_url": public_url,
            "filename": unique_filename
        }
        
    except Exception as e:
        print(f"❌ Failed to upload edited image to storage: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def save_edited_image_metadata(user_id, image_data):
    """Save edited image metadata to Firestore in _generated_images collection"""
    try:
        print(f"🔧 Saving edited image metadata for user: {user_id}")
        
        kaarigar_id = f"KR_{user_id.upper()}"
        
        # Create image document
        image_doc = {
            "user_id": user_id,
            "kaarigar_id": kaarigar_id,
            "image_type": "edited",
            "title": image_data["title"],
            "prompt": image_data["prompt"],
            "original_image_id": image_data["original_image_id"],
            "aspect_ratio": image_data.get("aspect_ratio", "1:1"),
            "filename": image_data["filename"],
            "blob_path": image_data["blob_path"],
            "public_url": image_data["public_url"],
            "file_size": image_data.get("file_size", 0),
            "generated_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        print(f"🔧 Created edited image document with {len(image_doc)} fields")
        
        # Save to _generated_images collection (same as generated images)
        images_ref = db.collection("media").document(user_id).collection("uploadmedia").document("media_data").collection("_generated_images")
        
        # Create document reference
        image_ref = images_ref.document()
        print(f"🔧 Document ID: {image_ref.id}")
        
        # Save the document
        print(f"🔧 Saving edited image document to Firestore...")
        image_ref.set(image_doc)
        print(f"🔧 Edited image document saved successfully!")
        
        print(f"✅ Edited image metadata saved to Firestore:")
        print(f"   - Path: media/{user_id}/uploadmedia/media_data/_generated_images/{image_ref.id}")
        
        return {
            "success": True,
            "image_id": image_ref.id,
            "message": "Edited image saved successfully"
        }
        
    except Exception as e:
        print(f"❌ Failed to save edited image metadata: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@image_edit_bp.route('/analyze-image', methods=['POST'])
def analyze_image():
    """Analyze image and generate creative editing suggestions"""
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get image URL
        image_url = data.get('image_url', '')
        if not image_url:
            return jsonify({"error": "No image URL provided"}), 400
        
        print(f"🔍 Analyzing image for user: {user_id}")
        print(f"🖼️ Image URL: {image_url}")
        
        # Process in memory - no temp folders
        try:
            # Download image content
            response = requests.get(image_url, stream=True)
            response.raise_for_status()
            
            # Create temporary file for processing (required by Gemini)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(response.content)
            temp_file.close()
            local_image_path = temp_file.name
            
            print(f"✅ Downloaded image to temp file: {local_image_path}")
            
            # Analyze image for suggestions
            analysis_result = analyze_image_for_suggestions(local_image_path)
            
            if not analysis_result["success"]:
                return jsonify({"error": f"Image analysis failed: {analysis_result['error']}"}), 500
            
            print(f"🎉 Image analysis completed successfully!")
            print(f"   - Generated {len(analysis_result['suggestions'])} suggestions")
            
            return jsonify({
                "success": True,
                "suggestions": analysis_result["suggestions"],
                "raw_analysis": analysis_result.get("raw_analysis", "")
            })
            
        finally:
            # Clean up temp file immediately
            try:
                if 'local_image_path' in locals() and os.path.exists(local_image_path):
                    os.unlink(local_image_path)
                    print(f"🧹 Cleaned up temp image file: {local_image_path}")
            except Exception as e:
                print(f"⚠️ Failed to clean up temp image file: {e}")
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Image analysis error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@image_edit_bp.route('/edit-image', methods=['POST'])
def edit_image():
    """Edit image using provided prompt"""
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get parameters
        image_url = data.get('image_url', '')
        prompt = data.get('prompt', '')
        title = data.get('title', '')
        original_image_id = data.get('original_image_id', '')
        
        if not image_url:
            return jsonify({"error": "No image URL provided"}), 400
        
        if not prompt.strip():
            return jsonify({"error": "No prompt provided"}), 400
        
        if not title.strip():
            return jsonify({"error": "No title provided"}), 400
        
        print(f"🎨 Starting image editing for user: {user_id}")
        print(f"🖼️ Image URL: {image_url}")
        print(f"📝 Prompt: {prompt}")
        print(f"📝 Title: {title}")
        
        # Process in memory - no temp folders
        try:
            # Download image content
            response = requests.get(image_url, stream=True)
            response.raise_for_status()
            
            # Create temporary file for processing (required by Gemini)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(response.content)
            temp_file.close()
            local_image_path = temp_file.name
            
            print(f"✅ Downloaded image to temp file: {local_image_path}")
            
            # Edit image using prompt
            edited_image_bytes = edit_image_with_prompt(local_image_path, prompt)
            
            if not edited_image_bytes:
                return jsonify({"error": "Failed to edit image"}), 500
            
            # Get file size
            file_size = len(edited_image_bytes)
            print(f"📊 Edited image size: {file_size / 1024:.1f} KB")
            
            # Upload edited image to Cloud Storage
            upload_result = upload_edited_image_to_storage(edited_image_bytes, user_id, title, original_image_id)
            
            if not upload_result["success"]:
                return jsonify({"error": f"Failed to upload edited image: {upload_result['error']}"}), 500
            
            # Prepare metadata for Firestore
            image_metadata = {
                "title": title,
                "prompt": prompt,
                "original_image_id": original_image_id,
                "aspect_ratio": "1:1",  # Default aspect ratio
                "filename": upload_result["filename"],
                "blob_path": upload_result["blob_path"],
                "public_url": upload_result["public_url"],
                "file_size": file_size
            }
            
            # Save metadata to Firestore
            save_result = save_edited_image_metadata(user_id, image_metadata)
            
            if not save_result["success"]:
                return jsonify({"error": f"Failed to save edited image metadata: {save_result['error']}"}), 500
            
            print(f"🎉 Image editing completed successfully!")
            print(f"   - Image ID: {save_result['image_id']}")
            print(f"   - Public URL: {upload_result['public_url']}")
            
            return jsonify({
                "success": True,
                "message": "Image edited successfully",
                "image_id": save_result["image_id"],
                "public_url": upload_result["public_url"],
                "title": title,
                "file_size": file_size
            })
            
        finally:
            # Clean up temp file immediately
            try:
                if 'local_image_path' in locals() and os.path.exists(local_image_path):
                    os.unlink(local_image_path)
                    print(f"🧹 Cleaned up temp image file: {local_image_path}")
            except Exception as e:
                print(f"⚠️ Failed to clean up temp image file: {e}")
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Image editing error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@image_edit_bp.route('/edit-image-with-reference', methods=['POST'])
def edit_image_with_reference_route():
    """Edit image using provided prompt with optional reference image (for branding)"""
    try:
        if not session.get('is_authenticated'):
            return jsonify({"error": "Not authenticated"}), 401
        
        user_id = get_user_from_session()
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Get parameters
        image_url = data.get('image_url', '')
        prompt = data.get('prompt', '')
        title = data.get('title', '')
        original_image_id = data.get('original_image_id', '')
        reference_image_url = data.get('reference_image_url', '')
        use_brand_logo = data.get('use_brand_logo', False)
        
        if not image_url:
            return jsonify({"error": "No image URL provided"}), 400
        
        if not prompt.strip():
            return jsonify({"error": "No prompt provided"}), 400
        
        if not title.strip():
            return jsonify({"error": "No title provided"}), 400
        
        print(f"🎨 Starting image editing with reference for user: {user_id}")
        print(f"🖼️ Image URL: {image_url}")
        print(f"📝 Prompt: {prompt}")
        print(f"📝 Title: {title}")
        print(f"🖼️ Reference image URL: {reference_image_url or 'None'}")
        print(f"🏷️ Use brand logo: {use_brand_logo}")
        
        # Get brand logo if use_brand_logo is True
        final_reference_url = reference_image_url
        reference_image_type = "user_selected"
        
        if use_brand_logo:
            try:
                # Fetch brand logo from profile
                profile_id = f"profile_{user_id}"
                profile_doc = db.collection("profiles").document(profile_id).get()
                
                if profile_doc.exists:
                    profile_data = profile_doc.to_dict()
                    brand_logo_url = profile_data.get("brandLogo", "")
                    
                    if brand_logo_url:
                        final_reference_url = brand_logo_url
                        reference_image_type = "brand_logo"
                        print(f"🏷️ Using brand logo from profile: {brand_logo_url}")
                    else:
                        print("⚠️ No brand logo found in profile, continuing without reference")
                else:
                    print("⚠️ Profile not found, continuing without reference")
            except Exception as e:
                print(f"⚠️ Error fetching brand logo: {e}, continuing without reference")
        
        # Process in memory
        try:
            # Download main image
            main_response = requests.get(image_url, stream=True)
            main_response.raise_for_status()
            
            main_temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            main_temp_file.write(main_response.content)
            main_temp_file.close()
            main_image_path = main_temp_file.name
            
            print(f"✅ Downloaded main image to temp file: {main_image_path}")
            
            # Download reference image if provided
            reference_image_path = None
            if final_reference_url:
                try:
                    ref_response = requests.get(final_reference_url, stream=True)
                    ref_response.raise_for_status()
                    
                    ref_temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                    ref_temp_file.write(ref_response.content)
                    ref_temp_file.close()
                    reference_image_path = ref_temp_file.name
                    
                    print(f"✅ Downloaded reference image to temp file: {reference_image_path}")
                except Exception as e:
                    print(f"⚠️ Failed to download reference image: {e}, continuing without reference")
                    reference_image_path = None
            
            # Edit image with or without reference
            if reference_image_path:
                edited_image_bytes = edit_image_with_reference(main_image_path, reference_image_path, prompt)
            else:
                edited_image_bytes = edit_image_with_prompt(main_image_path, prompt)
            
            if not edited_image_bytes:
                return jsonify({"error": "Failed to edit image"}), 500
            
            # Get file size
            file_size = len(edited_image_bytes)
            print(f"📊 Edited image size: {file_size / 1024:.1f} KB")
            
            # Upload edited image to Cloud Storage
            upload_result = upload_edited_image_to_storage(edited_image_bytes, user_id, title, original_image_id)
            
            if not upload_result["success"]:
                return jsonify({"error": f"Failed to upload edited image: {upload_result['error']}"}), 500
            
            # Prepare metadata for Firestore
            image_metadata = {
                "title": title,
                "prompt": prompt,
                "original_image_id": original_image_id,
                "aspect_ratio": "1:1",
                "filename": upload_result["filename"],
                "blob_path": upload_result["blob_path"],
                "public_url": upload_result["public_url"],
                "file_size": file_size,
                "has_reference_image": bool(reference_image_path),
                "reference_image_type": reference_image_type if reference_image_path else None
            }
            
            # Save metadata to Firestore
            save_result = save_edited_image_metadata(user_id, image_metadata)
            
            if not save_result["success"]:
                return jsonify({"error": f"Failed to save edited image metadata: {save_result['error']}"}), 500
            
            print(f"🎉 Image editing with reference completed successfully!")
            print(f"   - Image ID: {save_result['image_id']}")
            print(f"   - Public URL: {upload_result['public_url']}")
            print(f"   - Reference type: {reference_image_type if reference_image_path else 'None'}")
            
            return jsonify({
                "success": True,
                "message": "Image edited successfully",
                "image_id": save_result["image_id"],
                "public_url": upload_result["public_url"],
                "title": title,
                "file_size": file_size,
                "reference_image_type": reference_image_type if reference_image_path else None
            })
            
        finally:
            # Clean up temp files
            try:
                if 'main_image_path' in locals() and os.path.exists(main_image_path):
                    os.unlink(main_image_path)
                    print(f"🧹 Cleaned up main temp image file: {main_image_path}")
            except Exception as e:
                print(f"⚠️ Failed to clean up main temp file: {e}")
            
            try:
                if 'reference_image_path' in locals() and reference_image_path and os.path.exists(reference_image_path):
                    os.unlink(reference_image_path)
                    print(f"🧹 Cleaned up reference temp image file: {reference_image_path}")
            except Exception as e:
                print(f"⚠️ Failed to clean up reference temp file: {e}")
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ Image editing with reference error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@image_edit_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for image editing service"""
    return jsonify({
        "status": "ok",
        "service": "image_editing",
        "firestore_available": FIRESTORE_AVAILABLE,
        "storage_available": storage_client is not None,
        "bucket_name": BUCKET_NAME
    })
