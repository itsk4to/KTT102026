from __future__ import annotations
import secrets
from game.repositories.code_repository import CodeRepository
from game.services.errors import GameError
from game.content.items import ITEMS

class CodeService:
    def __init__(self, players, audit, repository: CodeRepository | None = None):
        self.players = players
        self.audit = audit
        if repository is None:
            raise ValueError("CodeRepository must be injected by the engine.")
        self.repo = repository

    def create(self, actor_id: str, code: str | None, stones: int, item_id: str | None, qty: int, max_uses: int):
        code = (code or "KATO-" + secrets.token_hex(4)).upper().strip()
        item_id = (item_id or "").strip().lower() or None
        if not code or len(code) > 32 or stones < 0 or qty < 0 or max_uses < 1:
            raise GameError("Thông số mật lệnh không hợp lệ.")
        if item_id and item_id not in ITEMS:
            raise GameError(f"Không tìm thấy ID vật phẩm `{item_id}`. Dùng `.vatpham` để tra ID chính xác.")
        if item_id and qty < 1:
            raise GameError("Đã chọn vật phẩm thì số lượng phải ít nhất là 1.")
        if not item_id and qty > 0:
            raise GameError("Đã nhập số lượng vật phẩm nhưng chưa có ID. Dùng `.vatpham` để tra ID hoặc đặt số lượng = 0.")
        if self.repo.exists(code):
            raise GameError("Mã đã tồn tại.")
        self.repo.create(code, stones, item_id or None, qty, max_uses)
        self.audit.log(actor_id, "create_redeem_code", code, f"stones={stones};item={item_id};qty={qty};max={max_uses}")
        return {"code": code, "stones": stones, "item": item_id, "qty": qty, "max_uses": max_uses}

    def disable(self, actor_id: str, code: str) -> dict:
        code = (code or "").strip().upper()
        if not code or len(code) > 32:
            raise GameError("Mã mật lệnh không hợp lệ.")
        row = self.repo.get(code)
        if not row:
            raise GameError("Không tìm thấy Mật Lệnh.")
        if int(row.get("enabled", 1)) == 0:
            raise GameError("Mật Lệnh này đã bị vô hiệu hóa.")
        with self.players.transaction():
            if not self.repo.disable(code):
                raise GameError("Không thể vô hiệu hóa Mật Lệnh.")
            self.audit.log(actor_id, "disable_redeem_code", code)
        return {"code": code}
