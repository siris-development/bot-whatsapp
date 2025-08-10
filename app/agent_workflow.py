from typing import TypedDict, Optional
from datetime import datetime
from langgraph.graph import StateGraph, START, END

from utils.read_data import get_service_names, get_professionals_by_service, get_schedules_by_professional_name

class State(TypedDict):
    user_name: str
    message: str
    role: str
    fecha: Optional[datetime]
    servicio: Optional[str]
    profesional_name: Optional[str]
    available: Optional[int]

# Define nodes (agent == node)
# return a state

# Tool retorna los nombres de los servicios
def node_1(state: State) -> State:
    user_name = state["user_name"]
    state["message"] = f"Hola {user_name} seleccione el tipo de servicio: {get_service_names()}"
    state["role"] = "bot"
    return state

def node_2(state: State) -> State:
    state["message"] = "Quiero agendar una consulta medica"
    state["role"] = "user"
    return state

# Dependiendo de la selección anterior, selecciona el médico
def node_3(state: State) -> State:
    state["servicio"] = "Consulta Medica"
    nombre_servicio = state["servicio"]
    state["message"] = f"Con que médico?: {get_professionals_by_service(nombre_servicio)}"
    state["role"] = "bot"
    return state

def node_4(state: State) -> State:
    state["message"] = "Con el Medico 1 por favor"
    state["role"] = "user"
    return state

def node_5(state: State) -> State:
    state["profesional_name"] = "Medico 1"
    professional_name = state["profesional_name"]
    state["message"] = f"Con el médico {professional_name} tenemos los siguientes horarios: {get_schedules_by_professional_name(professional_name)}"
    state["role"] = "bot" 
    return state

def node_6(state: State) -> State:
    state["message"] = "La cita sería para el día jueves 10 de julio a las 8"
    state["role"] = "user"
    return state

def node_7(state: State) -> State:
    state["fecha"] = datetime(2025,7,10,8)
    state["available"] = True
    state["role"] = "bot"

    fecha = state["fecha"]
    available = state["available"]
    servicio = state["servicio"]
    professional_name = state["profesional_name"]

    if available:
        message = f"La cita de tipo {servicio} será agendada para la fecha {fecha} con el doctor {professional_name} desea confirmar?"
    else:
        message = "Seleccione otro día"

    return {
        "message": message,
        "role": state["role"]
    }

# Conditional

# Define the graph

builder = StateGraph(State)

builder.add_node('node_1', node_1)
builder.add_node('node_2', node_2)
builder.add_node('node_3', node_3)
builder.add_node('node_4', node_4)
builder.add_node('node_5', node_5)
builder.add_node('node_6', node_6)
builder.add_node('node_7', node_7)

builder.add_edge(START, 'node_1')
builder.add_edge('node_1', 'node_2')
builder.add_edge('node_2', 'node_3')
builder.add_edge('node_3', 'node_4')
builder.add_edge('node_4', 'node_5')
builder.add_edge('node_5', 'node_6')
builder.add_edge('node_6', 'node_7')
builder.add_edge('node_7', END)

graph = builder.compile()