from celery import Celery
from celery.signals import after_setup_task_logger
from datetime import datetime
from deadshot import celery
from deadshot.api_server import create_app
from deadshot.configurations.api_server_config_data import Config
from pythonjsonlogger import jsonlogger
import sys
import logging
'''
This file initiates the Celery broker and sets up the logging format
'''

app = create_app()

celery.conf.update(app.config)
TaskBase = celery.Task


class ContextTask(TaskBase):
    abstract = True

    def __call__(self, *args, **kwargs):
        with app.app_context():
            return TaskBase.__call__(self, *args, **kwargs)


celery.Task = ContextTask


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record,
                                                    record, message_dict)
        if not log_record.get('timestamp'):
            # this doesn't use record.created, so it is slightly off
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('levelname'):
            log_record['levelname'] = log_record['levelname'].upper()
        else:
            log_record['levelname'] = record.levelname


@after_setup_task_logger.connect
def setup_task_logger(logger, *args, **kwargs):
    # for handler in logger.handlers:
    logging_level = Config().get_log_level()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomJsonFormatter('%(message)s %(levelname)s'
                                             ' %(timestamp)s %(module)s'
                                             ' %(lineno)s %(process)s'
                                             '%(filename)s %(funcName)s'
                                             '%(thread)s'))
    logger.addHandler(handler)
    logger.setLevel(logging_level)


# @celery.task
def example_task():
    print("celery: Web app sync")
