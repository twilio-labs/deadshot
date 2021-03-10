from celery.utils.log import get_task_logger
from deadshot.configurations.github_config import GithubConfig
from github import Github, GithubIntegration
import hashlib
import hmac
import requests

logger = get_task_logger(__name__)

# File defines class and methods to access and modify objects on Github via the Github App


class GithubServiceException(Exception):
    pass


class GithubService:
    """Wrapper around PyGithub but also adds functionality"""

    def __init__(self, base_url=None, token=None):
        self.github_base_url = base_url
        self.github_token = token
        try:
            if self.github_base_url is not None:
                self.github_connection = Github(
                    base_url=self.github_base_url,
                    login_or_token=self.github_token)
            else:
                self.github_connection = Github(
                    login_or_token=self.github_token)
        except Exception as e:
            logger.error(f"Failed github connection: {e}")

    def edit_app_comment(self, comments, url):
        # Method to edit the comments posted by the app on a single Pull Request
        try:
            headers = {
                "Authorization": f"token {self.github_token}"
            }
            res = requests.patch(url, json={"body": f"{comments}"}, headers=headers)
            return res.status_code
        except Exception as e:
            logger.error(f"Exception: {e}")

    def get_pr_comments(self, repo_name, pr_number):
        # Method to get all conversation comments posted on a single PUll Request
        try:
            repo = self.github_connection.get_repo(repo_name)
            pr = repo.get_pull(int(pr_number))
            comments = pr.get_issue_comments()
            return comments
        except Exception as e:
            logger.error(f"Exception: {e}")

    def get_app_comments(self, repo_name, pr_number):
        # Method to filter out only the Github app comments from all comments posted on a single Pull Request
        try:
            app_comments = []
            comments = self.get_pr_comments(repo_name, pr_number)
            for comment in comments:
                if GithubConfig().get_github_app_name() in comment.user.login:
                    app_comments.append({
                        "id": comment.id, "user": comment.user.login,
                        "body": comment.body, "issue_url": comment.issue_url,
                        "url": comment.url, "created_at": comment.created_at,
                        "updated_at": comment.updated_at
                    })

            return app_comments
        except Exception as e:
            logger.error(f"Exception: {e}")

    def get_latest_app_comment(self, repo_name=None, pr_number=None, comments=None):
        # Method to further filter out comments to only get the last/latest comment posted by the
        # Github app on a single Pull Request
        if comments is None and (repo_name is not None and pr_number is not None):
            comments = self.get_app_comments(repo_name, pr_number)
        latest_comment = {}
        for comment in comments:
            if len(latest_comment) < 1:
                latest_comment = comment
            else:
                if comment["updated_at"] > latest_comment["updated_at"]:
                    latest_comment = comment
        return latest_comment

    @staticmethod
    def get_signature(payload, secret):
        # Method to claculate the HMAC signature of the payload received from Github
        key = bytes(secret, 'utf-8')
        digester = hmac.new(key=key, msg=payload, digestmod=hashlib.sha1)
        digest_signature = digester.hexdigest()
        signature = "sha1=" + digest_signature
        return signature

    def post_issue_comment(self, comment, repo_name, pr_number):
        # Method to post a comment on the Pull Request conversation as the Github app
        try:
            gh_con = self.github_connection
            repo = gh_con.get_repo(repo_name)
            pr = repo.get_pull(int(pr_number))
            pr.create_issue_comment(comment)
        except Exception as e:
            logger.error(e)

    @classmethod
    def validate_webhook(cls, webhook_body, webhook_secret, sent_signature):
        # Method to validate the received X-GITHUB-SIGNATURE value against that calculated in the deadshot app using the
        # shared secret
        computed_signature = GithubService.get_signature(webhook_body,
                                                         webhook_secret)
        if not hmac.compare_digest(sent_signature, computed_signature):
            logger.info(f"computed sha: {computed_signature}")
            logger.error(
                "HMAC comparison of signature failed, raising exception")
            raise GithubServiceException(
                "Webhook Signature Did Not Match, Please Check Signature")
        return True


class GithubAppService:
    # Class to create a Github token using the app installation id, key, and base URL loaded to the Deadshot application
    def get_github_app_token(self, base_url, installation_id):
        gh_config = GithubConfig()
        integration_id, pem_key = gh_config.get_github_secrets()
        try:
            git_app_handler = GithubIntegration(integration_id, pem_key, base_url=base_url)
            access_token = git_app_handler.get_access_token(int(installation_id))
            token = access_token.token
            return token
        except Exception as e:
            logger.error(f"Failed to retrieve git token: {e}")
