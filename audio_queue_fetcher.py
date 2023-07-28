import threading
import time
import wave
import pyaudio
import config
from audio_stream_manager import AudioStreamManager

asm = AudioStreamManager()


class AudioQueueFetcher(threading.Thread):
    def __init__(self, audio_queue, running):
        threading.Thread.__init__(self)
        self.audio_queue = audio_queue
        self.running = running
        self.frames_per_buffer = 8000
        self.default_device_info = asm.input_device_info
        self.sample_rate = int(self.default_device_info['defaultSampleRate'])
        self.channels = 1
        self.stream = asm.open_input_stream(1, self.sample_rate, self.frames_per_buffer)

    def run(self):
        while self.running.is_set():
            data = self.stream.read(self.frames_per_buffer)
            self.audio_queue.put((time.time(), data))
        asm.close_input_stream(self.stream)

    def stop(self):
        self.running.clear()
