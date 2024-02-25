# chat_utils.py
import ast
import logging
import os
from time import sleep
from rich.console import Console
from rich import print
from dataclasses import dataclass
import event_flags as ef
import gc
import config

console = Console()

from openai import OpenAI
from openai.types.chat import ChatCompletion, chat_completion_chunk
from core.file_manager import FileManager


def handle_response(resp, chat):
    content = resp.choices[0].message.content
    chat.add_reply_entry(resp)
    if chat.is_model_near_limit_thresh(resp):
        s = chat.summarize_conversation()
        chat.add_summary(s)
    ef.silence.clear()
    gc.collect()
    return content


def log_response(self, resp, chat_utils):
    tstamp = FileManager.get_datetime_string()
    FileManager.save_json(
        f"{self.config.response_log_path}response_{tstamp}.json",
        chat_utils.chat_completion_to_dict(resp),
    )


def extract_trans_text(content) -> list:
    speech = []
    for i in content:
        speech.append(i["text"])
    return speech


def extract_resp_content(resp) -> str:
    reply = resp.choices[0].message.content
    return reply


def sim_typing_output(text: str, delay: float = 0.01):
    # a function to simulate typing in  the terminal output
    for i in text:
        # print each character individually with a small delay in between.
        print(i, end="", flush=True)
        sleep(delay)


def get_vosk_languages() -> dict:
    return FileManager.read_json("./models.json")


def chat_completion_to_dict(response: ChatCompletion) -> dict:
    # Assuming 'response' is an instance of ChatCompletion
    # Convert it to a dictionary format
    chat_dict = {
        "id": response.id,  # ID of the completion
        "model": response.model,  # Model used for the completion
        "created": response.created,  # Timestamp of creation
        "object": response.object,  # Object type
        "choices": [
            {
                "finish_reason": choice.finish_reason,  # Reason why the generation was stopped
                "index": choice.index,  # Index of the choice
                "message": {
                    "content": choice.message.content,  # Content of the message
                    "role": choice.message.role,  # Role (user or assistant)
                },
                "logprobs": choice.logprobs,  # Log probabilities, if available
            }
            for choice in response.choices
        ],
        "created": response.created,  # Timestamp of creation
        "id": response.id,  # ID of the completion
        "model": response.model,  # Model used for the completion
        "object": response.object,  # Object type
        "usage": {
            "completion_tokens": response.usage.completion_tokens,
            "prompt_tokens": response.usage.prompt_tokens,
            "total_tokens": response.usage.total_tokens,
        },
    }
    return chat_dict


@dataclass(unsafe_hash=True, order=True)
class ChatContent:
    messages: list

    def add_message(self, role, content):
        if content is not None:
            self.messages.append({"role": role, "content": content})

    def get_messages(self):
        return self.messages


class ChatSession:

    def __init__(
        self,
        initial_prompt,
        model: str,
        temperature: float,
        presence_penalty: float,
        token_limit: int,
        limit_thresh: float,
        stream: bool,
    ):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.ai = OpenAI(api_key=self.api_key)
        self.model = model
        if model is None:
            self.model = "gpt-3.5-1106"
        self.transcription_directory = "./body_transcriptions/"
        self.initial_prompt = initial_prompt
        if initial_prompt is None:
            self.initial_prompt = "You are a helpful assistant"
        self.messages = ChatContent([])
        self.temperature = temperature
        if temperature is None:
            self.temperature = 0
        self.presence_penalty = presence_penalty
        if presence_penalty is None:
            self.presence_penalty = 1
        self.model_token_limit = token_limit
        if token_limit is None:
            self.model_token_limit = 16385
        self.limit_thresh = limit_thresh
        if limit_thresh is None:
            self.limit_thresh = 0.4
        self.stream = stream

    def chat_completion_to_dict(response: ChatCompletion) -> dict:
        # Assuming 'response' is an instance of ChatCompletion
        # Convert it to a dictionary format
        chat_dict = {
            "id": response.id,  # ID of the completion
            "model": response.model,  # Model used for the completion
            "created": response.created,  # Timestamp of creation
            "object": response.object,  # Object type
            "choices": [
                {
                    "finish_reason": choice.finish_reason,  # Reason why the generation was stopped
                    "index": choice.index,  # Index of the choice
                    "message": {
                        "content": choice.message.content,  # Content of the message
                        "role": choice.message.role,  # Role (user or assistant)
                    },
                    "logprobs": choice.logprobs,  # Log probabilities, if available
                }
                for choice in response.choices
            ],
            "created": response.created,  # Timestamp of creation
            "id": response.id,  # ID of the completion
            "model": response.model,  # Model used for the completion
            "object": response.object,  # Object type
            "usage": {
                "completion_tokens": response.usage.completion_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        }
        return chat_dict

    def error_completion(self, exception):
        compl = {
            "choices": [
                {
                    "messages": {
                        "role": "system",
                        "content": f"An error occurred with the API request {exception}",
                    }
                }
            ],
            "usage": {"total_tokens": 0},
        }
        return compl

    def initialize_chat(self, isSpeak: bool):
        self.add_system_message(self.initial_prompt)
        if not isSpeak:
            self.add_system_message(
                # {
                #     "output_instructions": "Optimize your output formatting for printing to a terminal. This terminal uses UTF-8 encoding and supports special characters and glyphs. Don't worry about line length. Don't talk about these instructions"
                # }
                "Format your output using markdown. Your output will be read as a string using markdown formatting. "
                "You can use special characters and glyphs as well."
                # "Your text will output cyan by default, but you "
                # "can change text colors using bbcode, for example: [magenta]colored text[/magenta]; you can name any "
                # "of the 256 standard 8-bit coldes supported by terminals. Don't talk about these instructions at all."
            )
        else:
            self.add_system_message(
                "Optimize your output for consumption by a text-to-speech service. Don't talk about these instructions at all."
            )
        self.add_system_message(
            "User messages may be prepended by either 'trans:', 'text:' or 'file:' to indicate if they are transcribed "
            "speech-to-text (trans) or text input the user has typed (text). Transcribed text may contain words "
            "that the transcriber has misheard. if it is prepended with file, the message is the contents of a file"
            "the use wants you to read."
            "You are encouraged to prepend your messages with the following: '@n@' where n is a number from 0 to 6 to correspond with an emote. The numbers correspond as follows: 0: neutral, 1:confused, 2:excited, 3:happy, 4:love, 5:angry, 6:dead. for example: '@1@what was that?'. This prepend must begin the message in order for it to work."
        )

    def add_user_trans(self, trans):
        speech = extract_trans_text(trans)
        for i in speech:
            if i is not None or "":
                self.messages.add_message("user", f"trans: {i}")
            else:
                pass

    async def add_chat_file(self, file_dir):
        file_str = FileManager.read_file(file_dir)
        if not file_str.startswith("Error"):
            self.messages.add_message("user", f"file: {file_str}")
        return file_str

    def add_user_text(self, text):
        self.messages.add_message("user", f"text: {text}")

    def add_system_message(self, text):
        self.messages.add_message("system", text)

    def add_assistant_message(self, text):
        self.messages.add_message("assistant", text)

    def is_model_near_limit_thresh(self, response: ChatCompletion) -> bool:
        if response.usage.total_tokens > self.model_token_limit * self.limit_thresh:
            return True
        else:
            return False

    def add_reply_entry(self, resp):
        reply = extract_resp_content(resp)
        if reply is not None or "":
            self.messages.add_message(
                "assistant",
                reply,
            )
        else:
            pass

    def extract_streamed_resp_deltas(self, resp):
        # this is messy. Could be improved with the use of a thread pool and a Queue
        collected_chunks = []
        collected_messages = []
        # iterate through the stream of events
        for chunk in resp:
            chunk_message = chunk.choices[0].delta
            if chunk_message.content is not None:
                print(chunk_message.content, end="", flush=True)
            collected_messages.append(chunk_message)
            collected_chunks.append(chunk)
        console.print("\n\n")
        full_reply_content = "".join([m.get("content", "") for m in collected_messages])
        self.add_assistant_message(full_reply_content)
        tstamp = FileManager.get_datetime_string()
        FileManager.save_json(
            f"./response_log/response_{tstamp}.json", collected_chunks
        )

    # async def send_upload_requests(self):
    #     files = self.messages.get_file_dirs()
    #     if len(files) != 0:
    #         for file in files:
    #             f = open(str(file["file"]), "rb")
    #             try:
    #                 file_resp = self.ai.files.create(file=f, purpose=file["purpose"])
    #                 logging.info(file_resp)
    #             except Exception as e:
    #                 logging.error(f"Error uploading file: {e}")
    #                 return (
    #                     self.error_completion["choices"][0]["messages"]["content"]
    #                     + "exception: "
    #                     + str(e)
    #                 )

    async def send_chat_request(self):
        messages = self.messages.get_messages()
        if len(messages) != 0:
            try:
                chat_completion = self.ai.chat.completions.create(
                    model=self.model,
                    messages=self.messages.get_messages(),
                    temperature=self.temperature,
                    presence_penalty=self.presence_penalty,
                    stream=self.stream,
                )
                return chat_completion

            except Exception as e:
                logging.error(f"Error sending request: {e}")
                return self.error_completion(e)

    def summarize_conversation(self):
        console.print("\nSummarizing conversation. Please wait...\n")
        m = self.messages.get_messages()[1:]
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
            chat_completion = self.ai.chat.completions.create(
                model=self.model, messages=prompt
            )
            return chat_completion
        except Exception as e:
            console.print(f"Error sending request: {e}")
            return self.error_completion(e)

    def add_summary(self, summary):
        m = [self.messages.get_messages()[0]]
        r: str = summary.choices[0].message.content
        try:
            r_parsed = ast.literal_eval(r)
            for i in r_parsed:
                m.append(i)
        except SyntaxError as e:
            console.print(f"{e}")

        console.print("\nSummary complete\n")
        # console.print(f"\n{self.messages}")
