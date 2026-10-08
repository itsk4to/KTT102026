from __future__ import annotations

from dataclasses import dataclass

from ui.commands.core import cmd_create, cmd_help, cmd_info, cmd_leaderboard
from ui.commands.cultivation import cmd_cultivate, cmd_breakthrough, cmd_tribulation, cmd_daily
from ui.commands.exploration import cmd_explore, cmd_zone, cmd_hunt
from ui.commands.economy import (
    cmd_shop, cmd_buy, cmd_inventory, cmd_use, cmd_learn, cmd_equip,
    cmd_unequip, cmd_market, cmd_market_list, cmd_market_buy,
    cmd_market_cancel, cmd_transfer, cmd_code, cmd_gacha,
)
from ui.commands.dao import cmd_dao
from ui.commands.sect import cmd_sect, cmd_sect_create, cmd_sect_apply, cmd_sect_contribute, cmd_sect_leave
from ui.commands.admin import cmd_admin


@dataclass(frozen=True)
class CommandSpec:
    name: str
    aliases: tuple[str, ...]
    category: str
    usage: str
    description: str
    handler: object
    takes_args: bool = False


COMMAND_SPECS: tuple[CommandSpec, ...] = (
    CommandSpec("tutien", ("tamuontutien", "tao"), "start", ".tutien tien|ma", "Khai đạo tạo nhân vật.", cmd_create, True),
    CommandSpec("help", ("h",), "start", ".help", "Sổ tay lệnh.", cmd_help),
    CommandSpec("info", ("xem",), "start", ".info", "Xem nhân vật.", cmd_info),
    CommandSpec("tu", ("tuluyen",), "cultivation", ".tu", "Tu luyện.", cmd_cultivate),
    CommandSpec("dotpha", (), "cultivation", ".dotpha", "Đột phá cảnh giới.", cmd_breakthrough),
    CommandSpec("thienkiep", (), "cultivation", ".thienkiep", "Ứng Thiên Kiếp.", cmd_tribulation),
    CommandSpec("daily", (), "cultivation", ".daily", "Nhận thưởng hằng ngày.", cmd_daily),
    CommandSpec("bxh", ("top",), "start", ".bxh [tien|ma]", "Bảng xếp hạng.", cmd_leaderboard, True),
    CommandSpec("khampha", ("phieuluu",), "explore", ".khampha", "Khám phá.", cmd_explore, True),
    CommandSpec("khu", (), "explore", ".khu <mã>", "Chọn khu khám phá.", cmd_zone, True),
    CommandSpec("san", ("hunt",), "explore", ".san", "Săn yêu thú.", cmd_hunt),
    CommandSpec("shop", ("tiem",), "trade", ".shop", "Mở Tiên Phường.", cmd_shop),
    CommandSpec("mua", ("buy",), "trade", ".mua <item> [sl]", "Mua vật phẩm.", cmd_buy, True),
    CommandSpec("tui", ("inv", "inventory"), "trade", ".tui", "Xem túi đồ.", cmd_inventory),
    CommandSpec("dung", ("use",), "trade", ".dung <item> [sl]", "Dùng vật phẩm.", cmd_use, True),
    CommandSpec("hoc", ("learn",), "trade", ".hoc <công_pháp>", "Học công pháp.", cmd_learn, True),
    CommandSpec("trangbi", ("equip",), "trade", ".trangbi <item>", "Trang bị.", cmd_equip, True),
    CommandSpec("thao", ("unequip",), "trade", ".thao", "Tháo trang bị.", cmd_unequip),
    CommandSpec("cho", ("market",), "trade", ".cho", "Xem chợ.", cmd_market),
    CommandSpec("dangban", (), "trade", ".dangban <item> <sl> <gia>", "Đăng bán.", cmd_market_list, True),
    CommandSpec("muacho", (), "trade", ".muacho <id>", "Mua tin chợ.", cmd_market_buy, True),
    CommandSpec("huyban", (), "trade", ".huyban <id>", "Hủy tin bán.", cmd_market_cancel, True),
    CommandSpec("chuyen", ("transfer",), "trade", ".chuyen @user <số>", "Chuyển linh thạch.", cmd_transfer, True),
    CommandSpec("code", (), "trade", ".code <mã>", "Nhập mã thưởng.", cmd_code, True),
    CommandSpec("gacha", ("thienco",), "trade", ".gacha", "Thiên Cơ gacha.", cmd_gacha),
    CommandSpec("dao", (), "dao", ".dao [kiem|dao|phap|the|ma]", "Chọn/xem Đạo.", cmd_dao, True),
    CommandSpec("tongmon", ("tm",), "sect", ".tongmon", "Tông môn.", cmd_sect),
    CommandSpec("taotong", (), "sect", ".taotong <tên>", "Sáng lập tông môn.", cmd_sect_create, True),
    CommandSpec("xintong", (), "sect", ".xintong <sect_id>", "Xin gia nhập.", cmd_sect_apply, True),
    CommandSpec("congtong", (), "sect", ".congtong <số>", "Cống hiến.", cmd_sect_contribute, True),
    CommandSpec("roitong", (), "sect", ".roitong", "Rời tông môn.", cmd_sect_leave),
    CommandSpec("admin", (), "system", ".admin", "Mở bảng quản trị.", cmd_admin),
)

COMMAND_LOOKUP: dict[str, CommandSpec] = {}
for spec in COMMAND_SPECS:
    COMMAND_LOOKUP[spec.name] = spec
    for alias in spec.aliases:
        COMMAND_LOOKUP[alias] = spec
