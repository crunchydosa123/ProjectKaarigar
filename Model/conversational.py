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
from google import genai
from google.genai.types import LiveConnectConfig, HttpOptions, Modality, Content, Part

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
CHUNK_SIZE = 1024

# Choose if you want to use VertexAI or Gemini Developer API
use_vertexai = True  # Set to True for Vertex AI, False for Gemini Developer API (Google AI Studio API_KEY)
PROJECT_ID = 'karigar-475215'  # set this value with proper Project ID if you plan to use Vertex AI

# System prompt for Karigar information collection
SYSTEM_PROMPT = """You are an AI interviewer collecting information about artisans (Karigars) for the Karigar project. 

Your role is to ASK questions and LISTEN to the user's answers. DO NOT answer the questions yourself.

Information to collect:
1. Karigar's Name
2. Type of Products/Crafts they make
3. Location/Address (City, State)
4. Years of Experience
5. Price Range of their products
6. Specialization/Unique Skills
7. Materials Used
8. Contact Information (Phone/Email if available)
9. Any awards or recognition received
10. Workshop/Business Name (if any)

Instructions:
- Start by greeting and explaining you'll ask questions about their craft/business
- Ask ONE question at a time
- Wait for their answer before asking the next question
- Be conversational and friendly
- If an answer is unclear, politely ask them to clarify
- Keep track of what information you've collected
- When you have ALL 10 pieces of information, say EXACTLY: "INTERVIEW_COMPLETE" followed by a JSON summary

When complete, respond with:
"Thank you for providing all the details. INTERVIEW_COMPLETE
{
  "name": "value from user",
  "products": "value from user",
  "location": "value from user",
  "experience_years": "value from user",
  "price_range": "value from user",
  "specialization": "value from user",
  "materials": "value from user",
  "contact": "value from user",
  "awards": "value from user",
  "business_name": "value from user"
}"

Remember: You ASK questions, the user ANSWERS. Never provide mock or example data.
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
    
    async def listen_audio(self):
        """Captures audio from microphone and queues it for sending."""
        # Get default microphone
        mic_info = pya.get_default_input_device_info()
        
        # Open microphone stream
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
        
        # Continuously read audio chunks from microphone
        while not self.conversation_complete:
            try:
                data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
                await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
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
                        await self.audio_in_queue.put(data)
                    
                    # Handle text (if model includes it)
                    if text := response.text:
                        print("Gemini:", text)
                        self.full_transcript.append(text)
                        
                        # Check if conversation is complete
                        if "INTERVIEW_COMPLETE" in text:
                            self.conversation_complete = True
                            # Extract JSON from text
                            self.extract_information(text)
                            print("\n✓ All information collected! Processing...")
                
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
                continue
            except Exception as e:
                if not self.conversation_complete:
                    print(f"Audio play error: {e}")
                break
        
        stream.close()
    
    async def send_realtime(self):
        """Sends microphone audio to Gemini API."""
        while not self.conversation_complete:
            try:
                msg = await asyncio.wait_for(
                    self.out_queue.get(), 
                    timeout=1.0
                )
                await self.session.send(input=msg)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                if not self.conversation_complete:
                    print(f"Send error: {e}")
                break
    
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
            "price_range": "💰 Price Range",
            "specialization": "⭐ Specialization",
            "materials": "🔨 Materials Used",
            "contact": "📞 Contact Information",
            "awards": "🏆 Awards/Recognition",
            "business_name": "🏪 Business/Workshop Name"
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
        
        print("\n" + "="*70)
        
        # Save to JSON file
        output_file = "karigar_info.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.collected_info, f, indent=2, ensure_ascii=False)
            print(f"💾 Information saved to: {output_file}")
        except Exception as e:
            print(f"❌ Could not save to file: {e}")
        
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
                print("  • Use headphones to prevent audio feedback")
                print("\n🎤 Starting interview...\n")
                
                # Start all tasks
                send_task = tg.create_task(self.send_realtime())
                listen_task = tg.create_task(self.listen_audio())
                receive_task = tg.create_task(self.receive_audio())
                play_task = tg.create_task(self.play_audio())
                
                # Wait for conversation to complete
                while not self.conversation_complete:
                    await asyncio.sleep(1)
                
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