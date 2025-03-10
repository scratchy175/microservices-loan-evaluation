# Utilisation d'une image Python légère
FROM python:3.10-slim

WORKDIR /app

# Copier le fichier des dépendances et installer
COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source dans l'image
COPY main.py /app

# Démarrer l'application avec uvicorn sur le port 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
