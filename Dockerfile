FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN-FRONTEND noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY run.py wsgi.py ./
COPY app app

# split this into a development target eventually
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
COPY tests tests
COPY pytest.ini pytest.ini
