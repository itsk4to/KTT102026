# Kato Tu Tiên v3.0.1 — Structure Map

## Muốn sửa gì → mở file nào

| Việc | File |
|------|------|
| Command routing / startup | `bot.py` |
| Command nhân vật / help | `ui/commands/core.py` |
| Command tu luyện | `ui/commands/cultivation.py` |
| Command khám phá | `ui/commands/exploration.py` |
| Shop / túi / market commands | `ui/commands/economy.py` |
| Đạo commands | `ui/commands/dao.py` |
| Tông môn commands | `ui/commands/sect.py` |
| Admin commands | `ui/commands/admin.py` |
| Damage / hit / mastery | `game/rules/combat_rules.py` |
| Tu luyện / đột phá | `game/rules/cultivation_rules.py` |
| Thuế chợ / currency rules | `game/rules/economy_rules.py` |
| Quyền tông môn | `game/rules/sect_rules.py` + `game/content/sects_content.py` |
| Logic mua / dùng / market | `game/services/economy_service.py` |
| Logic tông môn | `game/services/sect_service.py` |
| Logic admin | `game/services/admin_service.py` |
| Combat PvE | `game/services/combat_service.py` |
| Khám phá / event | `game/services/exploration_service.py` |
| Item / shop data | `game/content/items.py` |
| Monster / zone | `game/content/monsters.py`, `zones.py` |
| DB connection / transaction | `game/database/connection.py` |
| DB schema | `game/database/schema.py` |
| DB version migrations | `game/database/migrations.py` |
| Emoji | `ui/emoji.py` |
| Embed | `ui/embeds.py` |
| Shop UI | `ui/views/shop_view.py` |
| Admin UI | `ui/views/admin_view.py` |

## Dependency direction

```text
bot.py
  ↓
ui/commands + ui/views
  ↓
game/services
  ↓
game/rules
  ↓
game/repositories
  ↓
game/database
```

`game/rules/` không làm I/O.
`game/content/` không làm database.
Discord code không được chứa gameplay formula.

## Database transaction rule

Business operation có nhiều bước phải dùng:

```python
with repository.db.transaction():
    ...
```

Repositories vẫn là nơi chạy SQL; service điều phối transaction.

## Public API

```python
from game.engine import GameEngine, GameError

engine = GameEngine("kato_tutien.db")
engine.players.create(user_id, name, "tien")
engine.cultivation.cultivate(user_id)
engine.economy.buy(user_id, "tu_khi_dan", 1)
engine.combat.start_encounter(user_id)
engine.sect.create(user_id, "Tông Name")
```
