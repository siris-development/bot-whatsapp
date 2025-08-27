from app.schemas.whatsapp_response import WhatsAppMessage, WhatsAppResponse
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from app.config import tools, llm_with_tools
from app.redis_client import get_redis_history

from app.state import State
from utils.constants import Constants, system_prompt_agent

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import AIMessage
import requests

def build_graph() -> StateGraph:
    graph_builder = StateGraph(State)

    def call_model(state: State):        
        tools_description = [tool.name for tool in tools]

        # Crear el mensaje de sistema explícito
        system_message_content = system_prompt_agent(tools_description=tools_description)
        
        # Create a prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message_content),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
            ]
        )

        # Create the conversational chain
        chain = prompt | llm_with_tools

        # Create a runnable with message history
        chain_with_history = RunnableWithMessageHistory(
            chain, get_redis_history, input_messages_key="input", history_messages_key="history"
        )

        # Obtener el último mensaje de manera segura
        if len(state["messages"]) > 0:
            last_message = state["messages"][-1].content
        else:
            # Si no hay mensajes, crear un mensaje de error amigable
            error_message = AIMessage(content="Lo siento, no pude procesar tu mensaje. Por favor, intenta de nuevo.")
            return {"messages": [error_message]}

        response = chain_with_history.invoke({"input": last_message}, 
                                             config={"configurable": {"session_id": state["sessionId"]}})

        try:                          
            post_data = WhatsAppResponse(
                sessionId=state["sessionId"],
                phoneNumberId=state["phoneNumberId"],
                to=state["to"],
                messages=[WhatsAppMessage(type="text", content=str(response.content))]
            )
            
            # Convertir el objeto Pydantic a diccionario para serialización JSON
            post_data_dict = post_data.model_dump()
            
            headers = {"Content-Type": "application/json"}
            resp = requests.post(url=f"{Constants.base_url}/whatsapp/send-message", headers=headers, json=post_data_dict)
            resp.raise_for_status()
            data = resp.json()

            print(f"WhatsApp API response: {data}")
            return {"messages": [response]}

        except requests.exceptions.ConnectionError as e:
            print(f"Error de conexión con WhatsApp API: {e}")
            # Crear mensaje de error específico para problemas de conexión
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
        

    graph_builder.add_node("call_model", call_model)
    
    tool_node = ToolNode(tools)
    graph_builder.add_node("tools", tool_node)

    graph_builder.add_conditional_edges("call_model", tools_condition)
    graph_builder.add_edge("tools", "call_model")
    graph_builder.add_edge(START, "call_model")

    return graph_builder.compile()

graph = build_graph()