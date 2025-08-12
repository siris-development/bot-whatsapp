from typing import List
from langchain.tools import tool
from utils.read_json import read_object

tool_path = 'tools/citas_json.json'

usuarios = read_object(tool_path, 'users')
servicios = read_object(tool_path,'services')
departamentos = read_object(tool_path,'departments')
profesionales = read_object(tool_path,'professionals')
horarios = read_object(tool_path,'schedules')

@tool
def get_phone_numbers(phone: str) -> List[str]:
    """Obtiene los números de teléfono de los usuarios"""
    phone_numbers = [{'id': user['id'], 'phone_number': user['whatsapp_number']} for user in usuarios 
                     if phone in user['whatsapp_number']]
    return phone_numbers

@tool
def get_service_names() -> List[str]:
    """Obtiene los nombres de los servicios"""
    services = [service for service in servicios]
    return services

@tool
def get_department_names() -> List[str]:
    """Obtiene los departamentos disponibles"""
    department_names = [{'name': department['name'], "id": department['_id']} for department in departamentos]
    return department_names

@tool
def get_professionals(professional_ids) -> List[str]:
    """Obtiene los profesionales"""
    professional_info = [
        professional['personal_info'] 
        for professional in profesionales 
        if professional['_id'] in professional_ids
    ]
    return professional_info

@tool
def get_schedules_by_professional(professional_id: str) -> List[str]:
    """Obtiene los horarios de un profesional"""
    schedule = []
    for horario in horarios:
        if horario['professional_id'] in professional_id:
            schedule.extend(horario['daily_schedules'])
    return schedule