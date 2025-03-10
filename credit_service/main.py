from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from models import init_db, SessionLocal, CreditEvaluation

# Initialisation de la base au démarrage
init_db()

app = FastAPI(title="Credit Service API")

# Dépendance pour obtenir une session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/credit/status/{loan_id}")
def get_credit_status(loan_id: str, db: Session = Depends(get_db)):
    # Recherche l'évaluation du crédit pour le loan_id donné
    evaluation = db.query(CreditEvaluation).filter(CreditEvaluation.loan_id == loan_id).first()
    if evaluation is None:
        raise HTTPException(status_code=404, detail="Évaluation de crédit non trouvée")
    
    return {
        "loan_id": evaluation.loan_id,
        "credit_score": evaluation.credit_score,
        "credit_result": evaluation.credit_result,
        "updated_at": evaluation.updated_at
    }
