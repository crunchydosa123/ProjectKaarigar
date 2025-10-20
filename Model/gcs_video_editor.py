# gcs_video_editor.py
"""
AI-Powered FFmpeg Video/Image Editor - Google Cloud Storage Edition
All operations happen directly on GCS without creating temporary local folders.
Edits are applied sequentially to the same video.

Just run: python gcs_video_editor.py
"""

import os
import json
import io
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
import ffmpeg
from google import genai
from google.cloud import storage
import requests
from urllib.parse import urlparse

# Configuration
GOOGLE_API_KEY = "AIzaSyDiUMs4sIAdOk09006hS7DcY79DZh53_M4"
BUCKET_NAME = "all_in_one_bucket"
MUSIC_DIR = "music_library"

# Initialize clients
client = genai.Client(api_key=GOOGLE_API_KEY)
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

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


class GCSVideoEditor:
    """Video editor that works entirely with Google Cloud Storage"""
    
    def __init__(self):
        self.current_video_blob = None
        self.current_video_info = None
        self.edit_history = []
        
    def download_video_to_memory(self, blob_name: str) -> io.BytesIO:
        """Download video from GCS to memory"""
        try:
            print(f"📥 Downloading video from GCS: {blob_name}")
            blob = bucket.blob(blob_name)
            video_bytes = blob.download_as_bytes()
            print(f"✅ Downloaded {len(video_bytes) / (1024*1024):.2f} MB")
            return io.BytesIO(video_bytes)
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def download_video_from_url(self, url: str) -> io.BytesIO:
        """Download video from URL to memory"""
        try:
            print(f"📥 Downloading video from URL...")
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            video_bytes = io.BytesIO()
            total_size = 0
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    video_bytes.write(chunk)
                    total_size += len(chunk)
            
            print(f"✅ Downloaded {total_size / (1024*1024):.2f} MB")
            video_bytes.seek(0)
            return video_bytes
        except Exception as e:
            print(f"❌ Download from URL failed: {e}")
            return None
    
    def upload_video_from_memory(self, blob_name: str, video_stream: io.BytesIO) -> str:
        """Upload video from memory to GCS and return signed URL"""
        try:
            print(f"📤 Uploading video to GCS: {blob_name}")
            blob = bucket.blob(blob_name)
            video_stream.seek(0)
            blob.upload_from_file(video_stream, content_type='video/mp4')
            
            # Generate signed URL (valid for 7 days)
            from datetime import datetime, timedelta
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.utcnow() + timedelta(days=7),
                method="GET"
            )
            
            print(f"✅ Uploaded successfully")
            print(f"🔗 Download URL: {url}")
            return url
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return None
    
    def get_video_info_from_memory(self, video_stream: io.BytesIO) -> Dict[str, Any]:
        """Get video information from memory stream"""
        try:
            # Upload to GCS temporarily for probing
            temp_blob_name = f"temp/probe_{os.urandom(8).hex()}.mp4"
            video_stream.seek(0)
            
            # Upload to GCS
            blob = bucket.blob(temp_blob_name)
            blob.upload_from_file(video_stream, content_type='video/mp4')
            
            # Create a unique temp file name
            temp_file_path = os.path.join(tempfile.gettempdir(), f"probe_{os.urandom(8).hex()}.mp4")
            
            try:
                # Download from GCS
                blob.download_to_filename(temp_file_path)
                
                probe = ffmpeg.probe(temp_file_path)
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
            finally:
                # Clean up temp file and GCS blob
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                except:
                    pass
                try:
                    blob.delete()
                except:
                    pass
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def process_video_in_memory(self, input_stream: io.BytesIO, filter_chain: str = "", 
                               additional_params: Dict = None, audio_file: str = None) -> io.BytesIO:
        """Process video using GCS for temporary storage"""
        try:
            # Upload input to GCS temporarily
            input_blob_name = f"temp/input_{os.urandom(8).hex()}.mp4"
            output_blob_name = f"temp/output_{os.urandom(8).hex()}.mp4"
            
            input_stream.seek(0)
            input_blob = bucket.blob(input_blob_name)
            input_blob.upload_from_file(input_stream, content_type='video/mp4')
            
            # Create unique temp file names
            input_temp_path = os.path.join(tempfile.gettempdir(), f"input_{os.urandom(8).hex()}.mp4")
            output_temp_path = os.path.join(tempfile.gettempdir(), f"output_{os.urandom(8).hex()}.mp4")
            
            try:
                # Download from GCS
                input_blob.download_to_filename(input_temp_path)
                
                # Build FFmpeg command
                input_stream_ffmpeg = ffmpeg.input(input_temp_path)
                
                if audio_file and os.path.exists(audio_file):
                    print(f"   🎵 Adding audio from: {os.path.basename(audio_file)}")
                    audio_input = ffmpeg.input(audio_file)
                    
                    if filter_chain:
                        video = input_stream_ffmpeg.video.filter_(filter_chain)
                    else:
                        video = input_stream_ffmpeg.video
                    
                    stream = ffmpeg.output(
                        video, 
                        audio_input.audio,
                        output_temp_path,
                        vcodec='libx264',
                        acodec='aac',
                        shortest=None,
                        **(additional_params or {})
                    )
                else:
                    output_params = additional_params or {}
                    if filter_chain:
                        output_params['vf'] = filter_chain
                    
                    stream = ffmpeg.output(input_stream_ffmpeg, output_temp_path, **output_params)
                
                # Run FFmpeg
                print(f"🔧 Processing video...")
                if filter_chain:
                    print(f"   Filter: {filter_chain}")
                
                ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
                
                # Upload output to GCS
                output_blob = bucket.blob(output_blob_name)
                output_blob.upload_from_filename(output_temp_path, content_type='video/mp4')
                
                # Download back to memory
                output_stream = io.BytesIO()
                output_blob.download_to_file(output_stream)
                
                return output_stream
                
            finally:
                # Clean up temp files and GCS blobs
                try:
                    if os.path.exists(input_temp_path):
                        os.remove(input_temp_path)
                except:
                    pass
                try:
                    if os.path.exists(output_temp_path):
                        os.remove(output_temp_path)
                except:
                    pass
                try:
                    input_blob.delete()
                except:
                    pass
                try:
                    output_blob.delete()
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            return None
    
    def trim_video_in_memory(self, input_stream: io.BytesIO, start: float = None, 
                           end: float = None, duration: float = None, action: str = "keep") -> io.BytesIO:
        """Trim video using GCS for temporary storage"""
        try:
            # Upload input to GCS temporarily
            input_blob_name = f"temp/trim_input_{os.urandom(8).hex()}.mp4"
            output_blob_name = f"temp/trim_output_{os.urandom(8).hex()}.mp4"
            
            input_stream.seek(0)
            input_blob = bucket.blob(input_blob_name)
            input_blob.upload_from_file(input_stream, content_type='video/mp4')
            
            # Create unique temp file names
            input_temp_path = os.path.join(tempfile.gettempdir(), f"trim_input_{os.urandom(8).hex()}.mp4")
            output_temp_path = os.path.join(tempfile.gettempdir(), f"trim_output_{os.urandom(8).hex()}.mp4")
            
            try:
                # Download from GCS
                input_blob.download_to_filename(input_temp_path)
                
                input_stream_ffmpeg = ffmpeg.input(input_temp_path)
                
                if action == "keep":
                    # Keep the segment
                    if start is not None and end is not None:
                        stream = input_stream_ffmpeg.trim(start=start, end=end).setpts('PTS-STARTPTS')
                    elif start is not None and duration is not None:
                        stream = input_stream_ffmpeg.trim(start=start, duration=duration).setpts('PTS-STARTPTS')
                    elif duration is not None:
                        stream = input_stream_ffmpeg.trim(duration=duration).setpts('PTS-STARTPTS')
                    else:
                        stream = input_stream_ffmpeg
                    
                    output = ffmpeg.output(stream, output_temp_path, vcodec='libx264', acodec='aac')
                    
                else:  # action == "remove"
                    # This is more complex - need to concatenate parts before and after
                    probe = ffmpeg.probe(input_temp_path)
                    video_duration = float(probe['format']['duration'])
                        
                    # Get video duration if end is negative (relative to end)
                    if end and end < 0:
                        end = video_duration + end
                    
                    # Create segments
                    segments = []
                    
                    # Part 1: Before removal
                    if start > 0:
                        temp1_path = os.path.join(tempfile.gettempdir(), f"part1_{os.urandom(8).hex()}.mp4")
                        part1 = ffmpeg.input(input_temp_path).trim(start=0, end=start).setpts('PTS-STARTPTS')
                        ffmpeg.output(part1, temp1_path, acodec='aac', vcodec='libx264').run(overwrite_output=True, quiet=True)
                        segments.append(temp1_path)
                    
                    # Part 2: After removal
                    if end < video_duration:
                        temp2_path = os.path.join(tempfile.gettempdir(), f"part2_{os.urandom(8).hex()}.mp4")
                        part2 = ffmpeg.input(input_temp_path).trim(start=end).setpts('PTS-STARTPTS')
                        ffmpeg.output(part2, temp2_path, acodec='aac', vcodec='libx264').run(overwrite_output=True, quiet=True)
                        segments.append(temp2_path)
                    
                    if len(segments) == 0:
                        return None
                    
                    # Concatenate segments
                    concat_file_path = os.path.join(tempfile.gettempdir(), f"concat_{os.urandom(8).hex()}.txt")
                    with open(concat_file_path, 'w') as concat_file:
                        for seg in segments:
                            concat_file.write(f"file '{os.path.abspath(seg)}'\n")
                    
                    # Use FFmpeg concat demuxer
                    cmd = [
                        'ffmpeg',
                        '-f', 'concat',
                        '-safe', '0',
                        '-i', concat_file_path,
                        '-c', 'copy',
                        '-y',
                        output_temp_path
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    # Cleanup segments and concat file
                    try:
                        os.remove(concat_file_path)
                    except:
                        pass
                    for seg in segments:
                        try:
                            os.remove(seg)
                        except:
                            pass
                    
                    if result.returncode != 0:
                        return None
                
                # Run FFmpeg for keep action
                print(f"🔧 Running trim operation...")
                ffmpeg.run(output, overwrite_output=True, capture_stdout=True, capture_stderr=True)
                
                # Upload output to GCS
                output_blob = bucket.blob(output_blob_name)
                output_blob.upload_from_filename(output_temp_path, content_type='video/mp4')
                
                # Download back to memory
                output_stream = io.BytesIO()
                output_blob.download_to_file(output_stream)
                
                return output_stream
                
            finally:
                # Clean up temp files and GCS blobs
                try:
                    if os.path.exists(input_temp_path):
                        os.remove(input_temp_path)
                except:
                    pass
                try:
                    if os.path.exists(output_temp_path):
                        os.remove(output_temp_path)
                except:
                    pass
                try:
                    input_blob.delete()
                except:
                    pass
                try:
                    output_blob.delete()
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Trim operation failed: {e}")
            return None
    
    def complex_video_edit_in_memory(self, input_stream: io.BytesIO, edit_config: Dict, 
                                   video_duration: float) -> io.BytesIO:
        """Handle complex video editing operations in memory"""
        try:
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
                
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as input_temp:
                    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as output_temp:
                        # Write input to temp file
                        input_stream.seek(0)
                        input_temp.write(input_stream.read())
                        input_temp.flush()
                        
                        # Extract the segment that will be moved
                        temp_segment = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                        print(f"\n   📹 Step 1: Extracting segment to move ({source_start}s to {source_end}s)...")
                        segment = ffmpeg.input(input_temp.name).trim(start=source_start, end=source_end).setpts('PTS-STARTPTS')
                        ffmpeg.output(segment, temp_segment.name, acodec='aac', vcodec='libx264').run(overwrite_output=True, quiet=True)
                        
                        segments_to_concat = []
                        
                        if target_position == "end":
                            print(f"\n   📹 Step 2: Extracting remaining parts...")
                            
                            # Part 1: Before the cut segment (if exists)
                            if source_start > 0:
                                temp_before = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                                print(f"      → Before segment: 0s to {source_start}s")
                                before = ffmpeg.input(input_temp.name).trim(start=0, end=source_start).setpts('PTS-STARTPTS')
                                ffmpeg.output(before, temp_before.name, acodec='aac', vcodec='libx264').run(overwrite_output=True, quiet=True)
                                segments_to_concat.append(temp_before.name)
                            
                            # Part 2: After the cut segment (if exists)
                            if source_end < video_duration:
                                temp_after = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                                print(f"      → After segment: {source_end}s to {video_duration}s")
                                after = ffmpeg.input(input_temp.name).trim(start=source_end).setpts('PTS-STARTPTS')
                                ffmpeg.output(after, temp_after.name, acodec='aac', vcodec='libx264').run(overwrite_output=True, quiet=True)
                                segments_to_concat.append(temp_after.name)
                            
                            # Add moved segment at the end
                            segments_to_concat.append(temp_segment.name)
                            
                        elif target_position == "beginning":
                            # Moved segment goes first
                            segments_to_concat.append(temp_segment.name)
                            
                            # Part 1: Before the cut segment
                            if source_start > 0:
                                temp_before = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                                before = ffmpeg.input(input_temp.name).trim(start=0, end=source_start).setpts('PTS-STARTPTS')
                                ffmpeg.output(before, temp_before.name, acodec='aac', vcodec='libx264').run(overwrite_output=True, quiet=True)
                                segments_to_concat.append(temp_before.name)
                            
                            # Part 2: After the cut segment
                            if source_end < video_duration:
                                temp_after = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                                after = ffmpeg.input(input_temp.name).trim(start=source_end).setpts('PTS-STARTPTS')
                                ffmpeg.output(after, temp_after.name, acodec='aac', vcodec='libx264').run(overwrite_output=True, quiet=True)
                                segments_to_concat.append(temp_after.name)
                        
                        if len(segments_to_concat) == 0:
                            return None
                        
                        # Concatenate all segments
                        concat_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
                        for seg in segments_to_concat:
                            concat_file.write(f"file '{os.path.abspath(seg)}'\n")
                        concat_file.close()
                        
                        print(f"\n   🔗 Concatenating {len(segments_to_concat)} segments...")
                        
                        # Use FFmpeg concat demuxer
                        cmd = [
                            'ffmpeg',
                            '-f', 'concat',
                            '-safe', '0',
                            '-i', concat_file.name,
                            '-c', 'copy',
                            '-y',
                            output_temp.name
                        ]
                        
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if result.returncode != 0:
                            # If copy fails, try re-encoding
                            cmd = [
                                'ffmpeg',
                                '-f', 'concat',
                                '-safe', '0',
                                '-i', concat_file.name,
                                '-c:v', 'libx264',
                                '-c:a', 'aac',
                                '-y',
                                output_temp.name
                            ]
                            result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        # Cleanup temp files
                        os.unlink(concat_file.name)
                        for seg in segments_to_concat:
                            os.unlink(seg)
                        os.unlink(temp_segment.name)
                        os.unlink(input_temp.name)
                        
                        if result.returncode != 0:
                            return None
                        
                        # Read output back to memory
                        with open(output_temp.name, 'rb') as f:
                            output_stream = io.BytesIO(f.read())
                        
                        os.unlink(output_temp.name)
                        
                        return output_stream
            
            elif edit_type == "loop":
                # Loop video N times
                count = edit_config.get("count", 2)
                print(f"   🔁 Creating {count} loops...")
                
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as input_temp:
                    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as output_temp:
                        # Write input to temp file
                        input_stream.seek(0)
                        input_temp.write(input_stream.read())
                        input_temp.flush()
                        
                        # Create temp copies
                        temp_copies = []
                        for i in range(count):
                            temp_copy = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                            shutil.copy2(input_temp.name, temp_copy.name)
                            temp_copies.append(temp_copy.name)
                        
                        # Create concat file
                        concat_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
                        for copy in temp_copies:
                            concat_file.write(f"file '{os.path.abspath(copy)}'\n")
                        concat_file.close()
                        
                        # Concatenate
                        cmd = [
                            'ffmpeg',
                            '-f', 'concat',
                            '-safe', '0',
                            '-i', concat_file.name,
                            '-c', 'copy',
                            '-y',
                            output_temp.name
                        ]
                        
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        
                        # Cleanup
                        os.unlink(concat_file.name)
                        for copy in temp_copies:
                            os.unlink(copy)
                        os.unlink(input_temp.name)
                        
                        if result.returncode != 0:
                            return None
                        
                        # Read output back to memory
                        with open(output_temp.name, 'rb') as f:
                            output_stream = io.BytesIO(f.read())
                        
                        os.unlink(output_temp.name)
                        
                        return output_stream
            
            elif edit_type == "remove_middle":
                # Remove X seconds from middle
                start = edit_config.get("start", 10)
                duration = edit_config.get("duration", 10)
                end = start + duration
                
                print(f"   ✂️  Removing {duration}s from position {start}s...")
                return self.trim_video_in_memory(input_stream, start=start, end=end, action="remove")
            
            else:
                print(f"❌ Unknown edit type: {edit_type}")
                return None
                
        except Exception as e:
            print(f"❌ Complex edit failed: {e}")
            return None
    
    def download_song(self, song: dict) -> str:
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
    
    def display_trending_songs(self):
        """Display trending songs library"""
        print("\n🎵 TRENDING SONGS LIBRARY:")
        print("=" * 70)
        for idx, song in enumerate(TRENDING_SONGS, 1):
            print(f"  {idx}. {song['title']} - {song['artist']} ({song['duration']}s)")
        print("=" * 70)
    
    def parse_prompt_to_ffmpeg(self, user_prompt: str, media_type: str, video_duration: float = 0, 
                              video_width: int = 0, video_height: int = 0) -> dict:
        """Converts natural language prompt to FFmpeg command parameters using Gemini"""
        
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
    
    def list_local_videos(self) -> list:
        """List all video files in current directory"""
        video_exts = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}
        files = []
        for file in os.listdir('.'):
            if Path(file).suffix.lower() in video_exts:
                files.append(file)
        return sorted(files)
    
    def list_edited_videos(self) -> list:
        """List all edited videos from GCS with their URLs"""
        try:
            blobs = bucket.list_blobs(prefix="edited_videos/")
            edited_videos = []
            
            for blob in blobs:
                if blob.name.endswith('.mp4'):
                    # Generate signed URL for each video
                    from datetime import datetime, timedelta
                    url = blob.generate_signed_url(
                        version="v4",
                        expiration=datetime.utcnow() + timedelta(days=7),
                        method="GET"
                    )
                    
                    # Get blob metadata
                    blob.reload()
                    size_mb = blob.size / (1024 * 1024) if blob.size else 0
                    created = blob.time_created.strftime("%Y-%m-%d %H:%M") if blob.time_created else "Unknown"
                    
                    edited_videos.append({
                        'name': blob.name,
                        'filename': blob.name.split('/')[-1],
                        'url': url,
                        'size_mb': size_mb,
                        'created': created
                    })
            
            return sorted(edited_videos, key=lambda x: x['created'], reverse=True)
        except Exception as e:
            print(f"❌ Failed to list edited videos: {e}")
            return []
    
    def apply_edit(self, video_stream: io.BytesIO, edit_request: str) -> io.BytesIO:
        """Apply a single edit to the video stream"""
        # Get current video info
        video_info = self.get_video_info_from_memory(video_stream)
        if not video_info.get("success"):
            print(f"❌ Could not get video info: {video_info.get('error')}")
            return None
        
        video_duration = video_info.get('duration', 0)
        video_width = video_info.get('width', 0)
        video_height = video_info.get('height', 0)
        
        # Parse the edit request
        ai_result = self.parse_prompt_to_ffmpeg(
            edit_request, "video", video_duration, video_width, video_height
        )
        
        if not ai_result.get("success"):
            print(f"❌ AI parsing failed: {ai_result.get('error')}")
            return None
        
        print(f"✅ AI Interpretation: {ai_result['explanation']}")
        
        # Apply the edit based on type
        if ai_result.get('trim_operation'):
            # Simple trim operation
            trim_op = ai_result['trim_operation']
            print(f"✂️  Trim Operation: {trim_op}")
            return self.trim_video_in_memory(
                video_stream,
                start=trim_op.get('start'),
                end=trim_op.get('end'),
                duration=trim_op.get('duration'),
                action=trim_op.get('action', 'keep')
            )
        
        elif ai_result.get('complex_edit'):
            # Complex editing operation
            complex_op = ai_result['complex_edit']
            print(f"🎬 Complex Edit: {complex_op.get('type')}")
            return self.complex_video_edit_in_memory(
                video_stream, complex_op, video_duration
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
                    self.display_trending_songs()
                    
                    song_selection = input("\nSelect a song (1-9) or press Enter for local file: ").strip()
                    
                    if song_selection.isdigit():
                        idx = int(song_selection) - 1
                        if 0 <= idx < len(TRENDING_SONGS):
                            selected_song = TRENDING_SONGS[idx]
                            print(f"\n🎵 Selected: {selected_song['title']} by {selected_song['artist']}")
                            audio_file = self.download_song(selected_song)
                
                if not audio_file:
                    # List local audio files
                    audio_exts = {".mp3", ".wav", ".aac", ".m4a", ".ogg", ".flac"}
                    audio_files = []
                    for file in os.listdir('.'):
                        if Path(file).suffix.lower() in audio_exts:
                            audio_files.append(file)
                    
                    if audio_files:
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
            
            print(f"\n⚙️  Processing video...")
            return self.process_video_in_memory(
                video_stream,
                filter_chain=ai_result['filter_chain'],
                additional_params=ai_result.get('additional_params', {}),
                audio_file=audio_file
            )
    
    def cleanup_temp_objects(self, blob_names: list):
        """Clean up temporary GCS objects"""
        for blob_name in blob_names:
            try:
                blob = bucket.blob(blob_name)
                blob.delete()
                print(f"🗑️  Cleaned up temporary object: {blob_name}")
            except Exception as e:
                print(f"⚠️  Could not clean up {blob_name}: {e}")
    
    def main(self):
        """Interactive main interface with progressive editing"""
        print("=" * 70)
        print("🎬 AI-Powered FFmpeg Editor - Progressive Editing System")
        print("   Edit local videos or continue editing from GCS!")
        print("=" * 70)
        
        while True:
            print("\n" + "=" * 50)
            print("📋 CHOOSE VIDEO SOURCE:")
            print("=" * 50)
            print("1. 📁 Edit local video files")
            print("2. 🔗 Continue editing from GCS (edited videos)")
            print("3. 🚪 Exit")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                self.edit_local_video()
            elif choice == "2":
                self.edit_from_gcs()
            elif choice == "3":
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
    
    def edit_local_video(self):
        """Edit a local video file"""
        # List local videos
        video_files = self.list_local_videos()
        
        if not video_files:
            print("\n❌ No video files found in current directory!")
            print("\nSupported formats:")
            print("  Videos: .mp4, .avi, .mov, .mkv, .webm, .flv")
            return
        
        print(f"\n📂 Found {len(video_files)} video file(s) in current directory:\n")
        for idx, file in enumerate(video_files, 1):
            size = os.path.getsize(file) / (1024 * 1024)
            print(f"  {idx}. {file} ({size:.2f} MB)")
        
        print("\n" + "=" * 70)
        while True:
            try:
                selection = input("Enter file number (or filename): ").strip()
                
                if selection.isdigit():
                    idx = int(selection) - 1
                    if 0 <= idx < len(video_files):
                        selected_video = video_files[idx]
                        break
                    else:
                        print(f"❌ Invalid number. Please enter 1-{len(video_files)}")
                elif selection in video_files:
                    selected_video = selection
                    break
                else:
                    print(f"❌ File '{selection}' not found. Try again.")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                return
        
        # Load local video to memory
        print(f"📥 Loading video: {selected_video}")
        try:
            with open(selected_video, 'rb') as f:
                video_stream = io.BytesIO(f.read())
            print(f"✅ Video loaded: {len(video_stream.getvalue()) / (1024*1024):.2f} MB")
        except Exception as e:
            print(f"❌ Failed to load video: {e}")
            return
        
        self.start_editing_session(video_stream, selected_video)
    
    def edit_from_gcs(self):
        """Continue editing from GCS edited videos"""
        edited_videos = self.list_edited_videos()
        
        if not edited_videos:
            print("\n❌ No edited videos found in GCS!")
            print("💡 Edit a local video first to create edited videos.")
            return
        
        print(f"\n🔗 Found {len(edited_videos)} edited video(s) in GCS:\n")
        for idx, video in enumerate(edited_videos, 1):
            print(f"  {idx}. {video['filename']}")
            print(f"     📅 Created: {video['created']}")
            print(f"     💾 Size: {video['size_mb']:.2f} MB")
            print(f"     🔗 URL: {video['url']}")
            print()
        
        print("=" * 70)
        while True:
            try:
                selection = input("Enter video number to continue editing: ").strip()
                
                if selection.isdigit():
                    idx = int(selection) - 1
                    if 0 <= idx < len(edited_videos):
                        selected_video = edited_videos[idx]
                        break
                    else:
                        print(f"❌ Invalid number. Please enter 1-{len(edited_videos)}")
                else:
                    print("❌ Please enter a valid number.")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                return
        
        # Download video from GCS URL
        print(f"📥 Downloading video: {selected_video['filename']}")
        video_stream = self.download_video_from_url(selected_video['url'])
        
        if not video_stream:
            print("❌ Failed to download video from GCS")
            return
        
        self.start_editing_session(video_stream, selected_video['filename'])
    
    def start_editing_session(self, video_stream: io.BytesIO, video_name: str):
        """Start an editing session with a video"""
        # Get video info
        video_info = self.get_video_info_from_memory(video_stream)
        if video_info.get("success"):
            if video_info['width']:
                print(f"📊 Resolution: {video_info['width']}x{video_info['height']}")
            if video_info.get('duration'):
                print(f"⏱️  Duration: {video_info['duration']:.2f}s")
            print(f"💾 Size: {video_info['size'] / (1024*1024):.2f} MB")
            if video_info.get('has_audio'):
                print(f"🎵 Audio: Yes ({video_info.get('audio_codec', 'unknown')})")
            else:
                print(f"🔇 Audio: No")
        
        # Store current video info
        self.current_video_info = video_info
        
        # Save original video once to edited_videos so users can revert/edit from it later
        try:
            original_blob_name = f"edited_videos/original_{Path(video_name).stem}.mp4"
            original_blob = bucket.blob(original_blob_name)
            if not original_blob.exists():
                print(f"\n💾 Saving original video copy to GCS: {original_blob_name}")
                orig_url = self.upload_video_from_memory(original_blob_name, video_stream)
                if orig_url:
                    print(f"🔗 Original video URL: {orig_url}")
                    self.edit_history.append(f"Original saved: {original_blob_name} - {orig_url}")
            else:
                print(f"\nℹ️  Original already saved: {original_blob_name}")
        except Exception as e:
            print(f"⚠️  Could not save original video: {e}")
        
        print("\n" + "=" * 70)
        print("✨ What would you like to do with this video?")
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
        
        # Main editing loop
        temp_objects = []  # Track temporary objects for cleanup
        
        while True:
            try:
                prompt = input("\nYour edit request (or 'done' to finish, 'save' to save to GCS): ").strip()
                
                if prompt.lower() == 'done':
                    break
                elif prompt.lower() == 'save':
                    # Save current video to GCS
                    save_name = input("Enter name for saved video (or press Enter for auto-generated): ").strip()
                    if not save_name:
                        save_name = f"edited_{Path(video_name).stem}_{len(self.edit_history)}.mp4"
                    
                    if not save_name.startswith("edited_videos/"):
                        save_name = f"edited_videos/{save_name}"
                    
                    saved_url = self.upload_video_from_memory(save_name, video_stream)
                    if saved_url:
                        print(f"✅ Video saved to GCS: {save_name}")
                        self.edit_history.append(f"Saved as: {save_name} - {saved_url}")
                    continue
                elif not prompt:
                    print("❌ No prompt provided.")
                    continue
                
                # Apply the edit
                print(f"\n📝 Applying: {prompt}")
                edited_stream = self.apply_edit(video_stream, prompt)
                
                if edited_stream:
                    video_stream = edited_stream  # Update current video
                    self.edit_history.append(prompt)
                    
                    # Get updated video info
                    updated_info = self.get_video_info_from_memory(video_stream)
                    if updated_info.get("success"):
                        print(f"\n✅ Edit applied successfully!")
                        if updated_info['width']:
                            print(f"📊 New Resolution: {updated_info['width']}x{updated_info['height']}")
                        if updated_info.get('duration'):
                            print(f"⏱️  New Duration: {updated_info['duration']:.2f}s")
                        print(f"💾 New Size: {updated_info['size'] / (1024*1024):.2f} MB")
                        
                        # Automatically save after each edit
                        auto_save_name = f"edited_videos/auto_save_{Path(video_name).stem}_{len(self.edit_history)}.mp4"
                        
                        saved_url = self.upload_video_from_memory(auto_save_name, video_stream)
                        if saved_url:
                            print(f"💾 Auto-saved to GCS: {auto_save_name}")
                            self.edit_history.append(f"Auto-saved: {auto_save_name} - {saved_url}")
                            
                            # Optional: choose which edited video to continue editing
                            print("\n" + "-" * 70)
                            print("🔗 Edited videos in GCS (choose one to continue editing, or press Enter to keep current):")
                            edited_videos = self.list_edited_videos()
                            if edited_videos:
                                for idx, vid in enumerate(edited_videos, 1):
                                    print(f"  {idx}. {vid['filename']}  (📅 {vid['created']}, 💾 {vid['size_mb']:.2f} MB)")
                                    print(f"     URL: {vid['url']}")
                                selection = input("Enter number to switch, or press Enter to keep current: ").strip()
                                if selection.isdigit():
                                    sel_idx = int(selection) - 1
                                    if 0 <= sel_idx < len(edited_videos):
                                        chosen = edited_videos[sel_idx]
                                        print(f"\n📥 Loading selected edited video: {chosen['filename']}")
                                        new_stream = self.download_video_from_url(chosen['url'])
                                        if new_stream:
                                            video_stream = new_stream
                                            video_name = chosen['filename']
                                            print("✅ Switched to selected edited video.")
                                        else:
                                            print("❌ Failed to load selected video; continuing with current video.")
                            else:
                                print("(No edited videos found yet; continuing with current video.)")
                else:
                    print("❌ Edit failed")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
        
        # Final save option
        if video_stream and self.edit_history:
            print("\n" + "=" * 70)
            print("📝 Edit History:")
            for idx, edit in enumerate(self.edit_history, 1):
                print(f"  {idx}. {edit}")
            
            save_final = input("\nSave final edited video to GCS? (y/n): ").strip().lower()
            if save_final == 'y':
                save_name = input("Enter name for final video (or press Enter for auto-generated): ").strip()
                if not save_name:
                    save_name = f"final_edited_{Path(video_name).stem}.mp4"
                
                if not save_name.startswith("edited_videos/"):
                    save_name = f"edited_videos/{save_name}"
                
                saved_url = self.upload_video_from_memory(save_name, video_stream)
                if saved_url:
                    print(f"✅ Final video saved to GCS: {save_name}")
                    print(f"🔗 Download URL: {saved_url}")
                    print(f"\n📋 Video saved! You can download it using the URL above.")
            
            # Show all saved videos
            saved_videos = [edit for edit in self.edit_history if "Auto-saved:" in edit or "Saved as:" in edit]
            if saved_videos:
                print("\n" + "=" * 70)
                print("💾 ALL SAVED VIDEOS:")
                print("=" * 70)
                for idx, video_info in enumerate(saved_videos, 1):
                    print(f"  {idx}. {video_info}")
                print("=" * 70)
        
        # Cleanup any temporary objects
        if temp_objects:
            self.cleanup_temp_objects(temp_objects)
        
        print("\n👋 Thank you for using GCS Video Editor!")


if __name__ == "__main__":
    try:
        editor = GCSVideoEditor()
        editor.main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
