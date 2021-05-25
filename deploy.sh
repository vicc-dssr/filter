#!/bin/sh

source venv/bin/activate
pip install -r requirements.txt
export DJANGO_SETTINGS_MODULE=filter.settings.local
export DB_NAME=
export DB_USER=
export DB_PASSWORD=
export DB_HOST=
export DB_PORT=
export EMAIL_PORT=
export EMAIL_HOST=
export EMAIL_HOST_USER=
export EMAIL_HOST_PASSWORD=
python manage.py migrate
python manage.py runserver