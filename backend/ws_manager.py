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
        if room_code in self.active_connections:
            try:
                self.active_connections[room_code].remove(websocket)
            except ValueError:
                pass
            
    async def broadcast(self, room_code: str, message: dict):
        if room_code not in self.active_connections:
            return
        dead = []
        for connection in self.active_connections[room_code]:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self.active_connections[room_code].remove(connection)

manager = ConnectionManager()