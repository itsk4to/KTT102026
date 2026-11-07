"""Văn bản hệ thống — giọng tu tiên (xianxia), dễ hiểu với đạo hữu mới.

Nguyên tắc:
- Dùng từ: đạo hữu, tu vi, cảnh giới, linh thạch, đột phá, thiên kiếp, bí cảnh, tông môn…
- Tránh từ kỹ thuật: GUI, HUD, dashboard, component…
- Chỉ dẫn ngắn, có lộ trình rõ cho người mới.
"""
from __future__ import annotations

# ----- Lời hệ thống chung -----
NOT_YOURS = "Bảng này không thuộc về đạo hữu."
NOT_REGISTERED = "Đạo hữu chưa khai mở tiên lộ. Hãy dùng **`.tutien`** để lập căn cơ."
BAG_EMPTY = "Túi Càn Khôn trống rỗng. Hãy ghé **Tiên Phường** (`.shop`) hoặc xuất hành tìm cơ duyên."
COOLDOWN_FMT = "Còn **{seconds}s** nữa mới có thể tiếp tục."

# ----- Khai đạo -----
PATH_TITLE = "✦ Khai Đạo · Ngã Rẽ Thiên Mệnh"
PATH_BODY = (
    "Linh khí bốn phương hội tụ. Đạo hữu đứng trước ngã rẽ đầu tiên trên con đường cầu đạo.\n\n"
    "**Tiên Đạo** — chính tâm tu luyện, lấy thanh tịnh làm gốc.\n"
    "**Ma Đạo** — lấy lực đoạt duyên, lấy sát phạt mở đường.\n\n"
    "*Chọn một con đường. Thiên đạo không quay đầu.*"
)
PATH_TIEN_LABEL = "Tiên Đạo"
PATH_MA_LABEL = "Ma Đạo"
PATH_REJECT_LABEL = "Rời đi"
PATH_REJECTED = "Đạo hữu tạm thời lui bước. Khi lòng đã định, hãy quay lại **`.tutien`**."

# ----- Trung tâm -----
HUB_TITLE = "✦ Động Phủ · Trung Tâm Tu Hành"
HUB_GUEST_TITLE = "✦ Cửa Ải Tiên Lộ"
HUB_GUEST_BODY = (
    "Linh khí nơi này rất đậm. Đạo hữu chưa lập căn cơ, chưa thể bước vào động phủ.\n\n"
    "**Bước một** — **`.tutien`**: chọn Tiên Đạo hoặc Ma Đạo.\n"
    "**Bước hai** — **`.menu`**: mở động phủ, xem toàn bộ lộ trình.\n"
    "**Bước ba** — **`.tu`**: ngồi thiền tụ khí, tích lũy tu vi."
)
HUB_HINT = "*Chạm cửa bên dưới để hành sự. Người mới nên đi theo lộ trình ngắn.*"

# ----- Hồ sơ -----
PROFILE_TITLE = "Hồ Sơ Đạo Hữu · {name}"
PROFILE_SUB = "{realm}\n{path} · *Chỉ số chân thực trên thân*"

# ----- Tu luyện / đột phá -----
CULTIVATE_TITLE = "Tĩnh Tọa Tu Luyện"
BREAKTHROUGH_TITLE = "Đột Phá Cảnh Giới"
BREAKTHROUGH_READY = "Linh khí đã đầy — có thể thử đột phá."
BREAKTHROUGH_NOT_READY = "Tu vi chưa đủ. Hãy tiếp tục tĩnh tọa hoặc dùng đan dược."
BREAKTHROUGH_RECOVERY = "Thân thể còn tổn thương sau lần thất bại. Còn **{time}** mới hồi phục."
PITY_LABEL = "Thiên đạo bảo hộ"
PITY_HINT = "Thất bại +5 · tối đa +20 điểm phần trăm"
THUNDER_TITLE = "Cửu Lôi Thiên Kiếp"
THUNDER_HINT = (
    "Đột phá đại cảnh từ Kim Đan trở lên sẽ phải đón **chín đạo thiên lôi**.\n"
    "Mỗi đạo mạnh hơn đạo trước. Hãy chuẩn bị **Lôi Kiếp Đan**, "
    "**Cửu Lôi Hộ Thân Phù** hoặc pháp bảo kháng lôi."
)

# ----- Help / người mới -----
HELP_WELCOME_TITLE = "Cẩm Nang Tiên Lộ"
HELP_WELCOME = (
    "**Chào mừng đạo hữu đến Kato Tu Tiên.**\n"
    "Nơi này mô phỏng con đường cầu đạo: tụ khí → đột phá → xuất hành → cầu duyên.\n\n"
    f"**LỘ TRÌNH NGƯỜI MỚI**\n"
    "① **`.tutien`** — khai đạo, chọn Tiên hoặc Ma.\n"
    "② **`.menu`** — vào động phủ (trung tâm mọi việc).\n"
    "③ **`.tu`** — tĩnh tọa mỗi ngày; **`.daily`** nhận lộc trời.\n"
    "④ **`.dotpha`** khi tu vi đầy; gặp đại cảnh thì **`.thienkiep`**.\n"
    "⑤ **`.khampha`** / **`.bicanh`** tìm cơ duyên · **`.shop`** / **`.tui`** lo đan khí.\n\n"
    "*Trên điện thoại: dùng nút trong `.menu` sẽ dễ hơn nhớ lệnh.*"
)

# ----- Menu labels (nút) -----
BTN_PROFILE = "Đạo Hữu"
BTN_EXPLORE = "Xuất Hành"
BTN_BAG = "Túi Càn Khôn"
BTN_SHOP = "Tiên Phường"
BTN_SECRET = "Bí Cảnh"
BTN_QUEST = "Sứ Mệnh"
BTN_SECT = "Tông Môn"
BTN_DAO_LU = "Đạo Lữ"
BTN_BOARD = "Thiên Bảng"
BTN_WORLD = "Thiên Hạ"
BTN_REFRESH = "Tẩy Mới"
BTN_CLOSE = "Khép Lại"
BTN_HOME = "Động Phủ"
BTN_BACK = "Quay Lại"
