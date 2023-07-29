import os

import openai
import whisper

import config
import json

ai = openai
ai.api_key = os.getenv('OPENAI_API_KEY')
ai.organization = "org-9YiPG54UMFObNmQ2TMOnPCar"
model = 'gpt-3.5-turbo'
reply = ""
messages = [{"role": "system", "content": "you are a helpful assistant"}]


def transcribe_bodies():
    mod = whisper.load_model("base")
    audio_directory = "prompt_bodies_audio"
    while len(os.listdir(audio_directory)) != 0:
        for file in os.listdir(audio_directory):
            result = mod.transcribe(f"{config.PATH_PROMPT_BODIES_AUDIO}{file}")
            print("transcription complete")
            os.remove(f"{config.PATH_PROMPT_BODIES_AUDIO}{file}")
            file = file.rstrip(".wav")
            result_object = json.dumps(result, indent=4)
            with open(f"body_transcriptions/transcription_{file}.json", "w") as outfile:
                outfile.write(result_object)
    do_request()


def do_request():
    b = open_transcript()
    add_user_entry(b)
    start_request(messages)


def open_transcript():
    b = {}
    d = "body_transcriptions/"
    for file in os.listdir(d):
        f = open(f"{d}{file}" "r")
        fd = json.load(f)
        b.update(fd)
    return b


def extract_reply(response):
    return response['choices'][0]['message']['content']


def add_user_entry(body):
    for b in body:
        a = {"role": "user", "content": b['text']}
        messages.append(a)


def start_request(m):
    print("request started")
    chat_completion = ai.ChatCompletion.create(model=model, messages=m)
    print(chat_completion)
