FROM python:3.12.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY simulator/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY simulator/simulator ./simulator
COPY simulator/tests ./tests

CMD ["python", "-m", "simulator"]
