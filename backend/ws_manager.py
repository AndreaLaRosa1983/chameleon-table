from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
    
    async def connect(self, room_code: str, websocket: WebSocket):
        await websocket.accept()
        if room_code not in self.active_connections:
            self.active_connections[room_code] = []
        self.active_connections[room_code].append(websocket)
    
    async def disconnect(self, room_code: str, websocket: WebSocket):
        self.active_connections[room_code].remove(websocket)
    
    async def broadcast(self, room_code: str, message: dict):
        if room_code in self.active_connections:
            for connection in self.active_connections[room_code]:
                await connection.send_json(message)

manager = ConnectionManager()