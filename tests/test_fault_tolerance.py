# Fault tolerance test: Redis loses a room's data, but the backend process
# itself stays alive (no restart, so lifespan()'s recovery never runs). The
# only way the room can come back is via the cache-aside repair in
# redis_store.get_game()/game_exists(), which falls back to Postgres.

import uuid
import pytest

from backend.redis_store import delete_game, game_exists, get_game, set_game
from tests.conftest import make_game_state_for_draw_card, setup_game, auth
from backend.database import save_game
from backend.state import reload_playing_games_from_postgres
RUN_ID = uuid.uuid4().hex[:8]


@pytest.mark.asyncio
async def test_redis_repairs_room_from_postgres_after_data_loss(async_client):
    room_code, tokens = await setup_game(
        async_client, players=[f"FaultAlice_{RUN_ID}", f"FaultBob_{RUN_ID}"], max_players=2
    )

    # Sanity check: room is live in Redis right after creation.
    assert await game_exists(room_code) is True

    # Simulate Redis losing this room's data outright (e.g. crash without
    # a completed RDB save).
    await delete_game(room_code)

    res = await async_client.get(f"/rooms/{room_code}/state")
    assert res.status_code == 200, "expected the room to be repaired from Postgres, not 404"

    state = res.json()["state"]
    assert state["room_code"] == room_code
    player_names = {p["name"] for p in state["players"]}
    assert player_names == {f"FaultAlice_{RUN_ID}", f"FaultBob_{RUN_ID}"}

    # The repair should have repopulated Redis, so subsequent reads hit the
    # fast path again instead of Postgres every time.
    assert await game_exists(room_code) is True

    # A real game action should work normally post-repair — proving the
    # repaired state is fully usable, not just readable.
    current_turn = state["current_turn"]
    res = await async_client.post(
        f"/rooms/{room_code}/draw", json={}, headers=auth(tokens[current_turn])
    )
    assert res.status_code == 200
    
    
@pytest.mark.asyncio
async def test_reload_playing_games_from_postgres_overwrites_stale_redis():
    room_code = "RECOVR"

    # Stale state in Redis: simulates old RDB sapshot after Redis restart
    stale_state = make_game_state_for_draw_card()
    stale_state.room_code = room_code
    stale_state.round_starter = "Bob"
    await set_game(room_code, stale_state)

    # Fresh state in Postgres: what should win after recovery
    fresh_state = make_game_state_for_draw_card()
    fresh_state.room_code = room_code
    fresh_state.round_starter = "Charlie"
    await save_game(room_code, fresh_state)

    await reload_playing_games_from_postgres()

    result = await get_game(room_code)
    assert result is not None
    assert result.round_starter == "Charlie"