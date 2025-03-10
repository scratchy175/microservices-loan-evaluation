FROM python:3.10-slim

WORKDIR /app

# Copier le fichier de dépendances et installer
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY main.py /app
COPY consumer.py /app

# Par défaut, lancer l'API FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
