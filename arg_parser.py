import argparse
from chat_manager import get_chat_models_names

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
    nargs=1,
    action="store",
    help="Show information about a particular chatgpt model",
    # TODO: Add handler
)

parser.add_argument(
    "-l",
    "--language",
    nargs=1,
    help="Choose a language fort the Vosk keyword detectector to use. Use argument 'help' to show a list of available languages.",
    # TODO: Add handler
)

parser.add_argument(
    "-p",
    "--prompt",
    nargs=1,
    action="store",
    help="Choose a stored prompt by name. Use argument 'help' to show a list of available prompts.",
    # TODO: Add handler
    # TODO: Needs proper prompt library for this
)

parser.add_argument(
    "-pc",
    "--prompt-custom",
    metavar="custom_prompt",
    type=open,
    help="Load a custom prompt from a markdown file",
    # TODO: Add handler
    # TODO: Needs function for parsing markdown file
)

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
    action="store",
    help="Choose a model to use transcription. If omitted, config value transcription will be used (default cloud).",
    # TODO: make list functionality for this
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
    "-pp" "--presence-penalty",
    metavar="presence_penalty",
    nargs=1,
    choices=range(0, 2),
    type=float,
    action="store",
    help="Set a presence penalty to use for the completion. Default is 1.0",
)

parser.add_argument("-log", action="store_true", help="log information to console")


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
        models = get_chat_models_names()
        if args.model[0] == "help":
            print("\navailable models:\ngpt-3.5:")
            for model in models["gpt-3.5"]:
                print(f"\t{model}")
            print("gpt-4:")
            for model in models["gpt-4"]:
                print(f"\t{model}")
            quit()
        elif args.model is models["gpt-3.5"] or args.model is models["gpt-4"]:
            config.CHAT_MODEL = args.model[0]
        else:
            print(f"{args.model[0]} is not a valid chatgpt model")
            quit()

    if args.sounds is not None:
        config.SOUNDS = args.sounds

    if args.stream is not None:
        config.STREAM = args.stream

    if args.speak is not None:
        config.SPEAK = args.speak

    if args.transcription is not None:
        if args.transcription[0] == "help":
            pass
            # TODO: make list of whisper models
        else:
            config.LOCAL_TRANCSCIBER_MODEL = args.transcription[0]

    if args.temp is not None:
        config.TEMPERATURE = args.temp

    if args.presence_penalty is not None:
        config.PRESENCE_PENALTY = args.presence_penalty
