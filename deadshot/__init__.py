from celery import Celery
from .api_server import create_app
from . import *
from deadshot.configurations.celery_config_data import celery_config


def make_celery(app_name=__name__):
    return Celery(
        celery_config["name"],
        backend=celery_config["broker"],
        broker=celery_config["backend"]
    )


celery = make_celery()
