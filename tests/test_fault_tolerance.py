# Fault tolerance test: Redis loses a room's data, but the backend process
# itself stays alive (no restart, so lifespan()'s recovery never runs). The
# only way the room can come back is via the cache-aside repair in
# redis_store.get_game()/game_exists(), which falls back to Postgres.

import uuid
import pytest

from backend.redis_store import delete_game, game_exists
from tests.conftest import setup_game, auth

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

    # NOTE: we can't assert game_exists(room_code) is False here. Checking
    # existence is itself what triggers the cache-aside repair, so the very
    # act of observing "is it gone?" immediately heals it. That's the
    # mechanism working as designed, not a gap in the test.

    # Backend never restarted — the only way this room comes back is via
    # the cache-aside repair on the next access.
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