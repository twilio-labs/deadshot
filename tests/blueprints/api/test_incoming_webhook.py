import json
import unittest
import deadshot
from unittest import mock

with open("tests/fixtures/good_pr.json") as good_pr_file:
    pr_string = good_pr_file.read()
with open("tests/fixtures/bad_pr.json") as bad_pr_file:
    bad_pr_string = bad_pr_file.read()

class TestParsing(unittest.TestCase):
    def setUp(self):
        self.app = deadshot.create_app('test')

    def test_healthcheck(self):
        with self.app.test_client() as tc:
            res = tc.get("/api/v1/healthcheck")
            assert res.status_code == 200, "[!] Error hitting /heartbeat"

    @mock.patch('deadshot.blueprints.blueprints.handle_webhook')
    def test_post_good_webhook(self, mock_handle_webhook):
        with self.app.test_client() as c:
            response = c.post("/api/v1/deadshot-webhook",
                              data=json.dumps(pr_string, indent=2),
                              headers={
                                  'X-GitHub-Enterprise-Host': 'mock.github.com',
                                  'X-Hub-Signature': 'sha1=cc58e852908be53414690b8a3af24ce100ba1653',
                                  'X-GitHub-Event': "pull_request"
                              },
                              content_type='application/json')
            # print(json.dumps(response.json, indent=2))
            self.assertEqual(response.status_code, 200)
