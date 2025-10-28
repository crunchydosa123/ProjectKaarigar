from flask import Blueprint, request, jsonify, session
from datetime import datetime
from google.cloud import firestore

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


@product_bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "product",
        "firestore_available": FIRESTORE_AVAILABLE
    })


