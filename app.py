import getpass
import json
import os
from pathlib import Path

from google import genai

APP_NAME = "SimpleGeminiAgent"
APP_VERSION = "1.0.0"
DEFAULT_MODEL = "gemini-flash-lite-latest"
CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
PURPLE = "\033[35m"
RESET = "\033[0m"


def read_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        print("Config file is unreadable, ignoring it.")
        return {}
    return data if isinstance(data, dict) else {}


def write_config(config: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
    if os.name != "nt":
        os.chmod(CONFIG_PATH, 0o600)


def get_api_key(config: dict) -> str:
    key = str(config.get("api_key", "")).strip()
    if key:
        return key

    key = getpass.getpass("Enter Gemini API key: ").strip()
    if not key:
        raise SystemExit("API key is empty.")

    config["api_key"] = key
    write_config(config)
    return key


def switch_model(client, chat, config: dict, new_model: str):
    """Return a new chat on new_model with the same history, or None on failure."""
    try:
        client.models.get(model=new_model)
        new_chat = client.chats.create(
            model=new_model,
            history=chat.get_history(),
        )
    except Exception as error:
        print(f"Cannot switch to '{new_model}': {error}")
        return None

    config["model"] = new_model
    write_config(config)
    return new_chat


def main() -> None:
    if os.name == "nt":
        os.system("")  # enables ANSI escape codes in the Windows console

    print(f"{PURPLE}{APP_NAME}{RESET} {APP_VERSION}")

    config = read_config()
    client = genai.Client(api_key=get_api_key(config))
    model = str(config.get("model", "")).strip() or DEFAULT_MODEL
    chat = client.chats.create(model=model)

    while True:
        try:
            user_text = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not user_text:
            continue
        if user_text.lower() in {"/exit", "/quit"}:
            break

        command, _, argument = user_text.partition(" ")
        if command == "/model":
            new_model = argument.strip()
            if not new_model:
                print(f"Current model: {model}")
                continue
            new_chat = switch_model(client, chat, config, new_model)
            if new_chat is not None:
                chat, model = new_chat, new_model
                print(f"Switched to {model}")
            continue

        try:
            response = chat.send_message(user_text)
        except Exception as error:
            print(f"Request failed: {error}")
            continue

        print(f"Gemini: {response.text}")


if __name__ == "__main__":
    main()