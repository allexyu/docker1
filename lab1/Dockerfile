FROM python:3.13-slim

RUN pip install \
    fastapi \
    uvicorn[standard]

WORKDIR /app

COPY amin.py .

# Порт для FastAPI
EXPOSE 8000

CMD ["python", "amin.py"]