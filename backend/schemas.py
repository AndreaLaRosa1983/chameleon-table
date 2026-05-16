from pydantic import BaseModel, Field
from typing import Optional
from backend.models import CardColor, CardType, GamePhase
class CardResponse(BaseModel):
    card_type: CardType
    color: Optional[CardColor] = None

class RowResponse(BaseModel):
    cards: list[CardResponse] = []
    taken_by: Optional[str] = None

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

class CreateRoomRequest(BaseModel):
    player_name: str
    max_players: int = Field(ge=2, le=5)

class CreateRoomResponse(BaseModel):
    room_code: str
    state: GameStateResponse
    
class JoinRoomRequest(BaseModel):
    player_name: str

class JoinRoomResponse(BaseModel):
    room_code: str
    state: GameStateResponse
    
class StartRoomRequest(BaseModel):
    player_name: str

class StartRoomResponse(BaseModel):
    room_code: str
    state: GameStateResponse
    
class RoomStateResponse(BaseModel):
    room_code: str
    state: GameStateResponse
    
class DrawCardRequest(BaseModel):
    player_name: str

class DrawCardResponse(BaseModel):
    card: CardResponse
    state: GameStateResponse

class PlaceCardRequest(BaseModel):
    player_name: str
    row_index: int

class PlaceCardResponse(BaseModel):
    state: GameStateResponse

class TakeRowRequest(BaseModel):
    player_name: str
    row_index: int

class TakeRowResponse(BaseModel):
    state: GameStateResponse

class LeaveRoomRequest(BaseModel):
    player_name: str

class LeaveRoomResponse(BaseModel):
    state: GameStateResponse
    
class RoomSummary(BaseModel):
    room_code: str
    players: int
    max_players: int
    phase: GamePhase

class RoomsListResponse(BaseModel):
    rooms: list[RoomSummary]
