# config.py
import time

import pyaudio

ENABLE_DUMP_KEYWORD_BLOCK: bool = False
TEST_FILE: str = "test_audio/Recording.wav"
PYAUDIO_FORMAT = pyaudio.paInt16
PYAUDIO_CHANNELS = 1
PYAUDIO_FRAMES_PER_BUFFER = 8000
ENABLE_PERFORMANCE_LOG = True
ENABLE_ALL_PARTIAL_RESULT_LOG = False
ENABLE_ACTIVE_SPEECH_LOG = False

PATH_PROMPT_BODIES_AUDIO = f"prompt_bodies_audio/body_{time.time()}.wav"
