from fastapi import FastAPI, HTTPException
from backend.schemas import CreateRoomRequest, CreateRoomResponse, GameStateResponse
from backend.game import create_game
import random
import string

app = FastAPI()

games: dict={}

def generate_room_code() -> str:
    return "".join(random.choices(string.ascii_uppercase, k=4))

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
        min_players=state.min_players
    )

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/rooms", response_model=CreateRoomResponse)
def create_room(request: CreateRoomRequest):
    room_code = generate_room_code()
    while room_code in games:
        room_code = generate_room_code()
    state = create_game(room_code, [request.player_name])
    state.max_players = request.max_players
    games[room_code] = state
    return CreateRoomResponse(
        room_code=room_code,
        state=game_state_to_response(state)
    )