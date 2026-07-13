import os
import json
import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool, Redis
from typing import Optional
from urllib.parse import urlsplit, urlunsplit

from backend.models import GameState
from backend.serializers import serialize_gamestate, deserialize_gamestate

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

if os.getenv("TESTING") == "1":
    # Route tests to a separate Redis logical DB (1) instead of the default
    # (0) used by dev/prod, so pytest runs never create/touch rooms visible
    # in the runing app. Overrides any db number already in REDIS_URL.
    parts = urlsplit(REDIS_URL)
    REDIS_URL = urlunsplit(parts._replace(path="/1"))

GAME_TTL = 60 * 60 * 24  # 24 ore

class RedisManager:
    
    _instance: Optional["RedisManager"] = None
    _pool: Optional[ConnectionPool] = None
    _client: Optional[Redis] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self) -> Redis:

        if self._client is not None:
            return self._client
        
        try:
        
            self._pool = ConnectionPool.from_url(
                REDIS_URL,
       
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,
                    2: 1,
                    3: 3,
                } if os.name == 'nt' else None,
                
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
                
                max_connections=10,
                
                retry_on_timeout=True,
                
                decode_responses=True,
            )
            

            self._client = Redis(connection_pool=self._pool)
            

            await self._client.ping()
            print("[Redis] Connection pool initialized and verified")
            
        except Exception as e:
            await self.disconnect()
            raise RuntimeError(f"Failed to connect to Redis: {e}")
        
        return self._client
    
    async def disconnect(self) -> None:

        if self._client is None:
            return
        
        try:

            await self._client.aclose(close_connection_pool=True)
            print("[Redis] Connection pool closed successfully")
        except Exception as e:
            print(f"[Redis] Warning during disconnect: {e}")
        finally:
            self._client = None
            self._pool = None
    
    async def get_client(self) -> Redis:

        if self._client is None:
            return await self.initialize()
        return self._client


_manager = RedisManager()


async def init_redis() -> Redis:

    return await _manager.initialize()


async def close_redis() -> None:

    await _manager.disconnect()


async def get_redis_client() -> Redis:

    global redis_client
    if redis_client is not None:
        return redis_client
    if _manager._client is None:
        return await _manager.initialize()
    return _manager._client


redis_client = None


async def _set_redis_client(client: Redis) -> None:

    global redis_client
    redis_client = client
    _manager._client = client  

def _key(room_code: str) -> str:
    """Helper: Build Redis key for a room."""
    return f"game:{room_code}"


async def _repair_from_postgres(room_code: str) -> GameState | None:
    # Cache-aside fallback: restore from Postgres if Redis lost data, repopulate cache
    from backend.database import load_game

    state = await load_game(room_code)
    if state is None:
        return None

    client = await get_redis_client()
    data = json.dumps(serialize_gamestate(state))
    await client.set(_key(room_code), data, ex=GAME_TTL)
    print(f"[Redis] Repaired room {room_code} from Postgres after cache miss")
    return state


async def redis_only_exists(room_code: str) -> bool:
# Check Redis only (no repair); used by lifespan to avoid double-restoration
    
    client = await get_redis_client()
    return await client.exists(_key(room_code)) == 1


async def get_game(room_code: str) -> GameState | None:

    client = await get_redis_client()
    data = await client.get(_key(room_code))
    if data is None:
        return await _repair_from_postgres(room_code)
    return deserialize_gamestate(json.loads(data))


async def set_game(room_code: str, state: GameState) -> None:

    client = await get_redis_client()
    data = json.dumps(serialize_gamestate(state))
    await client.set(_key(room_code), data, ex=GAME_TTL)


async def delete_game(room_code: str) -> None:

    client = await get_redis_client()
    await client.delete(_key(room_code))


async def game_exists(room_code: str) -> bool:

    client = await get_redis_client()
    if await client.exists(_key(room_code)) == 1:
        return True
    state = await _repair_from_postgres(room_code)
    return state is not None


async def get_all_game_keys() -> list[str]:

    client = await get_redis_client()
    keys = await client.keys("game:*")
    return [k.replace("game:", "") for k in keys]
