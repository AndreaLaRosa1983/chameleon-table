import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def setup_game(max_players=3, players=["Alice", "Bob", "Charlie"]):
    response = client.post("/rooms", json={"player_name": players[0], "max_players": max_players})
    room_code = response.json()["room_code"]
    for player in players[1:]:
        client.post(f"/rooms/{room_code}/join", json={"player_name": player})
    client.post(f"/rooms/{room_code}/start", json={"player_name": players[0]})
    return room_code

def test_draw_card():
    room_code = setup_game()
    state = client.get(f"/rooms/{room_code}/state").json()["state"]
    current_player = state["turn_order"][0]
    response = client.post(f"/rooms/{room_code}/draw", json={"player_name": current_player})
    assert response.status_code == 200
    assert "card" in response.json()
    assert "state" in response.json()

def test_draw_card_not_your_turn():
    room_code = setup_game()
    state = client.get(f"/rooms/{room_code}/state").json()["state"]
    wrong_player = state["turn_order"][1]
    response = client.post(f"/rooms/{room_code}/draw", json={"player_name": wrong_player})
    assert response.status_code == 400

def test_draw_card_room_not_found():
    response = client.post("/rooms/XXXX/draw", json={"player_name": "Alice"})
    assert response.status_code == 404

def test_draw_card_game_not_started():
    response = client.post("/rooms", json={"player_name": "Alice", "max_players": 3})
    room_code = response.json()["room_code"]
    response = client.post(f"/rooms/{room_code}/draw", json={"player_name": "Alice"})
    assert response.status_code == 400

def test_draw_twice_without_place():
    room_code = setup_game()
    state = client.get(f"/rooms/{room_code}/state").json()["state"]
    current_player = state["turn_order"][0]
    client.post(f"/rooms/{room_code}/draw", json={"player_name": current_player})
    response = client.post(f"/rooms/{room_code}/draw", json={"player_name": current_player})
    assert response.status_code == 400

def test_place_without_draw():
    room_code = setup_game()
    state = client.get(f"/rooms/{room_code}/state").json()["state"]
    current_player = state["turn_order"][0]
    response = client.post(f"/rooms/{room_code}/place", json={"player_name": current_player, "row_index": 0})
    assert response.status_code == 400
    
def test_take_row():
    room_code = setup_game()
    state = client.get(f"/rooms/{room_code}/state").json()["state"]
    current_player = state["turn_order"][0]
    client.post(f"/rooms/{room_code}/draw", json={"player_name": current_player})
    client.post(f"/rooms/{room_code}/place", json={"player_name": current_player, "row_index": 0})
    response = client.post(f"/rooms/{room_code}/take-row", json={"player_name": current_player, "row_index": 0})
    assert response.status_code == 200
    assert "state" in response.json()

def test_take_row_not_your_turn():
    room_code = setup_game()
    state = client.get(f"/rooms/{room_code}/state").json()["state"]
    wrong_player = state["turn_order"][1]
    response = client.post(f"/rooms/{room_code}/take-row", json={"player_name": wrong_player, "row_index": 0})
    assert response.status_code == 400

def test_take_row_room_not_found():
    response = client.post("/rooms/XXXX/take-row", json={"player_name": "Alice", "row_index": 0})
    assert response.status_code == 404

def test_take_row_with_pending_card():
    room_code = setup_game()
    state = client.get(f"/rooms/{room_code}/state").json()["state"]
    current_player = state["turn_order"][0]
    client.post(f"/rooms/{room_code}/draw", json={"player_name": current_player})
    response = client.post(f"/rooms/{room_code}/take-row", json={"player_name": current_player, "row_index": 0})
    assert response.status_code == 400
    
def test_leave_room():
    room_code = setup_game()
    response = client.post(f"/rooms/{room_code}/leave", json={"player_name": "Alice"})
    assert response.status_code == 200

def test_leave_room_not_found():
    response = client.post("/rooms/XXXX/leave", json={"player_name": "Alice"})
    assert response.status_code == 404

def test_leave_room_player_not_in_room():
    room_code = setup_game()
    response = client.post(f"/rooms/{room_code}/leave", json={"player_name": "Dave"})
    assert response.status_code == 403

def test_leave_room_aborts_game():
    room_code = setup_game()
    client.post(f"/rooms/{room_code}/leave", json={"player_name": "Alice"})
    client.post(f"/rooms/{room_code}/leave", json={"player_name": "Bob"})
    response = client.get(f"/rooms/{room_code}/state")
    assert response.json()["state"]["phase"] == "aborted"
    
def test_get_rooms_waiting():
    client.post("/rooms", json={"player_name": "Alice", "max_players": 3})
    client.post("/rooms", json={"player_name": "Bob", "max_players": 2})
    response = client.get("/rooms")
    assert response.status_code == 200
    assert "rooms" in response.json()
    assert len(response.json()["rooms"]) >= 2

def test_get_rooms_active():
    room_code = setup_game()
    response = client.get("/rooms/active")
    assert response.status_code == 200
    assert "rooms" in response.json()
    codes = [r["room_code"] for r in response.json()["rooms"]]
    assert room_code in codes