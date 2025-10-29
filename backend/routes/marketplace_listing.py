"""
Marketplace Listing Routes
Handles product listing generation for marketplaces like Amazon, Flipkart
Uses Gemini API directly - no subprocess needed
"""

import os
import json
import base64
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from google.cloud import firestore
from google import genai
from PIL import Image
from io import BytesIO

listing_bp = Blueprint('listing', __name__)

# Initialize Firestore
db = firestore.Client()

# Initialize Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDA6vL1W_ZcsNGQdsw3jcFjlfjBPiRjtfY')
client = genai.Client(api_key=GEMINI_API_KEY)

print("✅ Marketplace listing blueprint created successfully")
print("✅ Gemini API initialized")

def download_image_from_url(url):
    """Download image from URL and return bytes"""
    try:
        print(f"   Downloading image: {url[:80]}...")
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            print(f"   ✅ Downloaded successfully ({len(response.content)} bytes)")
            return response.content
        else:
            print(f"   ❌ Failed: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"   ❌ Error downloading: {str(e)}")
        return None


def generate_listing_with_gemini(image_urls, product_name, marketplace, price, description=""):
    """Generate marketplace listing using Gemini API directly"""
    print(f"🤖 Starting Gemini listing generation...")
    
    try:
        # Download images from URLs and convert to PIL Images
        print(f"📥 Downloading {len(image_urls)} image(s)...")
        pil_images = []
        
        for idx, url in enumerate(image_urls[:3], 1):  # Limit to 3 images
            print(f"   Image {idx}/{min(len(image_urls), 3)}:")
            image_data = download_image_from_url(url)
            if image_data:
                try:
                    # Convert bytes to PIL Image
                    pil_img = Image.open(BytesIO(image_data))
                    pil_images.append(pil_img)
                    print(f"   ✅ Converted to PIL Image: {pil_img.size}")
                except Exception as e:
                    print(f"   ❌ Failed to convert to PIL: {str(e)}")
        
        if not pil_images:
            print("❌ No images could be processed")
            return None
        
        print(f"✅ Processed {len(pil_images)} image(s) successfully")
        
        # Create prompt for marketplace listing
        platform_name = marketplace.capitalize()
        prompt = f"""You are an expert marketplace listing writer for {platform_name}.

Analyze the provided product images and create a professional, engaging product listing.

Product Information:
- Product Name: {product_name}
- Price: ₹{price}
- Description: {description if description else 'Create based on images'}
- Platform: {platform_name}

Generate a complete marketplace listing with:

1. **Title**: Catchy, SEO-optimized product title (max 200 characters)
   - Include key features and benefits
   - Use relevant keywords for {platform_name}

2. **Bullet Points**: 5-6 key highlights
   - Focus on features, benefits, and specifications
   - Start each bullet with a strong keyword
   - Be specific and measurable

3. **Description**: Detailed product description (200-300 words)
   - Write in an engaging, persuasive tone
   - Include use cases and benefits
   - Address customer pain points
   - SEO-optimized for {platform_name}

4. **Specifications**: Technical details as key-value pairs
   - Material, dimensions, weight, color, etc.
   - Any visible specifications from images

Return ONLY a valid JSON object with this exact structure:
{{
  "title": "Product title here",
  "bullets": ["bullet 1", "bullet 2", "bullet 3", "bullet 4", "bullet 5"],
  "description": "Full description here",
  "specifications": {{
    "Material": "value",
    "Dimensions": "value",
    "Weight": "value",
    "Color": "value"
  }}
}}

Important: Return ONLY the JSON object, no additional text or markdown formatting."""

        print(f"📝 Prompt created ({len(prompt)} characters)")
        print(f"🚀 Calling Gemini API...")
        
        # Build content list: text prompt + PIL images
        # Gemini SDK accepts: [str, Image, Image, ...] or just str for text-only
        content_parts = [prompt] + pil_images
        
        print(f"📦 Content parts: 1 text + {len(pil_images)} images")
        
        # Call Gemini API with PIL Images
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=content_parts
        )
        
        print(f"✅ Gemini API response received")
        
        # Extract JSON from response
        response_text = response.text.strip()
        print(f"📄 Response length: {len(response_text)} characters")
        
        # Try to extract JSON from response (remove markdown if present)
        if response_text.startswith('```'):
            # Remove markdown code blocks
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        # Parse JSON
        listing_data = json.loads(response_text)
        print(f"✅ Listing generated successfully")
        print(f"   Title: {listing_data.get('title', 'N/A')[:80]}...")
        print(f"   Bullets: {len(listing_data.get('bullets', []))}")
        print(f"   Description length: {len(listing_data.get('description', ''))} chars")
        print(f"   Specifications: {len(listing_data.get('specifications', {}))}")
        
        return listing_data
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {str(e)}")
        print(f"   Response text: {response_text[:500]}...")
        return None
    except Exception as e:
        print(f"❌ Gemini API error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


@listing_bp.route('/generate', methods=['POST'])
def generate_listing():
    """Generate marketplace listing using Gemini API directly"""
    print("\n" + "="*80)
    print("🔵 [Listing] /generate endpoint called")
    print("="*80)
    
    user_id = session.get('user_id')
    print(f"👤 User ID: {user_id}")
    
    if not user_id:
        print("❌ Not authenticated")
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.json
        product_id = data.get('product_id')
        marketplace = data.get('marketplace', 'amazon')
        
        print(f"🆔 Product ID: {product_id}")
        print(f"🏪 Marketplace: {marketplace}")
        
        if not product_id:
            return jsonify({'success': False, 'error': 'product_id required'}), 400
        
        # Get product from Firestore
        print(f"� Fetching product: products/{user_id}/items/{product_id}")
        product_ref = db.collection('products').document(user_id).collection('items').document(product_id)
        product_doc = product_ref.get()
        
        if not product_doc.exists:
            print(f"❌ Product not found")
            return jsonify({'success': False, 'error': 'Product not found'}), 404
        
        product_data = product_doc.to_dict()
        print(f"✅ Product: {product_data.get('name')} (₹{product_data.get('price')})")
        
        # Get product details
        image_urls = product_data.get('image_urls', [])
        product_name = product_data.get('name', 'Product')
        price = product_data.get('price', 0)
        description = product_data.get('description', '')
        
        print(f"📸 Images: {len(image_urls)}")
        
        if not image_urls:
            return jsonify({'success': False, 'error': 'Product must have images'}), 400
        
        # Generate listing with Gemini
        listing_data = generate_listing_with_gemini(
            image_urls, product_name, marketplace, price, description
        )
        
        if not listing_data:
            return jsonify({'success': False, 'error': 'Failed to generate listing'}), 500
        
        # Store in Firestore: listings/{user_id}/products/{product_id}/marketplaces/{marketplace}
        print(f"💾 Saving to Firestore...")
        print(f"   Path: listings/{user_id}/products/{product_id}/marketplaces/{marketplace}")
        
        # First ensure the user document exists (Firestore requirement for subcollections)
        user_doc_ref = db.collection('listings').document(user_id)
        user_doc_ref.set({'user_id': user_id, 'updated_at': firestore.SERVER_TIMESTAMP}, merge=True)
        
        # Then ensure the product document exists
        product_doc_ref = user_doc_ref.collection('products').document(product_id)
        product_doc_ref.set({
            'product_id': product_id,
            'product_name': product_name,
            'updated_at': firestore.SERVER_TIMESTAMP
        }, merge=True)
        
        # Finally save the marketplace listing
        listing_doc = {
            'product_id': product_id,
            'product_name': product_name,
            'marketplace': marketplace,
            'status': 'active',
            'price': price,
            'image_url': image_urls[0],
            'listed_at': firestore.SERVER_TIMESTAMP,
            'views': 0,
            'title': listing_data.get('title', ''),
            'bullets': listing_data.get('bullets', []),
            'description': listing_data.get('description', ''),
            'specifications': listing_data.get('specifications', {})
        }
        
        # Store at: listings/{user_id}/products/{product_id}/marketplaces/{marketplace}
        listing_ref = product_doc_ref.collection('marketplaces').document(marketplace)
        listing_ref.set(listing_doc)
        
        print(f"   ✅ User doc created/updated")
        print(f"   ✅ Product doc created/updated")
        print(f"   ✅ Marketplace listing saved")
        
        print(f"✅ Saved: {listing_ref.id}")
        print("="*80 + "\n")
        
        return jsonify({
            'success': True,
            'listing_id': listing_ref.id,
            'listing': listing_data,
            'message': f'Product listed on {marketplace} successfully'
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@listing_bp.route('/listings', methods=['GET'])
def get_marketplace_listings():
    """Get all marketplace listings for current user"""
    print("\n🔵 [Listing] /listings called")
    
    user_id = session.get('user_id')
    print(f"   User ID from session: {user_id}")
    
    if not user_id:
        print("   ❌ No user_id in session")
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        # Query from listings/{user_id}/products
        print(f"   Path: listings/{user_id}/products")
        
        listings = []
        
        # Get all products for this user
        products_ref = db.collection('listings').document(user_id).collection('products')
        products_docs = list(products_ref.stream())
        
        print(f"   📦 Found {len(products_docs)} products")
        
        for product_doc in products_docs:
            product_id = product_doc.id
            print(f"      Product: {product_id}")
            
            # Get all marketplaces for this product
            marketplaces_ref = product_doc.reference.collection('marketplaces')
            marketplace_docs = list(marketplaces_ref.stream())
            
            print(f"         Marketplaces: {len(marketplace_docs)}")
            
            for marketplace_doc in marketplace_docs:
                marketplace_name = marketplace_doc.id
                listing_data = marketplace_doc.to_dict()
                
                print(f"            - {marketplace_name}: {listing_data.get('product_name')}")
                
                listings.append({
                    'id': f"{product_id}_{marketplace_name}",
                    'product_id': product_id,
                    'product_name': listing_data.get('product_name'),
                    'marketplace': marketplace_name,  # marketplace name is the doc ID
                    'status': listing_data.get('status', 'active'),
                    'listed_at': listing_data.get('listed_at', datetime.now()).isoformat() if hasattr(listing_data.get('listed_at'), 'isoformat') else str(listing_data.get('listed_at')),
                    'image_url': listing_data.get('image_url'),
                    'price': listing_data.get('price', 0),
                    'views': listing_data.get('views', 0)
                })
        
        # Sort by listed_at descending
        listings.sort(key=lambda x: x.get('listed_at', ''), reverse=True)
        
        print(f"   ✅ Total listings: {len(listings)}")
        
        return jsonify({
            'success': True,
            'listings': listings
        })
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@listing_bp.route('/<product_id>/amazon-listing', methods=['GET'])
def get_amazon_listing(product_id):
    """Get Amazon listing details for a product"""
    print(f"\n🔵 [Listing] /amazon-listing called for product: {product_id}")
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        # Get listing from: listings/{user_id}/products/{product_id}/marketplaces/amazon
        print(f"   Path: listings/{user_id}/products/{product_id}/marketplaces/amazon")
        
        listing_ref = (db.collection('listings')
                      .document(user_id)
                      .collection('products')
                      .document(product_id)
                      .collection('marketplaces')
                      .document('amazon'))
        
        listing_doc = listing_ref.get()
        
        if not listing_doc.exists:
            print(f"   ❌ No Amazon listing found for product: {product_id}")
            return jsonify({'success': False, 'error': 'Amazon listing not found'}), 404
        
        listing_data = listing_doc.to_dict()
        print(f"   ✅ Found Amazon listing")
        
        # Format for Amazon UI (data is already flattened in the document)
        amazon_listing = {
            'product_id': product_id,
            'title': listing_data.get('title', listing_data.get('product_name', 'Product')),
            'description': listing_data.get('description', ''),
            'price': listing_data.get('price', 0),
            'original_price': int(listing_data.get('price', 0) * 1.2),  # Fake original price
            'rating': 4.3,  # Fake rating
            'reviews_count': 127,  # Fake reviews
            'bullets': listing_data.get('bullets', []),
            'specifications': listing_data.get('specifications', {}),
            'images': [listing_data.get('image_url')] if listing_data.get('image_url') else [],
            'in_stock': True,
            'delivery_date': 'Tomorrow',
            'seller': 'Kaarigar Store'
        }
        
        # Increment view count
        listing_ref.update({'views': firestore.Increment(1)})
        
        print(f"   ✅ Amazon listing retrieved")
        
        return jsonify({
            'success': True,
            'listing': amazon_listing
        })
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@listing_bp.route('/<product_id>/flipkart-listing', methods=['GET'])
def get_flipkart_listing(product_id):
    """Get Flipkart listing details for a product"""
    print(f"\n� [Listing] /flipkart-listing called for product: {product_id}")
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        # Get listing from: listings/{user_id}/products/{product_id}/marketplaces/flipkart
        print(f"   Path: listings/{user_id}/products/{product_id}/marketplaces/flipkart")
        
        listing_ref = (db.collection('listings')
                      .document(user_id)
                      .collection('products')
                      .document(product_id)
                      .collection('marketplaces')
                      .document('flipkart'))
        
        listing_doc = listing_ref.get()
        
        if not listing_doc.exists:
            print(f"   ❌ No Flipkart listing found for product: {product_id}")
            return jsonify({'success': False, 'error': 'Flipkart listing not found'}), 404
        
        listing_data = listing_doc.to_dict()
        print(f"   ✅ Found Flipkart listing")
        
        # Format for Flipkart UI
        flipkart_listing = {
            'product_id': product_id,
            'title': listing_data.get('title', listing_data.get('product_name', 'Product')),
            'description': listing_data.get('description', ''),
            'price': listing_data.get('price', 0),
            'original_price': int(listing_data.get('price', 0) * 1.25),  # Fake original price
            'rating': 4.2,  # Fake rating
            'reviews_count': 89,  # Fake reviews
            'bullets': listing_data.get('bullets', []),
            'specifications': listing_data.get('specifications', {}),
            'images': [listing_data.get('image_url')] if listing_data.get('image_url') else [],
            'in_stock': True,
            'delivery_date': 'by Tomorrow',
            'seller': 'Kaarigar Craftsmen'
        }
        
        # Increment view count
        listing_ref.update({'views': firestore.Increment(1)})
        
        print(f"   ✅ Flipkart listing retrieved")
        
        return jsonify({
            'success': True,
            'listing': flipkart_listing
        })
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@listing_bp.route('/<product_id>/myntra-listing', methods=['GET'])
def get_myntra_listing(product_id):
    """Get Myntra listing details for a product"""
    print(f"\n🔵 [Listing] /myntra-listing called for product: {product_id}")
    
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        # Get listing from: listings/{user_id}/products/{product_id}/marketplaces/myntra
        print(f"   Path: listings/{user_id}/products/{product_id}/marketplaces/myntra")
        
        listing_ref = (db.collection('listings')
                      .document(user_id)
                      .collection('products')
                      .document(product_id)
                      .collection('marketplaces')
                      .document('myntra'))
        
        listing_doc = listing_ref.get()
        
        if not listing_doc.exists:
            print(f"   ❌ No Myntra listing found for product: {product_id}")
            return jsonify({'success': False, 'error': 'Myntra listing not found'}), 404
        
        listing_data = listing_doc.to_dict()
        print(f"   ✅ Found Myntra listing")
        
        # Format for Myntra UI
        myntra_listing = {
            'product_id': product_id,
            'title': listing_data.get('title', listing_data.get('product_name', 'Product')),
            'description': listing_data.get('description', ''),
            'price': listing_data.get('price', 0),
            'original_price': int(listing_data.get('price', 0) * 1.3),  # Fake original price
            'rating': 4.4,  # Fake rating
            'reviews_count': 156,  # Fake reviews
            'bullets': listing_data.get('bullets', []),
            'specifications': listing_data.get('specifications', {}),
            'images': [listing_data.get('image_url')] if listing_data.get('image_url') else [],
            'in_stock': True,
            'delivery_date': 'Tomorrow',
            'seller': listing_data.get('product_name', 'Kaarigar').split()[0]  # Brand name from product
        }
        
        # Increment view count
        listing_ref.update({'views': firestore.Increment(1)})
        
        print(f"   ✅ Myntra listing retrieved")
        
        return jsonify({
            'success': True,
            'listing': myntra_listing
        })
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


print("�📋 Marketplace listing routes registered:")
print("   POST   /api/marketplace/generate")
print("   GET    /api/marketplace/listings")
print("   GET    /api/marketplace/<product_id>/amazon-listing")
print("   GET    /api/marketplace/<product_id>/flipkart-listing")
print("   GET    /api/marketplace/<product_id>/myntra-listing")
