# audio_fetcher.py

import threading
import time
import wave
from queue import Queue

import pyaudio

import config


class AudioFetcher(threading.Thread):
    def __init__(self, audio_queue, running, sample_rate, channels=1, frames_per_buffer=8000):
        threading.Thread.__init__(self)
        self.audio_queue = audio_queue
        self.running = running

        self.pa = pyaudio.PyAudio()
        self.channels = channels
        self.frames_per_buffer = frames_per_buffer
        self.default_device_info = self.pa.get_default_input_device_info()
        self.sample_rate = int(self.default_device_info['defaultSampleRate'])
        self.recording = False
        self.wave_file = None
        self.dump_queue = Queue()
        threading.Thread(target=self._dump_worker).start()

    @property
    def get_sample_rate(self):
        return self.sample_rate

    @property
    def get_device_info(self):
        return self.default_device_info

    def _dump_worker(self):
        while True:
            item = self.dump_queue.get()
            if item is None:
                break  # End worker
            timestamp, data = item
            self.wave_file.writeframes(data)
            self.dump_queue.task_done()
            print("dump_queue")

    def start_recording(self, timestamp):
        filename = f"prompt_bodies_audio/dump_{timestamp}.wav"
        try:
            self.wave_file = wave.open(filename, "wb")
            self.wave_file.setnchannels(self.channels)
            self.wave_file.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
            self.wave_file.setframerate(self.sample_rate)
            self.recording = True
        except Exception as e:
            print(f"An error occurred while opening the file {filename}: {e}")
            self.wave_file = None

    def stop_recording(self):
        self.recording = False
        if self.wave_file is not None:
            self.wave_file.close()
            self.wave_file = None
            print("body recorded")

    def dump_audio(self, data, filename="audio_dumps/dump.raw"):
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(data)

    def run(self):
        pa = pyaudio.PyAudio()
        stream = pa.open(format=config.PYAUDIO_FORMAT,
                         channels=config.PYAUDIO_CHANNELS,
                         rate=self.sample_rate,
                         input=True,
                         frames_per_buffer=config.PYAUDIO_FRAMES_PER_BUFFER)
        while self.running.is_set():
            data = stream.read(2000)
            self.audio_queue.put((time.time(), data))
            if self.recording:
                self.dump_queue.put((time.time(), data))
        stream.close()

    def stop(self):
        self.running.clear()
