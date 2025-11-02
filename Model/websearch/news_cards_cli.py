#!/usr/bin/env python3
"""
kaarigar_advisor_with_images_and_gcs.py

Enhanced script based on the user's original:
 - Generates 6 advisory paragraphs (Gemini)
 - Each insight includes a 5-6 word 'title' and 'text'
 - Generates an image for each insight via Vertex AI Imagen (google.genai)
 - Uploads generated images to Google Cloud Storage (bucket: all_in_one_bucket1)
 - Returns GCS public URL for each image and includes those links in the final JSON
 - Produces an HTML preview embedding the image URLs

USAGE:
 1) pip install google-generativeai google-genai google-cloud-storage jinja2 requests
 2) Make sure GOOGLE_APPLICATION_CREDENTIALS is set for GCS access (or gcloud auth application-default login)
 3) Ensure Vertex AI access is configured for the project "karigar-475215"
 4) Run:
      python kaarigar_advisor_with_images_and_gcs.py profile.json

IMPORTANT:
 - This script intentionally retains the hardcoded API keys present in the original
   (as requested). Keep them secure and remove/hide in production.
"""

import os
import sys
import json
import re
import argparse
import requests
from pathlib import Path

# Gemini text API (google-generativeai)
try:
    import google.generativeai as gtext
except Exception:
    print("Missing dependency 'google-generativeai'. Install with: pip install google-generativeai")
    raise

# Vertex AI image generation (google-genai)
try:
    from google import genai
    from google.genai.types import GenerateImagesConfig
except Exception:
    print("Missing dependency 'google-genai'. Install with: pip install google-genai")
    raise

# Google Cloud Storage
try:
    from google.cloud import storage
except Exception:
    print("Missing dependency 'google-cloud-storage'. Install with: pip install google-cloud-storage")
    raise

# Jinja2 for HTML preview (optional)
try:
    from jinja2 import Template
    HAVE_JINJA = True
except Exception:
    HAVE_JINJA = False

# Defaults / constants
TEXT_MODEL = os.getenv("TEXT_MODEL", "gemini-2.0-flash-exp")
HTML_OUTPUT = "six_insights_preview.html"
MAX_SEARCH_QUERIES = 4
RESULTS_PER_QUERY = 3
REQUEST_TIMEOUT = 10  # seconds
GCS_BUCKET_NAME = "all_in_one_bucket1"  # as requested by user
GCS_IMAGES_PREFIX = "kaarigar_images"    # folder in bucket to store images

# ----------------- Helpers ----------------- #

def require_text_api_key():
    # Intentional hardcoded key preserved as requested
    key = ""  # TODO: Set your Google API Key
    gtext.configure(api_key=key)


def load_profile_from_file(profile_path: str):
    p = Path(profile_path)
    if not p.exists():
        raise FileNotFoundError(f"Profile JSON file not found: {profile_path}")
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Profile JSON must be an object/dictionary.")
    data.setdefault("name", "Artisan")
    return data


def build_system_and_user_prompt(profile: dict):
    profile_json = json.dumps(profile, ensure_ascii=False)
    system = (
        "You are an experienced business & craft advisor for local artisans (Kaarigars). "
        "Provide practical, data-driven, and motivating advice. RETURN ONLY A JSON OBJECT and nothing else. "
        "The JSON must have a single key 'insights' whose value is an array of exactly six objects. "
        "Each object must have two keys: 'title' and 'text'. "
        " - 'title' should be a 5-6 word description summarizing the insight (concise phrase). "
        " - 'text' should be a short paragraph (2-5 sentences) specifically tailored to the PROFILE. "
        "Do NOT include extra keys or commentary outside the JSON.\n"
        "Topics (in order):\n"
        "1) Government schemes or initiatives\n"
        "2) Current sales trends and market demand\n"
        "3) Opportunities to expand online and offline reach\n"
        "4) Suggestions for improving product quality, design, or branding\n"
        "5) Financial or training programs they can benefit from\n"
        "6) Future trends and innovations relevant to their work\n"
    )
    user = (
        f"PROFILE: {profile_json}\n\n"
        "Task: Based on the PROFILE produce 6 actionable, motivating advisory entries as described above."
        " Make each entry specific to the PROFILE (use region, product, materials, price_range, experience, etc.)."
        " Where appropriate, cite concrete action steps (for example: which portal to check, what keywords to use online,"
        " which documents to prepare). Keep tone encouraging and growth-focused."
    )
    return system, user


def call_gemini(system_prompt: str, user_prompt: str, model_name: str = TEXT_MODEL):
    model = gtext.GenerativeModel(model_name)
    prompt = f"{system_prompt}\n\n{user_prompt}"
    resp = model.generate_content(prompt)
    return getattr(resp, "text", None) or str(resp)


# --- Vertex AI / Imagen image generation + save file --- #
def generate_image_local(title: str, index: int, project="karigar-475215", location="us-central1"):
    """
    Generates an image with Vertex AI (google-genai) and saves a local PNG file.
    Returns the local filename on success, or None on failure.
    """
    try:
        client = genai.Client(
            vertexai=True,
            project=project,
            location=location
        )

        # Use a descriptive prompt based on the title; keep it simple and concrete
        prompt = f"High-quality, evocative illustration representing: {title}. Clean composition, clear subject, 1:1 aspect ratio."

        image = client.models.generate_images(
            model="imagen-4.0-generate-001",
            prompt=prompt,
            config=GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",
            ),
        )

        output_file = f"insight_{index+1}.png"
        # The returned object has .generated_images[0].image.save()
        image.generated_images[0].image.save(output_file)
        print(f"✅ Generated local image: {output_file}")
        return output_file
    except Exception as e:
        print(f"⚠️ Image generation failed for '{title}': {e}")
        return None


# --- Google Cloud Storage helper --- #
def upload_blob_to_gcs(local_file_path: str, destination_blob_name: str, make_public: bool = True):
    """
    Uploads a local file to the configured GCS bucket and returns a public URL (if make_public True)
    or a gs:// URL fallback.
    """
    try:
        client = storage.Client()  # will pick up credentials from env or gcloud
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(local_file_path)
        if make_public:
            try:
                blob.make_public()
                public_url = blob.public_url
                print(f"📤 Uploaded and made public: {public_url}")
                return public_url
            except Exception as e:
                print(f"⚠️ Uploaded but failed to make public: {e}")
                # Fallback to gs:// URL
                return f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"
        else:
            return f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"
    except Exception as e:
        print(f"❌ Failed to upload {local_file_path} to GCS: {e}")
        return None


# --- Google Custom Search helper (unchanged, credentials preserved) --- #
def google_search(search_term: str, api_key: str, cx_id: str, num_results: int = 3):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cx_id,
        "q": search_term,
        "num": max(1, min(10, num_results))
    }
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        results = []
        for it in items:
            results.append({
                "title": it.get("title"),
                "snippet": it.get("snippet"),
                "link": it.get("link")
            })
        return results
    except Exception as e:
        print(f"Warning: Google search for '{search_term}' failed: {e}")
        return []


def build_search_queries(profile: dict):
    queries = []
    region = profile.get("region") or profile.get("country") or ""
    skill = profile.get("skill") or "artisan"
    product = profile.get("product") or "handicraft"
    material = profile.get("material") or ""
    country = profile.get("country") or ("India" if "India" in (region or "") else "")

    if region:
        queries.append(f"{region} artisan support schemes")
    if skill:
        queries.append(f"{skill} artisan government schemes {country}".strip())
    queries.append(f"MSME schemes for artisans {country}".strip())
    queries.append(f"handicraft schemes {country}".strip())
    if product:
        queries.append(f"support schemes for {product} artisans {country}".strip())
    if material:
        queries.append(f"{material} {skill} training programs {country}".strip())

    seen = set()
    out = []
    for q in queries:
        qn = q.lower()
        if qn and qn not in seen:
            out.append(q)
            seen.add(qn)
        if len(out) >= MAX_SEARCH_QUERIES:
            break
    return out


# --- JSON extraction & validation --- #
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


def validate_insights(obj: dict):
    if not isinstance(obj, dict):
        raise ValueError("Parsed output is not a JSON object.")
    insights = obj.get("insights")
    if not isinstance(insights, list) or len(insights) != 6:
        raise ValueError("'insights' must be an array of exactly 6 items.")
    for i, it in enumerate(insights):
        if not isinstance(it, dict):
            raise ValueError(f"Insight #{i+1} must be an object with 'title' and 'text'.")
        if "title" not in it or "text" not in it:
            raise ValueError(f"Insight #{i+1} missing 'title' or 'text'.")
        if not isinstance(it["title"], str) or not isinstance(it["text"], str):
            raise ValueError(f"Insight #{i+1} 'title' and 'text' must be strings.")
    return True


# --- HTML preview save --- #
def save_html(insights_obj: dict, profile: dict, links: dict, path: str = HTML_OUTPUT):
    template = """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8"/>
      <title>Kaarigar Advisory - Preview</title>
      <style>
        body { font-family: Arial, sans-serif; padding: 24px; background:#f7f9fc; color:#111; }
        .box { max-width:980px; margin:0 auto; background:white; border-radius:10px; padding:20px; box-shadow:0 8px 24px rgba(20,20,40,0.06); }
        h1 { font-size:22px; margin-bottom:6px; }
        h3 { font-size:14px; color:#555; margin-top:0; }
        p { line-height:1.5; }
        ol { padding-left:18px; }
        .insight { margin-bottom:20px; }
        img { max-width:360px; border-radius:8px; display:block; margin-top:8px; margin-bottom:8px; }
      </style>
    </head>
    <body>
      <div class="box">
        <h1>Advisory for {{ name }}</h1>
        <h3>Profile snapshot: {{ snapshot }}</h3>
        <hr/>
        <ol>
        {% for s in insights %}
          <li class="insight">
            <strong>{{ s.title }}</strong>
            {% if s.image_url %}
              <div><a href="{{ s.image_url }}" target="_blank"><img src="{{ s.image_url }}" alt="{{ s.title }}"/></a></div>
            {% endif %}
            <p>{{ s.text }}</p>
          </li>
        {% endfor %}
        </ol>

        <div class="links">
          <h3>Relevant links & resources (from web searches)</h3>
          {% if links %}
            {% for q, items in links.items() %}
              <div style="margin-bottom:12px;">
                <strong>Search:</strong> {{ q }}
                {% if items %}
                  {% for it in items %}
                    <div style="margin-top:6px;"><a href="{{ it.link }}" target="_blank">{{ it.title or it.link }}</a>
                      <div style="font-size:13px;color:#555;">{{ it.snippet }}</div>
                    </div>
                  {% endfor %}
                {% else %}
                  <div style="color:#777;">No results found or search failed.</div>
                {% endif %}
              </div>
            {% endfor %}
          {% else %}
            <div style="color:#777;">No web search performed. Set GOOGLE_API_KEY and GOOGLE_CX environment variables to enable.</div>
          {% endif %}
        </div>

      </div>
    </body>
    </html>
    """
    snapshot = ", ".join([f"{k}: {v}" for k, v in profile.items() if v])
    if HAVE_JINJA:
        tmpl = Template(template)
        html = tmpl.render(name=profile.get("name"), snapshot=snapshot, insights=insights_obj.get("insights", []), links=links)
    else:
        # Minimal fallback
        parts = [f"<h1>Advisory for {profile.get('name')}</h1>", f"<h3>Profile: {snapshot}</h3>", "<ol>"]
        for s in insights_obj.get("insights", []):
            parts.append(f"<li><strong>{s.get('title')}</strong>")
            if s.get("image_url"):
                parts.append(f"<div><img src='{s.get('image_url')}' style='max-width:360px'></div>")
            parts.append(f"<p>{s.get('text')}</p></li>")
        parts.append("</ol>")
        html = "<html><body>" + "\n".join(parts) + "</body></html>"

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved preview HTML to: {os.path.abspath(path)}")


# ---- CLI ----
def parse_args():
    parser = argparse.ArgumentParser(description="Generate 6 advisory paragraphs for a Kaarigar and images uploaded to GCS.")
    parser.add_argument("profile_json", help="Path to a profile JSON file")
    parser.add_argument("--no-preview", action="store_true", help="Do not save HTML preview")
    parser.add_argument("--no-search", action="store_true", help="Do not perform web searches for related links")
    parser.add_argument("--no-images", action="store_true", help="Skip image generation entirely")
    parser.add_argument("--no-upload", action="store_true", help="Generate images locally but do not upload to GCS (image_url will be local path)")
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        profile = load_profile_from_file(args.profile_json)
    except Exception as e:
        print(f"Failed to load profile: {e}")
        sys.exit(1)

    # Init Gemini text API
    require_text_api_key()

    system_prompt, user_prompt = build_system_and_user_prompt(profile)
    print("Asking Gemini for 6 advisory paragraphs with titles...")
    raw = call_gemini(system_prompt, user_prompt)

    try:
        parsed = extract_json_from_text(raw)
    except Exception as e:
        print("Failed to parse JSON from Gemini output. Raw response:")
        print(raw)
        print(f"Error: {e}")
        sys.exit(1)

    try:
        validate_insights(parsed)
    except Exception as e:
        print(f"Validation failed: {e}")
        print("Parsed JSON:")
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
        sys.exit(1)

    insights = parsed.get("insights")

    # For each insight, optionally generate image and upload
    for i, ins in enumerate(insights):
        # Ensure title brevity: we trust the model but truncate if too long
        title = ins.get("title", "").strip()
        if not title:
            # fallback title
            title = f"Insight {i+1}"
            ins["title"] = title

        if args.no_images:
            ins["image_local"] = None
            ins["image_url"] = None
            continue

        # 1) Generate local image
        local_image = generate_image_local(title, i)
        ins["image_local"] = local_image

        # 2) Upload to GCS (unless user specified --no-upload)
        if local_image and not args.no_upload:
            # Build destination path: e.g. kaarigar_images/<profile_name_sanitized>/insight_1.png
            profile_name = profile.get("name", "artisan").lower().replace(" ", "_")
            destination_name = f"{GCS_IMAGES_PREFIX}/{profile_name}/insight_{i+1}.png"
            public_url = upload_blob_to_gcs(local_image, destination_name, make_public=True)
            ins["image_url"] = public_url
        else:
            # Use local path as image_url (useful for local preview)
            ins["image_url"] = os.path.abspath(local_image) if local_image else None

    # Optional web searches for relevant links
    links_results = {}
    if not args.no_search:
        # TODO: Set your credentials
        google_api_key = ""  # TODO: Set your Google API Key
        google_cx = ""  # TODO: Set your Custom Search Engine ID
        if not google_api_key or not google_cx:
            print("Skipping web searches because GOOGLE_API_KEY or GOOGLE_CX not set.")
        else:
            queries = build_search_queries(profile)
            for q in queries:
                results = google_search(q, google_api_key, google_cx, num_results=RESULTS_PER_QUERY)
                links_results[q] = results

    # Save HTML preview (if requested)
    if not args.no_preview:
        save_html(parsed, profile, links_results, path=HTML_OUTPUT)

    # Final JSON output (profile, insights with image_url, links)
    output = {
        "profile": profile,
        "insights": insights,
        "links": links_results
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))
    print("Done.")


if __name__ == "__main__":
    main()
