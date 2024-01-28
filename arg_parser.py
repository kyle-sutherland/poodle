import argparse
import json
from file_manager import FileManager
import whisper

parser = argparse.ArgumentParser(
    description="Poodle. Talk to chatgpt with your command line.",
    prog="Poodle",
    epilog="By Kyle Sutherland. License: GPL v3. more info: https://github.com/vevleteen-rever/poodle",
    add_help=True,
)


parser.add_argument(
    "-k",
    "--keyword",
    nargs=1,
    action="store",
    help="Choose a keyword to use. Default: 'computer'",
)

parser.add_argument(
    "-m",
    "--model",
    nargs=1,
    action="store",
    help="Select a chatgpt model to use. Use argument 'help' to show a list of available models.",
)

parser.add_argument(
    "-mi",
    "--model-info",
    metavar="model_info",
    nargs=1,
    action="store",
    help="Show information about a particular chatgpt model",
)

parser.add_argument(
    "-l",
    "--language",
    nargs=1,
    help="Choose a language for the Vosk keyword detectector to use. Use argument 'help'\n"
    + "to show a list of available languages.",
)

# parser.add_argument(
#     "-p",
#     "--prompt",
#     nargs=1,
#     action="store",
#     help="Choose a stored prompt by name. Use argument 'help' to show a list of available prompts.",
#     # TODO: Add handler
#     # TODO: Needs proper prompt library for this
# )

# parser.add_argument(
#     "-pc",
#     "--prompt-custom",
#     metavar="custom_prompt",
#     type=open,
#     help="Load a custom prompt from a markdown file",
#     # TODO: Add handler
#     # TODO: Needs function for parsing markdown file
# )

parser.add_argument("--sounds", action="store_true", help="Play feedback sounds")

parser.add_argument(
    "--speak",
    action="store_true",
    help="enable speech synthesis. Cannot be used with --stream. Options are: 'local', 'cloud'.",
)

parser.add_argument("--stream", action="store_true", help="Stream response text.")

parser.add_argument(
    "-t",
    "--transcription",
    nargs=1,
    action="store",
    help="Choose a whisper model to use for local transcription. If omitted,\n"
    + "config value transcription will be used. Use argument 'help' to show\n"
    + "a list of available whisper models. Use argument 'cloud' to use\n"
    + "openai cloud transcription.",
)

parser.add_argument(
    "--temp",
    nargs=1,
    choices=range(0, 2),
    type=float,
    action="store",
    help="Set a temperatature to use for the completion. Default is 1.0",
)

parser.add_argument(
    "-pp",
    "--presence-penalty",
    metavar="presence_penalty",
    nargs=1,
    choices=range(0, 2),
    type=float,
    action="store",
    help="Set a presence penalty to use for the completion. Default is 1.0",
)

parser.add_argument("-log", action="store_true", help="log information to console")


def get_sorted_chat_models_names(models) -> dict:
    model_names = {"gpt-3.5": [], "gpt-4": []}
    for model in models:
        if "gpt-3.5" in model:
            model_names["gpt-3.5"].append(models[model]["name"])
        elif "gpt-4" in model:
            model_names["gpt-4"].append(models[model]["name"])
    return model_names


def ParseArgs(config):
    args = parser.parse_args()
    print(args)
    if help is args:
        print(args.help)
    if args.stream is True and args.stream is True:
        print("option '--stream' cannot be used with option '--speak'")

    if args.keyword is not None:
        config.KEYWORD = args.keyword[0]

    if args.model is not None:
        models = FileManager.read_json("./models.json")
        sorted_models = get_sorted_chat_models_names(models)
        if args.model[0] == "help":
            print("\navailable models:\ngpt-3.5:")
            for model in sorted_models["gpt-3.5"]:
                print(f"\t{model}")
            print("gpt-4:")
            for model in sorted_models["gpt-4"]:
                print(f"\t{model}")
            quit()
        elif args.model[0] in models:
            config.CHAT_MODEL = args.model[0]
            print(f"\nmodel selected: {config.CHAT_MODEL}")
        else:
            print(f"{args.model[0]} is not a valid chatgpt model")
            quit()

    if args.language is not None:
        langs = FileManager.read_json("./vosk_langs.json")
        if args.language[0] == "help":
            print("\navailable vosk (keyword detector) languages:")
            for lang in langs:
                print(f"\t{lang}")
            quit()
        elif args.language[0] in langs:
            config.VOSK_LANGUAGE = args.language[0]
            print(
                f"\nvosk (keyword detector) language selected: {config.VOSK_LANGUAGE}"
            )
        else:
            print(f"{args.language[0]} is not a valid vosk language")
            quit()

    if args.model_info is not None:
        models = FileManager.read_json("./models.json")
        if args.model_info[0] in models:
            print(json.dumps(models[args.model_info[0]], indent=4))
        quit()

    if args.sounds is not None:
        config.SOUNDS = args.sounds

    if args.stream is not None:
        config.STREAM = args.stream

    if args.speak is not None:
        config.SPEAK = args.speak

    if args.transcription is not None:
        if args.transcription[0] == "help":
            print(
                "\navailable whisper models (models will be downloaded automatically):"
            )
            for model in whisper.available_models():
                print(f"\t{model}")
            quit()
        else:
            config.LOCAL_TRANCSCIBER_MODEL = args.transcription[0]

    if args.temp is not None:
        config.TEMPERATURE = args.temp

    if args.presence_penalty is not None:
        config.PRESENCE_PENALTY = args.presence_penalty
