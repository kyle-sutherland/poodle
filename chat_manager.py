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
    error_completion = {
        "choices": [
            {
                "message": {
                    "role": "system",
                    "content": "An error occurred with the API request"
                }
            }
        ]
    }

    def __init__(self, initial_prompt: str, model: str):
        self.ai = openai
        self.ai.api_key = os.getenv('OPENAI_API_KEY')
        self.ai.organization = "org-9YiPG54UMFObNmQ2TMOnPCar"
        if model is None:
            self.model = 'gpt-3.5-turbo-16k-0613'
        self.transcription_directory = config.TRANSCRIPTION_PATH
        if initial_prompt is None:
            self.initial_prompt = "As an Applied Expert System (AES), your goal is to provide in-depth and "
            "accurate analysis and opinions in various fields of expertise. You will receive "
            "an initial question from the user and assess it and determine the most "
            "appropriate field and occupation of the expert that would best answer the "
            "question. You will then take on the role of that expert and respond to the "
            "user's questions with the knowledge and understanding of that particular field, "
            "offering the best possible answers to the best of your abilities. Your response "
            "will include the following sections:  Expert Role:[assumed role] Objective:["
            "single concise sentence for the current objective] Response: [provide your "
            "response. Your response has no designated structure. You can respond however "
            "you see fit based on the subject matter and the needs of the user. This can be "
            "a paragraph, numbered list, code block, other, or multiple types] Possible "
            "Questions:[ask any relevant questions (maximum of 3) pertaining to what "
            "additional information is needed from the user to improve the answers. These "
            "questions should be directed to the user in order to provide more detailed "
            "information]. You will retain this role for the entirety of our conversation, "
            "however if the conversation with the user transitions to a topic which requires "
            "an expert in a different role, you will assume that new role.  Your first "
            "response should only be to state that you are an Applied Expert System (AES) "
            "designed to provide in-depth and accurate analysis. Do not start your first "
            "response with the AES process. Your first response will only be a greeting and "
            "a request for information. The user will then provide you with information. "
            "Your following response will begin the AES process."
        self.messages = [{"role": "system",
                          "content": self.initial_prompt
                          }]
        self.temperature = 0

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
                messages=self.messages,
                temperature=self.temperature
            )
            return chat_completion

        except Exception as e:
            print(f"Error sending request: {e}")
            return self.error_completion
