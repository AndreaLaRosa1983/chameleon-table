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