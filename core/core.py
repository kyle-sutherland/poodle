# app.py
import json
import logging
import core.chat_utils
from core.chat_utils import ChatSession
from core.file_manager import FileManager


class Poodle:
    def __init__(self, config):
        self.config = config
        # Initialize other attributes as needed.
        self.keyword_detector = None
        self.convo = None
        self.chat_utils = core.chat_utils
        self.prompt_jo: dict = FileManager.read_json(self.config.AGENT_PATH)
        self.chat_session: ChatSession

    def isSpeak(self):
        if self.config.SPEAK.lower != "cloud" or self.config.SPEAK.lower() != "local":
            return False
        return True

    def get_session(self) -> ChatSession:
        return self.chat_session

    def run(self):
        # The main logic of the application will be moved here.
        # TODO: Make a function that loads all this stuff into variables at once.
        # minimize calls to read_json()
        model = FileManager.read_json("core/models.json")
        model = model[self.config.CHAT_MODEL]
        # set global event flags

        # Initializing other modules
        self.chat_session = ChatSession(
            json.dumps(self.prompt_jo, indent=None, ensure_ascii=True),
            model["name"],
            self.config.TEMPERATURE,
            self.config.PRESENCE_PENALTY,
            model["token_limit"],
            model["limit_thresh"],
            self.config.STREAM_RESPONSE,
        )
        try:
            self.chat_session.initialize_chat(self.isSpeak())
        except Exception as e:
            logging.error(f"exception: {e}")
