import random
from backend.models import Card, Row, Player, GameState, GameEvent, CardType, CardColor, GamePhase, GameAction


def create_deck(num_players: int) -> list[Card]:
    deck = []
    
    for color in CardColor:
        for _ in range(9):
            deck.append(Card(card_type=CardType.COLOR, color=color))
    
    if num_players == 3:
        color_to_remove = random.choice(list(CardColor))
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