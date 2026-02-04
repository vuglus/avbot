import sys
import os
from pydub import AudioSegment
from services.speech import recognize_speech
from services.config_service import Config, load_config

config = Config(load_config())

def convert_audio_to_oga(input_path, output_path):
    """Convert audio file to WAV format with required specifications"""
    sound = AudioSegment.from_file(input_path).set_frame_rate(16000).set_channels(1)
    sound.export(output_path, format="ogg")

def test_speech_recognition(audio_file_path):
    """Test speech recognition on an audio file"""
    # Convert to WAV if needed
    if not audio_file_path.endswith('.oga'):
        wav_path = audio_file_path + ".oga"
        convert_audio_to_oga(audio_file_path, wav_path)
        audio_file_path = wav_path
        print(f"Converted audio to OGA: {audio_file_path}")
    
    # Recognize speech using Yandex SpeechKit
    try:
        transcript = recognize_speech(audio_file_path, config.getCloudKey(), config.getCloudFolder())
        print(f"Recognized text: {transcript}")
        return transcript
    except Exception as e:
        print(f"Error recognizing speech: {str(e)}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_speech_service.py <audio_file_path>")
        sys.exit(1)
    
    audio_file_path = sys.argv[1]
    
    if not os.path.exists(audio_file_path):
        print(f"Error: File {audio_file_path} does not exist")
        sys.exit(1)
    
    print(f"Processing audio file: {audio_file_path}")
    result = test_speech_recognition(audio_file_path)
    
    if result:
        print(f"Transcription result: {result}")
    else:
        print("Failed to transcribe audio file")