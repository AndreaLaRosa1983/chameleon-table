# Plays a full 3-player match end-to-end through the real REST API. No
# strategy: rows are picked greedily just to reach a terminal phase. This
# exercises the whole turn/round/scoring pipeline over a long sequence of
# moves, including the "all rows full, must take a row" scenario, which
# naturally occurs at some point during a real game.

import uuid
import pytest

from tests.conftest import setup_game, auth

RUN_ID = uuid.uuid4().hex[:8]
MAX_TURNS = 300


def _available_row_for_placement(rows):
    for i, r in enumerate(rows):
        if not r["taken_by"] and len(r["cards"]) < r["max_cards"]:
            return i
    return None


def _any_takeable_row(rows):
    for i, r in enumerate(rows):
        if not r["taken_by"] and len(r["cards"]) > 0:
            return i
    return None


@pytest.mark.asyncio
async def test_full_three_player_game_reaches_finished_with_scores(async_client):
    players = [f"FullGameA_{RUN_ID}", f"FullGameB_{RUN_ID}", f"FullGameC_{RUN_ID}"]
    room_code, tokens = await setup_game(async_client, players=players, max_players=3)
    print(f"\n[GAME] Room {room_code} created with players: {players}")

    turn_number = 0
    for _ in range(MAX_TURNS):
        res = await async_client.get(f"/rooms/{room_code}/state")
        state = res.json()["state"]

        if state["phase"] != "playing":
            print(f"[GAME] Match ended after {turn_number} actions — phase: {state['phase']}")
            break

        current_turn = state["current_turn"]
        assert current_turn is not None, "current_turn went None while phase is still playing"
        token = tokens[current_turn]
        turn_number += 1

        if state["pending_card"] is not None:
            row_index = _available_row_for_placement(state["rows"])
            assert row_index is not None, "pending card exists but no row can accept it"
            card = state["pending_card"]
            res = await async_client.post(
                f"/rooms/{room_code}/place", json={"row_index": row_index}, headers=auth(token)
            )
            assert res.status_code == 200, res.text
            print(f"[GAME] #{turn_number} {current_turn}: place {card.get('color') or card['card_type']} on row {row_index}")
            continue

        row_index = _available_row_for_placement(state["rows"])
        if row_index is not None:
            res = await async_client.post(f"/rooms/{room_code}/draw", json={}, headers=auth(token))
            assert res.status_code == 200, res.text
            drawn = res.json()["card"]
            print(f"[GAME] #{turn_number} {current_turn}: draw -> {drawn.get('color') or drawn['card_type']}")
        else:
            row_index = _any_takeable_row(state["rows"])
            assert row_index is not None, "no row available to draw into and none takeable either"
            row_cards = [c.get("color") or c["card_type"] for c in state["rows"][row_index]["cards"]]
            res = await async_client.post(
                f"/rooms/{room_code}/take-row", json={"row_index": row_index}, headers=auth(token)
            )
            assert res.status_code == 200, res.text
            print(f"[GAME] #{turn_number} {current_turn}: take row {row_index} ({row_cards})")
    else:
        pytest.fail(f"game did not reach a terminal phase within {MAX_TURNS} turns")

    res = await async_client.get(f"/rooms/{room_code}/state")
    final_state = res.json()["state"]
    assert final_state["phase"] == "finished", f"expected finished, got {final_state['phase']!r}"

    res = await async_client.get(f"/rooms/{room_code}/scores")
    assert res.status_code == 200
    scores = res.json()
    print(f"[GAME] Final scores: {scores}")
    assert set(scores.keys()) == set(players)