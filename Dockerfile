FROM python:3.11-slim

WORKDIR /app
COPY udp_voice_server.py .
EXPOSE 5005/udp
CMD ["python", "udp_voice_server.py"]
