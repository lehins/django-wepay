import urllib2, json, decimal

from django.conf import settings

from wepay.api import WePay as WePayAPI

from .core import *
from .exceptions import WePayError

CLIENT_ID = getattr(settings, 'WEPAY_CLIENT_ID')
CLIENT_SECRET = getattr(settings, 'WEPAY_CLIENT_SECRET')
ACCOUNT_ID = getattr(settings, 'WEPAY_ACCOUNT_ID')

ACCESS_TOKEN = getattr(settings, 'WEPAY_ACCESS_TOKEN', None)
PRODUCTION = getattr(settings , 'WEPAY_PRODUCTION', True)

# default is full access
DEFAULT_SCOPE = getattr(
    settings, 'WEPAY_DEFAULT_SCOPE', "manage_accounts,collect_payments,"
    "view_balance,view_user,preapprove_payments,send_money")

class WePayBase(WePayAPI):

    def call(self, uri, params=None, access_token=None):
        """
        Same call function as python Wepay API. Except header is changed to
        Django WePay SDK.
        Basically this is the place for all api calls.
        :param str uri API uri to call
        :param dict params to include in the call
        :param str access_token to use for the call, mostly omitted.
        """
        headers = {'Content-Type' : 'application/json', 
                   'User-Agent' : 'Django WePay SDK'}
        url = self.api_endpoint + uri
        
        headers['Authorization'] = 'Bearer ' + (token or self.access_token)
            
        if params:
            for key, value in params.iteritems():
                if isinstance(params[key], decimal.Decimal):
                    params[key] = float(params[key])
            params = json.dumps(params)

        request = urllib2.Request(url, params, headers)
        try:
            response = urllib2.urlopen(request, timeout=30).read()
            return json.loads(response)
        except urllib2.HTTPError as e:
            response = json.loads(e.read())
            raise WePayError(response['error'], response['error_description'], 
                             error_code=['error_code'])


class WePay(WePayBase):

    oauth2 = OAuth2Call()
    app = AppCall()
    user = UserCall()
    account = AccountCall()
    checkout = CheckoutCall()
    preapproval = PreapprovalCall()
    withdrawal = WithdrawalCall()
    credit_card = CreditCardCall()
    batch = BatchCall()

    calls_supported = ['oauth2', 'app', 'user', 'account', 'checkout', 
                       'preapproval', 'withdrawal', 'credit_card', 'batch']

    def __init__(self, production=PRODUCTION, access_token=ACCESS_TOKEN):
        super(WePay, self).__init__(production=production, access_token=access_token)
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        for call in self.calls_supported:
            setattr(self, 'm', self)


