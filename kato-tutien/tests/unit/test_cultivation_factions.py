from game.rules.cultivation_rules import realm_text
from game.content.realms import REALMS


def test_two_factions_have_distinct_names_at_same_tier():
    assert realm_text(1, 1, "tien") == "Luyen Khí · Sơ kỳ" or realm_text(1, 1, "tien") == "Luyện Khí · Sơ kỳ"
    assert realm_text(1, 1, "ma").startswith("Ma Khí ·")
    assert realm_text(1, 1, "tien") != realm_text(1, 1, "ma")


def test_factions_share_same_tier_count_and_indexing():
    assert len(REALMS) == 14
    assert REALMS[1][1] == 9
    assert realm_text(9, 3, "tien").startswith("Độ Kiếp")
    assert realm_text(9, 3, "ma").startswith("Ma Kiếp")
