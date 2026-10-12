"""Central visual language for Kato Tu Tiên's Discord RPG interface."""

# Embed accents; native Discord components provide the matching button palette.
COLOR_MAIN = 0x6255D9       # đạo lực / mystical violet
COLOR_SUCCESS = 0x239B72   # jade / success
COLOR_INFO = 0x3D86D9      # celestial blue
COLOR_WARN = 0xD7A33F      # spirit gold / warning
COLOR_ERROR = 0xC94F62     # danger / blood-red
COLOR_GOLD = 0xC7A14A
COLOR_SURFACE = 0x171B2B
COLOR_CYAN = 0x3AB7BE
COLOR_PURPLE = 0x8A66D9

BRAND_NAME = "Tu Tiên"
BRAND_FOOTER = "— Đạo lộ vô cùng —"
DEFAULT_TIMEOUT = 300

BUTTON_ROLES = {
    "primary": "primary",
    "navigation": "secondary",
    "success": "success",
    "danger": "danger",
    "quiet": "secondary",
}

# Semantic label rules are normalized (accent-insensitive) by ui.theme.views.
# Keep exact-ish phrases first in each role to reduce accidental matches.
BUTTON_LABELS = {
    "danger": (
        "bo chay", "rut lui", "tu choi", "huy", "dong", "khep lai", "xoa", "roi tong", "roi bi canh",
        "vo hieu hoa", "tu bo", "xoa thanh vien", "huy loi moi", "giai tan",
        "khai tru", "giang chuc", "nhuong tong chu", "giam", "tu choi dot pha",
    ),
    "success": (
        "nhan thuong", "nhan loi", "chap nhan", "xac nhan", "dong y", "mua",
        "cap linh thach", "cong hien", "trang bi", "duyet", "thang chuc",
        "xin gia nhap", "nhan nhiem vu", "nhan loi moi", "hoc cong phap",
    ),
    "primary": (
        "tu luyen", "dot pha", "tan cong", "xuat hanh", "kham pha", "bat dau", "tao tong",
        "tao mat lenh", "thach dau", "noi chuyen", "dung vat pham", "xem chi tiet",
        "cau duyen", "song tu", "san yeu thu", "ho the", "gop suc", "nhap quy tac",
        "thi trien", "chon dao", "tiep tuc", "mo tui", "chuan bi",
    ),
    "navigation": (
        "trang chinh", "trung tam", "quay lai", "tro lai", "lam moi", "refresh",
        "trang truoc", "trang sau", "mo menu", "danh muc", "xem bxh",
    ),
}

BUTTON_EMOJIS = (
    (("trang chinh", "trung tam", "ve menu", "mo menu"), "🏠"),
    (("quay lai", "tro lai", "trang truoc"), "◀️"),
    (("trang sau", "tiep tuc"), "▶️"),
    (("lam moi", "refresh"), "🔄"),
    (("dong", "huy"), "✖️"),
    (("tu luyen",), "🌱"),
    (("dot pha",), "⚡"),
    (("tan cong", "san yeu thu"), "⚔️"),
    (("kham pha",), "🗺️"),
    (("nhan thuong",), "🎁"),
    (("mua",), "🛒"),
    (("xem chi tiet", "chi tiet"), "🔎"),
    (("nhiem vu",), "📜"),
    (("cong phap", "hoc cong phap", "ky nang"), "📖"),
    (("bi canh",), "🌌"),
)


def color_for_title(title: str) -> int:
    """Pick a readable, game-like accent from common screen intents."""
    text = (title or "").casefold()
    if any(token in text for token in ("lỗi", "thất bại", "bị từ chối", "không thành", "cảnh báo")):
        return COLOR_ERROR
    if any(token in text for token in ("thành công", "hoàn thành", "đã nhận", "chiến thắng", "vượt kiếp")):
        return COLOR_SUCCESS
    if any(token in text for token in ("boss", "chiến đấu", "trận", "quái", "cửu lôi")):
        return COLOR_WARN
    if any(token in text for token in ("tiên phường", "shop", "chợ", "linh thạch", "giao dịch")):
        return COLOR_GOLD
    if any(token in text for token in ("nhân vật", "hồ sơ", "bảng xếp hạng", "trung tâm", "thể trạng")):
        return COLOR_INFO
    if any(token in text for token in ("tông môn", "nhiệm vụ", "nhật ký", "đồng đạo")):
        return COLOR_SUCCESS
    if any(token in text for token in ("bí cảnh", "đạo", "tu luyện", "đột phá", "khai đạo")):
        return COLOR_PURPLE
    return COLOR_MAIN
