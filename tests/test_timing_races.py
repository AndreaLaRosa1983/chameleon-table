# Timing / race condition tests.
# Adjust the import below if your integration tests import helpers differently
# (e.g. "from conftest import ..." instead of "from tests.conftest import ...").

import asyncio
import uuid
import pytest
import pytest_asyncio

import backend.state as state_module
from tests.conftest import setup_game, auth

# Unique per pytest run, so player names never collide with leftover Redis
# state from a PREVIOUS run (Redis is not flushed between test sessions).
RUN_ID = uuid.uuid4().hex[:8]


# Shrinks INACTIVITY_TIMEOUT to 1s for a single test, so timing tests run in
# seconds instead of minutes. Patches the module attribute directly, since
# handle_inactivity/handle_disconnection read it as a global at call time.
@pytest_asyncio.fixture
async def fast_timeout(monkeypatch):
    monkeypatch.setattr(state_module, "INACTIVITY_TIMEOUT", 1)
    monkeypatch.setattr(state_module, "GRACE_PERIOD_TIMEOUT", 1)
    yield


@pytest.mark.asyncio
async def test_inactivity_full_cycle_does_not_self_cancel(async_client, fast_timeout):
    # Regression test for the self-cancel bug: handle_inactivity used to cancel
    # its own task via advance_sequence -> reset_inactivity_timer, so the match
    # stayed stuck in "playing" forever. With a 1s timeout and nobody acting,
    # the match should reach ABORTED within a few seconds if the fix holds.
    room_code, tokens = await setup_game(async_client, players=[f"TimingAlice1_{RUN_ID}", f"TimingBob1_{RUN_ID}"], max_players=2)

    await asyncio.sleep(3.5)

    res = await async_client.get(f"/rooms/{room_code}/state")
    state = res.json()["state"]

    assert state["phase"] == "aborted", f"expected aborted, got {state['phase']!r}"

    starter = state["turn_order"][0]
    starter_player = next(p for p in state["players"] if p["name"] == starter)
    assert starter_player["active"] is False


@pytest.mark.asyncio
async def test_concurrent_draw_only_current_turn_player_succeeds(async_client):
    # Two different players hit /draw at (almost) the same instant. Only the
    # current-turn player should succeed (200). The off-turn player is still a
    # real participant, so draw_card() rejects them with 400 ("not your turn"),
    # not 403 — 403 is reserved for users who aren't in the room at all.
    room_code, tokens = await setup_game(
        async_client, players=[f"TimingAlice2_{RUN_ID}", f"TimingBob2_{RUN_ID}", f"TimingCharlie2_{RUN_ID}"], max_players=3
    )

    res_before = await async_client.get(f"/rooms/{room_code}/state")
    state_before = res_before.json()["state"]
    current_turn = state_before["current_turn"]
    seq_before = state_before["sequence_number"]
    other_player = next(p for p in tokens if p != current_turn)

    results = await asyncio.gather(
        async_client.post(f"/rooms/{room_code}/draw", json={}, headers=auth(tokens[current_turn])),
        async_client.post(f"/rooms/{room_code}/draw", json={}, headers=auth(tokens[other_player])),
    )

    statuses = sorted(r.status_code for r in results)
    assert statuses == [200, 400], f"expected [200, 400], got {statuses}"

    res_after = await async_client.get(f"/rooms/{room_code}/state")
    seq_after = res_after.json()["state"]["sequence_number"]
    assert seq_after == seq_before + 1


@pytest.mark.asyncio
async def test_action_before_deadline_resets_timer(async_client, fast_timeout):
    # Player acts just before their inactivity deadline. The action should
    # reset the timer (advance_sequence -> reset_inactivity_timer -> fresh
    # start_inactivity_timer), pushing the real deadline further out. Total
    # elapsed time by the end of this test exceeds the ORIGINAL 1s window, but
    # the player must still be active — proving the reset actually happened
    # against real wall-clock time, not just in theory.
    room_code, tokens = await setup_game(async_client, players=[f"TimingAlice4_{RUN_ID}", f"TimingBob4_{RUN_ID}"], max_players=2)

    res = await async_client.get(f"/rooms/{room_code}/state")
    current_turn = res.json()["state"]["current_turn"]

    await asyncio.sleep(0.7)  # close to the 1s deadline, but not past it yet

    res = await async_client.post(
        f"/rooms/{room_code}/draw", json={}, headers=auth(tokens[current_turn])
    )
    assert res.status_code == 200

    await asyncio.sleep(0.7)  # total elapsed ~1.4s, past the ORIGINAL deadline

    res = await async_client.get(f"/rooms/{room_code}/state")
    state = res.json()["state"]

    assert state["phase"] == "playing", "match aborted even though the player acted before the deadline"
    player = next(p for p in state["players"] if p["name"] == current_turn)
    assert player["active"] is True, "player was marked inactive despite acting in time"


@pytest.mark.asyncio
async def test_concurrent_double_draw_same_player(async_client):
    # Simulates a double-click: same player fires two /draw requests almost
    # simultaneously. The room lock should serialize them — one succeeds, the
    # other is rejected for an already-pending card.
    room_code, tokens = await setup_game(async_client, players=[f"TimingAlice3_{RUN_ID}", f"TimingBob3_{RUN_ID}"], max_players=2)

    res = await async_client.get(f"/rooms/{room_code}/state")
    current_turn = res.json()["state"]["current_turn"]

    results = await asyncio.gather(
        async_client.post(f"/rooms/{room_code}/draw", json={}, headers=auth(tokens[current_turn])),
        async_client.post(f"/rooms/{room_code}/draw", json={}, headers=auth(tokens[current_turn])),
    )

    statuses = sorted(r.status_code for r in results)
    assert statuses == [200, 400], f"expected [200, 400], got {statuses}"

    res_after = await async_client.get(f"/rooms/{room_code}/state")
    assert res_after.json()["state"]["pending_card"] is not None


@pytest.mark.asyncio
async def test_turn_started_at_stable_across_reads(async_client):
    # Reading state repeatedly must not change turn_started_at — it should
    # only move when the turn actually changes hands. Also verifies it DOES
    # advance once a full draw+place cycle completes the turn.
    room_code, tokens = await setup_game(async_client, players=[f"TimingAlice5_{RUN_ID}", f"TimingBob5_{RUN_ID}"], max_players=2)

    res1 = await async_client.get(f"/rooms/{room_code}/state")
    state1 = res1.json()["state"]
    current_turn = state1["current_turn"]
    started_at_1 = state1["turn_started_at"]

    await asyncio.sleep(0.2)

    res2 = await async_client.get(f"/rooms/{room_code}/state")
    started_at_2 = res2.json()["state"]["turn_started_at"]

    assert started_at_1 == started_at_2, "turn_started_at changed with no action taken, just from reading state"

    res = await async_client.post(
        f"/rooms/{room_code}/draw", json={}, headers=auth(tokens[current_turn])
    )
    assert res.status_code == 200
    res = await async_client.post(
        f"/rooms/{room_code}/place", json={"row_index": 0}, headers=auth(tokens[current_turn])
    )
    assert res.status_code == 200

    state_after = res.json()["state"]
    assert state_after["current_turn"] != current_turn, "turn should have passed to the other player"
    assert state_after["turn_started_at"] > started_at_1, "turn_started_at should advance once the turn changes"


@pytest.mark.asyncio
async def test_cascading_timeouts_three_players(async_client, fast_timeout):
    # 3 players, nobody acts at all. Timeouts should cascade player by player
    # (inactivity -> disconnection -> next player's inactivity -> ...) without
    # ever getting stuck, eventually reaching ABORTED once too few remain active.
    room_code, tokens = await setup_game(
        async_client, players=[f"TimingAlice6_{RUN_ID}", f"TimingBob6_{RUN_ID}", f"TimingCharlie6_{RUN_ID}"], max_players=3
    )

    res = await async_client.get(f"/rooms/{room_code}/state")
    first_turn_player = res.json()["state"]["current_turn"]

    # Enough time for at least two full inactivity+disconnection cycles
    # (1s inactivity + 1s disconnection) x2, with margin for scheduling jitter.
    await asyncio.sleep(5)

    res = await async_client.get(f"/rooms/{room_code}/state")
    state = res.json()["state"]

    assert state["phase"] == "aborted", f"expected aborted after cascading timeouts, got {state['phase']!r}"

    first_player = next(p for p in state["players"] if p["name"] == first_turn_player)
    assert first_player["active"] is False, "the first player to time out should be inactive"