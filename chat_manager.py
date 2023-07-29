# chat_manager.py
import os

import openai

ai = openai
ai.api_key = os.getenv('OPENAI_API_KEY')
ai.organization = "org-9YiPG54UMFObNmQ2TMOnPCar"
model = 'gpt-3.5-turbo'
messages = [{"role": "system", "content": "you are a helpful assistant"}]


class ChatSession:
    def __init__(self):
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]

    def add_user_entry(self, content):
        self.messages.append(
            {"role": "user", "content": content},
        )

    def add_reply_entry(self, response):
        if 'choices' in response['model']:
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
