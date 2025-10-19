"""
Minimal Firestore seeding script for Project Kaarigar.

Creates the following collections/documents with mock values (no timestamps, no hashes):
- kaarigars/KR_1
- brands/BRAND_123
- conversations/SESS_1
- videos/VID_1
- products/PROD_1
- listings/LIST_1

Prereqs:
- GOOGLE_APPLICATION_CREDENTIALS must point to a valid service account JSON
- The Firestore database must exist in the target project
"""

from google.cloud import firestore


def main() -> None:
    # Update project_id if needed; falls back to default from credentials
    db = firestore.Client()

    # kaarigars
    db.collection("kaarigars").document("KR_1").set({
        "name": "Siddhartha",
        "occupation": "Potter",
        "languages": ["hi", "en"],
        "bio": "Terracotta artisan",
        "username": "mitti_crafts",
        "password": "change-this",
        "brandId": "BRAND_123",
    })

    # brands
    db.collection("brands").document("BRAND_123").set({
        "kaarigarId": "KR_1",
        "name": "Mitti Crafts",
        "category": "Pottery",
        "location": "Jaipur, RJ, IN",
        "summary": "Handmade terracotta pots",
        "brandDocUri": "gs://all_in_one_bucket/brands/BRAND_123/profile/brand.json",
    })

    # conversations
    db.collection("conversations").document("SESS_1").set({
        "kaarigarId": "KR_1",
        "brandId": "BRAND_123",
        "transcriptText": "Hello, tell me about your craft...",
        "extracted": {
            "name": "Siddhartha",
            "products": "Clay pots, bowls",
            "materials": "Terracotta clay",
        },
    })

    # videos
    db.collection("videos").document("VID_1").set({
        "kaarigarId": "KR_1",
        "brandId": "BRAND_123",
        "sourceUri": "gs://all_in_one_bucket/media/BRAND_123/uploads/videos/VID_1/source.mp4",
        "finalUri": "gs://all_in_one_bucket/media/BRAND_123/processed/videos/VID_1/final.mp4",
    })

    # products
    db.collection("products").document("PROD_1").set({
        "brandId": "BRAND_123",
        "title": "Handmade Clay Pot",
        "description": "Terracotta water pot",
        "price": 799,
        "currency": "INR",
        "imageUris": [
            "gs://all_in_one_bucket/products/BRAND_123/PROD_1/images/IMG_1.jpg"
        ],
        "videoIds": ["VID_1"],
    })

    # listings
    db.collection("listings").document("LIST_1").set({
        "brandId": "BRAND_123",
        "productId": "PROD_1",
        "marketplace": "Amazon",
        "title": "Terracotta Clay Pot - 2L",
        "description": "Eco-friendly clay pot for cool water.",
        "price": 799,
        "currency": "INR",
        "imageUris": [
            "gs://all_in_one_bucket/products/BRAND_123/PROD_1/images/IMG_1.jpg"
        ],
        "videoIds": ["VID_1"],
        "contentJson": {
            "bullets": [
                "Handmade terracotta",
                "Naturally cools water",
                "2L capacity",
            ],
            "seo_tags": ["terracotta", "handmade", "clay pot"],
        },
    })

    print("Seeded Firestore with minimal mock data.")


if __name__ == "__main__":
    main()


