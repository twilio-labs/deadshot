# Deadshot
Deadshot is a Pull Request scanner that looks for the introduction of secrets via PRs by matching each diff line against a set of known secret expressions.

## Application capabilities:
Service is responsible for:
- Real-time Pull Request diff processor to check for secrets being committed to Github via new code
- Notify the user on the PR conversation if it flags something
- Slack notify the security team channel when certain secrets are identified in code for which you've enabled slack notifications via a flag in regex.json

Service does NOT:
- Do any static or dynamic code analysis

## How does it work?
Deadshot is a Flask-Celery-Redis multi-container application that is installed as a Github app to run on every Pull Request created against the main branch of a repo on which the Github app is installed.

The Flask container is the entry point for the service by exposing API routes defined in blueprints.py. Once a Pull request payload is received on the API route the service forwards the payload to a Redis queue for the Celery container to pick up and
scan through the diff of the Pull Request. After the celery container scans for specified secrets regular expressions, it comments on PRs, slack notifies the security team channel, or creates a JIRA ticket for the team to follow up on.
The Github app is configured with the Flask API URL and a shared secret used for generating the payload SHA checksum.

One way the API URL can be setup is by deploying this code on an host and assigning a application load balancer to this host.

### Creating a Github App
Github Admins would need to create and install a Github app on Github before running or deploying the Deadshot application.
To know more about creating a Github app please read this [guide](https://docs.github.com/en/free-pro-team@latest/developers/apps/creating-a-github-app).

When creating the app please make sure you have a DNS ready for host on which you'll be deploying Deadshot containers and also a secret string for the webhook secret

### Github App Permissions
For this application to work your Github app will have to enable the following permissions and subscriptions on the permissions page of the Github app:
Repository Permissions:
- Metadata: Read-only
- PullRequests: Read & write
- Webhooks: Read & write

All other permissions are left unchanged to the deafult value of No access

Subscribe to events:
- Pull request
- Pull request review

## Running Deadshot
This application is a multi-container application designed to bring up all three containers (Flask, Celery, Redis) via the /bin/run.sh, so running the Dockerfile image should bring up the entirety of the application

### Environment variables:
This application needs the following environment variables to be given by the user
- GITHUB_URL: This is the URL behind which your Github instance is accessed. Please provide the DNS without scheme or port. Eg. if your Github web URL is https://github.mockcompany.com then provide the value github.mockcompany.com
- GITHUB_API: This is the API URL for Github. Eg. if you have your Github DNS as https://github.mockcompany.com then your API would be something like https://github.mockcompany.com/api/v3
- JIRA_SERVER= Your company's JIRA server web URL

Three environment variables are loaded with credentials in them. please load the appropriate json file key values before running this application.
- SECRET_GITHUB_SECRET: This variable loads local_dev_secrets/github_secrets.json and has the Github app's shared webhook secret, integration ID, and the pem key. All these three secrets are obtained from the Github app settings page
- SECRET_SLACK_WEBHOOKS: This loads local_dev_secrets/slack_webhook.json and has the webhook URL to which the deadshot app will send slack notifications when it finds secrets in a PR for which you set slack_alert=True in regex.json
- SECRET_JIRA_AUTH: This loads local_dev_secrets/jira_user.json and has the username and password for the user ID to access the org's JIRA board

### Running/Serving the Docker Image
This command will use docker-compose.yaml to bring up all the containers. Please update configuration/environment/localdev.env with values relevant to your organisation before running the below command
```bash
make serve
```

### Building and running the service using Dockerfiles
There are two ways to build and run the Dockerfiles. There are four Dockerfiles present in the repository, three of which are used to generate a individual image for each container needed for this service to work, and the fourth one is a Dockerfile setup to create a image that can be used to either bring up the Flask application or the celery worker depending on the DEADSHOT_RUN_MODE environment variable value provided
To run any of the steps below you need to be present in the root folder of the repository
#### Building images from individual Dockerfiles
There are three Dockerfiles relevant to this step. Dockerfile.api, Dockerfile.celery, and Dockerfile.redis
###### To build the Flask API image
```
docker build -f Dockerfile.api -t deadshot-api:<version> .
```

###### To build the celery image
```
docker build -f Dockerfile.celery -t deadshot-worker:<version> .
```

###### To build the redis image
```
docker build -f Dockerfile.redis -t deadshot-redis:<version> .
```

#### Running built images
The three images built in the previous steps all run in separate networks due to which they won't be able to talk to each other. To enable inter-container communications we need to add them to a container network

##### Create a docker network
```
docker network create deadshot-network
```
Run the images using the created network in the following order:
Start redis container
```
docker run --net deadshot-network --name redis deadshot-redis:<version>
```

Start celery container:
```
docker run --net deadshot-network deadshot-worker:<version>
```

Start Flask API container:
```
docker run --net deadshot-network -p 9001:9001 deadshot-api:<version>
```

### Building and running a single image for Flask API container and celery worker container
#### This step is useful only if you have a orchestration that allows you to feed in environment variables, secrets and other configurations at deployment time. Please use the above method of running the containers if you don't have a configurable CI/CD setup.
To build a single docker image for bringing up the api and celery worker based on DEADSHOT_RUN_MODE environment variable
```bash
make build
```
This command will also create the redis image that is needed for service

If the built image is run with the environment variable DEADSHOT_RUN_MODE=api, it will bring up the Flask application
If the image is run with environment variable DEADSHOT_RUN_MODE=worker then the celery worker will be initiated

### Server Healthcheck
Now that the API is ready to receive requests navigating to `http://localhost:9001/api/v1/heartbeat` in a browser should return a valid response or you could do a curl
```bash
curl loaclhost:9001/api/v1/healthcheck
```
Both should show the following message:
`{"healthcheck": "ready"}`

### Running a Pull Request scan
If you have a webhook payload of the Github app for your Pull Request then you can run the following curl command locally to test your application:
```bash
curl -X POST -H "content-type: application/json" -H "X-GitHub-Enterprise-Host: github.mockcompany.com" -H "X-Hub-Signature: sha1=85df4936c6396c149be94144befab41168149840" -H "X-GitHub-Event: pull_request" -d @tests/fixtures/good_pr.json http://localhost:9001/api/v1/deadshot-webhook
```

## Limitations
At this time, Deadshot has only tested with Github Enterprise, but should work with Github cloud as well.
