import getpass
import json
import os
import sys
from pathlib import Path

from google import genai
from google.genai import types

APP_NAME = "SimpleGeminiAgent"
APP_VERSION = "1.0.0"
DEFAULT_MODEL = "gemini-flash-lite-latest"
CONFIG_PATH = Path(__file__).resolve().parent / "config.json"
WORK_DIR = Path.cwd().resolve()
MAX_READ_BYTES = 100_000
MAX_LIST_ENTRIES = 200
MAX_VISIBLE_MODELS = 10
EXCLUDED_MODEL_PARTS = (
    "tts", "image", "embedding", "live", "audio", "robotics", "computer-use", "aqa",
)
PURPLE = "\033[35m"
GREEN = "\033[32m"
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


def resolve_path(path: str) -> Path:
    target = (WORK_DIR / path).resolve()
    if not target.is_relative_to(WORK_DIR):
        raise ValueError("Path is outside the working folder.")
    if target == CONFIG_PATH:
        raise ValueError("Access to the config file is not allowed.")
    return target


def display_path(target: Path) -> str:
    return target.relative_to(WORK_DIR).as_posix() or "."


def list_files(path: str = ".") -> str:
    """List files and folders inside a directory of the working folder.

    Args:
        path: Directory path relative to the working folder. Use "." for the working folder itself.

    Returns:
        One entry per line. Folder names end with "/".
    """
    try:
        target = resolve_path(path)
        if not target.is_dir():
            return f"Error: '{path}' is not a directory."

        lines = []
        for entry in sorted(target.iterdir(), key=lambda item: item.name.lower()):
            if entry.resolve() == CONFIG_PATH:
                continue
            lines.append(entry.name + ("/" if entry.is_dir() else ""))

        if not lines:
            return "The directory is empty."
        if len(lines) > MAX_LIST_ENTRIES:
            extra = len(lines) - MAX_LIST_ENTRIES
            lines = lines[:MAX_LIST_ENTRIES] + [f"... and {extra} more entries"]
        return "\n".join(lines)
    except (ValueError, OSError) as error:
        return f"Error: {error}"


def read_file(path: str) -> str:
    """Read a text file from the working folder.

    Args:
        path: File path relative to the working folder.

    Returns:
        The file content. Large files are truncated and marked as such.
    """
    try:
        target = resolve_path(path)
        if not target.is_file():
            return f"Error: '{path}' is not a file."

        with target.open("rb") as file:
            data = file.read(MAX_READ_BYTES + 1)

        if b"\0" in data:
            return "Error: the file looks binary and cannot be read as text."

        truncated = len(data) > MAX_READ_BYTES
        text = data[:MAX_READ_BYTES].decode("utf-8", errors="replace")
        if truncated:
            text += f"\n\n[Truncated: only the first {MAX_READ_BYTES} bytes are shown]"
        return text
    except (ValueError, OSError) as error:
        return f"Error: {error}"


def write_file(path: str, content: str) -> str:
    """Create a new file or overwrite an existing one in the working folder.

    The user is asked for confirmation before anything is written.

    Args:
        path: File path relative to the working folder.
        content: The full text content to write to the file.

    Returns:
        A message saying whether the file was written or the user declined.
    """
    try:
        target = resolve_path(path)
        if target.is_dir():
            return f"Error: '{path}' is a directory."

        action = "Overwrite existing file" if target.exists() else "Create file"
        question = f"\n[{action} '{display_path(target)}', {len(content)} chars. Confirm? y/n]: "
        try:
            answer = input(question).strip().lower()
        except (KeyboardInterrupt, EOFError):
            answer = "n"

        if answer not in {"y", "yes"}:
            return "The user declined the write. Nothing was changed."

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"File written: {display_path(target)}"
    except (ValueError, OSError) as error:
        return f"Error: {error}"


CHAT_CONFIG = types.GenerateContentConfig(tools=[list_files, read_file, write_file])


def read_key() -> str:
    """Block until a key is pressed and return 'up', 'down', 'enter' or ''."""
    if os.name == "nt":
        import msvcrt

        char = msvcrt.getwch()
        if char in ("\x00", "\xe0"):
            return {"H": "up", "P": "down"}.get(msvcrt.getwch(), "")
        if char == "\r":
            return "enter"
        if char == "\x03":
            raise KeyboardInterrupt
        return ""

    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        char = os.read(fd, 1)
        if char == b"\x1b":
            if select.select([fd], [], [], 0.05)[0]:
                return {b"[A": "up", b"[B": "down"}.get(os.read(fd, 2), "")
            return ""
        if char in (b"\r", b"\n"):
            return "enter"
        return ""
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def choose_model(models: list[str], current: str) -> str:
    index = models.index(current) if current in models else 0
    top = 0
    printed = 0

    print("Choose a model (Up/Down to move, Enter to confirm):")
    while True:
        if index < top:
            top = index
        elif index >= top + MAX_VISIBLE_MODELS:
            top = index - MAX_VISIBLE_MODELS + 1

        lines = []
        for position in range(top, min(top + MAX_VISIBLE_MODELS, len(models))):
            if position == index:
                lines.append(f"{GREEN}> {models[position]}{RESET}")
            else:
                lines.append(f"  {models[position]}")

        if printed:
            sys.stdout.write(f"\033[{printed}A\033[J")
        sys.stdout.write("\n".join(lines) + "\n")
        sys.stdout.flush()
        printed = len(lines)

        key = read_key()
        if key == "up":
            index = (index - 1) % len(models)
        elif key == "down":
            index = (index + 1) % len(models)
        elif key == "enter":
            return models[index]


def list_models(client) -> list[str]:
    names = set()
    for model in client.models.list():
        name = (model.name or "").removeprefix("models/")
        actions = model.supported_actions or []
        if "generateContent" not in actions or not name.startswith("gemini"):
            continue
        if any(part in name for part in EXCLUDED_MODEL_PARTS):
            continue
        names.add(name)
    return sorted(names)


def select_startup_model(client, config: dict) -> str:
    saved = str(config.get("model", "")).strip() or DEFAULT_MODEL
    if not sys.stdin.isatty():
        return saved

    try:
        models = list_models(client)
    except Exception as error:
        print(f"Cannot load the model list: {error}")
        return saved

    if saved not in models:
        models.insert(0, saved)

    try:
        chosen = choose_model(models, saved)
    except KeyboardInterrupt:
        print()
        raise SystemExit(0)

    if chosen != config.get("model"):
        config["model"] = chosen
        write_config(config)
    return chosen


def switch_model(client, chat, config: dict, new_model: str):
    """Return a new chat on new_model with the same history, or None on failure."""
    try:
        client.models.get(model=new_model)
        new_chat = client.chats.create(
            model=new_model,
            config=CHAT_CONFIG,
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
    print(f"Working folder: {WORK_DIR}\n")

    config = read_config()
    client = genai.Client(api_key=get_api_key(config))
    model = select_startup_model(client, config)
    print(f"Model: {model}")
    chat = client.chats.create(model=model, config=CHAT_CONFIG)

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

        print(f"Gemini: {response.text or '(empty response)'}")


if __name__ == "__main__":
    main()