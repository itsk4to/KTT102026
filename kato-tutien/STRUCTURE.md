# Kato Tu Tiên v3.4.0 — Canonical Architecture Tree

```text
KatoTuTien-v3.4.0/
├── bot.py
├── config.py
├── VERSION.txt
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── README.md
├── STRUCTURE.md
├── CHANGELOG.md
├── .env.example
├── game/
│   ├── engine.py
│   ├── models/
│   │   ├── player.py
│   │   ├── sect.py
│   │   ├── item.py
│   │   ├── combat.py
│   │   ├── world.py
│   │   └── economy.py
│   ├── services/
│   │   ├── player_service.py
│   │   ├── cultivation_service.py
│   │   ├── breakthrough_service.py
│   │   ├── dao_service.py
│   │   ├── dao_lu_service.py
│   │   ├── combat_service.py
│   │   ├── exploration_service.py
│   │   ├── fate_service.py
│   │   ├── reputation_service.py
│   │   ├── npc_service.py
│   │   ├── quest_service.py
│   │   ├── sect_service.py
│   │   ├── sect_tower_service.py
│   │   ├── economy_service.py
│   │   ├── world_service.py
│   │   ├── death_service.py
│   │   ├── heavenly_dao_service.py
│   │   ├── code_service.py
│   │   ├── admin_service.py
│   │   └── errors.py
│   ├── repositories/
│   │   ├── player_repository.py
│   │   ├── inventory_repository.py
│   │   ├── market_repository.py
│   │   ├── sect_repository.py
│   │   ├── quest_repository.py
│   │   ├── npc_repository.py
│   │   ├── world_repository.py
│   │   ├── exploration_repository.py
│   │   ├── dao_lu_repository.py
│   │   ├── code_repository.py
│   │   ├── heavenly_dao_repository.py
│   │   ├── mission_repository.py
│   │   └── audit_repository.py
│   ├── rules/
│   │   ├── cultivation_rules.py
│   │   ├── breakthrough_rules.py
│   │   ├── combat_rules.py
│   │   ├── dao_rules.py
│   │   ├── sect_rules.py
│   │   ├── economy_rules.py
│   │   └── death_rules.py
│   ├── content/
│   │   ├── realms.py
│   │   ├── dao_paths.py
│   │   ├── talents.py
│   │   ├── items.py
│   │   ├── pills.py
│   │   ├── talismans.py
│   │   ├── artifacts.py
│   │   ├── techniques.py
│   │   ├── monsters.py
│   │   ├── zones.py
│   │   ├── dungeons.py
│   │   ├── events.py
│   │   ├── quests.py
│   │   ├── npcs.py
│   │   ├── sects_content.py
│   │   ├── towers.py
│   │   └── world_events.py
│   ├── economy/
│   │   ├── currency.py
│   │   ├── crafting.py
│   │   ├── npc_shop.py
│   │   ├── player_market.py
│   │   └── auction.py
│   ├── security/
│   │   ├── permissions.py
│   │   └── admin_auth.py
│   └── database/
│       ├── connection.py
│       ├── schema.py
│       └── migrations.py
├── assets/
│   └── emojis/
│       ├── README.md
│       └── server/
│           ├── README.md
│           └── emojis.json
├── ui/
│   ├── theme/
│   │   ├── tokens.py
│   │   ├── embeds.py
│   │   ├── components.py
│   │   ├── views.py
│   │   └── README.md
│   ├── emoji.py
│   ├── colors.py
│   ├── embeds.py
│   ├── menus.py
│   ├── buttons.py
│   ├── selects.py
│   ├── commands/
│   │   ├── core.py
│   │   ├── cultivation.py
│   │   ├── exploration.py
│   │   ├── quest.py
│   │   ├── economy.py
│   │   ├── dao.py
│   │   ├── dao_lu.py
│   │   ├── sect.py
│   │   ├── admin.py
│   │   ├── context.py
│   │   └── registry.py
│   └── views/
│       ├── main_menu_view.py
│       ├── player_view.py
│       ├── cultivation_view.py
│       ├── breakthrough_view.py
│       ├── inventory_view.py
│       ├── combat_view.py
│       ├── exploration_view.py
│       ├── quest_view.py
│       ├── npc_view.py
│       ├── sect_view.py
│       ├── sect_management_view.py
│       ├── sect_member_admin_view.py
│       ├── shop_view.py
│       ├── market_view.py
│       ├── dao_view.py
│       ├── dao_lu_view.py
│       ├── world_view.py
│       ├── start_path_view.py
│       └── admin_view.py
└── tests/
    └── unit/
```

## Layer boundary

```text
Discord command/view
        ↓
Service / use-case
        ↓
Rules / pure gameplay logic
        ↓
Repository / persistence boundary
        ↓
Database
```

`game/content/` chỉ chứa dữ liệu tĩnh. `game/models/` chỉ mô tả state. `game/engine.py` chỉ compose/facade, không chứa Discord UI và không chứa SQL.

Các file `*_gui.py` cũ (`player_gui.py`, `dao_gui.py`, `npc_gui.py`, `exploration_gui.py`, `quest_gui.py`, `sect_gui.py`, `world_gui.py`, `gui_navigation.py`) chỉ còn là compatibility shims để code cũ không vỡ; code mới phải dùng file canonical trong `ui/views/`.


## UI Theme (v3.5.6)

`ui/theme/` là cây presentation riêng, nằm cạnh `ui/commands/` và `ui/views/`. Nó sở hữu design tokens, embed factory, component builders và quy ước bố cục; không chứa business logic.


## Bí Cảnh Tu Luyện (v3.5.6)

- `game/content/secret_realms.py`: bốn bí cảnh, cảnh giới yêu cầu và dải thưởng.
- `game/repositories/secret_realm_repository.py`: persistence cho chu kỳ bí cảnh.
- `game/services/secret_realm_service.py`: lựa chọn, thời gian 3 giờ, nhận thưởng một lần và rời bí cảnh.
- `ui/views/secret_realm_view.py`: GUI riêng; `.bicanh` / `.bc` và Trung Tâm cùng mở view.
- SQLite schema 14 lưu một phiên bí cảnh cho mỗi người chơi; migration không xóa dữ liệu cũ. Sau khi bot restart, người chơi dùng lại `.bicanh` để mở view mới; tiến trình vẫn được đọc từ DB.


## Khám Phá Mở Rộng (v3.5.6)

- `game/content/events.py`: sự kiện tức thời, sự kiện lựa chọn và rào cảnh giới/vùng.
- `game/content/monsters.py`: bestiary theo khu vực, 27 quái thường và 13 boss.
- `game/content/zones.py`: bảy vùng khám phá, bao gồm Vạn Cốt Lăng và Hư Không Cổ Giới.
- `game/services/exploration_service.py`: lọc sự kiện theo khu/cảnh giới và khởi tạo encounter phù hợp.
- `game/services/combat_service.py`: ưu tiên sinh vật bản địa và hệ số tinh anh/boss.
- `ui/views/exploration_view.py`: preview dấu vết quái/boss trước khi khám phá.
