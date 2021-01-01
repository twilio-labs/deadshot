from celery.utils.log import get_task_logger
from deadshot import celery
from deadshot.configurations.github_config import GithubConfig
from deadshot.services.common.jira_service import JiraService
from deadshot.services.github.github_service import GithubAppService
from deadshot.services.github.webhook_processor import PullRequestWebhookProcessor
from deadshot.services.scanner.pr_scanner import PRScanner

# This is the celery worker that processes each webhook payload after the blueprint verifies it's from a valid
# sender. The worker handles Pull Requests based on action mentioned in the payload (webhook_json). If it receives
# a open, reopen, or synchronize action it proceeds to search for tokens by passing it along to the pr_scanner
# function. If it receives a closed action then it scans for secrets and creates a JIRA ticket in the Security
# team's queue so they can reach out to the engineers.

logger = get_task_logger(__name__)


@celery.task
def webhook_async(webhook_json):
    pr_webhook_processor = PullRequestWebhookProcessor(webhook_json)
    if pr_webhook_processor.pr_processor():
        html_url = webhook_json['pull_request']['html_url']
        logger.info(f"Received request from {html_url}")
        pr_scanner = PRScanner(webhook_json)
        pr_scanner.scan()
        logger.info(f"Finished processing {html_url}")

    elif pr_webhook_processor.pr_closed():
        try:
            install_id = webhook_json["installation"]["id"]
            html_url = webhook_json['pull_request']['html_url']
            logger.info(f"Received closed pull request from {html_url}")
            gh_app_service = GithubAppService()
            gh_api = GithubConfig().get_github_api()
            git_token = gh_app_service.get_github_app_token(gh_api, install_id)

            pr_scanner = PRScanner(webhook_json)
            identified_secrets = pr_scanner.identify_secrets(git_token)

            if len(identified_secrets) > 0:
                description = pr_scanner.create_jira_description(identified_secrets)
                jira_summary = "Deadshot identified secrets in a closed PR"
                jira_description = f"Please check PR: {html_url} \nThe following were identified:\n" + description
                jira_service = JiraService()
                jira_service.create_jira_ticket(summary=jira_summary, description=jira_description)
            logger.info(f"Finished processing {html_url}")
        except Exception as e:
            logger.error(f"Exception: {e}")
