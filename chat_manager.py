# chat_manager.py
import ast
import logging
from time import sleep

import openai
import config
from file_manager import FileManager


def extract_trans_text(content) -> list:
    speech = []
    for i in content:
        speech.append(i["text"])
    return speech


def extract_resp_content(resp) -> str:
    reply = resp["choices"][0]["message"]["content"]
    return reply


def sim_typing_output(text: str, delay: float = 0.01):
    # a function to simulate typing in  the terminal output
    for i in text:
        # print each character individually with a small delay in between.
        print(i, end="", flush=True)
        sleep(delay)


class ChatSession:
    error_completion = {
        "choices": [
            {
                "message": {
                    "role": "system",
                    "content": "An error occurred with the API request",
                }
            }
        ]
    }

    def __init__(self, initial_prompt: str = None, model: str = None):
        self.ai = openai
        self.ai.api_key = FileManager.read_file("api_keys/keys")
        self.ai.organization = "org-9YiPG54UMFObNmQ2TMOnPCar"
        if model is None:
            self.model = "gpt-3.5-turbo-16k-0613"
        self.transcription_directory = config.TRANSCRIPTION_PATH
        self.initial_prompt = initial_prompt
        if initial_prompt is None:
            self.initial_prompt = (
                "As an Applied Expert System (AES), your goal is to provide in-depth and "
                "accurate analysis and opinions in various fields of expertise. You will receive "
                "an initial question from the user and assess it and determine the most "
                "appropriate field and occupation of the expert that would best answer the "
                "question. You will then take on the role of that expert and respond to the user's "
                "questions with the knowledge and understanding of that particular field, "
                "offering the most thorough possible answers to the best of your abilities. Your "
                "response"
                "will always include the following sections:  Expert Role:[assumed role] Objective:["
                "single concise sentence for the current objective] Response: [provide your "
                "response. Your response has no designated structure. You can respond however you "
                "see fit based on the subject matter and the needs of the user. This can be a "
                "paragraph, numbered list, code block, other, or multiple types.] Possible"
                "Questions:[ask any relevant questions (maximum of 3) pertaining to what "
                "additional information is needed from the user to improve the answers. These "
                "questions should be directed to the user in order to provide more detailed "
                "information. Avoid asking general questions like, 'is there anything else you "
                "would like to know about...']. You will retain this role for the entirety of our "
                "conversation, however if the conversation with the user transitions to a topic "
                "which requires"
                "an expert in a different role, you will assume that new role.  Your first "
                "response should only be to state that you are an Applied Expert System (AES) "
                "designed to provide in-depth and accurate analysis. Do not start your first "
                "response with the AES process. Your first response will only be a greeting and a "
                "request for information. The user will then provide you with information. Your "
                "following response will begin the AES process."
            )
        self.messages: list = [{"role": "system", "content": self.initial_prompt}]
        # self.messages: list = json.loads(FileManager.read_file("conversations/conversation_02-08-2023_10-06-14.json"))
        self.temperature = 0
        self.presence_penalty = 1
        self.model_token_limit = 16338
        self.limit_thresh = 0.4

    def add_user_entry(self, trans):
        speech = extract_trans_text(trans)
        for i in speech:
            if i is not None or "":
                self.messages.append(
                    {"role": "user", "content": i},
                )
            else:
                pass

    def is_model_near_limit_thresh(self, response) -> bool:
        if (
            response["usage"]["total_tokens"]
            > self.model_token_limit * self.limit_thresh
        ):
            return True
        else:
            return False

    def add_reply_entry(self, resp):
        reply = extract_resp_content(resp)
        if reply is not None or "":
            self.messages.append(
                {"role": "assistant", "content": reply},
            )
        else:
            pass

    def extract_streamed_resp_deltas(self, resp):
        # this is messy. Could be improved with the use of a thread pool and a Queue
        collected_chunks = []
        collected_messages = []
        # iterate through the stream of events
        for chunk in resp:
            chunk_message = chunk["choices"][0]["delta"]
            if "content" in chunk_message.keys():
                print(chunk_message["content"], end="", flush=True)
            collected_messages.append(chunk_message)
            collected_chunks.append(chunk)
        print("\n\n")
        full_reply_content = "".join([m.get("content", "") for m in collected_messages])
        self.messages.append({"role": "assistant", "content": full_reply_content})
        tstamp = FileManager.get_datetime_string()
        FileManager.save_json(
            f"{config.RESPONSE_LOG_PATH}response_{tstamp}.json", collected_chunks
        )

    def send_request(self):
        try:
            chat_completion = self.ai.ChatCompletion.create(
                model=self.model,
                messages=self.messages,
                temperature=self.temperature,
                stream=config.STREAM_RESPONSE,
            )
            return chat_completion

        except Exception as e:
            logging.error(f"Error sending request: {e}")
            return self.error_completion

    def summarize_conversation(self):
        print("\nSummarizing conversation. Please wait...\n")
        m = self.messages[1:]
        prompt = [
            {
                "role": "system",
                "content": "You will be receive an json object which contains a conversation. The object has the "
                "following structure:\n [{'role': 'user', 'content': '*content goes here*'}, "
                "{'role': 'assistant', 'content': '*content goes here*'}]\n"
                "The 'role' key defines a speaker in the conversation, while the 'content' key defines "
                "what that speaker said. Your task is to summarize this conversation to less than ten "
                "percent of it's original length and return your summary in the same structure "
                "as the original object:\n"
                "[{'role': 'user', 'content': '*content goes here*'}, "
                "{'role': 'assistant', 'content': '*content goes here*'}]",
            },
            {"role": "user", "content": f"{m}"},
        ]
        try:
            chat_completion = self.ai.ChatCompletion.create(
                model=self.model, messages=prompt, temperature=0
            )
            return chat_completion
        except Exception as e:
            print(f"Error sending request: {e}")
            return self.error_completion

    def add_summary(self, summary):
        m = [self.messages[0]]
        r: str = summary["choices"][0]["message"]["content"]
        try:
            r_parsed = ast.literal_eval(r)
            for i in r_parsed:
                m.append(i)
        except SyntaxError as e:
            print(f"{e}")

        print("\nSummary complete\n")
        # print(f"\n{self.messages}")
