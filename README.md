# SimpleGeminiAgent

A simple terminal agent built on top of Google Gemini. It can look through files on your computer, read them, and create or edit them, but only after you confirm. Think of it as an opencode-style assistant that is not focused on coding.

## Features (v1.0.0)

- Chat with Gemini right in your terminal
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
pip install google-genai
```

## Usage

```bash
python main.py
```

On the first run the program asks for your Gemini API key. The input is hidden, like a password prompt. The key is saved to `config.json` next to the script, so you only enter it once.

Example session:

```
SimpleGeminiAgent 1.0.0

You: Hi, create a file hello.txt and write "Hello from Gemini!" in it
Gemini: Done, here is your file hello.txt
You: Thanks!
Gemini: You're welcome! If you need anything, I'm always here.
```

Type `exit` or `quit` (or press Ctrl+C) to leave the chat.

## Safety

- Every file write requires your explicit confirmation. The confirmation is shown by the program itself, so the model cannot skip it.
- The agent works only inside its working folder and cannot access paths outside of it.
- `config.json` is never exposed to the model: it is excluded from file listing and reading.
- `config.json` contains your API key and is listed in `.gitignore`. Never commit it.

## Configuration

`config.json` is created automatically on the first run:

```json
{
  "api_key": "your-key-here"
}
```

To change the key, edit this file or delete it and start the program again.

## License

MIT License