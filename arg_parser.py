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
    help="Choose a keyword to use. Default: 'computer'\n\n",
)

parser.add_argument(
    "-m",
    "--model",
    nargs=1,
    action="store",
    help="Select a chatgpt model to use. Use argument 'help' to show a list of available models.\n\n",
)

parser.add_argument(
    "-mi",
    "--model-info",
    metavar="model_info",
    nargs=1,
    action="store",
    help="Show information about a particular chatgpt model\n\n",
)

parser.add_argument(
    "-l",
    "--language",
    nargs=1,
    help="Choose a language for the Vosk keyword detectector to use. Use argument 'help'\n"
    + "to show a list of available languages.",
)

parser.add_argument(
    "-a",
    "--agent",
    nargs=1,
    action="store",
    help="Enter path for agent file to use. Use argument 'help' to show a list of available prompts.",
    # TODO: Needs proper prompt-management library for this
)

# parser.add_argument(
#     "-pc",
#     "--prompt-custom",
#     metavar="custom_prompt",
#     type=open,
#     help="Load a custom prompt from a markdown file",
#     # TODO: Add handler
#     # TODO: Needs function for parsing markdown file
# )

parser.add_argument(
    "-sp",
    "--showprompt",
    action="store_true",
    help="Print the initial prompt/agent you are about to use.",
)

parser.add_argument("--sounds", action="store_true", help="Play feedback sounds\n\n")

parser.add_argument(
    "--speak",
    nargs="*",
    action="store",
    help="enable speech synthesis. Cannot be used with --stream. Options are: 'local', 'cloud'.\n\n",
)

parser.add_argument("--stream", action="store_true", help="Stream response text.\n\n")

parser.add_argument(
    "-t",
    "--transcription",
    nargs=1,
    action="store",
    help="Choose a whisper model to use for local transcription. If omitted,\n"
    + "config value transcription will be used. Use argument 'help' to show\n"
    + "a list of available whisper models. Use argument 'cloud' to use\n"
    + "openai cloud transcription.\n\n",
)

parser.add_argument(
    "--temp",
    nargs=1,
    type=float,
    action="store",
    help="Set a temperatature to use for the completion between 0.0 and 2.0.\n "
    + "See openai api docs for more information about 'temperature'.\n\n",
)

parser.add_argument(
    "-pp",
    "--presence-penalty",
    metavar="presence_penalty",
    nargs=1,
    type=float,
    action="store",
    help="Set a presence penalty to use for the completion between 0.0 and 2.0.\n"
    + "See openai api docs for more information about 'presence penalty'.\n\n",
)

parser.add_argument("-log", action="store_true", help="log information to console\n\n")


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
    if help is args:
        print(args.help)

    if args.agent is not None:
        config.AGENT_PATH = args.agent[0]

    if args.stream is True and args.stream is True:
        print("option '--stream' cannot be used with option '--speak'. Continuing.\n\n")

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
            print(f"\nmodel selected: {config.CHAT_MODEL}\n")
        else:
            print(f"{args.model[0]} is not a valid chatgpt model")
            quit()

    if args.showprompt:
        config.ENABLE_PRINT_PROMPT = args.showprompt

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
                f"\nvosk (keyword detector) language selected: {config.VOSK_LANGUAGE}\n\n"
            )
        else:
            print(f"{args.language[0]} is not a valid vosk language")
            quit()

    if args.model_info is not None:
        models = FileManager.read_json("./models.json")
        if args.model_info[0] in models:
            print(json.dumps(models[args.model_info[0]], indent=4))
        quit()

    if args.sounds:
        config.SOUNDS = args.sounds

    if args.stream:
        config.STREAM = args.stream

    if args.speak is not None:
        whisper_info = FileManager.read_json("./whisper.json")
        if len(args.speak) > 0:
            opts = args.speak[0:-1]
        opts = args.speak[0:]
        for opt in opts:
            match opt:
                case "help":
                    print(
                        " [...opts,], [VOICE] options:\n\tlocal: use local transcription\n\tcloud: use openai cloud transcription\n\nvoices: print list of available voices\n\tlanguages: print list of languages supported by cloud\n\nvoices: print list of available voices for cloud\n\nVOICE: select a voice to use."
                    )
                case "languages":
                    print("\nlanguages supported by openai cloud TTS:\n")
                    for lang in whisper_info["languages"]:
                        print(f"\t{lang}")
                    print("\n", end="")
                case "voices":
                    print("\nvoices available for openai cloud TTS:\n")
                    for voice in whisper_info["voices"]:
                        print(f"\t{voice}")
                    print("\n", end="")
                case "cloud" | "local":
                    i = 0
                    if i < 1:
                        config.SPEAK = opt
                        i = i + 1
                    else:
                        print("\ncloud or local cannot be used at the same time.")
        voice = args.speak[-1]
        if args.speak[-1] in whisper_info["voices"]:
            config.VOICE = voice

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
        if args.temp[0] >= 0.0 and args.temp[0] <= 2.0:
            config.TEMPERATURE = args.temp[0]
        else:
            print(
                f"Temperature must be between 0.0 and 2.0. Continuing with default. {config.TEMPERATURE}"
            )

    if args.presence_penalty is not None:
        if args.presence_penalty[0] >= 0.0 and args.presence_penalty[0] <= 2.0:
            config.PRESENCE_PENALTY = args.presence_penalty[0]
        else:
            print(
                f"Temperature must be between 0.0 and 2.0. Continuing with default {config.PRESENCE_PENALTY}."
            )
