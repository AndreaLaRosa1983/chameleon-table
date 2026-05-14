from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_create_room():
    response = client.post("/rooms", json={"player_name": "Alice", "max_players": 3})
    assert response.status_code == 200
    data = response.json()
    assert "room_code" in data
    assert "state" in data
    assert data["state"]["phase"] == "waiting"
    
def test_join_room():
    response = client.post("/rooms", json={"player_name": "Alice", "max_players": 3})
    room_code = response.json()["room_code"]
    response = client.post(f"/rooms/{room_code}/join", json={"player_name": "Bob"})
    assert response.status_code == 200
    data = response.json()
    assert "room_code" in data
    assert "state" in data

def test_join_room_not_found():
    response = client.post("/rooms/XXXX/join", json={"player_name": "Bob"})
    assert response.status_code == 404

def test_join_room_full():
    response = client.post("/rooms", json={"player_name": "Alice", "max_players": 2})
    room_code = response.json()["room_code"]
    client.post(f"/rooms/{room_code}/join", json={"player_name": "Bob"})
    response = client.post(f"/rooms/{room_code}/join", json={"player_name": "Charlie"})
    assert response.status_code == 400
    
def test_start_room():
    response = client.post("/rooms", json={"player_name": "Alice", "max_players": 2})
    room_code = response.json()["room_code"]
    client.post(f"/rooms/{room_code}/join", json={"player_name": "Bob"})
    response = client.post(f"/rooms/{room_code}/start", json={"player_name": "Alice"})
    assert response.status_code == 200
    assert response.json()["state"]["phase"] == "playing"

def test_start_room_not_found():
    response = client.post("/rooms/XXXX/start", json={"player_name": "Alice"})
    assert response.status_code == 404

def test_start_room_not_enough_players():
    response = client.post("/rooms", json={"player_name": "Alice", "max_players": 3})
    room_code = response.json()["room_code"]
    response = client.post(f"/rooms/{room_code}/start", json={"player_name": "Alice"})
    assert response.status_code == 400