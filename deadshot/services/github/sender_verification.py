from celery.utils.log import get_task_logger
from deadshot.configurations.github_config import GithubConfig
from deadshot.services.github.github_service import GithubService, GithubServiceException
logger = get_task_logger(__name__)

# This class and methods are used to verify the sender information of the webhook received before forwarding the payload
# for further processing and regex matching.
# Currently it checks for a match in the received host, event type, and signature against those that were either loaded in
# an environment variable or calculated at run time.


class SenderVerificationException(Exception):
    pass


class SenderVerificationProcessor:
    def __init__(self, sender_host, event_type, sent_signature, webhook_json):
        self.sender_host = sender_host
        self.webhook_json = webhook_json
        self.event_type = event_type
        self.sent_signature = sent_signature
        self.all_check_status = False
        self.gh_config = GithubConfig()
        self.github_url = self.gh_config.get_github_url()
        self.git_wh_secret = self.gh_config.get_github_webhook_secret()

    def verify_sender(self):
        if self.github_url != self.sender_host:
            logger.error(f"Invalid Sender: {self.sender_host}")

        if self.event_type != "pull_request":
            logger.error(f"Received a unsupported action: {self.event_type}")
            return self.all_check_status

        if self.sent_signature is None:
            logger.error("Missing github signature")
            return self.all_check_status

        try:
            GithubService.validate_webhook(
                webhook_body=self.webhook_json,
                webhook_secret=self.git_wh_secret,
                sent_signature=self.sent_signature
            )
        except GithubServiceException as github_service_exception:
            logger.error(github_service_exception)
            return self.all_check_status

        self.all_check_status = True

        return self.all_check_status
