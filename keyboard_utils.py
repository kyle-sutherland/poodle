import keyboard
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout


# Function to handle start/stop listening
def toggle_listening():
    # Your code to start/stop listening
    print("Toggled listening state")


# Function to handle text input after a hotkey is pressed
def text_input():
    session = PromptSession()
    with patch_stdout():
        text = session.prompt("text: ")
    # Your code to handle the input text
    print(f"Text added: {text}")


# Register hotkeys
keyboard.add_hotkey(
    "ctrl+alt+l", toggle_listening
)  # Example: Ctrl+Alt+L to toggle listening
keyboard.add_hotkey("ctrl+alt+t", text_input)  # Example: Ctrl+Alt+T to add text

# Keep the program running to listen for hotkeys
keyboard.wait("esc")  # Use Esc key to exit the program
