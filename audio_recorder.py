import threading

import pyaudio
import wave

import config
import state_controller
from audio_stream_manager import AudioStreamManager

asm = AudioStreamManager()


class AudioRecorder(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.default_device_info = asm.input_device_info
        self.sample_rate = int(self.default_device_info['defaultSampleRate'])
        self.channels = 1
        self.frames = []

    def start_recording(self):
        state_controller.recording.set()
        print("recording started")
        self.frames.clear()
        stream = asm.open_input_stream(channels=self.channels, rate=self.sample_rate)
        while state_controller.recording.is_set():
            data = stream.read(1024)
            self.frames.append(data)

    def stop_recording(self, filepath):
        state_controller.recording.clear()
        sound_file = wave.open(filepath, "wb")
        sound_file.setnchannels(config.PYAUDIO_CHANNELS)
        sound_file.setsampwidth(asm.pa.get_sample_size(pyaudio.paInt16))
        sound_file.setframerate(self.sample_rate)
        sound_file.writeframes(b''.join(self.frames))
        print("recording saved")

    def start(self):
        self.start_recording()

    def stop(self, filepath):
        asm.close_input_stream(asm.input_streams[1])
        self.stop_recording(filepath)
