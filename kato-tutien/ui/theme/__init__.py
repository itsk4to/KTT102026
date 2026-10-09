"""Shared presentation system for Kato Tu Tiên Discord UI.

Theme modules are presentation-only: do not put game rules or persistence here.
"""

from ui.theme.tokens import (
    BRAND_FOOTER, COLOR_ERROR, COLOR_GOLD, COLOR_INFO, COLOR_MAIN,
    COLOR_SUCCESS, COLOR_SURFACE, COLOR_WARN, DEFAULT_TIMEOUT,
)
from ui.theme.views import ThemedView

__all__ = [
    "BRAND_FOOTER", "COLOR_MAIN", "COLOR_SUCCESS", "COLOR_INFO", "COLOR_WARN",
    "COLOR_ERROR", "COLOR_GOLD", "COLOR_SURFACE", "DEFAULT_TIMEOUT", "ThemedView",
]
