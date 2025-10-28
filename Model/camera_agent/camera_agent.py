#!/usr/bin/env python3
"""
Voice-Controlled Conversational Agent with Camera and Recorder Integration.

Features:
- Analyze single camera frame using Gemini image analysis (with robust JSON parsing).
- Fallback to local OpenCV heuristics if Gemini fails.
- Before taking photo or starting video: show simple lighting/background suggestions,
  let the user fix them and re-check until satisfied.
- Once the user confirms it's fine, announce "photo/video in 5 seconds" (TTS + printed countdown),
  then take photo or start recording. For video, the user says "stop recording" (voice) or types it.
- Analyze recorded audio with Gemini to detect "stop recording" timestamp; trim audio/video at that timestamp with FFmpeg.
- Robust parsing and fallback trimming if Gemini doesn't give usable timestamp.

Enhancements added by assistant:
- If brightness/background problems are significant, ask the user whether they'd like the app to try automatic adjustments.
  If the user accepts, the script will preview adjusted frames and — if accepted — save adjusted photos or record adjusted video (frames are adjusted before writing).
- Live preview windows are shown during pre-check and recording. The preview overlays directional arrows to indicate which side is brighter
  and where the user should move relative to light sources.

Usage:
    python conversational_agent.py [--text-mode] [--no-tts-play] [--output-dir sessions]

Requirements:
- FFmpeg installed (for video processing)
- Set GEMINI_API_KEY environment variable for Gemini (optional; local fallback works)
"""

import os
import sys
import time
import io
import json
import argparse
import threading
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import cv2
import numpy as np

# Optional dependencies
try:
    import sounddevice as sd
    import soundfile as sf
    SOUNDDEVICE_AVAILABLE = True
except Exception:
    SOUNDDEVICE_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except Exception:
    SR_AVAILABLE = False

from gtts import gTTS

# Optional Gemini SDK
try:
    import google.generativeai as genai
    GEMINI_SDK_AVAILABLE = True
except Exception:
    GEMINI_SDK_AVAILABLE = False

# Configure GEMINI
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.5-flash")
if GEMINI_SDK_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
    except Exception:
        # proceed; we'll fallback to local heuristics if any Gemini calls fail
        pass

# ---------- Utilities ----------

def google_tts_bytes(text: str, lang: str = "en") -> bytes:
    tts = gTTS(text=text, lang=lang)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp.read()


def play_audio_file(path: str):
    """Play using ffplay if available; otherwise print path."""
    if not os.path.exists(path):
        print("Audio path not found:", path)
        return
    try:
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path], check=True)
    except Exception:
        print(f"(Playback not available) TTS saved to {path}")


def safe_tts(text: str, out_dir: Path, no_play: bool):
    if not text:
        return
    try:
        b = google_tts_bytes(text)
        p = out_dir / f"tts_{int(time.time())}.mp3"
        with open(p, "wb") as f:
            f.write(b)
        if not no_play:
            play_audio_file(str(p))
        else:
            print(f"(TTS suppressed) Saved to {p}")
    except Exception as e:
        print("TTS error:", e)

# ---------- Parsing helpers ----------

def parse_time_from_text(text: str) -> Optional[float]:
    """Extract seconds from free-form text."""
    if not text:
        return None
    # HH:MM:SS(.ms)
    m = re.search(r'(?:(\d{1,2}):)?(\d{1,2}):(\d{1,2}(?:\.\d+)?)', text)
    if m:
        try:
            h = int(m.group(1)) if m.group(1) else 0
            mm = int(m.group(2))
            ss = float(m.group(3))
            return h*3600 + mm*60 + ss
        except Exception:
            pass
    # MM:SS
    m2 = re.search(r'(\d{1,2}):(\d{1,2}(?:\.\d+)?)', text)
    if m2:
        try:
            mm = int(m2.group(1))
            ss = float(m2.group(2))
            return mm*60 + ss
        except Exception:
            pass
    # plain numbers
    nums = re.findall(r'(-?\d+(?:\.\d+)?)', text)
    for n in nums:
        try:
            val = float(n)
            if 0 <= val <= 24*3600:
                return val
        except Exception:
            continue
    return None

# ---------- Audio analysis with Gemini for stop timestamp ----------

def analyze_audio_for_timestamp(audio_path: str) -> float:
    """
    Use Gemini to find timestamp in the audio where user said 'stop recording'.
    Returns:
      - float timestamp in seconds if found
      - -1.0 if not found or error
    The function is robust: it attempts direct parsing, JSON parse, and uses parse_time_from_text as fallback.
    If Gemini SDK or API key is not available, it returns -1.0 immediately.
    """
    if not os.path.exists(audio_path):
        print("Audio file does not exist for analysis:", audio_path)
        return -1.0

    if not GEMINI_SDK_AVAILABLE or not GEMINI_API_KEY:
        print("Gemini SDK or API key not available; skipping audio analysis.")
        return -1.0

    try:
        client = genai.GenerativeModel(GEMINI_MODEL_NAME)
        uploaded = genai.upload_file(audio_path)
        prompt = (
            "Transcribe the provided audio and return ONLY a timestamp in seconds (a single number) "
            "representing the exact time when the speaker says 'stop recording' or 'recording stop'. "
            "If the phrase is not present, return -1. Do not add extra text."
        )
        # pass prompt + file
        response = client.generate_content([prompt, uploaded])
        resp_text = ""
        if hasattr(response, "text"):
            resp_text = response.text
        else:
            resp_text = str(response)
        resp_text = (resp_text or "").strip()
        # Try JSON parse if possible
        try:
            parsed = json.loads(resp_text)
            # If it's a number or contains a numeric field, try to retrieve
            if isinstance(parsed, (int, float)):
                val = float(parsed)
                return val if val >= 0 else -1.0
            if isinstance(parsed, dict):
                # try common keys
                for k in ("timestamp", "time", "seconds", "stop_timestamp"):
                    if k in parsed:
                        try:
                            v = float(parsed[k])
                            return v if v >= 0 else -1.0
                        except Exception:
                            continue
        except Exception:
            pass
        # Try to parse free-form text to get a number
        ts = parse_time_from_text(resp_text)
        if ts is not None:
            # success
            print(f"Gemini audio analysis returned timestamp {ts} seconds (raw response: {resp_text[:200]})")
            return float(ts)
        # explicit -1 check
        if re.search(r'\b-1\b', resp_text):
            return -1.0
        # nothing found
        print("Could not extract timestamp from Gemini response. Response was:")
        print(resp_text[:500])
        return -1.0
    except Exception as e:
        print("Error communicating with Gemini for audio analysis:", e)
        return -1.0

# ---------- Frame analysis (Gemini + local fallback) ----------

def analyze_frame_locally(image_path: str) -> Dict[str, Any]:
    """Local heuristics producing suggestions and basic metrics."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return {"lighting":"unknown","brightness":None,"contrast":None,"background_issues":[],"suggestions":["Could not read frame."]}
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray) / 255.0)
        contrast = float(np.std(gray) / 128.0)
        # classify brightness
        if brightness < 0.25:
            lighting = "dark"
        elif brightness < 0.45:
            lighting = "dim"
        elif brightness <= 0.75:
            lighting = "good"
        else:
            lighting = "bright"
        # side brightness differences -> possible backlight
        h, w = gray.shape
        thirds = [gray[:, :w//3], gray[:, w//3:2*w//3], gray[:, 2*w//3:]]
        side_means = [np.mean(t) for t in thirds]
        issues = []
        if max(side_means) - min(side_means) > 45:
            issues.append("Strong back or side light (window behind).")
        # clutter detection via edge density
        edges = cv2.Canny(gray, 50, 150)
        edge_density = edges.sum() / (h*w*255.0)
        if edge_density > 0.015:
            issues.append("Background looks cluttered.")
        # suggestions
        suggestions = []
        if lighting in ("dark", "dim"):
            suggestions.append("Add a soft front light (lamp behind camera) or move closer to window (but not behind it).")
        if "Strong back or side light (window behind)." in issues:
            suggestions.append("Turn so the window is in front or to your side (avoid backlighting).")
        if "Background looks cluttered." in issues:
            suggestions.append("Choose a plain wall or tidy a small area behind you.")
        if not suggestions:
            suggestions.append("Looks good — camera at eye level, keep it that way.")
        return {
            "lighting": lighting,
            "brightness": round(brightness, 3),
            "contrast": round(min(max(contrast, 0.0), 1.0), 3),
            "background_issues": issues,
            "suggestions": suggestions
        }
    except Exception as e:
        return {"lighting":"unknown","brightness":None,"contrast":None,"background_issues":[],"suggestions":[f"Error analyzing frame: {e}"]}


def analyze_frame_with_gemini(image_path: str) -> Dict[str, Any]:
    """
    If Gemini SDK available and API key set, ask it to return JSON analysis.
    Otherwise fallback to analyze_frame_locally.
    """
    if GEMINI_SDK_AVAILABLE and GEMINI_API_KEY:
        try:
            client = genai.GenerativeModel(GEMINI_MODEL_NAME)
            uploaded = genai.upload_file(image_path)
            prompt = (
                "Analyze the provided image for webcam-style lighting and background problems. "
                "Return ONLY a JSON object with keys: lighting (one of ['dark','dim','good','bright','overexposed']), "
                "brightness (0..1), contrast (0..1), background_issues (list of short strings), suggestions (list of 1-3 short strings)."
            )
            response = client.generate_content([prompt, uploaded])
            resp_text = response.text if hasattr(response, "text") else str(response)
            # try parse JSON
            try:
                parsed = json.loads(resp_text)
                # normalize keys
                out = {
                    "lighting": parsed.get("lighting", "unknown"),
                    "brightness": parsed.get("brightness"),
                    "contrast": parsed.get("contrast"),
                    "background_issues": parsed.get("background_issues", []),
                    "suggestions": parsed.get("suggestions", [])
                }
                # ensure lists
                out["background_issues"] = out["background_issues"] if isinstance(out["background_issues"], list) else []
                out["suggestions"] = out["suggestions"] if isinstance(out["suggestions"], list) else []
                return out
            except Exception:
                # try to extract JSON blob
                m = re.search(r'\{.*\}', resp_text, flags=re.DOTALL)
                if m:
                    try:
                        parsed = json.loads(m.group(0))
                        return {
                            "lighting": parsed.get("lighting", "unknown"),
                            "brightness": parsed.get("brightness"),
                            "contrast": parsed.get("contrast"),
                            "background_issues": parsed.get("background_issues", []),
                            "suggestions": parsed.get("suggestions", [])
                        }
                    except Exception:
                        pass
            # if anything fails, fallback
            print("Gemini response not parseable; falling back to local analysis.")
            return analyze_frame_locally(image_path)
        except Exception as e:
            print("Gemini image analysis failed:", e)
            return analyze_frame_locally(image_path)
    else:
        return analyze_frame_locally(image_path)

# ---------- New helper functions for in-app lighting adjustments and preview overlays ----------

def apply_gamma_correction(img: np.ndarray, gamma: float) -> np.ndarray:
    """Apply gamma correction to an image."""
    inv_gamma = 1.0 / float(gamma)
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(256)]).astype("uint8")
    return cv2.LUT(img, table)


def apply_clahe_color(img: np.ndarray) -> np.ndarray:
    """Apply CLAHE on the L channel of LAB to improve local contrast."""
    try:
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        final = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        return final
    except Exception:
        return img


def overlay_direction_arrows(frame: np.ndarray) -> Tuple[np.ndarray, int]:
    """Overlay simple arrows pointing to the side that is brighter and return which side (0=left,1=center,2=right).

    If lighting is already balanced (center is brightest and side difference small), the function will *not* draw arrows
    and instead annotate that lighting looks balanced.
    """
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    thirds = [gray[:, :w//3], gray[:, w//3:2*w//3], gray[:, 2*w//3:]]
    side_means = [np.mean(t) for t in thirds]
    best_idx = int(np.argmax(side_means))
    diff = float(max(side_means) - min(side_means))
    mean_brightness = float(np.mean(gray))

    # Decide whether arrows are needed: if center is best and differences are small and overall brightness is reasonable,
    # do not draw arrows (lighting is good).
    if best_idx == 1 and diff < 20 and 80 < mean_brightness < 200:
        label = "Lighting looks balanced"
        cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 0), 2)
        return frame, best_idx

    # otherwise draw directional guidance
    center = (w // 2, h // 2)
    if best_idx == 0:
        dest = (w // 6, h // 2)
        label = "Better light -> Left"
    elif best_idx == 1:
        dest = (w // 2, h // 4)
        label = "Light is centered"
    else:
        dest = (w * 5 // 6, h // 2)
        label = "Better light -> Right"
    cv2.arrowedLine(frame, center, dest, (0, 255, 0), 3, tipLength=0.15)
    cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    return frame, best_idx


def show_side_by_side_preview(orig: np.ndarray, adjusted: Optional[np.ndarray], window_name: str = "Preview (o: original, a: adjusted)"):
    """Show a side-by-side preview of original and adjusted frames with overlays. Non-blocking: displays for a limited time or until key press."""
    try:
        if adjusted is None:
            disp = orig.copy()
        else:
            # resize adjusted to match original if necessary
            if adjusted.shape != orig.shape:
                adjusted = cv2.resize(adjusted, (orig.shape[1], orig.shape[0]))
            left = cv2.resize(orig, (orig.shape[1]//2, orig.shape[0]//2))
            right = cv2.resize(adjusted, (orig.shape[1]//2, orig.shape[0]//2))
            disp = np.hstack([left, right])
        disp_overlay, _ = overlay_direction_arrows(disp)
        cv2.imshow(window_name, disp_overlay)
        # Wait for 1s but allow keypress to interrupt. Return key code.
        k = cv2.waitKey(1000) & 0xFF
        return k
    except Exception as e:
        print("Preview display error:", e)
        return -1

# ---------- Camera & Recorder (enhanced previews and adjustable capture) ----------

class VoiceControlledCamera:
    def __init__(self, cam_index=0):
        self.cap = cv2.VideoCapture(cam_index)
        if not self.cap.isOpened():
            raise ValueError("Could not open camera")
        self.photo_dir = "photos"
        Path(self.photo_dir).mkdir(exist_ok=True)

    def capture_frame(self, tmp_path="temp_frame.jpg") -> Optional[str]:
        ret, frame = self.cap.read()
        if not ret:
            return None
        cv2.imwrite(tmp_path, frame)
        return tmp_path

    def take_photo(self, adjusted_frame: Optional[np.ndarray] = None) -> Optional[str]:
        ret, frame = self.cap.read()
        if not ret:
            return None
        if adjusted_frame is not None:
            # ensure adjusted frame size matches captured frame
            try:
                if adjusted_frame.shape != frame.shape:
                    adjusted_frame = cv2.resize(adjusted_frame, (frame.shape[1], frame.shape[0]))
                frame_to_save = adjusted_frame
            except Exception:
                frame_to_save = frame
        else:
            frame_to_save = frame
        fname = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        path = Path(self.photo_dir) / fname
        cv2.imwrite(str(path), frame_to_save)
        return str(path)

    def release(self):
        if self.cap:
            self.cap.release()

class VoiceControlledRecorder:
    def __init__(self, out_dir="videos", cam_index=0):
        self.is_recording = False
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.video_filename = "temp_video.avi"
        self.audio_filename = "temp_audio.wav"
        self.cap = cv2.VideoCapture(cam_index)
        if not self.cap.isOpened():
            raise ValueError("Could not open camera")
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 20.0
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.video_writer = None
        self.record_thread = None
        self.audio_thread = None
        # New: whether to write adjusted frames to disk
        self.apply_adjustment_mode: Optional[str] = None  # e.g. 'gamma'|'clahe'|None
        self.preview_window_name = "Recording Preview"

    def start_audio_thread(self):
        if not SOUNDDEVICE_AVAILABLE:
            print("sounddevice not available; audio will not be recorded.")
            return
        def audio_loop():
            frames = []
            try:
                with sd.InputStream(samplerate=44100, channels=1) as stream:
                    while self.is_recording:
                        data, overflowed = stream.read(1024)
                        if not overflowed:
                            frames.append(data.copy())
            except Exception as e:
                print("Audio recording error:", e)
            if frames:
                try:
                    sf.write(self.audio_filename, np.concatenate(frames), 44100)
                except Exception as e:
                    print("Error saving audio:", e)
        self.audio_thread = threading.Thread(target=audio_loop, daemon=True)
        self.audio_thread.start()

    def record_loop(self):
        # show live preview while recording and optionally write adjusted frames
        cv2.namedWindow(self.preview_window_name, cv2.WINDOW_NORMAL)
        while self.is_recording:
            ret, frame = self.cap.read()
            if not ret:
                break
            frame_to_show = frame.copy()
            # overlay arrows for guidance
            frame_to_show, _ = overlay_direction_arrows(frame_to_show)
            # apply adjustment to frame_to_write if requested
            frame_to_write = frame
            if self.apply_adjustment_mode == 'gamma':
                frame_to_write = apply_gamma_correction(frame_to_write, 1.6)
            elif self.apply_adjustment_mode == 'clahe':
                frame_to_write = apply_clahe_color(frame_to_write)
            # write the (possibly adjusted) frame
            self.video_writer.write(frame_to_write)
            # show preview (resized for display)
            display = cv2.resize(frame_to_show, (min(800, frame_to_show.shape[1]), min(450, frame_to_show.shape[0])))
            cv2.imshow(self.preview_window_name, display)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                # allow quick-stop via preview window 'q'
                self.is_recording = False
                break
            time.sleep(1 / (self.fps or 20.0))
        if self.video_writer:
            self.video_writer.release()
        try:
            cv2.destroyWindow(self.preview_window_name)
        except Exception:
            pass

    def start_recording(self) -> bool:
        if self.is_recording:
            return False
        self.video_writer = cv2.VideoWriter(self.video_filename, self.fourcc, self.fps, (self.frame_width, self.frame_height))
        if not self.video_writer.isOpened():
            print("Could not open video writer.")
            return False
        self.is_recording = True
        self.record_thread = threading.Thread(target=self.record_loop, daemon=True)
        self.record_thread.start()
        self.start_audio_thread()
        return True

    def stop_recording(self):
        if not self.is_recording:
            return False
        self.is_recording = False
        # allow threads to finish and then merge
        time.sleep(0.6)
        self.merge_audio_video()
        return True

    # ---- updated merge_audio_video: uses Gemini audio analysis to trim ----
    def merge_audio_video(self):
        timestamp_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = str(self.out_dir / f"recording_{timestamp_tag}.mp4")

        video_exists = os.path.exists(self.video_filename)
        audio_exists = os.path.exists(self.audio_filename)

        if not video_exists:
            print("No video file to process.")
            return

        # default: no trimming (use full durations)
        stop_timestamp = None

        # If audio exists, ask Gemini to find 'stop recording' timestamp
        if audio_exists:
            detected = analyze_audio_for_timestamp(self.audio_filename)
            if detected is not None and detected >= 0:
                stop_timestamp = float(detected)
            else:
                stop_timestamp = None

        # probe durations to be safe and compute fallback
        def probe_duration(path):
            try:
                cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', path]
                res = subprocess.run(cmd, capture_output=True, text=True)
                dur = float(res.stdout.strip())
                return dur
            except Exception:
                return None

        video_dur = probe_duration(self.video_filename)
        audio_dur = probe_duration(self.audio_filename) if audio_exists else None

        # If Gemini detected timestamp, cap it to both durations
        if stop_timestamp is not None:
            if video_dur is not None and stop_timestamp > video_dur:
                print(f"Gemini timestamp {stop_timestamp}s > video duration {video_dur}s, capping to video duration.")
                stop_timestamp = video_dur
            if audio_dur is not None and stop_timestamp > audio_dur:
                print(f"Gemini timestamp {stop_timestamp}s > audio duration {audio_dur}s, capping to audio duration.")
                stop_timestamp = min(stop_timestamp, audio_dur)
        else:
            # fallback: trim last 3 seconds if durations available
            fallback_trim = 3.0
            if video_dur is not None:
                stop_timestamp = max(0.0, video_dur - fallback_trim)
            elif audio_dur is not None:
                stop_timestamp = max(0.0, audio_dur - fallback_trim)
            else:
                stop_timestamp = None

        # Prepare trimmed filenames
        trimmed_audio = None
        trimmed_video = None

        # Trim audio if present and stop_timestamp known
        if audio_exists and stop_timestamp is not None:
            trimmed_audio = os.path.join(self.out_dir, f"trimmed_audio_{timestamp_tag}.wav")
            try:
                # re-encode to ensure clean boundaries
                cmd_audio = [
                    'ffmpeg', '-loglevel', 'error', '-y', '-i', self.audio_filename,
                    '-to', str(stop_timestamp),
                    '-c:a', 'pcm_s16le', trimmed_audio
                ]
                subprocess.run(cmd_audio, check=True)
                print(f"Trimmed audio to {stop_timestamp}s -> {trimmed_audio}")
            except Exception as e:
                print("Audio trimming failed, will use original audio:", e)
                trimmed_audio = None

        # Trim video if stop_timestamp known
        if video_exists and stop_timestamp is not None:
            trimmed_video = os.path.join(self.out_dir, f"trimmed_video_{timestamp_tag}.avi")
            try:
                # re-encode trimmed video to ensure correct timestamps/pts
                cmd_video = [
                    'ffmpeg', '-loglevel', 'error', '-y', '-i', self.video_filename,
                    '-to', str(stop_timestamp),
                    '-c:v', 'libx264', '-preset', 'veryfast', trimmed_video
                ]
                subprocess.run(cmd_video, check=True)
                print(f"Trimmed video to {stop_timestamp}s -> {trimmed_video}")
            except Exception as e:
                print("Video trimming failed, will use original video:", e)
                trimmed_video = None

        # Determine which files to merge
        audio_to_merge = trimmed_audio if (trimmed_audio and os.path.exists(trimmed_audio)) else (self.audio_filename if audio_exists else None)
        video_to_merge = trimmed_video if (trimmed_video and os.path.exists(trimmed_video)) else self.video_filename

        # Improved merge step to re-encode video with proper pts, which helps with A/V sync issues.
        if audio_to_merge:
            cmd_merge = [
                'ffmpeg', '-loglevel', 'error', '-y', '-fflags', '+genpts', '-r', str(int(self.fps or 25)),
                '-i', video_to_merge, '-i', audio_to_merge,
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
                '-c:a', 'aac', '-b:a', '128k',
                '-map', '0:v:0', '-map', '1:a:0',
                '-shortest', '-movflags', '+faststart', output_file
            ]
            try:
                subprocess.run(cmd_merge, check=True)
                print("Merged trimmed video and audio ->", output_file)
                # cleanup temp files
                try:
                    if os.path.exists(self.video_filename):
                        os.remove(self.video_filename)
                    if os.path.exists(self.audio_filename):
                        os.remove(self.audio_filename)
                    if trimmed_audio and os.path.exists(trimmed_audio) and trimmed_audio != self.audio_filename:
                        os.remove(trimmed_audio)
                    if trimmed_video and os.path.exists(trimmed_video) and trimmed_video != self.video_filename:
                        os.remove(trimmed_video)
                except Exception:
                    pass
            except Exception as e:
                print("Merging failed, saving raw files instead:", e)
                # fallback behavior if merge fails
                if trimmed_video and os.path.exists(trimmed_video):
                    fallback = str(self.out_dir / f"recording_fallback_{timestamp_tag}.mp4")
                    os.rename(trimmed_video, fallback)
                    print("Saved trimmed video without audio to", fallback)
                elif os.path.exists(self.video_filename):
                    fallback = str(self.out_dir / f"recording_fallback_{timestamp_tag}.mp4")
                    os.rename(self.video_filename, fallback)
                    print("Saved raw video to", fallback)
        else:
            # no audio to merge: just save/rename video
            try:
                final_path = str(self.out_dir / f"recording_{timestamp_tag}.mp4")
                src = trimmed_video if (trimmed_video and os.path.exists(trimmed_video)) else self.video_filename
                if src and os.path.exists(src):
                    # re-encode to mp4/container for compatibility
                    cmd_wrap = [
                        'ffmpeg', '-loglevel', 'error', '-y', '-fflags', '+genpts', '-i', src,
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
                        '-movflags', '+faststart', final_path
                    ]
                    subprocess.run(cmd_wrap, check=True)
                    print("Saved video to", final_path)
                else:
                    print("No usable video file found to save.")
            except Exception as e:
                print("Failed to save video file:", e)

    def release(self):
        if self.cap:
            self.cap.release()
        if self.video_writer:
            self.video_writer.release()

# ---------- Simple voice/text helpers ----------

def capture_audio_segment(duration=4, sample_rate=44100, channels=1) -> str:
    """Record a short audio snippet and return Google STT transcript (if available)."""
    if not SOUNDDEVICE_AVAILABLE or not SR_AVAILABLE:
        return ""
    try:
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels)
        sd.wait()
        temp_wav = "temp_segment.wav"
        sf.write(temp_wav, recording, sample_rate)
        r = sr.Recognizer()
        with sr.AudioFile(temp_wav) as source:
            audio = r.record(source)
        text = r.recognize_google(audio)
        try:
            os.remove(temp_wav)
        except Exception:
            pass
        return text
    except Exception:
        return ""


def parse_ready_from_text(text: str) -> str:
    """Map recognized text to commands: 'ready'|'check'|'cancel'|'stop' or empty."""
    if not text:
        return ""
    t = text.lower()
    if any(k in t for k in ("ready", "proceed", "go", "yes", "ok", "okay")):
        return "ready"
    if any(k in t for k in ("check", "again", "recheck", "retry")):
        return "check"
    if any(k in t for k in ("cancel", "abort", "no")):
        return "cancel"
    if any(k in t for k in ("stop recording", "stop", "finish")):
        return "stop"
    return ""

# ---------- Interactive pre-check + capture flows (enhanced with auto-adjust & preview) ----------

def _ask_user_apply_adjustment(text_mode: bool, out_dir: Path, no_tts: bool) -> bool:
    """Ask the user whether they'd like the app to attempt automatic lighting adjustments."""
    prompt_msg = "I can try to automatically adjust exposure/contrast in software to improve lighting. Try it? (yes/no)"
    if not text_mode:
        safe_tts(prompt_msg, out_dir, no_tts)
        print(prompt_msg, "(listening 3s)")
        spoken = capture_audio_segment(duration=3)
        if spoken and any(k in spoken.lower() for k in ("yes", "yeah", "yep", "ok", "sure", "do it")):
            return True
        return False
    else:
        ans = input(prompt_msg + " ").strip().lower()
        return ans in ("y", "yes", "ok", "sure")


def _choose_adjustment_mode_based_on_brightness(lighting: str) -> str:
    """Simple heuristic: choose gamma for dark/dim, CLAHE for contrast issues."""
    if lighting in ("dark", "dim"):
        return 'gamma'
    return 'clahe'


def interactive_precheck_and_photo(camera: VoiceControlledCamera, out_dir: Path, text_mode: bool, no_tts: bool):
    """Analyze frame, suggest fixes, allow user to re-check, then take photo after 5s countdown."""
    tmp = "temp_frame.jpg"
    frame_path = camera.capture_frame(tmp)
    if not frame_path:
        print("Failed to capture camera frame for analysis.")
        return
    analysis = analyze_frame_with_gemini(frame_path)
    adjusted_frame_preview = None
    while True:
        # Present simple suggestions
        print("\n--- Camera check ---")
        print(f"Lighting: {analysis.get('lighting')}, brightness: {analysis.get('brightness')}, contrast: {analysis.get('contrast')}")
        if analysis.get("background_issues"):
            print("Background issues:", ", ".join(analysis["background_issues"]))
        print("Suggestions:")
        for s in analysis.get("suggestions", []):
            print(" -", s)
        # speak a short suggestion
        safe_tts("Quick camera suggestion: " + " ".join(analysis.get("suggestions", [])[:2]), out_dir, no_tts)

        # If problems are noticeable, offer automatic adjustment
        problems = (analysis.get('lighting') in ('dark', 'dim')) or bool(analysis.get('background_issues'))
        apply_adj = False
        chosen_adj_mode = None
        if problems:
            want_adj = _ask_user_apply_adjustment(text_mode, out_dir, no_tts)
            if want_adj:
                chosen_adj_mode = _choose_adjustment_mode_based_on_brightness(analysis.get('lighting'))
                # load current frame and create adjusted preview
                orig = cv2.imread(tmp)
                if orig is not None:
                    if chosen_adj_mode == 'gamma':
                        adjusted_frame_preview = apply_gamma_correction(orig, 1.6)
                    else:
                        adjusted_frame_preview = apply_clahe_color(orig)
                    # show preview side-by-side with overlay arrows
                    print("Showing side-by-side preview (original | adjusted). Press Enter to accept adjusted, 'r' to re-check, or anything else to continue without.")
                    k = show_side_by_side_preview(orig, adjusted_frame_preview)
                    # interpret key: Enter/Return usually 13; sometimes 10; if text_mode we ask
                    if text_mode:
                        ans = input("Accept adjusted image? (yes/no/recheck): ").strip().lower()
                        if ans in ('yes', 'y'):
                            apply_adj = True
                        elif ans in ('recheck', 'r'):
                            apply_adj = False
                            # continue loop to re-analyze
                            frame_path = camera.capture_frame(tmp)
                            if not frame_path:
                                print("Failed to capture frame. Aborting.")
                                return
                            analysis = analyze_frame_with_gemini(frame_path)
                            continue
                        else:
                            apply_adj = False
                    else:
                        # for non-text mode, accept if user said 'ready' in quick capture or if Enter pressed.
                        # The key returned from show_side_by_side_preview isn't reliable across platforms; use default: accept after preview
                        print("Auto-accepting adjusted preview (voice mode) — you can still choose 'check' when prompted next.)")
                        apply_adj = True
                else:
                    print("Could not load frame for adjustment preview.")

        # Ask user whether they want to fix and re-check or proceed
        if text_mode:
            choice = input("\nType 'ready' to take photo, 'check' to re-analyze, or 'cancel' to abort: ").strip().lower()
            if choice in ("ready", "go", "yes", "proceed"):
                cmd = "ready"
            elif choice in ("check", "again", "retry"):
                cmd = "check"
            elif choice in ("cancel", "quit", "abort"):
                cmd = "cancel"
            else:
                print("Unrecognized input; treating as 'check'.")
                cmd = "check"
        else:
            print("Say 'ready' to proceed, 'check' to re-analyze, or 'cancel' to abort (listening 4s)...")
            spoken = capture_audio_segment(duration=4)
            cmd = parse_ready_from_text(spoken)
            if not cmd:
                print("No clear voice command detected; defaulting to 'check'.")
                cmd = "check"
            else:
                print("Heard:", cmd)

        if cmd == "cancel":
            print("Cancelled.")
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
            return
        elif cmd == "check":
            # re-capture and analyze
            time.sleep(0.5)
            frame_path = camera.capture_frame(tmp)
            if not frame_path:
                print("Failed to capture frame. Aborting.")
                return
            analysis = analyze_frame_with_gemini(frame_path)
            continue
        elif cmd == "ready":
            # countdown 5s and take photo
            safe_tts("Taking photo in 5 seconds. Get ready.", out_dir, no_tts)
            for i in range(5, 0, -1):
                print(f"Taking photo in {i}...")
                time.sleep(1)
            # If apply_adj chosen, pass adjusted_frame_preview to save; otherwise None
            photo_path = camera.take_photo(adjusted_frame=adjusted_frame_preview if apply_adj else None)
            if photo_path:
                print("Photo saved to", photo_path)
                safe_tts("Photo taken.", out_dir, no_tts)
            else:
                print("Failed to take photo.")
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
            return


def interactive_precheck_and_video(camera: VoiceControlledCamera, recorder: VoiceControlledRecorder, out_dir: Path, text_mode: bool, no_tts: bool):
    """Analyze frame, suggest fixes, allow user to re-check, then start recording after 5s countdown and stop on 'stop recording'."""
    tmp = "temp_frame.jpg"
    frame_path = camera.capture_frame(tmp)
    if not frame_path:
        print("Failed to capture camera frame for analysis.")
        return
    analysis = analyze_frame_with_gemini(frame_path)
    apply_adj_for_video = False
    chosen_adj_mode = None
    while True:
        print("\n--- Camera check ---")
        print(f"Lighting: {analysis.get('lighting')}, brightness: {analysis.get('brightness')}, contrast: {analysis.get('contrast')}")
        if analysis.get("background_issues"):
            print("Background issues:", ", ".join(analysis["background_issues"]))
        print("Suggestions:")
        for s in analysis.get("suggestions", []):
            print(" -", s)
        safe_tts("Quick camera suggestion: " + " ".join(analysis.get("suggestions", [])[:2]), out_dir, no_tts)

        problems = (analysis.get('lighting') in ('dark', 'dim')) or bool(analysis.get('background_issues'))
        if problems:
            want_adj = _ask_user_apply_adjustment(text_mode, out_dir, no_tts)
            if want_adj:
                chosen_adj_mode = _choose_adjustment_mode_based_on_brightness(analysis.get('lighting'))
                orig = cv2.imread(tmp)
                adjusted_preview = None
                if orig is not None:
                    if chosen_adj_mode == 'gamma':
                        adjusted_preview = apply_gamma_correction(orig, 1.6)
                    else:
                        adjusted_preview = apply_clahe_color(orig)
                    print("Showing preview. Press Enter to accept adjusted preview (video will be recorded with adjustment), 'r' to re-check, or any other key to decline.")
                    show_side_by_side_preview(orig, adjusted_preview)
                    if text_mode:
                        ans = input("Accept adjusted preview for video (yes/no/recheck)? ").strip().lower()
                        if ans in ('yes', 'y'):
                            apply_adj_for_video = True
                        elif ans in ('recheck', 'r'):
                            frame_path = camera.capture_frame(tmp)
                            if not frame_path:
                                print("Failed to capture frame. Aborting.")
                                return
                            analysis = analyze_frame_with_gemini(frame_path)
                            continue
                        else:
                            apply_adj_for_video = False
                    else:
                        # default to accept in voice mode after preview
                        print("Auto-accepting adjusted preview for video (voice mode).")
                        apply_adj_for_video = True

        if text_mode:
            choice = input("\nType 'ready' to start recording, 'check' to re-analyze, or 'cancel' to abort: ").strip().lower()
            if choice in ("ready", "go", "yes", "proceed"):
                cmd = "ready"
            elif choice in ("check", "again", "retry"):
                cmd = "check"
            elif choice in ("cancel", "quit", "abort"):
                cmd = "cancel"
            else:
                print("Unrecognized input; treating as 'check'.")
                cmd = "check"
        else:
            print("Say 'ready' to start recording, 'check' to re-analyze, or 'cancel' to abort (listening 4s)...")
            spoken = capture_audio_segment(duration=4)
            cmd = parse_ready_from_text(spoken)
            if not cmd:
                print("No clear voice command detected; defaulting to 'check'.")
                cmd = "check"
            else:
                print("Heard:", cmd)

        if cmd == "cancel":
            print("Cancelled.")
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
            return
        elif cmd == "check":
            time.sleep(0.5)
            frame_path = camera.capture_frame(tmp)
            if not frame_path:
                print("Failed to capture frame. Aborting.")
                return
            analysis = analyze_frame_with_gemini(frame_path)
            continue
        elif cmd == "ready":
            safe_tts("Starting recording in 5 seconds. Say stop recording to end.", out_dir, no_tts)
            for i in range(5, 0, -1):
                print(f"Recording starts in {i}...")
                time.sleep(1)
            # configure recorder to write adjusted frames if needed
            if apply_adj_for_video and chosen_adj_mode:
                recorder.apply_adjustment_mode = chosen_adj_mode
            else:
                recorder.apply_adjustment_mode = None
            started = recorder.start_recording()
            if not started:
                print("Failed to start recording.")
                return
            print("Recording started. Say 'stop recording' or type it to stop. You can also press 'q' in the preview window to stop.")
            # Monitor for stop command either voice or text
            while recorder.is_recording:
                if text_mode:
                    # check typed input non-blocking: prompt user
                    print("(Type 'stop recording' to stop or press Enter to wait...)")
                    s = input().strip().lower()
                    if "stop recording" in s or s == "stop":
                        recorder.stop_recording()
                        safe_tts("Recording stopped and saved.", out_dir, no_tts)
                        break
                else:
                    # listen short segments for stop command
                    spoken = capture_audio_segment(duration=3)
                    cmd2 = parse_ready_from_text(spoken)
                    if cmd2 == "stop":
                        recorder.stop_recording()
                        safe_tts("Recording stopped and saved.", out_dir, no_tts)
                        break
                    # else continue listening
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
            return

# ---------- Main CLI ----------

def parse_args():
    p = argparse.ArgumentParser(description="Voice-Controlled Conversational Agent")
    p.add_argument("--text-mode", action="store_true", help="Use typed inputs instead of voice")
    p.add_argument("--no-tts-play", action="store_true", help="Don't play TTS audio (only save)")
    p.add_argument("--output-dir", "-o", default="sessions", help="Session output directory")
    return p.parse_args()


def main():
    args = parse_args()
    text_mode = args.text_mode
    no_tts = args.no_tts_play
    out_dir = Path(args.output_dir)
    out_dir.mkdir(exist_ok=True)
    audio_dir = out_dir / "audios"
    audio_dir.mkdir(exist_ok=True)
    video_dir = out_dir / "videos"
    video_dir.mkdir(exist_ok=True)
    photo_dir = out_dir / "photos"
    photo_dir.mkdir(exist_ok=True)

    # instantiate camera and recorder
    try:
        camera = VoiceControlledCamera()
    except Exception as e:
        print("Camera init failed:", e)
        return
    try:
        recorder = VoiceControlledRecorder(out_dir=str(video_dir))
    except Exception as e:
        print("Recorder init failed:", e)
        recorder = None

    print("Assistant ready. Say or type commands. Examples: 'take photo', 'record video', 'help', 'quit'.")

    # Welcome TTS
    safe_tts("Hello! I can check your lighting and background before taking photos or videos. Say or type 'take photo' or 'record video' to begin.", out_dir, no_tts)

    while True:
        user_input = ""
        if text_mode:
            user_input = input("\nYou: ").strip()
        else:
            # listen for command (short)
            print("\nListening for a command (4s)...")
            user_input = capture_audio_segment(duration=4)
            print("Heard:", user_input)
        if not user_input:
            continue
        ui = user_input.lower()

        if any(k in ui for k in ("quit", "exit", "bye")):
            print("Goodbye.")
            break
        if "help" in ui:
            print("Commands: 'take photo', 'record video', 'quit'")
            continue

        # Photo flow
        if any(k in ui for k in ("take photo", "take a photo", "photo", "take picture", "snap")):
            interactive_precheck_and_photo(camera, out_dir, text_mode, no_tts)
            continue

        # Video flow
        if any(k in ui for k in ("record video", "start recording", "record", "video")):
            if recorder is None:
                print("Recorder not initialized; cannot record video.")
                continue
            interactive_precheck_and_video(camera, recorder, out_dir, text_mode, no_tts)
            continue

        # General fallback
        print("I didn't catch a recognized command. Try 'take photo' or 'record video'. Type 'help' for options.")

    # cleanup
    camera.release()
    if recorder:
        recorder.release()
    try:
        cv2.destroyAllWindows()
    except Exception:
        pass

if __name__ == "__main__":
    main()
