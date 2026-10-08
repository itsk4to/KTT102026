# Kato Tu Tiên v3.0 — Architecture Blueprint

> Mục tiêu cao nhất: **code clear, dễ đọc, dễ sửa, dễ mở rộng**.
>
> Đây là blueprint cho bản rework MMORPG tu tiên. Chưa thay thế production `main`.

---

## 1. Nguyên tắc kiến trúc

### 1.1. Mỗi module chỉ có một trách nhiệm chính

Không để một file vừa xử lý:
- Discord UI
- gameplay
- database
- permission
- content
- business rules

Ví dụ:

```text
UI -> Service -> Repository -> Database
```

### 1.2. Gameplay không phụ thuộc Discord

Logic game phải có thể test mà không cần Discord.

Ví dụ:

```python
combat_service.attack(player, monster)
```

Không:

```python
async def discord_attack_button(...):
    # tính damage
    # sửa HP
    # sửa DB
    # tạo embed
```

Discord chỉ là lớp giao diện gọi service.

### 1.3. Không dùng `engine.py` làm nơi chứa mọi logic

`engine.py` chỉ đóng vai trò facade/entrypoint cho các service.

Ví dụ:

```python
engine.cultivation.train(...)
engine.combat.attack(...)
engine.sect.apply(...)
```

### 1.4. Content tách khỏi logic

Cảnh giới, item, monster, skill, khu vực... không được rải khắp service.

### 1.5. Database tách khỏi gameplay

Service không viết SQL trực tiếp.

```text
Service
   ↓
Repository
   ↓
Database
```

### 1.6. UI tách khỏi dữ liệu

Embed/View/Button/Select chỉ nhận dữ liệu đã được chuẩn hóa.

---

# 2. Cấu trúc thư mục đề xuất

```text
kato-tutien/
│
├── bot.py
├── config.py
│
├── game/
│   ├── __init__.py
│   ├── engine.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── player.py
│   │   ├── sect.py
│   │   ├── item.py
│   │   ├── combat.py
│   │   ├── world.py
│   │   └── economy.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── player_service.py
│   │   ├── cultivation_service.py
│   │   ├── breakthrough_service.py
│   │   ├── dao_service.py
│   │   ├── combat_service.py
│   │   ├── exploration_service.py
│   │   ├── fate_service.py
│   │   ├── sect_service.py
│   │   ├── economy_service.py
│   │   ├── reputation_service.py
│   │   ├── death_service.py
│   │   └── admin_service.py
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── player_repository.py
│   │   ├── sect_repository.py
│   │   ├── inventory_repository.py
│   │   ├── market_repository.py
│   │   ├── world_repository.py
│   │   └── audit_repository.py
│   │
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── cultivation_rules.py
│   │   ├── combat_rules.py
│   │   ├── dao_rules.py
│   │   ├── sect_rules.py
│   │   ├── economy_rules.py
│   │   └── death_rules.py
│   │
│   ├── content/
│   │   ├── __init__.py
│   │   ├── realms.py
│   │   ├── dao_paths.py
│   │   ├── items.py
│   │   ├── pills.py
│   │   ├── talismans.py
│   │   ├── artifacts.py
│   │   ├── techniques.py
│   │   ├── monsters.py
│   │   ├── zones.py
│   │   ├── dungeons.py
│   │   └── events.py
│   │
│   ├── economy/
│   │   ├── __init__.py
│   │   ├── currency.py
│   │   ├── crafting.py
│   │   ├── npc_shop.py
│   │   ├── player_market.py
│   │   └── auction.py
│   │
│   ├── security/
│   │   ├── __init__.py
│   │   ├── permissions.py
│   │   ├── admin_auth.py
│   │   └── audit.py
│   │
│   └── database/
│       ├── __init__.py
│       ├── connection.py
│       ├── schema.py
│       └── migrations.py
│
├── ui/
│   ├── __init__.py
│   ├── emoji.py
│   ├── colors.py
│   ├── embeds.py
│   ├── menus.py
│   ├── buttons.py
│   ├── selects.py
│   └── views/
│       ├── player_view.py
│       ├── inventory_view.py
│       ├── cultivation_view.py
│       ├── combat_view.py
│       ├── sect_view.py
│       ├── shop_view.py
│       └── admin_view.py
│
└── tests/
    ├── unit/
    ├── integration/
    └── test_shop.py
```

---

# 3. Luồng dữ liệu chuẩn

Mọi chức năng gameplay mới nên đi theo:

```text
Discord
   ↓
Command / View
   ↓
Service
   ↓
Rules
   ↓
Repository
   ↓
Database
```

Content được service/rules đọc từ:

```text
game/content/
```

Ví dụ người chơi đột phá:

```text
/button Đột Phá
      ↓
cultivation_view.py
      ↓
breakthrough_service.py
      ↓
breakthrough_rules.py
      ↓
player_repository.py
      ↓
SQLite
```

---

# 4. Player Model

Player là trung tâm nhưng không được chứa toàn bộ gameplay logic.

Các nhóm dữ liệu chính:

```text
Identity
- id
- name
- created_at

Cultivation
- realm
- realm_level
- cultivation_exp
- foundation
- lifespan
- injuries

Dao
- dao_path
- dao_level
- dao_affinities

Combat
- hp
- max_hp
- spirit
- attack
- defense
- accuracy
- evasion
- crit

Social
- sect_id
- sect_role
- contribution
- reputation

Economy
- spirit_stones

Progression
- achievements
- titles
- discoveries
```

---

# 5. Tu luyện

Service:

```text
cultivation_service.py
breakthrough_service.py
```

Rules:

```text
cultivation_rules.py
```

Các trạng thái:

```text
Tụ Khí
Trúc Cơ
Kim Đan
Nguyên Anh
Hóa Thần
...
```

Đột phá có thể gồm:

```text
cơ sở thành công
+ căn cơ
+ công pháp
+ chuẩn bị
+ đan dược
+ cơ duyên
- thương thế
- trạng thái xấu
```

Không hard-code toàn bộ công thức trong UI.

---

# 6. Đạo & Build

Đường Đạo là hệ thống build:

```text
⚔️ Kiếm
🗡️ Đao
🔮 Pháp
🛡️ Thể
👹 Ma
```

Mỗi Đạo có:

```text
identity
bonuses
weaknesses
skills
scaling
synergy
```

Build được hình thành bởi:

```text
Cảnh giới
+ Căn cơ
+ Đạo
+ Công pháp
+ Pháp bảo
+ Đan dược
+ Phù chú
+ Trang bị
```

---

# 7. Chiến đấu

Combat phải dùng một combat model/service độc lập Discord.

```text
CombatService
├── start_battle()
├── perform_action()
├── calculate_hit()
├── calculate_damage()
├── apply_status()
├── check_victory()
└── finish_battle()
```

Combat rules xử lý:

```text
cảnh giới
Đạo
khắc chế
crit
accuracy
evasion
defense
status effect
terrain
```

PvE và PvP dùng cùng core combat engine, nhưng luật trận đấu có thể khác.

---

# 8. Cơ duyên

Fate/Event system:

```text
game/services/fate_service.py
game/content/events.py
```

Ví dụ:

```text
🌌 Cơ duyên xuất hiện

Bạn phát hiện một cổ động phủ.

[ Khảo sát ]
[ Rời đi ]
[ Ép mở ]
```

Kết quả có thể:

```text
phần thưởng
thương thế
truyền thừa
địch thủ
mất tài nguyên
thay đổi danh vọng
mở khóa nội dung
```

Quan trọng: lựa chọn phải có hậu quả.

---

# 9. Tông môn

Tông môn là một domain riêng.

```text
Sect
├── identity
├── hierarchy
├── members
├── permissions
├── treasury
├── applications
├── invitations
├── missions
├── facilities
└── reputation
```

Cấp bậc ví dụ:

```text
👑 Tông Chủ
⚖️ Phó Tông Chủ
📜 Trưởng Lão
🪶 Chấp Sự
⚔️ Nội Môn Đệ Tử
🌿 Ngoại Môn Đệ Tử
🧹 Tạp Dịch
```

### Gia nhập

Không tự động vào tông môn.

Hai luồng:

```text
Player → Xin gia nhập → Chờ duyệt → Có người duyệt → Gia nhập
```

hoặc:

```text
Tông môn → Mời → Player chấp nhận → Gia nhập
```

### Quyền hạn

Mỗi chức vụ có permission riêng:

```text
sect.invite
sect.accept_application
sect.kick
sect.promote
sect.demote
sect.manage_treasury
sect.manage_facilities
sect.manage_missions
```

Không dựa đơn giản vào tên chức vụ.

---

# 10. Thế giới

World gồm:

```text
Region
Zone
Resource
Monster
Dungeon
Event
```

World có trạng thái theo thời gian:

```text
thường
→ sự kiện
→ biến động
→ thay đổi tài nguyên
→ kết thúc sự kiện
```

Sau này có thể mở rộng thành:

```text
chiến tranh
thiên tai
bí cảnh mở
boss xuất hiện
tài nguyên khan hiếm
```

---

# 11. Kinh tế

Tách ba loại thị trường:

```text
NPC Shop
Player Market
Auction
```

Ngoài ra:

```text
Alchemy
Smithing
Talisman
Crafting
```

Linh thạch là tiền tệ cốt lõi.

Không cho service tự sửa tiền tùy ý; mọi giao dịch đi qua economy rules/service để tránh bug duplication.

---

# 12. Danh vọng

Các bảng:

```text
🏆 Thiên Kiêu
📜 Truyền Thuyết
⚔️ Chiến tích
🏯 Tông môn
💰 Phú hào
🧭 Khám phá
```

Lịch sử nhân vật nên lưu các mốc quan trọng:

```text
đột phá cảnh giới
giết boss
nhận truyền thừa
gia nhập tông môn
lập công
chiến thắng PvP
đạt danh hiệu
```

---

# 13. Sinh tử

Không nhất thiết chết = xóa nhân vật.

Có thể có:

```text
bị thương
mất tài nguyên
giảm đạo tâm
mất thọ nguyên
rơi trang bị
tổn thất tu vi
để lại lịch sử
```

Death rules phải nằm riêng:

```text
game/rules/death_rules.py
game/services/death_service.py
```

Không nhúng death logic vào combat UI.

---

# 14. Lựa chọn

Mọi event quan trọng nên có:

```text
Choice
Condition
Consequence
History
```

Ví dụ:

```text
Bạn tìm thấy một truyền thừa Ma đạo.

[ Nhận ]
[ Từ chối ]
[ Phá hủy ]
```

Mỗi lựa chọn có thể ảnh hưởng:

```text
Player
Sect
Reputation
World
Future events
```

---

# 15. UI + Emoji

Emoji phải tập trung một chỗ:

```text
ui/emoji.py
```

Ví dụ:

```python
EMOJI = {
    "player": "...",
    "cultivation": "...",
    "breakthrough": "...",
    "attack": "...",
    "defense": "...",
    "sword": "...",
    "dao": "...",
    "magic": "...",
    "body": "...",
    "demon": "...",
    "sect": "...",
    "pill": "...",
    "artifact": "...",
    "talisman": "...",
    "technique": "...",
    "spirit_stone": "...",
}
```

Sau này thay custom emoji chỉ cần sửa file này.

UI không tự chứa game rules.

---

# 16. Admin

Admin UI độc lập:

```text
👑 ADMIN

├── 👤 Players
├── 🏯 Sects
├── 🎒 Items
├── ⚔️ Combat
├── 🌍 World
├── 💰 Economy
├── 📊 Statistics
├── 🗄️ Database
└── 🔐 Security
```

Admin actions phải có audit log.

Không đặt logic admin vào các service gameplay nếu không cần thiết.

---

# 17. Shop — bug hiện tại

Bug:

```text
Shop không mở được
```

Bắt buộc có test:

```text
tests/test_shop.py
```

Các test tối thiểu:

```text
shop loads
shop category loads
buy valid item
buy insufficient funds
buy invalid item
buy quantity
inventory receives item
transaction is atomic
```

Nếu UI hỏng nhưng service hoạt động thì sửa UI.

Nếu service hỏng thì sửa service.

Không dùng cách "patch đại" trong `bot.py`.

---

# 18. Database

Repository là lớp duy nhất giao tiếp database.

Ví dụ:

```python
player_repository.get(player_id)
player_repository.save(player)

sect_repository.get(sect_id)
sect_repository.save(sect)

inventory_repository.add_item(...)
```

Migration phải có version.

Không xóa dữ liệu người chơi một cách im lặng.

---

# 19. Testing

Ưu tiên:

```text
Unit tests
    ↓
Service tests
    ↓
Repository tests
    ↓
Integration tests
    ↓
Discord/UI smoke tests
```

Các hệ thống cần test mạnh:

```text
breakthrough
combat
sect permissions
economy
inventory
death
market
admin
```

---

# 20. Quy tắc code bắt buộc

### Không làm

```python
engine.py = 2000 lines
```

```python
bot.py
    ├── SQL
    ├── gameplay
    ├── combat
    ├── admin
    └── UI
```

### Làm

```text
bot.py
→ routing

service
→ business logic

rules
→ formulas / restrictions

repository
→ persistence

content
→ static data

ui
→ presentation
```

---

# 21. Thứ tự triển khai

## Phase 1 — Nền móng

```text
Models
Services
Repositories
Rules
Database
UI base
Emoji
```

## Phase 2 — Player

```text
Tu luyện
Cảnh giới
Căn cơ
Đạo
Inventory
Equipment
```

## Phase 3 — Combat

```text
PvE
PvP
Status
Khắc chế
Boss
```

## Phase 4 — Tông môn

```text
Applications
Invitations
Roles
Permissions
Treasury
Missions
Facilities
```

## Phase 5 — World

```text
Zones
Monsters
Resources
Dungeon
Fate events
```

## Phase 6 — Economy

```text
NPC Shop
Crafting
Player Market
Auction
```

## Phase 7 — Reputation + Death

```text
Leaderboard
Achievements
Titles
History
Death
Consequences
```

## Phase 8 — Admin

```text
Admin GUI
Audit
Player tools
World tools
Economy tools
Database tools
```

## Phase 9 — Polish

```text
Emoji
Embeds
Buttons
Menus
Error handling
Loading states
Pagination
```

---

# 22. Production safety

Production hiện tại phải được giữ nguyên.

```text
main
 └── Railway production

v3-rework
 └── development
```

Chỉ merge khi:

```text
tests pass
shop fixed
migration safe
UI smoke test pass
```

Không commit secret.

---

# 23. Tiêu chuẩn hoàn thành v3.0

Bản v3.0 đạt yêu cầu khi:

- Code được chia module rõ ràng.
- Không còn một engine khổng lồ chứa toàn bộ logic.
- Gameplay có thể test không cần Discord.
- Tông môn có hierarchy + permission + application/invitation.
- Admin có module riêng + audit.
- Emoji custom quản lý tập trung.
- Túi tiếp tục hoạt động tốt.
- Shop mở và mua bán bình thường.
- PvE/PvP có combat core chung.
- Cơ duyên có consequence.
- Sinh tử có hậu quả.
- Kinh tế có transaction an toàn.
- Có migration rõ ràng.
- Không phá dữ liệu production.
