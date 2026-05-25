from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool
from sqlalchemy import Column, String, JSON, DateTime, select
from datetime import datetime, timezone
from dataclasses import asdict
from dacite import from_dict, Config
from backend.models import GameState
from enum import Enum
import os
def deserialize_gamestate(data: dict) -> GameState:
    return from_dict(
        data_class=GameState,
        data=data,
        config=Config(cast=[Enum])
    )
    
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://chameleon:password@localhost:5432/chameleon"
)

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

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
def enum_handler(data):
    return {
        k: v.value if isinstance(v, Enum) else v
        for k, v in data
    }

def serialize_gamestate(state: GameState) -> dict:
    return asdict(state, dict_factory=enum_handler)

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



