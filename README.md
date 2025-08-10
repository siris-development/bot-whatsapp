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
