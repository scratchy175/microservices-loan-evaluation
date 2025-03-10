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
        body=json.dumps(message)
    )
    connection.close()

def callback(ch, method, properties, body):
    message = json.loads(body)
    event_type = message.get("event_type")
    data = message.get("data")
    
    if event_type == "loan_created":
        print("[CreditService] Reçu event 'loan_created':", data)
        celery_result = credit_scoring.delay(data)
        result = celery_result.get(timeout=10)
        credit_ok = result.get("credit_ok")
        score = result.get("score")
        result_event = "credit_verified" if credit_ok else "credit_denied"
        event_payload = {
            "loan_id": data["loan_id"],
            "credit_score": score
        }
        publish_event(result_event, event_payload)
        print(f"[CreditService] Publié event '{result_event}' avec payload : {event_payload}")

        # Persistance du résultat dans la base
        db = SessionLocal()
        credit_entry = db.query(CreditEvaluation).filter(CreditEvaluation.loan_id == data["loan_id"]).first()
        if not credit_entry:
            credit_entry = CreditEvaluation(loan_id=data["loan_id"])
            db.add(credit_entry)
        credit_entry.credit_score = score
        credit_entry.credit_result = "verified" if credit_ok else "denied"
        db.commit()
        db.close()
    
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    connection = pika.BlockingConnection(pika.URLParameters(BROKER_URL))
    channel = connection.channel()
    channel.exchange_declare(exchange='loan_exchange', exchange_type='fanout', durable=True)
    channel.queue_declare(queue='credit_service_queue', durable=True)
    channel.queue_bind(queue='credit_service_queue', exchange='loan_exchange', routing_key='')
    channel.basic_consume(queue='credit_service_queue', on_message_callback=callback)
    print("[CreditService] En attente des messages RabbitMQ...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
