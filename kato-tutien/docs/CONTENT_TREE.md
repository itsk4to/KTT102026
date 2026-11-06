# Content tree — cập nhật từng mục

```
game/content/
  items/                 ← toàn bộ vật phẩm
    _schema.py           ← rarity, shop order, role tags
    pills.py             ← đan dược
    talismans.py         ← bùa chú
    equipment.py         ← trang bị (weapon/armor/artifact/accessory)
    techniques.py        ← công pháp
    combat_items.py      ← vật phẩm trong trận
    __init__.py          ← aggregate → ITEMS
  breakthrough/          ← vai trò item đột phá / tra cứu
  realms.py              ← cảnh giới
  zones.py               ← khu vực khám phá
  monsters.py            ← quái / boss
  events.py              ← sự kiện khám phá
  quests.py / recurring_missions.py
  sects_content.py / towers.py / secret_realms.py
  dao_paths.py / talents.py
  techniques.py          ← STATUS_EFFECTS, GACHA (combat system, không phải item sách)
```

## Thêm vật phẩm
1. Chọn đúng file con theo vai trò (pill / talisman / equipment / …).
2. Gán `role` rõ (xem `ITEM_ROLES` trong `_schema.py`).
3. Không trộn nhiều mục đích trên một item (vd. vừa +tu vi vừa +3 chỉ số).

## Đột phá
- Tỉ lệ = 5 chỉ số gốc + dao_stage + foundation item + pity − injury.
- `breakthrough_bonus` chỉ có hiệu lực trong UI `.dotpha`.
- `thunder_resistance` chỉ có hiệu lực khi kích hoạt Cửu Lôi Kiếp.
