from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_sect_member_admin_does_not_show_raw_member_id_as_label():
    text = (ROOT / "ui/views/sect_member_admin_view.py").read_text()
    assert 'label=f"{m.user_id} · {m.role}"' not in text
    assert "player.display_name" in text


def test_sect_application_selector_uses_player_name():
    text = (ROOT / "ui/views/sect_management_view.py").read_text()
    assert "a['user_id']" in text
    assert "player.display_name" in text
    assert "Chọn người xin gia nhập" in text
