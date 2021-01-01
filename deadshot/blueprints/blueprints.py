from . import api_exceptions
from deadshot.services.celery_worker.webhook_async_processor import webhook_async
from deadshot.services.common.logger import get_logger
from deadshot.services.github.sender_verification import SenderVerificationProcessor
from flask import Blueprint
from flask import request, jsonify
import json

# This is a blueprint document for defining new API routes on the Flask application
# and defining how each route should be handled

logger = get_logger()
api_blueprint = Blueprint('api_blueprint', __name__)


@api_blueprint.errorhandler(api_exceptions.APIException)
def handleAPIException(error):
    response = error.jsonify()
    response.status_code = error.code
    return response


def handle_webhook(webhook_json):
    # call webhook async processor in a celery worker file
    webhook_async.delay(webhook_json)


@api_blueprint.route('/healthcheck', methods=['GET'])
def healthcheck():
    # Health check endpoint to test if the Flask application is up and running
    return json.dumps({"healthcheck": "ready"})


@api_blueprint.route('/deadshot-webhook', methods=['POST'])
def webhook_handler():
    # Endpoint called by your Github App webhook to send the Github PR payload
    # This method first verifies the sender of the payload and the signature of the payload.
    # If requests passes all checks then the payload is passed on to a celery task to initiate
    # Pull Request diff lines comparision against predefined regular expressions
    sender_host = request.headers.get('X-GitHub-Enterprise-Host')
    event_type = request.headers.get('X-GitHub-Event')
    sent_signature = request.headers.get('X-Hub-Signature')

    request_body = request.get_data()
    webhook_payload = json.loads(request_body)
    # Call function to verify the sender of the request
    sender_verify = SenderVerificationProcessor(sender_host, event_type, sent_signature, request_body)
    sender_status = sender_verify.verify_sender()

    if not sender_status:
        raise api_exceptions.BadRequestException("Invalid Sender")

    try:
        handle_webhook(webhook_payload)
    except Exception as e:
        logger.error(f"Failed queing celery task: {e}")

    return jsonify({
        "Status": 200
    })
