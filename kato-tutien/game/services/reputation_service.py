from game.services.errors import GameError
class ReputationService:
    def __init__(self,players): self.players=players
    def adjust(self,user_id,delta):
        p=self.players.get(user_id)
        if not p: raise GameError("Ngươi chưa bước lên con đường tu hành.")
        p.reputation += int(delta); self.players.save(p); return p
    def get(self,user_id):
        p=self.players.get(user_id)
        if not p: raise GameError("Ngươi chưa bước lên con đường tu hành.")
        return p.reputation
