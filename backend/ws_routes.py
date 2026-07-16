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
    """Per-connection lifecycle: authenticate, reactivate on reconnect, then
    serve the ping/pong loop until the socket dies.

    The pong carries the current sequence_number so a client that silently
    missed a broadcast can detect the gap and trigger a REST resync.

    Guards on `not player.left` throughout: `left` is permanent expulsion and
    must never be undone by a reconnection, unlike the temporary `active` flag.
    """
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
    # Reconnection path A: a grace period was running — cancel it before it
    # expels a player who is clearly back
    task_key = f"{room_code}_{player_name}"
    if task_key in disconnection_tasks:
        disconnection_tasks[task_key].cancel()
        disconnection_tasks.pop(task_key, None)
        # Reconnection path B: no pending task (e.g. inactivity timeout fired but
        # the grace period already completed its own cleanup). No-op if path A
        # already reactivated — the `not player.active` guard covers that.
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
        # Explicit initial state: broadcasts above may have fired before this
        # socket joined the room, so we always push current state on connect.
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