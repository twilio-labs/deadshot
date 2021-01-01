from deadshot.services.common.secrets_loader import get_secrets
import os
# Configuration settings for JIRA service access


class JiraConfig:
    def get_jira_url(self):
        jira_url = os.environ.get("JIRA_SERVER")
        return jira_url

    def get_jira_creds(self):
        _jira_secrets = get_secrets("SECRET_JIRA_AUTH")
        _jira_username = _jira_secrets["username"]
        _jira_password = _jira_secrets["password"]
        return _jira_username, _jira_password
