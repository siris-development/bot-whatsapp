from app.services.get_citas_disponibles import get_citas_disponibles
from app.services.get_especialidades import get_especialidades
from app.services.get_sedes import get_sedes
from app.services.guardar_cita import guardar_cita
from langchain.chat_models import init_chat_model

import os
from dotenv import load_dotenv
load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")

tools = [
    get_especialidades,
    get_sedes,
    get_citas_disponibles,
    guardar_cita
]

# Crea el modelo Ollama
llm = init_chat_model("gpt-oss:20b", model_provider="ollama", base_url=OLLAMA_BASE_URL, temperature=0)
llm_with_tools = llm.bind_tools(tools)