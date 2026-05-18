from backend.schemas import GameStateResponse
from backend.models import GameState
from asyncio import Lock


games: dict[str, GameState] = {}

room_locks: dict[str, Lock] = {}

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