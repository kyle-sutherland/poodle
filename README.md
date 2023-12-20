
# Voice Assistant Program

This program serves as a voice-based chat interface, leveraging the capabilities of keyword detection, audio transcription, and the OpenAI API to communicate with users.

## Purpose
The program continuously listens for a specific keyword. Once detected, it starts transcribing user speech, sends the transcribed text to OpenAI for processing, and returns the response to the user. 

## Usage

### Setting up the Environment

1. Ensure you have [Conda or Miniconda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) installed on your system.
2. Open a terminal and navigate to the project directory.
3. To create a Conda environment using the provided `environment.yml` file, run:
```bash
conda env create -f environment.yml
```
4. Create project folders, run:
```bash
mkdir ./conversations ./api_keys ./body_transcriptions ./prompt_bodies_audio ./response_log
```
5. You will need an OpenAI API key. Grab yours and paste it into a file called `keys` inside `./api_keys`

### Installing PyTorch

Visit the [official PyTorch website](https://pytorch.org/get-started/locally/) to get the installation command tailored for your system and hardware (CPU, CUDA). Follow the instructions on the site to install PyTorch in the Conda environment you just created.

### Running the Program

1. Activate the Conda environment:
```bash
conda activate poodle
```
Replace 'poodle' with your environment name if you specified a different one.

2. Navigate to the project directory and run the program:
```bash
python __main__.py
```
The default keyword to start Poodle listening is "computer". After the program prints "Ready", simply speak the keyword and Poodle will begin the process of transcribing your speech until a pause is detected. It will then send the API request with the transcribed message. The To change the initial prompt, change the string contained in the property `initial_prompt` in the `ChatSession` class in `chat_manager.py`.
## Feedback and Contributions

Feel free to provide feedback, report bugs, or make contributions to enhance the program's capabilities.
