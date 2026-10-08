# Changelog

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
