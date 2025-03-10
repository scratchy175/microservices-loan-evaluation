import time
import random
from celery import Celery
import os

BROKER_URL = os.getenv("BROKER_URL", "amqp://guest:guest@rabbitmq:5672//")
BACKEND_URL = os.getenv("BACKEND_URL", "redis://redis:6379/0")

celery_app = Celery("loan_tasks", broker=BROKER_URL, backend=BACKEND_URL)

@celery_app.task
def credit_scoring(loan_data: dict):
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
    
    # Exemple de règles simples (ces données doivent être présentes dans loan_data)
    revenu = loan_data.get("annual_income", 0)
    montant = loan_data.get("amount", 0)
    dette = loan_data.get("current_debt", 0)
    
    # Calcul du ratio d'endettement
    if revenu > 0:
        ratio = (dette + montant) / revenu
    else:
        ratio = 1.0  # Valeur par défaut si aucune information de revenu
    
    # Définir un seuil de tolérance (ce seuil peut être affiné)
    seuil = 0.5  # Par exemple, si le ratio est inférieur à 50%, le crédit est validé
    
    credit_ok = ratio < seuil
    
    # Pour illustrer, on calcule un "score" sur une échelle de 0 à 1 (inverse du ratio)
    score = max(0, 1 - ratio)
    
    return {"loan_id": loan_data.get("loan_id"), "credit_ok": credit_ok, "score": score}

@celery_app.task
def property_valuation(property_data: dict):
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
    
    # Valeur de base au m² (peut être ajustée selon le marché local)
    base_price_per_m2 = 3000
    
    area = property_data.get("area", 0)
    location = property_data.get("location", "standard")
    condition = property_data.get("condition", 1)  # Entre 0 et 1
    age = property_data.get("age", 0)
    
    # Facteur de localisation
    if location.lower() == "centre":
        location_factor = 1.2
    elif location.lower() == "banlieue":
        location_factor = 0.9
    else:
        location_factor = 1.0
    
    # Facteur lié à l'âge du bien : par exemple, on décale la valeur de 2% par an au-delà de 10 ans
    if age > 10:
        age_factor = 0.98 ** (age - 10)
    else:
        age_factor = 1.0
    
    # Calcul de l'estimation
    estimated_value = area * base_price_per_m2 * location_factor * condition * age_factor
    
    return {"estimated_value": estimated_value}
