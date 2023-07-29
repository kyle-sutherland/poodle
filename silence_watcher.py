# silence_watcher.py

import time


class SilenceWatcher:
    def __init__(self, silence_threshold=12, silence_duration=4):
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
