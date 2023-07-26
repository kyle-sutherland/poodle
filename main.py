# main.py
from keyword_recognizer import KeywordRecognizer
import time
import threading
import config


def print_keyword_message(recognizer, fetcher, keyword, data, callback):
    print(f"{keyword}!!")
    if not fetcher.recording:  # Only start recording if not already
        fetcher.start_recording(time.time())  # Start recording when keyword is detected
        # Timer to stop recording after 30 seconds
        threading.Timer(30, fetcher.stop_recording).start()
    callback()


def partial_listener(recognizer, fetcher, result):

    if config.ENABLE_RESULT_LOG:
        print(f"Partial result received: {result}")

    # Check if there's silence
    if not result.strip() and fetcher.recording:
        # If a timer already exists, cancel it
        if recognizer.silence_timer:
            recognizer.silence_timer.cancel()
        # Start a new timer that will stop recording after 10 seconds of silence
        recognizer.silence_timer = threading.Timer(10, fetcher.stop_recording)
        recognizer.silence_timer.start()
    elif fetcher.recording:
        # If speech is detected and recording is ongoing, reset the timer
        if recognizer.silence_timer:
            recognizer.silence_timer.cancel()
            print("still listening")
        recognizer.silence_timer = threading.Timer(10, fetcher.stop_recording)
        recognizer.silence_timer.start()


def dump_keyword_block(fetcher, data, callback):
    # put whatever code you want here, it will run concurrently with print_keyword_message
    fetcher.dump_audio(data)  # Now you can call dump_audio from another_listener
    callback()


def print_performance_info(recognizer):
    t_detect = recognizer.get_keyword_detected_time
    t_start = recognizer.get_start_time
    t_listeners_finished = recognizer.get_listeners_finished_time

    delta_detect = t_detect - t_start if t_detect and t_start else None
    delta_listeners = t_listeners_finished - t_detect if t_listeners_finished and t_detect else None
    delta_total = t_listeners_finished - t_start if t_listeners_finished and t_start else None
    listeners_triggered = recognizer.listeners_finished_count

    print(f"Keyword detection time: {delta_detect}")
    print(f"Listener handling time: {delta_listeners}")
    print(f"Total time: {delta_total}")
    print(f"Listeners triggered: {listeners_triggered}")


def main():
    recognizer = KeywordRecognizer("okay poodle")
    fetcher = recognizer.fetcher

    recognizer.add_keyword_listener(
        lambda keyword, data, callback: print_keyword_message(recognizer, fetcher, keyword, data, callback))
    recognizer.add_partial_listener(lambda result: partial_listener(recognizer, fetcher, result))

    if config.ENABLE_DUMP_KEYWORD_BLOCK:
        recognizer.add_keyword_listener(lambda keyword, data, callback: dump_keyword_block(fetcher, data, callback))

    if config.ENABLE_PERFORMANCE_LOG:
        recognizer.add_keyword_listener(lambda keyword, data, callback: print_performance_info(recognizer))

    recognizer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print_performance_info(recognizer)
        print("Closing the program")
        recognizer.close()
        recognizer.join()


if __name__ == '__main__':
    main()
