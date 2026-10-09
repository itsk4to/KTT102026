from __future__ import annotations

import random

import pytest

from game.content.realms import cultivation_requirement
from game.database.connection import Database
from game.engine import GameEngine, GameError
from game.rules.breakthrough_rules import (
    requires_nine_thunder_tribulation,
    thunder_strike_damage,
)


class FixedRng:
    def __init__(self, value: float):
        self.value = value

    def random(self):
        return self.value


def make_engine():
    eng = GameEngine(Database(":memory:"), random.Random(7))
    eng.players.create("u", "U", "tien")
    return eng


def place_at_kim_dan_peak(eng, *, hp=1000, max_hp=1000, defense=100, gear=None):
    p = eng.players.get("u")
    p.realm_index = 3
    p.realm_layer = 9
    p.cultivation = cultivation_requirement(3, 9)
    p.hp = hp
    p.max_hp = max_hp
    p.defense = defense
    p.loadout = {"artifact": gear} if gear else {}
    eng._players.save(p)
    return p


def test_cuu_loi_gate_starts_at_kim_dan_peak_and_uses_shared_realm_tree():
    assert not requires_nine_thunder_tribulation(2, 9)  # Trúc Cơ -> Kim Đan
    assert not requires_nine_thunder_tribulation(3, 8)  # Kim Đan inner layer
    assert requires_nine_thunder_tribulation(3, 9)    # Kim Đan -> Nguyên Anh
    assert requires_nine_thunder_tribulation(4, 9)    # Nguyên Anh -> Hóa Thần
    assert not requires_nine_thunder_tribulation(9, 3)  # final Độ Kiếp uses its own flow


def test_later_thunder_strikes_increase_slightly():
    damages = []
    previous = 0
    for strike in range(1, 10):
        damage = thunder_strike_damage(
            1000, 4, strike, defense=80, resistance=0.18, previous_damage=previous,
        )
        damages.append(damage)
        previous = damage
    assert len(damages) == 9
    assert all(later > earlier for earlier, later in zip(damages, damages[1:]))
    assert damages[-1] <= damages[0] * 2


def test_successful_breakthrough_resolves_nine_hits_consumes_protection_and_keeps_hp_loss():
    eng = make_engine()
    place_at_kim_dan_peak(eng, gear="thien_loi_chau")
    eng._inventory.add("u", "loi_kiep_dan", 1)
    eng._inventory.add("u", "cuu_loi_ho_than_phu", 1)
    eng.cultivation.rng = FixedRng(0.0)

    result = eng.breakthrough.breakthrough(
        "u", thunder_items=["loi_kiep_dan", "cuu_loi_ho_than_phu"],
    )

    assert result["success"] is True
    thunder = result["thunder_tribulation"]
    assert thunder["attempted"] is True
    assert len(thunder["strikes"]) == 9
    assert thunder["success"] is True
    assert result["realm"].startswith("Nguyên Anh")
    assert result["player"].hp < result["player"].max_hp
    assert eng._inventory.get_count("u", "loi_kiep_dan") == 0
    assert eng._inventory.get_count("u", "cuu_loi_ho_than_phu") == 0
    assert result["consumed_thunder_items"] == ["Lôi Kiếp Đan ×1", "Cửu Lôi Hộ Thân Phù ×1"]


def test_failing_thunder_keeps_realm_and_consumes_protection_used():
    eng = make_engine()
    place_at_kim_dan_peak(eng, hp=100, max_hp=1000, defense=0)
    eng._inventory.add("u", "loi_kiep_dan", 1)
    eng._inventory.add("u", "cuu_loi_ho_than_phu", 1)
    eng.cultivation.rng = FixedRng(0.0)

    result = eng.breakthrough.breakthrough(
        "u", thunder_items=["loi_kiep_dan", "cuu_loi_ho_than_phu"],
    )

    assert result["success"] is False
    assert result["thunder_tribulation"]["attempted"] is True
    assert result["thunder_tribulation"]["success"] is False
    assert result["player"].realm_index == 3
    assert result["player"].hp == 1
    assert result["recovery_seconds"] > 0
    assert eng._inventory.get_count("u", "loi_kiep_dan") == 0
    assert eng._inventory.get_count("u", "cuu_loi_ho_than_phu") == 0


def test_protection_is_not_consumed_if_breakthrough_roll_fails_before_thunder():
    eng = make_engine()
    place_at_kim_dan_peak(eng, gear="thien_loi_chau")
    eng._inventory.add("u", "loi_kiep_dan", 1)
    eng.cultivation.rng = FixedRng(0.999)

    result = eng.breakthrough.breakthrough("u", thunder_items=["loi_kiep_dan"])

    assert result["success"] is False
    assert result["thunder_tribulation"] is None
    assert result["consumed_thunder_items"] == []
    assert eng._inventory.get_count("u", "loi_kiep_dan") == 1
    assert eng.players.get("u").realm_index == 3


def test_unprepared_breakthrough_is_not_free_and_fails_without_protection():
    eng = make_engine()
    place_at_kim_dan_peak(eng, hp=1000, max_hp=1000, defense=100)
    eng.cultivation.rng = FixedRng(0.0)

    result = eng.breakthrough.breakthrough("u")

    assert result["success"] is False
    assert result["thunder_tribulation"]["attempted"] is True
    assert result["player"].realm_index == 3
    assert result["player"].hp == 1



def test_multiple_pill_doses_have_diminishing_returns_and_consume_selected_quantity():
    eng = make_engine()
    place_at_kim_dan_peak(eng, hp=1000, max_hp=1000, defense=100)
    eng._inventory.add("u", "loi_kiep_dan", 3)
    eng.cultivation.rng = FixedRng(0.0)

    one_dose = eng.breakthrough.stacked_thunder_resistance(0.18, 1)
    three_doses = eng.breakthrough.stacked_thunder_resistance(0.18, 3)
    assert one_dose == 0.18
    assert three_doses == 0.36

    result = eng.breakthrough.breakthrough("u", thunder_items=["loi_kiep_dan::3"])

    assert result["success"] is True
    assert result["thunder_tribulation"]["resistance"] == 0.36
    assert eng._inventory.get_count("u", "loi_kiep_dan") == 0
    assert result["consumed_thunder_items"] == ["Lôi Kiếp Đan ×3"]


def test_protection_items_cannot_be_accidentally_consumed_from_inventory():
    eng = make_engine()
    eng._inventory.add("u", "loi_kiep_dan", 1)

    with pytest.raises(GameError, match="vật phẩm hộ kiếp"):
        eng.economy.use_item("u", "loi_kiep_dan")

    assert eng._inventory.get_count("u", "loi_kiep_dan") == 1
