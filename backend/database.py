from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool
from sqlalchemy import Column, String, JSON, DateTime, select
from datetime import datetime, timezone
from backend.models import GameState
from backend.serializers import serialize_gamestate, deserialize_gamestate
from urllib.parse import urlsplit, urlunsplit
import asyncpg
import os
    
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://chameleon:password@localhost:5432/chameleon"
)

if os.getenv("TESTING") == "1":
    # Separate test DB (not just pool) to isolate pytest's DROP TABLE/DELETE FROM dev data; overrides DATABASE_URL
    parts = urlsplit(DATABASE_URL)
    DATABASE_URL = urlunsplit(parts._replace(path="/chameleon_test"))

if os.getenv("TESTING") == "1":
    kwargs = {"poolclass": NullPool}
else:
    kwargs = {}

engine = create_async_engine(DATABASE_URL, echo=False, **kwargs)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

class GameRecord(Base):
    __tablename__ = "games"
    
    room_code = Column(String, primary_key=True)
    state_json = Column(JSON, nullable=False)
    phase = Column(String, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class UserRecord(Base):
    __tablename__ = "users"
    
    username = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


async def ensure_test_database_exists():
    
    # Create test DB if missing, connects to postgres admin DB
    
    parsed = urlsplit(DATABASE_URL)
    admin_dsn = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"

    conn = await asyncpg.connect(admin_dsn)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = 'chameleon_test'"
        )
        if not exists:
            await conn.execute("CREATE DATABASE chameleon_test")
            print("[Test Setup] Created chameleon_test database")
    finally:
        await conn.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def room_code_exists(room_code: str) -> bool:
    async with AsyncSessionLocal() as session:
        existing = await session.get(GameRecord, room_code)
        return existing is not None
    
async def load_active_games() -> list[GameState]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(GameRecord).where(GameRecord.phase == "playing")
        )
        records = result.scalars().all()
        return [deserialize_gamestate(record.state_json) for record in records]


async def load_game(room_code: str) -> GameState | None:
    # Cache-aside fallback: load state from Postgres if Redis lost data.
    async with AsyncSessionLocal() as session:
        record = await session.get(GameRecord, room_code)
        if record is None:
            return None
        return deserialize_gamestate(record.state_json)

    
async def save_game(room_code: str, state: GameState):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            existing = await session.get(GameRecord, room_code)
            if existing:
                existing.state_json = serialize_gamestate(state)
                existing.phase = state.phase.value
                existing.updated_at = datetime.now(timezone.utc)
            else:
                session.add(GameRecord(
                    room_code=room_code,
                    state_json=serialize_gamestate(state),
                    phase=state.phase.value
                ))

async def get_user(username: str) -> UserRecord | None:
    async with AsyncSessionLocal() as session:
        return await session.get(UserRecord, username)

async def create_user(username: str, email: str, hashed_password: str) -> UserRecord:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            user = UserRecord(
                username=username,
                email=email,
                hashed_password=hashed_password
            )
            session.add(user)
            return user