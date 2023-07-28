# main.py
import queue
import threading

import kd_listeners
import silence_watcher
from audio_fetcher import AudioFetcher
from keyword_detector import KeywordDetector
import time
import config


def main():
    fetcher = AudioFetcher(queue.Queue(), threading.Event(), channels=config.PYAUDIO_CHANNELS,
                           frames_per_buffer=config.PYAUDIO_FRAMES_PER_BUFFER)

    kw_detector = KeywordDetector("computer")
    kw_detector.add_keyword_listener(
        lambda: kd_listeners.kwl_start_recording_on_keyword(fetcher))
    kw_detector.add_partial_listener(lambda pr: kd_listeners.pl_no_speech(silence_watcher, pr))

    kw_detector.add_keyword_listener(kd_listeners.kwl_print_keyword_message)

    if config.ENABLE_DUMP_KEYWORD_BLOCK:
        kw_detector.add_keyword_listener(kd_listeners.kwl_dump_keyword_block)

    if config.ENABLE_ALL_PARTIAL_RESULT_LOG:
        kw_detector.add_partial_listener(kd_listeners.pl_print_all_partials)

    if config.ENABLE_ACTIVE_SPEECH_LOG:
        kw_detector.add_partial_listener(kd_listeners.pl_print_active_speech_only)

    kw_detector.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Closing the program")
        kw_detector.close()
        kw_detector.join()


if __name__ == '__main__':
    main()
