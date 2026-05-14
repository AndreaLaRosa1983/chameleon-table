import pytest
from backend.game import create_game, end_round, place_card
from backend.models import Card, CardType, CardColor, Row, GamePhase
from tests.conftest import (
    make_game_state_for_end_round_two_players,
    make_game_state_for_end_round
)

def test_end_round_two_players_creates_special_rows():
    state = make_game_state_for_end_round_two_players()
    state = end_round(state)
    assert len(state.rows) == 3
    assert state.rows[0].max_cards == 1
    assert state.rows[1].max_cards == 2
    assert state.rows[2].max_cards == 3

def test_end_round_three_to_two_active_creates_special_rows():
    state = make_game_state_for_end_round()
    state.players[2].active = False
    state = end_round(state)
    assert len(state.rows) == 3
    assert state.rows[0].max_cards == 1
    assert state.rows[1].max_cards == 2
    assert state.rows[2].max_cards == 3

def test_place_card_respects_row_capacity_one():
    state = make_game_state_for_end_round_two_players()
    state.players[0].passed = False
    state.players[1].passed = False
    state.rows = [Row(max_cards=1), Row(max_cards=2), Row(max_cards=3)]
    card = Card(card_type=CardType.COLOR, color=CardColor.RED)
    state = place_card(state, "Alice", 0, card)
    assert len(state.rows[0].cards) == 1
    card2 = Card(card_type=CardType.COLOR, color=CardColor.BLUE)
    with pytest.raises(ValueError, match="Row taken or full"):
        place_card(state, "Alice", 0, card2)

def test_place_card_respects_row_capacity_two():
    state = make_game_state_for_end_round_two_players()
    state.players[0].passed = False
    state.players[1].passed = False
    state.rows = [Row(max_cards=1), Row(max_cards=2), Row(max_cards=3)]
    card1 = Card(card_type=CardType.COLOR, color=CardColor.RED)
    card2 = Card(card_type=CardType.COLOR, color=CardColor.BLUE)
    card3 = Card(card_type=CardType.COLOR, color=CardColor.GREEN)
    state = place_card(state, "Alice", 1, card1)
    state = place_card(state, "Alice", 1, card2)
    assert len(state.rows[1].cards) == 2
    with pytest.raises(ValueError, match="Row taken or full"):
        place_card(state, "Alice", 1, card3)

def test_create_game_two_players_deck_removes_two_colors():
    state = create_game("ROOM1", ["Alice", "Bob"])
    color_cards = [c for c in state.deck if c.card_type == CardType.COLOR]
    colors_in_deck = set(c.color for c in color_cards)
    assert len(colors_in_deck) == 5

def test_create_game_two_players_initial_cards():
    state = create_game("ROOM1", ["Alice", "Bob"])
    for player in state.players:
        assert len(player.cards) == 2
        assert player.cards[0].color != player.cards[1].color