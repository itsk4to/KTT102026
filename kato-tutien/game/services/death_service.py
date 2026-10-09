from game.rules.death_rules import defeat_penalty, apply_injury_cap
from game.services.errors import GameError


class DeathService:
    def __init__(self, players):
        self.players = players

    def apply_defeat(self, user_id: str):
        player = self.players.get(user_id)
        if player is None:
            raise GameError("Ngươi chưa bước lên con đường tu hành.")
        penalty = defeat_penalty(player.realm_index)
        player.injury = apply_injury_cap(player.injury + penalty["injury"])
        cultivation_loss = int(player.cultivation * penalty["cultivation_loss_pct"])
        stones_loss = min(
            player.spirit_stones,
            int(player.spirit_stones * penalty.get("stones_loss_pct", 0.0)),
        )
        player.cultivation = max(0, player.cultivation - cultivation_loss)
        player.spirit_stones = max(0, player.spirit_stones - stones_loss)
        self.players.save(player)
        return {"player": player, "penalty": penalty,
                "cultivation_loss": cultivation_loss, "stones_loss": stones_loss}
