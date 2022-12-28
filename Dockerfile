FROM python:3.9-slim

COPY ./proxyx /app
WORKDIR /app/

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

CMD exec uvicorn --reload --host 0.0.0.0 --port 8000 --log-level info app
