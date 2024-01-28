import gc
import logging
import warnings
import threading
from arg_parser import ParseArgs

import chat_manager
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
import config
import event_flags as ef


def do_request(chat: chat_manager.ChatSession, trans: list):
    """Sends a request with the transcribed text and processes the response.

    Parameters:
    - chat (chat_manager.ChatSession): The current chat session.
    - trans (str): The transcribed text to send.

    Side Effects:
    - Updates the chat session with user entries and replies.
    - Saves responses as JSON files.
    - Clears the 'silence' event flag.
    """
    if len(trans) != 0:
        chat.add_user_entry(trans)
    resp = chat.send_request()
    content = resp.choices[0].message.content

    def tts_task():
        match config.SPEAK:
            case "cloud":
                tts = TextToSpeech()
                logging.info(
                    "\ntime to start audio:"
                    + f" {time.time() - ef.stream_write_time} seconds\n"
                )
                tts.stream_voice(text=content, voice="shimmer")
            case "local":
                tts_local = TextToSpeechLocal()
                file = tts_local.generate_speech(text=content)
                logging.info(
                    "\ntime to start audio: "
                    + f" {time.time() - ef.stream_write_time} seconds\n"
                )
                tts_local.play_audio(file)
            case _:
                pass

    # Start TTS in a separate thread
    tts_thread = threading.Thread(target=tts_task)
    tts_thread.start()

    if not config.STREAM_RESPONSE:
        chat.add_reply_entry(resp)
        tstamp = FileManager.get_datetime_string()
        FileManager.save_json(
            f"{config.RESPONSE_LOG_PATH}response_{tstamp}.json",
            chat_manager.chat_completion_to_dict(resp),
        )
        print(f"\n{content}\n")
        logging.info(
            "\ntotal response time: "
            + f" {time.time() - ef.stream_write_time} seconds\n"
        )
    else:
        chat.extract_streamed_resp_deltas(resp)

    if not config.STREAM_RESPONSE:
        if chat.is_model_near_limit_thresh(resp):
            s = chat.summarize_conversation()
            chat.add_summary(s)
            FileManager.save_json(
                f"{config.RESPONSE_LOG_PATH}response_{FileManager.get_datetime_string()}.json",
                chat_manager.chat_completion_to_dict(s),
            )

    ef.silence.clear()
    gc.collect()
    tts_thread.join()


def main():
    """
    Main function to start the application.

    Sets up logging, initializes modules, and enters a loop to listen for user input.
    Transcribes the user input and sends it to get a response.

    Side Effects:
    - Continuously listens for user input until interrupted.
    - Updates and saves chat sessions.
    """
    kw_detector = None
    chat_session = None
    convo = None
    ParseArgs(config)
    # Setting up logging
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO + 1)
    print("\nLoading...\n")
    # load chat_config
    chat_config = FileManager.read_json("chat_config.json")
    # TODO: Make a function that loads all this stuff into variables at once.
    # minimize calls to read_json()
    model = FileManager.read_json("models.json")
    model = model[config.CHAT_MODEL]
    # initialize kw_detector
    kw_detector = KeywordDetector(config.KEYWORD)
    # add keyword_detector event listeners
    kw_detector.add_keyword_listener(kd_listeners.kwl_start_recording)
    kw_detector.add_keyword_listener(kd_listeners.kwl_stop_audio)
    kw_detector.add_partial_listener(lambda pr: kd_listeners.pl_no_speech(pr))
    kw_detector.add_keyword_listener(kd_listeners.kwl_print_keyword_message)
    if config.ENABLE_ALL_PARTIAL_RESULT_LOG:
        kw_detector.add_partial_listener(kd_listeners.pl_print_all_partials)
    if config.ENABLE_ACTIVE_SPEECH_LOG:
        kw_detector.add_partial_listener(kd_listeners.pl_print_active_speech_only)
    # set global event flags
    ef.speaking.clear()
    ef.silence.clear()

    # Initializing other modules
    chat_session = chat_manager.ChatSession(
        chat_config["prompt"],
        model["name"],
        chat_config["temperature"],
        chat_config["presence_penalty"],
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
        kw_detector.start()
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
                trans_text = chat_manager.extract_trans_text(transcriptions)
                if len(trans_text) == 0:
                    if config.SOUNDS:
                        # button-124476.mp3
                        playMp3Sound("./sounds/badcopy.mp3")
                    print("I didn't hear you")
                    ef.silence.clear()
                    continue
                if config.SOUNDS:
                    # start-13691.mp3
                    playMp3Sound("./sounds/listening.mp3")
                print(f"I heard:\n\n   {trans_text[0]}\n\n Replying...\n\n")
                do_request(chat_session, transcriptions)
            time.sleep(0.1)
    except Exception as e:
        logging.error(f"exception: {e}")
        kw_detector.close()
        kw_detector.join()
        gc.collect()
        quit()
    except KeyboardInterrupt:
        convo = chat_session.messages
        timestamp = FileManager.get_datetime_string()
        FileManager.save_json(
            f"{config.CONVERSATIONS_PATH}conversation_{timestamp}.json", convo
        )
        print("\n\nGoodbye.")
        kw_detector.close()
        kw_detector.join()
        # Save conversation when interrupted
        gc.collect()
        quit()


if __name__ == "__main__":
    main()
