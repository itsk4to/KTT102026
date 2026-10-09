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
from game.repositories.quest_repository import QuestRepository
from game.repositories.world_repository import WorldRepository
from game.repositories.npc_repository import NPCRepository
from game.repositories.exploration_repository import ExplorationRepository
from game.repositories.dao_lu_repository import DaoLuRepository
from game.repositories.code_repository import CodeRepository
from game.repositories.heavenly_dao_repository import HeavenlyDaoRepository
from game.repositories.mission_repository import MissionRepository
from game.repositories.pvp_repository import PvpRepository
from game.repositories.secret_realm_repository import SecretRealmRepository
from game.services.player_service import PlayerService
from game.services.cultivation_service import CultivationService
from game.services.breakthrough_service import BreakthroughService
from game.services.fate_service import FateService
from game.services.reputation_service import ReputationService
from game.services.death_service import DeathService
from game.services.combat_service import CombatService
from game.services.economy_service import EconomyService
from game.services.exploration_service import ExplorationService
from game.services.sect_service import SectService
from game.services.dao_service import DaoService
from game.services.admin_service import AdminService
from game.services.quest_service import QuestService
from game.services.npc_service import NPCService
from game.services.world_service import WorldService
from game.services.dao_lu_service import DaoLuService
from game.services.sect_tower_service import SectTowerService
from game.services.heavenly_dao_service import HeavenlyDaoService
from game.services.pvp_service import PvpService
from game.services.secret_realm_service import SecretRealmService
from game.services.code_service import CodeService
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
        self._quests = QuestRepository(db)
        self._world = WorldRepository(db)
        self._npcs = NPCRepository(db)
        self._exploration = ExplorationRepository(db)
        self._dao_lu = DaoLuRepository(db)
        self._codes = CodeRepository(db)
        self._heavenly = HeavenlyDaoRepository(db)
        self._missions = MissionRepository(db)
        self._pvp_repo = PvpRepository(db)
        self._secret_realms = SecretRealmRepository(db)

        # services
        self.players = PlayerService(self._players, self.rng)
        self.cultivation = CultivationService(self._players, self.rng, self._inventory)
        self.breakthrough = BreakthroughService(self.cultivation, self._players, self._inventory)
        self.combat = CombatService(self._players, self._inventory, self.rng)
        # Breakthrough tribulation uses the same equipment/talent/Dao max HP as combat.
        self.cultivation.combat = self.combat
        self.pvp = PvpService(self._players, self._inventory, self.combat, self._pvp_repo, self.rng)
        self.secret_realm = SecretRealmService(self._players, self._secret_realms, self.rng)
        self.economy = EconomyService(self._players, self._inventory, self._market, self.rng, self._codes)
        self.economy.combat = self.combat
        self.quests = QuestService(self._players, self._quests, self._inventory)
        self.world = WorldService(self._players, self._world, self.rng)
        self.npc = NPCService(self._players, self.quests, self._npcs)
        self.quests.npc_service = self.npc
        self.exploration = ExplorationService(self._players, self._inventory, self.combat, self.quests, self.world, self.rng, self._exploration)
        self.sect = SectService(self._players, self._sects)
        self.sect_tower = SectTowerService(self._players, self._sects, self.rng, self._missions)
        self.cultivation.sect_tower = self.sect_tower
        self.sect.sect_tower = self.sect_tower
        self.exploration.sect_tower = self.sect_tower
        self.dao = DaoService(self._players)
        self.fate = FateService(self._players)
        self.reputation = ReputationService(self._players)
        self.death = DeathService(self._players)
        self.dao_lu = DaoLuService(self._players, self._dao_lu)
        self.heavenly_dao = HeavenlyDaoService(self._players, self._audit, self._heavenly)
        self.codes = CodeService(self._players, self._audit, self._codes)
        self.admin_auth = AdminAuth()
        self.admin = AdminService(self._players, self._sects, self._audit, self.admin_auth)
        self.audit = self._audit


__all__ = ["GameEngine", "GameError"]
