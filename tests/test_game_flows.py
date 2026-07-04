# Fast integration tests for core game flows: voluntary leave, abort via
# explicit leaves (not the inactivity timeout path), and observer access.

import uuid
import pytest

from tests.conftest import setup_game, auth, register_and_login

# Unique per pytest run, so player names never collide with leftover Redis
# state from a PREVIOUS run (Redis is not flushed between test sessions).
RUN_ID = uuid.uuid4().hex[:8]


@pytest.mark.asyncio
async def test_leave_mid_game_others_continue(async_client):
    # One player leaves voluntarily out of 3. The match should stay PLAYING
    # (only 1 of 3 dropped), the leaver is marked inactive, the others aren't.
    room_code, tokens = await setup_game(
        async_client, players=[f"FlowLeaveA_{RUN_ID}", f"FlowLeaveB_{RUN_ID}", f"FlowLeaveC_{RUN_ID}"], max_players=3
    )

    res = await async_client.post(
        f"/rooms/{room_code}/leave", json={}, headers=auth(tokens[f"FlowLeaveB_{RUN_ID}"])
    )
    assert res.status_code == 200
    state = res.json()["state"]

    assert state["phase"] == "playing"
    players_by_name = {p["name"]: p for p in state["players"]}
    assert players_by_name[f"FlowLeaveB_{RUN_ID}"]["active"] is False
    assert players_by_name[f"FlowLeaveA_{RUN_ID}"]["active"] is True
    assert players_by_name[f"FlowLeaveC_{RUN_ID}"]["active"] is True


@pytest.mark.asyncio
async def test_abort_when_enough_players_leave(async_client):
    # 3-player match: 2 players leave one after another. Only 1 active player
    # remains, which should push the match into ABORTED.
    room_code, tokens = await setup_game(
        async_client, players=[f"FlowAbortA_{RUN_ID}", f"FlowAbortB_{RUN_ID}", f"FlowAbortC_{RUN_ID}"], max_players=3
    )

    await async_client.post(f"/rooms/{room_code}/leave", json={}, headers=auth(tokens[f"FlowAbortB_{RUN_ID}"]))
    res = await async_client.post(
        f"/rooms/{room_code}/leave", json={}, headers=auth(tokens[f"FlowAbortC_{RUN_ID}"])
    )
    assert res.status_code == 200
    state = res.json()["state"]

    assert state["phase"] == "aborted", f"expected aborted with only 1 active player left, got {state['phase']!r}"


@pytest.mark.asyncio
async def test_observer_can_view_but_not_act(async_client):
    # A non-participant joins as observer: they should show up in the state,
    # be able to read it, but be rejected (403) on any player action.
    room_code, tokens = await setup_game(
        async_client, players=[f"FlowObsA_{RUN_ID}", f"FlowObsB_{RUN_ID}", f"FlowObsC_{RUN_ID}"], max_players=3
    )

    watcher_token = await register_and_login(async_client, f"FlowWatcher_{RUN_ID}")

    res = await async_client.post(
        f"/rooms/{room_code}/observe", json={}, headers=auth(watcher_token)
    )
    assert res.status_code == 200
    state = res.json()["state"]
    assert f"FlowWatcher_{RUN_ID}" in state["observers"]

    # Anyone can read room state, no auth required.
    res = await async_client.get(f"/rooms/{room_code}/state")
    assert res.status_code == 200

    # But an observer isn't a player: any game action must be rejected.
    res = await async_client.post(
        f"/rooms/{room_code}/draw", json={}, headers=auth(watcher_token)
    )
    assert res.status_code == 403

    res = await async_client.post(
        f"/rooms/{room_code}/take-row", json={"row_index": 0}, headers=auth(watcher_token)
    )
    assert res.status_code == 403