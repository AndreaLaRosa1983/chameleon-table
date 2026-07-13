import asyncio
import json
from fastapi import APIRouter, WebSocket
from backend.ws_manager import manager
from backend.state import game_state_to_response, advance_sequence, get_lock, disconnection_tasks, handle_disconnection
from backend.models import GamePhase
from backend.auth import decode_token_raw
from backend.redis_store import get_game, set_game, game_exists

router = APIRouter()

@router.websocket("/ws/{room_code}")
async def websocket_endpoint(websocket: WebSocket, room_code: str, token: str):
    player_name = decode_token_raw(token)
    if player_name is None:
        await websocket.close(code=4401)
        return

    if not await game_exists(room_code):
        await websocket.close(code=4004)
        return

    state = await get_game(room_code)
    is_player = any(p.name == player_name for p in state.players)
    is_observer = player_name in state.observers
    if not is_player and not is_observer:
        await websocket.close(code=4403)
        return

    task_key = f"{room_code}_{player_name}"
    if task_key in disconnection_tasks:
        disconnection_tasks[task_key].cancel()
        disconnection_tasks.pop(task_key, None)
        async with get_lock(room_code):
            state = await get_game(room_code)
            player = next((p for p in state.players if p.name == player_name), None)
            if player and not player.left:
                player.active = True
                await set_game(room_code, state)
                state = await advance_sequence(room_code)
                await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))

    await manager.connect(room_code, websocket)

    async with get_lock(room_code):
        state = await get_game(room_code)
        player = next((p for p in state.players if p.name == player_name), None)
        if player and not player.active and not player.left:
            player.active = True
            await set_game(room_code, state)
            state = await advance_sequence(room_code)
            await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))

    try:
        state = await get_game(room_code)
        await websocket.send_json(game_state_to_response(state).model_dump(mode='json'))
        while True:
            raw_message = await websocket.receive_text()
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                continue

            if message.get("type") == "ping":
                state = await get_game(room_code)
                await websocket.send_json({
                    "type": "pong",
                    "sequence_number": state.sequence_number
                })
    except Exception:
        async with get_lock(room_code):
            state = await get_game(room_code)
            player = next((p for p in state.players if p.name == player_name), None)
            if player and not player.left:
                player.active = False
                await set_game(room_code, state)
                state = await advance_sequence(room_code)
                await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))
                task = asyncio.create_task(handle_disconnection(room_code, player_name))
                disconnection_tasks[task_key] = task
    finally:
        await manager.disconnect(room_code, websocket)