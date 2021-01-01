import logging
import sys
from datetime import datetime
from deadshot.configurations.api_server_config_data import Config
from pythonjsonlogger import jsonlogger

# This is a standardized logger function to be used in non-celery worker calls. For now, it's only used in the
# blueprints file functions


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


def get_logger(logging_level="INFO", logging_config="json"):
    logger = logging.getLogger()

    while logger.handlers:
        logger.handlers.pop()

    logHandler = logging.StreamHandler(sys.stdout)
    logging_level = Config().get_log_level()
    logHandler.setLevel(logging_level)

    if logging_config == "json":
        formatter = CustomJsonFormatter('%(message)s %(levelname)s'
                                        ' %(timestamp)s %(module)s'
                                        ' %(lineno)s %(process)s'
                                        '%(filename)s %(funcName)s'
                                        '%(thread)s')
        logHandler.setFormatter(formatter)

    logger.addHandler(logHandler)
    logger.setLevel(logging_level)

    return logger
