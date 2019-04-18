#!/bin/bash

set -e

if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "You need to activate your virtual env before running this script"
    exit 1
fi

toplevel=$(git rev-parse --show-toplevel)
cd $toplevel

./manage.py generate_swagger \
    --overwrite \
    -f yaml \
    notifications-webhook-2.0.yaml

echo "Converting Swagger to OpenAPI 3.0..."
npm run convert

MANAGE=manage.py ./bin/patch_content_types notifications-webhook.yaml
