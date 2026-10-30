import getpass
import json
import os
from pathlib import Path

from google import genai

APP_NAME = "SimpleGeminiAgent"
APP_VERSION = "1.0.0"
MODEL_NAME = "gemini-flash-lite-latest"
CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
PURPLE = "\033[35m"
RESET = "\033[0m"


def load_api_key() -> str:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            key = str(data.get("api_key", "")).strip()
            if key:
                return key
        except (json.JSONDecodeError, OSError):
            print("Config file is unreadable, asking for the key again.")

    key = getpass.getpass("Enter Gemini API key: ").strip()
    if not key:
        raise SystemExit("API key is empty.")

    CONFIG_PATH.write_text(
        json.dumps({"api_key": key}, indent=2),
        encoding="utf-8",
    )
    if os.name != "nt":
        os.chmod(CONFIG_PATH, 0o600)
    return key


def main() -> None:
    if os.name == "nt":
        os.system("")  # enables ANSI escape codes in the Windows console

    print(f"{PURPLE}{APP_NAME}{RESET} {APP_VERSION}")

    client = genai.Client(api_key=load_api_key())
    chat = client.chats.create(model=MODEL_NAME)

    while True:
        try:
            user_text = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit"}:
            break

        try:
            response = chat.send_message(user_text)
        except Exception as error:
            print(f"Request failed: {error}")
            continue

        print(f"Gemini: {response.text}")


if __name__ == "__main__":
    main()