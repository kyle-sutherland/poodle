# config.py
import dataclasses
from dataclasses import dataclass, field, fields
import json


@dataclass(unsafe_hash=True)
class Configurator:
    path_prompt_bodies_audio: str = field(default="")
    transcription_path: str = field(default="")
    conversations_path: str = field(default="")
    response_log_path: str = field(default="")
    local_transcriber_model: str = field(default="")
    speak: str = field(default="")
    voice: str = field(default="")
    agent_path: str = field(default="")
    chat_model: str = field(default="")
    keyword: str = field(default="")
    lang: str = field(default="")
    enable_dump_keyword_block: bool = field(default=False)
    enable_print_prompt: bool = field(default=False)
    enable_performance_log: bool = field(default=False)
    enable_all_partial_result_log: bool = field(default=False)
    enable_active_speech_log: bool = field(default=False)
    online_transcribe: bool = field(default=False)
    stream_response: bool = field(default=False)
    sounds: bool = field(default=False)
    pyaudio_channels: int = field(default=1)
    pyaudio_frames_per_buffer: int = field(default=8000)
    presence_penalty: float = field(default=1.0)
    temperature: float = field(default=1.0)

    def update_from_json(self, json_path):
        with open(json_path, "r") as file:
            data = json.load(file)

        for key, value in data.items():
            if hasattr(self, key):
                expected_type = type(getattr(self, key))
                if isinstance(value, expected_type) or getattr(self, key) is None:
                    setattr(self, key, value)
                else:
                    raise ValueError(
                        f"Type mismatch for {key}: Expected {expected_type}, got {type(value)}"
                    )
            else:
                print(
                    f"Key '{key}' in JSON file is not a valid attribute of Configurator and will be ignored."
                )

    def load_configurations(self, *json_paths):
        self.update_from_json("core/app_config.json")
        self.update_from_json("core/audio_config.json")
        self.update_from_json("core/chat_config.json")
        for path in json_paths:
            self.update_from_json(path)

        # Check for any unset required attributes
        for field in fields(self):
            if (
                getattr(self, field.name) is None
                and field.default is dataclasses.MISSING
            ):
                raise ValueError(
                    f"Configuration not complete: '{field.name}' is missing."
                )
