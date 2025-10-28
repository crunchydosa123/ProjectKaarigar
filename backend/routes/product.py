from flask import Blueprint, request, jsonify, session
from datetime import datetime
from google.cloud import firestore
import os
import json
import requests
from urllib.parse import urlparse
from pathlib import Path
from google import genai

# Blueprint
product_bp = Blueprint('product_bp', __name__)

# Firestore client
try:
    db = firestore.Client()
    FIRESTORE_AVAILABLE = True
except Exception as e:
    print(f"❌ Failed to init Firestore for product routes: {e}")
    db = None
    FIRESTORE_AVAILABLE = False

# GenAI Client for AI generation
GENAI_CLIENT = None
try:
    project_id = os.getenv("VERTEX_PROJECT", "useful-figure-475210-g7")
    location = os.getenv("VERTEX_LOCATION", "us-central1")
    GENAI_CLIENT = genai.Client(vertexai=True, project=project_id, location=location)
    print(f"✅ GenAI client initialized for project: {project_id}, location: {location}")
except Exception as e:
    print(f"⚠️ GenAI client initialization failed: {e}")
    GENAI_CLIENT = None


def get_user_from_session():
    if not session.get('is_authenticated'):
        raise ValueError("Not authenticated")
    user_id = session.get('user_id')
    if not user_id:
        raise ValueError("User ID not found in session")
    return user_id


def _collect_user_media(user_id: str):
    """Collect user's images and videos from media collection.
    Returns (images, videos) where each is a list of dicts with id, title, public_url, filename.
    """
    images = []
    videos = []

    if not FIRESTORE_AVAILABLE:
        return images, videos

    try:
        # Uploaded Images
        images_ref = db.collection("media").document(user_id).collection("uploadmedia").document("media_data").collection("images")
        for doc in images_ref.get():
            data = doc.to_dict() or {}
            if data.get('is_active', True) and data.get('public_url'):
                images.append({
                    "id": doc.id,
                    "title": data.get('title') or data.get('original_filename') or data.get('filename') or 'Image',
                    "public_url": data.get('public_url'),
                    "filename": data.get('filename')
                })

        # Generated Images (including edited)
        gen_images_ref = db.collection("media").document(user_id).collection("uploadmedia").document("media_data").collection("_generated_images")
        for doc in gen_images_ref.get():
            data = doc.to_dict() or {}
            if data.get('is_active', True) and data.get('public_url'):
                images.append({
                    "id": doc.id,
                    "title": data.get('title') or data.get('filename') or 'Generated Image',
                    "public_url": data.get('public_url'),
                    "filename": data.get('filename')
                })

        # Uploaded Videos
        videos_ref = db.collection("media").document(user_id).collection("uploadmedia").document("media_data").collection("videos")
        for doc in videos_ref.get():
            data = doc.to_dict() or {}
            if data.get('is_active', True) and data.get('public_url'):
                videos.append({
                    "id": doc.id,
                    "title": data.get('title') or data.get('filename') or 'Video',
                    "public_url": data.get('public_url'),
                    "filename": data.get('filename')
                })

        # Generated Reels
        reels_ref = db.collection("media").document(user_id).collection("uploadmedia").document("media_data").collection("_generated_reels")
        for doc in reels_ref.get():
            data = doc.to_dict() or {}
            if data.get('public_url'):
                videos.append({
                    "id": doc.id,
                    "title": data.get('title') or 'Generated Reel',
                    "public_url": data.get('public_url'),
                    "filename": data.get('filename') if 'filename' in data else None
                })
    except Exception as e:
        print(f"⚠️ Failed to collect media for user {user_id}: {e}")

    return images, videos


def _resolve_media_urls_by_ids(user_id: str, image_ids, video_ids):
    image_urls = []
    video_urls = []

    if not FIRESTORE_AVAILABLE:
        return image_urls, video_urls

    # Helper to fetch a doc by trying multiple subcollections
    def fetch_media_doc(subpath: str, doc_id: str):
        return db.collection("media").document(user_id).collection("uploadmedia").document("media_data").collection(subpath).document(doc_id).get()

    # Images: look in uploaded images and _generated_images
    for img_id in image_ids or []:
        try:
            doc = fetch_media_doc("images", img_id)
            if not doc.exists:
                doc = fetch_media_doc("_generated_images", img_id)
            if doc.exists:
                data = doc.to_dict() or {}
                if data.get('public_url'):
                    image_urls.append(data['public_url'])
        except Exception as e:
            print(f"⚠️ Failed resolving image id {img_id}: {e}")

    # Videos: look in uploaded videos and _generated_reels
    for vid_id in video_ids or []:
        try:
            doc = fetch_media_doc("videos", vid_id)
            if not doc.exists:
                doc = fetch_media_doc("_generated_reels", vid_id)
            if doc.exists:
                data = doc.to_dict() or {}
                if data.get('public_url'):
                    video_urls.append(data['public_url'])
        except Exception as e:
            print(f"⚠️ Failed resolving video id {vid_id}: {e}")

    return image_urls, video_urls


@product_bp.route('/media', methods=['GET'])
def list_available_media():
    """Return current user's images and videos to choose while creating a product."""
    try:
        user_id = get_user_from_session()
        images, videos = _collect_user_media(user_id)
        return jsonify({
            "success": True,
            "images": images,
            "videos": videos,
            "images_count": len(images),
            "videos_count": len(videos)
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ /product/media error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@product_bp.route('/create', methods=['POST'])
def create_product():
    """Create a product document under products/{user_id}/items/{autoId}."""
    try:
        if not FIRESTORE_AVAILABLE:
            return jsonify({"error": "Database not available"}), 500

        user_id = get_user_from_session()
        data = request.get_json() or {}

        # Extract fields
        name = (data.get('name') or '').strip()
        description = (data.get('description') or '').strip()
        price = data.get('price')
        stock = data.get('stock')
        currency = (data.get('currency') or 'INR').strip()
        variants = data.get('variants') or []
        image_ids = data.get('image_ids') or []
        video_ids = data.get('video_ids') or []
        image_urls_input = data.get('image_urls') or []
        video_urls_input = data.get('video_urls') or []

        # Basic validation
        if not name:
            return jsonify({"error": "Product name is required"}), 400

        # Resolve URLs from ids
        resolved_image_urls, resolved_video_urls = _resolve_media_urls_by_ids(user_id, image_ids, video_ids)

        # Combine provided URLs with resolved
        image_urls = list({*image_urls_input, *resolved_image_urls})
        video_urls = list({*video_urls_input, *resolved_video_urls})

        # Build product document
        product_doc = {
            "user_id": user_id,
            "name": name,
            "description": description,
            "price": price,
            "stock": stock,
            "currency": currency or "INR",
            "variants": variants,
            "image_ids": image_ids,
            "video_ids": video_ids,
            "image_urls": image_urls,
            "video_urls": video_urls,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "is_active": True,
        }

        # Save under products/{user_id}/items/{auto}
        items_ref = db.collection("products").document(user_id).collection("items")
        doc_ref = items_ref.document()
        doc_ref.set(product_doc)

        return jsonify({
            "success": True,
            "message": "Product created",
            "product_id": doc_ref.id
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ /product/create error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@product_bp.route('/update/<product_id>', methods=['PUT', 'PATCH'])
def update_product(product_id: str):
    """Update an existing product. Only the owner (session user) may update.

    Accepts partial fields in JSON body. If image_ids/video_ids are provided,
    their URLs will be resolved and merged with provided image_urls/video_urls.
    """
    try:
        if not FIRESTORE_AVAILABLE:
            return jsonify({"error": "Database not available"}), 500

        user_id = get_user_from_session()
        data = request.get_json() or {}

        items_ref = db.collection("products").document(user_id).collection("items")
        doc_ref = items_ref.document(product_id)
        doc = doc_ref.get()

        if not doc.exists:
            # The product might belong to another user or not exist
            return jsonify({"error": "Product not found"}), 404

        existing = doc.to_dict() or {}

        # Verify ownership: stored user_id on document must match session user
        owner_id = existing.get('user_id')
        if owner_id != user_id:
            return jsonify({"error": "Forbidden"}), 403

        # Extract updatable fields (allow partial updates)
        name = data.get('name')
        description = data.get('description')
        price = data.get('price')
        stock = data.get('stock')
        currency = data.get('currency')
        variants = data.get('variants')
        image_ids = data.get('image_ids')
        video_ids = data.get('video_ids')
        image_urls_input = data.get('image_urls')
        video_urls_input = data.get('video_urls')

        # Resolve any provided ids into URLs (if provided)
        resolved_image_urls, resolved_video_urls = _resolve_media_urls_by_ids(user_id, image_ids, video_ids)

        # Merge existing lists with new inputs where appropriate
        image_urls = existing.get('image_urls', [])
        video_urls = existing.get('video_urls', [])

        # If caller provided explicit image_urls/video_urls, prefer them (but merge unique)
        if image_urls_input is not None:
            image_urls = list({*image_urls_input, *resolved_image_urls})
        else:
            # merge resolved ids with existing
            image_urls = list({*image_urls, *resolved_image_urls})

        if video_urls_input is not None:
            video_urls = list({*video_urls_input, *resolved_video_urls})
        else:
            video_urls = list({*video_urls, *resolved_video_urls})

        # Build update document
        update_doc = {
            'updated_at': datetime.utcnow().isoformat(),
        }

        # Only set keys if provided (allow clearing by explicit null)
        if name is not None:
            update_doc['name'] = name.strip() if isinstance(name, str) else name
        if description is not None:
            update_doc['description'] = description.strip() if isinstance(description, str) else description
        if price is not None:
            update_doc['price'] = price
        if stock is not None:
            update_doc['stock'] = stock
        if currency is not None:
            update_doc['currency'] = currency
        if variants is not None:
            update_doc['variants'] = variants

        # Always update image/video ids and urls if present in request (even empty lists)
        if image_ids is not None:
            update_doc['image_ids'] = image_ids
        if video_ids is not None:
            update_doc['video_ids'] = video_ids

        update_doc['image_urls'] = image_urls
        update_doc['video_urls'] = video_urls

        # Apply update
        doc_ref.update(update_doc)

        return jsonify({"success": True, "message": "Product updated"}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ /product/update error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@product_bp.route('/list', methods=['GET'])
def list_products():
    """List products for current user from products/{user_id}/items."""
    try:
        if not FIRESTORE_AVAILABLE:
            return jsonify({"error": "Database not available"}), 500

        user_id = get_user_from_session()
        items_ref = db.collection("products").document(user_id).collection("items")
        products = []
        for doc in items_ref.get():
            data = doc.to_dict() or {}
            data["id"] = doc.id
            products.append(data)

        # Newest first by created_at
        products.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return jsonify({
            "success": True,
            "products": products,
            "count": len(products)
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ /product/list error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@product_bp.route('/ai-generate/<product_id>', methods=['POST'])
def ai_generate_product_content(product_id: str):
    """
    Generate AI title and description for a product using its image and description.
    Takes the first image URL and current description as input to GenAI.
    Returns: { success: bool, ai_generated_title: str, ai_generated_description: str }
    """
    try:
        if not FIRESTORE_AVAILABLE:
            return jsonify({"error": "Database not available"}), 500

        if not GENAI_CLIENT:
            return jsonify({"error": "AI service not configured"}), 500

        user_id = get_user_from_session()
        
        # Fetch the product
        items_ref = db.collection("products").document(user_id).collection("items")
        doc_ref = items_ref.document(product_id)
        doc = doc_ref.get()

        if not doc.exists:
            return jsonify({"error": "Product not found"}), 404

        product_data = doc.to_dict() or {}
        
        # Verify ownership
        if product_data.get('user_id') != user_id:
            return jsonify({"error": "Forbidden"}), 403

        # Get image URL and description
        image_urls = product_data.get('image_urls', [])
        if not image_urls:
            return jsonify({"error": "Product must have at least one image for AI generation"}), 400
        
        image_url = image_urls[0]
        description = product_data.get('description', '')
        product_name = product_data.get('name', '')

        # Download image
        try:
            resp = requests.get(image_url, timeout=15)
            resp.raise_for_status()
            image_bytes = resp.content
        except Exception as e:
            return jsonify({"error": f"Failed to download product image: {str(e)}"}), 400

        # Determine MIME type
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
            mime_type = mime_map.get(ext, "image/jpeg")
        except Exception:
            mime_type = "image/jpeg"

        # Build prompt
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

        # Call GenAI
        try:
            response = GENAI_CLIENT.models.generate_content(
                model="gemini-2.0-flash",
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
            return jsonify({"error": f"AI generation failed: {str(e)}"}), 500

        raw_text = getattr(response, "text", None) or str(response)

        # Parse JSON response
        ai_title = ""
        ai_description = ""
        
        try:
            parsed = json.loads(raw_text)
            ai_title = parsed.get("title", "")
            ai_description = parsed.get("description", "")
        except Exception:
            # Fallback parsing
            lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
            for line in lines:
                lw = line.lower()
                if '"title"' in lw or lw.startswith("title:"):
                    idx = line.find(":")
                    candidate = line[idx + 1:].strip() if idx != -1 else line
                    candidate = candidate.strip().strip('",').strip("'")
                    if candidate:
                        ai_title = candidate
                if '"description"' in lw or lw.startswith("description:"):
                    idx = line.find(":")
                    candidate = line[idx + 1:].strip() if idx != -1 else line
                    candidate = candidate.strip().strip('",').strip("'")
                    if candidate:
                        ai_description = candidate

            if not ai_title and lines:
                ai_title = lines[0].strip().strip('",').strip("'")
            if not ai_description and len(lines) >= 2:
                ai_description = " ".join(lines[1:3])

        # Update product with AI-generated content
        update_doc = {
            'ai_generated_title': ai_title,
            'ai_generated_description': ai_description,
            'updated_at': datetime.utcnow().isoformat(),
        }
        doc_ref.update(update_doc)

        return jsonify({
            "success": True,
            "ai_generated_title": ai_title,
            "ai_generated_description": ai_description,
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        print(f"❌ /product/ai-generate error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500


@product_bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "product",
        "firestore_available": FIRESTORE_AVAILABLE
    })


