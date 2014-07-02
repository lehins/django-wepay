from django.conf.global_settings import *
import os, sys

BASE_PATH = os.path.join(os.path.dirname(__file__), '..')

sys.path.insert(0, BASE_PATH)

DEBUG = False
SECRET_KEY = 'django-wepay'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
}


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.sites',
    
    'djwepay',
    'wepay_app',
)

SITE_ID = 1

WEPAY_APP_ID = 12345

WEPAY_PRODUCTION = True

WEPAY_DEBUG = DEBUG

WEPAY_THROTTLE_PROTECT = True

WEPAY_API_BACKEND = 'wepay_app.backends.TestWePay'

WEPAY_MODELS = (
    ('app', 'wepay_app.WePayApp'),
    ('user', 'wepay_app.WePayUser'),
    ('account', 'wepay_app.WePayAccount'),
    ('checkout', 'wepay_app.WePayCheckout'),
    ('preapproval', 'wepay_app.WePayPreapproval'),
    ('withdrawal', 'wepay_app.WePayWithdrawal'),
    ('credit_card', 'wepay_app.WePayCreditCard'),
    ('subscription_plan', 'wepay_app.WePaySubscriptionPlan'),
    ('subscription', 'wepay_app.WePaySubscription'),
    ('subscription_charge', 'wepay_app.WePaySubscriptionCharge')
)
