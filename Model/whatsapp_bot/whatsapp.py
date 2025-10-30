# whatsapp_bot_gemini_imagen_firestore.py
"""
WhatsApp bot using Twilio + Google Gemini (genai) + Imagen image generation,
now backed by Firestore for product storage for a hardcoded user ("user1").

Key behavior changes vs original:
 - Products are stored under Firestore path: products/{FIRESTORE_USER_ID}/items/{product_id}
 - On startup we load all products for the hardcoded user into PRODUCTS cache.
 - New products / image updates / inventory updates are written back to Firestore.
 - Image URLs are kept in Firestore as `image_urls` (list). We expose the first image as product image_url.
"""

import os
import uuid
import threading
import json
import time
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from werkzeug.utils import secure_filename
import re

# Google GenAI
from google import genai
from google.genai import types

# Firestore
from google.cloud import firestore

# ---------------------------
# Configuration (edit or use env variables)
# ---------------------------
# Gemini / GenAI
GENAI_API_KEY = os.environ.get("GENAI_API_KEY", "AIzaSyDiUMs4sIAdOk09006hS7DcY79DZh53_M4")
VERTEX_PROJECT = os.environ.get("VERTEX_PROJECT", "karigar-475215")   # optional Vertex project
VERTEX_LOCATION = os.environ.get("VERTEX_LOCATION", "us-central1")  # default location

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "ACe7815acf39a739898e084fb8f61f3edc")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "e1c5d57847356c3517fe2b2a3a7d1fdf")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
ADMIN_WHATSAPP_NUMBER = os.environ.get("ADMIN_WHATSAPP_NUMBER", "whatsapp:+917058642591")
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "verysecret")
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "https://whatsapp-bot-557742533869.asia-south1.run.app")

# Firestore user id (hardcoded per request)
FIRESTORE_USER_ID = os.environ.get("FIRESTORE_USER_ID", "user1")

# ---------------------------
# Safety checks & clients
# ---------------------------
if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN):
    print("Warning: TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN missing - Twilio sends will fail.")

# Initialize genai client (Vertex mode if VERTEX_PROJECT provided, otherwise API key)
if VERTEX_PROJECT:
    genai_client = genai.Client(vertexai=True, project=VERTEX_PROJECT, location=VERTEX_LOCATION)
elif GENAI_API_KEY:
    genai_client = genai.Client(api_key=GENAI_API_KEY)
else:
    genai_client = None
    print("Warning: genai client not configured — Gemini/Imagen calls will be skipped or fall back to defaults.")

if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
else:
    twilio_client = None

app = Flask(__name__)

# Ensure generated images folder exists
IMAGES_DIR = Path("generated_images")
IMAGES_DIR.mkdir(exist_ok=True)

# Allowed image extensions
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "gif"}

# ---------------------------
# USERS - keep a simple hardcoded test recipient set (replace with real production list)
# ---------------------------
USERS = {
    "whatsapp:+917058642591",  # test number (Siddhartha)
    "whatsapp:+919881790627",  # test number (Pratham)
    "whatsapp:+918767170653"   # test number (Suraj)
}

# ---------------------------
# Firestore initialization & helpers
# ---------------------------
def init_firestore():
    try:
        db = firestore.Client()
        app.logger.info("✅ Firestore connected successfully")
        return db
    except Exception as e:
        app.logger.exception("❌ Failed to connect to Firestore")
        raise

db = None
try:
    db = init_firestore()
except Exception as e:
    db = None
    # We proceed — code will guard Firestore usage and keep a local cache fallback.

# Local cache of products for quick reads (kept in sync)
# Each PRODUCTS[pid] contains:
# id, name, description, variants (dict keyed by sensible key), variant_order (list), variant_index_map (key->index),
# image_url, image_urls, video_urls, price, stock, ai_generated_*, created_at, updated_at, raw
PRODUCTS = {}

def product_doc_ref(pid: str):
    return db.collection("products").document(FIRESTORE_USER_ID).collection("items").document(pid)

def load_products_from_firestore():
    """Load all products for FIRESTORE_USER_ID into PRODUCTS cache, normalized to the structure used by the bot."""
    PRODUCTS.clear()
    if not db:
        app.logger.warning("Firestore not available — PRODUCTS will remain empty.")
        return
    try:
        items_ref = db.collection("products").document(FIRESTORE_USER_ID).collection("items")
        for doc in items_ref.stream():
            d = doc.to_dict() or {}
            pid = doc.id

            # Top-level price/stock if present
            top_price = d.get("price")
            top_stock = d.get("stock")

            # Normalize image_urls/video_urls
            image_urls = d.get("image_urls") or []
            video_urls = d.get("video_urls") or []

            # Normalize variants: Firestore may store variants as a list of dicts (your sample) or as a dict.
            variants_data = d.get("variants") or []
            normalized_variants = {}
            variant_order = []
            variant_index_map = {}

            if isinstance(variants_data, list):
                # Each variant is a dict with fields like size, stock, price, image_url, color...
                for idx, v in enumerate(variants_data, start=0):
                    possible_key = v.get("size") or v.get("color") or v.get("variant") or v.get("name") or v.get("key")
                    key = str(possible_key) if possible_key else f"v{idx+1}"
                    # avoid duplicate keys by appending index if needed
                    if key in normalized_variants:
                        key = f"{key}_{idx+1}"
                    # derive numeric price/inventory from variant or top-level
                    try:
                        price = float(v.get("price")) if v.get("price") is not None else (float(top_price) if top_price is not None else 0.0)
                    except Exception:
                        price = 0.0
                    try:
                        inventory = int(v.get("stock") or v.get("inventory") or top_stock or 0)
                    except Exception:
                        inventory = 0
                    normalized_variants[key] = {"price": price, "inventory": inventory, "raw": v}
                    variant_order.append(key)
                    variant_index_map[key] = idx  # index into Firestore list
            elif isinstance(variants_data, dict):
                # Often keys -> {price, inventory}
                for idx, (k, v) in enumerate(variants_data.items(), start=0):
                    try:
                        price = float(v.get("price", 0))
                    except Exception:
                        price = 0.0
                    try:
                        inventory = int(v.get("inventory", 0))
                    except Exception:
                        inventory = 0
                    normalized_variants[str(k)] = {"price": price, "inventory": inventory, "raw": v}
                    variant_order.append(str(k))
                    variant_index_map[str(k)] = None  # not a list-based storage
            else:
                # unknown shape, create a default single variant using top-level price/stock
                price = float(top_price) if top_price is not None else 0.0
                inventory = int(top_stock) if top_stock is not None else 0
                normalized_variants["default"] = {"price": price, "inventory": inventory, "raw": {}}
                variant_order.append("default")
                variant_index_map["default"] = None

            # Build PRODUCTS cache entry
            PRODUCTS[pid] = {
                "id": pid,
                "name": d.get("name") or d.get("title") or f"Product {pid}",
                "description": d.get("description", ""),
                "variants": normalized_variants,
                "variant_order": variant_order,
                "variant_index_map": variant_index_map,
                "image_url": image_urls[0] if image_urls else None,
                "image_urls": image_urls,
                "video_urls": video_urls,
                "price": float(top_price) if top_price is not None else None,
                "stock": int(top_stock) if top_stock is not None else None,
                "ai_generated_title": d.get("ai_generated_title"),
                "ai_generated_description": d.get("ai_generated_description"),
                "created_at": d.get("created_at"),
                "updated_at": d.get("updated_at"),
                "raw": d
            }

        app.logger.info("Loaded %d products for user %s from Firestore", len(PRODUCTS), FIRESTORE_USER_ID)
    except Exception:
        app.logger.exception("Failed to load products from Firestore")

def save_product_to_firestore(pid: str, product: dict, create_if_missing: bool = True):
    """Upsert product into Firestore under FIRESTORE_USER_ID. product is a dict with keys similar to PRODUCTS values."""
    if not db:
        app.logger.warning("Firestore not available — cannot save product.")
        return False
    try:
        doc_ref = product_doc_ref(pid)
        now = datetime.utcnow().isoformat() + "Z"
        # Build Firestore-friendly document
        doc = {
            "name": product.get("name"),
            "description": product.get("description", ""),
            "variants": product.get("variants", {}),
            "updated_at": now,
        }
        existing = doc_ref.get()
        if existing.exists:
            existing_data = existing.to_dict() or {}
            image_urls = existing_data.get("image_urls", [])
            doc["image_urls"] = image_urls
            doc["created_at"] = existing_data.get("created_at", existing_data.get("createdAt"))
        else:
            doc["image_urls"] = [product["image_url"]] if product.get("image_url") else []
            doc["created_at"] = now

        if product.get("image_url"):
            if product["image_url"] not in doc["image_urls"]:
                doc["image_urls"].insert(0, product["image_url"])

        # Also set top-level price/stock if provided
        if product.get("price") is not None:
            doc["price"] = product["price"]
        if product.get("stock") is not None:
            doc["stock"] = product["stock"]

        doc_ref.set(doc, merge=True)

        # update PRODUCTS cache to match saved doc
        load_products_from_firestore()
        app.logger.info("Saved product %s to Firestore (user %s)", pid, FIRESTORE_USER_ID)
        return True
    except Exception:
        app.logger.exception("Failed to save product to Firestore: %s", pid)
        return False

def append_image_url_to_product(pid: str, image_url: str):
    """Append an image URL to the Firestore product image_urls list and update cache."""
    if not db:
        app.logger.warning("Firestore not available — cannot append image_url.")
        return False
    try:
        doc_ref = product_doc_ref(pid)
        doc = doc_ref.get()
        now = datetime.utcnow().isoformat() + "Z"
        if not doc.exists:
            app.logger.warning("Product %s not found in Firestore to append image", pid)
            return False
        data = doc.to_dict() or {}
        image_urls = data.get("image_urls", [])
        if image_url not in image_urls:
            image_urls.insert(0, image_url)
        doc_ref.update({"image_urls": image_urls, "updated_at": now})
        # refresh cache
        load_products_from_firestore()
        app.logger.info("Appended image_url for %s", pid)
        return True
    except Exception:
        app.logger.exception("Failed to append image_url to product %s", pid)
        return False

# ---------------------------
# Proper transactional decrement using @firestore.transactional
# ---------------------------
@firestore.transactional
def _tx_decrement(transaction, doc_ref, variant_key, list_index, qty):
    """Transactional helper: if variants stored as list, list_index is index (int) else None.
       Returns True on success, False on insufficient stock/variant not found.
    """
    snapshot = doc_ref.get(transaction=transaction)
    if not snapshot.exists:
        return False
    data = snapshot.to_dict() or {}
    variants = data.get("variants", {}) or {}
    now = datetime.utcnow().isoformat() + "Z"

    # If Firestore stores variants as list
    if isinstance(variants, list):
        if list_index is None:
            # Try to find index by matching variant_key to variant fields
            found_idx = None
            for i, v in enumerate(variants):
                if str(v.get("size")) == variant_key or str(v.get("color")) == variant_key or str(v.get("variant")) == variant_key or str(v.get("name")) == variant_key:
                    found_idx = i
                    break
            if found_idx is None:
                # maybe variant_key is 'vN' mapping to index
                m = re.match(r"v(\d+)$", variant_key or "")
                if m:
                    idx = int(m.group(1)) - 1
                    if 0 <= idx < len(variants):
                        found_idx = idx
            if found_idx is None:
                return False
            idx = found_idx
        else:
            idx = list_index
            if idx < 0 or idx >= len(variants):
                return False
        current = int(variants[idx].get("stock") or variants[idx].get("inventory") or data.get("stock") or 0)
        if current < qty:
            return False
        # update stock
        variants[idx]["stock"] = current - qty
        transaction.update(doc_ref, {"variants": variants, "updated_at": now})
        return True

    # If Firestore stores variants as dict
    if isinstance(variants, dict):
        if variant_key not in variants:
            return False
        current = int(variants[variant_key].get("inventory", 0))
        if current < qty:
            return False
        variants[variant_key]["inventory"] = current - qty
        transaction.update(doc_ref, {"variants": variants, "updated_at": now})
        return True

    # fallback: top-level stock
    current = int(data.get("stock", 0))
    if current < qty:
        return False
    transaction.update(doc_ref, {"stock": current - qty, "updated_at": now})
    return True

def decrement_inventory_in_firestore(pid: str, variant: str, qty: int) -> bool:
    """Reduce inventory for variant by qty in Firestore and update cache.
       variant may be a key (e.g. '20') or an index-style 'v1' or '1'.
    """
    if not db:
        app.logger.warning("Firestore not available — cannot decrement inventory.")
        return False
    try:
        doc_ref = product_doc_ref(pid)
        # locate list_index if possible from cache
        list_index = None
        if pid in PRODUCTS:
            idx_map = PRODUCTS[pid].get("variant_index_map", {})
            if variant in idx_map and idx_map[variant] is not None:
                list_index = idx_map[variant]
            else:
                # if variant like 'v1' or simple number, convert to index
                m = re.match(r"^v?(\d+)$", str(variant))
                if m:
                    idx = int(m.group(1)) - 1
                    list_index = idx
                    # but we'll let transaction function validate index bounds for list vs dict
        # use transactional helper
        transaction = db.transaction()
        success = _tx_decrement(transaction, doc_ref, str(variant), list_index, int(qty))
        if success:
            load_products_from_firestore()
            app.logger.info("Decremented inventory for %s %s by %d", pid, variant, qty)
            return True
        else:
            app.logger.warning("Insufficient stock or variant not found for %s %s", pid, variant)
            return False
    except Exception:
        app.logger.exception("Failed to decrement inventory for %s %s", pid, variant)
        return False

# Load products at startup
if db:
    try:
        load_products_from_firestore()
    except Exception:
        app.logger.exception("Initial products load failed")

# ---------------------------
# Helpers (mostly unchanged)
# ---------------------------

def new_order_id():
    return str(uuid.uuid4())[:8]

def request_base_url():
    if PUBLIC_BASE_URL:
        return PUBLIC_BASE_URL.rstrip("/")
    return os.environ.get("HOST_FOR_LINKS", "http://127.0.0.1:5000").rstrip("/")

def create_payment_link(order_id: str) -> str:
    return f"{request_base_url()}/pay/{order_id}"

def send_whatsapp_message(to_whatsapp_number: str, message: str = None, media_url: str = None) -> bool:
    """Send a WhatsApp message via Twilio. Returns True on success."""
    if not twilio_client:
        app.logger.warning("Twilio client not configured - skipping send.")
        return False
    try:
        params = {"body": message or ""}
        if media_url:
            params["media_url"] = [media_url]
        msg = twilio_client.messages.create(from_=TWILIO_WHATSAPP_FROM, to=to_whatsapp_number, **params)
        app.logger.info(f"[twilio send] to={to_whatsapp_number} sid={msg.sid} media={bool(media_url)}")
        return True
    except Exception:
        app.logger.exception("Error sending WhatsApp message")
        return False

def allowed_file(filename):
    if not filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in ALLOWED_EXT

def product_image_url_for_display(p: dict) -> str:
    url = p.get("image_url")
    return url if url else "(no image)"

def format_catalog():
    """Format a catalog message using the richer product fields available in Firestore."""
    blocks = []
    if not PRODUCTS:
        return "No products found for this store."
    for p in PRODUCTS.values():
        block_lines = []
        header = f"🔹 {p['id']}: {p['name']}"
        block_lines.append(header)
        # include AI-generated title if present (short)
        if p.get("ai_generated_title"):
            block_lines.append(f"🏷️ {p.get('ai_generated_title')}")
        if p.get("description"):
            block_lines.append(p["description"])
        # top-level price/stock if present
        if p.get("price") is not None:
            if p.get("stock") is not None:
                block_lines.append(f"💰 Price: ₹{p['price']:.2f}  |  Stock: {p['stock']}")
            else:
                block_lines.append(f"💰 Price: ₹{p['price']:.2f}")
        # variants summary (enumerated)
        for i, key in enumerate(p.get("variant_order", list(p["variants"].keys())), start=1):
            info = p["variants"].get(key, {})
            try:
                price_str = f"₹{info['price']:.0f}"
            except Exception:
                price_str = f"₹{info.get('price')}"
            inventory = info.get("inventory", 0)
            # show both enumeration and underlying key (helpful when keys are sizes/colors)
            block_lines.append(f" • Variant {i} (key: {key}) — {price_str} (stock: {inventory})")
        # images/videos counts
        if p.get("image_urls"):
            block_lines.append(f"🖼️ Images: {len(p['image_urls'])} — view: {p.get('image_url')}")
        if p.get("video_urls"):
            block_lines.append(f"🎥 Videos: {len(p['video_urls'])}")
        blocks.append("\n".join(block_lines))
    blocks.append("\nReply with: order <PRODUCT_ID> <variant_key_or_vN_or_index> <qty> (e.g. order hkA092rWxK8BFmIRwkHa v1 1 or order hkA092rWxK8BFmIRwkHa 20 1)")
    return "\n\n".join(blocks)

def format_product_full(pid):
    """Show a full product detail message with images, videos, ai fields, timestamps and variant detail."""
    p = PRODUCTS.get(pid)
    if not p:
        return "Product not found."
    lines = []
    lines.append(f"🔹 {p['id']}: {p['name']}")
    if p.get("ai_generated_title"):
        lines.append(f"🏷️ {p['ai_generated_title']}")
    if p.get('description'):
        lines.append(p['description'])
    if p.get("ai_generated_description"):
        lines.append(f"🤖 {p['ai_generated_description']}")
    if p.get("price") is not None:
        lines.append(f"💰 Price: ₹{p['price']:.2f}")
    if p.get("stock") is not None:
        lines.append(f"📦 Stock: {p['stock']}")
    # Images
    if p.get("image_urls"):
        lines.append("\n📷 Images:")
        for idx, url in enumerate(p["image_urls"], start=1):
            lines.append(f"  {idx}. {url}")
    # Videos
    if p.get("video_urls"):
        lines.append("\n🎥 Videos:")
        for idx, url in enumerate(p["video_urls"], start=1):
            lines.append(f"  {idx}. {url}")
    # Variants: show enumerated variants and raw details
    if p.get("variants"):
        lines.append("\n🔀 Variants:")
        for i, key in enumerate(p.get("variant_order", list(p["variants"].keys())), start=1):
            v = p["variants"].get(key, {})
            price = v.get('price', 0)
            inv = v.get('inventory', 0)
            lines.append(f" • Variant {i} (key: {key}): price ₹{price:.2f}  stock: {inv}")
            raw = v.get("raw", {})
            if raw:
                detail_items = []
                for k in ("size", "color", "image_url", "video_url", "description"):
                    if raw.get(k) is not None and raw.get(k) != "":
                        detail_items.append(f"{k}: {raw.get(k)}")
                if detail_items:
                    lines.append("    " + " | ".join(detail_items))
    # timestamps
    if p.get("created_at"):
        lines.append(f"\nCreated: {p.get('created_at')}")
    if p.get("updated_at"):
        lines.append(f"Updated: {p.get('updated_at')}")
    lines.append("\nReply with: order <PRODUCT_ID> <variant_key_or_vN_or_index> <qty>")
    return "\n".join(lines)

def order_summary_text(order):
    lines = [f"Order #{order['order_id']}"]
    for d in order["details"]:
        lines.append(f"- {d['quantity']} x {d['product_name']} ({d['variant']}) — ₹{d['price']:.2f}")
    lines.append(f"Total: ₹{order['total']:.2f}")
    lines.append(f"Status: {order['status']}")
    return "\n".join(lines)

# ---------------------------
# Gemini helpers (unchanged except small fixes)
# ---------------------------

def gemini_parse_user_message(user_message: str):
    fallback = {"intent": "unknown", "product_id": None, "variant": None, "quantity": None,
                "reply": "Sorry, I couldn't understand. Send 'catalog' to view products or 'order <PRODUCT_ID> <variant> <qty>' to order."}
    if not genai_client:
        return {"intent": "unknown", "product_id": None, "variant": None, "quantity": None,
                "reply": "GenAI not configured — try 'catalog' or 'order <PRODUCT_ID> <variant> <qty>'."}

    prod_list = "".join([f"{p['id']}: {p['name']} " for p in PRODUCTS.values()])
    prompt = ("You are a parser that MUST return exactly one JSON object (no extra commentary). "
        "Available products:" + prod_list + " "
        "Return JSON with fields: intent (catalog|inventory|order|help|unknown), product_id (or null), "
        "variant (or null), quantity (number or null), reply (short message to send back). "
        "Examples: "
        '{"intent":"catalog","product_id":null,"variant":null,"quantity":null,"reply":"Here is the catalog..."} '
        '{"intent":"order","product_id":"P001","variant":"M","quantity":2,"reply":"Ordering P001 M x2..."} '
        f"User message: '''{user_message}''' Return only the JSON object."
    )
    try:
        resp = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=300, thinking_config=types.ThinkingConfig(thinking_budget=0))
        )
        text = resp.text.strip()
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_text = text[start:end+1]
            parsed = json.loads(json_text)
            parsed.setdefault("intent", "unknown")
            parsed.setdefault("product_id", None)
            parsed.setdefault("variant", None)
            parsed.setdefault("quantity", None)
            parsed.setdefault("reply", "")
            return parsed
        return {"intent": "unknown", "product_id": None, "variant": None, "quantity": None, "reply": text}
    except Exception:
        app.logger.exception("Gemini parse failed")
        return fallback

def gemini_generate_marketing(product_id: str, prompt_text: str = None):
    p = PRODUCTS.get(product_id)
    if not p:
        return "Product not found."

    base = f"Write a short WhatsApp promotional message for the product below. Include price and a call-to-action to reply 'order {product_id}'. Keep it one paragraph."
    if prompt_text:
        prompt_text = prompt_text.strip()
        base = prompt_text + " " + base

    content = (
        f"{base} Product: ID: {p['id']} Name: {p['name']} Description: {p['description']} Variants: "
        + " ".join([f"- {v}: ₹{info['price']:.0f}" for v, info in p['variants'].items()])
    )
    if not genai_client:
        return f"{p['name']} — {p['description']} (Variants: {', '.join(p['variants'].keys())}). Reply 'order {p['id']}' to buy."

    try:
        resp = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=content,
            config=types.GenerateContentConfig(max_output_tokens=200, thinking_config=types.ThinkingConfig(thinking_budget=0))
        )
        text = resp.text.strip()
        first_para = text.split("\n\n")[0].strip()
        return first_para
    except Exception:
        app.logger.exception("Gemini marketing failed")
        return f"{p['name']} — {p['description']}. Reply 'order {p['id']}' to buy."

def gemini_generate_from_prompt(prompt_text: str):
    if not genai_client:
        return prompt_text or "Promotion"

    prompt_text = prompt_text.strip()
    content = f"Write a short WhatsApp promotional message (one paragraph) based on the following instruction: {prompt_text}"
    try:
        resp = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=content,
            config=types.GenerateContentConfig(max_output_tokens=200, thinking_config=types.ThinkingConfig(thinking_budget=0))
        )
        text = resp.text.strip()
        first_para = text.split("\n\n")[0].strip()
        return first_para
    except Exception:
        app.logger.exception("Gemini creative generation failed")
        return prompt_text or "Special offer! Reply to order."

# ---------------------------
# Imagen (image generation) helper (unchanged behavior, but updates Firestore)
# ---------------------------
def generate_image_for_product(product_id: str, prompt_text: str = None) -> str:
    if not genai_client:
        app.logger.warning("genai client not configured - skipping image generation")
        return None

    p = PRODUCTS.get(product_id)
    if not p:
        app.logger.warning("Product not found for image generation: %s", product_id)
        return None

    default_prompt = (
        f"Product photo of '{p['name']}'. {p['description']}. "
        "E-commerce style, clean white background, studio lighting, high resolution, realistic photograph."
    )
    prompt = (prompt_text.strip() + " " + default_prompt) if prompt_text else default_prompt

    try:
        model_name = "imagen-4.0-generate-001"
        img_resp = genai_client.models.generate_images(
            model=model_name,
            prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="1:1")
        )
        image_obj = img_resp.generated_images[0]
        filename = f"{product_id}_{int(time.time())}.png"
        filepath = IMAGES_DIR / filename
        try:
            image_obj.image.save(str(filepath))
        except Exception:
            try:
                b = image_obj.image.image_bytes
                with open(filepath, "wb") as f:
                    f.write(b)
            except Exception:
                app.logger.exception("Failed to save generated image to disk")
                return None

        public_url = f"{request_base_url()}/images/{filename}"
        app.logger.info("Generated image saved: %s (url=%s)", filepath, public_url)
        # Update Firestore product image_urls
        append_image_url_to_product(product_id, public_url)
        return public_url
    except Exception:
        app.logger.exception("Image generation failed")
        return None

# ---------------------------
# Serve generated images
# ---------------------------
@app.route("/images/<path:filename>", methods=["GET"])
def serve_image(filename):
    return send_from_directory(str(IMAGES_DIR.resolve()), filename)

# ---------------------------
# Payment templates & routes (unchanged)
# ---------------------------
PAY_PAGE_TEMPLATE = """
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Pay Order {{order_id}}</title></head>
  <body>
    <h2>Pay Order {{order_id}}</h2>
    <pre>{{summary}}</pre>
    <form method="post" action="/pay/{{order_id}}/confirm">
      <button type="submit" style="padding:12px 20px; font-size:16px;">Pay ₹{{amount}}</button>
    </form>
  </body>
</html>
"""

PAID_PAGE_TEMPLATE = """
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>Payment Complete</title></head>
  <body>
    <h2>Payment successful</h2>
    <p>Thank you — payment for order {{order_id}} completed.</p>
    <p>You should receive a WhatsApp confirmation shortly.</p>
  </body>
</html>
"""

ORDERS = {}
SESSIONS = {}

@app.route("/pay/<order_id>", methods=["GET"])
def pay_page(order_id):
    order = ORDERS.get(order_id)
    if not order:
        return "Order not found", 404
    summary = "".join([f"{d['quantity']} x {d['product_name']} ({d['variant']}) - ₹{d['price']:.2f}\n" for d in order['details']])
    return render_template_string(PAY_PAGE_TEMPLATE, order_id=order_id, summary=summary, amount=f"{order['total']:.2f}")

@app.route("/pay/<order_id>/confirm", methods=["POST"])
def pay_confirm(order_id):
    order = ORDERS.get(order_id)
    if not order:
        return "Order not found", 404
    if order.get("status") == "paid":
        return render_template_string(PAID_PAGE_TEMPLATE, order_id=order_id)
    order["status"] = "paid"
    order["paid_at"] = datetime.utcnow().isoformat() + "Z"
    to_whatsapp = order["user"]
    send_whatsapp_message(to_whatsapp, f"✅ Payment received for Order #{order_id}. Thank you!\n\n{order_summary_text(order)}")
    return render_template_string(PAID_PAGE_TEMPLATE, order_id=order_id)

# ---------------------------
# Twilio webhook for incoming user messages (unchanged logic but uses Firestore-backed PRODUCTS)
# Supports variant keys or index-style 'v1' or '1'.
# ---------------------------
@app.route("/bot", methods=["POST"])
def bot():
    from_number = (request.values.get("From") or "").strip()
    body = (request.values.get("Body") or "").strip()
    resp = MessagingResponse()
    if not from_number:
        resp.message("Sender not detected.")
        return str(resp)

    parsed = gemini_parse_user_message(body)
    intent = parsed.get("intent", "unknown")

    if intent == "catalog":
        resp.message("📚 Catalog:" + format_catalog())
        return str(resp)

    if intent == "inventory" and parsed.get("product_id"):
        pid = parsed.get("product_id")
        resp.message(format_product_full(pid))
        return str(resp)

    if intent == "order" and parsed.get("product_id"):
        pid = parsed.get("product_id")
        if pid not in PRODUCTS:
            resp.message("Product not found.")
            return str(resp)

        # Resolve variant: accept key, 'vN' or simple numeric index
        raw_variant = parsed.get("variant")
        chosen_variant = None
        # default to first variant if none provided
        if not raw_variant:
            chosen_variant = PRODUCTS[pid]["variant_order"][0]
        else:
            raw_variant = str(raw_variant).strip()
            variants = PRODUCTS[pid]["variants"]
            # Direct key match
            if raw_variant in variants:
                chosen_variant = raw_variant
            else:
                # vN style or numeric index
                m = re.match(r"^v?(\d+)$", raw_variant)
                if m:
                    idx = int(m.group(1)) - 1
                    order_list = PRODUCTS[pid].get("variant_order", list(variants.keys()))
                    if 0 <= idx < len(order_list):
                        chosen_variant = order_list[idx]
                # fallback: maybe user provided the value of a field (e.g., size '20'); try to match that
                if not chosen_variant:
                    for k, info in variants.items():
                        raw_fields = info.get("raw", {})
                        if any(str(raw_fields.get(field)) == raw_variant for field in ("size", "color", "variant", "name", "key")):
                            chosen_variant = k
                            break

        if not chosen_variant:
            resp.message(f"Variant {raw_variant} not found. Available: {', '.join(PRODUCTS[pid]['variant_order'])}")
            return str(resp)

        try:
            qty = int(parsed.get("quantity") or 1)
        except:
            qty = 1

        info = PRODUCTS[pid]["variants"].get(chosen_variant)
        if not info:
            resp.message(f"Variant {chosen_variant} not found. Available: {', '.join(PRODUCTS[pid]['variant_order'])}")
            return str(resp)
        if info["inventory"] < qty:
            resp.message(f"Only {info['inventory']} available for variant {chosen_variant}. Reduce quantity.")
            return str(resp)

        # Attempt to decrement inventory in Firestore
        ok = decrement_inventory_in_firestore(pid, chosen_variant, qty)
        if not ok:
            resp.message(f"Failed to place order: insufficient stock or error. Try again.")
            return str(resp)

        oid = new_order_id()
        total = info["price"] * qty
        order = {
            "order_id": oid,
            "user": from_number,
            "product_id": pid,
            "product_name": PRODUCTS[pid]["name"],
            "variant": chosen_variant,
            "quantity": qty,
            "details": [{"product_id": pid, "product_name": PRODUCTS[pid]["name"], "variant": chosen_variant, "quantity": qty, "price": total}],
            "total": total,
            "status": "pending_payment",
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        ORDERS[oid] = order
        pay_link = create_payment_link(oid)
        resp.message(f"✅ Order {oid} created. Total: ₹{total:.2f}\nPay here: {pay_link}")
        return str(resp)

    reply_text = parsed.get("reply") or "Sorry, I didn't understand. Send 'catalog' to view products or 'order <PRODUCT_ID> <variant> <qty>' to order."
    resp.message(reply_text)
    return str(resp)

# ---------------------------
# Admin: add product (HTTP) -> generate marketing + image -> broadcast to USERS
# Uses Firestore to store the product under FIRESTORE_USER_ID
# ---------------------------
@app.route("/admin/add_product", methods=["POST"])
def admin_add_product():
    key = request.args.get("key") or request.headers.get("X-ADMIN-KEY")
    if key != ADMIN_API_KEY:
        return jsonify({"error": "invalid admin key"}), 403

    # Support either JSON body or multipart form (for image uploads)
    data = None
    if request.content_type and request.content_type.startswith("multipart/form-data"):
        # form fields
        data = {k: request.form.get(k) for k in request.form.keys()}
    else:
        data = request.get_json(force=True, silent=True) or {}

    name = data.get("name")
    description = data.get("description", "")
    variants = None
    if isinstance(data.get("variants"), dict):
        variants = data.get("variants")
    else:
        # allow variants as JSON string in form-data
        try:
            variants = json.loads(data.get("variants")) if data.get("variants") else None
        except Exception:
            variants = None

    prompt = data.get("prompt")
    generate_image_flag = data.get("generate_image", True)

    if not name or not variants or not isinstance(variants, dict):
        return jsonify({"error": "name and variants required (variants as JSON/dict)"}), 400

    pid = data.get("id") or f"P{str(len(PRODUCTS)+1).zfill(3)}"
    norm = {}
    try:
        for k, v in variants.items():
            norm[str(k)] = {"price": float(v["price"]), "inventory": int(v.get("inventory", 0))}
    except Exception:
        return jsonify({"error": "invalid variant format"}), 400

    # Prepare product skeleton
    product = {"id": pid, "name": name, "description": description, "variants": norm, "image_url": None}

    # If form included an image file, save and attach
    if request.files:
        file = request.files.get("image")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique = f"prod_{pid}_{int(time.time())}_{uuid.uuid4().hex[:6]}_{filename}"
            filepath = IMAGES_DIR / unique
            file.save(str(filepath))
            product["image_url"] = f"{request_base_url()}/images/{unique}"
            app.logger.info("Saved product image for %s: %s", pid, filepath)

    # If generate_image_flag and genai available and no uploaded image, create an image and attach (overrides if none provided)
    if generate_image_flag and genai_client and not product.get("image_url"):
        try:
            imgurl = generate_image_for_product(pid, prompt)
            if imgurl:
                product["image_url"] = imgurl
        except Exception:
            app.logger.exception("Image generation failed for new product")

    # Save to Firestore
    saved = save_product_to_firestore(pid, product)
    if not saved:
        return jsonify({"error": "failed to save product to Firestore"}), 500

    try:
        marketing_text = gemini_generate_marketing(pid, prompt)
    except Exception:
        app.logger.exception("Gemini marketing generation failed")
        marketing_text = f"{name} — {description}. Reply 'order {pid}' to buy."

    image_url = PRODUCTS[pid].get("image_url")

    broadcast_msg = marketing_text
    def do_broadcast():
        sent = 0
        for u in list(USERS):
            ok = send_whatsapp_message(u, message=broadcast_msg, media_url=image_url)
            if ok:
                sent += 1
        app.logger.info("Broadcast done: %d/%d", sent, len(USERS))
    threading.Thread(target=do_broadcast, daemon=True).start()

    return jsonify({"status": "product_added", "product": PRODUCTS[pid], "notified_count": len(USERS), "image_url": image_url}), 201

# ---------------------------
# NEW ROUTE:
# Accepts a prompt and an image (multipart/form-data) and sends marketing text + image
# Mirrors the /admin/add_product flow and updates product image if product_id provided and image uploaded.
# ---------------------------
@app.route("/admin/send_prompt_image", methods=["POST"])
def admin_send_prompt_image():
    key = request.args.get("key") or request.headers.get("X-ADMIN-KEY")
    if key != ADMIN_API_KEY:
        return jsonify({"error": "invalid admin key"}), 403

    prompt = (request.form.get("prompt") or request.values.get("prompt") or "").strip()
    product_id = (request.form.get("product_id") or request.values.get("product_id") or "").strip() or None
    file = request.files.get("image")

    # Must have at least one of prompt, product_id, or image
    if not (prompt or product_id or file):
        return jsonify({"error": "provide at least one of: prompt, product_id, image"}), 400

    image_url = None
    if file:
        filename = secure_filename(file.filename)
        if not filename or not allowed_file(filename):
            return jsonify({"error": "invalid image file or extension"}), 400
        unique = f"upload_{int(time.time())}_{uuid.uuid4().hex[:6]}_{filename}"
        filepath = IMAGES_DIR / unique
        file.save(str(filepath))
        image_url = f"{request_base_url()}/images/{unique}"
        app.logger.info("Uploaded image saved: %s", filepath)

        # If tied to a product, update that product's image_urls in Firestore so catalog will show it
        if product_id and db and product_id in PRODUCTS:
            append_image_url_to_product(product_id, image_url)
        elif product_id and db:
            # create basic product doc if not exists
            product = {"id": product_id, "name": f"Product {product_id}", "description": "", "variants": {}, "image_url": image_url}
            save_product_to_firestore(product_id, product)

    # If no file uploaded but product_id present, we can optionally generate an image (like add_product)
    if not image_url and product_id and genai_client:
        try:
            image_url = generate_image_for_product(product_id, prompt)
            if image_url and product_id in PRODUCTS:
                PRODUCTS[product_id]["image_url"] = image_url
        except Exception:
            app.logger.exception("Image generation failed for send_prompt_image")
            image_url = None

    # Build marketing text using same helpers as add_product
    marketing_text = None
    if product_id:
        if product_id not in PRODUCTS:
            return jsonify({"error": f"product_id {product_id} not found"}), 400
        try:
            marketing_text = gemini_generate_marketing(product_id, prompt)
        except Exception:
            app.logger.exception("Gemini generation failed for product")
            marketing_text = f"{PRODUCTS[product_id]['name']} — {PRODUCTS[product_id]['description']}. Reply 'order {product_id}' to buy."
    else:
        if not prompt:
            return jsonify({"error": "prompt required when product_id not provided"}), 400
        try:
            marketing_text = gemini_generate_from_prompt(prompt)
        except Exception:
            app.logger.exception("Gemini generation failed for prompt")
            marketing_text = prompt

    # Start async broadcast thread to match /admin/add_product behavior
    broadcast_msg = marketing_text
    def do_broadcast():
        sent = 0
        for u in list(USERS):
            ok = send_whatsapp_message(u, message=broadcast_msg, media_url=image_url)
            if ok:
                sent += 1
        app.logger.info("send_prompt_image broadcast done: %d/%d", sent, len(USERS))

    threading.Thread(target=do_broadcast, daemon=True).start()

    # Return immediately with similar structure to add_product
    return jsonify({
        "status": "sent",
        "message": marketing_text,
        "image_url": image_url,
        "notified_count": len(USERS)
    }), 200

# ---------------------------
# Debug endpoints
# ---------------------------
@app.route("/debug/users", methods=["GET"])
def debug_users():
    return jsonify(sorted(list(USERS)))

@app.route("/debug/products", methods=["GET"])
def debug_products():
    # Return the cached PRODUCTS and raw Firestore data
    return jsonify(PRODUCTS)

@app.route("/debug/orders", methods=["GET"])
def debug_orders():
    return jsonify(list(ORDERS.values()))

# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    print("Starting WhatsApp + Gemini + Imagen bot (Firestore-backed for user: %s)." % FIRESTORE_USER_ID)
    if not PUBLIC_BASE_URL:
        print("Warning: PUBLIC_BASE_URL not set — payment and image links may not be reachable externally.")
    # Ensure products cache loaded if Firestore available
    if db:
        try:
            load_products_from_firestore()
        except Exception:
            app.logger.exception("Failed to load products on startup.")

    # ✅ Use the port Cloud Run provides
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
