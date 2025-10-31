#!/usr/bin/env python3
"""
kaarigar_advisor_text_only.py

Generates 6 practical, motivating, data-driven advisory paragraphs tailored to a local
artisan (Kaarigar) from a provided profile JSON file using Gemini (google.generativeai).

This variant also fetches relevant web links (government schemes, portals, training
program pages) using the Google Custom Search JSON API and includes them in the HTML preview.

Usage:
 1) pip install google-generativeai jinja2 requests
 2) export GEMINI_API_KEY="your_gemini_api_key"
    export GOOGLE_API_KEY="your_google_api_key"    # for Custom Search JSON API
    export GOOGLE_CX="your_search_engine_id"       # Programmable Search Engine ID (CX)
 3) Create profile.json (example in header of prior message)
 4) Run:
     python kaarigar_advisor_text_only.py profile.json
"""

import os
import sys
import json
import re
import argparse
import requests
from pathlib import Path

try:
    import google.generativeai as gtext
except Exception:
    print("Missing dependency 'google-generativeai'. Install with: pip install google-generativeai")
    raise

try:
    from jinja2 import Template
    HAVE_JINJA = True
except Exception:
    HAVE_JINJA = False

# Defaults
TEXT_MODEL = os.getenv("TEXT_MODEL", "gemini-2.0-flash-exp")
HTML_OUTPUT = "six_insights_preview.html"
MAX_SEARCH_QUERIES = 4
RESULTS_PER_QUERY = 3
REQUEST_TIMEOUT = 10  # seconds for HTTP requests

# ----------------- Helpers ----------------- #

def require_text_api_key():
    key ="AIzaSyDA6vL1W_ZcsNGQdsw3jcFjlfjBPiRjtfY"
    gtext.configure(api_key=key)


def load_profile_from_file(profile_path: str):
    p = Path(profile_path)
    if not p.exists():
        raise FileNotFoundError(f"Profile JSON file not found: {profile_path}")
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Profile JSON must be an object/dictionary.")
    # Not strict about keys; default a name if missing
    if "name" not in data or not data.get("name"):
        data.setdefault("name", "Artisan")
    return data


def build_system_and_user_prompt(profile: dict):
    profile_json = json.dumps(profile, ensure_ascii=False)
    system = (
        "You are an experienced business & craft advisor for local artisans (Kaarigars)."
        " Provide practical, data-driven, and motivating advice."
        " RETURN ONLY A JSON OBJECT and nothing else."
        " The JSON must have a single key 'insights' whose value is an array of exactly six strings."
        " Each string should be a short paragraph (2-5 sentences) and cover one of these topics in order:\n"
        " 1) Government schemes or initiatives that can support this artisan.\n"
        " 2) Current sales trends and market demand related to their craft.\n"
        " 3) Opportunities to expand online and offline reach.\n"
        " 4) Suggestions for improving product quality, design, or branding.\n"
        " 5) Financial or training programs they can benefit from.\n"
        " 6) Future trends and innovations relevant to their work.\n"
        "Do NOT include additional keys, commentary, code fences, or explanation outside the JSON."
    )
    user = (
        f"PROFILE: {profile_json}\n\n"
        "Task: Based on the PROFILE produce 6 practical, actionable, and motivating paragraphs as described above."
        " Make each paragraph specific to the PROFILE (use region, product, materials, price_range, experience etc.)."
        " Where appropriate, cite concrete action steps (for example: which portal to check, what keywords to use online, which documents to prepare)."
        " Keep tone encouraging and focused on growth."
    )
    return system, user


def call_gemini(system_prompt: str, user_prompt: str, model_name: str = TEXT_MODEL):
    model = gtext.GenerativeModel(model_name)
    prompt = f"{system_prompt}\n\n{user_prompt}"
    resp = model.generate_content(prompt)
    text = getattr(resp, "text", None) or str(resp)
    return text


# --- Google Custom Search helper ---

def google_search(search_term: str, api_key: str, cx_id: str, num_results: int = 3):
    """
    Performs a Google Custom Search (Programmable Search Engine) request and returns a list of
    result dicts: {title, snippet, link}
    """
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
        # non-fatal: warn and return empty list
        print(f"Warning: Google search for '{search_term}' failed: {e}")
        return []


def build_search_queries(profile: dict):
    """
    Build a small prioritized list of searches likely to surface official scheme pages
    and training/financial resources for the artisan.
    """
    queries = []
    region = profile.get("region") or profile.get("country") or ""
    skill = profile.get("skill") or "artisan"
    product = profile.get("product") or "handicraft"
    material = profile.get("material") or ""
    country = profile.get("country") or ("India" if "India" in (region or "") else "")

    # Region-specific queries
    if region:
        queries.append(f"{region} artisan support schemes")
    # Craft + country queries
    if skill:
        queries.append(f"{skill} artisan government schemes {country}".strip())
    queries.append(f"MSME schemes for artisans {country}".strip())
    queries.append(f"handicraft schemes {country}".strip())

    # Product/material specific queries
    if product:
        queries.append(f"support schemes for {product} artisans {country}".strip())
    if material:
        queries.append(f"{material} {skill} training programs {country}".strip())

    # Deduplicate preserving order and limit count
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


def extract_json_from_text(text: str):
    # Try strict JSON first
    try:
        return json.loads(text)
    except Exception:
        # Find first JSON object in the output
        match = re.search(r'(\{(?:.|\s)*\})', text)
        if not match:
            raise ValueError("Could not find JSON object in model output.")
        json_text = match.group(1)
        # remove trailing commas before closing ] or }
        cleaned = re.sub(r',\s*([\]\}])', r'\1', json_text)
        return json.loads(cleaned)


def validate_insights(obj: dict):
    if not isinstance(obj, dict):
        raise ValueError("Parsed output is not a JSON object.")
    insights = obj.get("insights")
    if not isinstance(insights, list) or len(insights) != 6:
        raise ValueError("'insights' must be an array of exactly 6 strings.")
    for i, s in enumerate(insights):
        if not isinstance(s, str) or len(s.strip()) == 0:
            raise ValueError(f"Insight #{i+1} is not a non-empty string.")
    return True


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
        .links { margin-top:18px; }
        .link-group { margin-bottom:12px; }
        .link-group a { display:block; word-break:break-all; }
      </style>
    </head>
    <body>
      <div class="box">
        <h1>Advisory for {{ name }}</h1>
        <h3>Profile snapshot: {{ snapshot }}</h3>
        <hr/>
        <ol>
        {% for s in insights %}
          <li><p>{{ s }}</p></li>
        {% endfor %}
        </ol>

        <div class="links">
          <h3>Relevant links & resources (from web searches)</h3>
          {% if links %}
            {% for q, items in links.items() %}
              <div class="link-group">
                <strong>Search:</strong> {{ q }}
                {% if items %}
                  {% for it in items %}
                    <a href="{{ it.link }}" target="_blank">{{ it.title or it.link }}</a>
                    <div style="font-size:13px;color:#555;margin-bottom:6px;">{{ it.snippet }}</div>
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
        parts = [f"<h1>Advisory for {profile.get('name')}</h1>", f"<h3>Profile: {snapshot}</h3>", "<ol>"]
        for s in insights_obj.get("insights", []):
            parts.append(f"<li><p>{s}</p></li>")
        parts.append("</ol>")
        parts.append("<h3>Relevant links (web search)</h3>")
        for q, items in links.items():
            parts.append(f"<h4>Search: {q}</h4>")
            if items:
                for it in items:
                    parts.append(f"<div><a href='{it['link']}'>{it.get('title') or it.get('link')}</a><div>{it.get('snippet')}</div></div>")
            else:
                parts.append("<div>No results.</div>")
        html = "<html><body>" + "\n".join(parts) + "</body></html>"

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved preview HTML to: {os.path.abspath(path)}")


# ---- CLI ----

def parse_args():
    parser = argparse.ArgumentParser(description="Generate 6 advisory paragraphs for a Kaarigar from profile JSON and fetch related links.")
    parser.add_argument("profile_json", help="Path to a profile JSON file")
    parser.add_argument("--no-preview", action="store_true", help="Do not save HTML preview")
    parser.add_argument("--no-search", action="store_true", help="Do not perform web searches for related links")
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        profile = load_profile_from_file(args.profile_json)
    except Exception as e:
        print(f"Failed to load profile: {e}")
        sys.exit(1)

    # Init Gemini
    require_text_api_key()

    system_prompt, user_prompt = build_system_and_user_prompt(profile)
    print("Asking Gemini for 6 advisory paragraphs tailored to the profile...")
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

    print("\n--- Six Advisory Paragraphs ---\n")
    for i, p in enumerate(insights, 1):
        print(f"[{i}] {p}\n")

    links_results = {}
    if not args.no_search:
        google_api_key = "AIzaSyA-FSI1OrvEgzkcZYmSfp_QAU5SaOu6ekg"
        google_cx = "96fe143fecdae4723"
        if not google_api_key or not google_cx:
            print("Skipping web searches because GOOGLE_API_KEY or GOOGLE_CX environment variables are not set.")
        else:
            queries = build_search_queries(profile)
            for q in queries:
                results = google_search(q, google_api_key, google_cx, num_results=RESULTS_PER_QUERY)
                links_results[q] = results

    if not args.no_preview:
        save_html(parsed, profile, links_results, path=HTML_OUTPUT)

    print("Done.")

    # Final JSON output to stdout
    output = {
        "profile": profile,
        "insights": insights,
        "links": links_results
    }
    # Print machine-readable JSON to stdout only
    print(json.dumps(output, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
