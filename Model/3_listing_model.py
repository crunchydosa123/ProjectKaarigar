# -*- coding: utf-8 -*-
import os
import re
import sys
import json
import textwrap
from typing import List, Dict, Tuple, Optional

# Configure UTF-8 encoding for Windows console
if sys.platform == 'win32':
    # Set UTF-8 for stdout and stderr to handle Unicode characters
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import requests
except Exception:
    requests = None

try:
    from PIL import Image
    from io import BytesIO
except Exception:
    Image = None
    BytesIO = None

try:
    # Gemini SDK
    from google import genai  # pip install google-genai
    from google.genai import types
    from google.genai.types import HttpOptions
except Exception:
    genai = None
    types = None
    HttpOptions = None

# Placeholder API key. Replace this with your actual Gemini API key.
GEMINI_API_KEY = "AIzaSyDiUMs4sIAdOk09006hS7DcY79DZh53_M4"

# ==================== PATH-ONLY LISTING FUNCTIONS ====================

def get_image_editing_suggestions(client, image_path: str) -> List[str]:
    """Get AI-based editing suggestions for the image"""
    try:
        print(f"[AI Suggestions] Analyzing image for editing suggestions...")
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=image_data,
                    mime_type='image/jpeg',
                ),
                "Analyze this product image and suggest 3 specific editing improvements that would make it more appealing for e-commerce listings. Focus on: 1) Lighting and color enhancement, 2) Background improvements, 3) Product presentation. Provide concise, actionable suggestions."
            ],
            config=types.GenerateContentConfig(
                max_output_tokens=200,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
        )
        
        if response.candidates and response.candidates[0].content.parts:
            suggestions_text = response.candidates[0].content.parts[0].text
            # Split suggestions into list
            suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip() and not s.strip().startswith(('1.', '2.', '3.'))]
            return suggestions[:3] if suggestions else ["Enhance lighting and contrast", "Improve background", "Add product highlights"]
        else:
            return ["Enhance lighting and contrast", "Improve background", "Add product highlights"]
    except Exception as e:
        print(f"[AI Suggestions] Error: {str(e)}")
        return ["Enhance lighting and contrast", "Improve background", "Add product highlights"]

def edit_image_with_gemini(client, image_path: str, edit_prompt: str) -> str:
    """Edit image using Gemini and return path to edited image"""
    try:
        print(f"[Image Edit] Editing image with prompt: {edit_prompt}")
        
        # Load original image
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # Create PIL Image object for editing
        from PIL import Image
        original_image = Image.open(image_path)
        
        # Use Gemini to edit the image
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[edit_prompt, original_image],
            config=types.GenerateContentConfig(
                max_output_tokens=1000
            )
        )
        
        # Process response and save edited image
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                edited_image = Image.open(BytesIO(part.inline_data.data))
                # Generate unique filename
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                edited_path = f"{base_name}_edited_{len(os.listdir('.'))}.png"
                edited_image.save(edited_path)
                print(f"[Image Edit] Edited image saved as: {edited_path}")
                return edited_path
        
        print("[Image Edit] No edited image returned from Gemini")
        return image_path
        
    except Exception as e:
        print(f"[Image Edit] Error: {str(e)}")
        return image_path

def interactive_image_editing(client, image_paths: List[str]) -> List[str]:
    """Simplified image editing with auto-suggestions and satisfaction check"""
    edited_paths = image_paths.copy()
    
    for i, path in enumerate(image_paths):
        print(f"\n=== Image {i+1}/{len(image_paths)}: {os.path.basename(path)} ===")
        
        # Automatically get AI suggestions
        suggestions = get_image_editing_suggestions(client, path)
        print("\nAI Editing Suggestions:")
        for j, suggestion in enumerate(suggestions, 1):
            print(f"{j}. {suggestion}")
        
        # Simple choice
        choice = input("\nChoose: 1, 2, 3, or enter custom prompt (or press Enter to skip): ").strip()
        
        if choice == "":
            print("Skipping image editing...")
            continue
        elif choice in ["1", "2", "3"]:
            suggestion_index = int(choice) - 1
            edit_prompt = suggestions[suggestion_index]
            edited_path = edit_image_with_gemini(client, path, edit_prompt)
            edited_paths[i] = edited_path
            print(f"Applied: {edit_prompt}")
            print(f"Edited image saved: {edited_path}")
        else:
            # Custom prompt
            edit_prompt = choice
            edited_path = edit_image_with_gemini(client, path, edit_prompt)
            edited_paths[i] = edited_path
            print(f"Applied custom edit: {edit_prompt}")
            print(f"Edited image saved: {edited_path}")
        
        # Satisfaction check and further editing loop
        while True:
            print(f"\n=== Are you satisfied with the edited image? ===")
            print(f"Current image: {edited_paths[i]}")
            satisfaction = input("Are you satisfied? (y/n) or press Enter to continue: ").strip().lower()
            
            if satisfaction in ["y", "yes", ""]:
                print("Great! Moving to next image...")
                break
            elif satisfaction in ["n", "no"]:
                print("\n=== Further Editing Options ===")
                print("1. Get new AI suggestions")
                print("2. Manual edit prompt")
                print("3. Skip further editing")
                
                further_choice = input("Choose (1-3): ").strip()
                
                if further_choice == "1":
                    # Get new AI suggestions
                    new_suggestions = get_image_editing_suggestions(client, edited_paths[i])
                    print("\nNew AI Editing Suggestions:")
                    for j, suggestion in enumerate(new_suggestions, 1):
                        print(f"{j}. {suggestion}")
                    
                    apply_choice = input("\nApply suggestion (1-3) or press Enter to skip: ").strip()
                    if apply_choice in ["1", "2", "3"]:
                        suggestion_index = int(apply_choice) - 1
                        edit_prompt = new_suggestions[suggestion_index]
                        edited_path = edit_image_with_gemini(client, edited_paths[i], edit_prompt)
                        edited_paths[i] = edited_path
                        print(f"Applied: {edit_prompt}")
                        print(f"Updated image saved: {edited_path}")
                        
                elif further_choice == "2":
                    # Manual edit prompt
                    edit_prompt = input("Enter your editing prompt: ").strip()
                    if edit_prompt:
                        edited_path = edit_image_with_gemini(client, edited_paths[i], edit_prompt)
                        edited_paths[i] = edited_path
                        print(f"Applied custom edit: {edit_prompt}")
                        print(f"Updated image saved: {edited_path}")
                    else:
                        print("No prompt entered, skipping...")
                        
                elif further_choice == "3":
                    print("Skipping further editing...")
                    break
                else:
                    print("Invalid choice, please try again.")
            else:
                print("Invalid input, please enter y/n or press Enter.")
    
    return edited_paths

def analyze_images_with_gemini(client, image_paths: List[str]) -> List[str]:
    """Analyze local images using Gemini with verbose progress updates."""
    image_descriptions = []
    total = min(3, len(image_paths))
    for idx, path in enumerate(image_paths[:3], start=1):
        try:
            print(f"[1/{total}] Loading image {idx}/{total}: {path}")
            with open(path, "rb") as f:
                image_data = f.read()
            print(f"[2/{total}] Analyzing image {idx}/{total} with Gemini...")
            gemini_response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(
                        data=image_data,
                        mime_type='image/jpeg',
                    ),
                    "Describe this product image: materials, craftsmanship, style, use-cases, and unique selling points."
                ],
                config=types.GenerateContentConfig(
                    max_output_tokens=300,
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )
            if gemini_response.candidates and gemini_response.candidates[0].content.parts:
                description = gemini_response.candidates[0].content.parts[0].text
                image_descriptions.append(description)
                print(f"[3/{total}] Image {idx}/{total} analyzed. Summary: {description[:120]}...")
            else:
                image_descriptions.append("Product image analysis unavailable")
                print(f"[3/{total}] Image {idx}/{total} analysis returned no text.")
        except Exception as e:
            print(f"[!] Image {idx}/{total} failed: {str(e)}")
            image_descriptions.append("Image analysis failed")
    return image_descriptions

def generate_optimized_listing(client, platform: str, product_info: Dict, image_descriptions: List[str]) -> Dict:
    """Generate optimized listing for specific platform using Gemini"""
    
    # Prepare context for Gemini
    context = f"""
    Product Information:
    - Title: {product_info['title']}
    - Current Price: {product_info['price'] if product_info['price'] else 'Not specified'}
    - Source: Local images provided by user
    
    Image Analysis:
    {chr(10).join([f"Image {i+1}: {desc}" for i, desc in enumerate(image_descriptions)])}
    
    Platform: {platform.upper()}
    
    Create an optimized product listing for {platform} that includes:
    1. SEO-optimized title (under 200 characters)
    2. Compelling bullet points (5-7 points)
    3. Detailed description (150-200 words)
    4. Technical specifications
    5. SEO tags/keywords
    6. Price optimization suggestions
    7. FAQ section (3-5 questions)
    8. What's included in the package
    
    Focus on:
    - {platform}-specific best practices
    - SEO optimization for better visibility
    - Compelling copy that converts
    - Price positioning strategy
    - Highlighting craftsmanship and uniqueness
    
    Return the response as a JSON object with these fields:
    {{
        "title": "SEO optimized title",
        "bullets": ["bullet point 1", "bullet point 2", ...],
        "description": "detailed description",
        "specifications": {{"key": "value"}},
        "seo_tags": ["tag1", "tag2", ...],
        "faqs": [{{"q": "question", "a": "answer"}}],
        "pricing": {{"ai_price": number, "recommended_range": [low, high]}},
        "policies": {{"key": "value"}},
        "whats_in_the_box": ["item1", "item2", ...]
    }}
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=context,
            config=types.GenerateContentConfig(
                max_output_tokens=1500,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
        )
        
        if response.candidates and response.candidates[0].content.parts:
            content = response.candidates[0].content.parts[0].text
            
            # Try to parse as JSON
            try:
                # Look for JSON in the response
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1:
                    json_str = content[start:end+1]
                    data = json.loads(json_str)
                    data["platform"] = platform
                    return data
            except:
                pass
            
            # If JSON parsing fails, create structured response from text
            return {
                "platform": platform,
                "title": product_info['title'],
                "description": content,
                "price_analysis": f"Current price: {product_info['price'] if product_info['price'] else 'Not specified'}",
                "image_insights": image_descriptions,
                "raw_content": content
            }
        else:
            return {"error": "No response from Gemini"}
            
    except Exception as e:
        return {"error": f"Gemini generation failed: {str(e)}"}



# ==================== END NEW FUNCTIONS ====================
def read_user_input(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        return ""


def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def load_image_from_path(path: str) -> Optional[Image.Image]:
    if Image is None:
        return None
    try:
        return Image.open(path)
    except Exception:
        return None


def load_image_from_url(url: str) -> Optional[Image.Image]:
    # Deprecated: URL loading removed per new requirements
    return None


def collect_images_interactively() -> Tuple[List[str], List[str]]:
    local_paths: List[str] = []
    urls: List[str] = []

    print("\n=== IMAGE INPUT ===")
    print("You can provide:")
    print("  1. Local file paths (e.g., C:\\path\\img.jpg)")
    print("  2. URLs including Google Cloud Storage (e.g., https://storage.googleapis.com/...)")
    print("  3. Mix of both, separated by commas")
    print("\nThe script will automatically detect whether each input is a local path or URL.\n")
    
    # Single input field that accepts both paths and URLs
    p = read_user_input(
        "> Enter image paths or URLs (comma-separated): "
    )
    
    if p.strip():
        for token in p.split(","):
            item = normalize_whitespace(token).strip('"').strip()
            if item:
                # Check if it's a URL or local path
                if item.startswith(('http://', 'https://')):
                    urls.append(item)
                    print(f"  → Detected URL: {item[:60]}...")
                else:
                    local_paths.append(item)
                    print(f"  → Detected local path: {os.path.basename(item)}")

    # Optional: Additional URLs if user wants to add more
    print("\nAdd more image URLs (optional), or press Enter to continue.")
    u = read_user_input(
        "> Additional image URLs: "
    )
    if u.strip():
        for token in u.split(","):
            url = normalize_whitespace(token).strip()
            if url and url.startswith(('http://', 'https://')):
                urls.append(url)
                print(f"  → Added URL: {url[:60]}...")

    return local_paths, urls


def basic_image_keywords(paths: List[str], urls: List[str]) -> List[str]:
    keywords: List[str] = []
    for p in paths:
        base = os.path.basename(p)
        name = os.path.splitext(base)[0]
        tokens = re.split(r"[-_\s]+", name)
        for t in tokens:
            t = t.strip().lower()
            if t and t not in keywords and len(t) > 2:
                keywords.append(t)
    # URLs are no longer used for inputs
    return keywords[:25]


def summarize_images(paths: List[str], urls: List[str]) -> Dict[str, Dict[str, int]]:
    summary: Dict[str, Dict[str, int]] = {
        "local": {"count": 0},
        "urls": {"count": 0},
    }
    summary["local"]["count"] = len(paths)
    summary["urls"]["count"] = len(urls)

    if Image is not None:
        dims = []
        for p in paths:
            im = load_image_from_path(p)
            if im is not None:
                try:
                    w, h = im.size
                    dims.append((w, h))
                except Exception:
                    pass
        if dims:
            avg_w = sum(w for w, _ in dims) // len(dims)
            avg_h = sum(h for _, h in dims) // len(dims)
            summary["local"]["avg_width"] = int(avg_w)
            summary["local"]["avg_height"] = int(avg_h)
    return summary


# FAQs are generated by Gemini; no local fallback.


def build_listing(platform: str, module_name: str, keywords: List[str], price_info: Dict[str, float]) -> Dict[str, object]:
    # This function is no longer used for heuristic generation and is kept only
    # to support rendering if needed by downstream code. All fields should be
    # provided by Gemini; here we return a minimal structure with pricing.
    return {
        "platform": platform,
        "title": module_name,
        "bullets": [],
        "description": "",
        "specifications": {},
        "seo_tags": [],
        "faqs": [],
        "pricing": {
            "ai_price": price_info.get("ai_price", 0),
            "recommended_range": [price_info.get("low", 0), price_info.get("high", 0)],
        },
        "policies": {},
        "whats_in_the_box": []
    }


def render_listing(listing: Dict[str, object]) -> str:
    lines: List[str] = []
    platform = listing.get("platform", "").title()
    lines.append("=" * 90)
    lines.append(f"{platform} Listing")
    lines.append("=" * 90)
    lines.append("")
    lines.append(f"Title: {listing['title']}")
    lines.append("")
    lines.append("Key Features:")
    for b in listing["bullets"]:
        lines.append(f"  • {b}")
    lines.append("")
    lines.append("Description:")
    lines.append(textwrap.fill(listing["description"], width=100))
    lines.append("")
    lines.append("Specifications:")
    for k, v in listing["specifications"].items():
        lines.append(f"  - {k}: {v}")
    lines.append("")
    lines.append("SEO Tags:")
    lines.append("  " + ", ".join(listing["seo_tags"]))
    lines.append("")
    lines.append("Pricing:")
    pr = listing["pricing"]
    lines.append(f"  - AI Suggested Price: ₹{int(pr['ai_price'])}")
    lines.append(f"  - Recommended Range: ₹{int(pr['recommended_range'][0])} – ₹{int(pr['recommended_range'][1])}")
    lines.append("")
    lines.append("Policies:")
    for k, v in listing["policies"].items():
        lines.append(f"  - {k.title()}: {v}")
    lines.append("")
    lines.append("What's in the box:")
    for item in listing["whats_in_the_box"]:
        lines.append(f"  - {item}")
    lines.append("")
    lines.append("FAQs:")
    for q, a in listing["faqs"]:
        lines.append(f"  Q: {q}")
        lines.append(f"  A: {a}")
        lines.append("")
    return "\n".join(lines)


# ---------------- Gemini helpers ----------------

def get_gemini_client() -> Optional["genai.Client"]:
    if genai is None:
        return None
    api_key = (GEMINI_API_KEY or "").strip()
    if not api_key or api_key == "YOUR_GEMINI_API_KEY":
        return None
    try:
        if HttpOptions is not None:
            return genai.Client(api_key=api_key, http_options=HttpOptions(api_version="v1alpha"))
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def detect_mime_for_bytes(data: bytes) -> str:
    # naive detection by magic bytes
    if len(data) >= 8 and data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if len(data) >= 3 and data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    return "application/octet-stream"


def read_image_bytes(paths: List[str], urls: List[str]) -> List[Tuple[str, bytes]]:
    blobs: List[Tuple[str, bytes]] = []
    
    # Read local files
    for p in paths:
        try:
            with open(p, "rb") as f:
                b = f.read()
                blobs.append((p, b))
                print(f"✓ Loaded local file: {os.path.basename(p)}")
        except Exception as e:
            print(f"✗ Failed to load local file {p}: {str(e)}")
            continue
    
    # Fetch images from URLs (including Google Cloud Storage)
    if requests is not None:
        for url in urls:
            try:
                print(f"⬇ Downloading from URL: {url[:60]}...")
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    b = response.content
                    blobs.append((url, b))
                    print(f"✓ Downloaded from URL: {url[:60]}...")
                else:
                    print(f"✗ Failed to download {url}: HTTP {response.status_code}")
            except Exception as e:
                print(f"✗ Failed to download {url}: {str(e)}")
                continue
    else:
        if urls:
            print("⚠ requests library not available, skipping URL downloads")
    
    return blobs


def gemini_generate_listing(client: "genai.Client", model: str, platform: str, module_name: str, user_price: Optional[float], keywords: List[str], image_blobs: List[Tuple[str, bytes]]) -> Optional[Dict[str, object]]:
    """Ask Gemini to produce structured JSON for a marketplace listing from text + images."""
    system = (
        "You are an expert marketplace listing creator. Return STRICT JSON only. "
        "Target platform: " + platform + ". Follow typical best-practices for that marketplace."
    )
    instructions = (
        "Fields to return as a single JSON object: "
        "title (string), bullets (array of 5-8 short strings), description (string, 80-140 words), "
        "specifications (object of string->string), seo_tags (array of 8-15 strings), "
        "faqs (array of {q:string,a:string}), pricing ({ai_price:number, recommended_range:[number,number]}), "
        "policies (object), whats_in_the_box (array of strings). "
        "Keep brand claims generic; no restricted claims."
    )

    user_context = (
        f"Module name: {module_name}\n"
        f"User price: {user_price if user_price is not None else 'N/A'}\n"
        f"Seed keywords: {', '.join(keywords) if keywords else 'none'}\n"
        "Generate marketplace-appropriate content and price suggestions."
    )

    parts: List[object] = [
        {"text": system},
        {"text": instructions},
        {"text": user_context},
    ]
    # attach images as parts
    for name, blob in image_blobs[:6]:  # limit to a few images
        mime = detect_mime_for_bytes(blob)
        parts.append({"inline_data": {"mime_type": mime, "data": blob}})

    try:
        resp = client.models.generate_content(
            model=model,
            contents=parts,
        )
        text = getattr(resp, "text", "") or str(resp)
        # extract first top-level JSON
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            payload = text[start : end + 1]
            data = json.loads(payload)
            # minimal normalization
            if "platform" not in data:
                data["platform"] = platform
            return data
    except Exception:
        return None
    return None


def choose_platform_interactively() -> str:
    print("\nChoose a marketplace [amazon | flipkart]. Leave blank for Amazon.")
    choice = read_user_input("> Marketplace: ").strip().lower()
    if choice not in {"amazon", "flipkart", ""}:
        choice = "amazon"
    if not choice:
        choice = "amazon"
    return choice


def validate_and_adjust_price(price: Optional[float], product_name: str) -> float:
    """Validate and adjust unrealistic prices based on product type"""
    if price is None:
        return 0
    
    product_lower = product_name.lower()
    
    # Price validation logic based on product type
    if any(word in product_lower for word in ['book', 'diary', 'notebook', 'journal']):
        if price < 100:
            print(f"⚠️  Price ₹{price} seems too low for a {product_name}. Adjusting to ₹200+")
            return max(200, price * 2)
    elif any(word in product_lower for word in ['handcrafted', 'artisan', 'craft']):
        if price < 500:
            print(f"⚠️  Price ₹{price} seems too low for handcrafted {product_name}. Adjusting to ₹500+")
            return max(500, price * 2)
    elif any(word in product_lower for word in ['jewelry', 'necklace', 'ring', 'bracelet']):
        if price < 300:
            print(f"⚠️  Price ₹{price} seems too low for jewelry. Adjusting to ₹300+")
            return max(300, price * 2)
    elif any(word in product_lower for word in ['clothing', 'shirt', 'dress', 'kurta']):
        if price < 200:
            print(f"⚠️  Price ₹{price} seems too low for clothing. Adjusting to ₹200+")
            return max(200, price * 2)
    
    return price

def parse_price(value: str) -> Optional[float]:
    value = value.strip()
    if not value:
        return None
    try:
        cleaned = re.sub(r"[^0-9.]+", "", value)
        return float(cleaned) if cleaned else None
    except Exception:
        return None


def main() -> None:
    print("\n=== Product Listing Generator (Path-only, with live updates) ===\n")
    local_paths, urls = collect_images_interactively()

    module_name = read_user_input("\n> Enter a concise product/module name: ").strip()
    if not module_name:
        module_name = "Handcrafted Product"

    platform_choice = choose_platform_interactively()

    price_input = read_user_input("\n> Enter your target price (e.g., 799) or leave blank: ")
    raw_price = parse_price(price_input)
    user_price = validate_and_adjust_price(raw_price, module_name)

    inferred_keywords = basic_image_keywords(local_paths, urls)
    if not inferred_keywords:
        hint = read_user_input(
            "\n> Enter a few keywords about the product (comma-separated), or leave blank: "
        )
        if hint.strip():
            inferred_keywords = [normalize_whitespace(t).lower() for t in hint.split(",") if normalize_whitespace(t)]

    # Gemini multimodal generation (no fallbacks)
    client = get_gemini_client()
    if client is None:
        raise RuntimeError("GOOGLE_API_KEY not set or Gemini client unavailable. Set GOOGLE_API_KEY and retry.")

    # Load images from both local paths AND URLs
    print("\n[1/4] Loading images from all sources...")
    image_blobs = read_image_bytes(local_paths, urls)
    if not image_blobs:
        print("❌ No readable images found. Please check your paths/URLs. Exiting.")
        return
    
    print(f"✓ Successfully loaded {len(image_blobs)} image(s)")
    
    # Interactive image editing (only for local files, URLs are used as-is)
    print("\n[2/4] Interactive Image Editing...")
    if local_paths:
        edited_paths = interactive_image_editing(client, local_paths)
    else:
        edited_paths = []
        print("No local images to edit. Using URLs directly.")
    
    # Final confirmation before listing generation
    print("\n=== READY FOR LISTING GENERATION ===")
    print("All images have been processed. Press Enter to start generating the listing...")
    input("Press Enter to continue: ")
    
    # Analyze images (use edited versions for local, blobs for URLs)
    print("\n[3/4] Analyzing images with Gemini...")
    # Combine edited local paths with URL blobs
    all_image_sources = edited_paths if edited_paths else []
    
    # For URLs, we need to pass the blobs directly to Gemini
    if urls:
        print("Analyzing images from URLs...")
        image_descriptions = []
        # Analyze local edited images
        if all_image_sources:
            image_descriptions.extend(analyze_images_with_gemini(client, all_image_sources))
        # Analyze URL images from blobs
        for name, blob in image_blobs:
            if name.startswith(('http://', 'https://')):
                try:
                    print(f"Analyzing URL image: {name[:60]}...")
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[
                            types.Part.from_bytes(
                                data=blob,
                                mime_type='image/jpeg',
                            ),
                            "Describe this product image: materials, craftsmanship, style, use-cases, and unique selling points."
                        ],
                        config=types.GenerateContentConfig(
                            max_output_tokens=300,
                            thinking_config=types.ThinkingConfig(thinking_budget=0)
                        )
                    )
                    if response.candidates and response.candidates[0].content.parts:
                        description = response.candidates[0].content.parts[0].text
                        image_descriptions.append(description)
                        print(f"✓ Analyzed. Summary: {description[:100]}...")
                except Exception as e:
                    print(f"✗ Failed to analyze {name[:60]}: {str(e)}")
                    image_descriptions.append("Image analysis failed")
    else:
        image_descriptions = analyze_images_with_gemini(client, all_image_sources)
    
    # Build product info and single listing
    product_info = {
        "title": module_name,
        "price": user_price,
    }
    print("\n[4/4] Generating single listing for selected platform...")
    listing = generate_optimized_listing(client, platform_choice, product_info, image_descriptions)
    
    print("\n=== LISTING PREVIEW ===")
    if isinstance(listing, dict) and listing.get("title"):
        print(render_listing({
            "platform": platform_choice,
            "title": listing.get("title", module_name),
            "bullets": listing.get("bullets", []),
            "description": listing.get("description", ""),
            "specifications": listing.get("specifications", {}),
            "seo_tags": listing.get("seo_tags", []),
            "faqs": listing.get("faqs", []),
            "pricing": listing.get("pricing", {"ai_price": user_price or 0, "recommended_range": [user_price or 0, user_price or 0]}),
            "policies": listing.get("policies", {}),
            "whats_in_the_box": listing.get("whats_in_the_box", []),
        }))
    else:
        print("Listing generation returned an error:", listing)

    # Simple editing loop
    while True:
        print("\n=== EDITING OPTIONS ===")
        print("1. Edit images again")
        print("2. Regenerate listing")
        print("3. Save and exit")
        
        edit_choice = input("> Choose (1-3): ").strip()
        
        if edit_choice == "1":
            print("\n=== EDITING IMAGES AGAIN ===")
            edited_paths = interactive_image_editing(client, edited_paths)
            print("\nRe-analyzing edited images...")
            image_descriptions = analyze_images_with_gemini(client, edited_paths)
            print("\nRegenerating listing...")
            listing = generate_optimized_listing(client, platform_choice, product_info, image_descriptions)
            print("\n=== UPDATED LISTING ===")
            if isinstance(listing, dict) and listing.get("title"):
                print(render_listing({
                    "platform": platform_choice,
                    "title": listing.get("title", module_name),
                    "bullets": listing.get("bullets", []),
                    "description": listing.get("description", ""),
                    "specifications": listing.get("specifications", {}),
                    "seo_tags": listing.get("seo_tags", []),
                    "faqs": listing.get("faqs", []),
                    "pricing": listing.get("pricing", {"ai_price": user_price or 0, "recommended_range": [user_price or 0, user_price or 0]}),
                    "policies": listing.get("policies", {}),
                    "whats_in_the_box": listing.get("whats_in_the_box", []),
                }))
            else:
                print("Listing generation returned an error:", listing)
                
        elif edit_choice == "2":
            print("\nRegenerating listing...")
            listing = generate_optimized_listing(client, platform_choice, product_info, image_descriptions)
            print("\n=== REGENERATED LISTING ===")
            if isinstance(listing, dict) and listing.get("title"):
                print(render_listing({
                    "platform": platform_choice,
                    "title": listing.get("title", module_name),
                    "bullets": listing.get("bullets", []),
                    "description": listing.get("description", ""),
                    "specifications": listing.get("specifications", {}),
                    "seo_tags": listing.get("seo_tags", []),
                    "faqs": listing.get("faqs", []),
                    "pricing": listing.get("pricing", {"ai_price": user_price or 0, "recommended_range": [user_price or 0, user_price or 0]}),
                    "policies": listing.get("policies", {}),
                    "whats_in_the_box": listing.get("whats_in_the_box", []),
                }))
            else:
                print("Listing generation returned an error:", listing)
                
        elif edit_choice == "3":
            break
            
        else:
            print("Invalid choice, please try again.")

    # Save compact output to listing_output.json for backward compatibility
    out = {
        "input": {
            "module_name": module_name,
            "platform_selected": platform_choice,
            "user_price": user_price,
            "images": {
                "local_paths": edited_paths if edited_paths else local_paths,  # Use edited paths or original local
                "urls": urls,  # Include URLs used
            },
            "inferred_keywords": inferred_keywords,
        },
        "listing": listing,
    }
    try:
        with open("listing_output.json", "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print("Saved output to listing_output.json")
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)