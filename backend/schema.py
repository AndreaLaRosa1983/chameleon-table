from pydantic import BaseModel
from typing import Optional
from backend.models import CardColor, CardType

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