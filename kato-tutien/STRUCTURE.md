# Kato Tu Tiên v3.3.2 — Structure Map

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
| NPC / nhiệm vụ | `game/services/npc_service.py`, `quest_service.py` |
| Nội dung NPC / quest | `game/content/npcs.py`, `quests.py` |
| Biến động thế giới | `game/services/world_service.py`, `game/content/world_events.py` |
| Item / shop data | `game/content/items.py` |
| Monster / zone | `game/content/monsters.py`, `zones.py` |
| DB connection / transaction | `game/database/connection.py` |
| DB schema | `game/database/schema.py` |
| DB version migrations | `game/database/migrations.py` |
| Quest persistence | `game/repositories/quest_repository.py` |
| World event persistence | `game/repositories/world_repository.py` |
| Emoji | `ui/emoji.py` |
| Embed | `ui/embeds.py` |
| Shop UI | `ui/views/shop_view.py` |
| Inventory UI | `ui/views/inventory_view.py` |
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


## Player UI policy

Player-facing interaction follows two paths:

```text
Fast commands
.tu .dp .tk .dl .info .code ...

GUI systems
.menu -> Inventory / Shop / Exploration / Quest / NPC / Sect / Dao / World
```

Source identifiers remain English. Only rendered Discord text, labels, descriptions, and buttons are Vietnamese.

Main GUI modules:
```text
ui/views/gui_navigation.py
ui/views/inventory_view.py
ui/views/exploration_gui.py
ui/views/quest_gui.py
ui/views/npc_gui.py
ui/views/sect_gui.py
ui/views/dao_gui.py
ui/views/world_gui.py
```


## v3.3.8 module boundaries

```text
game/services/
├── cultivation_service.py      # cultivation / breakthrough
├── exploration_service.py     # world exploration
├── combat_service.py          # combat rules orchestration
├── dao_lu_service.py          # partner / intimacy
├── sect_service.py            # membership / roles
├── sect_tower_service.py      # sect tower / missions / linh mach
├── heavenly_dao_service.py    # admin-defined great-dao rules
└── code_service.py            # admin redeem-code creation

ui/views/
├── gui_navigation.py          # main player hub
├── start_path_view.py         # Tiên / Ma onboarding
├── inventory_view.py          # inventory filters / multi-use
├── combat_view.py             # combat buttons + selectors
├── breakthrough_view.py       # breakthrough confirmation flow
├── dao_lu_view.py             # Dao Lu GUI
└── sect_gui.py                # sect GUI
```

Player-facing text stays Vietnamese. Source identifiers and tree boundaries stay English.
