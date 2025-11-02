#!/usr/bin/env python3
"""
Image(s) to Veo Reel Converter (interactive fallback)

- Accepts multiple images (paths, glob or directory)
- If images or prompt are omitted on the command line, asks interactively
- Uses ffmpeg only to stitch clips (no moviepy anywhere)
"""

import os
import sys
import time
import glob
import argparse
import tempfile
import shutil
from pathlib import Path
from typing import List
import subprocess

# Google GenAI imports (same as your original)
from google import genai
from google.genai import types

# Configuration
PROJECT_ID = "karigar-475215"
LOCATION = "us-central1"

# Initialize client
client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

def optimize_prompt_with_gemini(user_prompt: str, image_path: str) -> str:
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        file_ext = Path(image_path).suffix.lower()
        mime_type = "image/jpeg" if file_ext in ['.jpg', '.jpeg'] else "image/png"
        gemini_prompt = f"""
        You are an expert video prompt engineer for Google's Veo 3.1 model.

        The user wants to create a vertical reel clip from this image and prompt: "{user_prompt}"

        Analyze the provided image and produce a single-line optimized prompt suitable for a 9:16 cinematic short:
        * Include camera movements (zoom, dolly, pan), temporal elements (slow-mo, speed ramp), atmosphere (lighting, weather),
          subject animation, and a clear cinematic mood.
        * Keep it compact and focused (one sentence).
        Output ONLY the optimized prompt.
        """
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[gemini_prompt, types.Part.from_bytes(data=image_bytes, mime_type=mime_type)],
        )
        optimized_prompt = response.text.strip()
        if not optimized_prompt:
            raise RuntimeError("Gemini returned empty prompt")
        print(f"🤖 Gemini optimized prompt: {optimized_prompt}")
        return optimized_prompt
    except Exception as e:
        print(f"⚠️  Gemini optimization failed for {image_path!r}: {e}")
        fallback_prompt = f"{user_prompt}. Add cinematic motion, camera movement, atmospheric effects, and adapt for 9:16 vertical."
        print(f"🔄 Using fallback prompt: {fallback_prompt}")
        return fallback_prompt

def generate_clip_for_image(image_path: str, optimized_prompt: str, duration_seconds: int, tmp_dir: str, idx: int) -> str:
    try:
        image_name = Path(image_path).stem
        out_name = Path(tmp_dir) / f"{idx:03d}_{image_name}_veo.mp4"
        print(f"\n🎬 Starting generation for {image_path} -> {out_name.name}")
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        print(f"📥 Image size: {len(img_bytes)/1024:.1f} KB")
        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=optimized_prompt,
            image=types.Image.from_file(location=image_path),
            config=types.GenerateVideosConfig(
                aspect_ratio="9:16",
                number_of_videos=1,
                duration_seconds=duration_seconds,
                resolution="1080p",
                person_generation="allow_adult",
                enhance_prompt=True,
                generate_audio=True,
            ),
        )
        print("⏳ Video generation started (this can take some time)...")
        while not operation.done:
            time.sleep(10)
            operation = client.operations.get(operation)
            print("⏳ still generating...")
        if not operation.response:
            raise RuntimeError("No response from video generation operation")
        result = operation.result
        generated = result.generated_videos[0]
        video_bytes = generated.video.video_bytes
        with open(out_name, "wb") as f:
            f.write(video_bytes)
        print(f"✅ Clip ready: {out_name} ({len(video_bytes)/(1024*1024):.1f} MB)")
        return str(out_name)
    except Exception as e:
        raise RuntimeError(f"Failed to generate clip for {image_path}: {e}")

def _check_ffmpeg_available() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        return False

def stitch_clips(clips: List[str], final_output: str, keep_temp: bool = False) -> bool:
    """
    Concatenate a list of mp4 clips into final_output using ffmpeg.
    Re-encodes to consistent 1080x1920 (9:16) and ensures audio is included.
    """
    if not clips:
        print("❌ No clips to stitch.")
        return False

    if not _check_ffmpeg_available():
        print("❌ ffmpeg not found. Please install ffmpeg and ensure it is in your PATH.")
        return False

    print(f"\n🔗 Stitching {len(clips)} clips into {final_output} using ffmpeg")

    # Create a temporary concat list file
    tmp_dir = tempfile.mkdtemp(prefix="veo_ffmpeg_concat_")
    list_file_path = Path(tmp_dir) / "concat_list.txt"
    try:
        with open(list_file_path, "w", encoding="utf-8") as lf:
            for c in clips:
                lf.write(f"file '{os.path.abspath(c)}'\n")

        # ffmpeg concat demuxer with re-encoding and scaling/padding to 1080x1920
        # We force aspect ratio preserve then pad to 1080x1920, so output is exactly vertical.
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file_path),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            str(final_output)
        ]

        print("🔁 Running ffmpeg...")
        completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if completed.returncode != 0:
            print("❌ ffmpeg failed. stderr:")
            print(completed.stderr.decode(errors="ignore"))
            return False

        print(f"✅ Reel created with ffmpeg: {final_output}")
        return True
    except Exception as e:
        print(f"❌ ffmpeg concatenation failed: {e}")
        return False
    finally:
        if not keep_temp:
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass
        else:
            print(f"ℹ️ ffmpeg concat temp files kept at: {tmp_dir}")

def collect_image_paths(inputs: List[str]) -> List[str]:
    paths = []
    for item in inputs:
        item = os.path.expanduser(item)
        if os.path.isdir(item):
            for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp"):
                paths.extend(sorted(glob.glob(os.path.join(item, ext))))
        else:
            if any(ch in item for ch in "*?[]"):
                matched = sorted(glob.glob(item))
                paths.extend(matched)
            else:
                if os.path.exists(item):
                    paths.append(item)
                else:
                    print(f"⚠️  Path not found: {item}")
    seen = set()
    ordered = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            ordered.append(p)
    return ordered

def convert_images_to_reel(image_inputs: List[str], user_prompt: str, output_name: str = None,
                           clip_duration: int = 4, keep_temp: bool = False) -> bool:
    image_paths = collect_image_paths(image_inputs)
    if not image_paths:
        print("❌ No valid images provided.")
        return False
    if not output_name:
        output_name = f"reel_{int(time.time())}.mp4"
    tmp_dir = tempfile.mkdtemp(prefix="veo_reel_")
    print(f"🗂️  Temporary working directory: {tmp_dir}")
    generated_clips = []
    try:
        for idx, img in enumerate(image_paths, start=1):
            print(f"\n=== Processing [{idx}/{len(image_paths)}] {img} ===")
            optimized_prompt = optimize_prompt_with_gemini(user_prompt, img)
            try:
                clip_path = generate_clip_for_image(img, optimized_prompt, duration_seconds=clip_duration, tmp_dir=tmp_dir, idx=idx)
                generated_clips.append(clip_path)
            except Exception as e:
                print(f"❌ Skipped image due to error: {e}")
        if not generated_clips:
            print("❌ No clips were generated. Aborting.")
            return False
        success = stitch_clips(generated_clips, output_name, keep_temp=keep_temp)
        if success:
            print(f"\n🎉 Reel assembled: {output_name}")
            if not keep_temp:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            else:
                print(f"ℹ️ Temporary files kept at: {tmp_dir}")
            return True
        else:
            print("❌ Failed to stitch clips.")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if not keep_temp and os.path.exists(tmp_dir):
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass

# ----------------- Argument parsing with interactive fallback -----------------
def parse_args_with_fallback():
    p = argparse.ArgumentParser(description="Convert multiple images into a Veo-generated 9:16 reel. Interactive fallback if args missing.")
    p.add_argument("images", nargs="*", help="Image files, directories, or glob patterns. Example: ./img1.jpg ./img2.png /path/to/dir '*.jpg'")
    p.add_argument("-p", "--prompt", required=False, help="Text prompt describing the desired reel/video style.")
    p.add_argument("-o", "--output", default=None, help="Output filename for the final reel (mp4).")
    p.add_argument("-d", "--duration", type=int, default=4, help="Duration in seconds for each generated clip (default: 4).")
    p.add_argument("--keep-temp", action="store_true", help="Keep temporary generated clips for debugging.")
    args = p.parse_args()

    # Interactive fallback for images
    if not args.images:
        try:
            user_in = input("Enter image paths/glob/directory (comma separated) or press Enter to cancel: ").strip()
        except EOFError:
            user_in = ""
        if not user_in:
            print("❌ No images provided. Exiting.")
            sys.exit(1)
        provided = [s.strip() for s in user_in.split(",") if s.strip()]
        args.images = provided

    # Interactive fallback for prompt
    if not args.prompt:
        try:
            prompt_in = input("Enter text prompt describing the desired reel/video style: ").strip()
        except EOFError:
            prompt_in = ""
        if not prompt_in:
            print("❌ No prompt provided. Exiting.")
            sys.exit(1)
        args.prompt = prompt_in

    return args

def main():
    args = parse_args_with_fallback()
    success = convert_images_to_reel(
        image_inputs=args.images,
        user_prompt=args.prompt,
        output_name=args.output,
        clip_duration=args.duration,
        keep_temp=args.keep_temp
    )
    if success:
        print("✅ Done.")
    else:
        print("❌ Conversion failed.")

if __name__ == "__main__":
    main()
