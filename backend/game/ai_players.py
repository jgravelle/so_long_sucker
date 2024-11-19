import os
import json
import re
from typing import Dict
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from .models import PlayerColor, GameState

class AIPlayer:
    def __init__(self, color: PlayerColor, model_type: str):
        self.color = color
        self.chips = []
        self.model_type = model_type
        self.defeated = False

    def _create_prompt(self, game_state: GameState) -> str:
        return f"""You are playing a game of So Long Sucker as the {self.color.value} player.

Rules:
1. On your turn, you must either play a chip onto a pile or transfer a chip to another player
2. You can play any chip you own (your color or prisoners)
3. When chips of the same color are on top of a pile, they are captured by that color's player
4. When all four colors are in a pile, the player whose chip is deepest gets the next move

Current Game State:
Your chips: {[c.color.value for c in self.chips]}
Piles in play: {[[c.color.value for c in pile] for pile in game_state.piles]}
Defeated players: {[p.value for p in game_state.defeated_players]}

Provide your move decision in this exact format:
{{
    "action": "play",     // or "transfer"
    "chip": "[color]",    // color of chip to play/transfer (red, blue, green, or yellow)
    "target": "[number or color]",   // pile number (0-9) for play, or player color for transfer
    "reasoning": "[brief explanation]"
}}

Respond ONLY with a valid JSON object, no other text."""

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON object from text, handling common formatting issues."""
        try:
            # Try to find JSON-like structure
            json_match = re.search(r'\{[^{}]*\}', text)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(text)
        except Exception as e:
            print(f"JSON extraction failed: {e}")
            return self._format_safe_move()

    def _format_safe_move(self) -> Dict:
        """Generate a safe default move when error occurs."""
        return {
            "action": "play",
            "chip": self.color.value,
            "target": "0",
            "reasoning": "Error occurred, making safe move"
        }

    def _validate_move(self, move: Dict) -> Dict:
        """Validate and fix move format if needed."""
        try:
            # Ensure all required fields exist
            required_fields = {"action", "chip", "target", "reasoning"}
            if not all(field in move for field in required_fields):
                return self._format_safe_move()

            # Validate action
            if move["action"] not in ["play", "transfer"]:
                move["action"] = "play"

            # Validate chip color
            valid_colors = {"red", "blue", "green", "yellow"}
            if move["chip"] not in valid_colors:
                move["chip"] = self.color.value

            # Validate target
            if move["action"] == "play":
                try:
                    # Ensure target is a valid pile number
                    pile_num = int(str(move["target"]))
                    move["target"] = str(min(max(0, pile_num), 9))
                except (ValueError, TypeError):
                    move["target"] = "0"
            elif move["target"] not in valid_colors:
                move["target"] = "0"

            return move
        except Exception as e:
            print(f"Move validation failed: {e}")
            return self._format_safe_move()

class GPTPlayer(AIPlayer):
    def __init__(self, color: PlayerColor):
        super().__init__(color, "gpt-4")
        self.client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    async def make_decision(self, game_state: GameState) -> Dict:
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{
                    "role": "system",
                    "content": "You are an AI playing So Long Sucker. Provide moves in the specified JSON format."
                }, {
                    "role": "user",
                    "content": self._create_prompt(game_state)
                }],
                temperature=0.7
            )
            move = self._extract_json(response.choices[0].message.content)
            return self._validate_move(move)
        except Exception as e:
            print(f"Error during {self.color}'s turn: {e}")
            return self._format_safe_move()

class ClaudePlayer(AIPlayer):
    def __init__(self, color: PlayerColor):
        super().__init__(color, "claude-3.5-sonnet")
        self.client = AsyncAnthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    async def make_decision(self, game_state: GameState) -> Dict:
        try:
            response = await self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": self._create_prompt(game_state)
                }],
                system="You are an AI playing So Long Sucker. Respond only with a JSON object containing your move."
            )
            move = self._extract_json(response.content[0].text)
            return self._validate_move(move)
        except Exception as e:
            print(f"Error during {self.color}'s turn: {e}")
            return self._format_safe_move()

class LocalPlayer(AIPlayer):
    def __init__(self, color: PlayerColor, model_name: str):
        super().__init__(color, model_name)
        self.model_name = model_name
        self.client = AsyncOpenAI(
            base_url="http://127.0.0.1:1234/v1",
            api_key="not-needed"
        )

    async def make_decision(self, game_state: GameState) -> Dict:
        try:
            prompt = f"""System: You are an AI playing So Long Sucker.
User: {self._create_prompt(game_state)}
Assistant: Here is my move in JSON format:"""

            response = await self.client.completions.create(
                model=self.model_name,
                prompt=prompt,
                max_tokens=500,
                temperature=0.7,
                stop=["User:", "System:", "Human:"]
            )
            
            move = self._extract_json(response.choices[0].text)
            return self._validate_move(move)
            
        except Exception as e:
            print(f"Error with local model {self.model_name}: {e}")
            return self._format_safe_move()