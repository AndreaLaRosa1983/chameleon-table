from backend.game import take_row, end_round
import pytest
from backend.models import CardType, CardColor, Player, GameState, GamePhase, Row, Card
from tests.conftest import make_game_state_for_take_row, make_game_state_for_end_round


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
    