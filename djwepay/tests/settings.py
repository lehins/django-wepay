from django.conf.global_settings import *
import os, sys

BASE_PATH = os.path.join(os.path.dirname(__file__), '../..')

sys.path.insert(0, BASE_PATH)

DEBUG = True
SECRET_KEY = 'django-wepay'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
}


INSTALLED_APPS = (
    'django.contrib.admin',
    'djwepay'
)

