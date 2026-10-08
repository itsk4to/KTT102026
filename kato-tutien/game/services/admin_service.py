from __future__ import annotations

from game.content.realms import REALMS
from game.models.player import Player
from game.repositories.audit_repository import AuditRepository
from game.repositories.player_repository import PlayerRepository
from game.repositories.sect_repository import SectRepository
from game.security.admin_auth import AdminAuth
from game.security.permissions import is_owner
from game.services.errors import GameError


class AdminService:
    """Authoritative admin operations with audit logging.

    The Discord layer handles presentation. This service owns the actual
    mutations so future admin UIs can reuse the same safe operations.
    """

    def __init__(self, players: PlayerRepository, sects: SectRepository, audit: AuditRepository, auth: AdminAuth):
        self.players = players
        self.sects = sects
        self.audit = audit
        self.auth = auth

    def ensure_access(self, actor_id: str) -> None:
        if not (is_owner(actor_id) or self.auth.has_session(actor_id) or self.audit.is_admin(actor_id)):
            raise GameError("Không có quyền quản trị.")

    def authorize_session(self, actor_id: str, password: str) -> bool:
        if not self.auth.verify_password(password):
            self.auth.record_failure(actor_id)
            return False
        self.auth.grant(actor_id)
        self.audit.log(actor_id, "admin_login")
        return True

    def overview(self, actor_id: str) -> dict:
        self.ensure_access(actor_id)
        return {
            "players": self.players.count(),
            "sects": self.sects.count(),
            "audit": self.audit.recent(10),
        }

    def find_player(self, actor_id: str, target_id: str) -> Player:
        self.ensure_access(actor_id)
        player = self.players.get(target_id)
        if not player:
            raise GameError("Không tìm thấy người chơi.")
        return player

    def grant_stones(self, actor_id: str, target_id: str, amount: int) -> Player:
        self.ensure_access(actor_id)
        if amount < 1:
            raise GameError("Số lượng phải > 0.")
        player = self.players.get(target_id)
        if not player:
            raise GameError("Không tìm thấy người chơi.")
        with self.players.db.transaction():
            player.spirit_stones += amount
            self.players.save(player)
            self.audit.log(actor_id, "grant_stones", target_id, f"amount={amount}")
        return player

    def set_realm(self, actor_id: str, target_id: str, realm_index: int, realm_layer: int) -> Player:
        self.ensure_access(actor_id)
        if not (0 <= realm_index < len(REALMS)):
            raise GameError("Cảnh giới không hợp lệ.")
        max_layer = REALMS[realm_index][1]
        if not (1 <= realm_layer <= max_layer):
            raise GameError(f"Tầng cảnh giới phải từ 1 đến {max_layer}.")
        player = self.players.get(target_id)
        if not player:
            raise GameError("Không tìm thấy người chơi.")
        with self.players.db.transaction():
            player.realm_index = realm_index
            player.realm_layer = realm_layer
            player.cultivation = 0
            self.players.save(player)
            self.players.add_history(target_id, "admin_realm", f"actor={actor_id} realm={realm_index}:{realm_layer}")
            self.audit.log(actor_id, "set_realm", target_id, f"realm={realm_index}:{realm_layer}")
        return player

    def recent_audit(self, actor_id: str, limit: int = 25) -> list[dict]:
        self.ensure_access(actor_id)
        return self.audit.recent(max(1, min(limit, 100)))

    def add_admin(self, actor_id: str, target_id: str) -> None:
        self.ensure_access(actor_id)
        if not is_owner(actor_id):
            raise GameError("Chỉ chủ quản mới được cấp quyền quản trị.")
        with self.players.db.transaction():
            self.audit.add_admin(target_id)
            self.audit.log(actor_id, "add_admin", target_id)

    def remove_admin(self, actor_id: str, target_id: str) -> None:
        self.ensure_access(actor_id)
        if not is_owner(actor_id):
            raise GameError("Chỉ chủ quản mới được gỡ quyền quản trị.")
        if is_owner(target_id):
            raise GameError("Không thể gỡ chủ quản bằng lệnh này.")
        with self.players.db.transaction():
            self.audit.remove_admin(target_id)
            self.audit.log(actor_id, "remove_admin", target_id)
