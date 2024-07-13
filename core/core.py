# app.py
import json
import logging
from config import Configurator
import core.chat_utils
from core.chat_utils import ChatSession
from core.chat_utils import ClaudeChatSession
from core.file_manager import FileManager


class Poodle:
    def __init__(self, config: Configurator):
        self.config = config
        # Initialize other attributes as needed.
        self.keyword_detector = None
        self.convo = None
        self.chat_utils = core.chat_utils
        self.prompt_jo: dict = FileManager.read_json(
            self.config.__getattribute__("agent_path")
        )
        self.chat_sessions: list[ChatSession] = []
        self.chat_models = None
        self.chat_model = None

    def isSpeak(self):
        if self.config.tts.lower != "cloud" or self.config.tts.lower() != "local":
            return False
        return True

    def get_session(self, index) -> ChatSession:
        return self.chat_sessions[index]

    def init_chat_session(self, model):
        if "claude" in model["name"]:
            chat_session = ClaudeChatSession(
                json.dumps(self.prompt_jo, indent=None, ensure_ascii=True),
                model["name"],
                self.config.temperature,
                self.config.presence_penalty,
                model["token_limit"],
                model["limit_thresh"],
                self.config.stream_response,
            )
        else:
            chat_session = ChatSession(
                json.dumps(self.prompt_jo, indent=None, ensure_ascii=True),
                model["name"],
                self.config.temperature,
                self.config.presence_penalty,
                model["token_limit"],
                model["limit_thresh"],
                self.config.stream_response,
            )
        self.chat_sessions.append(chat_session)

    def load_core(self):
        self.chat_models = FileManager.read_json("core/models.json")
        models = self.chat_models
        self.model = models[self.config.chat_model]
        self.init_chat_session(self.model)

    def run(self):
        try:
            self.chat_sessions[0].initialize_chat(self.isSpeak())
        except Exception as e:
            logging.error(f"exception: {e}")
