# Kato Tu Tiên — Architecture Tree (v3.8.5)

```text
kato-tutien/
├── bot.py / config.py / VERSION.txt
├── docs/
│   ├── CONTENT_TREE.md      ← cập nhật content theo mục
│   ├── ITEM_DESIGN.md       ← nguyên tắc vật phẩm có chủ đích
│   └── …
├── game/
│   ├── content/
│   │   ├── items/           ← vật phẩm (tách module)
│   │   │   ├── _schema.py
│   │   │   ├── pills.py
│   │   │   ├── talismans.py
│   │   │   ├── equipment.py
│   │   │   ├── techniques.py
│   │   │   └── combat_items.py
│   │   ├── breakthrough/    ← role item đột phá / tra cứu
│   │   ├── realms.py zones.py monsters.py events.py …
│   │   └── techniques.py    ← STATUS_EFFECTS / GACHA (combat system)
│   ├── rules/               ← pure formulas (breakthrough_chance, …)
│   ├── services/            ← use-cases
│   ├── repositories/ models/ database/
│   └── moderation/ economy/ security/
└── ui/                      ← Discord presentation
```

Cập nhật từng mục:
- Đan / bùa / trang bị / công pháp → `game/content/items/<module>.py`
- Tỉ lệ đột phá → `game/rules/cultivation_rules.py`
- Flow đột phá → `game/services/cultivation_service.py` + `breakthrough_service.py`
