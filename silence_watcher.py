# silence_watcher.py

import time

import config


class SilenceWatcher:

    def __init__(self, audio_fetcher, silence_threshold=10, silence_duration=5):
        self.audio_fetcher = audio_fetcher
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.silence_counter = 0
        self.silence_start_time = None

    def check_silence(self, no_speech):
        if no_speech:
            self.silence_counter += 1
            if self.silence_counter >= self.silence_threshold:
                print("silence detected")
                if not self.silence_start_time:
                    self.silence_start_time = time.time()
                elif time.time() - self.silence_start_time >= self.silence_duration:
                    print(f"{self.silence_duration} seconds of silence. Stopping recording.")
                    self.audio_fetcher.stop_recording(config.PATH_PROMPT_BODIES_AUDIO)
        else:
            self.reset()

    def reset(self):
        self.silence_counter = 0
        self.silence_start_time = None
