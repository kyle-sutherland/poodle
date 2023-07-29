import threading

import pyaudio
import wave

import config
import event_flags


class AudioRecorder(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.pa = pyaudio.PyAudio()
        self.default_device_info = self.pa.get_default_input_device_info()
        self.sample_rate = int(self.default_device_info['defaultSampleRate'])
        self.frames_per_buffer = 2048
        self.frames = []

    def create_stream(self):
        stream = self.pa.open(format=config.PYAUDIO_FORMAT,
                              channels=config.PYAUDIO_CHANNELS,
                              rate=self.sample_rate, input=True,
                              frames_per_buffer=self.frames_per_buffer)
        return stream

    def start_recording(self):
        event_flags.recording.set()
        print("recording started")
        self.frames.clear()
        stream = self.create_stream()
        while event_flags.recording.is_set():
            data = stream.read(self.frames_per_buffer)
            self.frames.append(data)

    def stop_recording(self, filepath):
        event_flags.recording.clear()
        sound_file = wave.open(filepath, "wb")
        sound_file.setnchannels(config.PYAUDIO_CHANNELS)
        sound_file.setsampwidth(self.pa.get_sample_size(pyaudio.paInt16))
        sound_file.setframerate(self.sample_rate)
        sound_file.writeframes(b''.join(self.frames))
        print("recording saved")

    def start(self):
        self.start_recording()

    def stop(self, filepath):
        self.stop_recording(filepath)

