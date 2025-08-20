import redis
import json
from langchain.cache import RedisCache
from langchain.globals import set_llm_cache
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_redis import RedisChatMessageHistory

import os
from dotenv import load_dotenv
load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
REDIS_SESSION_TTL = os.getenv("REDIS_SESSION_TTL")

redis_client = redis.Redis.from_url(REDIS_URL)
set_llm_cache(RedisCache(redis_client))

# Function to get or create a RedisChatMessageHistory instance
def get_redis_history(session_id: str) -> BaseChatMessageHistory:
    return RedisChatMessageHistory(session_id, redis_url=REDIS_URL, ttl=REDIS_SESSION_TTL)

def save_session(session_id: str, data: dict):
    redis_client.set(session_id, json.dumps(data))

def get_session(session_id: str) -> dict | None:
    value = redis_client.get(session_id)
    return json.loads(value) if value else None





