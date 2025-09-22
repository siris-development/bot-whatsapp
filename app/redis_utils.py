from dotenv import load_dotenv
import os
import redis
from typing import Callable
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

load_dotenv()

def get_redis_config() -> dict:
    """Get Redis configuration from environment variables"""

    return {
        "host": os.getenv("REDIS_HOST"),
        "port": int(os.getenv("REDIS_PORT", 6379)),  # Convert to int
        "password": os.getenv("REDIS_PASSWORD"),
        "db": int(os.getenv("REDIS_DB", 0)) if os.getenv("REDIS_DB") != "default" else 0,  # Handle "default" case
        "url": os.getenv("REDIS_URL") or os.getenv("REDIS_URL_PROD") or os.getenv("REDIS_URL_DEV"),
        "ttl": int(os.getenv("REDIS_TTL", 600))  # Default TTL to 600 seconds
    }

def test_redis_connection() -> bool:
    """Test Redis connection"""
    try:
        config = get_redis_config()
        r = redis.Redis(
            host=config["host"],
            port=config["port"],
            password=config["password"] if config["password"] else None,
            db=config["db"],
            decode_responses=True
        )
        r.ping()
        return True
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return False

def get_redis_url() -> str:
    """Get Redis URL for LangChain Redis components"""
    return get_redis_config()["url"]

def get_redis_ttl() -> int:
    """Get Redis TTL for LangChain Redis components"""
    return get_redis_config()["ttl"]

def get_redis_client() -> redis.Redis:
    """Get Redis client instance"""
    redis_url = get_redis_url()
    return redis.Redis.from_url(redis_url)

def _is_valid_to_number(value: str) -> bool:
    """Check if the value is a valid 'to' phone number (exactly 10 digits)."""
    return value.isdigit() and len(value) == 10

def _is_valid_phone_number_id(value: str) -> bool:
    """Check if the value is a valid phone number ID (exactly 15 digits)."""
    return value.isdigit() and len(value) == 15

def create_redis_session_factory() -> Callable[[str], BaseChatMessageHistory]:
    """Create a factory that can retrieve Redis chat histories.

    The chat histories are keyed by recipient and phoneNumberId using Redis.

    Returns:
        A factory that can retrieve Redis chat histories keyed by recipient and phoneNumberId.
    """
    
    def get_chat_history(to: str, phoneNumberId: str) -> RedisChatMessageHistory:
        """Get a Redis chat history from a recipient and phoneNumberId."""
        if not _is_valid_to_number(to):
            raise ValueError(
                f"Recipient {to} is not in a valid format. "
                "Recipient must be a valid phone number (digits only, 10 digits). "
                "Example: chain.invoke(.., {'configurable': {'to': '1234567890'}})"
            )
        if not _is_valid_phone_number_id(phoneNumberId):
            raise ValueError(
                f"Phone Number ID {phoneNumberId} is not in a valid format. "
                "Phone Number ID must be a valid phone number (digits only, 15 digits). "
                "Example: chain.invoke(.., {'configurable': {'phoneNumberId': '123456789012345'}})"
            )

        # Get Redis configuration from environment variables
        redis_url = get_redis_url()
        redis_ttl = get_redis_ttl()

        # Create a unique session key combining recipient and phoneNumberId
        session_key = f"chat_history:{to}:{phoneNumberId}"
        
        return RedisChatMessageHistory(
            session_id=session_key,
            url=redis_url,
            ttl=redis_ttl
        )

    return get_chat_history

if __name__ == "__main__":
    print("Testing Redis connection...")
    if test_redis_connection():
        print("✅ Redis connection successful!")
    else:
        print("❌ Redis connection failed!")
