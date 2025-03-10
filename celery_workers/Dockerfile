# Utilise une image Python légère
FROM python:3.10-slim

WORKDIR /app

# Copier et installer les dépendances
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source des tâches et du worker
COPY tasks.py /app
COPY worker.py /app

# Par défaut, lance le worker Celery
CMD ["python", "worker.py"]
