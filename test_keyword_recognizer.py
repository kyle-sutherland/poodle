# test_keyword_recognizer.py

import pytest
import wave
import queue
import time
import threading
from keyword_recognizer import KeywordRecognizer
import config  # Import the config module

AUDIO_FILE = config.TEST_FILE


def read_wave_data(filename, chunk_size=1024):
    """Reads audio data from a WAV file in chunks"""
    with wave.open(filename, 'rb') as f:
        while True:
            data = f.readframes(chunk_size)
            if not data:
                break
            yield data


def refill_queue(queue, audio_data_generator, chunk_size, framerate, stop_event):
    """Constantly refills the queue with audio data until a stop event is set."""
    for chunk in audio_data_generator:
        if stop_event.is_set():
            break
        queue.put((time.time(), chunk))
        time.sleep(chunk_size / framerate)


def prepare_audio_queue(file_path):
    audio_data_generator = read_wave_data(file_path)
    q = queue.Queue()
    with wave.open(file_path, 'rb') as f:
        chunk_size = 1024
        framerate = f.getframerate()

    stop_event = threading.Event()
    refill_thread = threading.Thread(target=refill_queue,
                                     args=(q, audio_data_generator, chunk_size, framerate, stop_event))
    refill_thread.start()

    return q, stop_event, refill_thread, framerate


@pytest.fixture(params=[
    {"channels": 1, "frames_per_buffer": 8000},
    {"channels": 2, "frames_per_buffer": 16000},
])
def recognizer(request):
    q, stop_event, refill_thread, sample_rate = prepare_audio_queue(AUDIO_FILE)

    r = KeywordRecognizer("okay poodle")
    r.audio_queue = q  # replace recognizer's queue with our queue filled with test data
    r.rate = sample_rate  # use sample rate from the audio file

    r.start()

    original_setting = config.ENABLE_DUMP_KEYWORD_BLOCK
    config.ENABLE_DUMP_KEYWORD_BLOCK = False  # Disable block dumping during tests
    yield r  # this is where the test function will execute
    r.close()
    r.join()
    config.ENABLE_DUMP_KEYWORD_BLOCK = original_setting  # Revert the setting after test

    stop_event.set()  # Signal the refill thread to stop
    refill_thread.join()  # Wait for the refill thread to finish


def test_keyword_recognition_default_params(benchmark):
    # Prepare audio data queue
    q, stop_event, refill_thread, sample_rate = prepare_audio_queue(AUDIO_FILE)

    # Create recognizer with default parameters
    recognizer = KeywordRecognizer("okay poodle")
    recognizer.audio_queue = q  # replace recognizer's queue with our queue filled with test data
    recognizer.rate = sample_rate  # use sample rate from the audio file

    # Start recognizer
    recognizer.start()

    # Use a wrapper function to break out of the recognizer's infinite loop after a set number of iterations
    def wrapper():
        for _ in range(10):  # Adjust this number as needed
            recognizer.run_once()  # This hypothetical method processes a single chunk of audio data

    # Benchmark the wrapper function
    benchmark(wrapper)

    # Close recognizer after benchmark
    recognizer.close()
    recognizer.join()

    stop_event.set()  # Signal the refill thread to stop
    refill_thread.join()  # Wait for the refill thread to finish


def test_keyword_recognition(recognizer, benchmark):
    # Use a wrapper function to break out of the recognizer's infinite loop after a set number of iterations
    def wrapper():
        for _ in range(10):  # Adjust this number as needed
            recognizer.run_once()  # This hypothetical method processes a single chunk of audio data

    # Benchmark the wrapper function
    benchmark(wrapper)
