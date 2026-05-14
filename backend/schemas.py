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