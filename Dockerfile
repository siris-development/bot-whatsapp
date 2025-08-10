# /app /usr /lib
FROM python:3.10-slim-buster

WORKDIR /code

# Copiar requerimientos.txt 
COPY ./requirements.txt /code/requirements.txt

# Instalar las dependencias
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copiar los demás directorios
COPY . .

# Asegura que Python pueda encontrar el módulo "app"
ENV PYTHONPATH=/code

# Correr aplicación una vez el container inicie
CMD ["fastapi", "run", "app/api.py", "--proxy-headers", "--port", "80"]