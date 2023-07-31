# chat_manager.py
import os
import openai
import config


def extract_trans_text(content) -> list:
    speech = []
    for i in content:
        speech.append(i["text"])
    return speech


class ChatSession:
    def __init__(self):
        self.ai = openai
        self.ai.api_key = os.getenv('OPENAI_API_KEY')
        self.ai.organization = "org-9YiPG54UMFObNmQ2TMOnPCar"
        self.model = 'gpt-3.5-turbo'
        self.transcription_directory = config.TRANSCRIPTION_PATH
        self.messages = [{"role": "system",
                          "content": "You are a helpful assistant"
                          }]

    def add_user_entry(self, content):
        speech = extract_trans_text(content)
        for i in speech:
            if i is not None or "":
                self.messages.append(
                    {"role": "user", "content": i},
                )
            else:
                pass

    def add_reply_entry(self, response):
        reply = response['choices'][0]['message']
        self.messages.append(reply)

    def send_request(self):
        try:
            chat_completion = self.ai.ChatCompletion.create(
                model=self.model,
                messages=self.messages
            )
            return chat_completion
        except Exception as e:
            print(f"Error sending request: {e}")
