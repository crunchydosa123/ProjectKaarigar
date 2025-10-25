# This script requires the following packages to be installed:
# pip install opencv-python speechrecognition pyttsx3 pyaudio
# Note: pyaudio might require additional setup on some systems (e.g., portaudio on macOS/Linux).
# Additionally, FFmpeg must be installed and available in the system PATH for merging audio and video.

import cv2
import speech_recognition as sr
import pyttsx3
import threading
import time
import os
import pyaudio
import wave
import subprocess
from datetime import datetime

class VoiceControlledRecorder:
    def __init__(self):
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Adjust for ambient noise
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        
        # Initialize TTS engine
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 150)  # Speed of speech
        
        # Recording state
        self.is_recording = False
        self.video_writer = None
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Using XVID for AVI compatibility with FFmpeg
        self.video_filename = 'temp_video.avi'
        self.audio_filename = 'temp_audio.wav'
        self.video_dir = 'videos'
        if not os.path.exists(self.video_dir):
            os.makedirs(self.video_dir)
        self.recording_thread = None
        self.audio_thread = None
        self.p = pyaudio.PyAudio()
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        
        # Camera setup
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise ValueError("Could not open camera")
        
        # Get camera properties for video writer
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps == 0:
            self.fps = 20.0  # Default FPS
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    def speak(self, text):
        """Convert text to speech."""
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
    
    def listen_for_command(self):
        """Listen for voice command."""
        try:
            with self.microphone as source:
                print("Listening for command...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
            
            command = self.recognizer.recognize_google(audio).lower()
            print(f"Recognized: {command}")
            return command
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Error with speech recognition service: {e}")
            return None
    
    def start_audio_recording(self):
        """Start audio recording in a separate thread."""
        self.wf = wave.open(self.audio_filename, 'wb')
        self.wf.setnchannels(self.channels)
        self.wf.setsampwidth(self.p.get_sample_size(self.format))
        self.wf.setframerate(self.rate)
        self.audio_thread = threading.Thread(target=self.audio_record_loop)
        self.audio_thread.daemon = True
        self.audio_thread.start()
    
    def audio_record_loop(self):
        """Loop to record audio frames."""
        stream = self.p.open(format=self.format,
                             channels=self.channels,
                             rate=self.rate,
                             input=True,
                             frames_per_buffer=self.chunk)
        frames = []
        while self.is_recording:
            data = stream.read(self.chunk)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        self.wf.writeframes(b''.join(frames))
        self.wf.close()
    
    def start_recording(self):
        """Start video and audio recording."""
        if not self.is_recording:
            self.video_writer = cv2.VideoWriter(self.video_filename, self.fourcc, self.fps, (self.frame_width, self.frame_height))
            if not self.video_writer.isOpened():
                print("Error opening video writer")
                self.speak("Failed to start recording")
                return
            self.is_recording = True
            self.speak("Recording started with audio")
            print("Recording started...")
            # Start video recording in a separate thread
            self.recording_thread = threading.Thread(target=self.record_loop)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            # Start audio recording
            self.start_audio_recording()
    
    def stop_recording(self):
        """Stop video and audio recording, then merge."""
        if self.is_recording:
            self.is_recording = False
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
            if self.cap:
                self.cap.release()
            # Wait a bit for threads to finish
            time.sleep(0.5)
            self.merge_audio_video()
            self.speak("Recording stopped")
    
    def merge_audio_video(self):
        """Merge video and audio files using FFmpeg."""
        if os.path.exists(self.video_filename) and os.path.exists(self.audio_filename):
            # Generate timestamp for output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_filename = os.path.join(self.video_dir, f"recording_{timestamp}.mp4")
            cmd = [
                'ffmpeg',
                '-i', self.video_filename,
                '-i', self.audio_filename,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-shortest',
                self.output_filename,
                '-y'  # Overwrite output file if exists
            ]
            result = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result == 0:
                # Clean up temp files
                if os.path.exists(self.video_filename):
                    os.remove(self.video_filename)
                if os.path.exists(self.audio_filename):
                    os.remove(self.audio_filename)
                print(f"Recording saved as {self.output_filename}")
                print("Audio and video merged successfully.")
            else:
                print("Warning: Failed to merge audio and video. Video saved without audio.")
                # Rename video to output
                os.rename(self.video_filename, self.output_filename)
                print(f"Recording saved as {self.output_filename}")
        else:
            print("Warning: One or both temp files missing.")
    
    def record_loop(self):
        """Loop to capture and write video frames while recording. No display to avoid GUI issues."""
        while self.is_recording:
            ret, frame = self.cap.read()
            if ret:
                self.video_writer.write(frame)
                # Removed cv2.imshow and cv2.waitKey to avoid GUI backend errors
            else:
                print("Failed to grab frame")
                break
            time.sleep(1 / self.fps)  # Control FPS manually
        # Ensure writer is released even if loop exits prematurely
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
    
    def run(self):
        """Main loop to listen for commands."""
        self.speak("Voice controlled recorder ready. Say 'start recording' or 'stop recording'.")
        
        try:
            while True:
                command = self.listen_for_command()
                if command:
                    if 'start recording' in command:
                        if not self.is_recording:
                            self.start_recording()
                        else:
                            self.speak("Already recording.")
                    elif 'stop recording' in command:
                        self.stop_recording()
                    else:
                        self.speak("Command not recognized. Say start or stop recording.")
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.5)
        except KeyboardInterrupt:
            self.stop_recording()
            print("Exiting...")
        finally:
            # Cleanup
            if self.cap:
                self.cap.release()
            if self.video_writer:
                self.video_writer.release()
            if hasattr(self, 'p'):
                self.p.terminate()

if __name__ == "__main__":
    recorder = VoiceControlledRecorder()
    try:
        recorder.run()
    except KeyboardInterrupt:
        recorder.stop_recording()
        print("Exiting...")