import redis
from langchain_community.cache import RedisCache
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
    """Obtiene el historial de chat con prefijo organizado y TTL configurado"""
    
    return RedisChatMessageHistory(
        session_id=session_id,
        redis_url=REDIS_URL,
        ttl=REDIS_SESSION_TTL
    )

def clear_redis_history(session_id: str) -> bool:
    """Limpia completamente todas las entradas de Redis relacionadas con una sesión"""
    try:
        # Obtener el historial
        history = get_redis_history(session_id)
        history.clear()
        
        return True
        
    except Exception as e:
        print(f"ERROR clearing session completely: {e}")
        return False


