# SimpleGeminiAgent

A simple terminal agent built on top of Google Gemini. It can look through files on your computer, read them, and create or edit them, but only after you confirm. Think of it as an opencode-style assistant that is not focused on coding.

## Features

- Chat with Gemini right in your terminal
- Model selection on every start: pick a model from the list with the arrow keys
- Three tools for working with files:
  - list files
  - read a file
  - write a file (always asks for your confirmation first)
- The API key is entered once with hidden input and stored locally

## Requirements

- Python 3.10 or newer
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/)

## Installation

```bash
git clone <repository-url>
cd SimpleGeminiAgent
pip install -r requirements.txt
```

## Usage

Run the program from the folder you want the agent to work in:

```bash
python main.py
```

The agent can only see and change files inside the folder it was started from. The current working folder is shown at startup.

On the first run the program asks for your Gemini API key. The input is hidden, like a password prompt. The key is saved to `config.json` next to the script, so you only enter it once.

After that you choose a model: use the Up and Down arrows to move, the highlighted (green) model is the selected one, and press Enter to confirm. The cursor starts on the model you used last time.

Example session:

```
SimpleGeminiAgent 1.0.0
Working folder: /home/user/notes

Choose a model (Up/Down to move, Enter to confirm):
> gemini-flash-lite-latest
  ...
Model: gemini-flash-lite-latest

You: Hi, create a file hello.txt and write "Hello from Gemini!" in it
[Create file 'hello.txt', 18 chars. Confirm? y/n]: y
Gemini: Done, here is your file hello.txt
You: Thanks!
Gemini: You're welcome! If you need anything, I'm always here.
```

If your terminal does not support interactive input (for example, the run window of some IDEs), the menu is skipped and the last used model is taken. Run the program from a regular terminal to see the menu.

## Commands

| Command | Description |
| --- | --- |
| `/model` | Show the current model |
| `/model <name>` | Switch to another model without losing the conversation |
| `/exit`, `/quit` | Leave the chat (Ctrl+C works too) |

## Tools

| Tool | What it does |
| --- | --- |
| `list_files` | Lists files and folders in a directory of the working folder |
| `read_file` | Reads a text file; large files are truncated, binary files are rejected |
| `write_file` | Creates or overwrites a file after your `y/n` confirmation |

## Safety

- Every file write requires your explicit confirmation. The confirmation is shown by the program itself, so the model cannot skip it.
- The agent works only inside the working folder and cannot access paths outside of it. Start it only in a folder you are fine with showing to the model.
- `config.json` is never exposed to the model: it is excluded from file listing and reading.
- `config.json` contains your API key and is listed in `.gitignore`. Never commit it.

## Configuration

`config.json` is created automatically on the first run and updated when you pick a model:

```json
{
  "api_key": "your-key-here",
  "model": "gemini-flash-lite-latest"
}
```

To change the key, edit this file or delete it and start the program again.

## License

This project is licensed under the [MIT License](LICENSE).