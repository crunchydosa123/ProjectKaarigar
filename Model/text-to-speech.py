"""
gemini_tts.py
Reusable module for Google Gemini Pro TTS (text-to-speech).

Features:
- Accepts text and optional parameters (voice, language, model).
- Writes MP3 output file.
- Returns the output file path.
- Can be imported in other Python files or run directly.

Usage example (from another file):
    from gemini_tts import synthesize_gemini_pro_tts
    synthesize_gemini_pro_tts("Hello world!", "output.mp3")
"""

from google.cloud import texttospeech

def synthesize_gemini_pro_tts(
    text: str,
    output_filepath: str = "output.mp3",
    language_code: str = "hi-IN",
    voice_name: str = "achernar",
    model_name: str = "gemini-2.5-pro-tts",
    speaking_rate: float = 1.0,
    pitch: float = 0.0,
) -> str:
    """
    Convert text to speech using Google Gemini Pro TTS.

    Args:
        text (str): The text to convert into speech.
        output_filepath (str): Path to save the generated MP3 file.
        language_code (str): Language code (e.g., 'hi-IN', 'en-IN').
        voice_name (str): The voice to use (e.g., 'achernar').
        model_name (str): TTS model to use ('gemini-2.5-pro-tts' by default).
        speaking_rate (float): Speech speed multiplier.
        pitch (float): Voice pitch adjustment.

    Returns:
        str: Path to the generated MP3 file.
    """
    if not text.strip():
        raise ValueError("Input text cannot be empty.")

    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name,
        model_name=model_name,
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speaking_rate,
        pitch=pitch,
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    with open(output_filepath, "wb") as out:
        out.write(response.audio_content)

    print(f"✅ Gemini Pro TTS audio saved to {output_filepath}")
    return output_filepath

if __name__ == "__main__":
    print("🎙️ Gemini Pro TTS — Text to Speech Demo")
    user_text = input("Enter text to speak: ").strip()
    if not user_text:
        print("No text entered. Exiting.")
    else:
        synthesize_gemini_pro_tts(
            text=user_text,
            output_filepath="gemini_output.mp3",
            language_code="hi-IN",
            voice_name="achernar",
        )
