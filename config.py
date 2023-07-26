# config.py
import pyaudio

ENABLE_DUMP_KEYWORD_BLOCK: bool = False
TEST_FILE: str = "test_audio/Recording.wav"
PYAUDIO_FORMAT = pyaudio.paInt16
PYAUDIO_CHANNELS = 1
PYAUDIO_FRAMES_PER_BUFFER = 8000
