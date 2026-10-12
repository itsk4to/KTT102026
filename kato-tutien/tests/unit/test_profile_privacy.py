from types import SimpleNamespace

from ui.embeds import public_player_embed
from game.content.items import ITEMS

EQUIPPED_ID = next(key for key, item in ITEMS.items() if item.get("type") == "equipment")


def test_public_profile_exposes_power_and_equipped_gear_but_not_private_resources():
    player = SimpleNamespace(
        display_name="Kato", path="tien", realm_index=2, realm_layer=1,
        spirit_stones=987654, dao_type="", sect_id=None, loadout={
            "weapon": EQUIPPED_ID, "artifact": None, "armor": None, "accessory": None,
        },
    )
    info = {"player": player, "realm": "Trúc Cơ · Sơ Kỳ"}
    embed = public_player_embed(info, combat_stats={"attack": 120, "defense": 80, "max_hp": 1000})

    all_text = embed.title + "\n" + (embed.description or "") + "\n" + "\n".join(
        f"{field.name}\n{field.value}" for field in embed.fields
    )
    assert "Chiến lực" in all_text
    assert "Trang bị đang mặc" in all_text
    assert "Vũ khí" in all_text
    assert "Linh thạch" not in all_text
    assert "987,654" not in all_text
    assert "Túi đồ" not in all_text
    assert "Thiên phú" not in all_text


def test_public_profile_lists_empty_equipment_slots_without_inventory_details():
    player = SimpleNamespace(
        display_name="Tu sĩ", path="ma", realm_index=0, realm_layer=1,
        spirit_stones=1000, dao_type="", sect_id=None, loadout={},
    )
    embed = public_player_embed({"player": player, "realm": "Luyện Khí"}, combat_stats={})
    gear = next(field.value for field in embed.fields if field.name == "🛡️ Trang bị đang mặc")
    assert "Chưa trang bị" in gear
