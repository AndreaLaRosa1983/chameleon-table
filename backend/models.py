from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Card:
    color: str  # color of the card (e.g. "red", "blue", "green")

@dataclass
class Row:
    # cards currently placed in this row (max 3)
    cards: list[Card] = field(default_factory=list)
    # name of the player who took this row (None if still available)
    taken_by: Optional[str] = None

@dataclass
class Player:
    name: str                                          # player's display name
    cards: list[Card] = field(default_factory=list)   # cards collected by the player
    passed: bool = False                               # True if player passed this round

@dataclass
class GameState:
    room_code: str                                      # unique room identifier
    deck: list[Card] = field(default_factory=list)      # remaining cards in the deck
    rows: list[Row] = field(default_factory=list)       # always 3 rows on the table
    players: list[Player] = field(default_factory=list) # list of players in the game
    current_turn: Optional[str] = None                  # name of the player whose turn it is
    phase: str = "waiting"                              # waiting | playing | finished