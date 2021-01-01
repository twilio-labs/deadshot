from deadshot.services.common.secrets_loader import get_secrets
import os
# Configuration settings for Github


class GithubConfig:
    def get_github_secrets(self):
        _github_secrets = get_secrets("SECRET_GITHUB_SECRET")
        webhook_secret = _github_secrets["webhook_secret"]
        integration_id = int(_github_secrets["github_app_integration_id"])
        app_pem = _github_secrets["github_app_pem_key"]
        return integration_id, app_pem

    def get_github_url(self):
        gh_url = os.environ.get("GITHUB_URL")
        return gh_url

    def get_github_webhook_secret(self):
        _github_secrets = get_secrets("SECRET_GITHUB_SECRET")
        webhook_secret = _github_secrets["webhook_secret"]
        return webhook_secret

    def get_github_api(self):
        gh_api = os.environ.get("GITHUB_API")
        return gh_api

    def get_github_app_name(self):
        app_name = os.environ.get("GITHUB_APP_NAME")
        return app_name
