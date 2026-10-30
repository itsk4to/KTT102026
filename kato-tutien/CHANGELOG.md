## v3.8.1 — Hợp nhất moderation và Phạt Tù Thiên Đạo

- Giữ nguyên gameplay, nội dung, UI và dữ liệu nền từ Kato Tu Tiên v3.7.4.
- Hợp nhất gói moderation v3.8.0; các lệnh được đưa ra cấp gốc: `/ban`, `/unban`, `/kick`, `/timeout`, `/untimeout`, `/warn`, `/warnings`, `/purge`, `/slowmode`, `/lock`, `/unlock`, `/logs`, `/case`. Nhóm `/mod ...` không còn được đăng ký.
- Bổ sung slash `/help`, tái sử dụng `COMMAND_SPECS` và lọc mục quản trị theo quyền người gọi; `.help` vẫn hoạt động.
- Bổ sung `/phattu`, `/tha_tu`, role tù nhân, kênh lao ngục và khôi phục permission overwrites theo snapshot.
- `.kthac` ghi đúng 10 linh thạch lao dịch/lượt, kiểm tra kênh, phiên tù, nhân vật, cooldown và ID tin nhắn để chống tính trùng.
- Hoàn tất tù chuyển qua trạng thái `release_pending`; chỉ chia thưởng sau khi Discord khôi phục quyền thành công. Payout có mã duy nhất, chia đều cho người đã đăng ký, loại trừ mọi tù nhân và người vừa được thả; số dư không chia hết được giữ ở `community_fund`.
- Thêm migration schema 17 → 18; migration 16 → 17 giữ nguyên moderation cases; không reset dữ liệu người chơi.
- Cần cấu hình role/kênh tù trong environment trước khi dùng `/phattu`.

## v3.8.0 — Quản trị máy chủ Discord thủ công

- Tích hợp nhóm Slash Commands `/mod` trên `discord.Client` + `app_commands.CommandTree` hiện tại.
- Bổ sung ban/unban, kick, timeout/untimeout, warn/xem cảnh cáo, purge, slowmode, lock/unlock và tra cứu case.
- Phân quyền qua Discord Owner/Admin, role ID cấu hình hoặc quyền quản trị Discord tương ứng; kiểm tra role hierarchy và quyền của bot trước khi xử lý.
- Tách lịch sử moderation khỏi `admin_audit` của gameplay bằng bảng `moderation_cases` và migration schema 16 → 17.
- Hỗ trợ kênh log tùy chọn qua `KATO_MOD_LOG_CHANNEL_ID`; không bật tự động quét link hoặc tự động xử phạt.
- Không thay đổi dữ liệu nhân vật, gameplay hoặc logic kinh tế.

## Bản vá bổ sung v3.7.4 — Hồ sơ công khai

- Dùng giá trị dự phòng an toàn cho công/ thủ/ HP khi hồ sơ công khai nhận đối tượng người chơi thiếu các thuộc tính chiến đấu.
- Điều chỉnh test trang bị để chấp nhận custom emoji do bộ render emoji chung thay thế, đồng thời vẫn xác minh nhãn và nội dung trang bị.
- Không thay đổi luật gameplay, schema database hoặc dữ liệu người chơi.

## v3.7.4 — Bao phủ Emoji Toàn GUI

- Bổ sung bộ chuyển emoji dùng chung: những emoji Unicode có ánh xạ tương đương sẽ tự dùng custom emoji trong embed, tiêu đề/trường thông tin, author/footer, log chiến đấu và mô tả vật phẩm.
- `ThemedView` tự chuyển emoji cho nút và lựa chọn dropdown, kể cả icon đã khai báo trực tiếp thay vì dùng registry.
- Bổ sung key còn thiếu cho Trung tâm, Bí Cảnh, nhiệm vụ, điều hướng, độ hiếm và các hệ thống GUI; ánh xạ chỉ dùng ID emoji đã được cung cấp.
- Không có custom emoji phù hợp thì vẫn giữ Unicode; `KATO_CUSTOM_EMOJI=0` tắt custom emoji toàn bộ.
- Không sửa luật gameplay, schema database hoặc dữ liệu người chơi.

## v3.7.3 — Tích hợp emoji Discord toàn GUI

- Bật custom emoji từ `assets/emojis/server/emojis.json` mặc định; đặt `KATO_CUSTOM_EMOJI=0` để quay về Unicode.
- Chuẩn hóa màn tra cứu ID vật phẩm dùng registry emoji chung.
- Giữ nguyên các thay đổi riêng tư số dư từ v3.7.2.

# Changelog

## v3.7.2 — Quyền riêng tư số dư linh thạch

- Chỉ lệnh `/info` của chính người chơi mới hiển thị số dư linh thạch đầy đủ (phản hồi riêng tư/DM).
- Ẩn số dư khỏi Trung tâm, hồ sơ dashboard, Shop, giao diện Bí Cảnh và các màn hình liên quan.
- Shop vẫn hiển thị giá món hàng và chi phí giao dịch; thông báo mua hàng không tiết lộ số dư còn lại.
- Lỗi không đủ tiền không nêu số dư hiện có; người chơi được hướng dẫn xem số dư trong `.info`.
- Xác nhận quản trị cấp linh thạch chỉ ghi số lượng đã cấp, không tiết lộ tổng tài sản của người nhận.
- Không thay đổi gameplay, số dư lưu trữ, schema database hoặc dữ liệu người chơi.

## v3.7.1 — Khám Phá: Yêu Thú Cường Hóa & Bestiary Mở Rộng

- Mở rộng danh sách từ 27 lên 48 yêu thú thường và từ 13 lên 20 Boss, thêm quái bản địa cho cả 7 khu vực.
- Bổ sung quái cho cảnh giới cao nhất (Tiên Vương / Tiên Đế), tránh thiếu đối thủ ở cuối tiến trình.
- Tăng sức ép theo khu vực: chỉ số quái tăng theo vùng, cảnh giới và cấp độ trận; Tinh Anh và Boss có hệ số HP/công/thủ riêng.
- Bổ sung 6 sự kiện chiến đấu theo vùng/cảnh giới, gồm Tinh Anh và Boss, để tăng tỷ lệ chạm trán ở khu nguy hiểm.
- Màn hình Khám Phá hiển thị tối đa 7 dấu vết yêu thú cùng cảnh giới xuất hiện, và thêm thông tin Boss có thể gặp.
- Không đổi schema database, ID vật phẩm, hoặc cấu trúc lưu nhân vật.

### Cân bằng dự kiến
- Hoang Nguyên vẫn giữ mức vào game tương đối dễ.
- Hải Vực trở đi tăng rõ rệt độ nguy hiểm; Ma Vực, Vạn Cốt Lăng và Hư Không Cổ Giới dành cho tu sĩ đã chuẩn bị trang bị/kỹ năng.
- Boss có thêm sức bền và sát thương; khuyến nghị hồi phục và trang bị trước khi săn.


## v3.7.0

### GUI
- Cáº©m nang `.help`: layout mobile (TrÆ°á»c/Sau Â· Trung tÃ¢m Â· KhÃ©p láº¡i), lá» trÃ¬nh 5 bÆ°á»c cho ngÆ°á»i má»i, copy tu tiÃªn.


## v3.6.9

### GUI
- Đạo Lộ + Đạo Lữ: layout mobile, nút Trung tâm / Khép lại, copy tu tiên.


## v3.6.8

### GUI
- Xuất hành: layout mobile (chọn khu · Khám phá / Săn · Trung tâm / Làm mới / Khép lại).


## v3.6.7

### GUI
- Sứ mệnh (cốt truyện + ngày/tuần): layout mobile, nút Trung tâm / Khép lại, emoji custom.


## v3.6.6

### GUI
- Bí Cảnh: layout mobile (chọn bí cảnh → Vào / Nhận thưởng / Rời; hàng điều hướng Trung tâm · Làm mới · Khép lại).
- Nút gọn, emoji custom, footer chu kỳ 3 giờ.


## 3.6.5 — Hồ sơ riêng tư
- Thêm slash command `/info`: xem hồ sơ bản thân bằng phản hồi ephemeral; chọn người chơi để xem hồ sơ công khai.
- Hồ sơ công khai chỉ hiển thị cảnh giới, phe, tông môn, chiến lực và trang bị đang mặc; không hiển thị linh thạch, túi đồ hoặc chỉ số thiên phú riêng.
- Lệnh prefix `.info` gửi hồ sơ bản thân qua DM; `.info @player` hiển thị hồ sơ công khai đã lọc.
- Không thay đổi gameplay, công thức chiến đấu hoặc schema database.


- Chuẩn hóa màu sắc, author/footer, bảng thông tin và kiểu nút trong toàn bộ view qua `ui/theme/`.
- Menu chính chuyển sang dạng hub: dropdown hệ thống, nút tắt cho Nhân vật/Khám Phá/Túi/Shop/Bí Cảnh/Nhiệm vụ/Tông Môn/Đạo lữ, kèm Làm mới và BXH.
- Hồ sơ nhân vật có action select; thêm HUD thanh HP/tu vi và trường chỉ số dễ quét.
- Shop tách quầy hàng, chi tiết vật phẩm, ID, giá, số dư và hiệu ứng; Túi Càn Khôn hiển thị 12 món mỗi trang.
- Khám Phá, Chợ Người Chơi, Nhiệm vụ, Bí Cảnh, Thế Giới và Đường Đạo trình bày dữ liệu theo panel; lựa chọn Đạo chuyển sang dropdown + xác nhận.
- Combat embed chỉ thay bố cục thanh HP và log chiến đấu; không sửa callback hoặc service chiến đấu.
- Không đổi schema database hoặc công thức gameplay.

## v3.6.2 — Cân bằng tỷ lệ đột phá
- Sửa lỗi thương thế tăng sau mỗi lần thất bại triệt tiêu điểm bảo hộ, khiến tỷ lệ không cải thiện.
- Thương thế trừ 0,3 điểm phần trăm mỗi điểm; sàn tỷ lệ 10%, trần 90%.
- Thêm test hồi quy cho tỷ lệ tăng sau thất bại và mức phạt thương thế.

## v3.6.1 — Shop, Nhiệm Vụ Thưởng & Bảo Hộ Đột Phá

- Làm rõ luồng Tiên Phường: chọn danh mục, chọn một vật phẩm, xem riêng giá/công dụng/ID/số dư rồi mới mua; sau mua tiếp tục hiển thị chi tiết và số dư mới.
- Thêm nhiệm vụ Khởi hành (một lần), Ngày và Tuần; tiến độ tự ghi khi tu luyện, khám phá hoặc mua vật phẩm thành công, phần thưởng phải nhận thủ công.
- Thưởng nhiệm vụ bị giới hạn theo ngưỡng tu vi tầng hiện tại; nhận thưởng lặp lại bị chặn bằng transaction và trạng thái claim trong SQLite.
- Thêm bảo hộ đột phá: thất bại +5 điểm phần trăm, tối đa +20; mọi dạng đột phá thành công đặt lại về 0, bao gồm Cửu Lôi Kiếp và Ứng Thiên Kiếp.
- Thêm migration schema 15 → 16, cột `players.breakthrough_pity` và bảng `player_mission_progress`; không reset dữ liệu cũ.
- Thêm test cho nhiệm vụ ngày/tuần/khởi hành, chống nhận thưởng hai lần, tiến độ sau giao dịch và bảo hộ đột phá.

## v3.6.0 — Combat / Exploration Skill Reliability

- Sửa luồng GUI chiến đấu: sau mỗi lượt tạo view mới với component ID mới, tránh nút/menu công pháp bị cũ hoặc không phản hồi.
- Thêm bộ đếm lượt cho encounter để đồng bộ các GUI mở trùng; click từ giao diện cũ chỉ tải lại trận, không đánh thêm lượt.
- Tăng thời hạn GUI chiến đấu lên 10 phút; `.khampha` hoặc `.san` sẽ mở lại trận đang diễn ra thay vì ghi đè bằng trận mới.
- Chặn bắt đầu trận mới, khám phá, săn hoặc đổi khu khi vẫn đang chiến đấu; tránh mất encounter và không đốt cooldown vì thao tác bị chặn.
- Kiểm tra công pháp đã học và loại vật phẩm trước khi thi triển; lỗi dữ liệu ID cũ trả thông báo dễ hiểu thay vì tiếp tục với metadata rỗng.
- Đồng bộ chỉ số công/thủ hiển thị trong combat embed với trang bị, thiên phú và Đạo thực tế.
- Thêm test hồi quy cho thi triển công pháp, mastery, encounter cũ, lượt trùng và cooldown trong trận.

## v3.5.9 — Thiên Đạo Admin Session & Security

- Kéo dài phiên Admin từ 5 phút lên 24 giờ.
- Lưu thời điểm tạo/hết hạn phiên trong SQLite để vẫn hợp lệ sau khi bot khởi động lại.
- Thêm migration schema 14 → 15 cho `admin_sessions`; không reset dữ liệu cũ.
- Dashboard và màn hình Thiên Đạo kiểm tra quyền ở mỗi tương tác; xác thực lại khi gửi form thêm quy tắc.
- Không nhúng mật khẩu quản trị dạng chữ thuần vào mã nguồn hoặc ZIP; thay mật khẩu qua `KATO_ADMIN_PASSWORD` trong cấu hình bí mật của host.

## v3.5.8 — Help & Menu Reliability Fix

- `.help` is now a three-page guide with real line breaks and bounded Discord embed lengths.
- `.menu` now opens the actual navigation dashboard instead of duplicating Help.
- Added the player market to the menu select list.
- Added guarded Help navigation (previous/next, open menu, close).
- Main-menu rendering now catches unexpected errors, logs the traceback, and gives the player a safe response.

## v3.5.6 — Economy & Stat Audit

- Cân bằng lại tỷ lệ đột phá: chỉ số nhân vật mới không còn đẩy tỷ lệ mặc định sát trần 92%; trần mới là 90%.
- Thu hẹp chỉ số khởi tạo cho nhân vật mới về 35–75; nhân vật đã tồn tại giữ nguyên.
- Giới hạn thưởng điểm danh theo streak 30 ngày (streak vẫn tiếp tục hiển thị), tránh lạm phát linh thạch dài hạn.
- Giới hạn phần thưởng tu vi từ vật phẩm, khám phá, chiến đấu, nhiệm vụ và sự kiện thế giới ở ngưỡng tầng hiện tại.
- Thưởng chiến đấu tăng nhẹ theo cảnh giới (tối đa +65%), còn boss/tinh anh giữ hệ số riêng.
- Giới hạn hiệu suất linh thạch từ May mắn ở mức +25%.
- Mỗi loại vật phẩm chỉ cấp phần tăng chỉ số vĩnh viễn một lần cho mỗi nhân vật; tu vi/hồi HP dùng lặp lại vẫn hoạt động.
- Sửa metadata/mô tả của vật phẩm chỉ dùng khi đột phá và kháng lôi trang bị.
- Sửa lỗi lựa chọn cuối nhiệm vụ không được lưu trước khi cộng thưởng hoàn thành.
- Thống nhất HP tối đa thực chiến giữa giao diện, hồi phục, thay trang bị và Cửu Lôi Kiếp; tháo trang bị tăng HP sẽ giới hạn HP theo mức mới.
- Kết quả thua trận áp dụng đầy đủ mức mất 1% linh thạch đã khai báo trong quy tắc, song song thương thế và mất tu vi nhỏ.
- Cập nhật tài liệu Cửu Lôi Kiếp để khớp với giá trị kháng lôi hiện hành.
- Thêm test hồi quy cho economy, stats và phần thưởng tu vi.

## v3.5.5 — Khám Phá Mở Rộng, Quái & Boss

- Mở rộng bestiary lên 27 quái thường và 13 boss với vùng xuất hiện riêng; boss có HP, công và thủ cao hơn theo cấp.
- Thêm hai khu endgame: Vạn Cốt Lăng (Ma đạo, cảnh giới 8) và Hư Không Cổ Giới (cảnh giới 10).
- Thêm nhiều sự kiện khám phá tức thời và sự kiện lựa chọn theo vùng/cảnh giới; có yêu thú tinh anh, bảo tàng, linh tuyền, thương đội, âm binh, lôi văn và cơ hội chạm trán boss.
- Đảm bảo sự kiện/boss cấp cao không lọt vào khu hoặc cảnh giới thấp.
- Combat chọn quái bản địa theo vùng; tinh anh mạnh hơn quái thường, GUI hiển thị gợi ý quái/boss có thể gặp.
- Không thay đổi schema database; giữ nguyên các lệnh khám phá hiện tại.

## v3.5.4 — Cân bằng vật phẩm & buff

- Cân bằng lại tu vi, hồi HP, chỉ số trang bị, kháng lôi, tỷ lệ đột phá và hệ số công pháp để tránh vật phẩm đơn lẻ quá mạnh.
- Chuẩn hóa 5 mục Tiên Phường: Đan dược, Bùa chú, Pháp bảo, Binh khí và Công pháp; mỗi mục có đúng 10 vật phẩm.
- Bổ sung vật phẩm mới theo vai trò riêng: hồi phục, bồi bổ, hộ kiếp, công kích, phòng thủ và công pháp.
- Hiển thị rõ HP tối đa, kháng lôi và tỷ lệ đột phá trong chi tiết vật phẩm; hiển thị HP tối đa trong catalog cửa hàng.
- Không thay đổi schema database; giữ nguyên ID các vật phẩm cũ để tương thích kho đồ, chợ, mã quà và dữ liệu người chơi hiện tại.
- Thêm test cân bằng số lượng theo mục và giới hạn các chỉ số vật phẩm.

## v3.5.3 — Bí Cảnh Tu Luyện (3 giờ)

- Thêm bốn bí cảnh theo cảnh giới, mỗi nơi có dải thưởng linh thạch/tu vi khác nhau.
- Người chơi chọn một bí cảnh; sau đủ 3 giờ nhận thưởng, chu kỳ kế tiếp tự khởi động ở cùng bí cảnh.
- Tiến trình được lưu trong SQLite, có migration schema 13 → 14; chỉ một chu kỳ hoạt động cho mỗi người chơi.
- Chặn nhận thưởng sớm/trùng bằng cập nhật có điều kiện trong transaction; tu vi thưởng bị giới hạn theo phần còn lại của tầng để không bỏ qua đột phá.
- Thêm `.bicanh` / `.bc`, GUI mới và đường dẫn từ Trung Tâm; rời sớm sẽ hủy tiến độ đang tích lũy.

## v3.5.2 — System-wide Premium GUI Polish

- Chuẩn hóa toàn bộ view trong `ui/views/` qua `ui/theme/views.py` (`ThemedView`): màu nút nguy hiểm, xác nhận, hành động chính và điều hướng thống nhất.
- Hoàn thiện theme tree riêng `ui/theme/` với quy tắc mở rộng, semantic button tokens và base view dùng chung.
- Chuẩn hóa nhận diện nhãn nút theo ý nghĩa tiếng Việt (kể cả chữ có dấu), để đóng/xóa/từ chối đỏ và xác nhận xanh nhất quán.
- Nâng dashboard trung tâm bằng thanh HP và tiến độ tu vi; phần xem trước được bảo vệ để không làm hỏng điều hướng khi dữ liệu tiến độ lỗi.
- Chỉ thay đổi tầng presentation/UX; không chỉnh service, rules, repository hoặc schema database.

## v3.5.1 — Unified Premium UI Theme

- Tạo cây giao diện độc lập `ui/theme/` gồm design tokens, embed factory, component builders và hướng dẫn mở rộng.
- Đồng bộ bảng màu tím huyền ảo / lam thiên giới / ngọc bích / vàng linh lực / đỏ cảnh báo.
- Gắn chân trang thương hiệu cho embed dùng `base_embed`, giúp các màn hình cũ nhất quán mà không đổi logic gameplay.
- Làm lại Trung Tâm theo bố cục dashboard: cảnh giới, linh thạch, thể trạng, công/thủ, thiên phú, Đạo tâm và lối tắt.
- Sắp xếp lại nút điều hướng thành nhóm gameplay, nhiệm vụ/cộng đồng/kinh tế và hệ thống tu hành nâng cao; chuẩn hóa qua component factory.
- Giữ tương thích các đường import cũ (`ui.colors`, `ui.embeds`) và không thay đổi schema database.

## v3.5.0 — Shop Details & PvP Wager Arena

- Mặc định hiển thị emoji Unicode thông thường cho Linh thạch, phe Tiên, phe Ma và các nút/giao diện, tránh phụ thuộc emoji custom Discord.
- Tách mapping emoji custom vào `assets/emojis/server/emojis.json`; chỉ dùng khi đặt `KATO_CUSTOM_EMOJI=1`.
- Tạo tài liệu cấu trúc ở `assets/emojis/README.md` và `assets/emojis/server/README.md`.

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
