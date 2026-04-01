import json
import pytest
from pathlib import Path


def test_load_config_returns_empty_when_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    import config
    result = config.load_config()
    assert result == {}


def test_save_and_load_config(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    import config
    config.save_config({"provider": "gemini"})
    result = config.load_config()
    assert result == {"provider": "gemini"}


def test_get_provider_defaults_to_claude(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    import config
    assert config.get_provider() == "claude"


def test_set_and_get_provider(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    import config
    config.set_provider("gemini")
    assert config.get_provider() == "gemini"


def test_config_file_is_valid_json(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    import config
    config.set_provider("claude")
    config_file = tmp_path / "LilAgents" / "config.json"
    data = json.loads(config_file.read_text())
    assert data["provider"] == "claude"
