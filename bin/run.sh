#!/usr/bin/env bash


# DEADSHOT_RUN_MODE environment variable is set to
#  instruct container how to start up (either as Flask API,
#  or as Celery worker to run PR checks)
case "$DEADSHOT_RUN_MODE" in
    api)
        CMD="gunicorn -b 0.0.0.0:9001 --workers=5 \"deadshot:create_app()\""
        ;;

    worker)
        CMD="celery -A deadshot.worker.celery_initialization.celery worker --loglevel=INFO"
        ;;

    *)
        echo $"DEADSHOT_RUN_MODE must be set to 'api' or 'worker'"
        exit 1

esac
export PYTHONPATH=/home/twilio/app/deadshot
cd deadshot
echo "[>] Command set to: $CMD $CELERY_BROKER_HOST $CELERY_BROKER_PORT"
echo "[i] Going to wait for redis..."
/bin/bash $APP_DIR/bin/wait-for-it.sh $CELERY_BROKER_HOST:$CELERY_BROKER_PORT --timeout=60 --strict
echo "[i]    Done waiting. Exit code: $?"

if [ $? != 0 ]; then
    echo "Error: Redis DB not available after 60s"
    exit 1
fi

echo "Running: $CMD"
eval $CMD
