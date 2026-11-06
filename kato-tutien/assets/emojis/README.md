# Emoji assets

Bot mặc định dùng **Unicode emoji** (💎 🧘 ⚔️ …) — không phụ thuộc emoji server.

- Mapping hiển thị: `ui/emoji.py` (`EMOJI` dict)
- Custom Discord emoji (tùy chọn): `server/emojis.json`
- Bật custom: đặt `KATO_CUSTOM_EMOJI=1` và điền token `<:name:id>` hợp lệ vào `server/emojis.json`

UI modules nên dùng `ui.emoji.EMOJI[...]` thay vì hard-code token custom.
