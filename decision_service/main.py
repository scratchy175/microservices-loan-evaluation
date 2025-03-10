from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from models import LoanProcess, init_db, SessionLocal

app = FastAPI(title="Decision Service API")

# Initialisation de la base de données
init_db()

# Dépendance pour obtenir la session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/decision/{loan_id}")
def get_decision(loan_id: str, db: Session = Depends(get_db)):
    process = db.query(LoanProcess).filter(LoanProcess.loan_id == loan_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Loan request not found")
    return {
        "loan_id": process.loan_id,
        "credit_score": process.credit_score,
        "credit_result": process.credit_result,
        "estimated_value": process.estimated_value,
        "decision": process.decision,
        "updated_at": process.updated_at
    }
