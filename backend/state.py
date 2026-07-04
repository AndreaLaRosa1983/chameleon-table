from backend.schemas import GameStateResponse, RowResponse, PlayerResponse, CardResponse
from backend.models import GameState, GamePhase
from backend.game import current_turn as compute_current_turn
from asyncio import Lock, Task
import asyncio
from backend.ws_manager import manager
import time   

room_locks: dict[str, Lock] = {}
disconnection_tasks: dict[str, Task] = {}
inactivity_tasks: dict[str, Task] = {}  

INACTIVITY_TIMEOUT = 60   #lower this for a fastest play or improve for a longest play

def get_lock(room_code: str) -> Lock:
    if room_code not in room_locks:
        room_locks[room_code] = Lock()
    return room_locks[room_code]

def game_state_to_response(state) -> GameStateResponse:
    return GameStateResponse(
        room_code=state.room_code,
        rows=[
            RowResponse(
                cards=[CardResponse(card_type=c.card_type, color=c.color) for c in row.cards],
                taken_by=row.taken_by,
                max_cards=row.max_cards
            )
            for row in state.rows
        ],
        players=[
            PlayerResponse(
                name=p.name,
                cards=[CardResponse(card_type=c.card_type, color=c.color) for c in p.cards],
                jokers=[CardResponse(card_type=c.card_type, color=c.color) for c in p.jokers],
                passed=p.passed,
                active=p.active
            )
            for p in state.players
        ],
        turn_order=state.turn_order,
        current_turn=state.current_turn,
        last_round=state.last_round,
        phase=state.phase,
        round_starter=state.round_starter,
        last_row_taker=state.last_row_taker,
        observers=state.observers,
        min_players=state.min_players,
        sequence_number=state.sequence_number,
        deck_count=len(state.deck),
        pending_card=CardResponse(
            card_type=state.pending_card.card_type,
            color=state.pending_card.color
        ) if state.pending_card else None,
        inactivity_timeout=INACTIVITY_TIMEOUT,
        turn_started_at=state.turn_started_at
    )

async def handle_inactivity(room_code: str, player_name: str):
    from backend.redis_store import get_game, set_game, game_exists
    await asyncio.sleep(INACTIVITY_TIMEOUT)
    if not await game_exists(room_code):
        return
    async with get_lock(room_code):
        state = await get_game(room_code)
        if state.phase != GamePhase.PLAYING:
            return
        if state.current_turn != player_name:
            return
        player = next((p for p in state.players if p.name == player_name), None)
        if player and player.active:
            player.active = False
            await set_game(room_code, state)

            inactivity_tasks.pop(f"{room_code}_{player_name}", None)

            state = await advance_sequence(room_code)
            await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))

            task = asyncio.create_task(handle_disconnection(room_code, player_name))
            disconnection_tasks[f"{room_code}_{player_name}"] = task

async def reset_inactivity_timer(room_code: str, player_name: str):
    
    task_key = f"{room_code}_{player_name}"
    if task_key in inactivity_tasks:
        inactivity_tasks[task_key].cancel()
        inactivity_tasks.pop(task_key, None)

def start_inactivity_timer(room_code: str, player_name: str):
    task_key = f"{room_code}_{player_name}"
    print(f"[INACTIVITY] Timer started for {player_name} in room {room_code}")
    task = asyncio.create_task(handle_inactivity(room_code, player_name))
    inactivity_tasks[task_key] = task

async def advance_sequence(room_code: str):
    from backend.redis_store import get_game, set_game
    state = await get_game(room_code)

    if state.phase == GamePhase.PLAYING and state.current_turn:
        await reset_inactivity_timer(room_code, state.current_turn)
    
    state.sequence_number += 1
    state.current_turn = compute_current_turn(state)
    state.turn_started_at = time.time() if state.current_turn else None
    await set_game(room_code, state)
    
    if state.phase == GamePhase.PLAYING and state.current_turn:
        print(f"[INACTIVITY] Starting timer for {state.current_turn} in room {room_code}") 
        start_inactivity_timer(room_code, state.current_turn)
    
    return state

async def handle_disconnection(room_code: str, player_name: str):
    from backend.redis_store import get_game, set_game, game_exists
    await asyncio.sleep(INACTIVITY_TIMEOUT)
    if not await game_exists(room_code):
        return
    async with get_lock(room_code):
        state = await get_game(room_code)
        player = next((p for p in state.players if p.name == player_name), None)
        if player and not player.active:
            player.left = True
            active_players = sum(1 for p in state.players if p.active)
            if active_players < 2:
                state.phase = GamePhase.ABORTED
            await set_game(room_code, state)
            state = await advance_sequence(room_code)
            await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))
    disconnection_tasks.pop(f"{room_code}_{player_name}", None)
