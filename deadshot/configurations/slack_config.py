from deadshot.services.common.secrets_loader import get_secrets
# Configuration settings for Slack webhooks to be used to send slack notifications


class SlackConfig:
    def get_slack_webhook(self):
        webhooks = get_secrets("SECRET_SLACK_WEBHOOKS")
        webhook = webhooks["hook"]
        return webhook
