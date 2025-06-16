FROM python:3.9-slim
LABEL authors="alexa"

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .

CMD ["python3", "main.py"]