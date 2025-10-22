#!/usr/bin/env python3
"""
reel_pipeline_fixed.py

Full pipeline for:
 - suggesting ideas (Gemini text model)
 - generating a 3-part script
 - generating 3 short 9:16 video segments via Vertex Veo with optional reference images
 - downloading segments from GCS
 - stitching segments with ffmpeg into final_reel.mp4

Fixes included:
 - Upload reference images to GCS and pass Image(gcs_uri=...) to generate_videos
 - Poll long-running operations correctly via operation.name
 - Exponential backoff and overall timeout for polling
 - Robust error handling and debug prints
"""

import os
import time
import pathlib
import subprocess
from urllib.parse import urlparse
from io import BytesIO

from PIL import Image as PilImage
from google.cloud import storage
from google import genai
from google.genai.types import GenerateVideosConfig, Image, Part

# ------------------------
# CONFIGURE VERTEX AI
# ------------------------
# Ensure your env var GOOGLE_APPLICATION_CREDENTIALS points to a service account JSON
client = genai.Client(
    vertexai=True,
    project="useful-figure-475210-g7",  # replace with your project
    location="us-central1"
)

# ------------------------
# CONFIG
# ------------------------
VIDEO_BUCKET = "gs://all_in_one_bucket/reels"  # must be a gs:// URI; replace with your bucket/prefix
LOCAL_DIR = "./segments"
os.makedirs(LOCAL_DIR, exist_ok=True)

# ------------------------
# Helper: Download from GCS
# ------------------------
def download_from_gcs(gcs_uri, local_path):
    parsed = urlparse(gcs_uri)
    bucket_name = parsed.netloc
    blob_name = parsed.path.lstrip("/")

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)
    print(f"Downloaded {gcs_uri} -> {local_path}")

# ------------------------
# Helper: Upload local file to GCS and return gs:// URI
# ------------------------
def upload_file_to_gcs(local_path, dest_bucket_gs_uri_prefix):
    """
    Upload local file to GCS and return gs://... URI.
    dest_bucket_gs_uri_prefix example: 'gs://my-bucket/prefix'
    """
    assert dest_bucket_gs_uri_prefix.startswith("gs://"), "VIDEO_BUCKET must start with gs://"
    parts = dest_bucket_gs_uri_prefix[5:].split("/", 1)
    bucket_name = parts[0]
    prefix = parts[1] if len(parts) > 1 else ""
    blob_name = f"{prefix.rstrip('/')}/{pathlib.Path(local_path).name}".lstrip("/")

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    gs_uri = f"gs://{bucket_name}/{blob_name}"
    print(f"Uploaded {local_path} -> {gs_uri}")
    return gs_uri

# ------------------------
# STEP 1: Suggest content ideas (simple wrapper around Gemini)
# ------------------------
import re
def suggest_content_ideas(prompt, num_ideas=3):
    """
    Ask the Gemini text model for numbered short-form video ideas.
    Returns list of up to num_ideas strings.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=(f"Give me {num_ideas} creative short-form video ideas for: {prompt}\n\n"
                  "Number them explicitly as:\n"
                  "1. Idea One\n"
                  "2. Idea Two\n"
                  "3. Idea Three\n"
                  "Do not include extra headers or text outside the numbering.")
    )
    text = response.candidates[0].content.parts[0].text
    idea_blocks = []
    for line in text.splitlines():
        match = re.match(r"^\s*(\d+)\.\s*(.+)", line)
        if match:
            idea_blocks.append(match.group(2).strip())
    if not idea_blocks:
        idea_blocks = [text.strip()]
    return idea_blocks[:num_ideas]

# ------------------------
# STEP 2: Generate 3-part script
# ------------------------
def generate_script(idea):
    """
    Return a list of 3 segment strings (each ~8s)
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Create a 3-part script for a 24-second short video (8s each) based on this idea: {idea}"
    )
    seg_parsed = response.candidates[0].content.parts[0].text
    segments = [seg.strip() for seg in seg_parsed.split("\n\n") if seg.strip()]
    if len(segments) < 3:
        # crude fallback: split evenly
        text = seg_parsed.strip()
        seg_length = max(1, len(text) // 3)
        segments = [text[i:i+seg_length].strip() for i in range(0, len(text), seg_length)]
    # normalize to exactly 3
    while len(segments) > 3:
        # merge smallest adjacent blocks
        min_idx = min(range(len(segments)-1), key=lambda i: len(segments[i])+len(segments[i+1]))
        segments[min_idx] = segments[min_idx] + "\n\n" + segments[min_idx+1]
        del segments[min_idx+1]
    return segments[:3]

# ------------------------
# STEP 3: Generate 8-second video for a segment (fixed)
# ------------------------
def generate_video_with_image(segment_prompt, segment_index, reference_image=None, model_name="veo-3.1-generate-preview", timeout_seconds=8*60):
    """
    Generate a video segment using Veo. If reference_image is provided:
      - if reference_image starts with 'gs://', use it directly
      - else upload the local file to VIDEO_BUCKET and reference the uploaded GS URI
    Returns local file path to downloaded mp4, or None on error.
    """
    print(f"\n⏳ Generating video segment {segment_index+1} (model={model_name})...")
    try:
        output_gcs_uri = f"{VIDEO_BUCKET}/segment_{segment_index+1}.mp4"
        config = GenerateVideosConfig(
            aspect_ratio="9:16",
            output_gcs_uri=output_gcs_uri
        )

        kwargs = {
            "model": model_name,
            "prompt": f"{segment_prompt}. Aspect ratio 9:16.",
            "config": config
        }

        if reference_image:
            # If it's already a GCS URI, use directly; otherwise upload it to the VIDEO_BUCKET
            if reference_image.startswith("gs://"):
                image_gs_uri = reference_image
            else:
                print(f"Uploading reference image {reference_image} to {VIDEO_BUCKET} ...")
                image_gs_uri = upload_file_to_gcs(reference_image, VIDEO_BUCKET)

            # Use Image(gcs_uri=...) as the documented pattern for Veo image guidance
            kwargs["image"] = Image(gcs_uri=image_gs_uri, mime_type="image/jpeg")

        operation = client.models.generate_videos(**kwargs)
        # Poll using operation.name with exponential backoff + overall timeout
        start = time.time()
        attempt = 0
        while True:
            attempt += 1
            operation = client.operations.get(operation.name)  # refresh via name
            if getattr(operation, "done", False):
                break
            elapsed = time.time() - start
            if elapsed > timeout_seconds:
                print(f"⏱ Timeout waiting for segment {segment_index+1} after {int(elapsed)}s.")
                return None
            sleep_for = min(30, 2 ** min(attempt, 6))
            print(f"Segment {segment_index+1} still generating (elapsed {int(elapsed)}s). Sleeping {sleep_for}s...")
            time.sleep(sleep_for)

        # Check for errors
        if getattr(operation, "error", None):
            print(f"❌ Error generating segment {segment_index+1}: {operation.error}")
            return None

        result = getattr(operation, "result", None)
        if not result or not getattr(result, "generated_videos", None):
            print("❌ Unexpected operation result structure; printing operation for debugging:")
            print(operation)
            return None

        video_uri = result.generated_videos[0].video.uri
        print(f"✅ Segment {segment_index+1} done: {video_uri}")

        # Download locally
        local_path = os.path.join(LOCAL_DIR, f"segment_{segment_index+1}.mp4")
        download_from_gcs(video_uri, local_path)
        return local_path

    except Exception as e:
        print(f"❌ Exception during video generation: {e}")
        return None

# ------------------------
# STEP 4: Stitch videos together using FFmpeg
# ------------------------
def stitch_videos_ffmpeg(video_paths, output_file="final_reel.mp4"):
    print("\n🔗 Stitching video segments with FFmpeg...")
    file_list_path = os.path.join(LOCAL_DIR, "file_list.txt")
    with open(file_list_path, "w") as f:
        for path in video_paths:
            f.write(f"file '{os.path.abspath(path)}'\n")

    try:
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", file_list_path, "-c", "copy", output_file
        ], check=True)
        print(f"🎉 Final video saved as {output_file}")
    except subprocess.CalledProcessError as e:
        print("❌ ffmpeg failed:", e)

# ------------------------
# Optional: analyze product images with Gemini Vision (best-effort)
# ------------------------
def analyze_product_images(image_paths):
    """
    Try to analyze product images using the Gemini Vision model.
    If the SDK accepts inline parts, we send Part.from_bytes.
    Returns a text analysis or None.
    """
    try:
        print("\n🔍 Analyzing product images (Gemini Vision)...")
        parts = []
        parts.append({"text": "Analyze these product images and provide:\n1. Key visual features\n2. Unique selling points\n3. Target audience\n4. Suggested video showcase style\n\nPlease be concise and numbered."})
        for p in image_paths:
            with open(p, "rb") as f:
                image_bytes = f.read()
            # Use inline_data dict format for safety (the older sample pattern),
            # many SDKs accept either Part.from_bytes or inline_data dict. If your SDK requires Part.from_bytes, swap accordingly.
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(image_bytes).decode('utf-8')
                }
            })
        response = client.models.generate_content(model="gemini-2.5-pro", contents=parts)
        analysis = response.candidates[0].content.parts[0].text
        return analysis
    except Exception as e:
        print("⚠️ Image analysis failed:", e)
        return None

# ------------------------
# Full pipeline function
# ------------------------
def create_reel(user_prompt, product_images=None):
    """
    High-level pipeline to:
     - suggest ideas
     - pick an idea (interactive)
     - generate script
     - confirm and create 3 segments (image-guided if images supplied)
    """
    print("\n💡 Suggesting content ideas...")
    ideas = suggest_content_ideas(user_prompt, num_ideas=3)

    print("\nSuggested ideas:")
    for i, it in enumerate(ideas, start=1):
        print(f"{i}. {it}")

    # Interactive selection
    try:
        choice = int(input("Select an idea (1-3): ").strip())
        if choice < 1 or choice > len(ideas):
            print("Invalid choice; defaulting to 1")
            choice = 1
    except Exception:
        choice = 1

    selected_idea = ideas[choice - 1]
    print(f"\nSelected idea: {selected_idea}")

    # Generate full script
    print("\n📝 Generating full script...")
    segments = generate_script(selected_idea)
    print("\n📝 Final 3 segments for video generation:")
    for idx, seg in enumerate(segments):
        print(f"\n--- Segment {idx+1} ---\n{seg}")

    proceed = input("\nDo you want to split into segments and generate the reel? (y/n): ").strip().lower()
    if proceed != "y":
        print("❌ Reel creation cancelled.")
        return

    # Generate videos for each segment, optionally using product_images per segment
    video_paths = []
    for idx, seg in enumerate(segments):
        reference_image = None
        if product_images and idx < len(product_images):
            reference_image = product_images[idx]
        local_video = generate_video_with_image(seg, idx, reference_image)
        if local_video:
            video_paths.append(local_video)
        else:
            print(f"⚠ Skipping failed segment {idx+1}")

    if len(video_paths) == len(segments):
        stitch_videos_ffmpeg(video_paths)
    else:
        print("❌ Not all segments generated successfully. Cannot stitch final video.")

# ------------------------
# CLI entrypoint
# ------------------------
if __name__ == "__main__":
    import base64

    user_prompt = input("Enter a prompt for your reel: ").strip()

    product_images = []
    while True:
        image_path = input("Enter path to product image (or press Enter to continue): ").strip()
        if not image_path:
            break
        if image_path.startswith("gs://") or os.path.exists(image_path):
            product_images.append(image_path)
        else:
            print("⚠️ Invalid image path. Please provide a local path or a gs:// URI.")

    create_reel(user_prompt, product_images if product_images else None)
