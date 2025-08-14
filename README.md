# 📱 Bot WhatsApp
## Ejecución con Docker

Descargar la imagen desde Docker Hub
```bash
docker pull siris837/bot-whatsapp:latest
```

Ejecutar el contenedor
```bash
docker run -d \
  --name bot-whatsapp \
  -p 80:80 \
  siris837/bot-whatsapp:latest
```

El bot estará disponible en:
http://localhost:80

## Ejecución local
Crear python environment

1. Crear un virtual environment: `python3 -m venv bot-whatsapp-env` 
2. Activar el virtual environment:
        - Linux or Mac: `source bot-whatsapp-env/bin/activate`
        - Windows Powershell: `bot-whatsapp-env\Scripts\activate`
3. Instalar los paquetes: `pip install -r requirements.txt`

## Pyenv
1. Instalar la versión de Python (ej. 3.11.6) `pyenv install 3.11.6`
2. Crear y usar el entorno virtual con pyenv-virtualenv: `pyenv virtualenv 3.11.6 bot-whatsapp-env`
3. Activar el entorno virtual `pyenv activate bot-whatsapp-env`
4. Instalar los paquetes `pip install -r requirements.txt`