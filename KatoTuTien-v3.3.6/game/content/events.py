from __future__ import annotations

# Exploration is intentionally split into immediate events and choice events.
# Choice events create the "one more click" loop: observe -> choose -> consequence.
EXPLORATION_EVENTS = [
    {"key": "linh_thach_nho", "weight": 20, "stones": (50, 150), "text": "Giữa lớp cỏ khô, ngươi phát hiện vài viên linh thạch lộ ra dưới đất."},
    {"key": "tu_vi_nho", "weight": 18, "cultivation": (30, 80), "text": "Một tia đạo vận lướt qua tâm thần. Ngươi ngồi xuống lĩnh hội trong chốc lát."},
    {"key": "yeu_thu", "weight": 15, "combat": True, "text": "Một tiếng gầm xé tan sự tĩnh lặng. Yêu thú đã phát hiện ngươi."},
    {"key": "co_duyen_nho", "weight": 8, "stones": (200, 500), "item": "tu_khi_dan", "text": "Một tia sáng lóe lên dưới khe đá. Có vẻ ngươi vừa gặp chút cơ duyên."},
    {"key": "thuong_the", "weight": 7, "injury": (5, 15), "text": "Ngươi vô tình chạm phải tàn trận. Linh lực phản phệ gây thương thế."},
    {"key": "truyen_thua", "weight": 5, "cultivation": (100, 300), "insight": 1, "text": "Một mảnh truyền thừa vụn vỡ lướt qua thần hồn."},
    {"key": "khong", "weight": 7, "text": "Ngươi đi qua một vùng hoang vắng. Không có bảo vật, nhưng cũng chẳng gặp nguy hiểm."},
]

# Each choice has a condition and consequence. Conditions are deliberately simple
# so new content can be authored without touching the service.
CHOICE_EVENTS = [
    {
        "key": "co_dong_phu",
        "weight": 8,
        "title": "Cổ Động Phủ",
        "zones": ["dongphu", "hoangnguyen", "yeuthusonmach"],
        "text": "Một phiến đá cổ nứt ra, để lộ cánh cửa động phủ bị phong ấn. Từ bên trong truyền ra kiếm ý yếu ớt.",
        "choices": [
            {"id": "observe", "label": "👁️ Quan sát", "effect": {"insight": 3, "discover": "dong_phu_kiem_y", "text": "Ngươi nhìn thấy một đường kiếm văn ẩn dưới lớp bụi. Một bí mật đã được ghi vào nhân sinh."}},
            {"id": "open", "label": "🚪 Thử mở", "effect": {"cultivation": [120, 240], "stones": [80, 180], "injury": [0, 8], "discover": "dong_phu_mo_cua", "text": "Phong ấn rung chuyển. Ngươi lấy được chút tài nguyên trước khi cửa động khép lại."}},
            {"id": "force", "label": "⚔️ Cưỡng ép phá trận", "condition": {"mind": 55}, "effect": {"cultivation": [250, 450], "item": "tu_khi_dan", "injury": [5, 18], "discover": "dong_phu_cuong_pha", "text": "Ngươi phá trận bằng sức mạnh thần thức. Cái giá là thương thế, nhưng truyền thừa đã lọt vào tay ngươi."}},
            {"id": "leave", "label": "🚶 Rời đi", "effect": {"fate": 1, "text": "Ngươi không tham lam. Có lẽ đây chưa phải thời điểm của ngươi."}},
        ],
    },
    {
        "key": "nguoi_bi_thuong",
        "weight": 7,
        "title": "Người Bị Thương",
        "zones": ["hoangnguyen", "yeuthusonmach", "dongphu", "haivuc", "mavuc"],
        "text": "Sau một bụi cây, một tu sĩ xa lạ đang bị thương nặng. Hắn nhìn ngươi đầy cảnh giác.",
        "choices": [
            {"id": "help", "label": "🤝 Giúp đỡ", "effect": {"stones": [-80, 120], "fate": 2, "reputation": 1, "discover": "nguoi_duoc_cuu", "text": "Ngươi ra tay cứu hắn. Trước khi rời đi, hắn để lại một lời hứa: nếu còn gặp lại, hắn sẽ trả ơn."}},
            {"id": "question", "label": "🗣️ Hỏi chuyện", "effect": {"insight": 2, "discover": "nguoi_la_bi_mat", "text": "Qua vài câu hỏi, ngươi nhận ra hắn đang chạy trốn khỏi một thế lực nào đó."}},
            {"id": "rob", "label": "💰 Lục soát", "effect": {"stones": [100, 260], "fate": -2, "discover": "nguoi_bi_hai", "text": "Ngươi lấy được một ít tài vật. Nhưng ánh mắt của hắn khiến ngươi có cảm giác chuyện này chưa kết thúc."}},
            {"id": "leave", "label": "🚶 Bỏ đi", "effect": {"text": "Ngươi không muốn dây vào chuyện của người khác. Bóng người phía sau dần biến mất."}},
        ],
    },
    {
        "key": "linh_qua_duoi_cay",
        "weight": 7,
        "title": "Linh Quả Dưới Cây",
        "zones": ["hoangnguyen", "yeuthusonmach", "haivuc"],
        "text": "Một quả linh quả đỏ sẫm treo giữa tán cây. Nhưng dưới gốc cây có dấu chân yêu thú còn mới.",
        "choices": [
            {"id": "pick", "label": "🍎 Hái ngay", "effect": {"item": "tu_khi_dan", "cultivation": [50, 100], "text": "Ngươi nhanh tay hái được linh quả trước khi chủ nhân của nó quay lại."}},
            {"id": "wait", "label": "🕵️ Chờ đợi", "effect": {"cultivation": [120, 260], "stones": [100, 250], "discover": "linh_qua_cho_doi", "text": "Ngươi kiên nhẫn chờ đợi và phát hiện một con yêu thú đang bảo vệ cả một ổ linh quả."}},
            {"id": "inspect", "label": "👁️ Quan sát kỹ", "condition": {"insight": 55}, "effect": {"item": "tu_khi_dan", "insight": 4, "discover": "linh_qua_gia", "text": "Ngươi nhận ra quả thật chỉ là mồi nhử. Bên dưới lớp rễ có một linh thảo quý hơn."}},
        ],
    },
]

INHERITANCE_EVENTS = [
    {"key": "kiem_y", "dao": "kiem", "insight": 15, "text": "Kiếm ý cổ xưa thấm vào tâm can."},
    {"key": "dao_y", "dao": "dao", "insight": 15, "text": "Đao hồn trấn áp hư không."},
    {"key": "phap_y", "dao": "phap", "insight": 15, "text": "Pháp tắc vận hành trong đan điền."},
    {"key": "the_y", "dao": "the", "insight": 15, "text": "Thể xác như được tôi luyện."},
]
