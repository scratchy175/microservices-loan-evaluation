import time
import random
from celery import Celery
import os
from celery.exceptions import MaxRetriesExceededError

BROKER_URL = os.getenv("BROKER_URL", "amqp://guest:guest@rabbitmq:5672//")
BACKEND_URL = os.getenv("BACKEND_URL", "redis://redis:6379/0")

celery_app = Celery("loan_tasks", broker=BROKER_URL, backend=BACKEND_URL)

# Configuration Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=86400,  # 24 hours
    worker_prefetch_multiplier=1
)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def credit_scoring(self, loan_data: dict):
    try:
        """
        Tâche de scoring de crédit.
        Utilise des règles simples pour déterminer si le crédit est valide.
        Par exemple, on peut utiliser des données comme:
          - revenu annuel
          - montant demandé
          - ratio dette/revenu
        """
        # Simuler un délai de traitement
        time.sleep(3)
        
        revenu = loan_data.get("annual_income", 0)
        montant = loan_data.get("amount", 0)
        dette = loan_data.get("current_debt", 0)
        
        if not all([revenu, montant]):
            raise ValueError("Données de revenu ou montant manquantes")
        
        # Calcul du ratio d'endettement
        if revenu > 0:
            ratio = (dette + montant) / revenu
        else:
            ratio = 1.0
        
        seuil = 0.5
        credit_ok = ratio < seuil
        score = max(0, 1 - ratio)
        
        return {"loan_id": loan_data.get("loan_id"), "credit_ok": credit_ok, "score": score}
    
    except ValueError as e:
        self.retry(exc=e)
    except Exception as e:
        self.retry(exc=e)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def property_valuation(self, property_data: dict):
    try:
        """
        Évalue un bien immobilier de manière plus réaliste.
        Exemples de paramètres attendus dans property_data:
          - area: surface en m²
          - location: "centre", "banlieue", ou autre (pour ajuster le facteur de localisation)
          - condition: note entre 0 et 1 (1 = excellent état)
          - age: âge du bien en années
        """
        # Simuler un délai de traitement (par exemple, interroger une base de données ou API externe)
        time.sleep(5)
        
        area = property_data.get("area", 0)
        location = property_data.get("location", "standard")
        condition = property_data.get("condition", 1)
        age = property_data.get("age", 0)
        
        if not area:
            raise ValueError("Surface du bien manquante")
        
        base_price_per_m2 = 3000
        
        location_factors = {
            "centre": 1.2,
            "banlieue": 0.9,
            "standard": 1.0
        }
        location_factor = location_factors.get(location.lower(), 1.0)
        
        age_factor = 0.98 ** (age - 10) if age > 10 else 1.0
        
        estimated_value = area * base_price_per_m2 * location_factor * condition * age_factor
        
        return {"estimated_value": estimated_value}
    
    except ValueError as e:
        self.retry(exc=e)
    except Exception as e:
        self.retry(exc=e)
