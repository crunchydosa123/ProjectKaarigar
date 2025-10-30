#!/usr/bin/env python3
"""
news_single_card_with_image.py

CLI to generate a single news-impact card tailored to a user's profile (provided
as a JSON file) using Gemini (google.generativeai) for text and Vertex (google.genai)
for image generation.

Key behavior changes from previous script:
 - Generates **only one** card (not 6).
 - Accepts a path to a JSON file containing the profile.
 - Uses environment variables for keys/config (no hardcoded API keys).
 - Saves one generated image to ./images/card-1.png and writes a small HTML preview.

Usage:
  1) pip install google-generativeai google-cloud-aiplatform jinja2
  2) Export required environment variables:
       export GEMINI_API_KEY="your_gemini_api_key"
       export VERTEX_PROJECT="your-gcp-project"
       export VERTEX_LOCATION="us-central1"    # optional, defaults to us-central1
       export IMAGE_MODEL="imagen-3.0"         # optional, defaults to imagen-3.0
  3) Create a profile JSON file, for example profile.json:
     {
       "name": "Raj",
       "occupation": "exporter",
       "country": "India",
       "industries": "textiles, apparel",
       "business_size": "small",
       "exports": "yes",
       "tax_status": "GST registered",
       "loan_need": "small",
       "risk_tolerance": "medium",
       "description": "exports cotton fabrics to the European Union"
     }
  4) Run:
       python news_single_card_with_image.py profile.json "EU increases import tariffs on textiles"

Notes:
 - The script forces the LLM to return strict JSON with a single 'card' object:
     {"card": {"headline": "...", "card_summary":"...", "bullets":["b1",...6 items]}}
 - If parsing fails, the raw model output is printed for debugging.
 - Ensure Vertex authentication (ADC) is configured (gcloud auth application-default login
   or GOOGLE_APPLICATION_CREDENTIALS pointing to a service account JSON).
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path

# Text (Gemini) client
try:
    import google.generativeai as gtext
except Exception as e:
    print("Missing dependency 'google-generativeai'. Install with: pip install google-generativeai")
    raise

# Vertex image client
try:
    from google import genai as gvertex
    from google.genai.types import GenerateImagesConfig
except Exception as e:
    print("Missing dependency 'google.genai' (Vertex). Install/enable Vertex SDK per docs.")
    raise

# Optional templating
try:
    from jinja2 import Template
    HAVE_JINJA = True
except Exception:
    HAVE_JINJA = False

# Defaults
TEXT_MODEL = os.getenv("TEXT_MODEL", "gemini-2.0-flash-exp")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "imagen-4.0-generate-001")
OUTPUT_DIR = Path("./images")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
HTML_OUTPUT = "single_card_preview.html"


# ----------------- Helpers ----------------- #

def require_text_api_key():
    key = "AIzaSyDA6vL1W_ZcsNGQdsw3jcFjlfjBPiRjtfY"
    gtext.configure(api_key=key)


def init_vertex_client():
    project = os.getenv("VERTEX_PROJECT","karigar-475215")
    location = os.getenv("VERTEX_LOCATION", "us-central1")
    if not project:
        print("ERROR: Please set VERTEX_PROJECT environment variable for Vertex (GCP project).")
        sys.exit(1)
    client = gvertex.Client(vertexai=True, project=project, location=location)
    return client


def load_profile_from_file(profile_path: str):
    p = Path(profile_path)
    if not p.exists():
        raise FileNotFoundError(f"Profile JSON file not found: {profile_path}")
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Profile JSON must be an object/dictionary.")
    if "name" not in data or "occupation" not in data:
        raise ValueError("Profile JSON must contain at least 'name' and 'occupation' fields.")
    return data


def build_system_and_user_prompt(profile: dict, news_query: str):
    profile_json = json.dumps(profile, ensure_ascii=False)
    system = (
        "You are a precise analyst that returns ONLY JSON and nothing else. "
        "Return a single JSON object with key 'card'. The 'card' object must contain exactly these keys:\n"
        "  - 'headline' : one-line headline string\n"
        "  - 'card_summary' : one short sentence summary (single-line)\n"
        "  - 'bullets' : array of exactly 6 short sentences\n"
        "\nIMPORTANT: Do NOT include extra keys, commentary, or any text outside the JSON.\n"
    )
    user = (
        f"PROFILE: {profile_json}\n\n"
        f"NEWS/TOPIC: {news_query}\n\n"
        "Task: Produce a single news-impact card tailored to the PROFILE and NEWS/TOPIC. "
        "Make bullets specific and practical (6 items). Return ONLY the JSON described above."
    )
    return system, user


def call_gemini(system_prompt: str, user_prompt: str, model_name: str = TEXT_MODEL):
    model = gtext.GenerativeModel(model_name)
    prompt = f"{system_prompt}\n\n{user_prompt}"
    resp = model.generate_content(prompt)
    text = getattr(resp, "text", None) or str(resp)
    return text


def extract_json_from_text(text: str):
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r'(\{(?:.|\s)*\})', text)
        if not match:
            raise ValueError("Could not find JSON object in model output.")
        json_text = match.group(1)
        cleaned = re.sub(r',\s*([\]\}])', r'\1', json_text)
        return json.loads(cleaned)


def validate_card_object(obj: dict):
    if not isinstance(obj, dict):
        raise ValueError("Parsed card is not an object.")
    headline = obj.get("headline")
    summary = obj.get("card_summary")
    bullets = obj.get("bullets")
    if not headline or not isinstance(headline, str):
        raise ValueError("Card 'headline' missing or not a string.")
    if not summary or not isinstance(summary, str):
        raise ValueError("Card 'card_summary' missing or not a string.")
    if not isinstance(bullets, list) or len(bullets) != 6:
        raise ValueError("Card 'bullets' must be an array of exactly 6 strings.")
    for b in bullets:
        if not isinstance(b, str):
            raise ValueError("Each bullet must be a string.")
    return True


def generate_single_image(vertex_client, card: dict, profile: dict, index: int = 0, aspect_ratio: str = "1:1"):
    """
    Generate exactly one image (PNG) via Vertex. Prompt explicitly requests:
      - No text in the image
      - Show impact graphically (visual metaphors/icons)
    Returns saved filepath string or None on failure.
    """
    prompt_parts = [
        f"Editorial thumbnail for headline: {card.get('headline')}.",
        card.get('card_summary', ''),
        f"Visually represent the impact using graphical metaphors and icons (e.g., shrinking profit bar, rising tariff blocks, supportive hand/loan icon).",
        f"Depict the subject: a {profile.get('occupation')} from {profile.get('country')} in {profile.get('industries','')}.",
        "No text, no labels, no logos, no watermarks. Clean editorial/illustrative style, clear composition, no faces of real people.",
        "Produce a single high-quality image suitable as a UI thumbnail."
    ]
    prompt = " ".join([p for p in prompt_parts if p]).strip()
    out_path = OUTPUT_DIR / f"card-{index+1}.png"

    try:
        image = vertex_client.models.generate_images(
            model=IMAGE_MODEL,
            prompt=prompt,
            config=GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio,
            ),
        )
        img_obj = image.generated_images[0].image
        img_obj.save(str(out_path))
        return str(out_path)
    except Exception as e:
        print(f"Image generation failed: {e}")
        return None


def save_html(card_with_image: dict, profile: dict, topic: str, path: str = HTML_OUTPUT):
    template = """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8"/>
      <title>Single Card Preview</title>
      <style>
        body { font-family: Arial, sans-serif; padding: 24px; background:#f7f9fc; color:#111; }
        .card { width: 640px; background:white; border-radius:10px; padding:16px; box-shadow:0 10px 30px rgba(20,20,40,0.06); }
        .thumb { width:100%; height:320px; background:#eee; border-radius:8px; overflow:hidden; margin-bottom:12px; display:flex; align-items:center; justify-content:center; }
        .thumb img { width:100%; height:100%; object-fit:cover; }
        .headline { font-size:20px; font-weight:700; margin-bottom:8px; }
        .summary { margin-bottom:12px; color:#333; font-size:15px; }
        ol { padding-left:18px; margin:0; }
      </style>
    </head>
    <body>
      <h2>News Impact Card for {{ name }}</h2>
      <h4>Topic: {{ topic }}</h4>
      <div class="card">
        <div class="thumb">
        {% if image_path %}
          <img src="{{ image_path }}" alt="card image"/>
        {% else %}
          <div>(no image)</div>
        {% endif %}
        </div>
        <div class="headline">{{ headline }}</div>
        <div class="summary">{{ summary }}</div>
        <ol>
          {% for b in bullets %}
          <li>{{ b }}</li>
          {% endfor %}
        </ol>
      </div>
    </body>
    </html>
    """
    if HAVE_JINJA:
        tmpl = Template(template)
        html = tmpl.render(
            name=profile.get("name"),
            topic=topic,
            image_path=card_with_image.get("image_path"),
            headline=card_with_image.get("headline"),
            summary=card_with_image.get("card_summary"),
            bullets=card_with_image.get("bullets", []),
        )
    else:
        parts = []
        parts.append(f"<h2>News Impact Card for {profile.get('name')}</h2>")
        parts.append(f"<h4>Topic: {topic}</h4>")
        if card_with_image.get("image_path"):
            parts.append(f"<img src='{card_with_image['image_path']}' style='max-width:640px;'/>")
        parts.append(f"<h3>{card_with_image.get('headline')}</h3>")
        parts.append(f"<p>{card_with_image.get('card_summary')}</p>")
        parts.append("<ol>")
        for b in card_with_image.get("bullets", []):
            parts.append(f"<li>{b}</li>")
        parts.append("</ol>")
        html = "<html><body>" + "\n".join(parts) + "</body></html>"

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved preview HTML to: {os.path.abspath(path)}")


# ---- CLI ----

def parse_args():
    parser = argparse.ArgumentParser(description="Generate a single news-impact card + one image from profile JSON.")
    parser.add_argument("profile_json", help="Path to a profile JSON file")
    parser.add_argument("topic", nargs="?", help="News/topic string (if omitted you'll be prompted)")
    parser.add_argument("--no-image", action="store_true", help="Skip image generation (text-only)")
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        profile = load_profile_from_file(args.profile_json)
    except Exception as e:
        print(f"Failed to load profile: {e}")
        sys.exit(1)

    topic = args.topic
    if not topic:
        topic = input("Enter NEWS topic/headline to analyze: ").strip()
        if not topic:
            print("Empty topic. Exiting.")
            sys.exit(0)

    # Init clients
    require_text_api_key()
    vertex_client = None
    if not args.no_image:
        vertex_client = init_vertex_client()

    # Generate card text
    system_prompt, user_prompt = build_system_and_user_prompt(profile, topic)
    print("Asking Gemini for one tailored card...")
    raw = call_gemini(system_prompt, user_prompt)
    try:
        parsed = extract_json_from_text(raw)
    except Exception as e:
        print("Failed to parse JSON from Gemini output. Raw response:")
        print(raw)
        print(f"Error: {e}")
        sys.exit(1)

    # Extract card
    card_obj = parsed.get("card") if isinstance(parsed, dict) else None
    if card_obj is None:
        if isinstance(parsed, dict) and "headline" in parsed and "card_summary" in parsed:
            card_obj = parsed
        else:
            print("Model output did not include expected 'card' object. Parsed JSON:")
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
            sys.exit(1)

    # Validate
    try:
        validate_card_object(card_obj)
    except Exception as e:
        print(f"Card validation failed: {e}")
        print("Parsed card object:")
        print(json.dumps(card_obj, indent=2, ensure_ascii=False))
        sys.exit(1)

    # Generate single image (optional)
    image_path = None
    if not args.no_image and vertex_client is not None:
        print("Generating one illustrative image for the card...")
        image_path = generate_single_image(vertex_client, card_obj, profile, index=0, aspect_ratio="1:1")
        if image_path:
            print(f"Saved image to: {image_path}")
        else:
            print("Image generation failed or returned no image.")

    card_with_image = {
        "headline": card_obj.get("headline").strip(),
        "card_summary": card_obj.get("card_summary").strip(),
        "bullets": card_obj.get("bullets"),
        "image_path": image_path,
    }

    # Console output
    print("\n--- Generated Card ---")
    print(f"Headline: {card_with_image['headline']}")
    print(f"Summary: {card_with_image['card_summary']}")
    print("Bullets:")
    for i, b in enumerate(card_with_image["bullets"], 1):
        print(f"  {i}. {b}")
    print(f"Image file: {card_with_image['image_path'] or '(none)'}")
    print("----------------------\n")

    # Save HTML preview
    save_preview = input("Save HTML preview with generated image? (Y/n) [Y]: ").strip() or "Y"
    if save_preview.lower().startswith("y"):
        save_html(card_with_image, profile, topic, path=HTML_OUTPUT)

    print("Done.")


if __name__ == "__main__":
    main()