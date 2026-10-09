from __future__ import annotations

import importlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUSTOM_TOKEN = re.compile(r"<a?:[A-Za-z0-9_~]+:[0-9]{15,}>\Z")


def _reload_registry():
    import ui.emoji as emoji_module
    return importlib.reload(emoji_module)


def test_unicode_emoji_are_the_default_everywhere_in_registry(monkeypatch):
    monkeypatch.setenv("KATO_CUSTOM_EMOJI", "0")
    module = _reload_registry()
    assert module.EMOJI["spirit_stone"] == "💎"
    assert module.EMOJI["cultivator"] == "🧘"
    assert module.EMOJI["demon"] == "👹"
    assert module.EMOJI["faction_tien"] == "🧘"
    assert module.EMOJI["faction_ma"] == "👹"
    assert all(not CUSTOM_TOKEN.fullmatch(value) for value in module.EMOJI.values())


def test_server_emoji_tree_is_separate_and_opt_in(monkeypatch):
    source = (ROOT / "ui/emoji.py").read_text(encoding="utf-8")
    assert not CUSTOM_TOKEN.search(source)
    config_path = ROOT / "assets/emojis/server/emojis.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert payload["emojis"]["spirit_stone"].startswith("<:linhthach:")
    assert payload["emojis"]["cultivator"].startswith("<:tutien:")
    assert payload["emojis"]["demon"].startswith("<:tuma:")
    assert payload["emojis"]["faction_tien"].startswith("<:tutien:")
    assert payload["emojis"]["faction_ma"].startswith("<:tuma:")

    previous = os.getenv("KATO_CUSTOM_EMOJI")
    try:
        monkeypatch.setenv("KATO_CUSTOM_EMOJI", "1")
        module = _reload_registry()
        assert module.EMOJI["spirit_stone"] == payload["emojis"]["spirit_stone"]
        assert module.EMOJI["cultivator"] == payload["emojis"]["cultivator"]
        assert module.EMOJI["demon"] == payload["emojis"]["demon"]
        assert module.EMOJI["faction_tien"] == payload["emojis"]["faction_tien"]
        assert module.EMOJI["faction_ma"] == payload["emojis"]["faction_ma"]
    finally:
        if previous is None:
            monkeypatch.delenv("KATO_CUSTOM_EMOJI", raising=False)
        else:
            monkeypatch.setenv("KATO_CUSTOM_EMOJI", previous)
        _reload_registry()
