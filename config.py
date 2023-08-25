# config.py
import pyaudio

# Determines whether to dump the keyword block or not
ENABLE_DUMP_KEYWORD_BLOCK: bool = False

# PyAudio configuration constants
PYAUDIO_FORMAT = pyaudio.paInt16  # Format of the audio chunks
PYAUDIO_CHANNELS = 1  # Number of audio channels
PYAUDIO_FRAMES_PER_BUFFER = 8000  # Number of frames per buffer

# Logging configuration flags
ENABLE_PERFORMANCE_LOG = False  # Enable performance logging
ENABLE_ALL_PARTIAL_RESULT_LOG = False  # Log all partial results
ENABLE_ACTIVE_SPEECH_LOG = False  # Log active speech

# Paths for various data storage
PATH_PROMPT_BODIES_AUDIO = "prompt_bodies_audio/"  # Path to store audio prompts
TRANSCRIPTION_PATH = "body_transcriptions/"  # Path to store transcriptions
CONVERSATIONS_PATH = 'conversations/'  # Path to store conversations
RESPONSE_LOG_PATH = 'response_log/'  # Path to store response logs

# Transcription settings
ONLINE_TRANSCRIBE = False  # Use online transcription service

# Determines whether the response should be streamed or not
STREAM_RESPONSE = False
