import random
from typing import Optional, List, Set
from .models import PlayerColor, Chip, GameState
from .ai_players import GPTPlayer, ClaudePlayer, LocalPlayer

class GameEngine:
    def __init__(self):
        self.state = GameState(
            players={
                PlayerColor.RED: GPTPlayer(PlayerColor.RED),
                PlayerColor.BLUE: ClaudePlayer(PlayerColor.BLUE),
                PlayerColor.GREEN: LocalPlayer(PlayerColor.GREEN, "llama-3.2-3b-instruct"),
                PlayerColor.YELLOW: LocalPlayer(PlayerColor.YELLOW, "qwen2-0.5b-instruct")
            },
            playing_area=[],
            defeated_players=[],
            current_turn=random.choice(list(PlayerColor)),  # Random first player
            piles=[]
        )
        self.removed_chips: Set[Chip] = set()  # Track chips removed from game
        self.initialize_game()

    def initialize_game(self):
        """Give each player their initial 7 chips."""
        for player in self.state.players.values():
            player.chips = [Chip(player.color, player.color) for _ in range(7)]

    def _check_captures(self, pile_index: int) -> Optional[PlayerColor]:
        """Check for captures in a pile and handle them. Returns the next player to move."""
        pile = self.state.piles[pile_index]
        if len(pile) < 2:
            return None

        # Check top two chips
        top_two = pile[-2:]
        if top_two[0].color == top_two[1].color:
            capturing_color = top_two[0].color
            
            # Remove one chip from game
            self.removed_chips.add(pile.pop())
            
            # Captured chips go to the capturing player
            captured_chips = pile.pop()  # Remove second chip
            
            # If capturing player is defeated, the capture rebounds
            if capturing_color in self.state.defeated_players:
                return self.state.current_turn
            
            # Give captured chips to capturing player
            capturing_player = self.state.players[capturing_color]
            capturing_player.chips.append(captured_chips)
            
            return capturing_color  # Capturing player gets next move
            
        return None

    def _check_all_colors_in_pile(self, pile: List[Chip]) -> Optional[PlayerColor]:
        """Check if all colors are in pile and return deepest player if so."""
        colors_in_pile = {chip.color for chip in pile}
        if len(colors_in_pile) == 4:
            # Find the first chip from bottom that belongs to a non-defeated player
            for chip in pile:
                if chip.color not in self.state.defeated_players:
                    return chip.color
        return None

    def _get_missing_colors(self, pile: List[Chip]) -> Set[PlayerColor]:
        """Get colors not present in the pile."""
        colors_in_pile = {chip.color for chip in pile}
        return set(PlayerColor) - colors_in_pile

    def _can_player_move(self, player: 'AIPlayer') -> bool:
        """Check if a player has any legal moves available."""
        return len(player.chips) > 0

    def execute_move(self, move: dict) -> bool:
        """Execute a player's move and handle all consequences."""
        current_player = self.state.players[self.state.current_turn]
        
        if current_player.defeated:
            return False
            
        try:
            if move["action"] == "play":
                # Find the chip to play
                chip_color = PlayerColor(move["chip"])
                chip = next((c for c in current_player.chips if c.color == chip_color), None)
                
                if not chip:
                    return False
                    
                # Get or create target pile
                target_pile = int(move["target"])
                while len(self.state.piles) <= target_pile:
                    self.state.piles.append([])
                
                # Play the chip
                self.state.piles[target_pile].append(chip)
                current_player.chips.remove(chip)
                
                # Check for captures
                next_player = self._check_captures(target_pile)
                if next_player:
                    self.state.current_turn = next_player
                    return True
                
                # Check for all colors
                pile = self.state.piles[target_pile]
                next_player = self._check_all_colors_in_pile(pile)
                if next_player:
                    self.state.current_turn = next_player
                    return True
                
                # Get missing colors and valid next players
                missing_colors = self._get_missing_colors(pile)
                valid_next_players = [
                    color for color in missing_colors 
                    if color not in self.state.defeated_players
                ]
                
                if valid_next_players:
                    # Current player chooses next player from valid options
                    # For AI, we'll just pick the first valid option
                    self.state.current_turn = valid_next_players[0]
                else:
                    # No valid next player, continue with current player
                    pass
                    
            elif move["action"] == "transfer":
                chip_color = PlayerColor(move["chip"])
                target_player = PlayerColor(move["target"])
                
                chip = next((c for c in current_player.chips if c.color == chip_color), None)
                if not chip or target_player == current_player.color:
                    return False
                    
                self.state.players[target_player].chips.append(chip)
                current_player.chips.remove(chip)
            
            return True
            
        except Exception as e:
            print(f"Error executing move: {e}")
            return False

    def update_turn(self):
        """Update turn and check for defeated players."""
        # Check if current player is defeated
        current_player = self.state.players[self.state.current_turn]
        if not self._can_player_move(current_player):
            if self.current_turn not in self.state.defeated_players:
                self.state.defeated_players.append(self.current_turn)
                current_player.defeated = True
            
            # Move returns to player who gave them the move
            # For now, we'll just move to the next non-defeated player
            self._move_to_next_player()
            return

        if not self._check_game_over():
            self._move_to_next_player()

    def _move_to_next_player(self):
        """Move to the next non-defeated player."""
        current_idx = list(PlayerColor).index(self.state.current_turn)
        next_idx = (current_idx + 1) % 4
        
        while next_idx != current_idx:
            next_color = list(PlayerColor)[next_idx]
            if next_color not in self.state.defeated_players:
                self.state.current_turn = next_color
                return
            next_idx = (next_idx + 1) % 4

    def _check_game_over(self) -> bool:
        """Check if the game is over."""
        active_players = [p for p in self.state.players.values() if not p.defeated]
        return len(active_players) <= 1

    def get_winner(self) -> Optional[PlayerColor]:
        """Get the winning player, if any."""
        active_players = [p for p in self.state.players.values() if not p.defeated]
        return active_players[0].color if len(active_players) == 1 else None