# main_logic.py
# Contains the core functionality of the Poodle application.

from chat_utils import ChatSession
from audio_utils import KeywordDetector
import event_flags as ef
import config as conf
from file_manager import FileManager
import kd_listeners


class PoodleApp:
    def __init__(self, config):
        self.config = config
        self.chat_session = None
        self.keyword_detector = None

    def run(self):
        # Initialize chat session
        self.chat_session = ChatSession(
            initial_prompt=self.config.INITIAL_PROMPT,
            model=self.config.CHAT_MODEL,
            temperature=self.config.TEMPERATURE,
            presence_penalty=self.config.PRESENCE_PENALTY,
            token_limit=self.config.TOKEN_LIMIT,
            limit_thresh=self.config.LIMIT_THRESH,
        )
        self.chat_session.initialize_chat(self.config.SPEAK)

        # Initialize keyword detector
        self.keyword_detector = KeywordDetector(
            keyword=self.config.KEYWORD,
            audio_params={
                "channels": self.config.PYAUDIO_CHANNELS,
                "frames_per_buffer": self.config.PYAUDIO_FRAMES_PER_BUFFER,
            },
        )
        self.keyword_detector.add_keyword_listener(
            kd_listeners.kwl_print_keyword_message
        )
        self.keyword_detector.add_keyword_listener(kd_listeners.kwl_start_recording)
        self.keyword_detector.add_keyword_listener(kd_listeners.kwl_stop_audio)
        self.keyword_detector.add_partial_listener(kd_listeners.pl_print_all_partials)
        self.keyword_detector.add_partial_listener(
            kd_listeners.pl_print_active_speech_only
        )
        self.keyword_detector.add_partial_listener(kd_listeners.pl_no_speech)

        # Start the keyword detector
        self.keyword_detector.start()

        # Main application loop
        try:
            while True:
                # Check for transcriptions
                if ef.transcribed.is_set():
                    transcriptions = FileManager.read_transcriptions(
                        self.config.TRANSCRIPTION_PATH
                    )
                    for transcription in transcriptions:
                        self.chat_session.add_user_trans(transcription)
                    ef.transcribed.clear()

                # Send chat messages and get response
                response = self.chat_session.send_request()
                self.chat_session.add_reply_entry(response)

                # Handle streaming response
                if self.config.STREAM_RESPONSE:
                    self.chat_session.extract_streamed_resp_deltas(response)

                # TODO: Add more application logic as needed

        except KeyboardInterrupt:
            print("Shutting down Poodle...")
        finally:
            if self.keyword_detector:
                self.keyword_detector.close()


# End of PoodleApp class definition
