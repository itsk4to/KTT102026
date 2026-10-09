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


# Expanded exploration pool: region gates keep end-game encounters out of early zones.
EXPLORATION_EVENTS.extend([
    {"key": "linh_thao_phat_hien", "weight": 5, "zones": ["hoangnguyen", "yeuthusonmach"], "stones": [45, 130], "cultivation": [35, 90], "text": "Bên cạnh một mạch nước nhỏ, ngươi tìm thấy linh thảo còn đọng sương. Hái được một ít, phần còn lại để lại cho người hữu duyên."},
    {"key": "thuong_nhan_lac_duong", "weight": 4, "zones": ["hoangnguyen", "yeuthusonmach", "dongphu"], "stones": [100, 260], "item": "tu_khi_dan", "text": "Một thương nhân lạc đường đổi chút hàng hóa lấy sự chỉ dẫn. Ngươi vừa có linh thạch vừa nhận được một viên Tụ Khí Đan."},
    {"key": "tinh_anh_yeu_thu", "weight": 5, "zones": ["yeuthusonmach", "haivuc", "mavuc"], "min_realm": 1, "combat": True, "elite": True, "text": "Khí tức khác thường bao phủ con đường. Một yêu thú tinh anh lao ra, mạnh hơn đồng loại rõ rệt!"},
    {"key": "co_tran_phan_phue", "weight": 4, "zones": ["dongphu"], "min_realm": 3, "stones": [120, 320], "cultivation": [80, 180], "injury": [0, 6], "text": "Tàn trận cổ xưa chợt sáng lên. Ngươi tranh thủ thu lấy linh thạch và đạo vận trước khi trận văn tan biến."},
    {"key": "co_mo_bat_dong", "weight": 2, "zones": ["dongphu"], "min_realm": 3, "combat": True, "boss": True, "text": "Cánh cửa cổ mộ rung chuyển. Cổ Mộ Kiếm Linh thức tỉnh, kiếm ý lạnh lẽo khóa chặt thần hồn ngươi!"},
    {"key": "hai_long_tap_kich", "weight": 2, "zones": ["haivuc"], "min_realm": 5, "combat": True, "boss": True, "text": "Mặt biển dựng thành bức tường. Hải Vương nổi lên từ vực sâu, không định để bất kỳ kẻ xâm nhập nào rời đi dễ dàng."},
    {"key": "ma_quan_xuat_the", "weight": 2, "zones": ["mavuc", "vancotlang"], "min_realm": 7, "combat": True, "boss": True, "text": "Ma khí cuộn thành vòng xoáy. Một ma chủ cảm nhận được khí tức của ngươi và tự mình chặn đường."},
    {"key": "phuc_dia_linh_tuyen", "weight": 4, "zones": ["hoangnguyen", "yeuthusonmach", "dongphu"], "stones": [50, 160], "cultivation": [90, 210], "text": "Ngươi phát hiện một khe suối có linh khí dồi dào. Chỉ tĩnh tọa một lát, kinh mạch đã lưu chuyển trơn tru hơn."},
    {"key": "doc_vu_am_hon", "weight": 4, "zones": ["mavuc", "vancotlang"], "min_realm": 7, "injury": [4, 12], "cultivation": [100, 240], "text": "Sương đen len qua hộ thể linh khí. Ngươi cố vận công chống đỡ, tuy bị thương nhẹ nhưng hiểu thêm cách vận chuyển linh lực."},
    {"key": "linh_loi_thien_quang", "weight": 3, "zones": ["haivuc", "hukhong"], "min_realm": 5, "cultivation": [160, 340], "insight": 1, "text": "Một tia thiên quang xuyên qua tầng mây, để lại dấu ấn huyền diệu trong thức hải của ngươi."},
    {"key": "vancot_am_binh", "weight": 3, "zones": ["vancotlang"], "min_realm": 8, "combat": True, "elite": True, "text": "Một đội âm binh bị đánh thức khỏi quan tài đá. Tên cầm đầu khoác giáp tàn tạ nhưng sát khí vẫn đáng sợ."},
    {"key": "hu_khong_rung_dong", "weight": 2, "zones": ["hukhong"], "min_realm": 10, "combat": True, "elite": True, "text": "Không gian bỗng gãy thành từng lớp. Dị thú hư không lao tới, kéo theo từng mảnh tinh thạch vỡ xoay trong cơn lốc."},
    {"key": "tang_bao_co_dai", "weight": 3, "zones": ["dongphu", "haivuc", "vancotlang", "hukhong"], "min_realm": 3, "stones": [180, 420], "item": "tu_khi_dan", "text": "Ngươi tìm được một hòm báu đã mất chủ. Trận bảo vệ đã suy yếu, chỉ còn đủ sức giữ lại chút linh thạch và đan dược."},
    {"key": "vo_tinh_ngo_dao", "weight": 4, "zones": ["yeuthusonmach", "dongphu", "haivuc", "mavuc", "vancotlang", "hukhong"], "cultivation": [120, 300], "insight": 2, "text": "Trong khoảnh khắc sinh tử, ngươi chợt hiểu một phần quy luật vận hành của thiên địa. Tu vi và ngộ tính cùng tăng đôi chút."},
])

CHOICE_EVENTS.extend([
    {
        "key": "thu_vien_tan_tich", "weight": 6, "title": "Thư Viện Tàn Tích", "zones": ["dongphu", "vancotlang", "hukhong"], "min_realm": 3,
        "text": "Một thư viện bị chôn vùi hiện ra sau vách đá. Nhiều ngọc giản đã vỡ, nhưng vẫn còn vài luồng thần niệm chưa tan.",
        "choices": [
            {"id": "doc", "label": "📜 Đọc ngọc giản", "condition": {"insight": 50}, "effect": {"cultivation": [160, 300], "insight": 2, "discover": "thu_vien_tan_tich_doc", "text": "Ngươi ghép nối được vài dòng công pháp cổ, lĩnh hội một chút chân ý."}},
            {"id": "tim", "label": "🔎 Tìm vật còn nguyên", "effect": {"stones": [150, 320], "item": "tu_khi_dan", "text": "Ngươi tìm thấy một hộp đan dược và chút linh thạch còn nguyên vẹn."}},
            {"id": "roi", "label": "🚶 Rời thư viện", "effect": {"fate": 1, "text": "Ngươi không động vào những ngọc giản không rõ lai lịch, tránh được một luồng thần niệm bất ổn."}},
        ],
    },
    {
        "key": "linh_tuyen_that_lac", "weight": 7, "title": "Linh Tuyền Thất Lạc", "zones": ["hoangnguyen", "yeuthusonmach", "haivuc"],
        "text": "Dưới một tảng đá phủ rêu, ngươi phát hiện linh tuyền đang bị rễ cây hút cạn.",
        "choices": [
            {"id": "thu_linh", "label": "💧 Hấp thu linh khí", "effect": {"cultivation": [90, 210], "text": "Ngươi ngồi bên dòng tuyền, hấp thu lượng linh khí vừa đủ mà không làm cạn linh tuyền."}},
            {"id": "go_re", "label": "🌱 Gỡ rễ cây", "condition": {"mind": 45}, "effect": {"stones": [100, 220], "insight": 1, "discover": "linh_tuyen_cuu_ho", "text": "Ngươi khơi lại dòng chảy, đổi lấy một phần linh thạch do linh tuyền kết tinh."}},
            {"id": "bo_qua", "label": "👣 Ghi nhớ vị trí", "effect": {"fate": 1, "text": "Ngươi đánh dấu vị trí và rời đi, để linh tuyền tiếp tục hồi phục."}},
        ],
    },
    {
        "key": "doan_xe_tieu_cuc", "weight": 6, "title": "Đoàn Xe Tiêu Cục", "zones": ["hoangnguyen", "yeuthusonmach", "dongphu", "haivuc"],
        "text": "Một đoàn xe bị chặn giữa đường. Tiêu sư nghi ngờ mọi người xung quanh, nhưng rõ ràng họ đang cần trợ giúp.",
        "choices": [
            {"id": "bao_ve", "label": "🛡️ Giúp hộ tống", "effect": {"stones": [80, 180], "reputation": 2, "text": "Ngươi hộ tống đoàn xe vượt qua đoạn đường nguy hiểm, được trả công xứng đáng."}},
            {"id": "deal", "label": "🤝 Đổi vật phẩm", "effect": {"stones": [40, 130], "item": "hoi_huyet_dan", "text": "Ngươi trao đổi tài nguyên với tiêu cục và nhận được một viên Hồi Huyết Đan."}},
            {"id": "leave", "label": "🚶 Không can dự", "effect": {"text": "Ngươi không muốn mất thời gian, lặng lẽ đi theo lối khác."}},
        ],
    },
    {
        "key": "am_binh_tuan_da", "weight": 5, "title": "Âm Binh Tuần Đêm", "zones": ["mavuc", "vancotlang"], "min_realm": 7,
        "text": "Tiếng giáp sắt vang trong màn sương. Một đội âm binh chặn lối, trên cờ còn ký hiệu của một tông môn đã diệt vong.",
        "choices": [
            {"id": "quan_sat", "label": "👁️ Quan sát đội hình", "condition": {"insight": 58}, "effect": {"insight": 2, "cultivation": [150, 300], "discover": "am_binh_doi_hinh", "text": "Ngươi nhận ra sơ hở trong trận hình, tránh được xung đột và lĩnh hội thêm chút đạo vận."}},
            {"id": "ne_tranh", "label": "🌫️ Lách qua sương", "effect": {"fate": 1, "text": "Ngươi men theo khe nứt nhỏ và tránh được đội âm binh."}},
            {"id": "cuong_hanh", "label": "⚔️ Cưỡng ép vượt qua", "condition": {"mind": 65}, "effect": {"stones": [180, 360], "injury": [6, 14], "text": "Ngươi phá vỡ một kết giới canh gác, đoạt lấy tài vật nhưng cũng chịu phản chấn."}},
        ],
    },
    {
        "key": "loi_van_trong_hu_khong", "weight": 4, "title": "Lôi Văn Trong Hư Không", "zones": ["hukhong"], "min_realm": 10,
        "text": "Những đường lôi văn nổi giữa không trung. Chúng có thể là dấu vết của một lần thiên kiếp cổ đại.",
        "choices": [
            {"id": "dan_luc", "label": "⚡ Dẫn một tia lôi văn", "condition": {"mind": 70}, "effect": {"cultivation": [240, 420], "insight": 2, "injury": [3, 9], "discover": "loi_van_hu_khong", "text": "Ngươi dẫn một tia lôi văn vào kinh mạch. Đạo vận tăng mạnh nhưng thân thể chịu chút áp lực."}},
            {"id": "ghi_chep", "label": "📝 Ghi lại lôi văn", "effect": {"cultivation": [120, 250], "insight": 1, "text": "Ngươi ghi nhớ đường đi của lôi văn, không mạo hiểm hấp thu trực tiếp."}},
            {"id": "roi", "label": "🚶 Lùi lại", "effect": {"fate": 1, "text": "Ngươi nhận ra sức mình chưa đủ để chạm vào lôi văn và chủ động rút lui."}},
        ],
    },
    {
        "key": "hoang_thon_dan_su", "weight": 6, "title": "Đan Sư Ẩn Cư", "zones": ["hoangnguyen", "yeuthusonmach", "dongphu", "vancotlang"],
        "text": "Một đan sư ẩn cư đang tìm nguyên liệu. Ông ta nói có thể chỉ điểm cho ngươi nếu ngươi chịu giúp một tay.",
        "choices": [
            {"id": "giup", "label": "🌿 Tìm nguyên liệu", "effect": {"cultivation": [60, 160], "item": "tu_khi_dan", "reputation": 1, "text": "Ngươi tìm đủ nguyên liệu, được đan sư tặng một viên Tụ Khí Đan và chỉ điểm tu luyện."}},
            {"id": "hoc", "label": "🧠 Thỉnh giáo", "condition": {"insight": 52}, "effect": {"insight": 2, "cultivation": [100, 210], "text": "Ngươi hỏi đúng trọng tâm và nhận được lời giải thích về cách vận khí."}},
            {"id": "tu_choi", "label": "🙏 Từ chối lịch sự", "effect": {"fate": 1, "text": "Ngươi không muốn làm phiền đan sư, hai bên chắp tay cáo biệt."}},
        ],
    },
])

INHERITANCE_EVENTS = [
    {"key": "kiem_y", "dao": "kiem", "insight": 15, "text": "Kiếm ý cổ xưa thấm vào tâm can."},
    {"key": "dao_y", "dao": "dao", "insight": 15, "text": "Đao hồn trấn áp hư không."},
    {"key": "phap_y", "dao": "phap", "insight": 15, "text": "Pháp tắc vận hành trong đan điền."},
    {"key": "the_y", "dao": "the", "insight": 15, "text": "Thể xác như được tôi luyện."},
]
