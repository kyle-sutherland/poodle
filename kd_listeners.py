# kd_listeners.py
import logging
import time
import json

import chat_manager
import config
import event_flags
from audio_utils import TextToSpeechLocal, Transcriber, AudioRecorder, SilenceWatcher, TextToSpeech
from file_manager import FileManager

silence_watcher = SilenceWatcher()
audio_recorder = AudioRecorder()
transcriber = Transcriber(config.PATH_PROMPT_BODIES_AUDIO, config.TRANSCRIPTION_PATH)
tts = TextToSpeech()
tts_local = TextToSpeechLocal()


def kwl_print_keyword_message(keyword, data, stream_write_time):
    trigger_time = time.time() - stream_write_time
    logging.info(f"Time from stream write to keyword trigger: {trigger_time} seconds")
    chat_manager.sim_typing_output(f" This is {keyword}. I am listening.", 0.02)
    print("\n")
    if config.SPEAK == "WHISPER":
        if tts.is_audio_playing():
            tts.stop_audio()
    if config.SPEAK == "LOCAL":
        tts_local.stop_audio()
    else:
        pass


def kwl_start_recording(keyword, data, stream_write_time):
    silence_watcher.reset()
    event_flags.stream_write_time = stream_write_time
    audio_recorder.start_recording()


def kwl_stop_audio(keyword, data, stream_write_time):
    if config.SPEAK == "WHISPER":
        if tts.is_audio_playing():
            tts.stop_audio()
    if config.SPEAK == "LOCAL":
        tts_local.stop_audio()
    else:
        pass


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
            timestamp = FileManager.get_datetime_string()
            audio_recorder.stop_recording(
                f"{config.PATH_PROMPT_BODIES_AUDIO}body_{timestamp}.wav"
            )
            silence_watcher.reset()
