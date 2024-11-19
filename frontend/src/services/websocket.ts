type GameState = {
    players: {
      [key: string]: {
        color: string;
        chips: Array<{ color: string; owner: string }>;
        modelType: string;
        defeated: boolean;
      };
    };
    piles: Array<Array<{ color: string; owner: string }>>;
    currentTurn: string;
    defeatedPlayers: string[];
  };
  
  type WebSocketCallback = (gameState: GameState) => void;
  
  class GameWebSocket {
    private ws: WebSocket | null = null;
    private callbacks: WebSocketCallback[] = [];
  
    connect() {
      this.ws = new WebSocket('ws://localhost:8000/ws');
  
      this.ws.onopen = () => {
        console.log('Connected to game server');
      };
  
      this.ws.onmessage = (event) => {
        const gameState: GameState = JSON.parse(event.data);
        this.notifyCallbacks(gameState);
      };
  
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
  
      this.ws.onclose = () => {
        console.log('Disconnected from game server');
        // Attempt to reconnect after 5 seconds
        setTimeout(() => this.connect(), 5000);
      };
    }
  
    startGame() {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'start_game' }));
      }
    }
  
    requestGameState() {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'get_state' }));
      }
    }
  
    subscribe(callback: WebSocketCallback) {
      this.callbacks.push(callback);
      return () => {
        this.callbacks = this.callbacks.filter(cb => cb !== callback);
      };
    }
  
    private notifyCallbacks(gameState: GameState) {
      this.callbacks.forEach(callback => callback(gameState));
    }
  
    disconnect() {
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
    }
  }
  
  export const gameWebSocket = new GameWebSocket();
  export type { GameState };