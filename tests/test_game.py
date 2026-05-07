# tests/test_game.py
from backend.game import create_deck, create_players, create_rows, assign_initial_colors
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

    # last_round has exactly 15 cards after it
    last_round_index = next(i for i, c in enumerate(deck) if c.card_type == CardType.LAST_ROUND)
    assert len(deck) - last_round_index - 1 == 15

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
    
    # exactly 1 last_round card
    last_round_cards = [c for c in deck if c.card_type == CardType.LAST_ROUND]
    assert len(last_round_cards) == 1

    # last_round has exactly 15 cards after it
    last_round_index = next(i for i, c in enumerate(deck) if c.card_type == CardType.LAST_ROUND)
    assert len(deck) - last_round_index - 1 == 15
    
    
def test_create_players():
    players = create_players(["Mario", "Luca", "Anna"])
    
    # correct number of players
    assert len(players) == 3
    
    # correct names
    assert players[0].name == "Mario"
    assert players[1].name == "Luca"
    assert players[2].name == "Anna"
    
    # all players start with empty cards and jokers
    for player in players:
        assert len(player.cards) == 0
        assert len(player.jokers) == 0
        assert player.passed == False
        assert player.active == True
        
def test_create_rows():
    rows = create_rows(4)
    
    # correct number of rows
    assert len(rows) == 4
    
    # all rows are empty
    for row in rows:
        assert len(row.cards) == 0
        assert row.taken_by is None

def test_assign_initial_colors():
    players = create_players(["Mario", "Luca", "Anna"])
    assign_initial_colors(players)
    
    # every player has exactly one card
    for player in players:
        assert len(player.cards) == 1
        assert player.cards[0].card_type == CardType.COLOR
    
    # all colors are different
    colors = [player.cards[0].color for player in players]
    assert len(set(colors)) == len(players)