from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import time

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
    WAITING = "waiting"       # waiting for players to join
    PLAYING = "playing"       # game in progress
    FINISHED = "finished"     # game ended normally
    ABORTED = "aborted"       # game ended because too many players disconnected

class GameAction(Enum):
    DRAW = "draw"
    TAKE_ROW = "take_row"
    GAME_START = "game_start"
    GAME_END = "game_end"
    ROUND_END = "round_end"
    PLAYER_LEFT = "player_left"   # player disconnected permanently
    GAME_ABORTED = "game_aborted" # game aborted due to insufficient players

@dataclass
class Card:
    card_type: CardType
    color: Optional[CardColor] = None  # only relevant when card_type == CardType.COLOR

@dataclass
class Row:
    cards: list[Card] = field(default_factory=list)
    taken_by: Optional[str] = None

@dataclass
class Player:
    name: str
    cards: list[Card] = field(default_factory=list)
    jokers: list[Card] = field(default_factory=list)  # kept separate, assigned to a color only at game end
    passed: bool = False                               # True if player passed this round, resets each round
    active: bool = True                                # False if player disconnected permanently

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
    rows: list[Row] = field(default_factory=list)              # N rows = N players
    players: list[Player] = field(default_factory=list)
    turn_order: list[str] = field(default_factory=list)        # ordered list of player names
    current_turn: Optional[str] = None
    last_round: bool = False                                   # True when last_round card is drawn from deck
    phase: GamePhase = GamePhase.WAITING
    history: list[GameEvent] = field(default_factory=list)
    round_starter: Optional[str] = None
    last_row_taker: Optional[str] = None
    min_players: int = 2       
    
    
