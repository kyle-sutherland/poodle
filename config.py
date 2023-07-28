# config.py

import pyaudio

TEST_FILE: str = "test_audio/Recording.wav"
PYAUDIO_FORMAT = pyaudio.paInt16
PYAUDIO_CHANNELS = 1
ENABLE_PERFORMANCE_LOG = True
ENABLE_ALL_PARTIAL_RESULT_LOG = False
ENABLE_ACTIVE_SPEECH_LOG = True

PATH_PROMPT_BODIES_AUDIO = "prompt_bodies_audio/"
