"""
Minimal Cloud Storage seeding script for Project Kaarigar.

Uploads only videos/images and the brand document, per project requirements:
- brands/BRAND_123/profile/brand.json
- media/BRAND_123/uploads/videos/VID_1/source.mp4 (if local file exists)
- media/BRAND_123/processed/videos/VID_1/final.mp4 (if local file exists)
- products/BRAND_123/PROD_1/images/IMG_1.jpg (if local file exists)

Prereqs:
- GOOGLE_APPLICATION_CREDENTIALS set
- Bucket name matches Database_Setup/googlecloudstorage_object_storage_setup.py
"""

import json
import os
from google.cloud import storage


BUCKET_NAME = "all_in_one_bucket1"  # keep in sync with googlecloudstorage_object_storage_setup.py


def upload_bytes(client: storage.Client, bucket_name: str, dest_path: str, data: bytes, content_type: str = "application/octet-stream") -> None:
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(dest_path)
    blob.upload_from_string(data, content_type=content_type)
    print(f"Uploaded bytes to gs://{bucket_name}/{dest_path}")


def upload_file_if_exists(client: storage.Client, bucket_name: str, local_path: str, dest_path: str, content_type: str | None = None) -> None:
    if not os.path.exists(local_path):
        print(f"Skip: Local file not found: {local_path}")
        return
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(dest_path)
    blob.upload_from_filename(local_path, content_type=content_type)
    print(f"Uploaded {local_path} to gs://{bucket_name}/{dest_path}")


def main() -> None:
    client = storage.Client()

    # 1) Brand document JSON
    brand_doc = {
        "name": "Mitti Crafts",
        "category": "Pottery",
        "location": "Jaipur, RJ, IN",
        "summary": "Handmade terracotta pots",
        "kaarigarId": "KR_1",
        "brandId": "BRAND_123",
    }
    upload_bytes(
        client,
        BUCKET_NAME,
        "brands/BRAND_123/profile/brand.json",
        json.dumps(brand_doc, ensure_ascii=False, indent=2).encode("utf-8"),
        content_type="application/json",
    )

    # 2) Sample video(s) if present
    # Adjust these paths if you have other local sample files available
    local_source_video = os.path.join(os.getcwd(), "dialogue_example.mp4")
    local_final_video = local_source_video  # reuse same file if you don't have a processed sample

    upload_file_if_exists(
        client,
        BUCKET_NAME,
        local_source_video,
        "media/BRAND_123/uploads/videos/VID_1/source.mp4",
        content_type="video/mp4",
    )

    upload_file_if_exists(
        client,
        BUCKET_NAME,
        local_final_video,
        "media/BRAND_123/processed/videos/VID_1/final.mp4",
        content_type="video/mp4",
    )

    # 3) Sample image if present
    # Look for an image in project root as a simple default
    candidate_images = [
        os.path.join(os.getcwd(), "generated_image.png"),
        os.path.join(os.getcwd(), "edited_diary_magical.png"),
    ]
    local_image = next((p for p in candidate_images if os.path.exists(p)), None)
    if local_image:
        # crude content type guess
        ext = os.path.splitext(local_image)[1].lower()
        ctype = "image/png" if ext == ".png" else "image/jpeg"
        upload_file_if_exists(
            client,
            BUCKET_NAME,
            local_image,
            "products/BRAND_123/PROD_1/images/IMG_1.jpg",
            content_type=ctype,
        )
    else:
        print("Skip: No sample image found next to project root")

    print("Seeded Cloud Storage with minimal assets.")


if __name__ == "__main__":
    main()


