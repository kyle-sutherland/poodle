# main.py
from keyword_recognizer import KeywordRecognizer
import time
import config


def print_keyword_message(keyword, data):
    print(f"{keyword}!!")


def dump_keyword_block(fetcher, data):
    # put whatever code you want here, it will run concurrently with print_keyword_message
    fetcher.dump_audio(data)  # Now you can call dump_audio from another_listener


def main():
    recognizer = KeywordRecognizer("computer")
    recognizer.add_keyword_listener(print_keyword_message)

    if config.ENABLE_DUMP_KEYWORD_BLOCK:
        recognizer.add_keyword_listener(dump_keyword_block)

    recognizer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Closing the program")
        recognizer.close()
        recognizer.join()


if __name__ == '__main__':
    main()
