import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Brain, Cpu, Bot } from 'lucide-react';
import type { GameState } from '../services/websocket';

const PlayerIcon = ({ modelType }: { modelType: string }) => {
  switch (modelType) {
    case 'gpt-4':
      return <Brain className="w-6 h-6 text-green-600" />;
    case 'claude-3.5-sonnet':
      return <Cpu className="w-6 h-6 text-blue-600" />;
    default:
      return <Bot className="w-6 h-6 text-purple-600" />;
  }
};

type ChipColor = 'red' | 'blue' | 'green' | 'yellow';

const Chip = ({ color, size = 'md' }: { color: ChipColor; size?: 'sm' | 'md' | 'lg' }) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  };

  const colorClasses: Record<ChipColor, string> = {
    red: 'bg-red-500',
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    yellow: 'bg-yellow-500'
  };

  return (
    <div className={`rounded-full ${sizeClasses[size]} ${colorClasses[color as ChipColor]} border-2 border-gray-300`} />
  );
};

const PlayerArea = ({ 
  color,
  modelType,
  chips,
  isCurrentTurn,
  isDefeated
}: {
  color: ChipColor;
  modelType: string;
  chips: Array<{ color: ChipColor; owner: ChipColor }>;
  isCurrentTurn: boolean;
  isDefeated: boolean;
}) => {
  return (
    <div className={`flex flex-col items-center p-4 border rounded-lg ${
      isCurrentTurn ? 'bg-yellow-50 ring-2 ring-yellow-400' : 
      isDefeated ? 'bg-gray-100 opacity-60' : 'bg-gray-50'
    }`}>
      <div className="flex items-center gap-2 mb-2">
        <PlayerIcon modelType={modelType} />
        <span className="font-semibold capitalize">{color}</span>
        {isDefeated && <span className="text-red-500 text-sm">(Defeated)</span>}
      </div>
      <div className="flex gap-2 flex-wrap justify-center">
        {chips.map((chip, i) => (
          <Chip key={i} color={chip.color} />
        ))}
      </div>
    </div>
  );
};

const PlayingArea = ({ piles }: { piles: GameState['piles'] }) => {
  return (
    <div className="flex flex-wrap gap-4 p-4 bg-white rounded-lg border min-h-[200px]">
      {piles.map((pile, pileIndex) => (
        <div key={pileIndex} className="flex flex-col items-center">
          {pile.map((chip, chipIndex) => (
            <div key={chipIndex} className="relative -mt-2 first:mt-0">
              <Chip color={chip.color as ChipColor} size="lg" />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

interface GameBoardProps {
  gameState: GameState;
}

const GameBoard: React.FC<GameBoardProps> = ({ gameState }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Game Progress</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Players */}
          <div className="grid grid-cols-2 gap-4">
            {Object.entries(gameState.players).map(([color, player]) => (
              <PlayerArea
                key={color}
                color={color as ChipColor}
                modelType={player.modelType}
                chips={player.chips.map(c => ({ ...c, color: c.color as ChipColor, owner: c.owner as ChipColor }))}
                isCurrentTurn={gameState.currentTurn === color}
                isDefeated={player.defeated}
              />
            ))}
          </div>

          {/* Playing Area */}
          <PlayingArea piles={gameState.piles} />

          {/* Game Status */}
          <div className="text-center">
            <p className="text-lg font-semibold capitalize">
              Current Turn: {gameState.currentTurn}
            </p>
            {gameState.defeatedPlayers.length > 0 && (
              <p className="text-sm text-gray-600">
                Defeated: {gameState.defeatedPlayers.join(', ')}
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default GameBoard;