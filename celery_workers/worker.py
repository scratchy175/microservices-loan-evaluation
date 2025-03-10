from tasks import celery_app

if __name__ == "__main__":
    # Lance le worker Celery avec le niveau de log en mode INFO
    celery_app.worker_main(["worker", "--loglevel=info"])
