from __future__ import annotations  # This enables forward references
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .ai_players import AIPlayer

class PlayerColor(Enum):
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"

@dataclass
class Chip:
    color: PlayerColor
    owner: PlayerColor

@dataclass
class GameState:
    players: Dict[PlayerColor, AIPlayer]
    playing_area: List[Chip]
    defeated_players: List[PlayerColor]
    current_turn: PlayerColor
    piles: List[List[Chip]]
    
    def to_dict(self):
        return {
            "players": {color.value: {
                "color": color.value,
                "chips": [{"color": c.color.value, "owner": c.owner.value} for c in player.chips],
                "modelType": player.model_type,
                "defeated": player.defeated
            } for color, player in self.players.items()},
            "piles": [[{"color": c.color.value, "owner": c.owner.value} for c in pile] for pile in self.piles],
            "currentTurn": self.current_turn.value,
            "defeatedPlayers": [p.value for p in self.defeated_players]
        }