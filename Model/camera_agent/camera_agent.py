#!/usr/bin/env python3
"""
Voice-Controlled Conversational Agent with Camera and Recorder Integration using LangGraph.

Notifies user when recording starts, suppresses responses during recording, uses sounddevice/soundfile for audio capture,
and analyzes video audio with Gemini (google.generativeai) to detect 'stop recording' timestamp for video trimming using FFmpeg.
Requirements:
- pip install opencv-python speechrecognition gtts sounddevice soundfile langgraph langchain-google-genai numpy google-generativeai
- FFmpeg installed for audio/video processing.
- Set environment variable: GEMINI_API_KEY
- Usage: python conversational_agent.py [--text-mode] [--no-tts-play]
"""

import os
import sys
import json
import time
import argparse
import io
from datetime import datetime
from pathlib import Path
import threading
import cv2
import subprocess
import re
import numpy as np
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
try:
    import sounddevice as sd
    import soundfile as sf
    SOUNDDEVICE_AVAILABLE = True
except Exception:
    SOUNDDEVICE_AVAILABLE = False
import speech_recognition as sr
from gtts import gTTS
import google.generativeai as genai

# ------------------ Configuration ------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDiUMs4sIAdOk09006hS7DcY79DZh53_M4")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.5-flash")  # Updated to 2.5-flash

# Configure genai client
genai.configure(api_key=GEMINI_API_KEY)

# ------------------ State Definition for LangGraph ------------------
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "add_messages"]

# ------------------ Tools ------------------
camera = None
recorder = None

@tool
def take_photo() -> str:
    """Take a photo using the camera."""
    global camera
    if camera is None:
        return "Camera not initialized."
    success = camera.take_photo()
    return "Photo taken successfully!" if success else "Failed to take photo."

@tool
def start_recording() -> str:
    """Start video and audio recording."""
    global recorder
    if recorder is None:
        return "Recorder not initialized."
    success = recorder.start_recording()
    return "Recording started!" if success else "Failed to start recording or already recording."

@tool
def stop_recording() -> str:
    """Stop recording and save the video."""
    global recorder
    if recorder is None:
        return "Recorder not initialized."
    success = recorder.stop_recording()
    return "Recording stopped and saved!" if success else "Not currently recording."

tools = [take_photo, start_recording, stop_recording]

# ------------------ LLM Setup ------------------
llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL_NAME, google_api_key=GEMINI_API_KEY)
llm_with_tools = llm.bind_tools(tools)

# ------------------ Gemini Audio Analysis ------------------
def analyze_audio_for_timestamp(audio_path: str) -> float:
    """Analyze audio with Gemini (google.generativeai) to find the timestamp of 'stop recording'."""
    try:
        client = genai.GenerativeModel(GEMINI_MODEL_NAME)
        # Upload audio file
        with open(audio_path, "rb") as audio_file:
            uploaded_file = genai.upload_file(audio_path)
        # Request transcription with timestamp for 'stop recording'
        prompt = (
            "Transcribe the audio and provide the exact timestamp (in seconds) when the phrase "
            "'stop recording' or 'recording stop' is spoken. Return only the timestamp as a float (e.g., 10.5). "
            "If the phrase is not found, return -1."
        )
        response = client.generate_content([prompt, uploaded_file])
        # Parse response (assuming it returns a timestamp as text)
        timestamp_str = response.text.strip()
        try:
            timestamp = float(timestamp_str)
            if timestamp >= 0:
                print(f"Detected 'stop recording' at {timestamp} seconds")
                return timestamp
            else:
                print("Could not detect 'stop recording' in audio. Using fallback trimming.")
                return -1
        except ValueError:
            print("Invalid timestamp format in Gemini response. Using fallback trimming.")
            return -1
    except Exception as e:
        print(f"Error analyzing audio with Gemini: {e}")
        return -1

# ------------------ LangGraph Nodes ------------------
def llm_node(state: AgentState) -> AgentState:
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)

# ------------------ Camera and Recorder Classes ------------------
class VoiceControlledCamera:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise ValueError("Could not open camera")
        self.photo_dir = 'photos'
        if not os.path.exists(self.photo_dir):
            os.makedirs(self.photo_dir)

    def take_photo(self):
        ret, frame = self.cap.read()
        if ret:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.photo_dir, f"photo_{timestamp}.jpg")
            cv2.imwrite(filename, frame)
            print(f"Photo saved as {filename}")
            return True
        else:
            print("Failed to grab frame")
            return False

    def __del__(self):
        if self.cap:
            self.cap.release()

class VoiceControlledRecorder:
    def __init__(self):
        self.is_recording = False
        self.video_writer = None
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_filename = 'temp_video.avi'
        self.audio_filename = 'temp_audio.wav'
        self.video_dir = 'videos'
        if not os.path.exists(self.video_dir):
            os.makedirs(self.video_dir)
        self.recording_thread = None
        self.audio_thread = None
        self.chunk = 1024
        self.channels = 1
        self.rate = 44100
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise ValueError("Could not open camera")
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 20.0
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def start_audio_recording(self):
        self.audio_thread = threading.Thread(target=self.audio_record_loop)
        self.audio_thread.daemon = True
        self.audio_thread.start()

    def audio_record_loop(self):
        if not SOUNDDEVICE_AVAILABLE:
            print("sounddevice not available, cannot record audio")
            return
        recording = []
        with sd.InputStream(samplerate=self.rate, channels=self.channels) as stream:
            while self.is_recording:
                data, overflowed = stream.read(self.chunk)
                if not overflowed:
                    recording.append(data)
        sf.write(self.audio_filename, np.concatenate(recording), self.rate)

    def start_recording(self):
        if not self.is_recording:
            self.video_writer = cv2.VideoWriter(self.video_filename, self.fourcc, self.fps, (self.frame_width, self.frame_height))
            if not self.video_writer.isOpened():
                print("Error opening video writer")
                return False
            self.is_recording = True
            print("Recording started...")
            self.recording_thread = threading.Thread(target=self.record_loop)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            self.start_audio_recording()
            return True
        return False

    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            time.sleep(0.5)
            self.merge_audio_video()
            return True
        return False

    def merge_audio_video(self):
        if os.path.exists(self.video_filename) and os.path.exists(self.audio_filename):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = os.path.join(self.video_dir, f"recording_{timestamp}.mp4")
            trimmed_audio = os.path.join(self.video_dir, f"trimmed_audio_{timestamp}.wav")
            trimmed_video = os.path.join(self.video_dir, f"trimmed_video_{timestamp}.avi")

            # Analyze audio to find 'stop recording' timestamp
            stop_timestamp = analyze_audio_for_timestamp(self.audio_filename)
            if stop_timestamp < 0:
                # Fallback: Trim last 3 seconds
                stop_timestamp = None
                print("Using fallback: trimming last 3 seconds of audio and video")

            # Trim audio
            if stop_timestamp is not None:
                trim_audio_cmd = [
                    'ffmpeg', '-i', self.audio_filename, '-to', str(stop_timestamp),
                    '-c:a', 'copy', trimmed_audio, '-y'
                ]
            else:
                trim_audio_cmd = [
                    'ffmpeg', '-i', self.audio_filename, '-t', 'trim=end-3',
                    '-c:a', 'copy', trimmed_audio, '-y'
                ]
            trim_result = subprocess.call(trim_audio_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            audio_to_use = trimmed_audio if trim_result == 0 else self.audio_filename
            print(f"Using audio: {audio_to_use}")

            # Trim video to match audio duration
            if stop_timestamp is not None:
                trim_video_cmd = [
                    'ffmpeg', '-i', self.video_filename, '-to', str(stop_timestamp),
                    '-c:v', 'copy', trimmed_video, '-y'
                ]
            else:
                # Estimate video duration and trim last 3 seconds
                probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', self.video_filename]
                probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
                try:
                    duration = float(json.loads(probe_result.stdout)['format']['duration'])
                    trim_duration = duration - 3
                except Exception:
                    trim_duration = 'trim=end-3'
                trim_video_cmd = [
                    'ffmpeg', '-i', self.video_filename, '-to', str(trim_duration),
                    '-c:v', 'copy', trimmed_video, '-y'
                ]
            trim_video_result = subprocess.call(trim_video_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            video_to_use = trimmed_video if trim_video_result == 0 else self.video_filename
            print(f"Using video: {video_to_use}")

            # Merge trimmed video and audio
            cmd = [
                'ffmpeg', '-i', video_to_use, '-i', audio_to_use,
                '-c:v', 'copy', '-c:a', 'aac', '-shortest', output_filename, '-y'
            ]
            result = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result == 0:
                os.remove(self.video_filename)
                os.remove(self.audio_filename)
                if os.path.exists(trimmed_audio):
                    os.remove(trimmed_audio)
                if os.path.exists(trimmed_video):
                    os.remove(trimmed_video)
                print(f"Recording saved as {output_filename}")
            else:
                os.remove(self.audio_filename)
                if os.path.exists(trimmed_audio):
                    os.remove(trimmed_audio)
                if os.path.exists(trimmed_video):
                    os.remove(trimmed_video)
                os.rename(video_to_use, output_filename)
                print(f"Recording saved as {output_filename} (no audio)")

    def record_loop(self):
        while self.is_recording:
            ret, frame = self.cap.read()
            if ret:
                self.video_writer.write(frame)
            else:
                print("Failed to grab frame")
                break
            time.sleep(1 / self.fps)
        if self.video_writer:
            self.video_writer.release()

    def __del__(self):
        if self.cap:
            self.cap.release()
        if self.video_writer:
            self.video_writer.release()

# ------------------ Audio Capture with sounddevice ------------------
def capture_audio_segment(duration=5, sample_rate=44100, channels=1) -> str:
    """Capture audio using sounddevice and transcribe with Google STT."""
    if not SOUNDDEVICE_AVAILABLE:
        print("sounddevice not available, cannot capture audio")
        return ""
    try:
        print("Listening...")
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels)
        sd.wait()
        temp_wav = "temp_segment.wav"
        sf.write(temp_wav, recording, sample_rate)
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_wav) as source:
            audio = recognizer.record(source)
        transcript = recognizer.recognize_google(audio)
        print(f"Recognized: {transcript}")
        os.remove(temp_wav)
        return transcript
    except sr.UnknownValueError:
        print("Could not understand audio")
        return ""
    except sr.RequestError as e:
        print(f"Error with Google STT service: {e}")
        return ""
    except Exception as e:
        print(f"Error capturing audio: {e}")
        return ""

# ------------------ Google TTS Helper ------------------
def google_tts_bytes(text: str, lang: str = 'en') -> bytes:
    tts = gTTS(text=text, lang=lang)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp.read()

def play_audio_file(path: str):
    if not os.path.exists(path):
        print("Audio file not found:", path)
        return
    try:
        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path], check=True)
    except Exception:
        print(f"🔈 TTS saved to {path} — no playback.")

# ------------------ LangGraph Setup ------------------
workflow = StateGraph(state_schema=AgentState)
workflow.add_node("llm", llm_node)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("llm")
workflow.add_conditional_edges("llm", tools_condition, {"tools": "tools", END: END})
workflow.add_edge("tools", END)
graph = workflow.compile()

# ------------------ Main CLI Loop ------------------
def parse_args():
    p = argparse.ArgumentParser(description="Voice-Controlled Conversational Agent with LangGraph")
    p.add_argument("--text-mode", action="store_true", help="Type inputs instead of voice")
    p.add_argument("--no-tts-play", action="store_true", help="Don't play TTS audio")
    p.add_argument("--output-dir", "-o", default="sessions", help="Session output directory")
    return p.parse_args()

def main():
    global camera, recorder
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(exist_ok=True)
    audios_dir = out_dir / "audios"
    audios_dir.mkdir(exist_ok=True)

    try:
        camera = VoiceControlledCamera()
        recorder = VoiceControlledRecorder()
    except ValueError as e:
        print(f"❌ Camera init failed: {e}")
        return

    messages = [SystemMessage(content="You are a helpful voice-controlled assistant integrated with a camera and recorder. You can chat casually, control the camera and recorder using tools. During recording, do not respond except to stop recording when requested. Keep responses short, natural, and engaging. Always end with a question to continue the conversation unless recording.")]
    print("Initializing agent...")

    # Welcome message
    welcome = "Hello! I'm your voice-controlled assistant. I can chat, take photos, record videos. What would you like to do?"
    print("\nAssistant:", welcome)
    try:
        tts_bytes = google_tts_bytes(welcome)
        welcome_path = audios_dir / f"welcome_{int(time.time())}.mp3"
        with open(welcome_path, "wb") as f:
            f.write(tts_bytes)
        if not args.no_tts_play:
            play_audio_file(str(welcome_path))
    except Exception as e:
        print("⚠️ TTS failed:", e)

    while True:
        transcript = ""
        if args.text_mode:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ("bye", "thank you bye"):
                print("Stopping script as requested.")
                break
            transcript = user_input
            print("\nYou:", transcript)
        else:
            transcript = capture_audio_segment(duration=5)
            if not transcript:
                continue
            if re.search(r'\b(thank you bye|bye)\b', transcript.lower()):
                print("Stopping script as requested.")
                break

        if transcript and not recorder.is_recording:
            messages.append(HumanMessage(content=transcript))
            result = graph.invoke({"messages": messages})
            new_messages = result["messages"]
            last_msg = new_messages[-1]
            if isinstance(last_msg, ToolMessage):
                assistant_text = last_msg.content
                if last_msg.content == "Recording started!":
                    print("\nAssistant:", assistant_text)
                    if not args.no_tts_play:
                        try:
                            tts_bytes = google_tts_bytes(assistant_text)
                            tts_path = audios_dir / f"assistant_{int(time.time())}.mp3"
                            with open(tts_path, "wb") as f:
                                f.write(tts_bytes)
                            play_audio_file(str(tts_path))
                        except Exception as e:
                            print("⚠️ TTS failed:", e)
            else:
                assistant_text = last_msg.content
                print("\nAssistant:", assistant_text)
                if not args.no_tts_play:
                    try:
                        tts_bytes = google_tts_bytes(assistant_text)
                        tts_path = audios_dir / f"assistant_{int(time.time())}.mp3"
                        with open(tts_path, "wb") as f:
                            f.write(tts_bytes)
                        play_audio_file(str(tts_path))
                    except Exception as e:
                        print("⚠️ TTS failed:", e)
            messages = new_messages
        elif recorder.is_recording:
            if re.search(r'\bstop recording\b', transcript.lower()):
                messages.append(HumanMessage(content="stop_recording"))
                result = graph.invoke({"messages": messages})
                new_messages = result["messages"]
                last_msg = new_messages[-1]
                assistant_text = last_msg.content
                print("\nAssistant:", assistant_text)
                if not args.no_tts_play:
                    try:
                        tts_bytes = google_tts_bytes(assistant_text)
                        tts_path = audios_dir / f"assistant_{int(time.time())}.mp3"
                        with open(tts_path, "wb") as f:
                            f.write(tts_bytes)
                        play_audio_file(str(tts_path))
                    except Exception as e:
                        print("⚠️ TTS failed:", e)
                messages = new_messages

        if args.text_mode:
            cont = input("Continue? (Enter or 'bye'): ").strip()
            if cont.lower() in ("bye", "thank you bye"):
                print("Stopping script as requested.")
                break

    # Cleanup
    if camera:
        del camera
    if recorder:
        del recorder
    history_path = out_dir / f"history_{int(time.time())}.json"
    with open(history_path, "w") as f:
        json.dump([{"role": m.type, "content": m.content} for m in messages], f, indent=2)
    print(f"\nSession saved to {history_path}. Goodbye!")

if __name__ == "__main__":
    main()