from langchain_core.tools import tool
from app.redis_client import clear_redis_history

@tool
def despedida(session_id: str) -> str:
    """
    Herramienta para despedirse del usuario y limpiar el historial de la conversación.
    
    Args:
        params: Parámetros con el ID de la sesión a limpiar
        
    Returns:
        str: Mensaje de despedida
    """
    try:
        # Limpiar completamente todas las entradas de Redis para esta sesión
        
        success = clear_redis_history(session_id)
        
        if success:
        else:
        
        return "¡Ha sido un placer ayudarte! Tu historial de conversación ha sido limpiado. ¡Que tengas un excelente día!"
        
    except Exception as e:
        return "¡Ha sido un placer ayudarte! ¡Que tengas un excelente día!"
