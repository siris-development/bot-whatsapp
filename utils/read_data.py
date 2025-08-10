from .read_json import read_object

tool_path = 'tools/citas_json.json'

usuarios = read_object(tool_path, 'users')
servicios = read_object(tool_path,'services')
departamentos = read_object(tool_path,'departments')
profesionales = read_object(tool_path,'professionals')
horarios = read_object(tool_path,'schedules')

def get_phone_numbers():
    """Extrae todos los números de teléfono de los usuarios."""
    phone_numbers = [user['whatsapp_number'] for user in usuarios]
    return phone_numbers

def get_service_names():
    """Extrae todos los nombres de los servicios."""
    service_names = [service['service_name'] for service in servicios]
    return service_names

def get_department_names():
    """Extrae todos los nombres de los departamentos."""
    department_names = [department['name'] for department in departamentos]
    return department_names

def get_professionals_by_service(service_name: str):
    """Obtiene la información de los profesionales que ofrecen un servicio específico."""
    # Buscar los servicios que coincidan con el nombre proporcionado
    matching_services = [service for service in servicios if service_name in service['service_name']]
    
    # Extraer los IDs de profesionales y aplanar la lista
    professional_ids = []
    for service in matching_services:
        professional_ids.extend(service['professionals'])

    # Obtener la información personal de los profesionales con los IDs coincidentes
    professional_info = [
        professional['personal_info'] 
        for professional in profesionales 
        if professional['_id'] in professional_ids
    ]
    
    return professional_info

def get_schedules_by_professional_name(professional_name: str):
    """Obtiene los horarios disponibles de un profesional por su nombre."""
    schedule = []
    for horario in horarios:
        if horario['professional_name'] in professional_name:
            schedule.extend(horario['daily_schedules'])
    return schedule