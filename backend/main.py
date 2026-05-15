from fastapi import FastAPI, HTTPException
from backend.schemas import CreateRoomRequest, CreateRoomResponse, GameStateResponse, JoinRoomRequest
from backend.schemas import JoinRoomResponse,StartRoomRequest, StartRoomResponse, RoomStateResponse
from backend.game import create_game
from backend.models import GamePhase, Player
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
    
@app.post("/rooms/{room_code}/join", response_model=JoinRoomResponse)
def join_room(room_code: str, request: JoinRoomRequest):
    if room_code not in games:
        raise HTTPException(status_code=404, detail="Room not found")
    if games[room_code].phase != GamePhase.WAITING:
        raise HTTPException(status_code=400, detail="Game already started")
    if len(games[room_code].players) >= games[room_code].max_players:
        raise HTTPException(status_code=400, detail="Room is full")
    if any(p.name == request.player_name for p in games[room_code].players):
        raise HTTPException(status_code=400, detail="Name already taken")
    games[room_code].players.append(Player(name=request.player_name))
    games[room_code].turn_order.append(request.player_name)
    return JoinRoomResponse(
        room_code=room_code,
        state=game_state_to_response(games[room_code])
    )
    
@app.post("/rooms/{room_code}/start", response_model=StartRoomResponse)
def start_room(room_code: str, request: StartRoomRequest):
    if room_code not in games:
        raise HTTPException(status_code=404, detail="Room not found")
    if games[room_code].phase != GamePhase.WAITING:
        raise HTTPException(status_code=400, detail="Game already started")
    if not any(p.name == request.player_name for p in games[room_code].players):
        raise HTTPException(status_code=403, detail="Only a player can start the game")
    if len(games[room_code].players) < 2:
        raise HTTPException(status_code=400, detail="Not enough players")
    games[room_code].phase = GamePhase.PLAYING
    return StartRoomResponse(
        room_code=room_code,
        state=game_state_to_response(games[room_code])
    )
    
@app.get("/rooms/{room_code}/state", response_model=RoomStateResponse)
def room_state(room_code: str):
    if room_code not in games:
        raise HTTPException(status_code=404, detail="Room not found")
    return RoomStateResponse(
        room_code=room_code,
        state=game_state_to_response(games[room_code])
    )