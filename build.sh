#!/usr/bin/env bash
set -euo pipefail

echo "==> Installing dependencies via Pipenv"
pip install --upgrade pip
pip install pipenv
pipenv install --deploy --ignore-pipfile

echo "==> Running migrations"
pipenv run python manage.py migrate --noinput

echo "==> Collecting static files"
pipenv run python manage.py collectstatic --noinput
