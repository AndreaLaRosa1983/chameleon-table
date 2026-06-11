from fastapi import FastAPI, HTTPException, WebSocket
from backend.ws_manager import manager
from backend.state import games, game_state_to_response, advance_sequence, get_lock, handle_disconnection, disconnection_tasks
from backend.schemas import (
    CreateRoomRequest, CreateRoomResponse,
    JoinRoomRequest, JoinRoomResponse,
    StartRoomRequest, StartRoomResponse,
    RoomStateResponse, GameStateResponse,
    DrawCardRequest, DrawCardResponse,
    PlaceCardRequest, PlaceCardResponse,
    TakeRowRequest, TakeRowResponse,
    CardResponse, LeaveRoomRequest,
    LeaveRoomResponse, RoomsListResponse,
    RoomSummary, ObserveRoomRequest, ObserveRoomResponse)
from backend.game import create_game, draw_card, place_card, take_row, add_observer, end_round, create_rows, assign_initial_colors, create_deck
from backend.models import GamePhase, Player
from backend.ws_routes import router as ws_router
from backend.database import room_code_exists, init_db, load_active_games, save_game
import random
import string
from asyncio import create_task
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await init_db()
    active_games = await load_active_games()
    for state in active_games:
        state.sequence_number += 1
        for player in state.players:
            if player.active:
                player.active = False
        games[state.room_code] = state
        for player in state.players:
            if not player.left:
                task = create_task(handle_disconnection(state.room_code, player.name))
                disconnection_tasks[f"{state.room_code}_{player.name}"] = task
    yield
    # shutdown (vuoto per ora)
app = FastAPI(lifespan=lifespan)  

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)  

def generate_room_code() -> str:
    return "".join(random.choices(string.ascii_uppercase, k=6))

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/rooms", response_model=CreateRoomResponse)
async def create_room(request: CreateRoomRequest):
    room_code = generate_room_code()
    attempts = 0
    while room_code in games or await room_code_exists(room_code):
        room_code = generate_room_code()
        attempts += 1
        if attempts > 1000:
            raise HTTPException(status_code=503, detail="No room codes available")
    state = create_game(room_code, [request.player_name])
    state.max_players = request.max_players
    games[room_code] = state
    return CreateRoomResponse(
        room_code=room_code,
        state=game_state_to_response(state)
    )

@app.post("/rooms/{room_code}/join", response_model=JoinRoomResponse)
async def join_room(room_code: str, request: JoinRoomRequest):
    if room_code not in games:
        raise HTTPException(status_code=404, detail="Room not found")
    async with get_lock(room_code):
        if games[room_code].phase != GamePhase.WAITING:
            raise HTTPException(status_code=400, detail="Game already started")
        if len(games[room_code].players) >= games[room_code].max_players:
            raise HTTPException(status_code=400, detail="Room is full")
        if any(p.name == request.player_name for p in games[room_code].players):
            raise HTTPException(status_code=400, detail="Same Player Error")
        games[room_code].players.append(Player(name=request.player_name))
        games[room_code].turn_order.append(request.player_name)
        await manager.broadcast(room_code, game_state_to_response(games[room_code]).model_dump(mode='json'))
        return JoinRoomResponse(
            room_code=room_code,
            state=game_state_to_response(games[room_code])
        )

@app.post("/rooms/{room_code}/start", response_model=StartRoomResponse)
async def start_room(room_code: str, request: StartRoomRequest):
    if room_code not in games:
        raise HTTPException(status_code=404, detail="Room not found")
    async with get_lock(room_code):
        if games[room_code].phase != GamePhase.WAITING:
            raise HTTPException(status_code=400, detail="Game already started")
        if not any(p.name == request.player_name for p in games[room_code].players):
            raise HTTPException(status_code=403, detail="Only a player can start the game")
        if len(games[room_code].players) < 2:
            raise HTTPException(status_code=400, detail="Not enough players")
        games[room_code].phase = GamePhase.PLAYING
        games[room_code].rows = create_rows(len(games[room_code].players))
        assigned_colors = assign_initial_colors(games[room_code].players)
        games[room_code].deck = create_deck(len(games[room_code].players), assigned_colors)
        advance_sequence(room_code)
        await save_game(room_code, games[room_code])
        await manager.broadcast(room_code, game_state_to_response(games[room_code]).model_dump(mode='json'))
        return StartRoomResponse(
            room_code=room_code,
            state=game_state_to_response(games[room_code])
        )

@app.get("/rooms/{room_code}/state", response_model=RoomStateResponse)
async def room_state(room_code: str):
    if room_code not in games:
        raise HTTPException(status_code=404, detail="Room not found")
    return RoomStateResponse(
        room_code=room_code,
        state=game_state_to_response(games[room_code])
    )

@app.post("/rooms/{room_code}/draw", response_model=DrawCardResponse)
async def draw(room_code: str, request: DrawCardRequest):
    if room_code not in games:
        raise HTTPException(status_code=404, detail="Room not found")
    async with get_lock(room_code):
        if games[room_code].phase != GamePhase.PLAYING:
            raise HTTPException(status_code=400, detail="Game not started or ended")
        if not any(p.name == request.player_name for p in games[room_code].players):
            raise HTTPException(status_code=403, detail="Only a player can draw a card")
        if games[room_code].pending_card is not None:
            raise HTTPException(status_code=400, detail="You have a pending card to place")
        try:
            state, card = draw_card(games[room_code], request.player_name)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        state.pending_card = card
        games[room_code] = state
        advance_sequence(room_code)
        await save_game(room_code, games[room_code])
        await manager.broadcast(room_code, game_state_to_response(games[room_code]).model_dump(mode='json'))
        return DrawCardResponse(
            card=CardResponse(card_type=card.card_type, color=card.color),
            state=game_state_to_response(games[room_code])
        )

@app.post("/rooms/{room_code}/place", response_model=PlaceCardResponse)
async def place(room_code: str, request: PlaceCardRequest):
    if room_code not in games:
        raise HTTPException(status_code=404, detail="Room not found")
    async with get_lock(room_code):
        if games[room_code].phase != GamePhase.PLAYING:
            raise HTTPException(status_code=400, detail="Game not started or ended")
        if not any(p.name == request.player_name for p in games[room_code].players):
            raise HTTPException(status_code=403, detail="Only a player can place a card")
        if games[room_code].pending_card is None:
            raise HTTPException(status_code=400, detail="No pending card to place")
        try:
            card = games[room_code].pending_card
            state = place_card(games[room_code], request.player_name, request.row_index, card)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        state.pending_card = None
        games[room_code] = state
        advance_sequence(room_code)
        await save_game(room_code, games[room_code])
        await manager.broadcast(room_code, game_state_to_response(games[room_code]).model_dump(mode='json'))
        return PlaceCardResponse(
            state=game_state_to_response(games[room_code])
        )

@app.post("/rooms/{room_code}/take-row", response_model=TakeRowResponse)
async def take_row_endpoint(room_code: str, request: TakeRowRequest):
    if room_code not in games:
        raise HTTPException(status_code=404, detail="Room not found")
    async with get_lock(room_code):
        if games[room_code].phase != GamePhase.PLAYING:
            raise HTTPException(status_code=400, detail="Game not started or ended")
        if not any(p.name == request.player_name for p in games[room_code].players):
            raise HTTPException(status_code=403, detail="Only a player can take a row")
        if games[room_code].pending_card:
            raise HTTPException(status_code=400, detail="There is a pending card, can't take a row")
        try:
            state = take_row(games[room_code], request.player_name, request.row_index)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        games[room_code] = state
        advance_sequence(room_code)
        await save_game(room_code, games[room_code])
        await manager.broadcast(room_code, game_state_to_response(games[room_code]).model_dump(mode='json'))
        if all(p.passed for p in games[room_code].players if p.active):
            state = end_round(games[room_code])
            games[room_code] = state
            advance_sequence(room_code)
            await save_game(room_code, games[room_code])
            await manager.broadcast(room_code, game_state_to_response(games[room_code]).model_dump(mode='json'))
        return TakeRowResponse(
            state=game_state_to_response(games[room_code])
        )

@app.post("/rooms/{room_code}/leave", response_model=LeaveRoomResponse)
async def leave(room_code: str, request: LeaveRoomRequest):
    if room_code not in games:
        raise HTTPException(status_code=404, detail="Room not found")
    async with get_lock(room_code):
        if not any(p.name == request.player_name for p in games[room_code].players):
            raise HTTPException(status_code=403, detail="Player not in room")
        player = next(p for p in games[room_code].players if p.name == request.player_name)
        player.active = False
        player.left = True
        active_players = sum(1 for p in games[room_code].players if p.active)
        initial_players = len(games[room_code].players)
        if active_players <= initial_players - 2:
            games[room_code].phase = GamePhase.ABORTED
        games[room_code] = games[room_code]
        advance_sequence(room_code)
        await save_game(room_code, games[room_code])
        await manager.broadcast(room_code, game_state_to_response(games[room_code]).model_dump(mode='json'))
        return LeaveRoomResponse(
            state=game_state_to_response(games[room_code])
        )

@app.get("/rooms", response_model=RoomsListResponse)
async def get_rooms():
    rooms = [
        RoomSummary(
            room_code=code,
            players=len(state.players),
            max_players=state.max_players,
            phase=state.phase
        )
        for code, state in games.items()
        if state.phase == GamePhase.WAITING
    ]
    return RoomsListResponse(rooms=rooms)

@app.get("/rooms/active", response_model=RoomsListResponse)
async def get_rooms_active():
    rooms = [
        RoomSummary(
            room_code=code,
            players=len(state.players),
            max_players=state.max_players,
            phase=state.phase
        )
        for code, state in games.items()
        if state.phase == GamePhase.PLAYING
    ]
    return RoomsListResponse(rooms=rooms)

@app.post("/rooms/{room_code}/observe", response_model=ObserveRoomResponse)
async def observe(room_code: str, request: ObserveRoomRequest):
    if room_code not in games:
        raise HTTPException(status_code=404, detail="Room not found")
    async with get_lock(room_code):
        if games[room_code].phase != GamePhase.PLAYING:
            raise HTTPException(status_code=400, detail="Game not started yet")
        try:
            state = add_observer(games[room_code], request.observer_name)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        games[room_code] = state
        advance_sequence(room_code)
        await save_game(room_code, games[room_code])
        await manager.broadcast(room_code, game_state_to_response(games[room_code]).model_dump(mode='json'))
        return ObserveRoomResponse(
            room_code=room_code,
            state=game_state_to_response(games[room_code])
        )
        


