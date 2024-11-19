import React, { useEffect, useState } from 'react';
import GameBoard from './components/GameBoard';
import { gameWebSocket, GameState } from './services/websocket';
import { Button } from '@/components/ui/button';

export default function App() {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Connect to WebSocket when component mounts
    gameWebSocket.connect();
    const unsubscribe = gameWebSocket.subscribe((newState) => {
      setGameState(newState);
    });

    // Check connection status
    const checkConnection = setInterval(() => {
      setIsConnected(gameWebSocket !== null);
    }, 1000);

    // Cleanup on unmount
    return () => {
      unsubscribe();
      gameWebSocket.disconnect();
      clearInterval(checkConnection);
    };
  }, []);

  const handleStartGame = () => {
    gameWebSocket.startGame();
  };

  if (!isConnected) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Connecting to game server...</h1>
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">So Long Sucker - AI Battle</h1>
          {!gameState && (
            <Button onClick={handleStartGame}>
              Start Game
            </Button>
          )}
        </div>
        
        {gameState ? (
          <GameBoard gameState={gameState} />
        ) : (
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-xl font-semibold mb-4">
              Welcome to So Long Sucker - AI Battle
            </h2>
            <p className="text-gray-600 mb-6">
              Watch four AI models compete in a game of strategy and betrayal.
              Click "Start Game" to begin!
            </p>
          </div>
        )}
      </div>
    </div>
  );
}