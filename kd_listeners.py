# kd_listeners.py

import time
import json


def kwl_print_keyword_message(keyword, stream_write_time):
    trigger_time = time.time() - stream_write_time
    print(f"Time from stream write to keyword trigger: {trigger_time} seconds")
    print(f"{keyword}!!")


def kwl_dump_keyword_block(fetcher, data):
    # put whatever code you want here, it will run concurrently with print_keyword_message
    fetcher.dump_audio(data)  # Now you can call dump_audio from another_listener


def kwl_start_recording_on_keyword(recorder):
    recorder.start_recording()


def pl_print_all_partials(partial_result):
    pr = json.loads(partial_result)
    print(pr)


def pl_print_active_speech_only(partial_result):
    pr = json.loads(partial_result)
    for key in pr:
        if pr[key] != "":
            print(pr[key])


def pl_no_speech(kw_detector, partial_result):
    pr = json.loads(partial_result)
    no_speech = all(pr[key] == "" for key in pr)
    kw_detector.check_silence(no_speech)
