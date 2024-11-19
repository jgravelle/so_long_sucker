import asyncio
import json
from fastapi import WebSocket
from game.engine import GameEngine

class GameManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.game: GameEngine = None
        self.game_task: asyncio.Task = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast_state(self):
        if not self.active_connections:
            return
            
        state_dict = self.game.state.to_dict()
        await asyncio.gather(
            *[connection.send_json(state_dict) for connection in self.active_connections]
        )

    async def run_game(self):
        self.game = GameEngine()
        
        while not self.game._check_game_over():
            current_player = self.game.state.players[self.game.state.current_turn]
            
            if not current_player.defeated:
                try:
                    move = await current_player.make_decision(self.game.state)
                    self.game.execute_move(move)
                    await self.broadcast_state()
                    await asyncio.sleep(1)  # Add delay between moves
                except Exception as e:
                    print(f"Error during {current_player.color}'s turn: {e}")
                    
            self.game.update_turn()

        winner = self.game.get_winner()
        await self.broadcast_state()
        return winner

game_manager = GameManager()

def setup_websocket(app):
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await game_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                command = json.loads(data)
                
                if command["type"] == "start_game" and not game_manager.game_task:
                    game_manager.game_task = asyncio.create_task(game_manager.run_game())
                    
                elif command["type"] == "get_state" and game_manager.game:
                    await websocket.send_json(game_manager.game.state.to_dict())
                    
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            game_manager.disconnect(websocket)