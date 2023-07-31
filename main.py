# main.py
import gc

import chat_manager
import kd_listeners
from audio_utils import KeywordDetector, Transcriber, TextToSpeech
from file_manager import FileManager
import time
import config
import event_flags as ef


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
    chat_session = chat_manager.ChatSession()
    transcriber = Transcriber(config.PATH_PROMPT_BODIES_AUDIO, config.TRANSCRIPTION_PATH)

    kw_detector.start()

    def do_request(chat, trans):
        text_to_speech = TextToSpeech()
        if len(trans) != 0:
            chat.add_user_entry(trans)
        resp = chat.send_request()
        chat.add_reply_entry(resp)
        tstamp = FileManager.get_datetime_string()
        FileManager.save_json(f'{config.RESPONSE_LOG_PATH}response_{tstamp}.json', resp)
        ef.speaking.set()
        text_to_speech.make_voice('things')
        # pyaudio currently seems to have issues in python 3.10. Going to try workarounds on the test branch
        # text_to_speech.play_voice()
        ef.speaking.clear()
        print(f'{resp["choices"][0]["message"]["content"]}/n')
        print("")
        print(f"total response time: {time.time() - ef.stream_write_time} seconds\n")
        ef.silence.clear()

    try:
        while True:
            transcriber.transcribe_bodies()
            if ef.silence.is_set() and not ef.recording.is_set():
                transcriptions = FileManager.read_transcriptions(config.TRANSCRIPTION_PATH)
                if len(chat_manager.extract_trans_text(transcriptions)) == 0:
                    print("I didn't hear you")
                    ef.silence.clear()
                    continue
                do_request(chat_session, transcriptions)
                convo = chat_session.messages
                timestamp = FileManager.get_datetime_string()
                FileManager.save_json(f'{config.CONVERSATIONS_PATH}conversation_{timestamp}.json', convo)
            time.sleep(1)
    except KeyboardInterrupt:
        print("Closing the program")
        kw_detector.close()
        kw_detector.join()
        gc.collect()


if __name__ == '__main__':
    main()
