from fastapi import APIRouter, WebSocket
from backend.ws_manager import manager
from backend.main import games, game_state_to_response

router = APIRouter()

@router.websocket("/ws/{room_code}/{player_name}")
async def websocket_endpoint(websocket: WebSocket, room_code: str, player_name: str):
    if room_code not in games:
        await websocket.close(code=4004)
        return
    await manager.connect(room_code, websocket)
    try:
        await websocket.send_json(game_state_to_response(games[room_code]).model_dump())
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        await manager.disconnect(room_code, websocket)
        
        
