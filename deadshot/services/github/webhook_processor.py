from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

# The class and methods in this file are used to verify the JSON payload has key fields that'll be necessary in the
# further processing of the payload data


class PullRequestWebhookProcessorException(Exception):
    pass


class PullRequestWebhookProcessor:
    def __init__(self, webhook_json):
        self.webhook_json = webhook_json
        # Github Enterprise webhook payload processor

    def pr_processor(self):
        try:
            pr_type = self.webhook_json["action"]
            pr_number = self.webhook_json["number"]
            pr_repository_owner = self.webhook_json["repository"]["owner"]["login"]
            pr_repository_name = self.webhook_json["repository"]["name"]
            installation_id = self.webhook_json["installation"]["id"]
            html_url = self.webhook_json['pull_request']['html_url']
        except KeyError as key_error:
            logger.error(f"Error retrieving: {key_error}; are you sure this is a pull request?\n")
            raise PullRequestWebhookProcessorException(
                f"Error retrieving PR field: {key_error}; are you sure this is a pull request?"
            )

        if pr_type == "opened" or pr_type == "synchronize" or pr_type == "reopened":
            return True
        else:
            return False

    def pr_closed(self):
        try:
            install_id = self.webhook_json["installation"]["id"]
            html_url = self.webhook_json['pull_request']['html_url']
            pr_type = self.webhook_json["action"]
            if pr_type == "closed":
                return True
            else:
                return False
        except KeyError as key_error:
            logger.error(f"Error retrieving: {key_error}; are you sure this is a pull request?\n")
            raise PullRequestWebhookProcessorException(
                f"Error retrieving PR field: {key_error}; are you sure this is a pull request?"
            )
