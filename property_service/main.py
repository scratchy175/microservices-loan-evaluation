from fastapi import FastAPI

from models import init_db
init_db()  # Création des tables si nécessaire


app = FastAPI(title="Property Service API")

@app.get("/property/status/{loan_id}")
def get_property_status(loan_id: str):
    # Dans une implémentation complète, on récupérerait ici
    # l'état de l'évaluation depuis une base de données.
    return {"loan_id": loan_id, "status": "PENDING"}
