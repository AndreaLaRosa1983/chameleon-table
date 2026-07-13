from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import time

MAX_OBSERVERS = 4

class CardColor(Enum):
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"
    PURPLE = "purple"
    ORANGE = "orange"
    BROWN = "brown"

class CardType(Enum):
    COLOR = "color"
    JOKER = "joker"
    PLUS2 = "plus2"
    LAST_ROUND = "last_round"

class GamePhase(Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"
    ABORTED = "aborted"

class GameAction(Enum):
    DRAW = "draw"
    TAKE_ROW = "take_row"
    GAME_START = "game_start"
    GAME_END = "game_end"
    ROUND_END = "round_end"
    PLAYER_LEFT = "player_left"
    GAME_ABORTED = "game_aborted"

@dataclass
class Card:
    card_type: CardType
    color: Optional[CardColor] = None

@dataclass
class Row:
    cards: list[Card] = field(default_factory=list)
    taken_by: Optional[str] = None
    max_cards: int = 3

@dataclass
class Player:
    name: str
    cards: list[Card] = field(default_factory=list)
    jokers: list[Card] = field(default_factory=list)
    passed: bool = False
    active: bool = True
    left: bool = False
@dataclass
class GameEvent:
    player: str
    action: GameAction
    details: dict
    timestamp: float = field(default_factory=time.time)

@dataclass
class GameState:
    room_code: str
    deck: list[Card] = field(default_factory=list)
    rows: list[Row] = field(default_factory=list)    
    players: list[Player] = field(default_factory=list)
    turn_order: list[str] = field(default_factory=list)
    current_turn: Optional[str] = None
    last_round: bool = False
    phase: GamePhase = GamePhase.WAITING
    history: list[GameEvent] = field(default_factory=list)
    round_starter: Optional[str] = None
    last_row_taker: Optional[str] = None
    pending_card: Optional[Card] = None
    observers: list[str] = field(default_factory=list)
    min_players: int = 2
    max_players: int = 5
    sequence_number: int = 0 
    turn_started_at: Optional[float] = None
    created_at: float = field(default_factory=time.time)