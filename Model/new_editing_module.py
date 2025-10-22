# ai_ffmpeg_editor.py
"""
AI-Powered FFmpeg Video/Image Editor - Interactive Version
Enhanced with music, cropping, trimming, and more features!

Just run: python datapython.py
"""

import os
import json
from pathlib import Path
import ffmpeg
from google import genai
import requests
from urllib.parse import urlparse
import tempfile
import subprocess
import shutil

# Configuration
GOOGLE_API_KEY = "AIzaSyDiUMs4sIAdOk09006hS7DcY79DZh53_M4"
OUTPUT_DIR = "outputs"
MUSIC_DIR = "music_library"
TEMP_DIR = "temp_segments"

# Trending Songs Library
TRENDING_SONGS = [
    {"id": "s1", "title": "Sahiba", "artist": "Aditya Rikhari", "duration": 30, "public_url": "https://drive.google.com/uc?export=download&id=1u5k0HPhka_ytUGLt6eyn3awVM3oYSS6b"},
    {"id": "s2", "title": "Saiyaara", "artist": "Tanishk Bagchi", "duration": 28, "public_url": "https://drive.google.com/uc?export=download&id=1CaPk8_CvQdH1FUZiEGVkjpbAff3FMaEz"},
    {"id": "s3", "title": "Dard", "artist": "Kushagra", "duration": 32, "public_url": "https://drive.google.com/uc?export=download&id=1fLXKnSdCmNYztsPTQf6S7Xxbnanw4M5E"},
    {"id": "s4", "title": "Kaanamale", "artist": "Mugen Rao", "duration": 25, "public_url": "https://drive.google.com/uc?export=download&id=1MixJI_YU5S2ORKfrQamOs-TbrmpTZi4m"},
    {"id": "s5", "title": "Pardesiya", "artist": "Sachin-Jigar", "duration": 29, "public_url": "https://drive.google.com/uc?export=download&id=1GC0zEcPp-TYMbCpr-p1u-zaHHsGB_Uuy"},
    {"id": "s6", "title": "Noormahal", "artist": "Chani Nattan", "duration": 27, "public_url": "https://drive.google.com/uc?export=download&id=1XtSSZOeaH1Uu8oBmDKzbFQXxl0EiDe5V"},
    {"id": "s7", "title": "The Night We Met", "artist": "Lord Huron", "duration": 30, "public_url": "https://drive.google.com/uc?export=download&id=1cz0o_si2oIaWKu5a3rgERbWoOCW5r9aS"},
    {"id": "s8", "title": "Yaarum Sollala", "artist": "Shreyas Narasimhan", "duration": 31, "public_url": "https://drive.google.com/uc?export=download&id=1JyncQt2piEU-0VdVCywpYPeGn0fJpID2"},
    {"id": "s9", "title": "Sapphire", "artist": "Ed Sheeran", "duration": 26, "public_url": "https://drive.google.com/uc?export=download&id=16jpFu95nzQy-vAky1U_h0UIsg0gGToPR"},
]

# Initialize Gemini Client
client = genai.Client(api_key=GOOGLE_API_KEY)


def download_song(song: dict) -> str:
    """Download a song from URL and return local path"""
    os.makedirs(MUSIC_DIR, exist_ok=True)
    
    filename = f"{song['id']}_{song['title'].replace(' ', '_')}.mp3"
    filepath = os.path.join(MUSIC_DIR, filename)
    
    if os.path.exists(filepath):
        print(f"   ✅ Song already cached: {song['title']}")
        return filepath
    
    try:
        print(f"   📥 Downloading: {song['title']} by {song['artist']}...")
        response = requests.get(song['public_url'], stream=True, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"   ✅ Downloaded successfully!")
        return filepath
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        return None


def display_trending_songs():
    """Display trending songs library"""
    print("\n🎵 TRENDING SONGS LIBRARY:")
    print("=" * 70)
    for idx, song in enumerate(TRENDING_SONGS, 1):
        print(f"  {idx}. {song['title']} - {song['artist']} ({song['duration']}s)")
    print("=" * 70)


def parse_prompt_to_ffmpeg(user_prompt: str, media_type: str, video_duration: float = 0, video_width: int = 0, video_height: int = 0) -> dict:
    """
    Converts natural language prompt to FFmpeg command parameters using Gemini
    """
    
    system_instruction = f"""You are an expert FFmpeg command generator. 
The user will provide a description of what they want to do with their {media_type}.
The video duration is {video_duration:.2f} seconds.
The video resolution is {video_width}x{video_height}.
Generate the appropriate FFmpeg filter chain and parameters.

IMPORTANT: When user says "cut first X seconds and add to end/last", they want to:
1. REMOVE the first X seconds from the beginning
2. APPEND those X seconds to the end of the video
Result: Video will start from X seconds and end with the original first X seconds

Return your response in this exact JSON format:
{{
    "filter_chain": "the FFmpeg filter string",
    "explanation": "brief explanation of what this does",
    "additional_params": {{"key": "value"}} for any extra parameters,
    "audio_file": "path/to/audio.mp3" if adding music (optional),
    "requires_audio_input": true/false if the operation needs an audio file,
    "use_trending_song": true/false if user wants to use trending songs,
    "trim_operation": {{"start": 0, "end": 10, "action": "keep"}} for trim operations,
    "complex_edit": {{"type": "cut_and_move", "segments": [...]}} for complex operations
}}

VISUAL EFFECTS:
- "make it black and white" → {{"filter_chain": "hue=s=0", "explanation": "Removes color saturation"}}
- "add blur effect" → {{"filter_chain": "boxblur=5:1", "explanation": "Applies box blur"}}
- "increase brightness" → {{"filter_chain": "eq=brightness=0.1", "explanation": "Increases brightness by 10%"}}
- "decrease brightness" → {{"filter_chain": "eq=brightness=-0.1", "explanation": "Decreases brightness by 10%"}}
- "increase contrast" → {{"filter_chain": "eq=contrast=1.5", "explanation": "Increases contrast"}}
- "add sepia tone" → {{"filter_chain": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131", "explanation": "Applies sepia tone effect"}}
- "sharpen" → {{"filter_chain": "unsharp=5:5:1.0:5:5:0.0", "explanation": "Sharpens the image"}}
- "add vignette" → {{"filter_chain": "vignette=PI/4", "explanation": "Adds dark vignette effect"}}
- "vintage effect" → {{"filter_chain": "curves=vintage", "explanation": "Applies vintage color curves"}}
- "negate colors" → {{"filter_chain": "negate", "explanation": "Inverts all colors"}}

ROTATION & FLIP:
- "rotate 90 degrees clockwise" → {{"filter_chain": "transpose=1", "explanation": "Rotates 90 degrees clockwise"}}
- "rotate 180 degrees" → {{"filter_chain": "hflip,vflip", "explanation": "Rotates 180 degrees"}}
- "flip horizontal" → {{"filter_chain": "hflip", "explanation": "Flips horizontally"}}
- "flip vertical" → {{"filter_chain": "vflip", "explanation": "Flips vertically"}}

SPEED & TIME:
- "speed up 2x" → {{"filter_chain": "setpts=0.5*PTS", "explanation": "Speeds up video by 2x", "additional_params": {{"filter:a": "atempo=2.0"}}}}
- "slow down 2x" → {{"filter_chain": "setpts=2.0*PTS", "explanation": "Slows down video by 2x", "additional_params": {{"filter:a": "atempo=0.5"}}}}

TRIMMING & CUTTING:
- "trim first 10 seconds" → {{"trim_operation": {{"start": 0, "end": 10, "action": "remove"}}, "explanation": "Removes first 10 seconds"}}
- "trim last 5 seconds" → {{"trim_operation": {{"start": -5, "end": 0, "action": "remove"}}, "explanation": "Removes last 5 seconds"}}
- "keep only first 20 seconds" → {{"trim_operation": {{"start": 0, "end": 20, "action": "keep"}}, "explanation": "Keeps only first 20 seconds"}}
- "cut from 10 to 30 seconds" → {{"trim_operation": {{"start": 10, "end": 30, "action": "keep"}}, "explanation": "Extracts segment from 10s to 30s"}}
- "remove middle 10 seconds" → {{"complex_edit": {{"type": "remove_middle", "start": 10, "duration": 10}}, "explanation": "Removes 10 seconds from middle"}}

ADVANCED CUTTING & REARRANGING (MOST IMPORTANT):
- "cut first 2 seconds and add to end" → {{"complex_edit": {{"type": "move_segment", "source_start": 0, "source_end": 2, "target_position": "end"}}, "explanation": "Cuts first 2s and appends to end. New video: [2s→end] + [0→2s]"}}
- "cut first 5 seconds and add to end" → {{"complex_edit": {{"type": "move_segment", "source_start": 0, "source_end": 5, "target_position": "end"}}, "explanation": "Cuts first 5s and appends to end"}}
- "cut first 10 seconds and move to end" → {{"complex_edit": {{"type": "move_segment", "source_start": 0, "source_end": 10, "target_position": "end"}}, "explanation": "Moves first 10s to end"}}
- "cut first 3 seconds and add to last" → {{"complex_edit": {{"type": "move_segment", "source_start": 0, "source_end": 3, "target_position": "end"}}, "explanation": "Moves first 3s to end"}}
- "cut last 5 seconds and add to beginning" → {{"complex_edit": {{"type": "move_segment", "source_start": {video_duration-5}, "source_end": {video_duration}, "target_position": "beginning"}}, "explanation": "Moves last 5s to beginning"}}
- "cut middle 10 seconds (from 20s) and add to end" → {{"complex_edit": {{"type": "move_segment", "source_start": 20, "source_end": 30, "target_position": "end"}}, "explanation": "Moves middle segment to end"}}
- "cut first 5 seconds and insert before last 2 seconds" → {{"complex_edit": {{"type": "move_segment", "source_start": 0, "source_end": 5, "target_position": "before_end", "offset": 2}}, "explanation": "Inserts first 5s before last 2s"}}
- "reverse the video" → {{"filter_chain": "reverse", "explanation": "Reverses video playback", "additional_params": {{"filter:a": "areverse"}}}}
- "loop 3 times" → {{"complex_edit": {{"type": "loop", "count": 3}}, "explanation": "Repeats video 3 times"}}

CROPPING & RESIZING - PORTRAIT MODE (9:16 for Instagram Reels/TikTok/YouTube Shorts):
- "make it portrait" → {{"filter_chain": "crop=ih*9/16:ih:(iw-ih*9/16)/2:0", "explanation": "Crops to 9:16 portrait (1080x1920) centered"}}
- "convert to portrait mode" → {{"filter_chain": "crop=ih*9/16:ih:(iw-ih*9/16)/2:0", "explanation": "Crops to vertical portrait 9:16"}}
- "crop for instagram reel" → {{"filter_chain": "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920", "explanation": "Crops to Instagram Reels format (1080x1920)"}}
- "crop for tiktok" → {{"filter_chain": "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920", "explanation": "Crops to TikTok format (1080x1920)"}}
- "crop for youtube shorts" → {{"filter_chain": "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920", "explanation": "Crops to YouTube Shorts format (1080x1920)"}}
- "mobile view" → {{"filter_chain": "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920", "explanation": "Crops to mobile portrait view"}}
- "vertical video" → {{"filter_chain": "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920", "explanation": "Crops to vertical 9:16 format"}}

CROPPING & RESIZING - OTHER FORMATS:
- "crop to square" → {{"filter_chain": "crop=ih:ih", "explanation": "Crops to square (1:1) aspect ratio"}}
- "crop to 16:9" → {{"filter_chain": "crop=ih*16/9:ih", "explanation": "Crops to 16:9 widescreen"}}
- "resize to 1080p" → {{"filter_chain": "scale=-1:1080", "explanation": "Resizes to 1080p height"}}
- "resize to 720p" → {{"filter_chain": "scale=-1:720", "explanation": "Resizes to 720p height"}}
- "crop center" → {{"filter_chain": "crop=iw/2:ih/2:iw/4:ih/4", "explanation": "Crops center 50% of video"}}

AUDIO OPERATIONS:
- "remove audio" → {{"filter_chain": "", "explanation": "Removes all audio", "additional_params": {{"an": None}}}}
- "add music" → {{"filter_chain": "", "explanation": "Adds background music from library", "requires_audio_input": true, "use_trending_song": true}}
- "add trending music" → {{"filter_chain": "", "explanation": "Adds music from trending library", "requires_audio_input": true, "use_trending_song": true}}
- "increase volume" → {{"filter_chain": "", "explanation": "Increases audio volume by 2x", "additional_params": {{"filter:a": "volume=2.0"}}}}
- "fade in audio" → {{"filter_chain": "", "explanation": "Fades in audio over 3 seconds", "additional_params": {{"filter:a": "afade=t=in:st=0:d=3"}}}}

ADVANCED EFFECTS:
- "stabilize video" → {{"filter_chain": "deshake", "explanation": "Stabilizes shaky footage"}}
- "denoise video" → {{"filter_chain": "hqdn3d", "explanation": "Reduces video noise"}}
- "pixelate" → {{"filter_chain": "scale=iw/10:ih/10,scale=iw*10:ih*10:flags=neighbor", "explanation": "Creates pixelated effect"}}

CRITICAL RULES:
1. "cut first X and add to end" ALWAYS means: remove first X seconds from beginning and append to end
2. Use "move_segment" type with "target_position": "end" for these operations
3. source_start and source_end must be the EXACT seconds to cut
4. The remaining video (after the cut) comes FIRST, then the cut segment
5. For portrait mode: ALWAYS use 9:16 aspect ratio (width = height * 9/16)
6. Portrait crop formula: crop=ih*9/16:ih:(iw-ih*9/16)/2:0 (crops from center)
7. For Instagram/TikTok: Add ,scale=1080:1920 after crop for standard resolution

Only return valid JSON. Do not include any markdown formatting or extra text.
"""
    
    prompt = f"{system_instruction}\n\nUser request: {user_prompt}\nMedia type: {media_type}\nVideo duration: {video_duration:.2f}s\nResolution: {video_width}x{video_height}"
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt
        )
        
        response_text = response.text.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip()
        
        result = json.loads(response_text)
        
        return {
            "success": True,
            "filter_chain": result.get("filter_chain", ""),
            "explanation": result.get("explanation", ""),
            "additional_params": result.get("additional_params", {}),
            "audio_file": result.get("audio_file"),
            "requires_audio_input": result.get("requires_audio_input", False),
            "use_trending_song": result.get("use_trending_song", False),
            "trim_operation": result.get("trim_operation"),
            "complex_edit": result.get("complex_edit"),
            "raw_response": response_text
        }
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON Parse Error: {e}")
        return {
            "success": False,
            "error": "Could not parse AI response as JSON",
            "raw_response": response_text if 'response_text' in locals() else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def concat_videos_with_file_list(video_files: list, output_path: str) -> dict:
    """
    Concatenate videos using FFmpeg concat demuxer (file list method)
    This is more reliable than complex filtergraphs
    """
    try:
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        # Create concat file list
        concat_file = os.path.join(TEMP_DIR, "concat_list.txt")
        with open(concat_file, 'w') as f:
            for video_file in video_files:
                # Use absolute path and escape special characters
                abs_path = os.path.abspath(video_file).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")
        
        # Use FFmpeg concat demuxer
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            '-y',
            output_path
        ]
        
        print(f"   🔗 Concatenating {len(video_files)} segments...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # If copy fails, try re-encoding
            print(f"   ⚠️  Copy mode failed, re-encoding...")
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-y',
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"FFmpeg concat failed: {result.stderr}"
                }
        
        # Cleanup concat file
        if os.path.exists(concat_file):
            os.remove(concat_file)
        
        return {
            "success": True,
            "output_path": output_path
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def trim_video(input_path: str, output_path: str, start: float = None, end: float = None, 
               duration: float = None, action: str = "keep") -> dict:
    """
    Trim video based on start/end/duration
    action: 'keep' = keep segment, 'remove' = remove segment
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        input_stream = ffmpeg.input(input_path)
        
        # Get video duration if end is negative (relative to end)
        if end and end < 0:
            probe = ffmpeg.probe(input_path)
            video_duration = float(probe['format']['duration'])
            end = video_duration + end
        
        if action == "keep":
            # Keep the segment
            if start is not None and end is not None:
                stream = input_stream.trim(start=start, end=end).setpts('PTS-STARTPTS')
            elif start is not None and duration is not None:
                stream = input_stream.trim(start=start, duration=duration).setpts('PTS-STARTPTS')
            elif duration is not None:
                stream = input_stream.trim(duration=duration).setpts('PTS-STARTPTS')
            else:
                stream = input_stream
            
            output = ffmpeg.output(stream, output_path, vcodec='libx264', acodec='aac')
            
        else:  # action == "remove"
            # This is more complex - need to concatenate parts before and after
            probe = ffmpeg.probe(input_path)
            video_duration = float(probe['format']['duration'])
            
            # Create two segments
            os.makedirs(TEMP_DIR, exist_ok=True)
            temp1 = os.path.join(TEMP_DIR, "part1.mp4")
            temp2 = os.path.join(TEMP_DIR, "part2.mp4")
            
            segments = []
            
            # Part 1: Before removal
            if start > 0:
                print(f"   📹 Extracting part 1 (0s to {start}s)...")
                part1 = ffmpeg.input(input_path).trim(start=0, end=start).setpts('PTS-STARTPTS')
                ffmpeg.output(part1, temp1, acodec='aac', vcodec='libx264').run(overwrite_output=True, quiet=True)
                segments.append(temp1)
            
            # Part 2: After removal
            if end < video_duration:
                print(f"   📹 Extracting part 2 ({end}s to end)...")
                part2 = ffmpeg.input(input_path).trim(start=end).setpts('PTS-STARTPTS')
                ffmpeg.output(part2, temp2, acodec='aac', vcodec='libx264').run(overwrite_output=True, quiet=True)
                segments.append(temp2)
            
            if len(segments) == 0:
                return {"success": False, "error": "No valid segments to process"}
            
            # Concatenate using file list method
            result = concat_videos_with_file_list(segments, output_path)
            
            # Cleanup
            for seg in segments:
                if os.path.exists(seg):
                    os.remove(seg)
            
            return result
        
        print(f"\n🔧 Running FFmpeg trim operation...")
        ffmpeg.run(output, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        
        return {
            "success": True,
            "output_path": output_path,
            "message": "Trim operation completed"
        }
        
    except ffmpeg.Error as e:
        error_message = e.stderr.decode('utf-8') if e.stderr else str(e)
        return {"success": False, "error": error_message}
    except Exception as e:
        return {"success": False, "error": str(e)}


def complex_video_edit(input_path: str, output_path: str, edit_config: dict, video_duration: float) -> dict:
    """
    Handle complex video editing operations like cut and move, reverse, loop
    """
    try:
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        edit_type = edit_config.get("type")
        
        if edit_type == "move_segment":
            # Cut segment and move it to a different position
            source_start = float(edit_config.get("source_start", 0))
            source_end = float(edit_config.get("source_end", 10))
            target_position = edit_config.get("target_position", "end")
            offset = float(edit_config.get("offset", 0))
            
            print(f"\n🎬 COMPLEX EDIT DETAILS:")
            print(f"   📍 Source: {source_start}s → {source_end}s")
            print(f"   📍 Target: {target_position}")
            print(f"   📍 Video Duration: {video_duration}s")
            
            temp_segment = os.path.join(TEMP_DIR, "segment.mp4")
            temp_before = os.path.join(TEMP_DIR, "before.mp4")
            temp_after = os.path.join(TEMP_DIR, "after.mp4")
            temp_middle = os.path.join(TEMP_DIR, "middle.mp4")
            
            segments_to_concat = []
            
            # Extract the segment that will be moved
            print(f"\n   📹 Step 1: Extracting segment to move ({source_start}s to {source_end}s)...")
            segment = ffmpeg.input(input_path).trim(start=source_start, end=source_end).setpts('PTS-STARTPTS')
            ffmpeg.output(segment, temp_segment, acodec='aac', vcodec='libx264').run(overwrite_output=True, quiet=True)
            print(f"   ✅ Segment extracted: {os.path.getsize(temp_segment) / (1024*1024):.2f} MB")
            
            if target_position == "end":
                print(f"\n   📹 Step 2: Extracting remaining parts...")
                
                # Part 1: Before the cut segment (if exists)
                if source_start > 0:
                    print(f"      → Before segment: 0s to {source_start}s")
                    before = ffmpeg.input(input_path).trim(start=0, end=source_start).setpts('PTS-STARTPTS')
                    ffmpeg.output(before, temp_before, acodec='aac', vcodec='libx264').run(overwrite_output=True, quiet=True)
                    segments_to_concat.append(temp_before)
                    print(f"      ✅ Before part: {os.path.getsize(temp_before) / (1024*1024):.2f} MB")
                
                # Part 2: After the cut segment (if exists)
                if source_end < video_duration:
                    print(f"      → After segment: {source_end}s to {video_duration}s")
                    after = ffmpeg.input(input_path).trim(start=source_end).setpts('PTS-STARTPTS')
                    ffmpeg.output(after, temp_after, acodec='aac', vcodec='libx264').run(overwrite_output=True, quiet=True)
                    segments_to_concat.append(temp_after)
                    print(f"      ✅ After part: {os.path.getsize(temp_after) / (1024*1024):.2f} MB")
                
                # Add moved segment at the end
                segments_to_concat.append(temp_segment)
                
                print(f"\n   🔗 Final order: ", end="")
                if source_start > 0:
                    print(f"[0→{source_start}s]", end="")
                if source_end < video_duration:
                    print(f" + [{source_end}s→end]", end="")
                print(f" + [{source_start}→{source_end}s]")
                
            elif target_position == "beginning":
                print(f"\n   📹 Step 2: Extracting remaining parts...")
                
                # Moved segment goes first
                segments_to_concat.append(temp_segment)
                
                # Part 1: Before the cut segment
                if source_start > 0:
                    print(f"      → Before segment: 0s to {source_start}s")
                    before = ffmpeg.input(input_path).trim(start=0, end=source_start).setpts('PTS-STARTPTS')
                    ffmpeg.output(before, temp_before, acodec='aac', vcodec='libx264').run(overwrite_output=True, quiet=True)
                    segments_to_concat.append(temp_before)
                
                # Part 2: After the cut segment
                if source_end < video_duration:
                    print(f"      → After segment: {source_end}s to {video_duration}s")
                    after = ffmpeg.input(input_path).trim(start=source_end).setpts('PTS-STARTPTS')
                    ffmpeg.output(after, temp_after, acodec='aac', vcodec='libx264').run(overwrite_output=True, quiet=True)
                    segments_to_concat.append(temp_after)
                
                print(f"\n   🔗 Final order: [{source_start}→{source_end}s]", end="")
                if source_start > 0:
                    print(f" + [0→{source_start}s]", end="")
                if source_end < video_duration:
                    print(f" + [{source_end}s→end]", end="")
                print()
                
            elif target_position == "before_end":
                # Calculate where to insert (offset seconds before the end)
                insert_point = video_duration - offset
                
                print(f"      → Insert point: {insert_point}s (before last {offset}s)")
                
                # Part 1: Everything from start to insert point (excluding source segment)
                if source_start < insert_point:
                    if source_start > 0:
                        # Before source segment
                        before = ffmpeg.input(input_path).trim(start=0, end=source_start).setpts('PTS-STARTPTS')
                        ffmpeg.output(before, temp_before, acodec='aac', vcodec='libx264').run(overwrite_output=True, quiet=True)
                        segments_to_concat.append(temp_before)
                    
                    # Between source segment and insert point
                    if source_end < insert_point:
                        middle = ffmpeg.input(input_path).trim(start=source_end, end=insert_point).setpts('PTS-STARTPTS')
                        ffmpeg.output(middle, temp_middle, acodec='aac', vcodec='libx264').run(overwrite_output=True, quiet=True)
                        segments_to_concat.append(temp_middle)
                
                # Add the moved segment
                segments_to_concat.append(temp_segment)
                
                # Part 2: Everything from insert point to end
                if insert_point < video_duration:
                    after = ffmpeg.input(input_path).trim(start=insert_point).setpts('PTS-STARTPTS')
                    ffmpeg.output(after, temp_after, acodec='aac', vcodec='libx264').run(overwrite_output=True, quiet=True)
                    segments_to_concat.append(temp_after)
            
            if len(segments_to_concat) == 0:
                return {"success": False, "error": "No segments to concatenate"}
            
            print(f"\n   🔗 Concatenating {len(segments_to_concat)} segments...")
            # Concatenate all segments
            result = concat_videos_with_file_list(segments_to_concat, output_path)
            
            # Cleanup temp files
            for temp_file in [temp_segment, temp_before, temp_after, temp_middle]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            return result
            
        elif edit_type == "loop":
            # Loop video N times
            count = edit_config.get("count", 2)
            
            print(f"   🔁 Creating {count} loops...")
            
            # Create temp copies
            temp_copies = []
            for i in range(count):
                temp_copy = os.path.join(TEMP_DIR, f"loop_{i}.mp4")
                # Just copy the original file
                shutil.copy2(input_path, temp_copy)
                temp_copies.append(temp_copy)
            
            # Concatenate
            result = concat_videos_with_file_list(temp_copies, output_path)
            
            # Cleanup
            for temp_file in temp_copies:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            return result
            
        elif edit_type == "remove_middle":
            # Remove X seconds from middle
            start = edit_config.get("start", 10)
            duration = edit_config.get("duration", 10)
            end = start + duration
            
            print(f"   ✂️  Removing {duration}s from position {start}s...")
            return trim_video(input_path, output_path, start=start, end=end, action="remove")
            
        else:
            return {"success": False, "error": f"Unknown edit type: {edit_type}"}
        
    except Exception as e:
        import traceback
        print(f"\n❌ Exception in complex_video_edit:")
        print(traceback.format_exc())
        return {"success": False, "error": str(e)}


def apply_ffmpeg_filter(input_path: str, output_path: str, filter_chain: str, 
                       additional_params: dict = None, audio_file: str = None) -> dict:
    """Apply FFmpeg filter to video or image with optional audio handling"""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        input_stream = ffmpeg.input(input_path)
        
        if audio_file and os.path.exists(audio_file):
            print(f"   🎵 Adding audio from: {os.path.basename(audio_file)}")
            audio_input = ffmpeg.input(audio_file)
            
            if filter_chain:
                video = input_stream.video.filter_(filter_chain) if filter_chain else input_stream.video
            else:
                video = input_stream.video
            
            stream = ffmpeg.output(
                video, 
                audio_input.audio,
                output_path,
                vcodec='libx264',
                acodec='aac',
                shortest=None,
                **(additional_params or {})
            )
        else:
            output_params = additional_params or {}
            
            if filter_chain:
                output_params['vf'] = filter_chain
            
            stream = ffmpeg.output(input_stream, output_path, **output_params)
        
        print(f"\n🔧 Running FFmpeg...")
        if filter_chain:
            print(f"   Filter: {filter_chain}")
        
        ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
        
        return {
            "success": True,
            "output_path": output_path,
            "message": "Media processed successfully"
        }
        
    except ffmpeg.Error as e:
        error_message = e.stderr.decode('utf-8') if e.stderr else str(e)
        return {
            "success": False,
            "error": error_message
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_media_info(file_path: str) -> dict:
    """Get media file information"""
    try:
        probe = ffmpeg.probe(file_path)
        video_info = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
        audio_info = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
        
        return {
            "success": True,
            "duration": float(probe['format'].get('duration', 0)),
            "size": int(probe['format'].get('size', 0)),
            "format": probe['format'].get('format_name', 'unknown'),
            "width": video_info.get('width') if video_info else None,
            "height": video_info.get('height') if video_info else None,
            "has_audio": audio_info is not None,
            "audio_codec": audio_info.get('codec_name') if audio_info else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def list_media_files():
    """List all video and image files in current directory"""
    video_exts = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}
    image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}
    
    files = []
    for file in os.listdir('.'):
        if Path(file).suffix.lower() in video_exts or Path(file).suffix.lower() in image_exts:
            files.append(file)
    
    return sorted(files)


def list_audio_files():
    """List all audio files in current directory"""
    audio_exts = {".mp3", ".wav", ".aac", ".m4a", ".ogg", ".flac"}
    
    files = []
    for file in os.listdir('.'):
        if Path(file).suffix.lower() in audio_exts:
            files.append(file)
    
    return sorted(files)


def main():
    """Interactive main interface"""
    
    print("=" * 70)
    print("🎬 AI-Powered FFmpeg Editor - Pro Edition")
    print("   Advanced Trimming, Cutting & Rearranging + Trending Music")
    print("=" * 70)
    
    media_files = list_media_files()
    
    if not media_files:
        print("\n❌ No video or image files found in current directory!")
        print("\nSupported formats:")
        print("  Videos: .mp4, .avi, .mov, .mkv, .webm, .flv")
        print("  Images: .jpg, .jpeg, .png, .gif, .bmp, .tiff")
        return
    
    print(f"\n📂 Found {len(media_files)} media file(s) in current directory:\n")
    for idx, file in enumerate(media_files, 1):
        size = os.path.getsize(file) / (1024 * 1024)
        print(f"  {idx}. {file} ({size:.2f} MB)")
    
    print("\n" + "=" * 70)
    while True:
        try:
            selection = input("Enter file number (or filename): ").strip()
            
            if selection.isdigit():
                idx = int(selection) - 1
                if 0 <= idx < len(media_files):
                    input_file = media_files[idx]
                    break
                else:
                    print(f"❌ Invalid number. Please enter 1-{len(media_files)}")
            elif selection in media_files:
                input_file = selection
                break
            else:
                print(f"❌ File '{selection}' not found. Try again.")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            return
    
    if not Path(input_file).exists():
        print(f"❌ Error: File '{input_file}' not found")
        return
    
    ext = Path(input_file).suffix.lower()
    video_exts = [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"]
    image_exts = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"]
    
    if ext in video_exts:
        media_type = "video"
    elif ext in image_exts:
        media_type = "image"
    else:
        print(f"❌ Error: Unsupported file format '{ext}'")
        return
    
    print("\n" + "=" * 70)
    print(f"📂 Selected File: {input_file}")
    print(f"🎭 Media Type: {media_type}")
    
    info = get_media_info(input_file)
    video_duration = 0
    video_width = 0
    video_height = 0
    
    if info.get("success"):
        if info['width']:
            video_width = info['width']
            video_height = info['height']
            print(f"📊 Resolution: {video_width}x{video_height}")
        if info.get('duration'):
            video_duration = info['duration']
            print(f"⏱️  Duration: {video_duration:.2f}s")
        print(f"💾 Size: {info['size'] / (1024*1024):.2f} MB")
        if info.get('has_audio'):
            print(f"🎵 Audio: Yes ({info.get('audio_codec', 'unknown')})")
        else:
            print(f"🔇 Audio: No")
    
    print("\n" + "=" * 70)
    print("✨ What would you like to do with this file?")
    print("\n📝 VISUAL EFFECTS:")
    print("  • make it black and white    • add blur effect")
    print("  • increase brightness         • add sepia tone")
    print("\n🔄 ROTATION & FLIP:")
    print("  • rotate 90 degrees clockwise • flip horizontal")
    print("\n⏱️  SPEED & TIME:")
    print("  • speed up 2x                 • slow down 2x")
    print("\n✂️  TRIMMING & CUTTING:")
    print("  • trim first 10 seconds       • trim last 5 seconds")
    print("  • keep only first 20 seconds  • cut from 10 to 30 seconds")
    print("  • remove middle 10 seconds")
    print("\n🎬 ADVANCED CUTTING & REARRANGING:")
    print("  • cut first 2 seconds and add to end")
    print("  • cut first 5 seconds and add to last 2 seconds")
    print("  • cut middle 10 seconds (from 20s) and add to end")
    print("  • reverse the video           • loop 3 times")
    print("\n📱 PORTRAIT MODE (Instagram Reels/TikTok/Shorts):")
    print("  • make it portrait            • convert to portrait mode")
    print("  • crop for instagram reel     • crop for tiktok")
    print("  • crop for youtube shorts     • mobile view")
    print("\n✂️  CROPPING & RESIZING:")
    print("  • crop to square (1:1)        • crop to 16:9")
    print("  • resize to 1080p             • resize to 720p")
    print("\n🎵 AUDIO OPERATIONS:")
    print("  • remove audio                • add music")
    print("  • add trending music          • increase volume")
    print("\n🌟 ADVANCED:")
    print("  • stabilize video             • denoise video")
    print("\n" + "=" * 70)
    
    try:
        prompt = input("Your edit request: ").strip()
        
        if not prompt:
            print("❌ No prompt provided. Exiting.")
            return
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        return
    
    print("\n" + "=" * 70)
    print(f"📝 Your Request: {prompt}")
    print("🤖 Asking Gemini to interpret your request...")
    
    ai_result = parse_prompt_to_ffmpeg(prompt, media_type, video_duration, video_width, video_height)
    
    if not ai_result.get("success"):
        print(f"❌ AI parsing failed: {ai_result.get('error')}")
        if ai_result.get('raw_response'):
            print(f"\nRaw AI Response:\n{ai_result['raw_response']}")
        return
    
    print(f"✅ AI Interpretation: {ai_result['explanation']}")
    
    output_dir = OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    
    output_filename = Path(input_file).stem + "_edited" + Path(input_file).suffix
    output_path = os.path.join(output_dir, output_filename)
    
    # Handle different operation types
    result = None
    
    if ai_result.get('trim_operation'):
        # Simple trim operation
        trim_op = ai_result['trim_operation']
        print(f"✂️  Trim Operation: {trim_op}")
        result = trim_video(
            input_path=input_file,
            output_path=output_path,
            start=trim_op.get('start'),
            end=trim_op.get('end'),
            duration=trim_op.get('duration'),
            action=trim_op.get('action', 'keep')
        )
        
    elif ai_result.get('complex_edit'):
        # Complex editing operation
        complex_op = ai_result['complex_edit']
        print(f"🎬 Complex Edit: {complex_op.get('type')}")
        result = complex_video_edit(
            input_path=input_file,
            output_path=output_path,
            edit_config=complex_op,
            video_duration=video_duration
        )
        
    else:
        # Standard filter operation
        if ai_result['filter_chain']:
            print(f"🔧 FFmpeg Filter: {ai_result['filter_chain']}")
        if ai_result.get('additional_params'):
            print(f"⚙️  Additional Params: {ai_result['additional_params']}")
        
        # Handle audio if needed
        audio_file = None
        if ai_result.get('requires_audio_input'):
            if ai_result.get('use_trending_song'):
                display_trending_songs()
                
                song_selection = input("\nSelect a song (1-9) or press Enter for local file: ").strip()
                
                if song_selection.isdigit():
                    idx = int(song_selection) - 1
                    if 0 <= idx < len(TRENDING_SONGS):
                        selected_song = TRENDING_SONGS[idx]
                        print(f"\n🎵 Selected: {selected_song['title']} by {selected_song['artist']}")
                        audio_file = download_song(selected_song)
            
            if not audio_file:
                audio_files = list_audio_files()
                
                if ai_result.get('audio_file'):
                    suggested_file = ai_result['audio_file']
                    if os.path.exists(suggested_file):
                        audio_file = suggested_file
                        print(f"🎵 Using audio file: {audio_file}")
                
                if not audio_file and audio_files:
                    print(f"\n🎵 Available local audio files:")
                    for idx, file in enumerate(audio_files, 1):
                        print(f"  {idx}. {file}")
                    
                    audio_selection = input("\nEnter audio file number or filename (or press Enter to skip): ").strip()
                    
                    if audio_selection:
                        if audio_selection.isdigit():
                            idx = int(audio_selection) - 1
                            if 0 <= idx < len(audio_files):
                                audio_file = audio_files[idx]
                        elif audio_selection in audio_files:
                            audio_file = audio_selection
                        elif os.path.exists(audio_selection):
                            audio_file = audio_selection
        
        print(f"\n⚙️  Processing media...")
        result = apply_ffmpeg_filter(
            input_path=input_file,
            output_path=output_path,
            filter_chain=ai_result['filter_chain'],
            additional_params=ai_result.get('additional_params', {}),
            audio_file=audio_file
        )
    
    if result and result.get("success"):
        print("\n" + "=" * 70)
        print(f"✅ Success! Output saved to: {output_path}")
        
        output_info = get_media_info(output_path)
        if output_info.get("success"):
            if output_info['width']:
                print(f"📊 Output Resolution: {output_info['width']}x{output_info['height']}")
            if output_info.get('duration'):
                print(f"⏱️  Duration: {output_info['duration']:.2f}s")
            print(f"💾 Output Size: {output_info['size'] / (1024*1024):.2f} MB")
            if output_info.get('has_audio'):
                print(f"🎵 Audio: Yes")
        print("=" * 70)
        
        print("\n" + "=" * 70)
        another = input("Edit another file? (y/n): ").strip().lower()
        if another == 'y':
            print("\n" * 2)
            main()
        else:
            print("\n👋 Thank you for using AI FFmpeg Editor Pro!")
            print("=" * 70)
    else:
        print(f"\n❌ Operation failed: {result.get('error') if result else 'Unknown error'}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")