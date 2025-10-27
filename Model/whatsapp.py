# whatsapp_bot_gemini_imagen.py
"""
WhatsApp bot using Twilio + Google Gemini (genai) + Imagen image generation.

Added route:
  POST /admin/send_prompt_image
    - headers or query: key=<ADMIN_API_KEY>
    - form fields:
        prompt (text, optional if product_id present)
        product_id (optional)
        image (file, optional)
    - Behavior:
        * Saves uploaded image (if any) to ./generated_images and serves at /images/<filename>
        * Generates marketing text using Gemini:
            - if product_id provided -> gemini_generate_marketing(product_id, prompt)
            - else -> gemini_generate_from_prompt(prompt)
        * Sends marketing text (and uploaded image as media) to all USERS (async broadcast, like /admin/add_product)
        * Returns JSON with message body, image_url, and notified_count

This version adds product image support and includes image URLs in the catalog and product details so customers can click the links to view images.
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

# Google GenAI
from google import genai
from google.genai import types

# ---------------------------
# Configuration (edit or use env variables)
# ---------------------------
# Gemini / GenAI
GENAI_API_KEY = os.environ.get("GENAI_API_KEY", "AIzaSyDiUMs4sIAdOk09006hS7DcY79DZh53_M4")  # set your key or leave empty for offline mode
VERTEX_PROJECT = os.environ.get("VERTEX_PROJECT", "useful-figure-475210-g7")   # optional Vertex project
VERTEX_LOCATION = os.environ.get("VERTEX_LOCATION", "us-central1")  # default location

TWILIO_ACCOUNT_SID = "ACe7815acf39a739898e084fb8f61f3edc"
TWILIO_AUTH_TOKEN = "e1c5d57847356c3517fe2b2a3a7d1fdf"
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
ADMIN_WHATSAPP_NUMBER = "whatsapp:+917058642591"
ADMIN_API_KEY = "verysecret"  # optional API key to protect admin endpoints
PUBLIC_BASE_URL = "https://marilynn-uncudgeled-potentially.ngrok-free.dev"

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
# Hardcoded USERS (end users) - replace with your real test numbers
# ---------------------------
USERS = {
    "whatsapp:+917058642591",
}

# ---------------------------
# In-memory stores (products now optionally include image_url)
# ---------------------------
PRODUCTS = {
    "P001": {
        "id": "P001",
        "name": "Handblock Kurti",
        "description": "Beautiful handblock-printed kurti made from cotton.",
        "variants": {
            "S": {"price": 799.0, "inventory": 10},
            "M": {"price": 799.0, "inventory": 12}
        },
        "image_url": "https://marilynn-uncudgeled-potentially.ngrok-free.dev/images/P003_1761556973.png"
    },
    "P002": {
        "id": "P002",
        "name": "Matka Pot",
        "description": "Traditional earthen matka for cool water storage.",
        "variants": {
            "small": {"price": 299.0, "inventory": 20},
            "large": {"price": 499.0, "inventory": 8}
        },
        "image_url": "https://marilynn-uncudgeled-potentially.ngrok-free.dev/images/P002_1761558646.png"
    }
}

ORDERS = {}
SESSIONS = {}

# ---------------------------
# Helpers
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
    """Return a displayable image URL for a product (absolute)."""
    url = p.get("image_url")
    return url if url else "(no image)"


def format_catalog():
    """Nicely formatted catalog for WhatsApp messages.Each product is shown as a small block with header, description, variants and an image link if available.
    """
    blocks = []
    for p in PRODUCTS.values():
        block_lines = []
        block_lines.append(f"\n🔹 {p['id']}: {p['name']}")
        if p.get('description'):
            block_lines.append(p['description'])
        for v, info in p['variants'].items():
            block_lines.append(f" \n• {v} — ₹{info['price']:.0f} (stock: {info['inventory']})")
        if p.get('image_url'):
            block_lines.append(f"\n🖼️ View: {p['image_url']}")
        blocks.append(" ".join(block_lines))
    blocks.append("\nReply with: order <PRODUCT_ID> <variant> <qty> (e.g. order P002 small 1)")
    return "\n".join(blocks)


def format_product_full(pid):
    p = PRODUCTS.get(pid)
    if not p:
        return "Product not found."
    lines = [f"🔹 {p['id']}: {p['name']}"]
    if p.get('description'):
        lines.append(p['description'])
    for v, info in p['variants'].items():
        lines.append(f" • {v}: ₹{info['price']:.2f} (stock: {info['inventory']})")
    if p.get('image_url'):
        lines.append(f"🖼️ View: {p['image_url']}")
    lines.append("Reply with: order <PRODUCT_ID> <variant> <qty>")
    return "    ".join(lines)


def order_summary_text(order):
    lines = [f"Order #{order['order_id']}"]
    for d in order["details"]:
        lines.append(f"- {d['quantity']} x {d['product_name']} ({d['variant']}) — ₹{d['price']:.2f}")
    lines.append(f"Total: ₹{order['total']:.2f}")
    lines.append(f"Status: {order['status']}")
    return "".join(lines)

# ---------------------------
# Gemini helpers (intent parsing & marketing)
# ---------------------------

def gemini_parse_user_message(user_message: str):
    fallback = {"intent": "unknown", "product_id": None, "variant": None, "quantity": None,
                "reply": "Sorry, I couldn't understand. Send 'catalog' to view products or 'order P001 S 1' to order."}
    if not genai_client:
        return {"intent": "unknown", "product_id": None, "variant": None, "quantity": None,
                "reply": "GenAI not configured — try 'catalog' or 'order <PRODUCT_ID> <variant> <qty>'."}

    prod_list = "".join([f"{p['id']}: {p['name']}" for p in PRODUCTS.values()])
    prompt = ("You are a parser that MUST return exactly one JSON object (no extra commentary)."
        "Available products:" + prod_list + ""
        "Return JSON with fields: intent (catalog|inventory|order|help|unknown), product_id (or null), "
        "variant (or null), quantity (number or null), reply (short message to send back)."
        "Examples:"
        '{"intent":"catalog","product_id":null,"variant":null,"quantity":null,"reply":"Here is the catalog..."}'
        '{"intent":"order","product_id":"P001","variant":"M","quantity":2,"reply":"Ordering P001 M x2..."}'
        f"User message: '''{user_message}'''Return only the JSON object."
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
        base = prompt_text + "" + base

    content = (
        f"{base}Product:ID: {p['id']}Name: {p['name']}Description: {p['description']}Variants:"
        + "".join([f"- {v}: ₹{info['price']:.0f}" for v, info in p['variants'].items()])
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
        first_para = text.split('')[0].strip()
        return first_para
    except Exception:
        app.logger.exception("Gemini marketing failed")
        return f"{p['name']} — {p['description']}. Reply 'order {p['id']}' to buy."


def gemini_generate_from_prompt(prompt_text: str):
    """Use generic prompt (no product_id) to generate a short promotional message."""
    if not genai_client:
        return prompt_text or "Promotion"

    prompt_text = prompt_text.strip()
    content = f"Write a short WhatsApp promotional message (one paragraph) based on the following instruction:{prompt_text}"
    try:
        resp = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=content,
            config=types.GenerateContentConfig(max_output_tokens=200, thinking_config=types.ThinkingConfig(thinking_budget=0))
        )
        text = resp.text.strip()
        first_para = text.split('')[0].strip()
        return first_para
    except Exception:
        app.logger.exception("Gemini creative generation failed")
        return prompt_text or "Special offer! Reply to order."

# ---------------------------
# Imagen (image generation) helper (unchanged)
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
    prompt = (prompt_text.strip() + "" + default_prompt) if prompt_text else default_prompt

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

@app.route("/pay/<order_id>", methods=["GET"])
def pay_page(order_id):
    order = ORDERS.get(order_id)
    if not order:
        return "Order not found", 404
    summary = "".join([f"{d['quantity']} x {d['product_name']} ({d['variant']}) - ₹{d['price']:.2f}" for d in order['details']])
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
    send_whatsapp_message(to_whatsapp, f"✅ Payment received for Order #{order_id}. Thank you! We will process your order.{order_summary_text(order)}")
    return render_template_string(PAID_PAGE_TEMPLATE, order_id=order_id)

# ---------------------------
# Twilio webhook for incoming user messages (unchanged)
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
        variant = parsed.get("variant") or list(PRODUCTS[pid]["variants"].keys())[0]
        try:
            qty = int(parsed.get("quantity") or 1)
        except:
            qty = 1

        info = PRODUCTS[pid]["variants"].get(variant)
        if not info:
            resp.message(f"Variant {variant} not found. Available: {', '.join(PRODUCTS[pid]['variants'].keys())}")
            return str(resp)
        if info["inventory"] < qty:
            resp.message(f"Only {info['inventory']} available for variant {variant}. Reduce quantity.")
            return str(resp)

        oid = new_order_id()
        total = info["price"] * qty
        order = {
            "order_id": oid,
            "user": from_number,
            "product_id": pid,
            "product_name": PRODUCTS[pid]["name"],
            "variant": variant,
            "quantity": qty,
            "details": [{"product_id": pid, "product_name": PRODUCTS[pid]["name"], "variant": variant, "quantity": qty, "price": total}],
            "total": total,
            "status": "pending_payment",
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        ORDERS[oid] = order
        PRODUCTS[pid]["variants"][variant]["inventory"] -= qty
        pay_link = create_payment_link(oid)
        resp.message(f"✅ Order {oid} created. Total: ₹{total:.2f}Pay here: {pay_link}")
        return str(resp)

    reply_text = parsed.get("reply") or "Sorry, I didn't understand. Send 'catalog' to view products or 'order P001 S 1' to order."
    resp.message(reply_text)
    return str(resp)

# ---------------------------
# Admin: add product (HTTP) -> generate marketing + image -> broadcast to USERS
# Improved to accept optional image file (multipart/form-data) or image_url in JSON.
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
        return jsonify({"error": "name and variants required"}), 400

    pid = data.get("id") or f"P{str(len(PRODUCTS)+1).zfill(3)}"
    norm = {}
    try:
        for k, v in variants.items():
            norm[str(k)] = {"price": float(v["price"]), "inventory": int(v.get("inventory", 0))}
    except Exception:
        return jsonify({"error": "invalid variant format"}), 400

    # Prepare product skeleton
    PRODUCTS[pid] = {"id": pid, "name": name, "description": description, "variants": norm, "image_url": None}

    # If form included an image file, save and attach
    if request.files:
        file = request.files.get("image")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique = f"prod_{pid}_{int(time.time())}_{uuid.uuid4().hex[:6]}_{filename}"
            filepath = IMAGES_DIR / unique
            file.save(str(filepath))
            PRODUCTS[pid]["image_url"] = f"{request_base_url()}/images/{unique}"
            app.logger.info("Saved product image for %s: %s", pid, filepath)

    # If generate_image_flag and genai available, create an image and attach (overrides if none provided)
    if generate_image_flag and genai_client and not PRODUCTS[pid].get("image_url"):
        try:
            imgurl = generate_image_for_product(pid, prompt)
            if imgurl:
                PRODUCTS[pid]["image_url"] = imgurl
        except Exception:
            app.logger.exception("Image generation failed for new product")

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
    """
    POST multipart/form-data:
      - prompt: text (optional if product_id provided)
      - product_id: optional product to tie marketing to
      - image: optional uploaded image file
      - key: admin key either as query param or X-ADMIN-KEY header

    Behavior mirrors /admin/add_product: generate marketing text using the same helper,
    save uploaded image (if provided) to ./generated_images, and broadcast asynchronously to USERS.
    If a product_id and image are provided, product's image_url will be updated to the uploaded image.
    """
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

        # If tied to a product, update that product's image_url so catalog will show it
        if product_id and product_id in PRODUCTS:
            PRODUCTS[product_id]["image_url"] = image_url

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
    return jsonify(PRODUCTS)

@app.route("/debug/orders", methods=["GET"])
def debug_orders():
    return jsonify(list(ORDERS.values()))

# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    print("Starting WhatsApp + Gemini + Imagen bot with prompt+image admin route.")
    if not PUBLIC_BASE_URL:
        print("Warning: PUBLIC_BASE_URL not set — payment and image links may not be reachable externally.")
    app.run(host="0.0.0.0", port=5000, debug=False)
