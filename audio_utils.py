# audio_utils.py
import os
import queue
import wave
import pyaudio
import torch.cuda
import whisper
import threading
import time
from TTS.api import TTS
import config
import event_flags as ef
from file_manager import FileManager
from vosk import Model, KaldiRecognizer
from concurrent.futures import ThreadPoolExecutor
from playsound import playsound


class KeywordDetector(threading.Thread):

    def __init__(self, keyword, audio_params=None, max_listener_threads=10):
        threading.Thread.__init__(self)
        self.stream_write_time = None
        self.keyword = keyword
        self.model = Model(lang='en-us')
        self.audio_queue = queue.Queue()
        self.keyword_listeners = []
        self.partial_listeners = []
        self.running = threading.Event()
        self.running.set()
        self.stream_write_time = None
        self.audio_params = audio_params or {}
        self.fetcher = AudioQueueFetcher(self.audio_queue, self.running, **self.audio_params)
        self.sample_rate = self.fetcher.sample_rate
        self.executor = ThreadPoolExecutor(max_listener_threads)
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)

    def run(self):
        self.fetcher.start()
        try:
            while self.running.is_set() or not self.audio_queue.empty():
                self.stream_write_time, data = self.audio_queue.get()
                if self.recognizer.AcceptWaveform(data):
                    final_result = self.recognizer.FinalResult()
                    if self.keyword in final_result:
                        self.notify_keyword_listeners(data, self.stream_write_time)
                partial_result = self.recognizer.PartialResult()
                if partial_result:
                    self.notify_partial_listeners(partial_result)
                time.sleep(0.05)
        except queue.Empty:
            print("Queue is empty.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def add_keyword_listener(self, listener_func):
        self.keyword_listeners.append(listener_func)

    def notify_keyword_listeners(self, data, stream_write_time):
        for listener in self.keyword_listeners:
            self.executor.submit(listener, self.keyword, data, stream_write_time)

    def add_partial_listener(self, listener_func):
        self.partial_listeners.append(listener_func)

    def notify_partial_listeners(self, data):
        for listener in self.partial_listeners:
            self.executor.submit(listener, data)

    def close(self):
        self.running.clear()
        self.fetcher.stop()  # use the stop method of AudioFetcher


class AudioQueueFetcher(threading.Thread):
    def __init__(self, audio_queue, running, channels=config.PYAUDIO_CHANNELS, frames_per_buffer=8000):
        threading.Thread.__init__(self)
        self.audio_queue = audio_queue
        self.running = running

        self.pa = pyaudio.PyAudio()
        self.channels = channels
        self.frames_per_buffer = frames_per_buffer
        self.default_device_info = self.pa.get_default_input_device_info()
        self.sample_rate = int(self.default_device_info['defaultSampleRate'])

    def run(self):
        stream = self.pa.open(format=config.PYAUDIO_FORMAT,
                              channels=config.PYAUDIO_CHANNELS,
                              rate=self.sample_rate,
                              input=True,
                              frames_per_buffer=config.PYAUDIO_FRAMES_PER_BUFFER)
        while self.running.is_set():
            data = stream.read(self.frames_per_buffer)
            self.audio_queue.put((time.time(), data))
            time.sleep(0.05)
        stream.stop_stream()
        stream.close()
        self.pa.terminate()

    def stop(self):
        self.running.clear()


class Transcriber:
    def __init__(self, audio_directory, transcription_directory):
        self.audio_directory = audio_directory
        self.transcription_directory = transcription_directory
        self.whisper = whisper
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = 'tiny'
        self.mod = whisper.load_model(self.model, self.device)

    def transcribe_bodies(self):
        while len(os.listdir(self.audio_directory)) != 0:
            for file in os.listdir(self.audio_directory):
                t = time.time()
                result = self.mod.transcribe(audio=f"{self.audio_directory}{file}")
                os.remove(f"{self.audio_directory}{file}")
                file = file.rstrip(".wav")
                FileManager.save_json(f"{self.transcription_directory}transcription_{file}.json", result)
                print(
                    f"transcription completed in: {time.time() - t} seconds using device: {self.device}, model: {self.model}\n")


class AudioRecorder(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.pa = pyaudio.PyAudio()
        self.default_device_info = self.pa.get_default_input_device_info()
        self.sample_rate = int(self.default_device_info['defaultSampleRate'])
        self.frames_per_buffer = 2048
        self.frames = []

    def start_recording(self):
        stream = self.pa.open(format=config.PYAUDIO_FORMAT,
                              channels=config.PYAUDIO_CHANNELS,
                              rate=self.sample_rate, input=True,
                              frames_per_buffer=self.frames_per_buffer)

        ef.recording.set()
        print("recording started")
        self.frames.clear()
        while ef.recording.is_set():
            data = stream.read(self.frames_per_buffer)
            self.frames.append(data)

    def stop_recording(self, filepath):
        ef.recording.clear()
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


class SilenceWatcher:
    def __init__(self, silence_threshold=8, silence_duration=1.5):
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.silence_counter = 0
        self.silence_start_time = None

    def check_silence(self, pr) -> bool:
        no_speech = all(pr[key] == "" for key in pr)
        if no_speech:
            self.silence_counter += 1
            if self.silence_counter >= self.silence_threshold:
                if not self.silence_start_time:
                    self.silence_start_time = time.time()
                elif time.time() - self.silence_start_time >= self.silence_duration:
                    print("silence detected")
                    return True
        else:
            self.reset()

    def reset(self):
        self.silence_counter = 0
        self.silence_start_time = None


class TextToSpeech:
    def __init__(self):
        self.file = 'voice.wav'
        self.pa = pyaudio.PyAudio()
        self.model = "tts_models/en/ljspeech/glow-tts"
        self.tts = TTS(self.model)

    def make_voice(self, text):
        if os.path.exists(self.file):
            os.remove(self.file)
        self.tts.tts_to_file(text=text, gpu=True, file_path=self.file, progress_bar=False)

    def play_voice(self):
        playsound(self.file)
