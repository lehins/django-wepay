from django.conf import settings

WEPAY_CLIENT_ID = getattr(settings, 'WEPAY_CLIENT_ID')
WEPAY_CLIENT_SECRET = getattr(settings, 'WEPAY_CLIENT_SECRET')
WEPAY_ACCOUNT_ID = getattr(settings, 'WEPAY_ACCOUNT_ID')
WEPAY_ACCESS_TOKEN = getattr(settings, 'WEPAY_ACCESS_TOKEN')

WEPAY_PRODUCTION = getattr(settings, 'WEPAY_PRODUCTION', False)

WEPAY_RETAIN_RECORDS = getattr(settings, 'WEPAY_RETAIN_RECORDS', True)

WEPAY_IPN_LIMIT = getattr(settings, 'WEPAY_IPN_LIMIT', (20, 10))

# Example https://example.com
SITE_FULL_URL = getattr(settings, 'SITE_FULL_URL', None)

FORCE_SCRIPT_NAME = getattr(settings, 'FORCE_SCRIPT_NAME', '')

# default is full access
WEPAY_DEFAULT_SCOPE = getattr(
    settings, 'WEPAY_DEFAULT_SCOPE',
    "manage_accounts,collect_payments,view_balance,view_user,refund_payments,"
    "preapprove_payments,send_money")

WEPAY_OBJECTS_DEFAULTS = getattr(settings, 'WEPAY_OBJECTS_DEFAULTS', {})

WEPAY_EXTRA_MODELS_MODULE = getattr(settings, 'WEPAY_EXTRA_MODELS_MODULE', None)
if WEPAY_EXTRA_MODELS_MODULE:
    WEPAY_EXTRA_MODELS = getattr(settings, 'WEPAY_EXTRA_MODELS', ())

# full list is: 
# ['WPUser', 'WPAccount', 'WPCheckout', 'WPPreapproval', 'WPWithdrawal']
WEPAY_FULL_MODELS = getattr(settings, 'WEPAY_FULL_MODELS', [])
