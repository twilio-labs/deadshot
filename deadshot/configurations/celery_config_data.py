import os
# Configuration settings for the celery container
name = os.environ.get("CELERY_NAME", "deadshot")
broker_host = os.environ.get("CELERY_BROKER_HOST", "deadshot-redis")
broker_port = os.environ.get("CELERY_BROKER_PORT", "6379")
broker_db = os.environ.get("CELERY_BROKER_DATABASE", "1")
broker = "redis://" + broker_host + ":" + broker_port + "/" + broker_db
backend = broker
celery_config = {
    "name": name,
    "broker": broker,
    "backend": backend
}
