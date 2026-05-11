# tests/test_game.py
from backend.game import create_deck, create_players, create_rows, assign_initial_colors, create_game, current_turn, take_row, end_round, draw_card
import pytest
from backend.models import CardType, CardColor, Player, GameState, GamePhase, Row, Card

 
def test_deck_5_players():
    players = create_players(["Mario", "Luca", "Anna", "Paolo", "Sara"])
    assigned_colors = assign_initial_colors(players)
    deck = create_deck(5, assigned_colors)
    
    # total: 58 color (5 colors with 8 cards + 2 colors with 9 cards) + 10 plus2 + 3 joker + 1 last_round = 72 cards
    assert len(deck) == 72
    
    # 58 color cards
    color_cards = [c for c in deck if c.card_type == CardType.COLOR]
    assert len(color_cards) == 58
    
    # assigned colors have 8 cards, others have 9
    for color in CardColor:
        count = len([c for c in color_cards if c.color == color])
        if color in assigned_colors:
            assert count == 8
        else:
            assert count == 9
    
    # last_round has exactly 15 cards after it
    last_round_index = next(i for i, c in enumerate(deck) if c.card_type == CardType.LAST_ROUND)
    assert len(deck) - last_round_index - 1 == 15

def test_deck_3_players():
    players = create_players(["Mario", "Luca", "Anna"])
    assigned_colors = assign_initial_colors(players)
    deck = create_deck(3, assigned_colors)
    
    # total: 51 color + 10 plus2 + 3 joker + 1 last_round = 65 cards
    assert len(deck) == 65
    
    # only 6 distinct colors (one removed for 3 players)
    color_cards = [c for c in deck if c.card_type == CardType.COLOR]
    colors_in_deck = set(c.color for c in color_cards)
    assert len(colors_in_deck) == 6
    
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
    
def test_create_game_basic_structure():
    state = create_game("ROOM1", ["Alice", "Bob", "Charlie"])
    assert isinstance(state, GameState)
    assert state.phase == GamePhase.WAITING
    assert len(state.players) == 3
    assert len(state.rows) == 3
    assert state.round_starter == state.turn_order[0]
    assert state.last_row_taker is None
    assert set(state.turn_order) == {"Alice", "Bob", "Charlie"}


def test_create_game_deck_and_colors():
    state = create_game("ROOM1", ["Alice", "Bob", "Charlie"])
    assert len(state.deck) > 0
    assert any(c.card_type == CardType.LAST_ROUND for c in state.deck)
    colors = [p.cards[0].color for p in state.players]
    assert len(colors) == len(set(colors))


def test_create_game_two_players():
    state = create_game("ROOM1", ["Alice", "Bob"])
    assert len(state.players) == 2
    assert len(state.rows) == 2


def test_create_game_five_players():
    state = create_game("ROOM1", ["Alice", "Bob", "Charlie", "Dave", "Eve"])
    assert len(state.players) == 5
    assert len(state.rows) == 5


def make_state(player_configs: list[dict]) -> GameState:
    # Helper: creates minimal GameState with players and turn_order
    players = []
    for cfg in player_configs:
        p = Player(name=cfg["name"])
        p.passed = cfg.get("passed", False)
        p.active = cfg.get("active", True)
        players.append(p)

    return GameState(
        room_code="TEST",
        players=players,
        turn_order=[cfg["name"] for cfg in player_configs]
    )


def test_current_turn_returns_first_player():
    state = make_state([{"name": "Alice"}, {"name": "Bob"}, {"name": "Charlie"}])
    assert current_turn(state) == "Alice"

def test_current_turn_skips_passed_and_inactive():
    state = make_state([
        {"name": "Alice", "passed": True},
        {"name": "Bob", "active": False},
        {"name": "Charlie"},
    ])
    assert current_turn(state) == "Charlie"

def test_current_turn_returns_none_when_all_passed_or_inactive():
    state = make_state([
        {"name": "Alice", "passed": True},
        {"name": "Bob", "active": False},
    ])
    assert current_turn(state) is None

def test_current_turn_empty_turn_order():
    state = GameState(room_code="TEST")
    assert current_turn(state) is None
    
def make_game_state_for_take_row() -> GameState:
    # Helper: creates a GameState ready for take_row tests.
    players = [
        Player(name="Alice"),
        Player(name="Bob"),
        Player(name="Charlie"),
    ]
    rows = [
        Row(cards=[Card(card_type=CardType.COLOR, color=CardColor.RED)]),
        Row(cards=[Card(card_type=CardType.COLOR, color=CardColor.BLUE)]),
        Row(cards=[Card(card_type=CardType.COLOR, color=CardColor.GREEN)]),
    ]
    return GameState(
        room_code="TEST",
        players=players,
        rows=rows,
        turn_order=["Alice", "Bob", "Charlie"],
        round_starter="Alice"
    )
    
def test_take_row_adds_cards_to_player():
    state = make_game_state_for_take_row()
    take_row(state, "Alice", 0)
    alice = next(p for p in state.players if p.name == "Alice")
    assert len(alice.cards) == 1
    assert alice.cards[0].color == CardColor.RED


def test_take_row_sets_player_passed():
    state = make_game_state_for_take_row()
    take_row(state, "Alice", 0)
    alice = next(p for p in state.players if p.name == "Alice")
    assert alice.passed == True


def test_take_row_marks_row_as_taken():
    state = make_game_state_for_take_row()
    take_row(state, "Alice", 0)
    assert state.rows[0].taken_by == "Alice"


def test_take_row_not_your_turn_raises():
    state = make_game_state_for_take_row()
    with pytest.raises(ValueError):
        take_row(state, "Bob", 0)
        
def test_take_row_jokers_go_to_player_jokers():
    players = [Player(name="Alice"), Player(name="Bob"), Player(name="Charlie")]
    rows = [
        Row(cards=[
            Card(card_type=CardType.COLOR, color=CardColor.RED),
            Card(card_type=CardType.JOKER),
        ]),
        Row(cards=[Card(card_type=CardType.COLOR, color=CardColor.BLUE)]),
        Row(cards=[Card(card_type=CardType.COLOR, color=CardColor.GREEN)]),
    ]
    state = GameState(
        room_code="TEST",
        players=players,
        rows=rows,
        turn_order=["Alice", "Bob", "Charlie"],
        round_starter="Alice"
    )
    take_row(state, "Alice", 0)
    alice = next(p for p in state.players if p.name == "Alice")
    assert len(alice.cards) == 1
    assert len(alice.jokers) == 1
    assert alice.jokers[0].card_type == CardType.JOKER
    
def make_game_state_for_end_round(last_round: bool = False) -> GameState:
    """Helper: creates a GameState where all players have passed."""
    players = [
        Player(name="Alice", passed=True),
        Player(name="Bob", passed=True),
        Player(name="Charlie", passed=True),
    ]
    rows = [
        Row(cards=[], taken_by="Bob"),
        Row(cards=[], taken_by="Alice"),
        Row(cards=[], taken_by="Charlie"),
    ]
    return GameState(
        room_code="TEST",
        players=players,
        rows=rows,
        turn_order=["Alice", "Bob", "Charlie"],
        round_starter="Alice",
        last_row_taker="Charlie",
        last_round=last_round,
        phase=GamePhase.PLAYING
    )


def test_end_round_resets_passed():
    state = make_game_state_for_end_round()
    end_round(state)
    for player in state.players:
        assert player.passed == False


def test_end_round_clears_rows():
    state = make_game_state_for_end_round()
    end_round(state)
    for row in state.rows:
        assert row.taken_by is None
        assert len(row.cards) == 0


def test_end_round_updates_round_starter():
    state = make_game_state_for_end_round()
    end_round(state)
    assert state.round_starter == "Charlie"


def test_end_round_rotates_turn_order():
    state = make_game_state_for_end_round()
    end_round(state)
    assert state.turn_order[0] == "Charlie"


def test_end_round_sets_finished_if_last_round():
    state = make_game_state_for_end_round(last_round=True)
    end_round(state)
    assert state.phase == GamePhase.FINISHED


def test_end_round_keeps_playing_if_not_last_round():
    state = make_game_state_for_end_round(last_round=False)
    end_round(state)
    assert state.phase == GamePhase.PLAYING
    
def make_game_state_for_draw_card() -> GameState:
    """Helper: creates a GameState ready for draw_card tests."""
    players = [
        Player(name="Alice"),
        Player(name="Bob"),
        Player(name="Charlie"),
    ]
    rows = [
        Row(cards=[]),
        Row(cards=[]),
        Row(cards=[]),
    ]
    deck = [
        Card(card_type=CardType.COLOR, color=CardColor.RED),
        Card(card_type=CardType.COLOR, color=CardColor.BLUE),
        Card(card_type=CardType.COLOR, color=CardColor.GREEN),
    ]
    return GameState(
        room_code="TEST",
        players=players,
        rows=rows,
        deck=deck,
        turn_order=["Alice", "Bob", "Charlie"],
        round_starter="Alice",
        phase=GamePhase.PLAYING
    )


def test_draw_card_returns_card():
    state = make_game_state_for_draw_card()
    _, card = draw_card(state, "Alice")
    assert card.card_type == CardType.COLOR
    assert card.color == CardColor.RED


def test_draw_card_removes_card_from_deck():
    state = make_game_state_for_draw_card()
    draw_card(state, "Alice")
    assert len(state.deck) == 2


def test_draw_card_not_your_turn_raises():
    state = make_game_state_for_draw_card()
    with pytest.raises(ValueError):
        draw_card(state, "Bob")


def test_draw_card_last_round_sets_flag():
    state = make_game_state_for_draw_card()
    state.deck.insert(0, Card(card_type=CardType.LAST_ROUND))
    _, card = draw_card(state, "Alice")
    assert state.last_round == True
    assert card.card_type != CardType.LAST_ROUND