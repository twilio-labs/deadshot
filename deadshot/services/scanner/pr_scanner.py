from celery.utils.log import get_task_logger
from deadshot.configurations.github_config import GithubConfig
from deadshot.services.common.slack_notification import SlackService
from deadshot.services.github.github_service import GithubService, GithubAppService
from deadshot.services.github.git_diff_parser import GithubDiffProcessor
from deadshot.services.scanner.regex_scanner import run as regex_scan

logger = get_task_logger(__name__)

# Class to manage Pull Request diff scans per line and create/edit the end comment to be sent to the Github Pull Request
# conversation


class PRScanner:
    def __init__(self, pull_request_webhook):
        self.pull_request_webhook = pull_request_webhook
        self.html_url = self.pull_request_webhook['pull_request']['html_url']
        self.pr_url = str(self.pull_request_webhook['pull_request']['url'])
        self.pr_number = int(self.pull_request_webhook['number'])
        self.repo_name = str(self.pull_request_webhook['pull_request']['head']['repo']['full_name'])
        self.installation_id = self.pull_request_webhook["installation"]["id"]
        self.identified_tokens = None
        self.slack_message_dict = {}

    def scan(self):
        try:
            base_url = GithubConfig().get_github_api()
            git_app = GithubAppService()
            git_token = git_app.get_github_app_token(base_url, self.installation_id)

            self.identified_tokens = self.identify_secrets(git_token)
            if self.identified_tokens:
                github_service = GithubService(base_url=base_url, token=git_token)
                latest_app_comment = github_service.get_latest_app_comment(repo_name=self.repo_name, pr_number=self.pr_number)
                if len(latest_app_comment) == 0:
                    comments, post_to_slack = self.create_issue_comment()
                    github_service.post_issue_comment(comments, self.repo_name, self.pr_number)

                else:
                    old_comment_list = self.split_comments(latest_app_comment)
                    new_comments, post_to_slack = self.create_issue_comment(old_comment_list)
                    response = github_service.edit_app_comment(new_comments, latest_app_comment["url"])
                if post_to_slack:
                    self.post_slack_message()

        except Exception as e:
            logger.error(f"Exception: {e}")

    def create_issue_comment(self, old_comments=None):
        comments = "### Ahoy!! Your PR has some security concerns. " \
                   "Please review the files listed below:\n"
        post_to_slack = False

        try:
            if old_comments is not None:
                temp_comments = ""
                for item in old_comments:
                    temp_comments = temp_comments + item + "\n"
                comments += temp_comments
            for title, nested_values in self.identified_tokens.items():
                for issue_iterator, nested_issue_values in nested_values.items():
                    if old_comments is not None:
                        comment_exists = self.evaluate_app_comment(old_comments, title, issue_iterator)
                    else:
                        comment_exists = False
                    if not comment_exists:
                        comments += f"- [ ] <b>File: </b> {title} <b>Issue:</b> {issue_iterator}. " \
                                    f"<b>Recommendation:</b> {nested_issue_values['recommendation']}\n"
                        if nested_issue_values["slack_alert"] == "True":
                            post_to_slack = True
                            if issue_iterator in self.slack_message_dict:
                                self.slack_message_dict[issue_iterator] = int(self.slack_message_dict[issue_iterator]) + 1
                            else:
                                self.slack_message_dict[issue_iterator] = int(1)

            comments += "\nIf you have any questions please reach out to #help-security"
            return comments, post_to_slack
        except Exception as e:
            logger.error(f"Failed creating comment: {e}")

    @staticmethod
    def create_jira_description(identified_secrets):
        description = ""
        try:
            for title, nested_values in identified_secrets.items():
                for issue_iterator, nested_issue_values in nested_values.items():
                    description += \
                        f"File: {title} " \
                        f"Issue: {issue_iterator}\n"

            return description

        except Exception as e:
            logger.error(f"Failed creating jira description: {e}")

    @staticmethod
    def evaluate_app_comment(app_comments, title, issue_iterator):
        try:
            comment_exists = False
            for comment in app_comments:
                if title in comment and issue_iterator in comment:
                    comment_exists = True

            return comment_exists
        except Exception as e:
            logger.error(f"Failed to iterate through comments: {e}")

    def identify_secrets(self, git_token):
        try:
            identified_tokens = {}
            github_diff = GithubDiffProcessor(self.pr_url, git_token)
            for git_file in github_diff.diff_files():
                if "test" not in git_file.full_filename:
                    for git_line in git_file.diff_lines():
                        if git_line.line_type == "+":
                            res = regex_scan(body=str(git_line.value), file_name=git_file.full_filename, line_number=git_line.line_number)
                            if len(res) > 0 and git_line.line_number is not None:
                                if str(git_file.full_filename + ":" + str(git_line.line_number)) in identified_tokens:
                                    identified_tokens[str(git_file.full_filename) + ":" + str(git_line.line_number)].update(res)
                                else:
                                    identified_tokens[git_file.full_filename + ":" + str(git_line.line_number)] = res

            return identified_tokens
        except Exception as e:
            logger.error(f"Failed identifying all tokens: {e}")

    def post_slack_message(self):
        try:
            slack_message = "Ahoy!! Deadshot has identified: "
            slack = SlackService()

            for issue, issue_count in self.slack_message_dict.items():
                slack_message += f"`{issue_count}` `{issue}`, "
            slack_message += f"in PR: {self.html_url}"
            slack.send_message(slack_message)

        except Exception as e:
            logger.error(f"Exception: {e}")

    @staticmethod
    def split_comments(latest_app_comment):
        try:
            temp_text = latest_app_comment["body"]
            temp_list = temp_text.split("\n")
            temp_list = list(filter(None, temp_list))
            final_list = []
            for i in range(0, len(temp_list)-1):
                if "- [ ]" in temp_list[i] or "- [x]" in temp_list[i]:
                    final_list.append(temp_list[i])
            return final_list
        except Exception as e:
            logger.error(f"Exception: {e}")
