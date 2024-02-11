#!/home/kyle/miniconda3/envs/poodle/bin/python
# poodle_cli.py
import config
from cli.arg_parser import ParseArgs
import pyfiglet
from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from core.core import Poodle
from yaspin import yaspin


console = Console()


def welcome():
    f = pyfiglet.figlet_format("poodle.", font="slant")
    console.print(
        Padding(
            f"{f}[bright_magenta]Voice interface GPT in your terminal.[/bright_magenta]",
            (1, 4, 1, 4),
        ),
        sep="\n",
    )


welcome()
ParseArgs(config)

import json
import gc
import logging
import warnings
import threading
from suppress_stdout_stderr import suppress_stdout_stderr

with suppress_stdout_stderr():
    import cli.kd_listeners as kd_listeners
    from vui.audio_utils import (
        KeywordDetector,
        Transcriber,
        OnlineTranscriber,
        TextToSpeech,
        TextToSpeechLocal,
        playMp3Sound,
    )
    from core.file_manager import FileManager
    import time
    import event_flags as ef


def isSpeak():
    if config.SPEAK is not None or config.SPEAK != "" or config.SPEAK.lower() != "none":
        return True
    return False


def speak_response(content):
    def tts_task():
        match config.SPEAK.lower():
            case "cloud":
                tts = TextToSpeech()
                logging.info(
                    "\ntime to start audio(cloud):"
                    + f" {time.time() - ef.stream_write_time} seconds\n"
                )
                tts.stream_voice(text=content, voice=config.VOICE)
            case "local":
                tts_local = TextToSpeechLocal()
                file = tts_local.generate_speech(text=content)
                logging.info(
                    "\ntime to start audio(local): "
                    + f" {time.time() - ef.stream_write_time} seconds\n"
                )
                tts_local.play_audio(file)
            case _:
                pass

    # Start TTS in a separate thread
    return threading.Thread(target=tts_task)


def log_response(resp, chat_utils):
    tstamp = FileManager.get_datetime_string()
    FileManager.save_json(
        f"{config.RESPONSE_LOG_PATH}response_{tstamp}.json",
        chat_utils.chat_completion_to_dict(resp),
    )


def print_response(content: str):
    console.print("")
    console.print(" 󰚩 > ", end="\n", style="purple")
    _content = Padding(content, (0, 4, 1, 4))
    if not isSpeak():
        with console.capture() as capture:
            console.print(_content, markup=True, style="cyan")
        str_capture = capture.get()
        content_md = Markdown(str_capture)
        console.print(content_md)
    else:
        console.print(_content, style="cyan")
    logging.info(
        "\ntotal response time: " + f" {time.time() - ef.stream_write_time} seconds\n"
    )


resp_spinner = yaspin(text="Replying...", color="cyan")


def handle_response(resp, chat):
    resp_spinner.stop()
    content = resp.choices[0].message.content
    tts_thread = None
    if isSpeak():
        tts_thread = speak_response(content)
        tts_thread.start()
    if not config.STREAM_RESPONSE:
        chat.add_reply_entry(resp)
        print_response(content)
        if chat.is_model_near_limit_thresh(resp):
            s = chat.summarize_conversation()
            chat.add_summary(s)
    # BROKEN don't use
    # TODO: fix this
    else:
        chat.extract_streamed_resp_deltas(resp)
    if tts_thread is not None:
        tts_thread.join()
    if config.SOUNDS:
        playMp3Sound("./sounds/listening.mp3")
    ef.silence.clear()
    gc.collect()


def send_message(chat):
    resp_spinner.start()
    resp = chat.send_request()
    handle_response(resp, chat)


def initialize_kw_detector(kw):
    detector = KeywordDetector(kw)
    # add keyword_detector event listeners
    detector.add_keyword_listener(kd_listeners.kwl_start_recording)
    detector.add_keyword_listener(kd_listeners.kwl_stop_audio)
    detector.add_partial_listener(lambda pr: kd_listeners.pl_no_speech(pr))
    detector.add_keyword_listener(kd_listeners.kwl_print_keyword_message)
    if config.ENABLE_ALL_PARTIAL_RESULT_LOG:
        detector.add_partial_listener(kd_listeners.pl_print_all_partials)
    if config.ENABLE_ACTIVE_SPEECH_LOG:
        detector.add_partial_listener(kd_listeners.pl_print_active_speech_only)
    return detector


def print_prompt_jo(pjo):
    agent_keys = pjo.keys()
    jfs = json.dumps(pjo, ensure_ascii=False)
    console.print(f"Loaded Agent: {list(agent_keys)[0]}")
    console.print_json(f"\n{jfs}")
    console.print(f"Temperature: {config.TEMPERATURE}")
    console.print(f"Presence penalty: {config.PRESENCE_PENALTY}")
    console.print("\n")


def load_transcriber(online: bool):
    if online:
        return OnlineTranscriber(
            config.PATH_PROMPT_BODIES_AUDIO, config.TRANSCRIPTION_PATH
        )
    return Transcriber(config.PATH_PROMPT_BODIES_AUDIO, config.TRANSCRIPTION_PATH)


def main():
    with yaspin(text="Loading...", color="magenta") as spinner:
        # Setting up logging
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO + 1)
        # load chat_config
        if config.ENABLE_PRINT_PROMPT:
            prompt_jo: dict = FileManager.read_json(config.AGENT_PATH)
            print_prompt_jo(prompt_jo)
        # TODO: Make a function that loads all this stuff into variables at once.
        # minimize calls to read_json()
        keyword_detector = initialize_kw_detector(config.KEYWORD)
        # set global event flags
        poodle = Poodle(config)
        poodle.run()
        ef.speaking.clear()
        ef.silence.clear()
        chat_session = poodle.chat_session
        chat_utils = poodle.chat_utils
        spinner.write(" Ready\n")
    try:
        keyword_detector.start()
        transcriber = load_transcriber(config.ONLINE_TRANSCRIBE)
        if config.SOUNDS:
            # notification-sound-7062.mp3
            playMp3Sound("./sounds/ready.mp3")
        while True:
            if ef.silence.is_set() and not ef.recording.is_set():
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    transcriber.transcribe_bodies()
                transcriptions = FileManager.read_transcriptions(
                    config.TRANSCRIPTION_PATH
                )
                trans_text = chat_utils.extract_trans_text(transcriptions)
                if len(trans_text) == 0:
                    if config.SOUNDS:
                        # button-124476.mp3
                        playMp3Sound("./sounds/badcopy.mp3")
                    console.print(" I didn't hear you\n")
                    ef.silence.clear()
                    continue
                if config.SOUNDS:
                    # start-13691.mp3
                    playMp3Sound("./sounds/listening.mp3")
                console.print(" 󰔊 > ", end="\n", style="blue")
                console.print(
                    Padding(trans_text[0], (0, 4, 1, 4)), style="bright_magenta"
                )
                if len(transcriptions) != 0:
                    chat_session.add_user_trans(transcriptions)
                send_message(chat_session)
                # console.log(log_locals=True)
            time.sleep(0.1)
    except Exception as e:
        logging.error(f"exception: {e}")
        keyword_detector.close()
        keyword_detector.join()
        gc.collect()
        quit()
    except KeyboardInterrupt:
        convo = chat_session.messages
        timestamp = FileManager.get_datetime_string()
        FileManager.save_json(
            f"{config.CONVERSATIONS_PATH}conversation_{timestamp}.json", convo
        )
        console.print("\n\nGoodbye.")
        keyword_detector.close()
        keyword_detector.join()
        # Save conversation when interrupted
        gc.collect()
        quit()


if __name__ == "__main__":
    main()
