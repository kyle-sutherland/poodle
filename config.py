# config.py
# Determines whether to dump the keyword block or not
ENABLE_DUMP_KEYWORD_BLOCK: bool = False

# PyAudio configuration constants
PYAUDIO_CHANNELS = 1  # Number of audio channels
PYAUDIO_FRAMES_PER_BUFFER = 8000  # Number of frames per buffer
ENABLE_PRINT_PROMPT = False
# Logging configuration flags
ENABLE_PERFORMANCE_LOG = True  # Enable performance logging
ENABLE_ALL_PARTIAL_RESULT_LOG = True  # Log all partial results
ENABLE_ACTIVE_SPEECH_LOG = False  # Log active speech
# Paths for various data storage
PATH_PROMPT_BODIES_AUDIO = "vui/prompt_bodies_audio/"  # Path to store audio prompts
TRANSCRIPTION_PATH = "vui/body_transcriptions/"  # Path to store transcriptions
CONVERSATIONS_PATH = "core/conversations/"  # Path to store conversations
RESPONSE_LOG_PATH = "core/response_log/"  # Path to store response logs

# Transcription settings
ONLINE_TRANSCRIBE = False  # Use online transcription service
LOCAL_TRANSCRIBER_MODEL = "base"  # available models given by whisper.available_models()

# Determines whether the response should be streamed or not
# text-to-speech valid options: LOCAL, cloud, NONE
STREAM_RESPONSE = False
SPEAK = ""
VOICE = "shimmer"
AGENT_PATH = "agents/standard.json"
CHAT_MODEL = "gpt-4-1106-preview"
PRESENCE_PENALTY = 1.0
TEMPERATURE = 1.0
SOUNDS = True
KEYWORD = "computer"
LANG = "english-us"
