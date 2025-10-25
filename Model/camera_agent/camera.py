# This script requires the following packages to be installed:
# pip install opencv-python speechrecognition pyttsx3 pyaudio
# Note: pyaudio might require additional setup on some systems (e.g., portaudio on macOS/Linux).

import cv2
import speech_recognition as sr
import pyttsx3
import threading
import time
import os
from datetime import datetime

class VoiceControlledCamera:
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
        
        # Camera setup
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise ValueError("Could not open camera")
        
        # Photo directory
        self.photo_dir = 'photos'
        if not os.path.exists(self.photo_dir):
            os.makedirs(self.photo_dir)
    
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
    
    def take_photo(self):
        """Capture and save a photo."""
        ret, frame = self.cap.read()
        if ret:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.photo_dir, f"photo_{timestamp}.jpg")
            cv2.imwrite(filename, frame)
            self.speak("Photo taken")
            print(f"Photo saved as {filename}")
        else:
            self.speak("Failed to capture photo")
            print("Failed to grab frame")
    
    def run(self):
        """Main loop to listen for commands."""
        self.speak("Voice controlled camera ready. Say 'take photo' to capture an image.")
        
        try:
            while True:
                command = self.listen_for_command()
                if command:
                    if 'take photo' in command:
                        self.take_photo()
                    else:
                        self.speak("Command not recognized. Say take photo.")
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("Exiting...")
        finally:
            # Cleanup
            if self.cap:
                self.cap.release()

if __name__ == "__main__":
    camera = VoiceControlledCamera()
    try:
        camera.run()
    except KeyboardInterrupt:
        print("Exiting...")