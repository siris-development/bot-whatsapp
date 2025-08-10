from .read_json import read_object

tool_path = 'tools/citas_json.json'

servicios = read_object(tool_path,'services')
profesionales = read_object(tool_path,'professionals')
horarios = read_object(tool_path,'schedules')

def get_service_names():
    """Extract all the service_names"""
    service_names = [service['service_name'] for service in servicios]
    return service_names

def get_professionals_by_service(service_name: str):
    """Extract the professionals by service"""

    # Find the service that matches the service_name
    matching_services = [service for service in servicios if service_name in service['service_name']]
    
    # Extract professional IDs from matching services and flatten the list
    professional_ids = []
    for service in matching_services:
        professional_ids.extend(service['professionals'])

    # Get professional info for the matching IDs
    professional_info = [professional['personal_info'] for professional in profesionales if professional['_id'] in professional_ids]
    
    return professional_info

def get_schedules_by_professional_name(professional_name: str):
    """Extract the schedules by the selected professional"""
    schedule = []
    for horario in horarios:
        if horario['professional_name'] in professional_name:
            schedule.extend(horario['daily_schedules'])
    return schedule