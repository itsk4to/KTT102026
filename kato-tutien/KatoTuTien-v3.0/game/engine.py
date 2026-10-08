"""
GameEngine facade — composes services. No Discord dependency.

Usage:
    engine.players.create(...)
    engine.cultivation.train(...)  # via cultivate
    engine.combat.attack(...)
    engine.economy.buy(...)
"""
from __future__ import annotations

import random

from game.database.connection import Database
from game.database.migrations import run_migrations
from game.repositories.player_repository import PlayerRepository
from game.repositories.inventory_repository import InventoryRepository
from game.repositories.sect_repository import SectRepository
from game.repositories.market_repository import MarketRepository
from game.repositories.audit_repository import AuditRepository
from game.services.player_service import PlayerService
from game.services.cultivation_service import CultivationService
from game.services.combat_service import CombatService
from game.services.economy_service import EconomyService
from game.services.exploration_service import ExplorationService
from game.services.sect_service import SectService
from game.services.dao_service import DaoService
from game.services.admin_service import AdminService
from game.security.admin_auth import AdminAuth
from game.services.errors import GameError


class GameEngine:
    def __init__(self, db: Database | str = "kato_tutien.db", rng: random.Random | None = None):
        if isinstance(db, str):
            db = Database(db)
        self.db = db
        run_migrations(db)
        self.rng = rng or random.Random()

        # repositories
        self._players = PlayerRepository(db)
        self._inventory = InventoryRepository(db)
        self._sects = SectRepository(db)
        self._market = MarketRepository(db)
        self._audit = AuditRepository(db)

        # services
        self.players = PlayerService(self._players, self.rng)
        self.cultivation = CultivationService(self._players, self.rng)
        self.combat = CombatService(self._players, self._inventory, self.rng)
        self.economy = EconomyService(self._players, self._inventory, self._market, self.rng)
        self.exploration = ExplorationService(self._players, self._inventory, self.combat, self.rng)
        self.sect = SectService(self._players, self._sects)
        self.dao = DaoService(self._players)
        self.admin_auth = AdminAuth()
        self.admin = AdminService(self._players, self._sects, self._audit, self.admin_auth)
        self.audit = self._audit


__all__ = ["GameEngine", "GameError"]
