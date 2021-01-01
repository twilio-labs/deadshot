from celery.utils.log import get_task_logger
from deadshot.configurations.slack_config import SlackConfig
import requests
import json

# Class with method to send notification to a Slack channel whenever the tool finds secrets for which the admin set
# slack_alert to True in regex.json

logger = get_task_logger(__name__)


class SlackService:
    def send_message(self, slack_message):
        try:
            message = f"*Deadshot Notification:* \n"
            message = message + slack_message
            slack_message = {'text': message}
            webhook = SlackConfig().get_slack_webhook()
            slack_alert_response = requests.post(
                webhook, data=json.dumps(slack_message),
                headers={'Content-Type': 'application/json'})
            if slack_alert_response.status_code != 200:
                logger.error(f"Failed sending alert to slack with "
                             f"status code:"
                             f" {slack_alert_response.status_code}")
        except Exception as e:
            logger.error(f"Failed slack notify: {e}")
