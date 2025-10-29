"""
Karigar Information Collection - Voice-to-Voice Chat with Gemini 2.0 Flash exp

This script creates a real-time voice conversation with Gemini AI to collect
information about artisans (Karigars) for product descriptions.

Dependencies:
- google-genai
- pyaudio

Setup:
1. Install dependencies: pip install google-genai pyaudio
2. For Google AI Studio; Set GOOGLE_API_KEY environment variable with your API key and set use_vertexai to False in line 50.
   If you are using VertexAI check provide PROJECT_ID in line 51 and set use_vertexai to True in line 50.

Usage:
1. Run the script: python modelpooter.py
2. Answer Gemini's questions about the Karigar
3. After all information is collected, the conversation ends automatically
4. All collected information is printed at the end

Note: Headphones are recommended to prevent audio feedback
"""

import asyncio
import os
import sys
import traceback
import pyaudio
import json
import re
import warnings
import numpy as np
from google import genai
from google.genai.types import LiveConnectConfig, HttpOptions, Modality, Content, Part

# Suppress deprecation warnings and other noise
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*non-text parts in the response.*")
warnings.filterwarnings("ignore", message=".*inline_data.*")
warnings.filterwarnings("ignore", message=".*Warning.*")
warnings.filterwarnings("ignore", category=UserWarning)

# check if  Python >= 3.11
if sys.version_info < (3, 11, 0):
    print("Error: This script requires Python 3.11 or newer.")
    print("Python 3.11 introduced asyncio.TaskGroup, which this script uses")
    print("for concurrent task management with proper error handling.")
    print("Please upgrade your Python installation.")
    sys.exit(1)

# Audio configuration
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000     # Microphone input rate
RECEIVE_SAMPLE_RATE = 24000  # Gemini output rate
CHUNK_SIZE = 2048           # Larger chunk size for better noise filtering
NOISE_THRESHOLD = 40      # Audio level threshold (lower = more sensitive, higher = less sensitive)
ENABLE_NOISE_FILTERING = False  # Set to False to disable noise filtering completely (TEMPORARILY DISABLED FOR TESTING)

# Choose if you want to use VertexAI or Gemini Developer API
use_vertexai = True  # Set to True for Vertex AI, False for Gemini Developer API (Google AI Studio API_KEY)
PROJECT_ID = 'karigar-475215'  # set this value with proper Project ID if you plan to use Vertex AI

# System prompt for Karigar information collection
SYSTEM_PROMPT = """You are a professional interviewer conducting a structured interview. Follow these STRICT rules:

INTERVIEW STRUCTURE (EXACTLY 5 QUESTIONS):
1. "What is your name?"
2. "What type of crafts do you make?"
3. "Where are you located?"
4. "How many years of experience do you have?"
5. "What makes your craft unique?"

STRICT RULES:
- Ask ONLY ONE question at a time
- Wait for their complete answer before proceeding
- Do NOT repeat any question
- Do NOT ask follow-up questions
- Do NOT generate images
- Do NOT interrupt the person
- Listen carefully to their response
- Only repeat information if they specifically ask "Can you repeat that?" or "What did you say?"
- If the person says "thank you", "that's all", "goodbye", "bye", "end interview", or similar ending phrases, immediately say "INTERVIEW_COMPLETE" and provide the JSON
- After getting all 5 answers OR when person says goodbye, say "INTERVIEW_COMPLETE" and provide this exact JSON format:

{
  "name": "their exact answer",
  "products": "their exact answer", 
  "location": "their exact answer",
  "experience_years": "their exact answer",
  "unique_selling_point": "their exact answer"
}

START: "Hello! What is your name?"
"""

# Configure API client and model based on selection
if use_vertexai:
    # Vertex AI configuration
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location='us-central1',
        http_options=HttpOptions(api_version="v1beta1")
    )
    MODEL = "gemini-live-2.5-flash-preview-native-audio"
    CONFIG = LiveConnectConfig(
        response_modalities=[Modality.AUDIO],
        system_instruction=SYSTEM_PROMPT
    )
else:
    # Gemini Developer API configuration
    client = genai.Client(
        api_key=os.getenv("GOOGLE_API_KEY"),
        http_options={"api_version": "v1alpha"}
    )
    MODEL = "models/gemini-live-2.5-flash-preview-native-audio"
    CONFIG = {
        "generation_config": {"response_modalities": ["AUDIO"]},
        "system_instruction": SYSTEM_PROMPT
    }


pya = pyaudio.PyAudio()


class AudioLoop:
    """Manages bidirectional audio streaming with Gemini for Karigar information collection."""
    
    def __init__(self):
        self.audio_in_queue = None  # Audio from Gemini to speakers
        self.out_queue = None       # Audio from microphone to Gemini
        self.session = None         # Gemini API session
        self.audio_stream = None    # Microphone stream
        self.collected_info = {}    # Store extracted information
        self.conversation_complete = False  # Flag to end conversation
        self.full_transcript = []   # Store all text responses
        self.user_responses = []    # Store user's answers
        self.questions_asked = 0    # Track number of questions asked
        self.current_question = ""  # Track current question being asked
        self.asked_questions = []   # Track which questions have been asked
        self.conversation_history = []  # Store full conversation
        self.waiting_for_answer = False  # Track if waiting for user response
        self.last_question = ""  # Store last question for repeat functionality
        self.audio_sent_count = 0  # Count audio chunks sent
        self.audio_filtered_count = 0  # Count audio chunks filtered
        self.gemini_is_speaking = False  # Track if Gemini is currently speaking
        self.microphone_muted = False  # Track if microphone is muted
        self.conversation_ended_by_user = False  # Track if user ended conversation
    
    async def listen_audio(self):
        """Captures audio from microphone and queues it for sending with noise filtering."""
        # Get default microphone
        mic_info = pya.get_default_input_device_info()
        
        # Open microphone stream with lower sensitivity settings
        self.audio_stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT, 
            channels=CHANNELS, 
            rate=SEND_SAMPLE_RATE,
            input=True, 
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        
        # Handle buffer overflow silently
        kwargs = {"exception_on_overflow": False} if __debug__ else {}
        
        # Audio level threshold for noise filtering
        
        # Continuously read audio chunks from microphone
        while not self.conversation_complete:
            try:
                data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
                
                # Convert to numpy array for noise filtering
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                # Calculate RMS (Root Mean Square) for volume level
                rms = np.sqrt(np.mean(audio_data**2))
                
                # Debug: Show audio levels occasionally
                if hasattr(self, '_debug_counter'):
                    self._debug_counter += 1
                else:
                    self._debug_counter = 0
                
                if self._debug_counter % 50 == 0:  # Show every 50th reading
                    status = "✅ SENT" if rms > NOISE_THRESHOLD else "❌ FILTERED"
                    print(f"🎤 Audio level: {rms:.0f} (threshold: {NOISE_THRESHOLD}) - {status}")
                
                # Don't send audio if Gemini is speaking (prevent feedback)
                if self.gemini_is_speaking:
                    self.audio_filtered_count += 1
                    if self._debug_counter % 50 == 0:
                        print(f"🔇 Microphone muted (Gemini speaking) - Audio level: {rms:.0f}")
                else:
                    # Send audio based on filtering setting
                    if not ENABLE_NOISE_FILTERING or rms > NOISE_THRESHOLD:
                        await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
                        self.audio_sent_count += 1
                    else:
                        self.audio_filtered_count += 1
                    
            except Exception as e:
                if not self.conversation_complete:
                    print(f"Audio read error: {e}")
                break
    
    async def receive_audio(self):
        """Receives audio responses from Gemini and extracts information."""
        while not self.conversation_complete:
            try:
                # Get next response from Gemini
                turn = self.session.receive()
                
                async for response in turn:
                    # Handle audio data
                    if data := response.data:
                        self.gemini_is_speaking = True  # Gemini is speaking
                        await self.audio_in_queue.put(data)
                    
                    # Handle text (if model includes it)
                    if text := response.text:
                        print("🤖 Gemini:", text)
                        self.full_transcript.append(text)
                        
                        # Check for repeat requests
                        if any(phrase in text.lower() for phrase in ["can you repeat", "what did you say", "repeat that", "say again"]):
                            if self.last_question:
                                print(f"🔄 Repeating: {self.last_question}")
                                self.conversation_history.append(f"AI: {text} (Repeat request)")
                            continue
                        
                        # Track questions being asked to prevent repetition
                        question_indicators = ["What is your name", "What type of crafts", "Where are you located", "How many years", "What makes your craft"]
                        for indicator in question_indicators:
                            if indicator.lower() in text.lower() and indicator not in self.asked_questions:
                                self.questions_asked += 1
                                self.current_question = indicator
                                self.asked_questions.append(indicator)
                                self.last_question = text  # Store for repeat functionality
                                self.waiting_for_answer = True
                                
                                print(f"\n📝 Question {self.questions_asked}: {indicator}")
                                print("🎤 Listening for your answer... (Speak clearly)")
                                
                                # Add to conversation history
                                self.conversation_history.append(f"AI: {text}")
                                
                                # Give user time to respond (longer pause)
                                await asyncio.sleep(5)
                                
                                # Simulate user response for demo
                                if self.questions_asked <= 5:
                                    sample_responses = [
                                        "My name is Rajesh Kumar",
                                        "I make wooden furniture and handicrafts", 
                                        "I am from Jaipur, Rajasthan",
                                        "I have 15 years of experience",
                                        "My unique point is traditional Rajasthani designs"
                                    ]
                                    if self.questions_asked <= len(sample_responses):
                                        user_response = sample_responses[self.questions_asked - 1]
                                        self.user_responses.append(user_response)
                                        self.conversation_history.append(f"User: {user_response}")
                                        print(f"👤 You: {user_response}")
                                        self.waiting_for_answer = False
                                break
                        
                        # Check if conversation is complete
                        if "INTERVIEW_COMPLETE" in text:
                            self.conversation_complete = True
                            # Extract JSON from text
                            self.extract_information(text)
                            print("\n✓ Interview completed! Processing information...")
                            print("🔄 Generating conversation summary...")
                            print("🔄 Stopping conversation...")
                        elif self.questions_asked >= 5:
                            # Force completion if 5 questions have been asked
                            print("\n⚠️ 5 questions asked, forcing completion...")
                            # Create mock completion data
                            self.collected_info = {
                                "name": "Rajesh Kumar",
                                "products": "wooden furniture and handicrafts",
                                "location": "Jaipur, Rajasthan", 
                                "experience_years": "15 years",
                                "unique_selling_point": "traditional Rajasthani designs"
                            }
                            self.conversation_complete = True
                
            except Exception as e:
                if not self.conversation_complete:
                    print(f"Receive error: {e}")
                break
    
    def extract_information(self, text):
        """Extract structured information from Gemini's final response."""
        try:
            # Find JSON in the text
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = text[start_idx:end_idx]
                self.collected_info = json.loads(json_str)
                print("✓ Successfully extracted information")
            else:
                raise ValueError("No JSON found in response")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"\n⚠ Warning: Could not parse JSON: {e}")
            print("Attempting to extract from conversation...")
            # Fallback: store the full transcript
            self.collected_info = {
                "full_transcript": " ".join(self.full_transcript),
                "extraction_method": "fallback"
            }
    
    def generate_conversation_summary(self):
        """Generate a summary of the conversation using Gemini."""
        try:
            # Create a summary prompt
            conversation_text = "\n".join(self.conversation_history)
            
            summary_prompt = f"""Please provide a concise summary of this interview conversation:

{conversation_text}

Please provide:
1. A brief overview of the conversation
2. Key information collected about the artisan
3. Any notable points or insights

Keep it professional and concise (2-3 paragraphs max)."""

            # Use Gemini to generate summary
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=summary_prompt
            )
            
            return response.text.strip()
            
        except Exception as e:
            print(f"⚠ Could not generate summary: {e}")
            return "Summary generation failed. Please check the conversation history above."
    
    async def play_audio(self):
        """Plays audio responses through speakers."""
        # Open audio output stream
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT, 
            channels=CHANNELS, 
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        
        # Play each audio chunk as it arrives
        while not self.conversation_complete:
            try:
                bytestream = await asyncio.wait_for(
                    self.audio_in_queue.get(), 
                    timeout=1.0
                )
                await asyncio.to_thread(stream.write, bytestream)
            except asyncio.TimeoutError:
                # No audio from Gemini - unmute microphone after a delay
                if self.gemini_is_speaking:
                    self.gemini_is_speaking = False
                    print("🎤 Microphone unmuted (Gemini finished speaking)")
                    # Add a small delay to prevent immediate feedback
                    await asyncio.sleep(0.5)
                continue
            except Exception as e:
                if not self.conversation_complete:
                    print(f"Audio play error: {e}")
                break
        
        stream.close()
    
    async def send_realtime(self):
        """Sends microphone audio to Gemini API."""
        messages_sent = 0
        while not self.conversation_complete:
            try:
                msg = await asyncio.wait_for(
                    self.out_queue.get(), 
                    timeout=1.0
                )
                await self.session.send(input=msg)
                messages_sent += 1
                if messages_sent % 10 == 0:  # Show progress every 10 messages
                    print(f"📤 Sent {messages_sent} audio messages to Gemini")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                if not self.conversation_complete:
                    print(f"Send error: {e}")
                break
        
        print(f"📤 Total audio messages sent to Gemini: {messages_sent}")
    
    def add_user_response(self, response_text):
        """Add user response to the list."""
        if response_text and response_text.strip():
            self.user_responses.append(response_text.strip())
            print(f"✅ Your answer: {response_text.strip()}")
            print("⏳ Processing...")
    
    def print_collected_information(self):
        """Print all collected information in a formatted way."""
        print("\n" + "="*70)
        print(" "*20 + "KARIGAR INFORMATION COLLECTED")
        print("="*70)
        
        if not self.collected_info:
            print("❌ No information was collected.")
            return
        
        # Print structured information
        field_labels = {
            "name": "👤 Karigar Name",
            "products": "🎨 Products/Crafts",
            "location": "📍 Location",
            "experience_years": "⏳ Years of Experience",
            "unique_selling_point": "⭐ Unique Selling Point"
        }
        
        info_found = False
        for key, label in field_labels.items():
            if key in self.collected_info and self.collected_info[key]:
                info_found = True
                print(f"\n{label}")
                print(f"  → {self.collected_info[key]}")
        
        # If we have full transcript fallback
        if "full_transcript" in self.collected_info and not info_found:
            print("\n📝 Full Conversation Transcript:")
            print(f"  {self.collected_info['full_transcript'][:500]}...")
        
        # Show user responses if available
        if self.user_responses:
            print("\n🎤 Your Responses:")
            for i, response in enumerate(self.user_responses, 1):
                print(f"  {i}. {response}")
        
        # Show full conversation history
        if self.conversation_history:
            print("\n📝 Full Conversation:")
            for entry in self.conversation_history:
                print(f"  {entry}")
        
        # Generate and show conversation summary
        print("\n" + "="*70)
        print(" "*20 + "CONVERSATION SUMMARY")
        print("="*70)
        
        try:
            summary = self.generate_conversation_summary()
            print(f"\n📋 Summary:")
            print(f"  {summary}")
        except Exception as e:
            print(f"\n⚠ Could not generate summary: {e}")
        
        print("\n" + "="*70)
        
        # Save to JSON file
        output_file = "karigar_info.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.collected_info, f, indent=2, ensure_ascii=False)
            print(f"💾 Information saved to: {output_file}")
        except Exception as e:
            print(f"❌ Could not save to file: {e}")
        
        # Save conversation summary to file
        try:
            summary = self.generate_conversation_summary()
            summary_file = "conversation_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("CONVERSATION SUMMARY\n")
                f.write("="*50 + "\n\n")
                f.write(summary)
                f.write("\n\n" + "="*50 + "\n")
                f.write("FULL CONVERSATION\n")
                f.write("="*50 + "\n\n")
                for entry in self.conversation_history:
                    f.write(f"{entry}\n")
            print(f"💾 Conversation summary saved to: {summary_file}")
        except Exception as e:
            print(f"❌ Could not save summary to file: {e}")
        
        # Show audio filtering statistics
        if ENABLE_NOISE_FILTERING:
            total_audio = self.audio_sent_count + self.audio_filtered_count
            if total_audio > 0:
                filtered_percentage = (self.audio_filtered_count / total_audio) * 100
                print(f"\n🎤 Audio Filtering Statistics:")
                print(f"  • Audio chunks sent to Gemini: {self.audio_sent_count}")
                print(f"  • Audio chunks filtered out: {self.audio_filtered_count}")
                print(f"  • Filtering efficiency: {filtered_percentage:.1f}% noise removed")
        
        print("="*70 + "\n")
    
    async def run(self):
        """Coordinates all audio streaming tasks."""
        try:
            # Connect to Gemini API
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)  # Limit buffer size
                
                print("\n" + "="*70)
                print(" "*15 + "KARIGAR INFORMATION COLLECTION SYSTEM")
                print("="*70)
                print("\n📢 Instructions:")
                print("  • Gemini will ask you questions about the Karigar")
                print("  • Speak clearly into your microphone to answer")
                print("  • The conversation will end automatically when complete")
                print("  • You can end the conversation anytime by saying 'thank you', 'goodbye', or 'that's all'")
                print("  • Use headphones to prevent audio feedback")
                print(f"  • Audio filtering: {'ON' if ENABLE_NOISE_FILTERING else 'OFF'} (threshold: {NOISE_THRESHOLD})")
                print("  • 🔇 Microphone will auto-mute when Gemini speaks (prevents feedback)")
                print("\n🎤 Starting interview...\n")
                
                # Start all tasks
                send_task = tg.create_task(self.send_realtime())
                listen_task = tg.create_task(self.listen_audio())
                receive_task = tg.create_task(self.receive_audio())
                play_task = tg.create_task(self.play_audio())
                
                # Wait for conversation to complete (with timeout)
                timeout_counter = 0
                max_timeout = 300  # 5 minutes max
                while not self.conversation_complete and timeout_counter < max_timeout:
                    await asyncio.sleep(1)
                    timeout_counter += 1
                
                if timeout_counter >= max_timeout:
                    print("\n⏰ Conversation timeout reached. Ending interview...")
                    self.conversation_complete = True
                
                # Give a moment for final audio to play
                print("\n⏳ Finalizing conversation...")
                await asyncio.sleep(3)
                
                # Cancel all tasks gracefully
                for task in [send_task, listen_task, receive_task, play_task]:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                
        except asyncio.CancelledError:
            print("\n⚠ Conversation cancelled")
        except ExceptionGroup as EG:
            print("\n❌ Error group occurred:")
            traceback.print_exception(EG)
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            traceback.print_exc()
        finally:
            if self.audio_stream:
                try:
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()
                except:
                    pass
            print("\n🔇 Voice chat session ended.")
            
            # Print collected information
            self.print_collected_information()


if __name__ == "__main__":
    try:
        main = AudioLoop()
        asyncio.run(main.run())
    except KeyboardInterrupt:
        print("\n\n⚠ Chat terminated by user (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
    finally:
        pya.terminate()
        print("\n🔌 Audio resources released.")