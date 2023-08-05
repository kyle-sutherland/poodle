
# Voice Assistant Program

This program serves as a voice-based chat interface, leveraging the capabilities of keyword detection, audio transcription, and the OpenAI API to communicate with users.

## Purpose
The program continuously listens for a specific keyword. Once detected, it starts transcribing user speech, sends the transcribed text to OpenAI for processing, and returns the response to the user. 

## Usage

### Setting up the Environment

1. Ensure you have [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) installed on your system.
2. Navigate to the project directory.
3. To create a Conda environment using the provided `environment.yml` file, run:
```bash
conda env create -f environment.yml
```


### Installing PyTorch

Visit the [official PyTorch website](https://pytorch.org/get-started/locally/) to get the installation command tailored for your system and hardware (CPU, CUDA). Follow the instructions on the site to install PyTorch in the Conda environment you just created.

### Running the Program

1. Activate the Conda environment:
```bash
conda activate <environment_name>
```
Replace `<environment_name>` with the name of the environment specified in the `environment.yml` file.

2. Navigate to the project directory and run the program:
```bash
python __main__.py
```

## Feedback and Contributions

Feel free to provide feedback, report bugs, or make contributions to enhance the program's capabilities.
