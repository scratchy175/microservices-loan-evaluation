import pika
import json
import os
from celery_workers.tasks import property_valuation
from models import PropertyEvaluation, SessionLocal

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
        print("[PropertyService] Reçu event 'loan_created':", data)
        # Préparation des données pour une évaluation plus réaliste
        property_data = {
            "area": data.get("area", 0),
            "location": data.get("location", "standard"),
            "condition": data.get("condition", 1),
            "age": data.get("age", 0)
        }
        celery_result = property_valuation.delay(property_data)
        result = celery_result.get(timeout=15)
        estimated_value = result.get("estimated_value")
        result_payload = {
            "loan_id": data["loan_id"],
            "estimated_value": estimated_value
        }
        publish_event("property_evaluated", result_payload)
        print(f"[PropertyService] Publié event 'property_evaluated' avec payload: {result_payload}")

        # Persistance du résultat de l'évaluation
        db = SessionLocal()
        property_entry = db.query(PropertyEvaluation).filter(PropertyEvaluation.loan_id == data["loan_id"]).first()
        if not property_entry:
            property_entry = PropertyEvaluation(loan_id=data["loan_id"])
            db.add(property_entry)
        property_entry.estimated_value = estimated_value
        db.commit()
        db.close()
    
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    connection = pika.BlockingConnection(pika.URLParameters(BROKER_URL))
    channel = connection.channel()
    channel.exchange_declare(exchange='loan_exchange', exchange_type='fanout', durable=True)
    channel.queue_declare(queue='property_service_queue', durable=True)
    channel.queue_bind(queue='property_service_queue', exchange='loan_exchange', routing_key='')
    channel.basic_consume(queue='property_service_queue', on_message_callback=callback)
    print("[PropertyService] En attente de messages RabbitMQ...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
