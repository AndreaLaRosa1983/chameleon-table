from backend.schemas import GameStateResponse, RowResponse, PlayerResponse, CardResponse
from backend.models import GameState, GamePhase
from backend.game import current_turn as compute_current_turn
from asyncio import Lock, Task, sleep, create_task
import asyncio
from backend.ws_manager import manager

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
        ) if state.pending_card else None
    )

def advance_sequence(room_code: str):
    games[room_code].sequence_number += 1
    games[room_code].current_turn = compute_current_turn(games[room_code])
    
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