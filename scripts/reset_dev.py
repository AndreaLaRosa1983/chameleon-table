import asyncio
from backend.database import engine
from sqlalchemy import text
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def reset():
    print("Resetting database...")
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM games"))
    print("Database cleared!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset())