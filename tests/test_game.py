# tests/test_game.py
from backend.game import create_deck
from backend.models import CardType

def test_deck_5_players():
    deck = create_deck(5)
    
    # total: 63 color + 10 plus2 + 3 joker + 1 last_round = 77 cards
    assert len(deck) == 77
    
    # 63 color cards (9 per color * 7 colors)
    color_cards = [c for c in deck if c.card_type == CardType.COLOR]
    assert len(color_cards) == 63
    
    # 10 plus2 cards
    plus2_cards = [c for c in deck if c.card_type == CardType.PLUS2]
    assert len(plus2_cards) == 10
    
    # 3 jokers
    joker_cards = [c for c in deck if c.card_type == CardType.JOKER]
    assert len(joker_cards) == 3
    
    # exactly 1 last_round card
    last_round_cards = [c for c in deck if c.card_type == CardType.LAST_ROUND]
    assert len(last_round_cards) == 1
    
    # last_round is exactly at position -15 from the bottom
    assert deck[-15].card_type == CardType.LAST_ROUND

def test_deck_3_players():
    deck = create_deck(3)
    
    # one color removed: 54 color + 10 plus2 + 3 joker + 1 last_round = 68 cards
    assert len(deck) == 68
    
    # 54 color cards (9 per color * 6 colors)
    color_cards = [c for c in deck if c.card_type == CardType.COLOR]
    assert len(color_cards) == 54
    
    # only 6 distinct colors present
    colors_in_deck = set(c.color for c in color_cards)
    assert len(colors_in_deck) == 6
    
    # plus2 and jokers unchanged
    assert len([c for c in deck if c.card_type == CardType.PLUS2]) == 10
    assert len([c for c in deck if c.card_type == CardType.JOKER]) == 3
    
    # last_round at position -15
    assert deck[-15].card_type == CardType.LAST_ROUNDpytest -vars