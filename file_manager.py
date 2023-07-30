# file_manager.py
import os
from datetime import datetime
import config
import json


class FileManager:
    @staticmethod
    def get_datetime_string() -> str:
        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y_%H-%M-%S")
        return timestamp

    @staticmethod
    def write_file(file_path, content):
        with open(file_path, "w") as outfile:
            outfile.write(content)

    @staticmethod
    def read_file(file_path):
        with open(file_path, "r") as infile:
            return infile.read()

    @staticmethod
    def delete_transcription(file_name):
        file_path = os.path.join(config.TRANSCRIPTION_PATH, file_name)
        os.remove(file_path)

    @staticmethod
    def save_json(file_name, content):
        with open(file_name, 'w') as f:
            json.dump(content, fp=f, indent=4)

    @staticmethod
    def mark_as_read(file_name):
        original_file_path = os.path.join(config.TRANSCRIPTION_PATH, file_name)
        marked_file_path = os.path.join(config.TRANSCRIPTION_PATH, f"_read_{file_name}")
        os.rename(original_file_path, marked_file_path)

    @staticmethod
    def read_transcriptions(directory):
        transcriptions = []
        for file in os.listdir(directory):
            if not file.startswith("_read_"):
                file_path = os.path.join(directory, file)
                if os.path.exists(file_path):
                    if os.stat(file_path).st_size != 0:
                        with open(file_path, "r") as f:
                            try:
                                transcription = json.load(f)
                                transcriptions.append(transcription)
                            except ValueError as e:
                                print(f"Error reading {file_path}: {e}")
                        FileManager.mark_as_read(file)
                    else:
                        print(f"File {file_path} is empty.")
                else:
                    print(f"File {file_path} does not exist.")
            else:
                continue
        return transcriptions
