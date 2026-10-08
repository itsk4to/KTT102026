from game.repositories.heavenly_dao_repository import HeavenlyDaoRepository


class HeavenlyDaoService:
    def __init__(self, players, audit, repository: HeavenlyDaoRepository | None = None):
        self.players = players
        self.audit = audit
        if repository is None:
            raise ValueError("HeavenlyDaoRepository must be injected by the engine.")
        self.repo = repository

    def list_rules(self, actor_id: str):
        return self.repo.list_all()

    def set_rule(self, actor_id: str, key: str, text: str, enabled: bool = True):
        key = key.strip()[:64]
        text = text.strip()[:1000]
        self.repo.upsert(key, text, enabled, actor_id)
        self.audit.log(actor_id, "heavenly_rule_set", key, f"enabled={enabled}")
        return {"key": key, "text": text, "enabled": enabled}
