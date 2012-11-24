from django.conf import settings

WEPAY_CLIENT_ID = getattr(settings, 'WEPAY_CLIENT_ID')
WEPAY_CLIENT_SECRET = getattr(settings, 'WEPAY_CLIENT_SECRET')
WEPAY_ACCOUNT_ID = getattr(settings, 'WEPAY_ACCOUNT_ID')
WEPAY_ACCESS_TOKEN = getattr(settings, 'WEPAY_ACCESS_TOKEN')

WEPAY_PRODUCTION = getattr(settings, 'WEPAY_PRODUCTION', False)

WEPAY_RETAIN_RECORDS = getattr(settings, 'WEPAY_RETAIN_RECORDS', True)

WEPAY_IPN_LIMIT = getattr(settings, 'WEPAY_IPN_LIMIT', (20, 10))

# Make sure to use trailing slash.
# Example https://example.com/ 
SITE_FULL_URL = getattr(settings, 'SITE_FULL_URL', None)

FORCE_SCRIPT_NAME = getattr(settings, 'FORCE_SCRIPT_NAME', '')

# default is full access
WEPAY_DEFAULT_SCOPE = getattr(
    settings, 'WEPAY_DEFAULT_SCOPE',
    "manage_accounts,collect_payments,view_balance,view_user,refund_payments,"
    "preapprove_payments,send_money")

WEPAY_OBJECTS_DEFAULTS = getattr(settings, 'WEPAY_OBJECTS_DEFAULTS', {
    'theme_object': {
        'name': 'default_theme',
        'primary_color': '3B1060',
        'secondary_color': 'F8F8F8',
        'background_color': 'F8F8F8',
        'button_color': 'F36B22',
        },
    'account': {
        'type': 'nonprofit',
        'image_uri': "https://www.mainstreetcrowd.com/static/images/msc_logo.png",
        },
    'checkout': {
        'app_fee': 0,
        'fee_payer': 'payee',
        'type': "DONATION",
        'shipping_fee': 0,
        },
    'preapproval': {
        'app_fee': 0,
        'fee_payer': 'payee',
        'require_shipping': False,
        'shipping_fee': 0,
        'charge_tax': False,
        'payer_email_message': 
        "Thank you for your contribution at Main Street Crowd",
        'payee_email_message': "Thank you for participation at Main Street Crowd",
        'frequency': 1,
        'auto_recur': False,
        'mode': 'iframe',
        'funding_sources': 'cc',
        }
    })

WEPAY_EXTRA_MODELS_MODULE = getattr(settings, 'WEPAY_EXTRA_MODELS_MODULE', None)
if WEPAY_EXTRA_MODELS_MODULE:
    WEPAY_EXTRA_MODELS = getattr(settings, 'WEPAY_EXTRA_MODELS', ())

# full list is: 
# ['WPUser', 'WPAccount', 'WPCheckout', 'WPPreapproval', 'WPWithdrawal']
WEPAY_FULL_MODELS = getattr(settings, 'WEPAY_FULL_MODELS', [])
