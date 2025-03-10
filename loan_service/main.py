from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uuid
import os
import json
import pika
import requests

app = FastAPI(title="Loan Service")
templates = Jinja2Templates(directory="templates")

# Variables d'environnement
BROKER_URL = os.getenv("BROKER_URL", "amqp://guest:guest@localhost:5672//")
DECISION_SERVICE_URL = os.getenv("DECISION_SERVICE_URL", "http://decision-service:8000")

def publish_event(event_type: str, payload: dict):
    try:
        connection = pika.BlockingConnection(pika.URLParameters(BROKER_URL))
        channel = connection.channel()
        channel.exchange_declare(exchange='loan_exchange', exchange_type='fanout', durable=True)
        message = {"event_type": event_type, "data": payload}
        channel.basic_publish(
            exchange='loan_exchange',
            routing_key='',
            body=json.dumps(message)
        )
    except Exception as e:
        print("Erreur lors de la publication de l'événement :", e)
    finally:
        if 'connection' in locals() and connection.is_open:
            connection.close()

@app.get("/", response_class=HTMLResponse)
def read_form(request: Request):
    """
    Affiche le formulaire de demande de prêt.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/loans")
def create_loan_request(
    client_name: str = Form(...),
    amount: float = Form(...),
    property_address: str = Form(...),
    annual_income: float = Form(...),
    current_debt: float = Form(...),
    area: float = Form(...),
    location: str = Form(...),
    condition: float = Form(...),
    age: int = Form(...)
):
    """
    Traite le formulaire, publie l'événement 'loan_created' et redirige vers le suivi du prêt.
    """
    if amount <= 0 or annual_income <= 0:
        raise HTTPException(status_code=400, detail="Les montants doivent être supérieurs à 0")
    
    loan_id = str(uuid.uuid4())
    loan_data = {
        "loan_id": loan_id,
        "client_name": client_name,
        "amount": amount,
        "property_address": property_address,
        "annual_income": annual_income,
        "current_debt": current_debt,
        "area": area,
        "location": location,
        "condition": condition,
        "age": age
    }
    
    # Publie l'événement pour démarrer le traitement dans les autres microservices
    publish_event("loan_created", loan_data)
    
    # Redirection vers la page de suivi
    return RedirectResponse(url=f"/loan_status/{loan_id}", status_code=303)

@app.get("/loan_status/{loan_id}", response_class=HTMLResponse)
def loan_status(request: Request, loan_id: str):
    """
    Interroge le Decision Service pour obtenir le statut final du prêt.
    Si le Decision Service renvoie une erreur ou si le statut n'est pas encore disponible, 
    le message "En cours de traitement..." est affiché.
    """
    try:
        response = requests.get(f"{DECISION_SERVICE_URL}/decision/{loan_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            decision = data.get("decision", "En cours de traitement...")
        else:
            decision = "En cours de traitement..."
    except Exception as e:
        print("Erreur lors de la récupération du statut depuis le Decision Service :", e)
        decision = "En cours de traitement..."

    context = {"request": request, "loan_id": loan_id, "status": decision}
    return templates.TemplateResponse("loan_status.html", context)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
