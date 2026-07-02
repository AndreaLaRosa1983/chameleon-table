from pydantic import BaseModel, Field
from typing import Optional
from backend.models import CardColor, CardType, GamePhase
class CardResponse(BaseModel):
    card_type: CardType
    color: Optional[CardColor] = None

class RowResponse(BaseModel):
    cards: list[CardResponse] = []
    taken_by: Optional[str] = None
    max_cards: int = 3
class PlayerResponse(BaseModel):
    name: str
    cards: list[CardResponse] = []
    jokers: list[CardResponse] = []
    passed: bool = False
    active: bool = True
    
class GameStateResponse(BaseModel):
    room_code: str
    rows: list[RowResponse] = []
    players: list[PlayerResponse] = []
    turn_order: list[str] = []
    current_turn: Optional[str] = None
    last_round: bool = False
    phase: GamePhase = GamePhase.WAITING
    round_starter: Optional[str] = None
    last_row_taker: Optional[str] = None
    observers: list[str] = []
    min_players: int = 2
    sequence_number: int = 0
    deck_count: int = 0
    pending_card: Optional[CardResponse] = None

class CreateRoomRequest(BaseModel):
    max_players: int = Field(ge=2, le=5)

class CreateRoomResponse(BaseModel):
    room_code: str
    state: GameStateResponse
    
class JoinRoomRequest(BaseModel):
    pass

class JoinRoomResponse(BaseModel):
    room_code: str
    state: GameStateResponse
    
class StartRoomRequest(BaseModel):
    pass

class StartRoomResponse(BaseModel):
    room_code: str
    state: GameStateResponse
    
class RoomStateResponse(BaseModel):
    room_code: str
    state: GameStateResponse
    
class DrawCardRequest(BaseModel):
    pass

class DrawCardResponse(BaseModel):
    card: CardResponse
    state: GameStateResponse

class PlaceCardRequest(BaseModel):
    row_index: int

class PlaceCardResponse(BaseModel):
    state: GameStateResponse

class TakeRowRequest(BaseModel):
    row_index: int

class TakeRowResponse(BaseModel):
    state: GameStateResponse

class LeaveRoomRequest(BaseModel):
    pass

class LeaveRoomResponse(BaseModel):
    state: GameStateResponse

class RoomSummary(BaseModel):
    room_code: str
    players: int
    max_players: int
    phase: GamePhase
    players_list: list[str] = [] 


class RoomsListResponse(BaseModel):
    rooms: list[RoomSummary]

class ObserveRoomRequest(BaseModel):
    pass

class ObserveRoomResponse(BaseModel):
    room_code: str
    state: GameStateResponse
    
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class RegisterResponse(BaseModel):
    username: str
    email: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
class LeaveObserveRequest(BaseModel):
    pass

class LeaveObserveResponse(BaseModel):
    room_code: str
    state: GameStateResponse