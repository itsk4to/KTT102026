# Thiết kế vật phẩm có chủ đích

| Role | File | Mục đích |
|------|------|----------|
| cultivation | pills.py | Lấp tu vi trước đột phá (3 bậc) |
| heal | pills.py / combat_items.py | Hồi HP |
| stat_root/insight/luck/fate/mind | pills + talismans | +chỉ số gốc vĩnh viễn |
| breakthrough | pills + talismans | +% đột phá (UI .dotpha) |
| thunder_guard | pills + talismans + một số artifact | Kháng Cửu Lôi |
| combat_weapon/armor/artifact/accessory | equipment.py | Chiến đấu |
| technique | techniques.py | Skill + chỉ số khi học |

Nguyên tắc: **một item → một việc chính**.
