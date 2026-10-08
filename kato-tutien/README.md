# Kato Tu Tiên v3.0.1

Discord cultivation MMORPG — **clean architecture rework + safety hardening**.

> Ưu tiên số 1: code rõ ràng, module nhỏ, dễ đọc, dễ sửa và dễ mở rộng.

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
| UI | `ui/` | Embeds, Views, emoji |
| Services | `game/services/` | Business logic |
| Rules | `game/rules/` | Pure formulas / permissions |
| Repositories | `game/repositories/` | Persistence access |
| Content | `game/content/` | Static data |
| Models | `game/models/` | Domain objects |
| Database | `game/database/` | Connection, schema, migrations |
| Security | `game/security/` | Admin auth / permissions |

## v3.0.1 updates

### 1. Database migration thật

- Schema version tăng lên `4`.
- Migration chạy từng bước, idempotent.
- DB cũ thiếu known columns được tự sửa bằng `ALTER TABLE` an toàn.
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

Current local result:

```text
26 passed
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
- Nên chạy v3.0.1 trên branch/test DB trước khi cho Railway dùng DB production.
