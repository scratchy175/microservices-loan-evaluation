import pika
import json
import os
from notification_service.main import broadcast_message

# Récupère l'URL du broker RabbitMQ depuis la variable d'environnement
BROKER_URL = os.getenv("BROKER_URL", "amqp://guest:guest@localhost:5672//")

def callback(ch, method, properties, body):
    message = json.loads(body)
    event_type = message.get("event_type")
    data = message.get("data", {})
    
    # Nous sommes intéressés par les événements finaux de décision
    if event_type in ["loan_approved", "loan_rejected"]:
        loan_id = data.get("loan_id", "inconnu")
        notification = f"Prêt {loan_id} : {event_type.upper()}"
        print(f"[NotificationService] Diffusion de : {notification}")
        broadcast_message(notification)
    
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    connection = pika.BlockingConnection(pika.URLParameters(BROKER_URL))
    channel = connection.channel()
    
    # S'assurer que l'exchange existe
    channel.exchange_declare(exchange='loan_exchange', exchange_type='fanout', durable=True)
    
    # Créer et lier une queue dédiée à ce service
    channel.queue_declare(queue='notification_service_queue', durable=True)
    channel.queue_bind(queue='notification_service_queue', exchange='loan_exchange', routing_key='')
    
    channel.basic_consume(queue='notification_service_queue', on_message_callback=callback)
    print("[NotificationService] En attente des événements RabbitMQ...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
