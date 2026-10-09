"""Design tokens: one place to tune the whole bot's visual identity."""

# Discord embed accents; buttons use Discord's native component palette.
COLOR_MAIN = 0x7564E8       # mystical violet
COLOR_SUCCESS = 0x28B996   # jade
COLOR_INFO = 0x4798E8      # celestial blue
COLOR_WARN = 0xE4B65A      # spirit-gold
COLOR_ERROR = 0xDE5F70     # coral-red
COLOR_GOLD = 0xC9A65D
COLOR_SURFACE = 0x202434

BRAND_NAME = "KATO TU TIÊN"
BRAND_FOOTER = "✦ KATO TU TIÊN  •  ĐẠO LỘ MMORPG"
DEFAULT_TIMEOUT = 300

# Button roles communicate intent consistently across all feature views.
BUTTON_ROLES = {
    "primary": "primary",
    "navigation": "secondary",
    "success": "success",
    "danger": "danger",
    "quiet": "secondary",
}

# Label-based rules are deliberately small and semantic: destructive actions red,
# confirmations jade, main actions violet, and navigation neutral.
BUTTON_LABELS = {
    "danger": (
        "tu choi", "huy", "dong", "xoa", "roi tong", "vo hieu hoa",
        "bo chay", "tu bo", "xoa thanh vien", "huy loi moi", "giai tan",
        "khai tru", "giang chuc", "nhuong tong chu",
    ),
    "success": (
        "nhan loi", "chap nhan", "xac nhan", "dong y", "nhan nhiem vu",
        "nhan thuong", "mua", "cap linh thach", "cong hien", "trang bi",
        "duyet", "thang chuc", "xin gia nhap",
    ),
    "primary": (
        "tu luyen", "dot pha", "tan cong", "kham pha", "bat dau", "tao tong",
        "tao mat lenh", "thach dau", "noi chuyen", "dung vat pham", "xem chi tiet",
        "cau duyen", "song tu", "san yeu thu", "ho the", "gop suc", "nhap quy tac",
    ),
    "navigation": (
        "trang chinh", "trung tam", "quay lai", "tro lai", "lam moi", "refresh",
        "trang truoc", "trang sau", "nhan vat",
    ),
}
