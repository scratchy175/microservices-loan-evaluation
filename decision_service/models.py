from sqlalchemy import Column, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./decision.db")  # Pour un prototype, SQLite est suffisant

Base = declarative_base()

class LoanProcess(Base):
    __tablename__ = "loan_process"
    loan_id = Column(String, primary_key=True, index=True)
    credit_score = Column(Float, nullable=True)
    credit_result = Column(String, nullable=True)  # "verified" ou "denied"
    estimated_value = Column(Float, nullable=True)
    decision = Column(String, nullable=True)  # "loan_approved" ou "loan_rejected"
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# Création du moteur et de la session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
