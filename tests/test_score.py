from backend.game import calculate_score
from backend.models import GameState, GamePhase, Row, Card
from tests.conftest import make_players_for_calculate_score


def test_calculate_score_no_jokers():
    players = make_players_for_calculate_score()
    state = GameState(
        room_code="TEST",
        players=players,
        phase=GamePhase.FINISHED
    )
    scores = calculate_score(state)
    assert scores["Alice"] == 34


def test_calculate_score_one_joker():
    players = make_players_for_calculate_score()
    state = GameState(
        room_code="TEST",
        players=players,
        phase=GamePhase.FINISHED
    )
    scores = calculate_score(state)
    assert scores["Bob"] == 27


def test_calculate_score_two_jokers():
    players = make_players_for_calculate_score()
    state = GameState(
        room_code="TEST",
        players=players,
        phase=GamePhase.FINISHED
    )
    scores = calculate_score(state)
    assert scores["Charlie"] == 31


def test_calculate_score_returns_all_players():
    players = make_players_for_calculate_score()
    state = GameState(
        room_code="TEST",
        players=players,
        phase=GamePhase.FINISHED
    )
    scores = calculate_score(state)
    assert set(scores.keys()) == {"Alice", "Bob", "Charlie"}