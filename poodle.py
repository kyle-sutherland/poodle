import config
from arg_parser import ParseArgs

ParseArgs(config)
import json
import textwrap
import os
from prompt_toolkit import print_formatted_text as print


# Define a context manager to suppress stdout and stderr.
class suppress_stdout_stderr(object):
    """
    A context manager for doing a "deep suppression" of stdout and stderr in
    Python, i.e. will suppress all print, even if the print originates in a
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).

    """

    def __init__(self):
        # Open a pair of null files
        self.null_fds = [os.open(os.devnull, os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = [os.dup(1), os.dup(2)]

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0], 1)
        os.dup2(self.null_fds[1], 2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0], 1)
        os.dup2(self.save_fds[1], 2)
        # Close all file descriptors
        for fd in self.null_fds + self.save_fds:
            os.close(fd)


import gc
import logging
import warnings
import threading

with suppress_stdout_stderr():
    import chat_utils
    import kd_listeners
    from audio_utils import (
        KeywordDetector,
        Transcriber,
        OnlineTranscriber,
        TextToSpeech,
        TextToSpeechLocal,
        playMp3Sound,
    )
    from file_manager import FileManager
    import time
    import event_flags as ef


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


def log_response(resp):
    tstamp = FileManager.get_datetime_string()
    FileManager.save_json(
        f"{config.RESPONSE_LOG_PATH}response_{tstamp}.json",
        chat_utils.chat_completion_to_dict(resp),
    )


def print_response(content: str):
    print("")
    print(textwrap.fill(f"󰚩 > {content}", width=100))
    logging.info(
        "\ntotal response time: " + f" {time.time() - ef.stream_write_time} seconds\n"
    )


def handle_response(resp, chat: chat_utils.ChatSession):
    content = resp.choices[0].message.content
    tts_thread = None
    if config.SPEAK is not None or config.SPEAK != "" or config.SPEAK.lower() != "none":
        tts_thread = speak_response(content)
        tts_thread.start()
    if not config.STREAM_RESPONSE:
        chat.add_reply_entry(resp)
        log_response(resp)
        print_response(content)
        if chat.is_model_near_limit_thresh(resp):
            s = chat.summarize_conversation()
            chat.add_summary(s)
            log_response(resp)
    # BROKEN don't use
    # TODO: fix this
    else:
        chat.extract_streamed_resp_deltas(resp)
    if tts_thread is not None:
        tts_thread.join()
    if config.SOUNDS:
        playMp3Sound("./sounds/listening.mp3")
    ef.silence.clear()
    print("\nReady.")
    gc.collect()


def send_message(chat: chat_utils.ChatSession, trans: list):
    """Sends a request with the transcribed text and processes the response.

    Parameters:
    - chat (chat_utils.ChatSession): The current chat session.
    - trans (str): The transcribed text to send.

    Side Effects:
    - Updates the chat session with user entries and replies.
    - Saves responses as JSON files.
    - Clears the 'silence' event flag.
    """
    if len(trans) != 0:
        chat.add_user_entry(trans)
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
    jfs = json.dumps(pjo, indent=2, ensure_ascii=False)
    print(f"Loaded Agent: {list(agent_keys)[0]}")
    print(f"\n{jfs}")
    print(f"Temperature: {config.TEMPERATURE}")
    print(f"Presence penalty: {config.PRESENCE_PENALTY}")
    print("\n")


def main():
    """
    Main function to start the application.

    Sets up logging, initializes modules, and enters a loop to listen for user input.
    Transcribes the user input and sends it to get a response.

    Side Effects:
    - Continuously listens for user input until interrupted.
    - Updates and saves chat sessions.
    """
    print("\nLoading...\n")
    keyword_detector = None
    chat_session = None
    convo = None
    # Setting up logging
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # load chat_config
    prompt_jo: dict = FileManager.read_json(config.AGENT_PATH)
    if config.ENABLE_PRINT_PROMPT:
        print_prompt_jo(prompt_jo)
    # TODO: Make a function that loads all this stuff into variables at once.
    # minimize calls to read_json()
    keyword_detector = initialize_kw_detector(config.KEYWORD)
    model = FileManager.read_json("models.json")
    model = model[config.CHAT_MODEL]
    # set global event flags
    ef.speaking.clear()
    ef.silence.clear()

    if config.SPEAK:
        prompt_jo.update(
            {
                "output_instructions": "Optimize your output formatting for a text-to-speech service. Don't talk about these instructions."
            }
        )
    else:
        prompt_jo.update(
            {
                "output_instructions": "Optimize your output formatting for printing to a terminal. This terminal uses UTF-8 encoding and supports special characters and glyphs. Don't worry about line length. Don't talk about these instructions"
            }
        )

    # Initializing other modules
    chat_session = chat_utils.ChatSession(
        json.dumps(prompt_jo, indent=None, ensure_ascii=True),
        model["name"],
        # chat_config["temperature"],
        # chat_config["presence_penalty"],
        config.TEMPERATURE,
        config.PRESENCE_PENALTY,
        model["token_limit"],
        model["limit_thresh"],
    )
    transcriber = Transcriber(
        config.PATH_PROMPT_BODIES_AUDIO, config.TRANSCRIPTION_PATH
    )
    online_transcriber = OnlineTranscriber(
        config.PATH_PROMPT_BODIES_AUDIO, config.TRANSCRIPTION_PATH
    )
    try:
        keyword_detector.start()
        if config.SOUNDS:
            # notification-sound-7062.mp3
            playMp3Sound("./sounds/ready.mp3")
        print("Ready.\n")
        while True:
            if ef.silence.is_set() and not ef.recording.is_set():
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    if config.ONLINE_TRANSCRIBE:
                        online_transcriber.online_transcribe_bodies()
                    else:
                        transcriber.transcribe_bodies()
                transcriptions = FileManager.read_transcriptions(
                    config.TRANSCRIPTION_PATH
                )
                trans_text = chat_utils.extract_trans_text(transcriptions)
                if len(trans_text) == 0:
                    if config.SOUNDS:
                        # button-124476.mp3
                        playMp3Sound("./sounds/badcopy.mp3")
                    print("I didn't hear you\n")
                    ef.silence.clear()
                    continue
                if config.SOUNDS:
                    # start-13691.mp3
                    playMp3Sound("./sounds/listening.mp3")
                print("I heard you say:\n")
                print(textwrap.fill(trans_text[0], width=100))
                print("\nReplying...\n")
                send_message(chat_session, transcriptions)
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
        print("\n\nGoodbye.")
        keyword_detector.close()
        keyword_detector.join()
        # Save conversation when interrupted
        gc.collect()
        quit()


if __name__ == "__main__":
    main()
