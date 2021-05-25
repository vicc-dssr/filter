"""
Django settings for filter project.

Generated by 'django-admin startproject' using Django 3.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""

from .base import *

DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
# MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get("DB_NAME"),
        'USER': os.environ.get("DB_USER"),
        'PASSWORD': os.environ.get("DB_PASSWORD"),
        'HOST': os.environ.get("DB_HOST"),
        'PORT': os.environ.get("DB_PORT"),
    }
}

INTERNAL_IPS = [
    '127.0.0.1', 'localhost'
]

STATIC_URL = '/static/'

