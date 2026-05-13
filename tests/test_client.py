from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_create_room():
    response = client.post("/rooms", json={"player_name": "Alice", "min_players": 2})
    assert response.status_code == 200
    assert "room_code" in response.json()