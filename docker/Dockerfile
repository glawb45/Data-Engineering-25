# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.9-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install build dependencies and sqlite
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libpq-dev \
    sqlite3 \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pip requirements with Airflow constraints
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install apache-airflow==2.8.1 \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.8.1/constraints-3.9.txt"
RUN pip install -r requirements.txt --no-deps


WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser