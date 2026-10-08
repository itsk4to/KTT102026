from ui.commands.registry import COMMAND_LOOKUP


def test_common_short_aliases_resolve_to_expected_commands():
    expected = {
        "tl": "tu",
        "dp": "dotpha",
        "tk": "thienkiep",
        "kp": "khampha",
        "nv": "nhiemvu",
        "tg": "thegioi",
        "sp": "shop",
        "m": "mua",
        "tb": "trangbi",
        "gc": "gacha",
    }
    for alias, command in expected.items():
        assert COMMAND_LOOKUP[alias].name == command
