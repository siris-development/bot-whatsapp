from app.schemas.whatsapp_response import WhatsAppMessage, WhatsAppResponse
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode
from app.redis_client import get_redis_history, clear_redis_history
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from tools.get_sedes import get_sedes
from tools.get_citas_disponibles import get_citas_disponibles
from tools.get_especialidades import get_especialidades
from tools.guardar_cita import guardar_cita
from tools.despedida import despedida

from app.state import State
from utils.constants import Constants, system_prompt_agent

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import AIMessage
import requests

tools = [
    get_sedes,
    get_citas_disponibles,
    get_especialidades,
    guardar_cita,
    despedida
]

def build_graph() -> StateGraph:
    graph_builder = StateGraph(State)

    def call_model(state: State):
          # Obtener el último mensaje de manera segura
        if len(state["messages"]) > 0:
            last_message = state["messages"][-1].content
        else:
            # Si no hay mensajes, usar un mensaje por defecto
            last_message = "Hola, ¿en qué puedo ayudarte?"
       
        print(f"Last message: {last_message}")
        print(f"Total messages in state: {len(state['messages'])}")

        # Debug: Mostrar los primeros mensajes del historial
        if len(state["messages"]) > 1:
            print("First few messages in history:")
            for i, msg in enumerate(state["messages"][:3]):
                print(f"  {i}: {type(msg).__name__} - {msg.content[:100]}...")

        tools_description = [tool.name for tool in tools]

        # Crear el mensaje de sistema explícito
        system_message_content = system_prompt_agent(tools_description=tools_description)
        
        # Create a prompt template with explicit history handling
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message_content),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )

        # Get LLM with tools dynamically (validates availability)
        try:
            llm_with_tools = OllamaProvider(model_name="gpt-oss:20b").get_langchain_model()
        except Exception as e:
            print(f"ERROR getting LLM: {e}")
            error_message = AIMessage(content="Lo siento, no puedo acceder a los servicios de IA en este momento. Por favor, intenta de nuevo más tarde.")
            clear_redis_history(state["sessionId"])
            return {"messages": [error_message]}

        # Create the conversational chain
        chain = prompt | llm_with_tools

        # Create a runnable with message history
        chain_with_history = RunnableWithMessageHistory(
            chain, 
            get_redis_history, 
            input_messages_key="input", 
            history_messages_key="history"
        )

        # Invocar el modelo con manejo de errores y reintentos
        try:
            response = chain_with_history.invoke(
                    {"input": last_message}, 
                    config={"configurable": {"session_id": state["sessionId"]}}
                )
            print(f"Model response: {response}")
            print(f"Has tool_calls: {hasattr(response, 'tool_calls') and response.tool_calls}")
            return {"messages": [response]}
            
        except Exception as e:
            print(f"ERROR invoking model: {e}")
            error_message = AIMessage(content="Lo siento, tuve un problema técnico. Por favor, intenta de nuevo.")
            clear_redis_history(state["sessionId"])
            return {"messages": [error_message]}

    def send_to_whatsapp(state: State):
        """Nodo que envía la respuesta final a WhatsApp"""
        try:
            # Obtener el último mensaje de la respuesta del modelo de manera segura
            try:
                last_response = state["messages"][-1]
            except Exception as e:
                print(f"ERROR accessing last response: {e}")
                error_message = AIMessage(content="Lo siento, tuve un problema técnico. Por favor, intenta de nuevo.")
                return {"messages": [error_message]}
            
            # Verificar que sea una respuesta válida
            if not hasattr(last_response, 'content') or not last_response.content:
                print("ERROR: No valid response content to send to WhatsApp")
                error_message = AIMessage(content="Lo siento, no pude procesar tu solicitud. Por favor, intenta de nuevo.")
                return {"messages": [error_message]}
            
            print(f"Sending to WhatsApp: {last_response.content}")
            
            post_data = WhatsAppResponse(
                sessionId=state["sessionId"],
                phoneNumberId=state["phoneNumberId"],
                to=state["to"],
                messages=[WhatsAppMessage(type="text", content=str(last_response.content))]
            )
            
            post_data_dict = post_data.model_dump()
            
            headers = {"Content-Type": "application/json"}
            resp = requests.post(url=f"{Constants.base_url}/whatsapp/send-message", headers=headers, json=post_data_dict)
            resp.raise_for_status()
            data = resp.json()

            print(f"WhatsApp API response: {data}")
            return {"messages": [last_response]}

        except requests.exceptions.ConnectionError as e:
            print(f"Error de conexión con WhatsApp API: {e}")
            error_message = AIMessage(content="Lo siento, estoy teniendo problemas de conexión. Por favor, intenta de nuevo en unos momentos.")
            return {"messages": [error_message]}
            
        except requests.exceptions.Timeout as e:
            print(f"Timeout en WhatsApp API: {e}")
            error_message = AIMessage(content="La solicitud está tomando más tiempo del esperado. Por favor, intenta de nuevo.")
            return {"messages": [error_message]}
            
        except requests.exceptions.HTTPError as e:
            print(f"Error HTTP en WhatsApp API: {e}")
            error_message = AIMessage(content="Hubo un problema técnico. Por favor, intenta de nuevo más tarde.")
            return {"messages": [error_message]}
            
        except requests.RequestException as e:
            print(f"Error general en WhatsApp API: {e}")
            error_message = AIMessage(content="Hubo un problema al enviar tu mensaje. Por favor, intenta de nuevo.")
            return {"messages": [error_message]}
            
        except Exception as e:
            print(f"Error inesperado: {e}")
            error_message = AIMessage(content="Ocurrió un error inesperado. Por favor, intenta de nuevo.")
            return {"messages": [error_message]}

    # Agregar nodos al graph
    graph_builder.add_node("call_model", call_model)
    graph_builder.add_node("tools", ToolNode(tools))
    graph_builder.add_node("send_to_whatsapp", send_to_whatsapp)
    
    # Agregar edges condicionales personalizados
    def should_continue(state: State) -> str:
        """Función condicional que decide si ir a herramientas o enviar a WhatsApp"""
        try:
            last_response = state["messages"][-1]
            
            # Si hay tool_calls, ir a herramientas
            if hasattr(last_response, 'tool_calls') and last_response.tool_calls:
                print("INFO: Going to tools node")
                return "tools"
            
            # Si no hay tool_calls, enviar a WhatsApp
            print("INFO: Going to WhatsApp node")
            return "send_to_whatsapp"
        except Exception as e:
            print(f"ERROR in should_continue: {e}")
            return "send_to_whatsapp"
    
    graph_builder.add_conditional_edges("call_model", should_continue)
    
    graph_builder.add_edge("tools", "call_model")  # Después de herramientas, volver al modelo
    graph_builder.add_edge(START, "call_model")    # Empezar con el modelo

    return graph_builder.compile()

graph = build_graph()