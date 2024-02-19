# file_manager.py
import logging
import os
from datetime import datetime

from openai.types.chat import ChatCompletion
from config import Configurator
import json


class FileManager:
    """
    Utility class to handle file operations, such as reading, writing,
    and managing transcription files.
    """

    @staticmethod
    def search_dict_by_key(data, target):
        for key, value in data.items():
            if isinstance(value, dict):
                yield from FileManager.search_dict_by_key(value, target)
            elif key == target:
                yield value

    @staticmethod
    def get_datetime_string() -> str:
        """Get the current datetime as a formatted string."""
        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y_%H-%M-%S")
        return timestamp

    @staticmethod
    def write_file(file_path: str, content: str) -> None:
        try:
            """Write content to a file."""
            with open(file_path, "w") as outfile:
                outfile.write(content)
        except Exception as e:
            logging.error(e)

    @staticmethod
    def read_file(file_path: str) -> str:
        try:
            """Read content from a file."""
            with open(file_path, "r") as infile:
                return infile.read()
        except Exception as e:
            return f"Error reading file: {e}"

    @staticmethod
    def read_json(file_path: str) -> dict:
        """read json file and return contents as dict"""
        data = None
        try:
            with open(file_path, "r") as infile:
                data = json.load(infile)
            return data
        except Exception as e:
            logging.error(e)
            return {"error": e}

    @staticmethod
    def delete_transcription(file_name: str, path):
        """Delete a transcription file."""
        file_path = os.path.join(path, file_name)
        os.remove(file_path)

    @staticmethod
    def save_json(file_name: str, content: dict | list | ChatCompletion):
        """Save content as a JSON file."""
        try:
            with open(file_name, "w") as f:
                json.dump(content, fp=f, indent=4)
        except Exception as e:
            logging.error(e)

    @staticmethod
    def mark_as_read(file_name: str, path: str):
        """Mark a transcription file as read by renaming it."""
        original_file_path = os.path.join(path, file_name)
        marked_file_path = os.path.join(path, f"_read_{file_name}")
        os.rename(original_file_path, marked_file_path)

    @staticmethod
    def read_transcriptions(path: str) -> list:
        """Read transcriptions from a directory."""
        transcriptions = []
        for file in os.listdir(path):
            if not file.startswith("_read_"):
                file_path = os.path.join(path, file)
                if os.path.exists(file_path):
                    if os.stat(file_path).st_size != 0:
                        with open(file_path, "r") as f:
                            try:
                                transcription = json.load(f)
                                transcriptions.append(transcription)
                            except ValueError as e:
                                logging.error(f"Error reading {file_path}: {e}")
                        FileManager.mark_as_read(file, path)
                    else:
                        logging.error(f"File {file_path} is empty.")
                else:
                    logging.error(f"File {file_path} does not exist.")
            else:
                continue
        return transcriptions

    @staticmethod
    def clear_transcriptions(directory: str) -> None:
        for file in os.listdir(directory):
            if file.startswith("_read_"):
                os.remove(file)
