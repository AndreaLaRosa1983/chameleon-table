from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, String, JSON, DateTime
from datetime import datetime, timezone
from dataclasses import asdict
from dacite import from_dict, Config
from backend.models import GameState
from enum import Enum


def deserialize_gamestate(data: dict) -> GameState:
    return from_dict(
        data_class=GameState,
        data=data,
        config=Config(cast=[Enum])
    )
DATABASE_URL = "postgresql+asyncpg://chameleon:chameleon@localhost:5432/chameleon"

engine = create_async_engine(DATABASE_URL, echo=True)

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
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

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