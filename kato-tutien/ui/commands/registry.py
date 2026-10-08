from __future__ import annotations

from dataclasses import dataclass

from ui.commands.core import cmd_create, cmd_help, cmd_info, cmd_leaderboard, cmd_menu
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
from ui.commands.dao_lu import cmd_dao_lu
from ui.commands.quest import cmd_npc, cmd_quest, cmd_world


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
    CommandSpec("tutien", ("tt", "tamuontutien", "tao"), "start", ".tutien tien|ma", "Khai đạo tạo nhân vật.", cmd_create, True),
    CommandSpec("help", ("h",), "start", ".help", "Sổ tay lệnh và phân loại thao tác.", cmd_help),
    CommandSpec("menu", ("mn",), "system", ".menu", "Mở Trung Tâm giao diện.", cmd_menu),
    CommandSpec("info", ("i", "xem"), "start", ".info", "Xem nhân vật.", cmd_info),
    CommandSpec("tu", ("tl", "tuluyen"), "cultivation", ".tu", "Tu luyện.", cmd_cultivate),
    CommandSpec("dotpha", ("dp",), "cultivation", ".dotpha", "Đột phá cảnh giới.", cmd_breakthrough),
    CommandSpec("thienkiep", ("tk",), "cultivation", ".thienkiep", "Ứng Thiên Kiếp.", cmd_tribulation),
    CommandSpec("daily", ("dl",), "cultivation", ".daily", "Nhận thưởng hằng ngày.", cmd_daily),
    CommandSpec("bxh", ("top",), "start", ".bxh [tien|ma]", "Bảng xếp hạng.", cmd_leaderboard, True),
    CommandSpec("khampha", ("kp", "phieuluu"), "explore", ".khampha", "Mở giao diện khám phá.", cmd_explore, True),
    CommandSpec("khu", ("kh",), "explore", ".khu <mã>", "Chọn khu khám phá.", cmd_zone, True),
    CommandSpec("san", ("s", "hunt"), "explore", ".san", "Săn yêu thú.", cmd_hunt),
    CommandSpec("npc", ("n", "nhanvat"), "world", ".npc [mã]", "Mở giao diện NPC; có thể dùng mã cho thao tác nhanh.", cmd_npc, True),
    CommandSpec("nhiemvu", ("q", "quest", "nv"), "world", ".nhiemvu [mã|nhan <mã>]", "Mở giao diện nhiệm vụ; mã vẫn hỗ trợ thao tác nâng cao.", cmd_quest, True),
    CommandSpec("thegioi", ("tg", "world"), "world", ".thegioi [thamgia <mã>]", "Mở giao diện biến động thế giới.", cmd_world, True),
    CommandSpec("shop", ("sp", "tiem"), "trade", ".shop", "Mở Tiên Phường bằng GUI.", cmd_shop),
    CommandSpec("mua", ("m", "buy"), "trade", ".mua <vật_phẩm> [số_lượng]", "Mua vật phẩm.", cmd_buy, True),
    CommandSpec("tui", ("bag", "inv", "inventory"), "trade", ".tui", "Mở Túi Càn Khôn bằng GUI.", cmd_inventory),
    CommandSpec("dung", ("use",), "trade", ".dung <vật_phẩm> [số_lượng]", "Dùng vật phẩm.", cmd_use, True),
    CommandSpec("hoc", ("learn",), "trade", ".hoc <công_pháp>", "Học công pháp.", cmd_learn, True),
    CommandSpec("trangbi", ("tb", "equip"), "trade", ".trangbi <vật_phẩm>", "Trang bị.", cmd_equip, True),
    CommandSpec("thao", ("unequip",), "trade", ".thao", "Tháo trang bị.", cmd_unequip),
    CommandSpec("cho", ("ch", "market"), "trade", ".cho", "Xem chợ.", cmd_market),
    CommandSpec("dangban", ("db",), "trade", ".dangban <vật_phẩm> <số_lượng> <giá>", "Đăng bán.", cmd_market_list, True),
    CommandSpec("muacho", ("mc",), "trade", ".muacho <mã_tin>", "Mua tin chợ.", cmd_market_buy, True),
    CommandSpec("huyban", ("hb",), "trade", ".huyban <mã_tin>", "Hủy tin bán.", cmd_market_cancel, True),
    CommandSpec("chuyen", ("cv", "transfer"), "trade", ".chuyen @người_chơi <số_linh_thạch>", "Chuyển linh thạch.", cmd_transfer, True),
    CommandSpec("code", (), "trade", ".code <mã>", "Nhập mã thưởng.", cmd_code, True),
    CommandSpec("gacha", ("gc", "thienco"), "trade", ".gacha", "Thiên Cơ gacha.", cmd_gacha),
    CommandSpec("dao", (), "dao", ".dao [kiem|dao|phap|the|ma]", "Mở giao diện Đạo; mã vẫn hỗ trợ chọn nhanh.", cmd_dao, True),
    CommandSpec("daolu", ("dlp",), "social", ".daolu", "Mở giao diện Đạo Lữ.", cmd_dao_lu),
    CommandSpec("tongmon", ("tm",), "sect", ".tongmon", "Mở giao diện tông môn.", cmd_sect),
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
