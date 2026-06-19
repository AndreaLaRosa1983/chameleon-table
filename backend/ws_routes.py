import asyncio
from fastapi import APIRouter, WebSocket
from backend.ws_manager import manager
from backend.state import games, game_state_to_response, advance_sequence, get_lock, disconnection_tasks
from backend.models import GamePhase
from backend.state import handle_disconnection
from backend.auth import decode_token_raw

router = APIRouter()

async def handle_disconnection(room_code: str, player_name: str):
    await asyncio.sleep(120)  # 2 minuti
    if room_code not in games:
        return
    async with get_lock(room_code):
        player = next((p for p in games[room_code].players if p.name == player_name), None)
        if player and not player.active:
            player.left = True
            active_players = sum(1 for p in games[room_code].players if p.active)
            initial_players = len(games[room_code].players)
            if active_players <= initial_players - 2:
                games[room_code].phase = GamePhase.ABORTED
            advance_sequence(room_code)
            await manager.broadcast(room_code, game_state_to_response(games[room_code]).model_dump(mode='json'))
    disconnection_tasks.pop(f"{room_code}_{player_name}", None)

@router.websocket("/ws/{room_code}")
async def websocket_endpoint(websocket: WebSocket, room_code: str, token: str):
    player_name = decode_token_raw(token)
    if player_name is None:
        await websocket.close(code=4401)
        return

    if room_code not in games:
        await websocket.close(code=4004)
        return

    # cancella timer se il player si sta riconnettendo
    task_key = f"{room_code}_{player_name}"
    if task_key in disconnection_tasks:
        disconnection_tasks[task_key].cancel()
        disconnection_tasks.pop(task_key, None)
        async with get_lock(room_code):
            player = next((p for p in games[room_code].players if p.name == player_name), None)
            if player:
                player.active = True
                advance_sequence(room_code)
                await manager.broadcast(room_code, game_state_to_response(games[room_code]).model_dump(mode='json'))

    await manager.connect(room_code, websocket)
    
    async with get_lock(room_code):
        player = next((p for p in games[room_code].players if p.name == player_name), None)
        if player and not player.active:
            player.active = True
            advance_sequence(room_code)
            await manager.broadcast(room_code, game_state_to_response(games[room_code]).model_dump(mode='json'))

    try:
        await websocket.send_json(game_state_to_response(games[room_code]).model_dump(mode='json'))
        while True:
            await websocket.receive_text()
    except Exception:
            async with get_lock(room_code):
                player = next((p for p in games[room_code].players if p.name == player_name), None)
                if player and not player.left:
                    player.active = False
                    advance_sequence(room_code)
                    await manager.broadcast(room_code, game_state_to_response(games[room_code]).model_dump(mode='json'))
                    task = asyncio.create_task(handle_disconnection(room_code, player_name))
                    disconnection_tasks[task_key] = task
    finally:
        await manager.disconnect(room_code, websocket)