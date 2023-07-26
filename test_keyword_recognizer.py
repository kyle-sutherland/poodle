# test_keyword_recognizer.py
import queue
import time

import pytest
import threading
from keyword_recognizer import KeywordRecognizer
from mock_audio_fetcher import MockAudioFetcher
from pytest_benchmark.plugin import benchmark
import config

AUDIO_FILE = config.TEST_FILE


@pytest.fixture(params=["okay poodle"])
def recognizer_factory(request):
    keyword = request.param

    def _create_recognizer():
        recognizer = KeywordRecognizer(keyword)
        return recognizer

    return _create_recognizer


@pytest.fixture()
def fetcher_factory():
    def _create_fetcher(audio_queue, running):
        fetcher = MockAudioFetcher(audio_queue, running, AUDIO_FILE)
        fetcher.start()
        return fetcher

    return _create_fetcher


def test_keyword_recognition_with_listeners(recognizer_factory, fetcher_factory, benchmark):
    sleep_time = 5

    def dummy_listener(keyword, data):
        print(f"Keyword: {keyword}, Data: {data}")

    def do_test():
        running = threading.Event()
        running.set()
        audio_queue = queue.Queue()

        fetcher = fetcher_factory(audio_queue, running)  # get new fetcher instance
        recognizer = recognizer_factory()  # get new recognizer instance
        recognizer.audio_queue = audio_queue

        recognizer.add_listener(dummy_listener)
        recognizer.start()
        time.sleep(sleep_time)
        recognizer.run_once()
        recognizer.close()
        recognizer.join()

        # Stop the fetcher
        fetcher.stop()
        fetcher.join()
        return sleep_time

    sleep_time = benchmark(do_test)  # Run the benchmark
    print("Adjusted time: ", benchmark.stats['min'] - sleep_time)
