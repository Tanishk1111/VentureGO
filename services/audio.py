import os
import wave
import google.cloud.speech as speech
import google.cloud.texttospeech as tts
from fastapi import UploadFile, HTTPException
from typing import Dict, Any, Optional, Tuple

from config import RATE, AUDIO_FORMAT, CHANNELS

# Initialize the clients
speech_client = speech.SpeechClient()
tts_client = tts.TextToSpeechClient()

async def transcribe_audio_file(file_path: str) -> str:
    """Transcribe audio file using Google Speech-to-Text"""
    try:
        # Read the audio file
        with open(file_path, 'rb') as audio_file:
            content = audio_file.read()
        
        # Configure request
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code="en-US",
            enable_automatic_punctuation=True,
            model="latest_long",
            use_enhanced=True
        )
        
        # Send request
        response = speech_client.recognize(config=config, audio=audio)
        
        # Extract transcript
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript
        
        return transcript
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

async def generate_speech(text: str, voice_type: str = "male") -> bytes:
    """Generate speech from text using Google Text-to-Speech"""
    try:
        # Filter unwanted words
        unwanted_words = ['asterisk', '*']
        for word in unwanted_words:
            text = text.replace(word, '')
        
        # Clean up text formatting
        text = text.replace('\n\n', ' ').replace('\n', ' ')
        
        # Configure voice
        if voice_type.lower() == "female":
            voice_name = "en-US-Chirp3-HD-Leda"
        else:
            voice_name = "en-US-Chirp3-HD-Charon"
            
        voice = tts.VoiceSelectionParams(
            language_code="en-US",
            name=voice_name
        )
        
        # Configure audio
        audio_config = tts.AudioConfig(
            audio_encoding=tts.AudioEncoding.LINEAR16,
            speaking_rate=0.98,
            pitch=0.0,
            volume_gain_db=1.0,
            effects_profile_id=["large-home-entertainment-class-device"]
        )
        
        # Generate speech
        synthesis_input = tts.SynthesisInput(text=text)
        response = tts_client.synthesize_speech(
            input=synthesis_input, 
            voice=voice, 
            audio_config=audio_config
        )
        
        return response.audio_content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech generation error: {str(e)}")

async def convert_audio_format(file: UploadFile, target_format: str = "wav") -> Tuple[str, bytes]:
    """Convert uploaded audio to required format"""
    try:
        content = await file.read()
        
        # For now, we'll just return the content as-is, assuming it's already in the right format
        # In a real implementation, you'd use a library like pydub to convert between formats
        
        return f"converted.{target_format}", content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio conversion error: {str(e)}")
