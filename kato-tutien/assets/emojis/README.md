# Emoji assets

The bot uses ordinary Unicode emoji by default for consistent rendering in all Discord contexts.

Custom server emoji are isolated in `server/emojis.json`; custom emoji strings are deliberately not embedded in Python modules.

## Enable custom server emoji

1. Confirm the emoji IDs in `server/emojis.json` belong to the server where the bot runs and the bot can access them.
2. Set `KATO_CUSTOM_EMOJI=1` in the bot environment.
3. Restart the bot.

To temporarily use regular emoji again, set `KATO_CUSTOM_EMOJI=0` (the default) and restart. Unknown or invalid custom entries automatically fall back to Unicode.

## Emoji key names

Use stable semantic keys such as `spirit_stone`, `cultivator`, `demon`, `attack`, and `shop`. UI modules should refer to `ui.emoji.EMOJI` instead of embedding custom emoji tokens.
