from __future__ import annotations
import time

class HeavenlyDaoService:
    def __init__(self, players, audit):
        self.players = players
        self.audit = audit

    def list_rules(self, actor_id: str):
        rows = self.players.db.fetchall("SELECT * FROM heavenly_rules ORDER BY rule_key")
        return [dict(r) for r in rows]

    def set_rule(self, actor_id: str, key: str, text: str, enabled: bool = True):
        key = key.strip()[:64]
        text = text.strip()[:1000]
        self.players.db.execute(
            "INSERT OR REPLACE INTO heavenly_rules(rule_key,rule_text,enabled,updated_by,updated_at) VALUES(?,?,?,?,?)",
            (key, text, 1 if enabled else 0, actor_id, int(time.time())),
        )
        self.audit.log(actor_id, "heavenly_rule_set", key, f"enabled={enabled}")
        return {"key": key, "text": text, "enabled": enabled}
