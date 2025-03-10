from sqlalchemy import Column, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./property.db")

Base = declarative_base()

class PropertyEvaluation(Base):
    __tablename__ = "property_evaluation"
    loan_id = Column(String, primary_key=True, index=True)
    estimated_value = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
