from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://loan_user:loan_password@postgresql:5432/loan_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(String, index=True)
    event_type = Column(String)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class LoanStatus(Base):
    __tablename__ = "loan_status"

    loan_id = Column(String, primary_key=True, index=True)
    status = Column(String)
    credit_score = Column(Integer, nullable=True)
    property_value = Column(Integer, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 