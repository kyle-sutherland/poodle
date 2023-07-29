# chat_manager.py
import os
import threading
import time

import openai

import config
from file_manager import FileManager

ai = openai
ai.api_key = os.getenv('OPENAI_API_KEY')
ai.organization = "org-9YiPG54UMFObNmQ2TMOnPCar"
model = 'gpt-3.5-turbo'
messages = [{"role": "system", "content": "you are a helpful assistant"}]


class ChatSession:
    def __init__(self):
        self.transcription_directory = config.TRANSCRIPTION_PATH
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]

    def add_user_entry(self, content):
        self.messages.append(
            {"role": "user", "content": content[0]["text"]},
        )

    def add_reply_entry(self, response):
        reply = response['choices'][0]['message']['content']
        self.messages.append({"role": "assistant", "content": reply})

    def send_request(self):
        try:
            chat_completion = ai.ChatCompletion.create(
                model=model,
                messages=self.messages
            )
            return chat_completion
        except Exception as e:
            print(f"Error sending request: {e}")
