# event_flags.py
import threading

# Event flag indicating that the system is currently listening
listening = threading.Event()

# Event flag indicating that the system is currently replying
replying = threading.Event()

# Event flag indicating silence detection
silence = threading.Event()

# Event flag indicating that the system is currently recording
recording = threading.Event()

# Event flag indicating that the system is currently transcribing
transcribing = threading.Event()

# Event flag indicating that the system has finished transcribing
transcribed = threading.Event()

# Event flag indicating that the system is currently speaking or playing back audio
speaking = threading.Event()

# Time at which the stream was last written to
stream_write_time: float = 0
