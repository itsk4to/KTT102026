# Custom server emoji map

This is the dedicated storage tree for custom Discord emoji used by Kato Tu Tiên. Keep mappings in `emojis.json`; use a semantic key and a Discord token such as `<:linhthach:123456789012345678>`.

Custom emoji are enabled by default. The central UI layer uses this map in embeds, component buttons/dropdowns and relevant legacy content. The bot continues to show regular Unicode emoji for icons without a suitable mapping, and all mapped icons fall back to Unicode when `KATO_CUSTOM_EMOJI=0` is set.
