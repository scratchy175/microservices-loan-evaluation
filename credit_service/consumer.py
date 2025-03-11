import pika
import json
import os
from celery_workers.tasks import credit_scoring
from models import CreditEvaluation, SessionLocal

BROKER_URL = os.getenv("BROKER_URL", "amqp://guest:guest@rabbitmq:5672//")

def publish_event(event_type: str, payload: dict):
    connection = pika.BlockingConnection(pika.URLParameters(BROKER_URL))
    channel = connection.channel()
    channel.exchange_declare(exchange='loan_exchange', exchange_type='fanout', durable=True)
    message = {"event_type": event_type, "data": payload}
    channel.basic_publish(
        exchange='loan_exchange',
        routing_key='',
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
            content_type='application/json'
        )
    )
    connection.close()

def callback(ch, method, properties, body):
    message = json.loads(body)
    event_type = message.get("event_type")
    data = message.get("data")
    
    if event_type == "loan_created":
        print("[CreditService] Reçu event 'loan_created':", data)
        try:
            celery_result = credit_scoring.delay(data)
            result = celery_result.get(timeout=10)
            credit_ok = result.get("credit_ok")
            score = result.get("score")
            
            # Store state in database first
            db = SessionLocal()
            credit_entry = db.query(CreditEvaluation).filter(CreditEvaluation.loan_id == data["loan_id"]).first()
            if not credit_entry:
                credit_entry = CreditEvaluation(loan_id=data["loan_id"])
                db.add(credit_entry)
            credit_entry.credit_score = score
            credit_entry.credit_result = "verified" if credit_ok else "denied"
            db.commit()
            
            # Then publish event
            result_event = "credit_verified" if credit_ok else "credit_denied"
            event_payload = {
                "loan_id": data["loan_id"],
                "credit_score": score
            }
            publish_event(result_event, event_payload)
            print(f"[CreditService] Publié event '{result_event}' avec payload : {event_payload}")
            
        except Exception as e:
            print(f"[CreditService] Erreur lors du traitement: {e}")
            # Publish compensation event
            compensation_payload = {
                "loan_id": data["loan_id"],
                "service": "credit_service",
                "error": str(e)
            }
            publish_event("credit_evaluation_failed", compensation_payload)
            # Rollback database changes if any
            if 'db' in locals():
                db.rollback()
        finally:
            if 'db' in locals():
                db.close()
    
    # Handle compensation events from other services
    elif event_type in ["property_evaluation_failed", "decision_failed"]:
        print(f"[CreditService] Received compensation event: {event_type}")
        loan_id = data.get("loan_id")
        if loan_id:
            # Cleanup any stored data for this loan
            db = SessionLocal()
            try:
                credit_entry = db.query(CreditEvaluation).filter(CreditEvaluation.loan_id == loan_id).first()
                if credit_entry:
                    db.delete(credit_entry)
                    db.commit()
            except Exception as e:
                print(f"[CreditService] Error during compensation: {e}")
                db.rollback()
            finally:
                db.close()
    
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    connection = pika.BlockingConnection(pika.URLParameters(BROKER_URL))
    channel = connection.channel()
    
    # Enable publisher confirms
    channel.confirm_delivery()
    
    channel.exchange_declare(exchange='loan_exchange', exchange_type='fanout', durable=True)
    channel.queue_declare(queue='credit_service_queue', durable=True)
    channel.queue_bind(queue='credit_service_queue', exchange='loan_exchange', routing_key='')
    
    # Enable consumer acknowledgments
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue='credit_service_queue',
        on_message_callback=callback,
        auto_ack=False
    )
    
    print("[CreditService] En attente des messages RabbitMQ...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
