# kd_listeners.py
import time
import json
import body_transcriber
import config
from silence_watcher import SilenceWatcher
import event_flags
from audio_recorder import AudioRecorder

silence_watcher = SilenceWatcher()
audio_recorder = AudioRecorder()


def kwl_print_keyword_message(keyword, data, stream_write_time):
    trigger_time = time.time() - stream_write_time
    print(f"Time from stream write to keyword trigger: {trigger_time} seconds")
    print(f"{keyword}!!")


def kwl_start_recording(keyword, data, stream_write_time):
    audio_recorder.start_recording()
    event_flags.listening.set()


def pl_print_all_partials(partial_result):
    pr = json.loads(partial_result)
    print(pr)


def pl_print_active_speech_only(partial_result):
    pr = json.loads(partial_result)
    for key in pr:
        if pr[key] != "":
            print(pr[key])


def pl_no_speech(partial_result):
    pr = json.loads(partial_result)
    if event_flags.recording.is_set():
        if silence_watcher.check_silence(pr):
            event_flags.silence.set()
            timestamp = time.time()
            audio_recorder.stop_recording(f"{config.PATH_PROMPT_BODIES_AUDIO}body_{timestamp}.wav")
            body_transcriber.transcribe_bodies()
            silence_watcher.reset()
