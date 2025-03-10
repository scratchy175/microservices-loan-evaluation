from sqlalchemy import Column, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

# Pour un prototype, on peut utiliser SQLite. En prod, vous utiliserez PostgreSQL par exemple.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./credit.db")

Base = declarative_base()

class CreditEvaluation(Base):
    __tablename__ = "credit_evaluation"
    loan_id = Column(String, primary_key=True, index=True)
    credit_score = Column(Float, nullable=True)
    credit_result = Column(String, nullable=True)  # "verified" ou "denied"
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# Création du moteur et de la session
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
