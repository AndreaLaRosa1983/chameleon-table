from backend.schemas import GameStateResponse
from backend.models import GameState
from asyncio import Lock, Task
from asyncio import sleep, create_task, Task
from backend.ws_manager import manager
from backend.models import GamePhase

games: dict[str, GameState] = {}

room_locks: dict[str, Lock] = {}

disconnection_tasks: dict[str, Task] = {}

def get_lock(room_code: str) -> Lock:
    if room_code not in room_locks:
        room_locks[room_code] = Lock()
    return room_locks[room_code]


def game_state_to_response(state) -> GameStateResponse:
    return GameStateResponse(
        room_code=state.room_code,
        rows=[],
        players=[],
        turn_order=state.turn_order,
        current_turn=state.current_turn,
        last_round=state.last_round,
        phase=state.phase,
        round_starter=state.round_starter,
        last_row_taker=state.last_row_taker,
        observers=state.observers,
        min_players=state.min_players,
        sequence_number=state.sequence_number
    )

def advance_sequence(room_code: str):
    games[room_code].sequence_number += 1
    
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