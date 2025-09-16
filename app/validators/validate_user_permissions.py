def validate_user_permissions(users: list) -> tuple[bool, str]:
    """Validate if user has permissions to schedule appointments"""
    if not users:
        return False, "No se encontraron usuarios en la sesión."
    
    # Check if any user can schedule appointments
    for user in users:
        if hasattr(user, 'puedeAgendar') and user.puedeAgendar.lower() in ['true', '1', 'yes', 'si']:
            return True, f"Usuario {user.nombreCompleto} tiene permisos para agendar citas."
    
    return False, "Ninguno de los usuarios tiene permisos para agendar citas."