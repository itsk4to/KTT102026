# Emoji assets

The bot uses the configured server custom emoji by default, with Unicode fallbacks when custom emoji are disabled or unavailable.

Custom server emoji are isolated in `server/emojis.json`; custom emoji strings are deliberately not embedded in Python modules.

## Configure custom server emoji

1. Confirm the emoji IDs in `server/emojis.json` belong to the server where the bot runs and the bot can access them.
2. Custom emojis are enabled by default; set `KATO_CUSTOM_EMOJI=1` explicitly if your host overrides the setting.
3. Restart the bot.

To temporarily use regular emoji again, set `KATO_CUSTOM_EMOJI=0` (the opt-out setting) and restart. Unknown or invalid custom entries automatically fall back to Unicode.

## Emoji key names

Use stable semantic keys such as `spirit_stone`, `cultivator`, `demon`, `attack`, and `shop`. UI modules should refer to `ui.emoji.EMOJI` instead of embedding custom emoji tokens.
