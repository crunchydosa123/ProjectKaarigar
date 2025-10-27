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
- Better error handling and logging
- API helper function for Flask integration
- Support for empty image_inputs list

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
from typing import List, Optional, Dict
import subprocess
import json
from datetime import datetime

# Google GenAI imports
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

# Logging helper
def log_event(event_type: str, message: str, details: Optional[Dict] = None) -> None:
    """Log events with timestamp and optional details"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{event_type}] {message}")
    if details:
        for key, value in details.items():
            print(f"     {key}: {value}")


# -------------------- Utilities for font / ffmpeg --------------------
COMMON_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def _find_font() -> Optional[str]:
    """Find an available system font for text overlay"""
    for p in COMMON_FONTS:
        if os.path.exists(p):
            log_event("FONT", f"Found system font", {"path": p})
            return p
    log_event("WARN", "No common font found; ffmpeg may use default")
    return None


def _check_ffmpeg_available() -> bool:
    """Check if ffmpeg is installed and available in PATH"""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=5
        )
        log_event("CHECK", "ffmpeg is available")
        return True
    except subprocess.TimeoutExpired:
        log_event("ERROR", "ffmpeg check timed out")
        return False
    except Exception as e:
        log_event("ERROR", f"ffmpeg not found", {"error": str(e)})
        return False


# -------------------- Gemini prompt optimizer --------------------
def optimize_prompt_with_gemini(user_prompt: str, image_path: Optional[str] = None) -> str:
    """Optimize prompt using Gemini 2.5 Flash for video generation
    
    Args:
        user_prompt: Original user prompt
        image_path: Optional path to image for context
        
    Returns:
        Optimized prompt string
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
            if not os.path.exists(image_path):
                log_event("WARN", f"Image not found for context", {"path": image_path})
            else:
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                file_ext = Path(image_path).suffix.lower()
                mime_type = "image/jpeg" if file_ext in ['.jpg', '.jpeg'] else "image/png"
                contents.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
                log_event("INFO", "Image attached to Gemini for context optimization")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
        )
        optimized_prompt = response.text.strip()
        
        if not optimized_prompt:
            raise RuntimeError("Gemini returned empty prompt")
        
        log_event("GEMINI", "Prompt optimized successfully", 
                 {"original_length": len(user_prompt), "optimized_length": len(optimized_prompt)})
        return optimized_prompt
        
    except Exception as e:
        log_event("WARN", "Gemini optimization failed, using fallback", {"error": str(e)})
        fallback_prompt = f"{user_prompt}. Add cinematic motion, camera movement, atmospheric effects, and adapt for 9:16 vertical."
        return fallback_prompt


# -------------------- Video generation --------------------
def generate_clip_for_image(image_path: str, optimized_prompt: str, duration_seconds: int, 
                           tmp_dir: str, idx: int) -> str:
    """Generate video clip from image using Veo 3.1
    
    Args:
        image_path: Path to input image
        optimized_prompt: Optimized text prompt
        duration_seconds: Clip duration in seconds
        tmp_dir: Temporary directory for output
        idx: Clip index for naming
        
    Returns:
        Path to generated MP4 file
        
    Raises:
        RuntimeError: If generation fails
    """
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        image_name = Path(image_path).stem
        out_name = Path(tmp_dir) / f"{idx:03d}_{image_name}_veo.mp4"
        
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        
        file_size_kb = len(img_bytes) / 1024
        log_event("GENERATE", f"Starting image-to-video generation", 
                 {"image": image_name, "size_kb": f"{file_size_kb:.1f}", "duration": f"{duration_seconds}s"})
        
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
        
        log_event("INFO", "Video generation started...")
        poll_count = 0
        while not operation.done:
            time.sleep(10)
            operation = client.operations.get(operation)
            poll_count += 1
            if poll_count % 3 == 0:  # Log every 30 seconds
                log_event("PROGRESS", f"Still generating ({poll_count * 10}s elapsed)")
        
        if not operation.response:
            raise RuntimeError("No response from video generation operation")
        
        result = operation.result
        if not result.generated_videos:
            raise RuntimeError("No videos in generation result")
        
        generated = result.generated_videos[0]
        video_bytes = generated.video.video_bytes
        
        with open(out_name, "wb") as f:
            f.write(video_bytes)
        
        file_size_mb = len(video_bytes) / (1024 * 1024)
        log_event("SUCCESS", "Clip generated successfully", 
                 {"output": out_name.name, "size_mb": f"{file_size_mb:.2f}"})
        
        return str(out_name)
        
    except Exception as e:
        log_event("ERROR", f"Failed to generate clip for image", {"image": image_path, "error": str(e)})
        raise RuntimeError(f"Failed to generate clip for {image_path}: {e}")


def generate_clip_for_text(optimized_prompt: str, duration_seconds: int, 
                          tmp_dir: str, idx: int) -> str:
    """Generate video clip from text-only prompt using Veo 3.1
    
    Args:
        optimized_prompt: Optimized text prompt
        duration_seconds: Clip duration in seconds
        tmp_dir: Temporary directory for output
        idx: Clip index for naming
        
    Returns:
        Path to generated MP4 file
        
    Raises:
        RuntimeError: If generation fails
    """
    try:
        out_name = Path(tmp_dir) / f"{idx:03d}_textonly_veo.mp4"
        
        log_event("GENERATE", f"Starting text-only video generation", 
                 {"duration": f"{duration_seconds}s", "prompt_length": len(optimized_prompt)})
        
        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=optimized_prompt,
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
        
        log_event("INFO", "Text-only video generation started...")
        poll_count = 0
        while not operation.done:
            time.sleep(10)
            operation = client.operations.get(operation)
            poll_count += 1
            if poll_count % 3 == 0:
                log_event("PROGRESS", f"Still generating ({poll_count * 10}s elapsed)")
        
        if not operation.response:
            raise RuntimeError("No response from video generation operation")
        
        result = operation.result
        if not result.generated_videos:
            raise RuntimeError("No videos in generation result")
        
        generated = result.generated_videos[0]
        video_bytes = generated.video.video_bytes
        
        with open(out_name, "wb") as f:
            f.write(video_bytes)
        
        file_size_mb = len(video_bytes) / (1024 * 1024)
        log_event("SUCCESS", "Text-only clip generated successfully", 
                 {"output": out_name.name, "size_mb": f"{file_size_mb:.2f}"})
        
        return str(out_name)
        
    except Exception as e:
        log_event("ERROR", f"Failed to generate text-only clip", {"error": str(e)})
        raise RuntimeError(f"Failed to generate text-only clip: {e}")


# -------------------- Stitching --------------------
def stitch_clips(clips: List[str], final_output: str, keep_temp: bool = False) -> bool:
    """Concatenate multiple MP4 clips into single video using ffmpeg
    
    Args:
        clips: List of input clip paths
        final_output: Path to output combined video
        keep_temp: Whether to keep temporary files
        
    Returns:
        True if successful, False otherwise
    """
    if not clips:
        log_event("ERROR", "No clips provided to stitch")
        return False

    if not _check_ffmpeg_available():
        log_event("ERROR", "ffmpeg not available for stitching")
        return False

    log_event("STITCH", f"Starting to stitch {len(clips)} clips")

    tmp_dir = tempfile.mkdtemp(prefix="veo_ffmpeg_concat_")
    list_file_path = Path(tmp_dir) / "concat_list.txt"
    
    try:
        with open(list_file_path, "w", encoding="utf-8") as lf:
            for c in clips:
                lf.write(f"file '{os.path.abspath(c)}'\n")

        final_output_fwd = str(final_output).replace("\\", "/")

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
            final_output_fwd
        ]

        log_event("INFO", "Running ffmpeg concatenation...")
        completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
        
        if completed.returncode != 0:
            stderr_msg = completed.stderr.decode(errors="ignore")
            log_event("ERROR", "ffmpeg concatenation failed", {"stderr": stderr_msg[-200:]})
            return False

        if os.path.exists(final_output):
            file_size_mb = os.path.getsize(final_output) / (1024 * 1024)
            log_event("SUCCESS", "All clips stitched successfully", 
                     {"output": final_output, "size_mb": f"{file_size_mb:.2f}"})
        else:
            log_event("ERROR", "Output file was not created")
            return False
            
        return True
        
    except subprocess.TimeoutExpired:
        log_event("ERROR", "ffmpeg stitching timed out (>10 minutes)")
        return False
    except Exception as e:
        log_event("ERROR", "ffmpeg concatenation exception", {"error": str(e)})
        return False
    finally:
        if not keep_temp:
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass
        else:
            log_event("INFO", "Temporary files kept", {"path": tmp_dir})


# -------------------- Input collection --------------------
def collect_image_paths(inputs: List[str]) -> List[str]:
    """Collect and deduplicate image paths from various input formats
    
    Args:
        inputs: List of file paths, directories, or glob patterns
        
    Returns:
        Deduplicated list of valid image paths
    """
    paths = []
    
    for item in inputs:
        item = os.path.expanduser(item)
        
        if os.path.isdir(item):
            log_event("INFO", f"Scanning directory for images", {"directory": item})
            for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp"):
                matched = sorted(glob.glob(os.path.join(item, ext)))
                paths.extend(matched)
                
        elif any(ch in item for ch in "*?[]"):
            matched = sorted(glob.glob(item))
            if matched:
                log_event("INFO", f"Glob pattern matched {len(matched)} files")
                paths.extend(matched)
            else:
                log_event("WARN", f"Glob pattern matched no files", {"pattern": item})
                
        else:
            if os.path.exists(item):
                paths.append(item)
            else:
                log_event("WARN", f"Path not found", {"path": item})
    
    # Remove duplicates while preserving order
    seen = set()
    ordered = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            ordered.append(p)
    
    log_event("INFO", f"Collected {len(ordered)} unique images")
    return ordered


# -------------------- Main conversion logic --------------------
def convert_images_to_reel(image_inputs: List[str], user_prompt: str, output_name: str = None,
                           clip_duration: int = 4, keep_temp: bool = False, segments: int = 1,
                           captions: Optional[List[str]] = None, text_only: bool = False) -> bool:
    """Main orchestration for video generation
    
    Supports:
    - Multiple segments per image
    - Text captions on clips
    - Text-only generation (no images)
    
    Args:
        image_inputs: List of image paths (can be empty for text-only)
        user_prompt: Text prompt for video generation
        output_name: Output MP4 filename (auto-generated if None)
        clip_duration: Duration per clip in seconds
        keep_temp: Whether to keep temporary files
        segments: Number of segments per image
        captions: Optional list of captions for clips
        text_only: If True, generate from text only (no images needed)
        
    Returns:
        bool: True if successful, False otherwise
    """
    log_event("START", "=== REEL GENERATION START ===")
    
    # Safely handle empty or None image_inputs
    if image_inputs is None:
        image_inputs = []
    
    image_paths = collect_image_paths(image_inputs) if image_inputs else []

    if not image_paths and not text_only:
        log_event("ERROR", "No valid images and text-only not requested")
        return False

    if not output_name:
        output_name = f"reel_{int(time.time())}.mp4"
    
    tmp_dir = tempfile.mkdtemp(prefix="veo_reel_")
    log_event("INFO", "Temporary directory created", {"path": tmp_dir})
    
    generated_clips = []

    # Motion variations for dynamic segment generation
    motion_variations = [
        "slow push-in, gentle dolly forward, soft cinematic haze",
        "slow pan left with parallax, subtle speed ramp, golden rim light",
        "dramatic zoom out, slight camera vibrance, moody contrast",
        "floating dolly up, slow reveal, atmospheric fog",
        "slow tracking right, filmic grain, warm cinematic glow",
    ]

    # Compute total segments
    total_segments = (len(image_paths) if image_paths else 0) * max(1, segments)
    if text_only:
        total_segments = max(1, segments)

    # Normalize captions list
    caption_sequence = []
    if captions:
        if len(captions) == 1:
            caption_sequence = captions * total_segments
        elif len(image_paths) > 0 and len(captions) == len(image_paths):
            for c in captions:
                caption_sequence.extend([c] * max(1, segments))
        elif len(captions) == total_segments:
            caption_sequence = captions[:]
        else:
            log_event("WARN", "Caption count mismatch, using first caption for all")
            caption_sequence = [captions[0]] * total_segments if captions else []

    try:
        clip_idx = 1

        if text_only and not image_paths:
            log_event("INFO", f"Generating text-only content with {total_segments} segment(s)")
            optimized_prompt_base = optimize_prompt_with_gemini(user_prompt, image_path=None)
            
            for s in range(total_segments):
                variation = motion_variations[s % len(motion_variations)]
                optimized_prompt = f"{optimized_prompt_base}. {variation}"
                try:
                    clip_path = generate_clip_for_text(optimized_prompt, duration_seconds=clip_duration, 
                                                      tmp_dir=tmp_dir, idx=clip_idx)
                    # Skip text overlay
                    generated_clips.append(clip_path)
                    clip_idx += 1
                except Exception as e:
                    log_event("WARN", f"Skipped segment", {"index": clip_idx, "error": str(e)})
                    
        else:
            for img_idx, img in enumerate(image_paths, start=1):
                num_this_image = segments if segments > 0 else 1
                log_event("INFO", f"Processing image [{img_idx}/{len(image_paths)}]", 
                         {"image": Path(img).name, "segments": num_this_image})
                
                optimized_prompt_base = optimize_prompt_with_gemini(user_prompt, img)

                for s in range(num_this_image):
                    variation = motion_variations[s % len(motion_variations)]
                    optimized_prompt = f"{optimized_prompt_base}. {variation}"

                    try:
                        clip_path = generate_clip_for_image(img, optimized_prompt, duration_seconds=clip_duration, 
                                                           tmp_dir=tmp_dir, idx=clip_idx)
                        # Skip text overlay
                        generated_clips.append(clip_path)
                        clip_idx += 1
                    except Exception as e:
                        log_event("WARN", f"Skipped segment", {"index": clip_idx, "error": str(e)})

        if not generated_clips:
            log_event("ERROR", "No clips were generated")
            return False

        log_event("INFO", f"All {len(generated_clips)} clips generated, starting stitch...")
        success = stitch_clips(generated_clips, output_name, keep_temp=keep_temp)
        
        if success:
            log_event("SUCCESS", "Reel generated successfully", {"output": output_name})
            
            if not keep_temp:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            else:
                log_event("INFO", "Temporary files preserved", {"path": tmp_dir})
                
            return True
        else:
            log_event("ERROR", "Failed to stitch clips")
            return False
            
    except Exception as e:
        log_event("ERROR", "Unexpected error during generation", {"error": str(e)})
        return False
    finally:
        if not keep_temp and os.path.exists(tmp_dir):
            try:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass

        log_event("END", "=== REEL GENERATION COMPLETE ===")


# -------------------- API Helper Function --------------------
def get_reel_status(output_path: str) -> Dict:
    """Get status of generated reel (for API responses)
    
    Args:
        output_path: Path to generated video file
        
    Returns:
        Dict with video metadata or error info
    """
    try:
        if not os.path.exists(output_path):
            return {
                "success": False,
                "error": "Video file not found",
                "path": output_path
            }
        
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        file_name = os.path.basename(output_path)
        created_timestamp = os.path.getctime(output_path)
        created_datetime = datetime.fromtimestamp(created_timestamp)
        
        return {
            "success": True,
            "file_name": file_name,
            "file_path": output_path,
            "file_size_mb": round(file_size_mb, 2),
            "created_at": created_datetime.isoformat()
        }
    except Exception as e:
        log_event("ERROR", "Failed to get reel status", {"error": str(e)})
        return {
            "success": False,
            "error": str(e)
        }


# -------------------- CLI --------------------
def parse_args_with_fallback():
    p = argparse.ArgumentParser(
        description="Convert images/text to Veo-generated 9:16 vertical reel with optional captions"
    )
    p.add_argument("images", nargs="*", help="Image files, directories, or glob patterns")
    p.add_argument("-p", "--prompt", required=False, help="Text prompt for video generation")
    p.add_argument("-o", "--output", default=None, help="Output MP4 filename")
    p.add_argument("-d", "--duration", type=int, default=4, help="Duration per clip in seconds (default: 4)")
    p.add_argument("--keep-temp", action="store_true", help="Keep temporary files for debugging")
    p.add_argument("--segments", type=int, default=1, help="Segments per image (default: 1)")
    p.add_argument("--captions", type=str, default=None, help="Comma-separated captions")
    p.add_argument("--captions-file", type=str, default=None, help="File with captions (one per line)")
    p.add_argument("--text-only", action="store_true", help="Generate from text only (no images)")
    
    args = p.parse_args()

    # Interactive fallback for images
    if not args.images:
        if not args.text_only:
            try:
                user_in = input("Images (paths/glob/dir) or 'text' for text-only, or Enter to cancel: ").strip()
            except EOFError:
                user_in = ""
            
            if not user_in:
                log_event("ERROR", "No input provided")
                sys.exit(1)
            
            if user_in.lower() == 'text':
                args.text_only = True
                args.images = []
            else:
                args.images = [s.strip() for s in user_in.split(",") if s.strip()]

    # Interactive fallback for prompt
    if not args.prompt:
        try:
            prompt_in = input("Enter video prompt: ").strip()
        except EOFError:
            prompt_in = ""
        
        if not prompt_in:
            log_event("ERROR", "No prompt provided")
            sys.exit(1)
        
        args.prompt = prompt_in

    # Load captions
    captions_list = None
    if args.captions_file:
        if os.path.exists(args.captions_file):
            with open(args.captions_file, "r", encoding="utf-8") as cf:
                lines = [l.strip() for l in cf.readlines() if l.strip()]
                captions_list = lines if lines else None
        else:
            log_event("WARN", f"Captions file not found", {"path": args.captions_file})
    elif args.captions:
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
        log_event("SUCCESS", "Conversion completed successfully")
    else:
        log_event("ERROR", "Conversion failed")
        sys.exit(1)


if __name__ == "__main__":
    main()