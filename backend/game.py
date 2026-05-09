import random
from backend.models import Card, Row, Player, GameState, GameEvent, CardType, CardColor, GamePhase, GameAction
from typing import Optional

def create_deck(num_players: int, assigned_colors: list[CardColor]) -> list[Card]:
    deck = []
    
    for color in CardColor:
        count = 8 if color in assigned_colors else 9
        for _ in range(count):
            deck.append(Card(card_type=CardType.COLOR, color=color))
    
    if num_players == 3:
        color_to_remove = random.choice(list(set(CardColor) - set(assigned_colors)))
        deck = [card for card in deck if card.color != color_to_remove]
    
    for _ in range(3):
        deck.append(Card(card_type=CardType.JOKER))
        
      
    for _ in range(10):
        deck.append(Card(card_type=CardType.PLUS2))
        
    
    random.shuffle(deck)
    
    
    deck.insert(len(deck) - 15, Card(card_type=CardType.LAST_ROUND))
    
    return deck

def create_players(player_names: list[str]) -> list[Player]:
    return [Player(name=name) for name in player_names]

def create_rows(num_players: int) -> list[Row]:
    return [Row() for _ in range(num_players)]

def assign_initial_colors(players: list[Player]) -> list[CardColor]:
    
    colors = random.sample(list(CardColor), len(players))
    
    for player, color in zip(players, colors):
        player.cards.append(Card(card_type=CardType.COLOR, color=color))
    return colors

def create_game(room_code: str, player_names: list[str]) -> GameState:
    
    players = create_players(player_names)
    
    n_players = len(players)
    
    assigned_color = assign_initial_colors(players)
    deck = create_deck(n_players,assigned_color)
    rows = create_rows(n_players)
    
    start = random.randint(0, n_players - 1)
    turn_order = player_names[start:] + player_names[:start]
    
    return GameState(
    room_code=room_code,
    deck=deck,
    rows=rows,
    players=players,
    turn_order=turn_order,
    round_starter=turn_order[0],
    phase=GamePhase.WAITING
    )
    
def current_turn(state: GameState) -> Optional[str]:
    for name in state.turn_order:
        player = next((p for p in state.players if p.name == name), None)
        if player and not player.passed and player.active:
            return name
    return None

def take_row(state: GameState, player_name: str, row_index: int) -> GameState:
    if current_turn(state) != player_name:
        raise ValueError("Not your turn")
    
    row = state.rows[row_index]
    
    if len(row.cards) == 0:
        raise ValueError("Row is empty")
    
    if row.taken_by is not None:
        raise ValueError("Row already taken")
    
    player = next(p for p in state.players if p.name == player_name)
    player.cards.extend(row.cards)
    player.passed = True
    row.taken_by = player_name
    
    return state