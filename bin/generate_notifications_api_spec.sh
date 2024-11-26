#!/bin/bash

set -e

if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "You need to activate your virtual env before running this script"
    exit 1
fi

DJANGO_SETTINGS_MODULE=notifications_webhook.settings ./manage.py spectacular --file notifications-webhook.yaml --validate
