from celery.utils.log import get_task_logger
from deadshot.configurations.jira_config import JiraConfig
from jira import JIRA

# This class defines a method to create a JIRA ticket in a single project when a PR is closed without addressing
# all the identified secrets in the PR. This currently allows for the security team to get a ticket in their queue
# and follow up with the team that merged the PR

logger = get_task_logger(__name__)


class JiraService:
    def __init__(self):
        pass

    # @param project - project ID on JIRA board
    # @param issuetype - JIRA board issue type relevant to your org
    def create_jira_ticket(self, project='SECURITY', summary='', description='', labels=[]):
        config = JiraConfig()
        _user, _password = config.get_jira_creds()
        _server = config.get_jira_url()
        jira = JIRA(basic_auth=(_user, _password), options={'server': _server})
        issue_dict = {
            'project': project,
            'summary': summary,
            'description': description,
            'issuetype': {'name': 'Security'}
        }

        try:
            new_issue = jira.create_issue(fields=issue_dict)
            return new_issue.key
        except Exception as e:
            logger.error(f"Error creating SSD ticket: {e}")
