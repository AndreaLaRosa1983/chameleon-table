from fastapi import FastAPI, HTTPException, Depends
from backend.ws_manager import manager
from backend.state import game_state_to_response, advance_sequence, get_lock, handle_disconnection, disconnection_tasks, reset_inactivity_timer, cleanup_stale_waiting_rooms, hard_cleanup_room_memory, redis_recovery_watcher
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
    RoomSummary, ObserveRoomRequest, ObserveRoomResponse,
    LeaveObserveRequest, LeaveObserveResponse)
from backend.game import create_game, draw_card, place_card, remove_observer, take_row, add_observer, end_round, create_rows, assign_initial_colors, create_deck
from backend.models import GamePhase, Player
from backend.ws_routes import router as ws_router
from backend.database import room_code_exists, init_db, load_active_games, save_game
from backend.redis_store import get_game, set_game, game_exists, get_all_game_keys, redis_only_exists
import random
import string
from asyncio import create_task
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from backend.auth import hash_password, verify_password, create_access_token, get_current_user
from backend.database import get_user, create_user
from backend.schemas import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse
from backend.game import calculate_score
from backend.redis_store import init_redis, close_redis
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # SETUP
    await init_redis()  
    await init_db()
    active_games = await load_active_games()
    for state in active_games:
        already_in_redis = await redis_only_exists(state.room_code)
        if already_in_redis:
            continue
        print(f"[LIFESPAN] Restoring room {state.room_code}: marking players inactive and starting grace period timers")
        state.sequence_number += 1
        for player in state.players:
            if player.active:
                player.active = False
        await set_game(state.room_code, state)
        for player in state.players:
            if not player.left:
                task = create_task(handle_disconnection(state.room_code, player.name))
                disconnection_tasks[f"{state.room_code}_{player.name}"] = task

    cleanup_task = create_task(cleanup_stale_waiting_rooms())
    recovery_task = create_task(redis_recovery_watcher())
    yield

    cleanup_task.cancel()
    recovery_task.cancel()
    await close_redis()

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
async def create_room(request: CreateRoomRequest, username: str = Depends(get_current_user)):
    room_codes = await get_all_game_keys()
    for code in room_codes:
        state = await get_game(code)
        if state and state.phase in [GamePhase.WAITING, GamePhase.PLAYING]:
            if any(p.name == username and not p.left for p in state.players):
                raise HTTPException(status_code=400, detail="You are already in a game")

    room_code = generate_room_code()
    attempts = 0
    while await game_exists(room_code) or await room_code_exists(room_code):
        room_code = generate_room_code()
        attempts += 1
        if attempts > 1000:
            raise HTTPException(status_code=503, detail="No room codes available")
    state = create_game(room_code, [username])
    state.max_players = request.max_players
    await set_game(room_code, state)
    await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))
    return CreateRoomResponse(
        room_code=room_code,
        state=game_state_to_response(state)
    )

@app.post("/rooms/{room_code}/join", response_model=JoinRoomResponse)
async def join_room(room_code: str, request: JoinRoomRequest, username: str = Depends(get_current_user)):
    if not await game_exists(room_code):
        raise HTTPException(status_code=404, detail="Room not found")
    
    room_codes = await get_all_game_keys()
    for code in room_codes:
        if code == room_code:
            continue
        state = await get_game(code)
        if state and state.phase in [GamePhase.WAITING, GamePhase.PLAYING]:
            if any(p.name == username and not p.left for p in state.players):
                raise HTTPException(status_code=400, detail="You are already in a game")

    async with get_lock(room_code):
        state = await get_game(room_code)
        if state.phase != GamePhase.WAITING:
            raise HTTPException(status_code=400, detail="Game already started")
        if len(state.players) >= state.max_players:
            raise HTTPException(status_code=400, detail="Room is full")
        if any(p.name == username for p in state.players):
            raise HTTPException(status_code=400, detail="Same Player Error")
        state.players.append(Player(name=username))
        state.turn_order.append(username)
        await set_game(room_code, state)
        state = await advance_sequence(room_code)
        await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))
        return JoinRoomResponse(
            room_code=room_code,
            state=game_state_to_response(state)
        )
        
@app.post("/rooms/{room_code}/start", response_model=StartRoomResponse)
async def start_room(room_code: str, request: StartRoomRequest, username: str = Depends(get_current_user)):
    if not await game_exists(room_code):
        raise HTTPException(status_code=404, detail="Room not found")
    async with get_lock(room_code):
        state = await get_game(room_code)
        if state.phase != GamePhase.WAITING:
            raise HTTPException(status_code=400, detail="Game already started")
        if not any(p.name == username for p in state.players):
            raise HTTPException(status_code=403, detail="Only a player can start the game")
        if len(state.players) < 2:
            raise HTTPException(status_code=400, detail="Not enough players")
        state.phase = GamePhase.PLAYING
        state.rows = create_rows(len(state.players))
        assigned_colors = assign_initial_colors(state.players)
        state.deck = create_deck(len(state.players), assigned_colors)
        await set_game(room_code, state)
        state = await advance_sequence(room_code)
        try:
            await save_game(room_code, state)
        except Exception as e:
            print(f"[WARNING] Postgres unavailable, state only in Redis: {e}")
        await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))
        return StartRoomResponse(
            room_code=room_code,
            state=game_state_to_response(state)
        )

@app.get("/rooms/{room_code}/state", response_model=RoomStateResponse)
async def room_state(room_code: str):
    if not await game_exists(room_code):
        raise HTTPException(status_code=404, detail="Room not found")
    state = await get_game(room_code)
    return RoomStateResponse(
        room_code=room_code,
        state=game_state_to_response(state)
    )

@app.post("/rooms/{room_code}/draw", response_model=DrawCardResponse)
async def draw(room_code: str, request: DrawCardRequest, username: str = Depends(get_current_user)):
    if not await game_exists(room_code):
        raise HTTPException(status_code=404, detail="Room not found")
    async with get_lock(room_code):
        state = await get_game(room_code)
        if state.phase != GamePhase.PLAYING:
            raise HTTPException(status_code=400, detail="Game not started or ended")
        if not any(p.name == username for p in state.players):
            raise HTTPException(status_code=403, detail="Only a player can draw a card")
        if state.pending_card is not None:
            raise HTTPException(status_code=400, detail="You have a pending card to place")
        try:
            state, card = draw_card(state, username)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        state.pending_card = card
        await set_game(room_code, state)
        state = await advance_sequence(room_code)
        try:
            await save_game(room_code, state)
        except Exception as e:
            print(f"[WARNING] Postgres unavailable, state only in Redis: {e}")
        await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))
        return DrawCardResponse(
            card=CardResponse(card_type=card.card_type, color=card.color),
            state=game_state_to_response(state)
        )

@app.post("/rooms/{room_code}/place", response_model=PlaceCardResponse)
async def place(room_code: str, request: PlaceCardRequest, username: str = Depends(get_current_user)):
    if not await game_exists(room_code):
        raise HTTPException(status_code=404, detail="Room not found")
    async with get_lock(room_code):
        state = await get_game(room_code)
        if state.phase != GamePhase.PLAYING:
            raise HTTPException(status_code=400, detail="Game not started or ended")
        if not any(p.name == username for p in state.players):
            raise HTTPException(status_code=403, detail="Only a player can place a card")
        if state.pending_card is None:
            raise HTTPException(status_code=400, detail="No pending card to place")
        try:
            card = state.pending_card
            state = place_card(state, username, request.row_index, card)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        state.pending_card = None
        await set_game(room_code, state)
        state = await advance_sequence(room_code)
        try:
            await save_game(room_code, state)
        except Exception as e:
            print(f"[WARNING] Postgres unavailable, state only in Redis: {e}")
        await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))
        return PlaceCardResponse(
            state=game_state_to_response(state)
        )

@app.post("/rooms/{room_code}/take-row", response_model=TakeRowResponse)
async def take_row_endpoint(room_code: str, request: TakeRowRequest, username: str = Depends(get_current_user)):
    if not await game_exists(room_code):
        raise HTTPException(status_code=404, detail="Room not found")
    finished = False
    async with get_lock(room_code):
        state = await get_game(room_code)
        if state.phase != GamePhase.PLAYING:
            raise HTTPException(status_code=400, detail="Game not started or ended")
        if not any(p.name == username for p in state.players):
            raise HTTPException(status_code=403, detail="Only a player can take a row")
        if state.pending_card:
            raise HTTPException(status_code=400, detail="There is a pending card, can't take a row")
        try:
            state = take_row(state, username, request.row_index)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        await set_game(room_code, state)
        state = await advance_sequence(room_code)
        try:
            await save_game(room_code, state)
        except Exception as e:
            print(f"[WARNING] Postgres unavailable, state only in Redis: {e}")
        await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))
        if all(p.passed for p in state.players if not p.left):
            state = end_round(state)
            await set_game(room_code, state)
            state = await advance_sequence(room_code)
            try:
                await save_game(room_code, state)
            except Exception as e:
                print(f"[WARNING] Postgres unavailable, state only in Redis: {e}")
            await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))
            if state.phase == GamePhase.FINISHED:
                finished = True
        response = TakeRowResponse(state=game_state_to_response(state))
    # lock released: if the game finished, free its RAM
    if finished:
        hard_cleanup_room_memory(room_code)
    return response

@app.post("/rooms/{room_code}/leave", response_model=LeaveRoomResponse)
async def leave(room_code: str, request: LeaveRoomRequest, username: str = Depends(get_current_user)):
    if not await game_exists(room_code):
        raise HTTPException(status_code=404, detail="Room not found")
    aborted = False
    async with get_lock(room_code):
        state = await get_game(room_code)
        if not any(p.name == username for p in state.players):
            raise HTTPException(status_code=403, detail="Player not in room")
        player = next(p for p in state.players if p.name == username)
        player.active = False
        player.left = True
        active_players = sum(1 for p in state.players if not p.left)
        if active_players < 2:
            state.phase = GamePhase.ABORTED
            aborted = True
        await set_game(room_code, state)
        state = await advance_sequence(room_code)
        try:
            await save_game(room_code, state)
        except Exception as e:
            print(f"[WARNING] Postgres unavailable, state only in Redis: {e}")
        await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))
        response = LeaveRoomResponse(state=game_state_to_response(state))
    # lock released: if the room aborted, free its RAM
    if aborted:
        hard_cleanup_room_memory(room_code)
    return response

@app.get("/rooms", response_model=RoomsListResponse)
async def get_rooms():
    room_codes = await get_all_game_keys()
    rooms = []
    for code in room_codes:
        state = await get_game(code)
        if state and state.phase == GamePhase.WAITING:
            rooms.append(RoomSummary(
                room_code=code,
                players=len(state.players),
                max_players=state.max_players,
                phase=state.phase,
                players_list=[p.name for p in state.players]
            ))
    return RoomsListResponse(rooms=rooms)

@app.get("/rooms/active", response_model=RoomsListResponse)
async def get_rooms_active():
    room_codes = await get_all_game_keys()
    rooms = []
    for code in room_codes:
        state = await get_game(code)
        if state and state.phase == GamePhase.PLAYING:
            rooms.append(RoomSummary(
                room_code=code,
                players=len(state.players),
                max_players=state.max_players,
                phase=state.phase,
                players_list=[p.name for p in state.players]
            ))
    return RoomsListResponse(rooms=rooms)

@app.post("/rooms/{room_code}/observe", response_model=ObserveRoomResponse)
async def observe(room_code: str, request: ObserveRoomRequest, username: str = Depends(get_current_user)):
    if not await game_exists(room_code):
        raise HTTPException(status_code=404, detail="Room not found")
    async with get_lock(room_code):
        state = await get_game(room_code)
        if state.phase != GamePhase.PLAYING:
            raise HTTPException(status_code=400, detail="Game not started yet")
        try:
            state = add_observer(state, username)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        await set_game(room_code, state)
        state = await advance_sequence(room_code)
        try:
            await save_game(room_code, state)
        except Exception as e:
            print(f"[WARNING] Postgres unavailable, state only in Redis: {e}")
        await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))
        return ObserveRoomResponse(
            room_code=room_code,
            state=game_state_to_response(state)
        )
        
        
@app.post("/rooms/{room_code}/leave-observe", response_model=LeaveObserveResponse)
async def leave_observe(room_code: str, request: LeaveObserveRequest, username: str = Depends(get_current_user)):
    if not await game_exists(room_code):
        raise HTTPException(status_code=404, detail="Room not found")
    async with get_lock(room_code):
        state = await get_game(room_code)
        try:
            state = remove_observer(state, username)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        await set_game(room_code, state)
        state = await advance_sequence(room_code)
        try:
            await save_game(room_code, state)
        except Exception as e:
            print(f"[WARNING] Postgres unavailable, state only in Redis: {e}")
        await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))
        return LeaveObserveResponse(
            room_code=room_code,
            state=game_state_to_response(state)
        )
# for debug purpose to end a match istantly
# @app.post("/rooms/{room_code}/debug-finish")  
# async def debug_finish(room_code: str):
#    state = await get_game(room_code)
#    state.phase = GamePhase.FINISHED
#    await set_game(room_code, state)
#    await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))
#    return {"ok": True} '''

@app.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest):
    if os.getenv("REGISTRATION_ENABLED", "true").lower() == "false":
        raise HTTPException(status_code=403, detail="Registration is disabled")
    existing = await get_user(request.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    hashed = hash_password(request.password)
    user = await create_user(request.username, request.email, hashed)
    return RegisterResponse(username=user.username, email=user.email)

@app.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    user = await get_user(request.username)
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user.username)
    return LoginResponse(access_token=token)

@app.get("/rooms/{room_code}/scores")
async def get_scores(room_code: str):
    state = await get_game(room_code)
    if state is None:
        raise HTTPException(status_code=404, detail="Room not found")
    if state.phase != GamePhase.FINISHED:
        raise HTTPException(status_code=400, detail="Game not finished yet")
    return calculate_score(state)

@app.post("/rooms/{room_code}/abort")
async def abort_game(room_code: str, username: str = Depends(get_current_user)):
    if not await game_exists(room_code):
        raise HTTPException(status_code=404, detail="Room not found")
    async with get_lock(room_code):
        state = await get_game(room_code)
        if state.phase != GamePhase.WAITING:
            raise HTTPException(status_code=400, detail="Game already started")
        if state.turn_order[0] != username:
            raise HTTPException(status_code=403, detail="Only the host can abort the game")
        state.phase = GamePhase.ABORTED
        await set_game(room_code, state)
        state = await advance_sequence(room_code)
        try:
            await save_game(room_code, state)
        except Exception as e:
            print(f"[WARNING] Postgres unavailable, state only in Redis: {e}")
        await manager.broadcast(room_code, game_state_to_response(state).model_dump(mode='json'))
    # lock released: free the aborted room's RAM
    hard_cleanup_room_memory(room_code)
    return {"ok": True}