from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
import requests
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def is_ollama_running():
    """Check if Ollama is running and accessible"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except (requests.RequestException, Exception):
        return False

def get_available_llm():
    """Get the best available LLM, checking availability in real-time"""
    # Try Ollama first
    if OLLAMA_BASE_URL and is_ollama_running():
        try:
            ollama_llm = ChatOllama(
                model="gpt-oss:20b",
                base_url=OLLAMA_BASE_URL,
                temperature=0,
                # Configuración específica para Ollama
                format="json" if "json" in "gpt-oss:20b" else None
            )
            print("Using Ollama LLM")
            return ollama_llm
        except Exception as e:
            print(f"Error initializing Ollama LLM: {e}")
    
    # Fallback to OpenAI
    if OPENAI_API_KEY:
        try:
            openai_llm = ChatOpenAI(
                model="gpt-4o", 
                api_key=OPENAI_API_KEY, 
                temperature=0,
                # Configuración específica para OpenAI
                max_tokens=4000,
                request_timeout=60
            )
            print("Using OpenAI LLM")
            return openai_llm
        except Exception as e:
            print(f"Error initializing OpenAI LLM: {e}")
    
    # If neither works, raise an error
    raise Exception("No LLM available. Please check your configuration.")

