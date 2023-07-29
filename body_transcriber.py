# body_transcriber.py
import os
import time

import openai
import whisper
import config
import json

ai = openai
ai.api_key = os.getenv('OPENAI_API_KEY')
ai.organization = "org-9YiPG54UMFObNmQ2TMOnPCar"
model = 'gpt-3.5-turbo'
messages = [{"role": "system", "content": "you are a helpful assistant"}]


def transcribe_bodies():
    mod = whisper.load_model("base")
    audio_directory = "prompt_bodies_audio"
    while len(os.listdir(audio_directory)) != 0:
        for file in os.listdir(audio_directory):
            result = mod.transcribe(f"{config.PATH_PROMPT_BODIES_AUDIO}{file}")
            # print("transcription complete")
            os.remove(f"{config.PATH_PROMPT_BODIES_AUDIO}{file}")
            file = file.rstrip(".wav")
            result_object = json.dumps(result, indent=4)
            with open(f"body_transcriptions/transcription_{file}.json", "w") as outfile:
                outfile.write(result_object)
    do_request()


def do_request():
    b = open_transcript()
    add_user_entry(b)
    resp = send_request(messages)
    # save_response(resp)
    reply = extract_reply(resp)
    print(reply)
    add_reply_entry(resp)


def mark_as_read(filename, directory):
    os.rename(os.path.join(directory, filename), os.path.join(directory, "_read_" + filename))


def open_transcript():
    b = []
    d = "body_transcriptions/"
    for file in os.listdir(d):
        if file.startswith("_read_"):
            continue
        file_path = os.path.join(d, file)
        if os.path.exists(file_path):
            if os.stat(file_path).st_size != 0:
                # print(f"Opening {file_path}")
                with open(file_path, "r") as f:
                    try:
                        fd = json.load(f)
                        b.append(fd)
                    except ValueError as e:
                        print(f"Error reading {file_path}: {e}")
                # print(f"Finished reading {file_path}")
                mark_as_read(file, d)
            else:
                print(f"File {file_path} is empty.")
        else:
            print(f"File {file_path} does not exist.")
    return b


def extract_reply(response):
    return response['choices'][0]['message']['content']


def add_reply_entry(response):
    rep = response['choices'][0]['message']
    messages.append(rep)


def add_user_entry(body):
    for b in body:
        a = {"role": "user", "content": b['text']}
        messages.append(a)


def send_request(m):
    # print("request started")
    try:
        chat_completion = ai.ChatCompletion.create(model=model, messages=m)
        return chat_completion
    except Exception as e:
        print(f"Error sending request: {e}")


def save_response(res):
    timestamp = time.time()
    with open(f"response_log/response_{timestamp}.json") as out:
        out.write(res)
