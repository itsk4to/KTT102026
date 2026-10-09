## v3.4.8 — Shop Details & PvP Wager Arena

- Tiên Phường hiển thị emoji theo loại vật phẩm, biểu tượng phẩm cấp, giá và tác dụng cụ thể ngay ở danh sách lẫn màn hình chọn vật phẩm.
- Thêm `.pvp @người_chơi linhthach <số> [50|45|55]` và `.pvp @người_chơi vatpham <mã> <số> [50|45|55]`.
- Cược 50/50 yêu cầu giá trị ngang nhau; tỷ lệ 45/55 xác định phần đóng góp của người thách đấu và tự tính phần bên nhận lời.
- Trận đấu theo lượt có Tấn công/Hộ thể; cược được giữ trong escrow khi hai bên nhận lời, người thắng nhận toàn bộ.
- Migration schema 12 → 13 lưu trạng thái cược; nếu bot khởi động lại khi trận đang diễn ra, hệ thống hoàn cược để tránh mất tài sản.

## v3.4.7 — Cửu Lôi Kiếp & Hộ Kiếp

- Đột phá đại cảnh giới từ Kim Đan → Nguyên Anh và các mốc lớn tiếp theo (cùng một cây cảnh giới cho Tu Tiên/Tu Ma) phải vượt 9 tia Cửu Lôi Kiếp.
- Mỗi tia lôi tăng sát thương nhẹ so với tia trước; phòng ngự trang bị và kháng lôi làm giảm sát thương.
- Thêm Lôi Kiếp Đan, Cửu Lôi Hộ Thân Phù và Thiên Lôi Châu; người chơi có thể chọn tối đa hai loại đan/bùa (1–3 liều mỗi loại) trước khi xác nhận đột phá. Liều bổ sung có hiệu lực giảm dần.
- Vật phẩm hộ kiếp chỉ bị tiêu hao khi lần đột phá thành công và Cửu Lôi Kiếp thực sự bắt đầu.
- Thất bại lôi kiếp giữ nguyên cảnh giới, gây tổn thất tu vi/thương thế, còn 1 HP và hồi phục lâu hơn. Vượt kiếp không tự hồi đầy HP.
- Không thay đổi schema database; giữ riêng luồng Ứng Thiên Kiếp cuối Độ Kiếp.

## v3.4.6 — Onboarding, Split Leaderboards & Dao Lữ Commands

- `.bxh` now displays separate Tu Tiên and Tu Ma leaderboards; `.bxh tien` and `.bxh ma` show one faction.
- Added a global new-player onboarding hint before gameplay commands, with `.tutien` / `.tamuontutien` instructions.
- Main-menu buttons now guide players without an account to character creation instead of letting feature views fail.
- Added `.songtu` / `.st` quick command while keeping `.daolu` GUI and `.ketduyen @user` request flow.
- Existing account IDs, database schema, and saved player data are unchanged.

## v3.4.5 — Unified Help & Main Menu
- `.help` now combines beginner onboarding, categorized commands, and the interactive main menu.
- `.menu` remains compatible and opens the same combined interface.

# v3.4.4 — Sect Player Display

- Tông môn: danh sách quản trị thành viên hiển thị `display_name` thay vì raw Discord user ID.
- Tông môn: danh sách đơn xin gia nhập hiển thị tên người chơi.
- Backend vẫn giữ Discord ID làm định danh nội bộ để không ảnh hưởng dữ liệu.

# Changelog


## v3.4.3 — Admin Redeem Code Disable
- Thêm nút **Vô hiệu hóa** trong Kho Mật Lệnh Admin.
- Mật Lệnh bị vô hiệu hóa không thể đổi thưởng nữa.
- Thêm migration schema 11 → 12 với trạng thái `enabled`.
- Ghi audit khi Admin vô hiệu hóa Mật Lệnh.


## v3.4.2 — Exploration & Player Market Hotfix
- Fixed `.khampha` GUI crash caused by missing `EMOJI` import in `exploration_view.py`.
- Restored all exploration view dependencies (`realm_text`, item registry, combat embed and combat view) so the GUI can build and transition into events/combat.
- Fixed `.dangban` crash caused by reading `r["price"]`; market service returns `price_each` for the unit price.


## v3.4.1 — Breakthrough Recovery
- Thất bại đột phá áp dụng thời gian hồi phục theo cảnh giới.
- Trong thời gian hồi phục không thể tu luyện/đột phá/ứng kiếp.
- Thời gian tăng theo đại cảnh giới; tầng cuối và Độ Kiếp có hệ số nặng hơn.
- Thêm migration schema 10 → 11 với `breakthrough_recovery_until`.


## v3.4.0 — Gameplay Integrity & Canonical Tree
- Schema 10: explicit reputation, mission claim state and market unit price.
- Fixed sect mission infinite reward using per-member daily progress/claim state.
- Added sect inbox GUI for applications and invitations.
- Breakthrough items are only consumed on confirmed breakthrough.
- Fixed Dao Lu request rollback when DM delivery fails.
- Connected Dao stage, crit and spirit modifiers to combat.
- Added active talent/destiny modifiers.
- Added reputation state and real reputation consequences.
- Restricted quests/world events to valid context and realm.
- Matched combat encounters/bosses to player realm.
- Added canonical content/economy architecture modules.
- Clarified new market listings as price-per-item.
- Added player-market GUI and full sect member-management GUI.
- Canonicalized UI view files; legacy `*_gui.py` paths remain as compatibility shims only.
- Removed direct database access from services/UI/economy; repositories own persistence boundaries.
- Connected talent injury modifiers and strict NPC zone checks.

## 3.3.8 — Gameplay GUI Expansion
- Chuẩn hóa custom emoji theo semantic mapping do server cung cấp.
- `.tutien` mở GUI chọn Tiên/Ma; giữ legacy args để tương thích.
- Exploration hiển thị cảnh giới tối thiểu và đường Tiên/Ma.
- Combat GUI: Tấn công / Kỹ năng / Dùng vật phẩm / Bỏ chạy; hiển thị Công/HP/Thủ hai bên.
- Breakthrough GUI: Đồng ý / Từ chối / Dùng đạo cụ; thêm đạo cụ hỗ trợ tỷ lệ đột phá.
- Inventory giữ phân loại và dùng nhiều ×1/×5/×10/số khác.
- Thêm Đạo Lữ module + GUI.
- Tông môn thêm Tông Tháp, Nhiệm vụ Tông Môn, nâng cấp Linh Mạch và tạo tông bằng GUI.
- Thêm Thiên Đạo rule store và Kho Mật Lệnh Admin dạng ephemeral.
- Database schema v8.

## 3.3.7 — Admin Version Check
- Thêm nút **Phiên bản** trong Admin.
- Kiểm tra `VERSION.txt` và `pyproject.toml` có đồng bộ hay không.
- Hiển thị phiên bản đang chạy và database schema version.
- Không gọi Internet và không thay đổi gameplay/database schema.

## 3.3.6 — Player Dashboard & Quick Actions
- Thêm trang **Nhân vật** trong Trung Tâm giao diện.
- Thêm dashboard hiển thị thuộc tính, linh thạch, HP, Đạo và tiến độ đột phá.
- Thêm nút thao tác nhanh: **Tu luyện / Đột phá / Thiên kiếp / Daily**.
- Kết quả thao tác có nút quay lại **Nhân vật / Trung tâm / Đóng**.
- `.info` và các lệnh nhanh cũ vẫn giữ nguyên; GUI chỉ là đường thao tác bổ sung.
- Mở Túi và Đạo trực tiếp từ trang Nhân vật.
- Không đổi service/rules/repository/database schema.
- Kiểm tra: `compileall` + static checks PASS; pytest không collect được vì môi trường thiếu `discord.py`.

## 3.3.5 — Main Hub & GUI Navigation
- Thêm `.menu` / `.mn` làm Trung Tâm giao diện chính.
- Phân tách UX rõ ràng: lệnh cho thao tác nhanh, GUI cho hệ thống nhiều lựa chọn.
- `.khampha`, `.nhiemvu`, `.npc`, `.thegioi`, `.tongmon`, `.dao` mở GUI trực tiếp.
- Khám phá có menu chọn khu + nút Khám phá + Săn yêu thú.
- Nhiệm vụ có chọn nhiệm vụ, xem chi tiết, nhận nhiệm vụ và xử lý lựa chọn.
- NPC có chọn NPC và Nói chuyện trực tiếp.
- Tông môn có chọn tông, xin gia nhập, cống hiến bằng modal và rời tông.
- Đạo có chọn Đạo bằng menu.
- Thế giới có chọn biến động, góp sức và làm mới.
- `.help` phân loại rõ **⚡ LỆNH NHANH** và **🖱️ GIAO DIỆN**.
- Giữ nguyên service/rules/repository/database; không đổi schema.

## 3.3.4
- Integrated the supplied custom Discord emoji set into the centralized UI registry.
- Added semantic `accept`, `reject`, `cultivator`, `demon`, and `cultivation` aliases.
- Reused the supplied item/technique/pill/combat emoji across inventory and gameplay UI.
- Kept source identifiers in English and player-facing text in Vietnamese.

# Kato Tu Tiên v3.3.3

## Inventory GUI Polish
- Đổi `.tui` thành mini GUI túi đồ theo 2 lớp menu: chọn loại → chọn vật phẩm.
- Dùng emoji tập trung cho loại vật phẩm, từng vật phẩm và các nút thao tác.
- Nút dùng nhanh: ×1 / ×5 / ×10 / Số khác.
- Nút Trang bị / Học công pháp tự bật theo loại vật phẩm đang chọn.
- Thêm lọc danh mục, phân trang, làm mới và đóng giao diện.
- Hiển thị vật phẩm đang chọn ngay trên embed để thao tác nhanh.
- Không thay đổi business logic hoặc database schema.

Kato Tu Tiên v3.3.2 — Utilities & Vietnamese UI

- Thêm alias lệnh ngắn cho thao tác thường dùng.
- `.tui` mở túi đồ dạng chọn vật phẩm.
- Chọn vật phẩm để xem chi tiết và dùng nhanh / trang bị / học công pháp.
- Thêm phân trang túi đồ, làm mới và đóng giao diện.
- Việt hóa help, menu, nút, nhãn và thông báo người chơi.
- Không đổi business logic, schema database hoặc cấu trúc layer gameplay.

# Kato Tu Tiên v3.3.1

## UX Polish
- Compact cultivation embeds with progress bars.
- Cleaner exploration results and zone list.
- Cleaner NPC, quest journal, and world-event embeds.
- Action-oriented footers for common next steps.
- No gameplay/database changes; custom emoji mapping remains centralized for the upcoming emoji pack.

## 3.3.9 — UX Fixes & Gameplay Audit

- Fixed Dao selection GUI by replacing the single select with direct Dao buttons.
- Added `.ketduyen @player` request flow with recipient DM GUI for Accept/Reject.
- Updated Help with current quick commands, GUI sections, advanced actions and Dao Lu request flow.
- Expanded Shop into a full GUI: category -> item -> quantity -> purchase, with centralized emoji mapping.
- Added Sect "Tuyển thành viên" GUI action for authorized roles.
- Added Dao Lu rejection service.
- Version metadata synchronized to 3.3.9.
