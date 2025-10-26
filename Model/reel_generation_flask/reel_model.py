#!/usr/bin/env python3
"""
Image(s) to Veo Reel Converter (interactive fallback)

- Accepts multiple images (paths, glob or directory)
- If images or prompt are omitted on the command line, asks interactively
- Uses ffmpeg only to stitch clips (no moviepy anywhere)

Enhancements added in this version:
- Support producing multiple segments per image (useful when only 1 image is provided to make a multi-shot reel)
- Support text captions applied to clips (single caption, per-image captions, or per-segment captions)
- Support generating a video purely from text (no images) using Veo
- New CLI flags: --segments, --captions, --captions-file, --text-only

Note: ffmpeg is required for stitching and caption overlay. Make sure ffmpeg is installed and available in PATH.
"""

import os
import sys
import time
import glob
import argparse
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional
import subprocess

# Google GenAI imports (same as your original)
from google import genai
from google.genai import types

# Configuration
PROJECT_ID = "useful-figure-475210-g7"
LOCATION = "us-central1"

# Initialize client
client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

# -------------------- Utilities for font / ffmpeg --------------------
COMMON_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def _find_font() -> Optional[str]:
    for p in COMMON_FONTS:
        if os.path.exists(p):
            return p
    return None


def _check_ffmpeg_available() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except Exception:
        return False


# -------------------- Gemini prompt optimizer (unchanged) --------------------
def optimize_prompt_with_gemini(user_prompt: str, image_path: Optional[str] = None) -> str:
    """If image_path provided, attach the image bytes for Gemini to analyze; otherwise just optimize based on text.
    Returns a single-line optimized prompt.
    """
    try:
        contents = []
        gemini_prompt = f"""
        You are an expert video prompt engineer for Google's Veo 3.1 model.

        The user wants to create a vertical reel clip from this prompt: "{user_prompt}"

        Analyze context (and the provided image if any) and produce a single-line optimized prompt suitable for a 9:16 cinematic short:
        * Include camera movements (zoom, dolly, pan), temporal elements (slow-mo, speed ramp), atmosphere (lighting, weather),
          subject animation, and a clear cinematic mood.
        * Keep it compact and focused (one sentence).
        Output ONLY the optimized prompt.
        """
        contents.append(gemini_prompt)
        if image_path:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            file_ext = Path(image_path).suffix.lower()
            mime_type = "image/jpeg" if file_ext in ['.jpg', '.jpeg'] else "image/png"
            contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
        )
        optimized_prompt = response.text.strip()
        if not optimized_prompt:
            raise RuntimeError("Gemini returned empty prompt")
        print(f"🤖 Gemini optimized prompt: {optimized_prompt}")
        return optimized_prompt
    except Exception as e:
        print(f"⚠️  Gemini optimization failed: {e}")
        fallback_prompt = f"{user_prompt}. Add cinematic motion, camera movement, atmospheric effects, and adapt for 9:16 vertical."
        print(f"🔄 Using fallback prompt: {fallback_prompt}")
        return fallback_prompt


# -------------------- Video generation --------------------
def generate_clip_for_image(image_path: str, optimized_prompt: str, duration_seconds: int, tmp_dir: str, idx: int) -> str:
    """Generate a single video clip for the given image using Veo. Returns the path to the generated mp4."""
    try:
        image_name = Path(image_path).stem
        out_name = Path(tmp_dir) / f"{idx:03d}_{image_name}_veo.mp4"
        print(f"🎬 Starting generation for {image_path} -> {out_name.name}")
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


def generate_clip_for_text(optimized_prompt: str, duration_seconds: int, tmp_dir: str, idx: int) -> str:
    """Generate a single video clip from text-only prompt using Veo (no image). Returns the path to the generated mp4."""
    try:
        out_name = Path(tmp_dir) / f"{idx:03d}_textonly_veo.mp4"
        print(f"🎬 Starting text-only generation -> {out_name.name}")
        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=optimized_prompt,
            # no image provided for text-only generation
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
        print(f"✅ Text-only clip ready: {out_name} ({len(video_bytes)/(1024*1024):.1f} MB)")
        return str(out_name)
    except Exception as e:
        raise RuntimeError(f"Failed to generate text-only clip: {e}")


# -------------------- Text overlay with ffmpeg --------------------
def overlay_text_on_clip(clip_path: str, text: str, out_path: str, fontsize: int = 46, margin_bottom: int = 80) -> bool:
    """Overlay a single-line (or short multi-line) caption onto clip_path and write to out_path using ffmpeg drawtext.

    Uses a common system font when available. If none found the drawtext may still work depending on ffmpeg build.
    """
    if not _check_ffmpeg_available():
        print("❌ ffmpeg not found. Please install ffmpeg and ensure it is in your PATH.")
        return False

    font = _find_font()
    # Use a temporary text file to avoid complex escaping for drawtext
    tmp_txt = None
    try:
        tmp_dir = tempfile.mkdtemp(prefix="veo_caption_")
        tmp_txt = Path(tmp_dir) / "caption.txt"
        with open(tmp_txt, "w", encoding="utf-8") as f:
            f.write(text)

        drawtext_parts = [
            f"textfile={str(tmp_txt)}",
            f"fontsize={fontsize}",
            "fontcolor=white",
            "box=1",
            "boxcolor=black@0.5",
            "boxborderw=10",
            # center horizontally, position above bottom by margin
            "x=(w-text_w)/2",
            f"y=h-text_h-{margin_bottom}",
            "reload=1",
        ]
        if font:
            drawtext_parts.insert(0, f"fontfile='{font}'")

        vf = "drawtext=" + ":".join(drawtext_parts)

        cmd = [
            "ffmpeg",
            "-y",
            "-i", clip_path,
            "-vf", vf,
            "-c:a", "copy",
            out_path
        ]
        print(f"🔁 Adding caption to {Path(clip_path).name}: '{text[:60]}{'...' if len(text)>60 else ''}'")
        completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if completed.returncode != 0:
            print("❌ ffmpeg text overlay failed. stderr:")
            print(completed.stderr.decode(errors="ignore"))
            return False
        return True
    except Exception as e:
        print(f"❌ overlay_text_on_clip error: {e}")
        return False
    finally:
        if tmp_txt and tmp_txt.exists():
            try:
                tmp_txt.unlink()
            except Exception:
                pass
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass


# -------------------- Stitching (unchanged, but now can accept overlaid files) --------------------
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

    print(f"🔗 Stitching {len(clips)} clips into {final_output} using ffmpeg")

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


# -------------------- Input collection (unchanged) --------------------
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


# -------------------- Main conversion logic --------------------
def convert_images_to_reel(image_inputs: List[str], user_prompt: str, output_name: str = None,
                           clip_duration: int = 4, keep_temp: bool = False, segments: int = 1,
                           captions: Optional[List[str]] = None, text_only: bool = False) -> bool:
    """Main orchestration. Supports multiple segments per image, caption overlay, and text-only generation.

    captions: optional list of caption strings. Interpretation rules:
      - If None: no captions applied.
      - If single-element list: same caption for all generated clips.
      - If list length == number of images: that caption will be used for all segments of that image.
      - If list length == total_segments (images * segments): captions applied sequentially to generated clips.
    text_only: when True and no images provided, generate clips purely from the prompt.
    """
    image_paths = collect_image_paths(image_inputs)

    if not image_paths and not text_only:
        print("❌ No valid images provided and text-only not requested.")
        return False

    if not output_name:
        output_name = f"reel_{int(time.time())}.mp4"
    tmp_dir = tempfile.mkdtemp(prefix="veo_reel_")
    print(f"🗂️  Temporary working directory: {tmp_dir}")
    generated_clips = []

    # small set of variation phrases to produce distinct segments from a single image or text
    motion_variations = [
        "slow push-in, gentle dolly forward, soft cinematic haze",
        "slow pan left with parallax, subtle speed ramp, golden rim light",
        "dramatic zoom out, slight camera vibrance, moody contrast",
        "floating dolly up, slow reveal, atmospheric fog",
        "slow tracking right, filmic grain, warm cinematic glow",
    ]

    # compute total segments
    total_items = max(1, len(image_paths) if image_paths else 0)
    total_segments = (len(image_paths) if image_paths else 0) * max(1, segments)
    if text_only:
        # for text-only, total_segments is simply segments
        total_segments = max(1, segments)

    caption_sequence = []
    if captions:
        # normalize captions list based on rules described above
        if len(captions) == 1:
            caption_sequence = captions * total_segments
        elif len(image_paths) > 0 and len(captions) == len(image_paths):
            # expand per-image captions to per-segment
            for c in captions:
                caption_sequence.extend([c] * max(1, segments))
        elif len(captions) == total_segments:
            caption_sequence = captions[:]
        else:
            print("⚠️  Number of captions doesn't match images or segments. Falling back to single caption if provided.")
            caption_sequence = [captions[0]] * total_segments

    try:
        clip_idx = 1

        if text_only and not image_paths:
            print(f"=== Generating text-only content: {total_segments} segment(s) ===")
            optimized_prompt_base = optimize_prompt_with_gemini(user_prompt, image_path=None)
            for s in range(total_segments):
                variation = motion_variations[s % len(motion_variations)]
                optimized_prompt = f"{optimized_prompt_base}. {variation}"
                try:
                    clip_path = generate_clip_for_text(optimized_prompt, duration_seconds=clip_duration, tmp_dir=tmp_dir, idx=clip_idx)
                    caption_text = caption_sequence[clip_idx - 1] if caption_sequence else None
                    if caption_text:
                        overlaid = Path(tmp_dir) / f"{Path(clip_path).stem}_caption.mp4"
                        success_overlay = overlay_text_on_clip(clip_path, caption_text, str(overlaid))
                        if success_overlay:
                            generated_clips.append(str(overlaid))
                        else:
                            print("⚠️  Caption overlay failed; using original clip")
                            generated_clips.append(clip_path)
                    else:
                        generated_clips.append(clip_path)
                    clip_idx += 1
                except Exception as e:
                    print(f"❌ Skipped segment due to error: {e}")
        else:
            for img_idx, img in enumerate(image_paths, start=1):
                num_this_image = segments if segments > 0 else 1
                print(f"=== Processing image [{img_idx}/{len(image_paths)}]: {img} (will produce {num_this_image} segment(s)) ===")
                optimized_prompt_base = optimize_prompt_with_gemini(user_prompt, img)

                for s in range(num_this_image):
                    # create a prompt variation for each segment (helps single-image reels feel dynamic)
                    variation = motion_variations[(s) % len(motion_variations)]
                    optimized_prompt = f"{optimized_prompt_base}. {variation}"

                    try:
                        clip_path = generate_clip_for_image(img, optimized_prompt, duration_seconds=clip_duration, tmp_dir=tmp_dir, idx=clip_idx)

                        # apply caption overlay if requested
                        caption_text = caption_sequence[clip_idx - 1] if caption_sequence else None
                        if caption_text:
                            overlaid = Path(tmp_dir) / f"{Path(clip_path).stem}_caption.mp4"
                            success_overlay = overlay_text_on_clip(clip_path, caption_text, str(overlaid))
                            if success_overlay:
                                generated_clips.append(str(overlaid))
                            else:
                                print("⚠️  Caption overlay failed; using original clip")
                                generated_clips.append(clip_path)
                        else:
                            generated_clips.append(clip_path)

                        clip_idx += 1
                    except Exception as e:
                        print(f"❌ Skipped segment due to error: {e}")

        if not generated_clips:
            print("❌ No clips were generated. Aborting.")
            return False

        success = stitch_clips(generated_clips, output_name, keep_temp=keep_temp)
        if success:
            print(f"🎉 Reel assembled: {output_name}")
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
    p.add_argument("--segments", type=int, default=1, help="Number of segments to produce per image (or total segments for text-only). Useful when only 1 image is provided (default: 1).")
    p.add_argument("--captions", type=str, default=None, help="Optional captions. Provide a single caption, comma-separated captions per image, or comma-separated captions per segment.")
    p.add_argument("--captions-file", type=str, default=None, help="Path to a text file containing captions (one per line). If provided it overrides --captions.")
    p.add_argument("--text-only", action="store_true", help="Generate a video from text prompt only (no images). If images provided, this is ignored.)")
    args = p.parse_args()

    # Interactive fallback for images and text-only behavior
    if not args.images:
        # If user didn't pass images, allow text-only if requested; otherwise prompt interactively
        if not args.text_only:
            try:
                user_in = input("Enter image paths/glob/directory (comma separated), or type 'text' to create a text-only video, or press Enter to cancel: ").strip()
            except EOFError:
                user_in = ""
            if not user_in:
                print("❌ No images provided. Exiting.")
                sys.exit(1)
            if user_in.lower() == 'text':
                args.text_only = True
                args.images = []
            else:
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

    # Normalize captions from CLI
    captions_list = None
    if args.captions_file:
        if os.path.exists(args.captions_file):
            with open(args.captions_file, "r", encoding="utf-8") as cf:
                lines = [l.strip() for l in cf.readlines() if l.strip()]
                captions_list = lines if lines else None
        else:
            print(f"⚠️  captions-file not found: {args.captions_file}")
    elif args.captions:
        # split on comma but allow escaped commas? simple split first
        captions_list = [c.strip() for c in args.captions.split(",") if c.strip()]

    args._captions_list = captions_list
    return args


def main():
    args = parse_args_with_fallback()
    success = convert_images_to_reel(
        image_inputs=args.images,
        user_prompt=args.prompt,
        output_name=args.output,
        clip_duration=args.duration,
        keep_temp=args.keep_temp,
        segments=args.segments,
        captions=args._captions_list,
        text_only=args.text_only
    )
    if success:
        print("✅ Done.")
    else:
        print("❌ Conversion failed.")


if __name__ == "__main__":
    main()
