import argparse
import config

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
    help="Select a chatgpt model to use. Omit follower to show a list of available models.",
)

parser.add_argument(
    "-mi",
    "--model-info",
    nargs=1,
    action="store",
    help="Show information about a particular chatgpt model",
)

parser.add_argument(
    "-l",
    "--language",
    nargs=1,
    help="Choose a language fort the Vosk keyword detectector to use.",
)

parser.add_argument(
    "-p",
    "--prompt",
    nargs=1,
    action="store",
    help="Choose a stored prompt by name. Omit follower to show a list of available prompts.",
)

parser.add_argument(
    "-pc",
    "--prompt-custom",
    type=open,
    help="Load a custom prompt from a markdown file",
)

parser.add_argument("--sound", action="store_true", help="Play feedback sounds")

parser.add_argument(
    "--speak",
    action="store_true",
    help="enable speech synthesis. Cannot be used with --stream",
)

parser.add_argument("--stream", action="store_true", help="Stream response text.")

parser.add_argument(
    "-t",
    "--transcription",
    nargs=1,
    action="store",
    help="Choose to use local or cloud-based transcription. Default is cloud. Both options use openai models. If you choose local, the model will be downloaded automatically (~50mB).",
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
    "--presence-penalty",
    nargs=1,
    choices=range(0, 2),
    type=float,
    action="store",
    help="Set a presence penalty to use for the completion. Default is 1.0",
)

parser.add_argument("-log", action="store_true", help="log information to console")


def ParseArgs():
    args = parser.parse_args()
    print(args)
    if help is args:
        print(args.help)
    match args.stream:
        case True:
            config.STREAM_RESPONSE = True
        case False:
            config.STREAM_RESPONSE = False
        case None:
            config.STREAM_RESPONSE = False
