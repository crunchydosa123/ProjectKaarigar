"""
Simplified model to generate AI title and AI description from an image URL and product description.

Key points:
- Does NOT validate GOOGLE_APPLICATION_CREDENTIALS locally. Assumes credentials are already provided
  in the environment (as you indicated).
- Accepts image URLs (HTTP/HTTPS) and product descriptions.
- Returns only an AI-generated title and AI-generated description.
- Uses Vertex AI / GenAI client (google.genai).
"""

from typing import Optional, Dict
from urllib.parse import urlparse
from pathlib import Path
import requests
import json
import os

from google import genai


# Default configuration (override when constructing the class if needed)
DEFAULT_PROJECT_ID = "useful-figure-475210-g7"
DEFAULT_LOCATION = "us-central1"
DEFAULT_MODEL = "gemini-2.0-flash"


class TitleDescriptionGenerator:
    """
    Minimal generator that takes an image URL and a text description and returns:
      { "title": "...", "description": "..." }
    """

    def __init__(
        self,
        project_id: str = DEFAULT_PROJECT_ID,
        location: str = DEFAULT_LOCATION,
        model: str = DEFAULT_MODEL,
    ):
        """
        Initialize the GenAI client. This does not check for local credential files;
        it assumes GOOGLE_APPLICATION_CREDENTIALS (or other ADC) is already configured in the environment.
        """
        self.project_id = project_id
        self.location = location
        self.model = model

        try:
            self.client = genai.Client(vertexai=True, project=project_id, location=location)
        except Exception as e:
            # Initialize failure is fatal for this module usage
            raise RuntimeError(f"Failed to initialize GenAI client: {e}")

    @staticmethod
    def _get_mime_type_from_url(image_url: str) -> str:
        """
        Very small helper to determine mime type from URL path extension.
        Defaults to image/jpeg.
        """
        try:
            path = urlparse(image_url).path
            ext = Path(path).suffix.lower()
            mime_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
                ".bmp": "image/bmp",
            }
            return mime_map.get(ext, "image/jpeg")
        except Exception:
            return "image/jpeg"

    def _download_image(self, image_url: str, timeout: int = 15) -> bytes:
        """
        Download image bytes from the given URL.
        Raises requests.HTTPError on non-200 responses.
        """
        resp = requests.get(image_url, timeout=timeout)
        resp.raise_for_status()
        return resp.content

    def generate(self, image_url: str, description: str, product_name: Optional[str] = None) -> Dict:
        """
        Generate a short SEO-friendly title and a 2-3 sentence product description.

        Returns:
          {
            "status": "success"|"error",
            "data": {
              "title": "...",
              "description": "..."
            },
            "raw_response": "<raw model output>"
          }
        """
        if not image_url:
            return {"status": "error", "message": "image_url is required", "data": None}

        # Download image
        try:
            image_bytes = self._download_image(image_url)
        except Exception as e:
            return {"status": "error", "message": f"Failed to download image: {e}", "data": None}

        mime_type = self._get_mime_type_from_url(image_url)

        # Build a strict prompt so the model returns JSON only with 'title' and 'description' keys.
        # We ask for a JSON-only response to make parsing straightforward.
        prompt = (
            "You are a product listing writer. Analyze the provided product image and the short product "
            "description and return ONLY a valid JSON object with exactly two keys: "
            "\"title\" and \"description\".\n\n"
            "Requirements:\n"
            "- title: one short SEO-friendly product title (5-12 words max).\n"
            "- description: 2-3 professional, engaging sentences describing the product and benefits.\n"
            "- Do NOT include any other keys, commentary, or wrapping text. Return pure JSON only.\n\n"
            f"Product Name (if any): {product_name or 'Not specified'}\n"
            f"Product Description: {description}\n\n"
            "Now produce the JSON."
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    genai.types.Content(
                        role="user",
                        parts=[
                            genai.types.Part(text=prompt),
                            genai.types.Part(
                                inline_data=genai.types.Blob(
                                    mime_type=mime_type,
                                    data=image_bytes
                                )
                            ),
                        ],
                    )
                ],
            )
        except Exception as e:
            return {"status": "error", "message": f"Model request failed: {e}", "data": None}

        raw_text = getattr(response, "text", None) or str(response)

        # Try to parse JSON directly
        try:
            parsed = json.loads(raw_text)
            # Defensive: ensure keys exist
            ai_title = parsed.get("title") if isinstance(parsed, dict) else None
            ai_description = parsed.get("description") if isinstance(parsed, dict) else None

            if not ai_title or not ai_description:
                # Fall through to fallback parsing below
                raise ValueError("Missing title/description in model JSON response")

            return {
                "status": "success",
                "data": {"title": ai_title, "description": ai_description},
                "raw_response": raw_text,
            }

        except Exception:
            # Fallback: attempt to extract simple "title" and "description" lines using heuristic parsing.
            # Look for lines like: "title": "..." or Title: ...
            title = None
            desc = None

            # Try simple heuristics
            lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
            for i, line in enumerate(lines):
                lw = line.lower()
                if '"title"' in lw or lw.startswith("title:") or lw.startswith("title "):
                    # extract after colon or quote
                    try:
                        # attempt JSON-ish extraction
                        idx = line.find(":")
                        candidate = line[idx + 1 :].strip() if idx != -1 else line
                        # strip quotes and trailing commas
                        candidate = candidate.strip().strip('",').strip("'")
                        if candidate:
                            title = candidate
                    except Exception:
                        pass
                if '"description"' in lw or lw.startswith("description:") or lw.startswith("description "):
                    try:
                        idx = line.find(":")
                        candidate = line[idx + 1 :].strip() if idx != -1 else line
                        candidate = candidate.strip().strip('",').strip("'")
                        if candidate:
                            desc = candidate
                    except Exception:
                        pass

            # If still missing, attempt to use first line as title and next 1-2 lines as description
            if not title and lines:
                title = lines[0].strip().strip('",').strip("'")
            if not desc and len(lines) >= 2:
                desc = " ".join(lines[1:3])

            # Final sanity check
            if not title:
                title = ""
            if not desc:
                desc = ""

            return {
                "status": "success",
                "data": {"title": title, "description": desc},
                "raw_response": raw_text,
            }


if __name__ == "__main__":
    # Simple CLI for convenience
    import argparse

    parser = argparse.ArgumentParser(description="Generate AI title and description from image URL + text.")
    parser.add_argument("--image_url", required=False, help="Image URL (http/https). If omitted, will prompt.")
    parser.add_argument("--description", required=False, help="Short product description. If omitted, will prompt.")
    parser.add_argument("--product_name", required=False, help="Optional product name.")
    parser.add_argument("--project_id", required=False, help="GCP Project ID", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--location", required=False, help="Vertex AI location", default=DEFAULT_LOCATION)
    args = parser.parse_args()

    if not args.image_url:
        args.image_url = input("Image URL: ").strip()
    if not args.description:
        args.description = input("Product description: ").strip()

    gen = TitleDescriptionGenerator(project_id=args.project_id, location=args.location)
    result = gen.generate(image_url=args.image_url, description=args.description, product_name=args.product_name)
    print(json.dumps(result, indent=2, ensure_ascii=False))