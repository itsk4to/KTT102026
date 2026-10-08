from game.rules.death_rules import defeat_penalty, apply_injury_cap
class DeathService:
    def __init__(self,players): self.players=players
    def apply_defeat(self,user_id):
        p=self.players.get(user_id); pen=defeat_penalty(p.realm_index); p.injury=apply_injury_cap(p.injury+pen["injury"]); p.cultivation=max(0,p.cultivation-int(p.cultivation*pen["cultivation_loss_pct"])); self.players.save(p); return {"player":p,"penalty":pen}
