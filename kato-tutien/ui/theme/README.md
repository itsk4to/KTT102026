# Kato Tu Tiên UI Theme Tree

`ui/theme/` is the presentation-only design system shared by every Discord GUI. It stays
separate from game services, rules, repositories and persistence.

- `tokens.py`: brand palette, default footer, timeout and semantic button-label roles.
- `embeds.py`: branded embed creation and safe field helpers.
- `components.py`: reusable Discord buttons and select menus.
- `views.py`: `ThemedView`, the shared base for every feature view; it normalizes destructive,
  confirmation, primary-action and navigation button styles for static and dynamic controls.

## Design rules for every screen

1. Use `ui.embeds.base_embed()` (delegates to this tree) for every embed.
2. Use shared color roles for outcome states: success, warning, error and information.
3. Keep titles concise; place progress, costs and state before flavour text when that helps a decision.
4. Keep callbacks, validation, permissions and game rules in their existing feature/service layers.
5. Every `ui/views/*.py` view inherits from `ThemedView`; no feature should reimplement visual tokens.
6. Keep the KATO footer unless a screen needs a genuinely important contextual footer.
7. Discord components are constrained to five rows and 25 options per select; paginate rather than overcrowd.

## Adding a new GUI

Create the view under `ui/views/`, inherit from `ThemedView`, use `base_embed()` for content, and
keep interactions in that feature module. Use `themed_button()` / `themed_select()` for dynamic
controls whenever that makes intent clearer. No gameplay service should import `ui/theme/`.
