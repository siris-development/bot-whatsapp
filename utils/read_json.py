import json

def read_object(tool_path: str, key: str):
    try:
        with open(tool_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            obj = data.get(key, [])
            return obj
    except Exception as e:
        print(f"Error al leer el archivo JSON: {e}")
        return []