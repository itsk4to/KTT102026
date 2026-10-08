from __future__ import annotations
import secrets
from game.services.errors import GameError

class CodeService:
    def __init__(self, players, audit):
        self.players = players
        self.audit = audit

    def create(self, actor_id: str, code: str | None, stones: int, item_id: str | None, qty: int, max_uses: int):
        code = (code or "KATO-" + secrets.token_hex(4)).upper().strip()
        if not code or len(code) > 32 or stones < 0 or qty < 0 or max_uses < 1:
            raise GameError("Thông số mật lệnh không hợp lệ.")
        if self.players.db.fetchone("SELECT 1 FROM redeem_codes WHERE code=?", (code,)):
            raise GameError("Mã đã tồn tại.")
        self.players.db.execute(
            "INSERT INTO redeem_codes(code,reward_stones,reward_item,reward_qty,max_uses,used_count) VALUES(?,?,?,?,?,0)",
            (code, stones, item_id or None, qty, max_uses),
        )
        self.audit.log(actor_id, "create_redeem_code", code, f"stones={stones};item={item_id};qty={qty};max={max_uses}")
        return {"code": code, "stones": stones, "item": item_id, "qty": qty, "max_uses": max_uses}
