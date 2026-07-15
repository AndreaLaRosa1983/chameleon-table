from backend.schemas import GameStateResponse, RowResponse, PlayerResponse, CardResponse
from backend.models import GameState, GamePhase
from backend.game import current_turn as compute_current_turn, end_round
from backend.redis_store import game_exists, get_all_game_keys, get_game, set_game
from asyncio import Lock, Task
import asyncio
import os
from backend.ws_manager import manager
import time   

room_locks: dict[str, Lock] = {}
disconnection_tasks: dict[str, Task] = {}
inactivity_tasks: dict[str, Task] = {}  


INACTIVITY_TIMEOUT = 60       #lower this for a fastest play or improve for a longest play
GRACE_PERIOD_TIMEOUT = 120    # reconnection grace period after going inactive/disconnecting
WAITING_ROOM_TIMEOUT = 600    # abort a WATING room nobody started/cancelled within this long
CLEANUP_CHECK_INTERVAL = 60   #how often the background sweep below checks for stale rooms
REDIS_RETRY_DELAY = 2         # seconds between those retries
REDIS_HEALTHCHECK_INTERVAL = float(os.getenv("REDIS_HEALTHCHECK_INTERVAL", "5"))  # how often we ping Redis to detect a restart

def get_lock(room_code: str) -> Lock:
    if room_code not in room_locks:
        room_locks[room_code] = Lock()
    return room_locks[room_code]


def reactivate_if_needed(state, player_name: str):
    # Reactivates a player who just acted via REST and cancels their pending
    # expulsion task — an orpha task would fire at its ORIGINAL deadline
    # during a later inactivity cycle, expelling the player early.
    player = next((p for p in state.players if p.name == player_name), None)
    if player and not player.active and not player.left:
        player.active = True
        task = disconnection_tasks.pop(f"{state.room_code}_{player_name}", None)
        if task:
            task.cancel()


def hard_cleanup_room_memory(room_code: str, exclude_current_task: bool = False):
    # Event-driven RAM cleanup: call AFTER the room lock is released, once a
    # room reaches a terminal state (ABORTED/FINISHED). Frees the room lock and
    # cancels any lingering inactivity/disconnection tasks. Touches RAM only —
    # never Redis/Postgres — so game data and /scores stay intact.
    # exclude_current_task=True when called from inside one of those tasks, so
    # it never cancels the task running it (self-cancel guard).
    room_locks.pop(room_code, None)
    prefix = f"{room_code}_"
    current = asyncio.current_task() if exclude_current_task else None
    for task_dict in (inactivity_tasks, disconnection_tasks):
        for key in list(task_dict.keys()):
            if key.startswith(prefix):
                task = task_dict.pop(key, None)
                if task and task is not current:
                    task.cancel()


async def _room_exists_with_retry(room_code: str) -> bool:
    # Retries indefinitely until Redis answers 
    while True:
        try:
            return await game_exists(room_code)
        except Exception as e:
            print(f"[TIMER] Redis unreachable checking {room_code}, retrying: {e}")
            await asyncio.sleep(REDIS_RETRY_DELAY)

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
    # finally always removes the key (leak-safe). The early pop before
    # advance_sequence is intentional: it stops the task from cancelling itself
    # via reset_inactivity_timer (see test_inactivity_full_cycle_does_not_self_cancel).
    try:
        await asyncio.sleep(INACTIVITY_TIMEOUT)
        if not await _room_exists_with_retry(room_code):
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
    finally:
        inactivity_tasks.pop(f"{room_code}_{player_name}", None)

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
    # finally leak-safe as above; no self-cancel risk here.
    try:
        await asyncio.sleep(GRACE_PERIOD_TIMEOUT)
        if not await _room_exists_with_retry(room_code):
            return
        async with get_lock(room_code):
            state = await get_game(room_code)
            player = next((p for p in state.players if p.name == player_name), None)
            if player and not player.active:
                player.left = True
                active_players = sum(1 for p in state.players if not p.left)
                if active_players < 2:
                    state.phase = GamePhase.ABORTED
                await set_game(room_code, state)
                state = await advance_sequence(room_code)
                await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))

                if state.phase == GamePhase.PLAYING and all(p.passed for p in state.players if not p.left):
                    state = end_round(state)
                    await set_game(room_code, state)
                    state = await advance_sequence(room_code)
                    await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))
    finally:
        disconnection_tasks.pop(f"{room_code}_{player_name}", None)


async def cleanup_stale_waiting_rooms():
    # Background sweep started once from lifespan(). Every
    # CLEANUP_CHECK_INTERVAL seconds, aborts any room still in WAITING more
    # than WAITING_ROOM_TIMEOUT since creation. Wrapped in try/except so a
    # transient Redis hiccup logs and retries next cycle instead of killing
    # this long-runing task for good.
        
    while True:
        await asyncio.sleep(CLEANUP_CHECK_INTERVAL)
        try:
            room_codes = await get_all_game_keys()
            for room_code in room_codes:
                should_cleanup = False
                async with get_lock(room_code):
                    state = await get_game(room_code)
                    if state is None:
                        continue
                    if state.phase != GamePhase.WAITING:
                        continue
                    if time.time() - state.created_at < WAITING_ROOM_TIMEOUT:
                        continue
                    state.phase = GamePhase.ABORTED
                    await set_game(room_code, state)
                    await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))
                    print(f"[CLEANUP] Aborted stale waiting room {room_code}")
                    should_cleanup = True
                # lock released here; safe to free RAM. exclude_current_task=True: we run inside the sweep task.
                if should_cleanup:
                    hard_cleanup_room_memory(room_code, exclude_current_task=True)
        except Exception as e:
            print(f"[CLEANUP] Error during sweep, will retry next cycle: {e}")


async def reload_playing_games_from_postgres():
    # On Redis return: restore playing games from Postgres over any stale
    # snapshot. Pure restore — no inactive marking, no seq bump.
    from backend.database import load_active_games
    games = await load_active_games()
    for state in games:
        await set_game(state.room_code, state)
        print(f"[RECOVERY] Reloaded room {state.room_code} from Postgres")


async def redis_recovery_watcher():
    # Pings Redis every iterval; on the down->up edge, reloads playing games
    # from Postgres so a stale RDB snapshot can't mask fresher Postgres state.
    from backend.redis_store import get_redis_client
    redis_was_down = False
    while True:
        await asyncio.sleep(REDIS_HEALTHCHECK_INTERVAL)
        try:
            client = await get_redis_client()
            await client.ping()
            if redis_was_down:
                print("[RECOVERY] Redis back, reloading from Postgres")
                await reload_playing_games_from_postgres()
                redis_was_down = False
        except Exception:
            redis_was_down = True
