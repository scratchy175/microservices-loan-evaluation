FROM python:3.10-slim

WORKDIR /app

# Copier et installer les dépendances
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY main.py /app
COPY consumer.py /app

# Par défaut, démarre l'API FastAPI (tu pourras lancer le consumer séparément)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
