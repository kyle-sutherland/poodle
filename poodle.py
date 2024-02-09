from main_logic import PoodleApp
from arg_parser import ParseArgs
import config as conf

def main():
    # Parse command line arguments
    config = ParseArgs(conf)
    # Create and run the Poodle application
    app = PoodleApp(config)
    app.run()

if __name__ == "__main__":
    main()
