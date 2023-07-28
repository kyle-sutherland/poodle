import pyaudio

import config
from Singleton import Singleton


class AudioStreamManager(Singleton):
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.input_streams = []
        self.output_streams = []
        self.input_device_info = self.pa.get_default_input_device_info()
        self.output_device_info = self.pa.get_default_output_device_info()

    def open_input_stream(self, channels, rate, frames_per_buffer=1024):
        stream = self.pa.open(format=config.PYAUDIO_FORMAT,
                              channels=channels,
                              rate=rate,
                              input=True,
                              frames_per_buffer=frames_per_buffer)
        self.input_streams.append(stream)
        return stream

    def open_output_stream(self, channels, rate, frames_per_buffer=1024):
        stream = self.pa.open(format=config.PYAUDIO_FORMAT,
                              channels=channels,
                              rate=rate,
                              output=True,
                              frames_per_buffer=frames_per_buffer)
        self.output_streams.append(stream)
        return stream

    def close_input_stream(self, stream):
        stream.stop_stream()
        stream.close()
        self.input_streams.remove(stream)

    def close_output_stream(self, stream):
        stream.stop_stream()
        stream.close()
        self.output_streams.remove(stream)

    def close_all_streams(self):
        for stream in self.input_streams + self.output_streams:
            stream.stop_stream()
            stream.close()
        self.input_streams = []
        self.output_streams = []

    def __del__(self):
        self.close_all_streams()
        self.pa.terminate()
