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


def purchase_product_by_id(db, user_id: str, product_id: str, buyer_user_id: str, variant_id: str = None):
    """
    Helper function to purchase a product - decreases stock by 1 and increases item_bought count.
    Can be called from routes, webhooks, or other functions.
    
    Args:
        db: Firestore client instance
        user_id (str): The user ID of the product owner (from products/{user_id}/items/{product_id})
        product_id (str): The product document ID
        buyer_user_id (str): The user ID of the buyer
        variant_id (str, optional): Variant ID if product has variants
    
    Returns:
        dict: {
            'success': bool,
            'remaining_stock': int,
            'total_purchases': int,
            'variant_id': str (if applicable),
            'purchase_id': str
        }
    
    Raises:
        ValueError: If product not found, out of stock, or invalid parameters
        Exception: For database errors
    """
    if not db:
        raise Exception("Database not available")
    
    if not user_id or not product_id or not buyer_user_id:
        raise ValueError("user_id, product_id, and buyer_user_id are required")
    
    # Reference to the product document
    items_ref = db.collection("products").document(user_id).collection("items")
    doc_ref = items_ref.document(product_id)
    
    # Use transaction to ensure atomic update
    transaction = db.transaction()
    
    @firestore.transactional
    def purchase_transaction(transaction, doc_ref):
        # Get current product data
        snapshot = doc_ref.get(transaction=transaction)
        
        if not snapshot.exists:
            raise ValueError(f"Product {product_id} not found for user {user_id}")
        
        product_data = snapshot.to_dict() or {}
        
        # Check if product is active
        if not product_data.get('is_active', True):
            raise ValueError("Product is not available for purchase")
        
        # Handle variant-based products
        variants = product_data.get('variants', [])
        if variants and variant_id:
            # Find the specific variant
            variant_found = False
            updated_variants = []
            variant_stock = 0
            
            for idx, variant in enumerate(variants):
                # Match by index (variant_id is string of index like "0", "1", "2")
                if str(idx) == str(variant_id):
                    variant_found = True
                    variant_stock = variant.get('stock', 0)
                    
                    # Check if variant has stock
                    if variant_stock <= 0:
                        raise ValueError(f"Variant '{variant_id}' is out of stock")
                    
                    # Update variant stock and purchases
                    updated_variant = variant.copy()
                    updated_variant['stock'] = variant_stock - 1
                    updated_variant['item_bought'] = variant.get('item_bought', 0) + 1
                    updated_variants.append(updated_variant)
                else:
                    updated_variants.append(variant)
            
            if not variant_found:
                raise ValueError(f"Variant '{variant_id}' not found")
            
            # Update product with modified variants
            update_data = {
                'variants': updated_variants,
                'item_bought': product_data.get('item_bought', 0) + 1,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            transaction.update(doc_ref, update_data)
            
            # Return updated variant stock (find by index)
            variant_idx = int(variant_id)
            updated_variant_data = updated_variants[variant_idx]
            return {
                'remaining_stock': updated_variant_data['stock'],
                'total_purchases': update_data['item_bought'],
                'variant_id': variant_id,
                'variant_stock': updated_variant_data['stock']
            }
        
        # Handle regular products (no variants)
        else:
            current_stock = product_data.get('stock', 0)
            
            # Check if product has stock
            if current_stock <= 0:
                raise ValueError("Product is out of stock")
            
            # Update stock and purchase count
            update_data = {
                'stock': current_stock - 1,
                'item_bought': product_data.get('item_bought', 0) + 1,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            transaction.update(doc_ref, update_data)
            
            return {
                'remaining_stock': update_data['stock'],
                'total_purchases': update_data['item_bought']
            }
    
    # Execute transaction
    result = purchase_transaction(transaction, doc_ref)
    
    # Log the purchase in purchases collection
    try:
        purchase_log_ref = db.collection("purchases").document()
        purchase_data = {
            'purchase_id': purchase_log_ref.id,
            'product_id': product_id,
            'product_owner_user_id': user_id,
            'buyer_user_id': buyer_user_id,
            'variant_id': result.get('variant_id'),
            'purchased_at': datetime.utcnow().isoformat(),
            'quantity': 1,
            'remaining_stock': result['remaining_stock']
        }
        purchase_log_ref.set(purchase_data)
        
        result['purchase_id'] = purchase_log_ref.id
        result['success'] = True
        
    except Exception as log_error:
        print(f"⚠️ Failed to log purchase: {log_error}")
        # Still return success since the stock was updated
        result['purchase_id'] = None
        result['success'] = True
    
    return result

def main():
    """Main function."""
    db = init_firestore()
    
    print("\n🛍️ Product Management System")
    print("=" * 80)
    print("Options:")
    print("1. View all products for a user")
    print("2. View single product details")
    print("3. Purchase a product (test purchase flow)")
    print("=" * 80)
    
    # Check if command line args provided
    if len(sys.argv) >= 2:
        choice = "1"  # Default to listing if args provided
        user_id = sys.argv[1]
        
        if len(sys.argv) >= 3:
            # Specific product requested
            choice = "2"
            product_id = sys.argv[2]
    else:
        # Interactive mode
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice not in ['1', '2', '3']:
            print("❌ Invalid choice!")
            sys.exit(1)
        
        user_id = input("Enter user ID (product owner): ").strip()
        if not user_id:
            print("❌ User ID is required!")
            sys.exit(1)
    
    # Execute based on choice
    if choice == "1":
        # Get all products
        get_all_products(db, user_id)
    
    elif choice == "2":
        # Get single product
        if len(sys.argv) < 3:
            product_id = input("Enter product ID: ").strip()
            if not product_id:
                print("❌ Product ID is required!")
                sys.exit(1)
        
        get_single_product(db, user_id, product_id)
    
    elif choice == "3":
        # Purchase product - First show compact product list
        print("\n📦 Fetching available products...")
        items_ref = db.collection("products").document(user_id).collection("items")
        products = []
        
        print("=" * 80)
        print(f"Available Products for User: {user_id}")
        print("=" * 80)
        
        for doc in items_ref.get():
            data = doc.to_dict() or {}
            products.append({
                'id': doc.id,
                'name': data.get('name', 'N/A'),
                'price': data.get('price', 'N/A'),
                'stock': data.get('stock', 'N/A'),
                'variants': data.get('variants', [])
            })
            
            # Print compact product info
            print(f"\n🆔 Product ID: {doc.id}")
            print(f"   📦 Name: {data.get('name', 'N/A')}")
            print(f"   💰 Price: {data.get('currency', 'INR')} {data.get('price', 'N/A')}")
            print(f"   📊 Stock: {data.get('stock', 'N/A')}")
            if data.get('variants'):
                print(f"   🔀 Variants: {len(data.get('variants', []))}")
        
        print("\n" + "=" * 80)
        print(f"Total: {len(products)} product(s)")
        print("=" * 80)
        
        if not products:
            print("❌ No products found for this user!")
            sys.exit(1)
        
        print("\n🛒 Purchase Flow")
        print("=" * 80)
        
        # Ask for product ID from the list
        product_id = input("\nEnter product ID to purchase (from list above): ").strip()
        if not product_id:
            print("❌ Product ID is required!")
            sys.exit(1)
        
        # Get product details
        items_ref = db.collection("products").document(user_id).collection("items")
        doc_ref = items_ref.document(product_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            print(f"❌ Product {product_id} not found!")
            sys.exit(1)
        
        product_data = doc.to_dict() or {}
        
        # Show product summary
        print(f"\n{'='*80}")
        print(f"📦 Selected Product:")
        print(f"{'='*80}")
        print(f"Name: {product_data.get('name', 'N/A')}")
        print(f"Price: {product_data.get('currency', 'INR')} {product_data.get('price', 'N/A')}")
        print(f"Current Stock: {product_data.get('stock', 'N/A')}")
        
        # Handle variants
        variant_id = None
        variant_index = None
        if product_data.get('variants'):
            print(f"\n🔀 Available Variants:")
            for idx, variant in enumerate(product_data['variants'], 1):
                v_color = variant.get('color', 'N/A')
                v_size = variant.get('size', 'N/A')
                v_price = variant.get('price', 'N/A')
                v_stock = variant.get('stock', 0)
                print(f"  {idx}. Color: {v_color}, Size: {v_size}, Price: {v_price}, Stock: {v_stock}")
            
            variant_choice = input("\nEnter variant number (or press Enter to skip): ").strip()
            if variant_choice and variant_choice.isdigit():
                variant_index = int(variant_choice) - 1
                if 0 <= variant_index < len(product_data['variants']):
                    # Use variant index as identifier
                    variant_id = str(variant_index)
                else:
                    print("❌ Invalid variant number!")
                    sys.exit(1)
        
        # Use anonymous buyer ID
        buyer_user_id = "anonymous_buyer"
        
        # Confirm purchase
        print(f"\n{'='*80}")
        print("📋 Purchase Summary:")
        print(f"{'='*80}")
        print(f"Product: {product_data.get('name', 'N/A')}")
        print(f"Product Owner: {user_id}")
        if variant_id is not None and variant_index is not None:
            v = product_data['variants'][variant_index]
            print(f"Variant: Color {v.get('color')}, Size {v.get('size')}, Price {v.get('price')}")
        print(f"{'='*80}")
        
        confirm = input("\nConfirm purchase? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            print("❌ Purchase cancelled!")
            sys.exit(0)
        
        # Execute purchase
        try:
            print("\n💳 Processing purchase...")
            result = purchase_product_by_id(
                db=db,
                user_id=user_id,
                product_id=product_id,
                buyer_user_id=buyer_user_id,
                variant_id=variant_id
            )
            
            print("\n" + "=" * 80)
            print("✅ PURCHASE SUCCESSFUL!")
            print("=" * 80)
            print(f"Purchase ID: {result.get('purchase_id', 'N/A')}")
            print(f"Remaining Stock: {result['remaining_stock']}")
            print(f"Total Purchases: {result['total_purchases']}")
            if result.get('variant_id'):
                print(f"Variant Purchased: {result['variant_id']}")
            print("=" * 80)
            
            # Show updated product
            print("\n📦 Updated Product Details:")
            get_single_product(db, user_id, product_id)
            
        except ValueError as e:
            print(f"\n❌ Purchase failed: {e}")
        except Exception as e:
            print(f"\n❌ Error during purchase: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
