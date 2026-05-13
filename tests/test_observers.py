import pytest
from backend.game import add_observer, remove_observer
from tests.conftest import make_game_state_for_observers

def test_add_observer():
    state = add_observer(make_game_state_for_observers(), "Spectator1")
    assert "Spectator1" in state.observers

def test_add_observer_full():
    state = make_game_state_for_observers()
    state = add_observer(state, "S1")
    state = add_observer(state, "S2")
    state = add_observer(state, "S3")
    state = add_observer(state, "S4")
    with pytest.raises(ValueError, match="Room is full"):
        add_observer(state, "S5")

def test_add_observer_already_observing():
    state = add_observer(make_game_state_for_observers(), "S1")
    with pytest.raises(ValueError, match="Already observing"):
        add_observer(state, "S1")

def test_add_observer_already_player():
    with pytest.raises(ValueError, match="Already a player"):
        add_observer(make_game_state_for_observers(), "Alice")

def test_remove_observer():
    state = add_observer(make_game_state_for_observers(), "S1")
    state = remove_observer(state, "S1")
    assert "S1" not in state.observers

def test_remove_observer_not_present():
    with pytest.raises(ValueError, match="Not an observer"):
        remove_observer(make_game_state_for_observers(), "S1")