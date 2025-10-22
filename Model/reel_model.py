from google.cloud import storage
import time
from google import genai
from google.genai.types import GenerateVideosConfig
import os, re
import subprocess

# ------------------------
# CONFIGURE VERTEX AI
# ------------------------
client = genai.Client(
    vertexai=True,
    project="useful-figure-475210-g7",
    location="us-central1"
)

VIDEO_BUCKET = "gs://all_in_one_bucket/reels"  # your GCS bucket
LOCAL_DIR = "./segments"  # temporary local storage

os.makedirs(LOCAL_DIR, exist_ok=True)

# ------------------------
# Helper: Download from GCS
# ------------------------
def download_from_gcs(gcs_uri, local_path):
    from urllib.parse import urlparse
    parsed = urlparse(gcs_uri)
    bucket_name = parsed.netloc
    blob_name = parsed.path.lstrip("/")

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)
    print(f"Downloaded {gcs_uri} -> {local_path}")

# ------------------------
# STEP 1: Suggest content ideas
# ------------------------
import re

def suggest_content_ideas(prompt, num_ideas=3):
    # Prompt AI to number the ideas explicitly
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=(
            f"Give me {num_ideas} creative short-form video ideas for: {prompt}\n\n"
            "Number them explicitly as:\n"
            "1. Idea One\n"
            "2. Idea Two\n"
            "3. Idea Three\n"
            "Do not include extra headers or text outside the numbering."
        ),
    )
    text = response.candidates[0].content.parts[0].text

    # Extract lines starting with "1.", "2.", etc.
    idea_blocks = []
    for line in text.split("\n"):
        match = re.match(r"^\s*(\d+)\.\s*(.+)", line)
        if match:
            idea_blocks.append(match.group(2).strip())

    # Fallback: if parsing fails, return full text as single idea
    if not idea_blocks:
        idea_blocks = [text.strip()]

    # Return exactly `num_ideas` ideas
    return idea_blocks[:num_ideas]

# ------------------------
# STEP 2: Generate 3-part script
# ------------------------
def generate_script(idea):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Create a 3-part script for a 24-second short video (8s each) based on this idea: {idea}",
    )
    seg_parsed = response.candidates[0].content.parts[0].text
    segments = [seg.strip() for seg in seg_parsed.split("\n") if seg.strip()]
    if len(segments) < 3:
        text = seg_parsed
        seg_length = len(text) // 3
        segments = [text[i:i+seg_length] for i in range(0, len(text), seg_length)]
    return segments[:3]

# ------------------------
# STEP 3: Generate 8-second video for a segment
# ------------------------
def generate_video(segment_prompt, segment_index):
    print(f"⏳ Generating video segment {segment_index+1}...")
    operation = client.models.generate_videos(
        model="veo-3.0-generate-001",
        prompt=f"{segment_prompt}. Aspect ratio 9:16.",
        config=GenerateVideosConfig(
            aspect_ratio="9:16",
            output_gcs_uri=f"{VIDEO_BUCKET}/segment_{segment_index+1}.mp4"
        )
    )
    while not operation.done:
        print(f"Segment {segment_index+1} status: Generating...")
        time.sleep(15)
        operation = client.operations.get(operation)

    if operation.error:
        print(f"❌ Error generating segment {segment_index+1}: {operation.error['message']}")
        return None

    video_uri = operation.result.generated_videos[0].video.uri
    print(f"✅ Segment {segment_index+1} done: {video_uri}")

    # Download locally
    local_path = os.path.join(LOCAL_DIR, f"segment_{segment_index+1}.mp4")
    download_from_gcs(video_uri, local_path)
    return local_path

# ------------------------
# STEP 4: Stitch videos together using FFmpeg
# ------------------------
def stitch_videos_ffmpeg(video_paths, output_file="final_reel.mp4"):
    print("🔗 Stitching video segments with FFmpeg...")
    file_list_path = os.path.join(LOCAL_DIR, "file_list.txt")
    with open(file_list_path, "w") as f:
        for path in video_paths:
            f.write(f"file '{os.path.abspath(path)}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", file_list_path, "-c", "copy", output_file
    ], check=True)
    print(f"🎉 Final video saved as {output_file}")

# ------------------------
# STEP 5: Full pipeline
# ------------------------
# ------------------------
# STEP 5: Full pipeline (with confirmation)
# ------------------------
def create_reel(user_prompt):
    # Step 1: Suggest ideas
    ideas = suggest_content_ideas(user_prompt)
    print("\n💡 Suggested content ideas:")
    for idx, idea in enumerate(ideas):
        print(f"{idx+1}: {idea}")

    choice = int(input("Select an idea (1-3): ")) - 1
    selected_idea = ideas[choice]

    # Step 2: Generate full script (unsplit)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Create a 3-part script for a 24-second short video (8s each) based on this idea: {selected_idea}",
    )
    full_script = response.candidates[0].content.parts[0].text
    print("\n📝 Full generated script (preview):\n")
    print(full_script)

    # Step 3: Ask user if they want to proceed with segmenting and video creation
    proceed = input("\nDo you want to split into segments and generate the reel? (y/n): ").strip().lower()
    if proceed != "y":
        print("❌ Reel creation cancelled.")
        return

    # Step 4: Split into segments (as before)
    segments = [seg.strip() for seg in full_script.split("\n\n") if seg.strip()]
    if len(segments) < 3:
        # fallback: split evenly
        text = full_script
        seg_length = len(text) // 3
        segments = [text[i:i+seg_length] for i in range(0, len(text), seg_length)]
    elif len(segments) > 3:
        # merge smaller blocks to get exactly 3
        while len(segments) > 3:
            min_idx = min(range(len(segments)-1), key=lambda i: len(segments[i])+len(segments[i+1]))
            segments[min_idx] = segments[min_idx] + "\n\n" + segments[min_idx+1]
            del segments[min_idx+1]
    segments = segments[:3]

    print("\n📝 Final 3 segments for video generation:")
    for idx, seg in enumerate(segments):
        print(f"\n--- Segment {idx+1} ---\n{seg}")

    # Step 5: Generate videos & stitch
    video_paths = []
    for idx, seg in enumerate(segments):
        path = generate_video(seg, idx)
        if path:
            video_paths.append(path)
        else:
            print("⚠ Skipping failed segment")

    if len(video_paths) == len(segments):
        stitch_videos_ffmpeg(video_paths)
    else:
        print("❌ Not all segments generated successfully. Cannot stitch final video.")

# ------------------------
# RUN
# ------------------------
if __name__ == "__main__":
    user_prompt = input("Enter a prompt for your reel: ")
    create_reel(user_prompt)
