# test_keyword_recognizer.py

import pytest
from keyword_recognizer import KeywordRecognizer
import queue
import time
import wave
import pyaudio
import config


def read_wave_data(filename):
    """Reads audio data from a WAV file"""
    with wave.open(filename, 'rb') as f:
        n = f.getnframes()
        frames = f.readframes(n)
    return frames


def test_keyword_recognition(benchmark):
    # save original config and disable another_listener for this test
    original_setting = config.ENABLE_DUMP_KEYWORD_BLOCK
    config.ENABLE_ANOTHER_LISTENER = False

    # read test audio data from a file
    audio_data = read_wave_data('test_audio/test_audio.raw')

    def listener(keyword, stream_write_time):
        # listener does nothing in this test
        pass

    recognizer = KeywordRecognizer('test_keyword')
    recognizer.add_listener(listener)

    # create a queue and put audio data into it
    q = queue.Queue()
    q.put((time.time(), audio_data))

    # replace recognizer's queue with our queue filled with test data
    recognizer.audio_queue = q

    # benchmark keyword recognition
    benchmark(recognizer.run)

    recognizer.close()

    # restore original config after test
    config.ENABLE_DUMP_KEYWORD_BLOCK = original_setting
