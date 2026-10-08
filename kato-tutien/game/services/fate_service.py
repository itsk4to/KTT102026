from game.services.errors import GameError
class FateService:
    def __init__(self,players): self.players=players
    def adjust(self,user_id,delta):
        p=self.players.get(user_id)
        if not p: raise GameError("Ngươi chưa bước lên con đường tu hành.")
        p.fate=max(0,min(100,p.fate+int(delta))); self.players.save(p); return p
