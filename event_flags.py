import threading

listening = threading.Event()
replying = threading.Event()
silence = threading.Event()
recording = threading.Event()
transcribing = threading.Event()
transcribed = threading.Event()
