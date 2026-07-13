import os
os.environ["TESTING"] = "1"

import asyncio
import pytest
import pytest_asyncio
from sqlalchemy import text
from httpx import AsyncClient, ASGITransport
from backend.database import engine, init_db, ensure_test_database_exists
from backend.main import app
from backend.models import CardType, CardColor, Player, GameState, GamePhase, Row, Card

@pytest_asyncio.fixture(scope="session", autouse=True)
async def manage_redis_lifecycle():
    
    from backend.redis_store import init_redis, close_redis, _set_redis_client
    
    try:
        redis_client = await init_redis()
        await _set_redis_client(redis_client)
        print("\n[Test Setup] Redis pool initialized")
    except Exception as e:
        print(f"\n[Test Setup] Warning: Redis not available: {e}")
        yield
        return
    
    yield
    
    try:
        await close_redis()
        print("\n[Test Teardown] Redis pool closed cleanly")
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            print(f"\n[Test Teardown] Event loop already closing (expected on Windows)")
        else:
            print(f"\n[Test Teardown] Redis cleanup error: {e}")
    except Exception as e:
        print(f"\n[Test Teardown] Redis cleanup warning: {e}")


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    """Initialize database schema at start of test session."""
    await ensure_test_database_exists()
    await init_db()
    yield
    # Cleanup after all tests
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS games"))
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    """Clean games and users tables between tests."""
    yield
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM games"))
        await conn.execute(text("DELETE FROM users"))


@pytest_asyncio.fixture
async def async_client():
    """AsyncClient with ASGI transport for FastAPI."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


async def register_and_login(
    async_client: AsyncClient,
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


def auth(token: str) -> dict:
    """Helper to build Authorization header."""
    return {"Authorization": f"Bearer {token}"}


async def setup_game(
    async_client: AsyncClient,
    players: list[str] = ["Alice", "Bob", "Charlie"],
    max_players: int = 3
) -> tuple[str, dict]:
    """
    Register players, create a room, join and start.
    Returns (room_code, tokens_dict)
    """
    # Register and login all players
    tokens = {}
    for p in players:
        tokens[p] = await register_and_login(async_client, p)
    
    # Create room
    res = await async_client.post(
        "/rooms",
        json={"max_players": max_players},
        headers=auth(tokens[players[0]])
    )
    room_code = res.json()["room_code"]
    
    # Join room
    for p in players[1:]:
        await async_client.post(
            f"/rooms/{room_code}/join",
            json={},
            headers=auth(tokens[p])
        )
    
    # Start game
    await async_client.post(
        f"/rooms/{room_code}/start",
        json={},
        headers=auth(tokens[players[0]])
    )
    
    return room_code, tokens


def make_state(player_configs: list[dict]) -> GameState:
    """Helper: creates minimal GameState with players and turn_order"""
    players = []
    for cfg in player_configs:
        p = Player(name=cfg["name"])
        p.passed = cfg.get("passed", False)
        p.active = cfg.get("active", True)
        p.left = cfg.get("left", False)
        players.append(p)

    return GameState(
        room_code="TEST",
        players=players,
        turn_order=[cfg["name"] for cfg in player_configs]
    )


def make_game_state_for_take_row() -> GameState:
    """Helper: creates a GameState ready for take_row tests."""
    players = [
        Player(name="Alice"),
        Player(name="Bob"),
        Player(name="Charlie"),
    ]
    rows = [
        Row(cards=[Card(card_type=CardType.COLOR, color=CardColor.RED)]),
        Row(cards=[Card(card_type=CardType.COLOR, color=CardColor.BLUE)]),
        Row(cards=[Card(card_type=CardType.COLOR, color=CardColor.GREEN)]),
    ]
    return GameState(
        room_code="TEST",
        players=players,
        rows=rows,
        turn_order=["Alice", "Bob", "Charlie"],
        round_starter="Alice"
    )


def make_game_state_for_end_round(last_round: bool = False) -> GameState:
    """Helper: creates a GameState where all players have passed."""
    players = [
        Player(name="Alice", passed=True),
        Player(name="Bob", passed=True),
        Player(name="Charlie", passed=True),
    ]
    rows = [
        Row(cards=[], taken_by="Bob"),
        Row(cards=[], taken_by="Alice"),
        Row(cards=[], taken_by="Charlie"),
    ]
    return GameState(
        room_code="TEST",
        players=players,
        rows=rows,
        turn_order=["Alice", "Bob", "Charlie"],
        round_starter="Alice",
        last_row_taker="Charlie",
        last_round=last_round,
        phase=GamePhase.PLAYING
    )


def make_game_state_for_draw_card() -> GameState:
    """Helper: creates a GameState ready for draw_card tests."""
    players = [
        Player(name="Alice"),
        Player(name="Bob"),
        Player(name="Charlie"),
    ]
    rows = [
        Row(cards=[]),
        Row(cards=[]),
        Row(cards=[]),
    ]
    deck = [
        Card(card_type=CardType.COLOR, color=CardColor.RED),
        Card(card_type=CardType.COLOR, color=CardColor.BLUE),
        Card(card_type=CardType.COLOR, color=CardColor.GREEN),
    ]
    return GameState(
        room_code="TEST",
        players=players,
        rows=rows,
        deck=deck,
        turn_order=["Alice", "Bob", "Charlie"],
        round_starter="Alice",
        phase=GamePhase.PLAYING
    )


def make_game_state_for_place_card() -> GameState:
    """Helper: creates a GameState ready for place_card tests."""
    players = [
        Player(name="Alice"),
        Player(name="Bob"),
        Player(name="Charlie"),
    ]
    rows = [
        Row(cards=[]),
        Row(cards=[]),
        Row(cards=[]),
    ]
    return GameState(
        room_code="TEST",
        players=players,
        rows=rows,
        deck=[],
        turn_order=["Alice", "Bob", "Charlie"],
        round_starter="Alice",
        phase=GamePhase.PLAYING
    )


def make_players_for_calculate_score() -> list[Player]:
    """Helper: creates 3 players with realistic card distributions."""
    
    def make_color_cards(color: CardColor, count: int) -> list[Card]:
        return [Card(card_type=CardType.COLOR, color=color) for _ in range(count)]
    
    def make_plus2_cards(count: int) -> list[Card]:
        return [Card(card_type=CardType.PLUS2) for _ in range(count)]
    
    def make_joker_cards(count: int) -> list[Card]:
        return [Card(card_type=CardType.JOKER) for _ in range(count)]
    
    alice = Player(name="Alice")
    alice.cards = (
        make_color_cards(CardColor.BLUE, 5) +
        make_color_cards(CardColor.GREEN, 4) +
        make_color_cards(CardColor.RED, 3) +
        make_color_cards(CardColor.YELLOW, 1) +
        make_color_cards(CardColor.PURPLE, 1) +
        make_color_cards(CardColor.ORANGE, 1) +
        make_plus2_cards(3)
    )

    bob = Player(name="Bob")
    bob.cards = (
        make_color_cards(CardColor.YELLOW, 4) +
        make_color_cards(CardColor.RED, 3) +
        make_color_cards(CardColor.ORANGE, 3) +
        make_color_cards(CardColor.BLUE, 1) +
        make_color_cards(CardColor.GREEN, 1) +
        make_color_cards(CardColor.PURPLE, 2) +
        make_plus2_cards(3)
    )
    bob.jokers = make_joker_cards(1)

    charlie = Player(name="Charlie")
    charlie.cards = (
        make_color_cards(CardColor.PURPLE, 4) +
        make_color_cards(CardColor.GREEN, 3) +
        make_color_cards(CardColor.ORANGE, 3) +
        make_color_cards(CardColor.RED, 2) +
        make_color_cards(CardColor.BLUE, 1) +
        make_color_cards(CardColor.YELLOW, 1) +
        make_plus2_cards(3)
    )
    charlie.jokers = make_joker_cards(2)
    
    return [alice, bob, charlie]


def make_game_state_for_observers() -> GameState:
    """Helper: creates a GameState ready for observer tests."""
    players = [
        Player(name="Alice"),
        Player(name="Bob"),
        Player(name="Charlie"),
    ]
    return GameState(
        room_code="TEST",
        players=players,
        turn_order=["Alice", "Bob", "Charlie"],
        phase=GamePhase.WAITING
    )


def make_game_state_for_end_round_two_players() -> GameState:
    """Helper: creates a GameState for end_round tests with 2 players."""
    players = [
        Player(name="Alice", passed=True),
        Player(name="Bob", passed=True),
    ]
    rows = [
        Row(cards=[], taken_by="Alice", max_cards=1),
        Row(cards=[], taken_by="Bob", max_cards=2),
        Row(cards=[], taken_by=None, max_cards=3),
    ]
    return GameState(
        room_code="TEST",
        players=players,
        rows=rows,
        turn_order=["Alice", "Bob"],
        round_starter="Alice",
        last_row_taker="Bob",
        last_round=False,
        phase=GamePhase.PLAYING
    )