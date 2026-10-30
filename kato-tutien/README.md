Kato Tu Tiên v3.8.1 — Moderation & Phạt Tù Thiên Đạo

# Kato Tu Tiên v3.8.1

Discord cultivation MMORPG — **clean architecture rework + safety hardening**.

> Ưu tiên số 1: code rõ ràng, module nhỏ, dễ đọc, dễ sửa và dễ mở rộng.

## Giao diện MMORPG — nền v3.7.4, phát hành v3.8.1

- HUD nhân vật, thanh HP/tu vi, bảng chỉ số và điều hướng game được đồng bộ qua `ui/theme/`.
- Menu chính gọn lại với dropdown hệ thống + nút tắt; màn Nhân vật có action menu.
- Shop, Túi Càn Khôn, Nhiệm vụ, Khám Phá, Bí Cảnh, Chợ và Đường Đạo dùng panel/field và dropdown để đọc dễ hơn trên di động.
- Chỉ thay đổi presentation; logic chiến đấu và dữ liệu gameplay giữ nguyên.

## Cơ chế hồi phục sau thất bại đột phá

Khi đột phá thất bại, nhân vật bị thương và bước vào trạng thái **Hồi phục**. Trong thời gian này không thể tu luyện, đột phá lại hoặc Ứng Thiên Kiếp. Thời gian được tính theo đại cảnh giới đang đột phá:

| Đại cảnh giới | Hồi phục |
|---|---:|
| Luyện Khí | 1 phút |
| Trúc Cơ | 2 phút |
| Kim Đan | 5 phút |
| Nguyên Anh | 10 phút |
| Hóa Thần | 15 phút |
| Luyện Hư | 20 phút |
| Hợp Thể | 30 phút |
| Đại Thừa | 1 giờ |
| Độ Kiếp | 2 giờ |
| Chân Tiên | 3 giờ |
| Thiên Tiên | 4 giờ |
| Tiên Vương | 6 giờ |
| Tiên Đế | 8 giờ |

Tầng cuối của một đại cảnh giới tăng thêm 25%. Thất bại Thiên Kiếp tăng thêm 50%. Trạng thái được lưu trong database nên restart bot không làm mất thời gian hồi phục.

## Shop, Nhiệm vụ & Bảo hộ đột phá (v3.6.1)

- Shop mở theo luồng danh mục → chọn một vật phẩm → xem chi tiết → mua; chi tiết cho biết ID, phẩm cấp, giá, hiệu ứng và số dư linh thạch sau giao dịch.
- `.nhiemvu thuong` mở nhiệm vụ Khởi hành, Ngày và Tuần. Tiến độ tự tăng sau hành động tu luyện/khám phá/mua sắm thành công; người chơi phải bấm nhận thưởng.
- Nhiệm vụ ngày làm mới 00:00 và nhiệm vụ tuần làm mới vào thứ Hai theo múi giờ `Asia/Ho_Chi_Minh`. Phần thưởng linh thạch và tu vi chỉ nhận một lần mỗi chu kỳ.
- Mỗi lần đột phá thất bại tích lũy +5 điểm phần trăm bảo hộ, tối đa +20; thành công sẽ đặt bảo hộ về 0. Điểm bảo hộ được lưu trên nhân vật và hiển thị trong preview.
- SQLite schema 16 thêm `breakthrough_pity` và bảng `player_mission_progress` bằng migration; dữ liệu người chơi cũ được giữ nguyên.

## Combat / Khám Phá reliability (v3.6.0)

- View chiến đấu được tạo mới sau mỗi lượt để đồng bộ component ID của nút và menu kỹ năng.
- Encounter giữ bộ đếm lượt; các GUI cũ hoặc mở trùng được làm mới mà không thực hiện thêm lượt.
- Khi còn trận đang đánh, `.khampha` và `.san` mở lại trận đó; hệ thống không ghi đè encounter hay tiêu hao cooldown khám phá/săn.
- GUI chiến đấu có timeout 10 phút. Nếu hết hạn, dùng `.khampha` hoặc `.san` để mở lại trận còn hiệu lực.
- Chỉ công pháp đã học mới được thi triển; ID công pháp không hợp lệ trả thông báo hướng dẫn.
- Combat embed hiển thị công/thủ thực chiến sau trang bị và các hệ số hiện hành.

## Architecture

```text
Discord transport / commands
          ↓
        UI / Views
          ↓
       Services
          ↓
         Rules
          ↓
     Repositories
          ↓
       Database

Content = static game data
Models  = domain data
```

| Layer | Path | Responsibility |
|-------|------|----------------|
| Discord entry | `bot.py` | Client startup, prefix routing, slash wiring |
| Commands | `ui/commands/` | Command handlers grouped by domain |
| UI | `ui/` | Embeds, Views, emoji và điều hướng |
| UI Theme | `ui/theme/` | Design tokens, embed factory, component builders; chỉ phụ trách trình bày |
| Services | `game/services/` | Business logic |
| Rules | `game/rules/` | Pure formulas / permissions |
| Repositories | `game/repositories/` | Persistence access |
| Content | `game/content/` | Static data |
| Models | `game/models/` | Domain objects |
| Database | `game/database/` | Connection, schema, migrations |
| Security | `game/security/` | Admin auth / permissions |

## Architecture / v3.0 rework

### 1. Database migration thật

- Schema version hiện tại: `18` (từ schema 16 của nền v3.7.4, qua moderation 17 và prison 18).
- Migration chạy tuần tự và idempotent; không reset dữ liệu người chơi hiện có.
- DB cũ thiếu known columns được tự sửa bằng `ALTER TABLE` an toàn; migration 9 → 10 bổ sung giá / cái cho chợ.
- Không còn kiểu chỉ đổi số version rồi giả vờ migration đã xong.
- Thêm `sect_role_history` để lưu lịch sử chức vụ.

### 2. Transaction thật sự

`Database.transaction()` giờ chặn các repository commit giữa chừng.

Các giao dịch quan trọng được bọc atomic:

- Shop purchase
- Dùng vật phẩm
- Học công pháp
- Player market list/buy/cancel
- Chuyển linh thạch
- Redeem code
- Gacha
- Tạo / duyệt / mời / rời / giải tán tông môn
- Cống hiến tông môn
- Admin mutation

Ví dụ lỗi giữa giao dịch sẽ rollback thay vì mất tiền nhưng không nhận item.

### 3. Bot không còn phình thành một file command

`bot.py` hiện chỉ giữ transport/routing.

Command đã tách theo domain:

```text
ui/commands/
├── core.py
├── cultivation.py
├── exploration.py
├── economy.py
├── dao.py
├── sect.py
└── admin.py
```

Muốn sửa Shop → `ui/commands/economy.py` + service liên quan.
Muốn sửa Tông môn → `ui/commands/sect.py` + `game/services/sect_service.py`.

### 4. Tông môn có authority thật hơn

- Application + invitation.
- Permission matrix.
- Không thể tự đổi chức.
- Không thể gán chức vụ bằng hoặc cao hơn quyền của người thao tác.
- Promote / demote được kiểm soát theo rank.
- Khai trừ có kiểm tra quyền.
- Tông Chủ có thể nhường chức.
- Lịch sử đổi chức vụ được lưu.
- Không tạo application/invitation pending trùng.

### 5. Admin GUI cơ bản

Có:

```text
/admin
└── 🔐 Login Modal
    └── 👑 Admin View
        ├── 📊 Tổng quan
        ├── 💎 Cấp linh thạch
        ├── 📜 Audit
        └── ✖️ Đóng phiên
```

Password không phải gõ trực tiếp vào prefix message.

Admin mutation đi qua `game/services/admin_service.py` và có audit log.

### 6. Shop / túi

Shop vẫn giữ service-first architecture.
Túi không bị thay đổi theo kiểu phá API cũ.
Bộ test Shop vẫn chạy đầy đủ.

## Tests

```bash
python -m pytest -q
```

Ngoài full shop suite còn có test cho:

- migration repair
- transaction rollback
- sect authority matrix
- sect role history

## Runtime

```bash
python -m pip install -r requirements.txt
# set DISCORD_TOKEN, KATO_ADMIN_PASSWORD, KATO_OWNER_IDS
python bot.py
```

### Admin / Thiên Đạo session (v3.5.9)

- Admin login is configured through the host secret/environment variable `KATO_ADMIN_PASSWORD`; the password is intentionally not hard-coded into the repository or ZIP. Set that variable to the new password in Railway/hosting settings before redeploying.
- A successful login grants a **24-hour session**, stored in SQLite (`admin_sessions`) and retained across bot restarts. `.admin` can reopen the panel while that session remains valid.
- Use **Đóng** to revoke the current user's session immediately. Expired sessions are deleted when checked. Admin GUI buttons re-check authorization on every interaction.
- Historical note: the database schema advanced from 14 to 15 for admin sessions; v3.6.1 advances schema 15 to 16 for breakthrough protection and repeatable missions. Existing player data is preserved.

## Production safety

- Không commit secret/token/password vào GitHub.
- v2 production không cần bị xóa để thử v3.
- Migration không tự reset database.
- Nên chạy v3.4.7 trên branch/test DB trước khi cho Railway dùng DB production.


## UX nhanh

`.help` hoặc `.menu` mở Trung Tâm giao diện và hướng dẫn nhập môn.
Các hệ thống nhiều lựa chọn ưu tiên GUI; các hành động lặp lại giữ lệnh tắt như `.tu`, `.dp`, `.tk`, `.dl`.


## Cửu Lôi Kiếp · Thông số hiện tại

Từ mốc **Kim Đan tầng 9 → Nguyên Anh tầng 1**, mỗi lần đột phá qua đại cảnh giới đến trước cửa Ứng Thiên Kiếp đều phải chịu 9 tia sét. Quy tắc dùng cùng chỉ số cảnh giới cho cả Tu Tiên và Tu Ma. Mỗi tia tăng sát thương dần; phòng ngự và kháng lôi từ pháp bảo làm giảm sát thương.

- **Lôi Kiếp Đan**: giảm 12% sát thương cơ bản cho lần hộ kiếp.
- **Cửu Lôi Hộ Thân Phù**: giảm 10%; **Tĩnh Lôi Phù**: giảm 8% cho lần hộ kiếp.
- **Thiên Lôi Châu**: kháng lôi 8% khi trang bị; **Huyền Thiết Linh Kính**: 5%.
- Chọn đan/bùa trong giao diện `.dotpha`. Có thể phối hợp tối đa hai loại; mỗi loại chọn 1–3 liều. Liều thứ hai và ba tăng hiệu lực theo mức giảm dần; vật phẩm chỉ bị tiêu hao khi Cửu Lôi Kiếp thực sự bắt đầu.
- Kháng lôi cộng dồn và phòng ngự đều có giới hạn; tổng giảm sát thương sau phòng ngự bị chặn ở 65%.
- Đan/bùa không bị mất nếu lần đột phá thông thường thất bại trước khi lôi kiếp bắt đầu. Khi lôi kiếp bắt đầu, vật phẩm đã chọn bị tiêu hao dù sống sót hay thất bại.
- Nếu thất bại, cảnh giới không tăng, tu vi và tuổi thọ bị tổn thất, thương thế nặng, HP còn 1 và phải hồi phục. Nếu thành công, HP còn lại sau chín tia được giữ nguyên.



## UI Theme (v3.5.2)

Toàn bộ giao diện Discord dùng cây thiết kế riêng `ui/theme/`: `tokens.py` quản lý màu sắc/role,
`embeds.py` tạo embed có thương hiệu, `components.py` tạo component dùng chung, và `views.py`
chuẩn hóa kiểu nút cho tất cả màn hình. Các view tính năng kế thừa `ThemedView`, còn callback và
logic gameplay vẫn ở module tính năng hiện tại. Trung tâm có thanh HP và tiến độ tu vi để dễ đọc
trạng thái nhân vật ngay khi mở menu.

## Bí Cảnh Tu Luyện (v3.5.3)

Dùng `.bicanh` hoặc `.bc` để mở GUI bí cảnh. Chọn một nơi phù hợp với cảnh giới; mỗi chu kỳ kéo dài 3 giờ. Khi đủ thời gian, nhận linh thạch và tu vi, sau đó chu kỳ mới tự bắt đầu tại cùng bí cảnh. Dùng nút **Rời bí cảnh** để đổi nơi; rời trước khi đủ thời gian sẽ hủy tiến độ chưa nhận. Trạng thái được lưu trong SQLite nên còn sau khi bot khởi động lại; sau restart, dùng lại `.bicanh` để mở giao diện mới. Mỗi lần chỉ tích lũy một phần thưởng, không cộng dồn nhiều chu kỳ bỏ quên.


## Khám Phá mở rộng (v3.5.5)

- Tăng bestiary lên 27 quái thường và 13 boss, phần lớn được gắn vùng xuất hiện để mỗi khu có bản sắc riêng.
- Thêm Vạn Cốt Lăng (cảnh giới 8, Ma đạo) và Hư Không Cổ Giới (cảnh giới 10, cả hai con đường).
- Bổ sung nhiều tình huống tức thời và sự kiện lựa chọn, bao gồm yêu thú tinh anh, tàn tích, linh tuyền, thương đội, âm binh, lôi văn và những lần chạm trán boss theo khu vực.
- Khu vực được ưu tiên chọn quái/boss bản địa; sự kiện cuối game bị khóa theo cảnh giới, tránh xuất hiện sớm ở khu thấp.
- GUI Khám Phá hiển thị dấu vết quái và boss có thể gặp. Encounter giữ nguyên cooldown, kết quả chiến đấu và cơ chế thưởng hiện có; không đổi schema database.


## Audit tiền tệ & chỉ số (v3.5.6)

Các thông số cân bằng hiện tại được ghi chi tiết tại [`docs/ECONOMY_AND_BALANCE.md`](docs/ECONOMY_AND_BALANCE.md). Bản audit giới hạn thưởng tu vi theo tầng hiện tại, phần thưởng điểm danh theo streak 30 ngày, mức tăng linh thạch từ May Mắn ở +25%, và tỷ lệ đột phá trong 5%–90%. Chỉ số chiến đấu/HP trên menu dùng giá trị thực chiến sau trang bị, thiên phú và Đạo; bỏ trang bị HP sẽ kẹp HP theo giới hạn mới. Thất bại chiến đấu áp dụng các hình phạt đã khai báo: thương thế, mất tu vi nhỏ và 1% linh thạch (không vượt quá số đang sở hữu).


## v3.6.2 — Sửa cân bằng tỷ lệ đột phá

- Giảm mức phạt thương thế trong công thức đột phá từ 1 điểm phần trăm mỗi điểm thương thế xuống 0,3 điểm phần trăm.
- Mỗi lần thất bại thông thường (+5 bảo hộ, +5 thương thế) nay tăng tỷ lệ dự kiến ròng khoảng 3,5 điểm phần trăm thay vì hai hiệu ứng triệt tiêu nhau.
- Tỷ lệ tối thiểu tăng từ 5% lên 10%; trần vẫn là 90%.
- Công thức preview và lần thử thật vẫn dùng cùng một hàm; chỉ số căn cơ, đạo tâm, ngộ tính, đạo giai, thương thế, thiên phú/định mệnh, vật phẩm và bảo hộ vẫn có ảnh hưởng.
- Không thay đổi logic chiến đấu/khám phá hoặc schema database.

## v3.8.1 — Moderation & Phạt Tù Thiên Đạo

Bản 3.8.1 được xây dựng trên toàn bộ mã nguồn Kato Tu Tiên v3.7.4 và tích hợp gói moderation v3.8.0. Không thay thế hệ thống gameplay cũ. Database được nâng tuần tự từ schema 16 lên 18; hãy sao lưu file SQLite trước khi deploy như với mọi bản cập nhật.

### Cấu hình Discord moderation

- `KATO_MOD_ADMIN_ROLE_IDS`: Role ID có quyền quản trị moderation đầy đủ, phân tách bằng dấu phẩy.
- `KATO_MODERATOR_ROLE_IDS`: Role ID nhận diện đội Moderator; từng slash command vẫn yêu cầu quyền Discord tương ứng riêng.
- `KATO_MOD_LOG_CHANNEL_ID`: Kênh log moderation tùy chọn.

Các lệnh moderation được đăng ký ở cấp gốc: `/ban`, `/unban`, `/kick`, `/timeout`, `/untimeout`, `/warn`, `/warnings`, `/purge`, `/slowmode`, `/lock`, `/unlock`, `/logs`, `/case`.

### Cấu hình Phạt Tù Thiên Đạo

Cấu hình trên host (không commit ID/token bí mật):

- `KATO_PRISON_ROLE_ID`: ID role Tù Nhân.
- `KATO_PRISON_CHANNEL_ID`: ID kênh văn bản lao ngục.
- `KATO_PRISON_ANNOUNCE_CHANNEL_ID`: ID kênh thông báo mãn hạn tù.
- `KATO_PRISON_COOLDOWN_SECONDS`: Cooldown giữa các lượt `.kthac` (mặc định 30 giây).
- `KATO_PRISON_MAX_REQUIRED_STONES`: Chỉ tiêu tối đa cho `/phattu` (mặc định 1.000.000).

Bot cần bật **Server Members Intent** trong Discord Developer Portal và quyền **Manage Roles** và **Manage Channels**; role bot phải cao hơn role Tù Nhân và các role mục tiêu. Dùng một role Tù Nhân chuyên biệt, không gán thủ công cho người chơi. Role/channel ID phải thuộc cùng máy chủ. Kiểm tra cấu hình trong một kênh thử nghiệm trước khi đưa vào server chính.

`/phattu member required_stones reason` có thể áp dụng cả người chưa đăng ký nhân vật. Người chưa đăng ký chỉ có thể dùng `.tutien` để tạo nhân vật ngay trong kênh lao ngục; sau đó dùng `.kthac`. Tù nhân chỉ dùng `.tutien`, `.kthac`, `.help` trong kênh lao ngục; `.kthac` luôn cộng 10 linh thạch lao dịch vào phiên tù, không cộng vào ví cá nhân. Khi đủ chỉ tiêu, bot khôi phục permission overwrites đã chụp trước đó, gỡ role tù và chia tổng lao dịch cho người chơi đã đăng ký nhưng không còn phiên tù đang hoạt động (bao gồm cả người vừa được thả trong sự kiện đó). Phần dư được ghi vào `community_fund`. `/tha_tu` là lệnh đặc xá thủ công dành cho Owner/Admin.

Nếu Discord không thể khôi phục mọi overwrite, phiên tù ở trạng thái chờ xử lý và payout chưa được thực hiện. Kiểm tra log/quyền bot rồi chạy lại `/tha_tu` hoặc restart bot để recovery thử lại.

### Cập nhật từ v3.7.4 lên v3.8.1

1. Dừng bot và sao lưu file SQLite đang dùng (đường dẫn `KATO_DB_PATH`; mặc định `kato_tutien.db`).
2. Giải nén toàn bộ gói `KatoTuTien-v3.8.1-complete.zip` và cập nhật mã nguồn. Giữ lại file `.env` và database hiện tại; không tạo database mới để thay thế.
3. Bổ sung các biến `KATO_PRISON_*` trong phần cấu hình phía trên, đồng thời kiểm tra role/kênh thuộc đúng máy chủ Discord.
4. Cài dependency bằng `python -m pip install -r requirements.txt`.
5. Khởi động bot. Migration sẽ tự chạy tuần tự từ schema 16 lên 17 rồi 18; không xóa dữ liệu nhân vật.
6. Trước khi dùng ở máy chủ chính, thử `/phattu`, `.tutien`, `.kthac`, tự động mãn hạn và `/tha_tu` trong máy chủ thử nghiệm.

Không chia sẻ token bot hoặc nội dung `.env`. Nếu migration bị gián đoạn, dừng bot, khôi phục bản sao lưu và kiểm tra log trước khi chạy lại.
