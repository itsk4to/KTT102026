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


def test_unicode_fallback_is_available_when_custom_emoji_disabled(monkeypatch):
    monkeypatch.setenv("KATO_CUSTOM_EMOJI", "0")
    module = _reload_registry()
    assert module.EMOJI["spirit_stone"] == "💎"
    assert module.EMOJI["cultivator"] == "🧘"
    assert module.EMOJI["demon"] == "👹"
    assert module.EMOJI["faction_tien"] == "🧘"
    assert module.EMOJI["faction_ma"] == "👹"
    assert all(not CUSTOM_TOKEN.fullmatch(value) for value in module.EMOJI.values())


def test_server_emoji_tree_is_separate_and_custom_emoji_enabled(monkeypatch):
    source = (ROOT / "ui/emoji.py").read_text(encoding="utf-8")
    assert not CUSTOM_TOKEN.search(source)
    config_path = ROOT / "assets/emojis/server/emojis.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert payload["emojis"]["spirit_stone"].startswith("<:spirit_stone:")
    assert payload["emojis"]["cultivator"].startswith("<:cultivator:")
    assert payload["emojis"]["demon"].startswith("<:demon:")
    assert payload["emojis"]["faction_tien"].startswith("<:cultivator:")
    assert payload["emojis"]["faction_ma"].startswith("<:demon:")

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


def test_custom_emoji_enabled_by_default(monkeypatch):
    monkeypatch.delenv("KATO_CUSTOM_EMOJI", raising=False)
    module = _reload_registry()
    payload = json.loads((ROOT / "assets/emojis/server/emojis.json").read_text(encoding="utf-8"))
    assert module.EMOJI["spirit_stone"] == payload["emojis"]["spirit_stone"]
    assert module.EMOJI["attack"] == payload["emojis"]["attack"]
    assert module.EMOJI["victory"] == payload["emojis"]["victory"]


def test_legacy_unicode_in_text_is_resolved_through_registry(monkeypatch):
    monkeypatch.setenv("KATO_CUSTOM_EMOJI", "1")
    module = _reload_registry()
    rendered = module.render_emojis("⚔️ Công · 🛡️ Thủ · 💎 Linh thạch")
    assert "<:attack:" in rendered
    assert "<:def:" in rendered
    assert "<:spirit_stone:" in rendered
    assert "⚔️" not in rendered
    assert "🛡️" not in rendered


def test_unknown_or_unmapped_unicode_is_preserved(monkeypatch):
    monkeypatch.setenv("KATO_CUSTOM_EMOJI", "1")
    module = _reload_registry()
    assert module.render_emojis("🌌 Bí Cảnh · 🏠 Trung tâm") == "🌌 Bí Cảnh · 🏠 Trung tâm"
    assert module.extract_leading_emoji("⚔️ Tấn công") == (module.EMOJI["attack"], "Tấn công")


def test_registry_covers_every_literal_key_used_by_gui():
    import ast
    registry = (ROOT / "ui/emoji.py").read_text(encoding="utf-8")
    tree = ast.parse(registry)
    registered = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "EMOJI" for t in node.targets) and isinstance(node.value, ast.Dict):
            registered = {key.value for key in node.value.keys if isinstance(key, ast.Constant)}
            break
    used = set()
    for path in (ROOT / "ui").rglob("*.py"):
        if path.name == "emoji.py":
            continue
        source = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(source):
            if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "EMOJI" and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                used.add(node.slice.value)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "EMOJI" and node.func.attr == "get" and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                used.add(node.args[0].value)
    assert used <= registered, f"Missing emoji keys: {sorted(used - registered)}"
