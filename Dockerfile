FROM python:3.9.0-buster

RUN apt-get update
RUN pip install --upgrade pip

ENV APP_USER twilio
ENV FLASK_APP deadshot
ENV APP_DIR /home/twilio/app/deadshot
ENV APP_INSTALL_DIR /app/deadshot
ENV DEADSHOT_RUN_MODE api

RUN mkdir -p /home/twilio
RUN groupadd -r twilio &&\
    useradd -r -g twilio -d /home/twilio -s /sbin/nologin -c "Twilio Docker image user" twilio

RUN chown twilio /home/twilio
RUN chgrp twilio /home/twilio

RUN mkdir -p $APP_INSTALL_DIR
COPY deadshot $APP_INSTALL_DIR/deadshot
COPY bin $APP_INSTALL_DIR/bin
COPY local_dev_secrets $APP_DIR/secrets
COPY requirements.txt $APP_INSTALL_DIR
ENV SECRET_GITHUB_SECRETS $APP_DIR/secrets/github_secrets.json
ENV SECRET_SLACK_WEBHOOKS $APP_DIR/secrets/slack_webhook.json
ENV SECRET_JIRA_AUTH $APP_DIR/secrets/jira_user.json
RUN pip3 install -r $APP_INSTALL_DIR/requirements.txt

USER $APP_USER
RUN mkdir -p $APP_DIR

ADD --chown=twilio:twilio deadshot $APP_DIR/deadshot
ADD --chown=twilio:twilio bin $APP_DIR/bin
WORKDIR $APP_DIR

EXPOSE 9001

CMD (/bin/bash ./bin/run.sh)
