import json
import os
from pathlib import Path


def _config_path() -> Path:
    appdata = os.environ.get("APPDATA", str(Path.home()))
    config_dir = Path(appdata) / "LilAgents"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def load_config() -> dict:
    path = _config_path()
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_config(data: dict) -> None:
    path = _config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_provider() -> str:
    return load_config().get("provider", "claude")


def set_provider(provider: str) -> None:
    data = load_config()
    data["provider"] = provider
    save_config(data)
