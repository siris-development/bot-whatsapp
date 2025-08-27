import redis
from langchain.cache import RedisCache
from langchain.globals import set_llm_cache
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_redis import RedisChatMessageHistory

import os
from dotenv import load_dotenv
load_dotenv()

REDIS_URL = os.getenv("REDIS_URL_PROD")
REDIS_SESSION_TTL = os.getenv("REDIS_SESSION_TTL")

redis_client = redis.Redis.from_url(REDIS_URL)
set_llm_cache(RedisCache(redis_client))

def get_redis_history(session_id: str) -> BaseChatMessageHistory:
    return RedisChatMessageHistory(session_id, redis_url=REDIS_URL, ttl=REDIS_SESSION_TTL)




