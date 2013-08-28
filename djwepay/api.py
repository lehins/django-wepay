from django.conf import settings

from djwepay import core

CLIENT_ID = getattr(settings, 'WEPAY_CLIENT_ID')
CLIENT_SECRET = getattr(settings, 'WEPAY_CLIENT_SECRET')

ACCESS_TOKEN = getattr(settings, 'WEPAY_ACCESS_TOKEN', None)
PRODUCTION = getattr(settings , 'WEPAY_PRODUCTION', True)

# default is full access
DEFAULT_SCOPE = getattr(
    settings, 'WEPAY_DEFAULT_SCOPE', "manage_accounts,collect_payments,"
    "view_balance,view_user,preapprove_payments,send_money")

DEFAULT_CREATE = getattr(settings, 'WEPAY_OBJECTS_DEFAULT_CREATE', {})

class ApiCall(core.Call):
    def __init__(self, production=PRODUCTION, access_token=ACCESS_TOKEN,
                 client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                 local_object=None, **kwargs):
        self.local_object = local_object
        self._client_id = client_id
        self._client_secret = client_secret
        self._defaults = DEFAULT_CREATE
        super(ApiCall, self).__init__(
            production=production, access_token=access_token, **kwargs)

class OAuth2Call(ApiCall, core.OAuth2):
    def authorize(self, redirect_uri, **kwargs):
        return super(OAuth2Call, self).authorize(
            self._client_id, redirect_uri, DEFAULT_SCOPE, **kwargs)
        
    def token(self, redirect_uri, code, **kwargs):
        return super(OAuth2Call, self).token(
            self._client_id, redirect_uri, self._client_secret, code, **kwargs)

class AppCall(ApiCall, core.App):
    
    def __call__(self, **kwargs):
        return super(AppCall, self).__call__(
            self._client_id, self._client_secret, **kwargs)


    def modify(self, **kwargs):
        return super(AppCall, self).modify(
            self._client_id, self._client_secret, **kwargs)

class UserCall(ApiCall, core.User, OAuth2Call):
    def __call__(self, **kwargs):
        return super(UserCall, self).__call__(**kwargs)

    def create(self, *args, **kwargs):
        return self.token(*args, **kwargs)

class AccountCall(ApiCall, core.Account):
    
    def __call__(self, **kwargs):
        return super(AccountCall, self).__call__(self.local_object.pk, **kwargs)

    def create(self, *args, **kwargs):
        kwargs_new = {}
        if 'account' in self._defaults:
            kwargs_new.update(self._defaults['account'])
        kwargs_new.update(kwargs)
        return super(AccountCall, self).create(*args, **kwargs_new)

    def modify(self, **kwargs):
        return super(AccountCall, self).modify(self.local_object.pk, **kwargs)
        
    def delete(self, **kwargs):
        return super(AccountCall, self).delete(self.local_object.pk, **kwargs)

    def balance(self, **kwargs):
        return super(AccountCall, self).balance(self.local_object.pk, **kwargs)
        
    def add_bank(self, **kwargs):
        return super(AccountCall, self).add_bank(self.local_object.pk, **kwargs)

    def set_tax(self, taxes, **kwargs):
        return super(AccountCall, self).set_tax(self.local_object.pk, taxes, **kwargs)

    def get_tax(self, **kwargs):
        return super(AccountCall, self).get_tax(self.local_object.pk, **kwargs)

class CheckoutCall(ApiCall, core.Checkout):

    def __call__(self, **kwargs):
        return super(CheckoutCall, self).__call__(self.local_object.pk, **kwargs)

    def create(self, *args, **kwargs):
        kwargs_new = {}
        if 'checkout' in self._defaults:
            kwargs_new.update(self._defaults['checkout'])
        kwargs_new.update(kwargs)
        return super(CheckoutCall, self).create(*args, **kwargs_new)

    def cancel(self, cancel_reason, **kwargs):
        return super(CheckoutCall, self).cancel(
            self.local_object.pk, cancel_reason, **kwargs)

    def refund(self, refund_reason, **kwargs):
        return super(CheckoutCall, self).refund(
            self.local_object.pk, refund_reason, **kwargs)

    def capture(self, **kwargs):
        return super(CheckoutCall, self).capture(self.local_object.pk, **kwargs)

    def modify(self, **kwargs):
        return super(CheckoutCall, self).modify(self.local_object.pk, **kwargs)


class PreapprovalCall(ApiCall, core.Preapproval):
    def __call__(self, **kwargs):
        return super(PreapprovalCall, self).__call__(self.local_object.pk, **kwargs)

    def create(self, *args, **kwargs):
        kwargs_new = {}
        if 'preapproval' in self._defaults:
            kwargs_new.update(self._defaults['preapproval'])
        kwargs_new.update(kwargs)
        return super(PreapprovalCall, self).create(*args, **kwargs_new)

    def cancel(self, **kwargs):
        return super(PreapprovalCall, self).cancel(self.local_object.pk, **kwargs)

    def modify(self, **kwargs):
        return super(PreapprovalCall, self).modify(self.local_object.pk, **kwargs)

class WithdrawalCall(ApiCall, core.Withdrawal):
    def __call__(self, **kwargs):
        return super(WithdrawalCall, self).__call__(self.local_object.pk, **kwargs)

    def create(self, *args, **kwargs):
        kwargs_new = {}
        if 'withdrawal' in self._defaults:
            kwargs_new.update(self._defaults['withdrawal'])
        kwargs_new.update(kwargs)
        return super(WithdrawalCall, self).create(*args, **kwargs_new)

    def modify(self, **kwargs):
        return super(WithdrawalCall, self).modify(self.local_object.pk, **kwargs)

class CreditCardCall(ApiCall, core.CreditCard):
    def __call__(self, **kwargs):
        return super(CreditCardCall, self).__call__(
            self._client_id, self._client_secret, self.local_object.pk, **kwargs)

    def create(self, cc_number, cvv, expiration_month, expiration_year,
               user_name, email, address, **kwargs):
        return super(CreditCardCall, self).create(
            self._clinet_id, cc_number, cvv, expiration_month, expiration_year,
            user_name, email, address, **kwargs)

    def authorize(self, **kwargs):
        return super(CreditCardCall, self).authorize(
            self._client_id, self._client_secret, self.local_object.pk, **kwargs)

    def find(self, **kwargs):
        return super(CreditCardCall, self).find(
            self._client_id, self._client_secret, **kwargs)

    def delete(self, **kwargs):
        return super(CreditCardCall, self).delete(
            self._client_id, self._client_secret, self.local_object.pk, **kwargs)

class BatchCall(ApiCall, core.Batch):
    pass


class WePay(core.WePayHandler):

    oauth2 = OAuth2Call
    app = AppCall
    user = UserCall
    account = AccountCall
    checkout = CheckoutCall
    preapproval = PreapprovalCall
    withdrawal = WithdrawalCall
    credit_card = CreditCardCall
    batch = BatchCall

    _calls_supported = ['oauth2', 'app', 'user', 'account', 'checkout', 
                        'preapproval', 'withdrawal', 'credit_card', 'batch']

    def __init__(self, production=PRODUCTION, access_token=ACCESS_TOKEN):
        super(WePay, self).__init__(production=production, access_token=access_token)
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        for call_name in self._calls_supported:
            call_class = getattr(self, call_name)
            call = call_class(
                production=production, access_token=access_token, handler=self)
            setattr(self, call_name, call)


