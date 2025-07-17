
FROM python:3.9-slim-buster


WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY app/ app/


ENV PYTHONUNBUFFERED=1


CMD python -m app.main