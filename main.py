# main.py
from keyword_recognizer import KeywordRecognizer
import time
import config


def print_keyword_message(keyword, data, callback):
    print(f"{keyword}!!")
    callback()


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
    recognizer.add_keyword_listener(print_keyword_message)

    if config.ENABLE_DUMP_KEYWORD_BLOCK:
        recognizer.add_keyword_listener(dump_keyword_block)

    if config.ENABLE_PERFORMANCE_LOG:
        recognizer.add_keyword_listener(print_performance_info)

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
