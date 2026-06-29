from dataclasses import asdict
from dacite import from_dict, Config
from backend.models import GameState
from enum import Enum

def enum_handler(data):
    return {
        k: v.value if isinstance(v, Enum) else v
        for k, v in data
    }

def serialize_gamestate(state: GameState) -> dict:
    return asdict(state, dict_factory=enum_handler)

def deserialize_gamestate(data: dict) -> GameState:
    return from_dict(
        data_class=GameState,
        data=data,
        config=Config(cast=[Enum])
    )