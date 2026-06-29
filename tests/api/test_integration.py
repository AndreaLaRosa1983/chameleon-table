import os
os.environ["TESTING"] = "1"

import pytest
import uuid


def auth(token: str) -> dict:
    """Helper to build Authorization header."""
    return {"Authorization": f"Bearer {token}"}


async def register_and_login(
    async_client,
    username: str,
    password: str = "password123"
) -> str:
    """Register a user and return their JWT token."""
    await async_client.post("/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": password
    })
    res = await async_client.post(
        "/login",
        json={"username": username, "password": password}
    )
    return res.json()["access_token"]


async def setup_game(
    async_client,
    players: list[str] = None,
    max_players: int = 3
) -> tuple[str, dict]:
    """Register players, create a room, join and start."""
    if players is None:
        # Generate unique player names
        uid = str(uuid.uuid4())[:8]
        players = [f"Alice_{uid}", f"Bob_{uid}", f"Charlie_{uid}"]
    
    tokens = {}
    for p in players:
        tokens[p] = await register_and_login(async_client, p)
    
    res = await async_client.post(
        "/rooms",
        json={"max_players": max_players},
        headers=auth(tokens[players[0]])
    )
    room_code = res.json()["room_code"]
    
    for p in players[1:]:
        await async_client.post(
            f"/rooms/{room_code}/join",
            json={},
            headers=auth(tokens[p])
        )
    
    await async_client.post(
        f"/rooms/{room_code}/start",
        json={},
        headers=auth(tokens[players[0]])
    )
    
    return room_code, tokens


@pytest.mark.asyncio
async def test_register(async_client):
    uid = str(uuid.uuid4())[:8]
    res = await async_client.post("/register", json={
        "username": f"TestUser_{uid}",
        "email": f"test_{uid}@test.com",
        "password": "password123"
    })
    assert res.status_code == 200
    assert res.json()["username"] == f"TestUser_{uid}"


@pytest.mark.asyncio
async def test_register_duplicate_username(async_client):
    uid = str(uuid.uuid4())[:8]
    username = f"Dup_{uid}"
    await async_client.post("/register", json={"username": username, "email": f"a_{uid}@a.com", "password": "pw"})
    res = await async_client.post("/register", json={"username": username, "email": f"b_{uid}@b.com", "password": "pw"})
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_login_valid(async_client):
    uid = str(uuid.uuid4())[:8]
    username = f"LoginUser_{uid}"
    await async_client.post("/register", json={"username": username, "email": f"l_{uid}@l.com", "password": "pw"})
    res = await async_client.post("/login", json={"username": username, "password": "pw"})
    assert res.status_code == 200
    assert "access_token" in res.json()


@pytest.mark.asyncio
async def test_login_invalid(async_client):
    res = await async_client.post("/login", json={"username": "nobody", "password": "wrong"})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_create_room(async_client):
    uid = str(uuid.uuid4())[:8]
    token = await register_and_login(async_client, f"Creator1_{uid}")
    res = await async_client.post("/rooms", json={"max_players": 3}, headers=auth(token))
    assert res.status_code == 200
    assert "room_code" in res.json()
    assert res.json()["state"]["phase"] == "waiting"


@pytest.mark.asyncio
async def test_create_room_unauthorized(async_client):
    res = await async_client.post("/rooms", json={"max_players": 3})
    assert res.status_code == 401 or res.status_code == 422


@pytest.mark.asyncio
async def test_join_room(async_client):
    uid = str(uuid.uuid4())[:8]
    t1 = await register_and_login(async_client, f"Host1_{uid}")
    t2 = await register_and_login(async_client, f"Guest1_{uid}")
    res = await async_client.post("/rooms", json={"max_players": 3}, headers=auth(t1))
    room_code = res.json()["room_code"]
    res = await async_client.post(f"/rooms/{room_code}/join", json={}, headers=auth(t2))
    assert res.status_code == 200
    players = [p["name"] for p in res.json()["state"]["players"]]
    assert f"Guest1_{uid}" in players


@pytest.mark.asyncio
async def test_join_room_not_found(async_client):
    uid = str(uuid.uuid4())[:8]
    token = await register_and_login(async_client, f"JoinNF_{uid}")
    res = await async_client.post("/rooms/XXXXX/join", json={}, headers=auth(token))
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_join_room_full(async_client):
    uid = str(uuid.uuid4())[:8]
    t1 = await register_and_login(async_client, f"FullHost_{uid}")
    t2 = await register_and_login(async_client, f"FullG1_{uid}")
    t3 = await register_and_login(async_client, f"FullG2_{uid}")
    res = await async_client.post("/rooms", json={"max_players": 2}, headers=auth(t1))
    room_code = res.json()["room_code"]
    await async_client.post(f"/rooms/{room_code}/join", json={}, headers=auth(t2))
    res = await async_client.post(f"/rooms/{room_code}/join", json={}, headers=auth(t3))
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_start_room(async_client):
    uid = str(uuid.uuid4())[:8]
    t1 = await register_and_login(async_client, f"StartH_{uid}")
    t2 = await register_and_login(async_client, f"StartG_{uid}")
    res = await async_client.post("/rooms", json={"max_players": 2}, headers=auth(t1))
    room_code = res.json()["room_code"]
    await async_client.post(f"/rooms/{room_code}/join", json={}, headers=auth(t2))
    res = await async_client.post(f"/rooms/{room_code}/start", json={}, headers=auth(t1))
    assert res.status_code == 200
    assert res.json()["state"]["phase"] == "playing"


@pytest.mark.asyncio
async def test_start_room_not_enough_players(async_client):
    uid = str(uuid.uuid4())[:8]
    token = await register_and_login(async_client, f"Alone1_{uid}")
    res = await async_client.post("/rooms", json={"max_players": 3}, headers=auth(token))
    room_code = res.json()["room_code"]
    res = await async_client.post(f"/rooms/{room_code}/start", json={}, headers=auth(token))
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_abort_room(async_client):
    uid = str(uuid.uuid4())[:8]
    token = await register_and_login(async_client, f"AbortH_{uid}")
    res = await async_client.post("/rooms", json={"max_players": 3}, headers=auth(token))
    room_code = res.json()["room_code"]
    res = await async_client.post(f"/rooms/{room_code}/abort", headers=auth(token))
    assert res.status_code == 200
    state = (await async_client.get(f"/rooms/{room_code}/state")).json()["state"]
    assert state["phase"] == "aborted"


@pytest.mark.asyncio
async def test_draw_card(async_client):
    room_code, tokens = await setup_game(async_client)
    state = (await async_client.get(f"/rooms/{room_code}/state")).json()["state"]
    current = state["current_turn"]
    res = await async_client.post(f"/rooms/{room_code}/draw", json={}, headers=auth(tokens[current]))
    assert res.status_code == 200
    assert "card" in res.json()
    assert res.json()["state"]["pending_card"] is not None


@pytest.mark.asyncio
async def test_draw_card_not_your_turn(async_client):
    room_code, tokens = await setup_game(async_client)
    state = (await async_client.get(f"/rooms/{room_code}/state")).json()["state"]
    player_names = list(tokens.keys())
    wrong = [p for p in player_names if p != state["current_turn"]][0]
    res = await async_client.post(f"/rooms/{room_code}/draw", json={}, headers=auth(tokens[wrong]))
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_draw_twice_without_place(async_client):
    room_code, tokens = await setup_game(async_client)
    state = (await async_client.get(f"/rooms/{room_code}/state")).json()["state"]
    current = state["current_turn"]
    await async_client.post(f"/rooms/{room_code}/draw", json={}, headers=auth(tokens[current]))
    res = await async_client.post(f"/rooms/{room_code}/draw", json={}, headers=auth(tokens[current]))
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_place_card(async_client):
    room_code, tokens = await setup_game(async_client)
    state = (await async_client.get(f"/rooms/{room_code}/state")).json()["state"]
    current = state["current_turn"]
    await async_client.post(f"/rooms/{room_code}/draw", json={}, headers=auth(tokens[current]))
    res = await async_client.post(f"/rooms/{room_code}/place", json={"row_index": 0}, headers=auth(tokens[current]))
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_place_without_draw(async_client):
    room_code, tokens = await setup_game(async_client)
    state = (await async_client.get(f"/rooms/{room_code}/state")).json()["state"]
    current = state["current_turn"]
    res = await async_client.post(f"/rooms/{room_code}/place", json={"row_index": 0}, headers=auth(tokens[current]))
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_take_row(async_client):
    room_code, tokens = await setup_game(async_client)
    state = (await async_client.get(f"/rooms/{room_code}/state")).json()["state"]
    current = state["current_turn"]
    await async_client.post(f"/rooms/{room_code}/draw", json={}, headers=auth(tokens[current]))
    await async_client.post(f"/rooms/{room_code}/place", json={"row_index": 0}, headers=auth(tokens[current]))
    state = (await async_client.get(f"/rooms/{room_code}/state")).json()["state"]
    next_player = state["current_turn"]
    res = await async_client.post(f"/rooms/{room_code}/take-row", json={"row_index": 0}, headers=auth(tokens[next_player]))
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_leave_room(async_client):
    room_code, tokens = await setup_game(async_client)
    player_names = list(tokens.keys())
    res = await async_client.post(f"/rooms/{room_code}/leave", json={}, headers=auth(tokens[player_names[0]]))
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_leave_room_aborts_game(async_client):
    room_code, tokens = await setup_game(async_client)
    player_names = list(tokens.keys())
    await async_client.post(f"/rooms/{room_code}/leave", json={}, headers=auth(tokens[player_names[0]]))
    await async_client.post(f"/rooms/{room_code}/leave", json={}, headers=auth(tokens[player_names[1]]))
    state = (await async_client.get(f"/rooms/{room_code}/state")).json()["state"]
    assert state["phase"] == "aborted"


@pytest.mark.asyncio
async def test_observe_room(async_client):
    room_code, tokens = await setup_game(async_client)
    uid = str(uuid.uuid4())[:8]
    t = await register_and_login(async_client, f"Spectator1_{uid}")
    res = await async_client.post(f"/rooms/{room_code}/observe", json={}, headers=auth(t))
    assert res.status_code == 200
    assert f"Spectator1_{uid}" in res.json()["state"]["observers"]


@pytest.mark.asyncio
async def test_observe_room_full(async_client):
    room_code, tokens = await setup_game(async_client)
    uid = str(uuid.uuid4())[:8]
    for i in range(1, 5):
        t = await register_and_login(async_client, f"Spec{i}_{uid}")
        await async_client.post(f"/rooms/{room_code}/observe", json={}, headers=auth(t))
    t5 = await register_and_login(async_client, f"Spec5_{uid}")
    res = await async_client.post(f"/rooms/{room_code}/observe", json={}, headers=auth(t5))
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_observe_room_already_player(async_client):
    room_code, tokens = await setup_game(async_client)
    player_names = list(tokens.keys())
    res = await async_client.post(f"/rooms/{room_code}/observe", json={}, headers=auth(tokens[player_names[0]]))
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_sequence_number_increases_on_draw(async_client):
    room_code, tokens = await setup_game(async_client)
    state_before = (await async_client.get(f"/rooms/{room_code}/state")).json()["state"]
    seq_before = state_before["sequence_number"]
    current = state_before["current_turn"]
    await async_client.post(f"/rooms/{room_code}/draw", json={}, headers=auth(tokens[current]))
    state_after = (await async_client.get(f"/rooms/{room_code}/state")).json()["state"]
    assert state_after["sequence_number"] > seq_before


@pytest.mark.asyncio
async def test_sequence_number_increases_on_leave(async_client):
    room_code, tokens = await setup_game(async_client)
    state_before = (await async_client.get(f"/rooms/{room_code}/state")).json()["state"]
    seq_before = state_before["sequence_number"]
    player_names = list(tokens.keys())
    await async_client.post(f"/rooms/{room_code}/leave", json={}, headers=auth(tokens[player_names[0]]))
    state_after = (await async_client.get(f"/rooms/{room_code}/state")).json()["state"]
    assert state_after["sequence_number"] > seq_before
