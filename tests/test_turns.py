from backend.game import current_turn, draw_card, place_card
import pytest
from backend.models import CardType, CardColor, GameState, Card
from tests.conftest import make_state, make_game_state_for_draw_card, make_game_state_for_place_card

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
    


def test_place_card_adds_card_to_row():
    state = make_game_state_for_place_card()
    card = Card(card_type=CardType.COLOR, color=CardColor.RED)
    place_card(state, "Alice", 0, card)
    assert len(state.rows[0].cards) == 1
    assert state.rows[0].cards[0].color == CardColor.RED


def test_place_card_not_your_turn_raises():
    state = make_game_state_for_place_card()
    card = Card(card_type=CardType.COLOR, color=CardColor.RED)
    with pytest.raises(ValueError):
        place_card(state, "Bob", 0, card)


def test_place_card_row_not_available_raises():
    state = make_game_state_for_place_card()
    state.rows[0].taken_by = "Bob"
    card = Card(card_type=CardType.COLOR, color=CardColor.RED)
    with pytest.raises(ValueError):
        place_card(state, "Alice", 0, card)