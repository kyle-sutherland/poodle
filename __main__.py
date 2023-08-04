# __main__.py
import gc
import logging

import chat_manager
import kd_listeners
from audio_utils import KeywordDetector, Transcriber, OnlineTranscriber
from file_manager import FileManager
import time
import config
import event_flags as ef


def do_request(chat, trans):
    # text_to_speech = TextToSpeech()
    if len(trans) != 0:
        chat.add_user_entry(trans)
    resp = chat.send_request()

    if not config.STREAM_RESPONSE:
        chat.add_reply_entry(resp)
        tstamp = FileManager.get_datetime_string()
        FileManager.save_json(f"{config.RESPONSE_LOG_PATH}response_{tstamp}.json", resp)
        print(f'\n{resp["choices"][0]["message"]["content"]}\n')
        logging.info(
            f"\ntotal response time: {time.time() - ef.stream_write_time} seconds\n"
        )

    else:
        chat.extract_streamed_resp_deltas(resp)

    if not config.STREAM_RESPONSE:
        if chat.is_model_near_limit_thresh(resp):
            s = chat.summarize_conversation()
            chat.add_summary(s)
            FileManager.save_json(
                f"{config.RESPONSE_LOG_PATH}response_{FileManager.get_datetime_string()}.json",
                s,
            )

    ef.silence.clear()
    gc.collect()
    # pyaudio currently seems to have issues in python 3.10. Going to try workarounds on the test branch
    # ok. found a workaround: use playsound instead of pyaudio to play the file. Not ideal but works for now.
    # may try to use python 3.9 at some point. This is insanely expensive and takes FOREVER. Going to try to figure
    # that out, too.
    # ef.speaking.set()
    # text_to_speech.make_voice(resp["choices"][0]["message"]["content"])
    # time.sleep(0.1)
    # text_to_speech.play_voice()
    # ef.speaking.clear()
    # print("")
    # del text_to_speech


def main():
    kw_detector = KeywordDetector("computer")
    kw_detector.add_keyword_listener(kd_listeners.kwl_start_recording)
    kw_detector.add_partial_listener(lambda pr: kd_listeners.pl_no_speech(pr))

    kw_detector.add_keyword_listener(kd_listeners.kwl_print_keyword_message)

    if config.ENABLE_ALL_PARTIAL_RESULT_LOG:
        kw_detector.add_partial_listener(kd_listeners.pl_print_all_partials)

    if config.ENABLE_ACTIVE_SPEECH_LOG:
        kw_detector.add_partial_listener(kd_listeners.pl_print_active_speech_only)

    ef.speaking.clear()
    ef.silence.clear()
    chat_session = chat_manager.ChatSession()
    transcriber = Transcriber(
        config.PATH_PROMPT_BODIES_AUDIO, config.TRANSCRIPTION_PATH
    )
    online_transcriber = OnlineTranscriber(
        config.PATH_PROMPT_BODIES_AUDIO, config.TRANSCRIPTION_PATH
    )

    try:
        kw_detector.start()
        logging.info("ready")
        while True:
            if ef.silence.is_set() and not ef.recording.is_set():
                if config.ONLINE_TRANSCRIBE:
                    online_transcriber.online_transcribe_bodies()
                else:
                    transcriber.transcribe_bodies()
                transcriptions = FileManager.read_transcriptions(
                    config.TRANSCRIPTION_PATH
                )
                trans_text = chat_manager.extract_trans_text(transcriptions)
                if len(trans_text) == 0:
                    print("I didn't hear you")
                    ef.silence.clear()
                    continue
                print(f"You said:\n{trans_text}\n")
                chat_manager.sim_typing_output("Replying...\n")
                do_request(chat_session, transcriptions)
                convo = chat_session.messages
                timestamp = FileManager.get_datetime_string()
                FileManager.save_json(
                    f"{config.CONVERSATIONS_PATH}conversation_{timestamp}.json", convo
                )
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\nClosing the program")
        kw_detector.close()
        gc.collect()
    except Exception as e:
        logging.critical(f"exception: {e}")
        kw_detector.close()
        gc.collect()


if __name__ == "__main__":
    main()
