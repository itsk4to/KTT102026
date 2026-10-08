from __future__ import annotations

from dataclasses import dataclass

from game.engine import GameEngine


@dataclass(frozen=True)
class CommandContext:
    engine: GameEngine
    command_specs: tuple
