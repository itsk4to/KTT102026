Kato Tu Tiên v3.5.6 — Economy & Stat Audit

# Kato Tu Tiên v3.5.6

Discord cultivation MMORPG — **clean architecture rework + safety hardening**.

> Ưu tiên số 1: code rõ ràng, module nhỏ, dễ đọc, dễ sửa và dễ mở rộng.

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

- Schema version hiện tại: `14`.
- Migration chạy từng bước, idempotent, có đường nâng cấp 0 → 12.
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
