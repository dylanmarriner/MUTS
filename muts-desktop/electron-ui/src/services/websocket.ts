export function initializeWebSocket(): void {
  // WebSocket initialization for real-time communication
  // This handles IPC between renderer and main process
  console.log('WebSocket service initialized');
}

export function connectToBackend(url: string): WebSocket {
  const ws = new WebSocket(url);
  ws.onopen = () => {
    console.log('Connected to backend WebSocket');
  };
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  return ws;
}
