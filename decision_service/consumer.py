import pika
import json
import os
from sqlalchemy.orm import Session
from models import LoanProcess, SessionLocal
from decision_service.main import app  # Pour avoir accès à la fonction de publication des événements

BROKER_URL = os.getenv("BROKER_URL", "amqp://guest:guest@rabbitmq:5672//")

def publish_event(event_type: str, payload: dict):
    connection = pika.BlockingConnection(pika.URLParameters(BROKER_URL))
    channel = connection.channel()
    channel.exchange_declare(exchange='loan_exchange', exchange_type='fanout', durable=True)
    message = {"event_type": event_type, "data": payload}
    channel.basic_publish(
        exchange='loan_exchange',
        routing_key='',
        body=json.dumps(message)
    )
    connection.close()

def get_db_session() -> Session:
    return SessionLocal()

def evaluate_decision(loan: LoanProcess):
    # Si on a reçu les deux informations, on prend une décision.
    if loan.credit_result and loan.estimated_value is not None:
        # Par exemple, si le crédit est vérifié et que la valeur du bien est suffisante
        if loan.credit_result == "verified":
            decision = "loan_approved"
        else:
            decision = "loan_rejected"
        loan.decision = decision

        # Publie l'événement final
        publish_event(decision, {"loan_id": loan.loan_id})

def callback(ch, method, properties, body):
    message = json.loads(body)
    event_type = message.get("event_type")
    data = message.get("data")
    loan_id = data.get("loan_id")

    db = get_db_session()
    loan = db.query(LoanProcess).filter(LoanProcess.loan_id == loan_id).first()
    if not loan:
        # Crée un nouveau processus si nécessaire
        loan = LoanProcess(loan_id=loan_id)
        db.add(loan)
    
    if event_type in ["credit_verified", "credit_denied"]:
        loan.credit_score = data.get("credit_score")
        loan.credit_result = "verified" if event_type == "credit_verified" else "denied"
        print(f"[DecisionService] Mise à jour de la partie crédit pour {loan_id}: {loan.credit_result}")
    
    elif event_type == "property_evaluated":
        loan.estimated_value = data.get("estimated_value")
        print(f"[DecisionService] Mise à jour de l'évaluation immobilière pour {loan_id}")
    
    db.commit()
    evaluate_decision(loan)
    db.commit()
    db.close()
    
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    connection = pika.BlockingConnection(pika.URLParameters(BROKER_URL))
    channel = connection.channel()
    channel.exchange_declare(exchange='loan_exchange', exchange_type='fanout', durable=True)
    
    channel.queue_declare(queue='decision_service_queue', durable=True)
    channel.queue_bind(queue='decision_service_queue', exchange='loan_exchange', routing_key='')
    
    channel.basic_consume(queue='decision_service_queue', on_message_callback=callback)
    print("[DecisionService] En attente des messages RabbitMQ...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
