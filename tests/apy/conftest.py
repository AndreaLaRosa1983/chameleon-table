import os
os.environ["TESTING"] = "1"

import pytest_asyncio
from sqlalchemy import text
from backend.database import engine, init_db

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS games"))
    await engine.dispose()

@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    yield
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM games"))