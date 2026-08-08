FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
COPY app.py .

RUN pip install -r requirements.txt

CMD ["python3", "app.py"]
