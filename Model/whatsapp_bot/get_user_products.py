"""
Get all products for a user from Firestore with detailed information.
Usage: python get_user_products.py [user_id] [product_id]
"""

import sys
import json
from google.cloud import firestore
from datetime import datetime


def init_firestore():
    """Initialize Firestore client."""
    try:
        db = firestore.Client()
        print("✅ Firestore connected successfully\n")
        return db
    except Exception as e:
        print(f"❌ Failed to connect to Firestore: {e}")
        sys.exit(1)


def get_all_products(db, user_id):
    """Get all products for a specific user."""
    try:
        items_ref = db.collection("products").document(user_id).collection("items")
        products = []
        
        print(f"📦 Fetching all products for user: {user_id}")
        print("=" * 80)
        
        for doc in items_ref.get():
            data = doc.to_dict() or {}
            data["id"] = doc.id
            products.append(data)
            
            print(f"\n{'='*80}")
            print(f"🔹 Product ID: {doc.id}")
            print(f"{'='*80}")
            print(f"Name: {data.get('name', 'N/A')}")
            print(f"Description: {data.get('description', 'N/A')}")
            print(f"Price: {data.get('currency', 'INR')} {data.get('price', 'N/A')}")
            print(f"Stock: {data.get('stock', 'N/A')}")
            print(f"Images: {len(data.get('image_urls', []))} image(s)")
            print(f"Videos: {len(data.get('video_urls', []))} video(s)")
            print(f"Variants: {len(data.get('variants', []))} variant(s)")
            
            if data.get('ai_generated_title'):
                print(f"\n🤖 AI Generated Title: {data.get('ai_generated_title')}")
            if data.get('ai_generated_description'):
                print(f"🤖 AI Generated Description: {data.get('ai_generated_description')}")
            
            print(f"\nCreated: {data.get('created_at', 'N/A')}")
            print(f"Updated: {data.get('updated_at', 'N/A')}")
            
            if data.get('image_urls'):
                print(f"\n📷 Image URLs:")
                for idx, url in enumerate(data.get('image_urls', []), 1):
                    print(f"  {idx}. {url}")
            
            if data.get('video_urls'):
                print(f"\n🎥 Video URLs:")
                for idx, url in enumerate(data.get('video_urls', []), 1):
                    print(f"  {idx}. {url}")
            
            if data.get('variants'):
                print(f"\n🔀 Variants:")
                for idx, variant in enumerate(data.get('variants', []), 1):
                    print(f"  Variant {idx}:")
                    for key, value in variant.items():
                        print(f"    - {key}: {value}")
        
        print(f"\n{'='*80}")
        print(f"📊 Total products found: {len(products)}")
        print(f"{'='*80}\n")
        
        return products
        
    except Exception as e:
        print(f"❌ Error fetching products: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_single_product(db, user_id, product_id):
    """Get details for a single product."""
    try:
        doc_ref = db.collection("products").document(user_id).collection("items").document(product_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            print(f"❌ Product not found: {product_id}")
            return None
        
        data = doc.to_dict() or {}
        data["id"] = doc.id
        
        print(f"\n{'='*80}")
        print(f"🔹 Product Details")
        print(f"{'='*80}")
        print(f"ID: {doc.id}")
        print(f"User ID: {user_id}")
        print(f"\n📋 Full Data (JSON):")
        print(json.dumps(data, indent=2, default=str))
        print(f"{'='*80}\n")
        
        return data
        
    except Exception as e:
        print(f"❌ Error fetching product: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function."""
    db = init_firestore()
    
    # Get user ID from command line or ask for input
    if len(sys.argv) >= 2:
        user_id = sys.argv[1]
    else:
        user_id = input("Enter user ID: ").strip()
        if not user_id:
            print("❌ User ID is required!")
            sys.exit(1)
    
    # Check if specific product ID is provided
    if len(sys.argv) >= 3:
        # Get specific product
        product_id = sys.argv[2]
        get_single_product(db, user_id, product_id)
    else:
        # Get all products with full details
        get_all_products(db, user_id)


if __name__ == "__main__":
    main()
