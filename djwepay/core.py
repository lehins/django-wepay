import urllib2, json, decimal, warnings

from wepay.api import WePay

from djwepay.exceptions import WePayError, WePayWarning

__all__ = ["WePayHandler", "OAuth2", "App", "User", "Account", "Checkout", 
           "Preapproval", "Withdrawal", "CreditCard", "Batch"]


class WePayHandler(WePay):

    def call(self, uri, params=None, access_token=None):
        """
        Same call function as in Python-SDK WePay API with some minor changes. 
        Decimal numbers are casted to float, header is changed to
        'Django WePay SDK' and error changed to djwepay.exceptions.WePayError 
        which also includes and error_code.
        Basically this is the place for all api calls.
        :param uri: API uri to call
        :type uri: string
        :param params: parameters to include in the call
        :type params: dict
        :param access_token: access_token to use for the call, mostly omitted.
        :type access_token: string
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


class Call(object):
    prefix = ''

    def __init__(self, production=True, access_token=None, handler=None, 
                 batch_mode=False, reference_id=None):
        self._production = production,
        self._access_token = access_token
        self._handler = handler
        self._batch_mode = batch_mode
        self._reference_id = reference_id
        
    def _call(self, suffix=None, params={}, allowed_params=[]):
        uri = self.prefix 
        if not suffix is None:
            uri+= suffix
        unrecognized_params = set(params) ^ set(allowed_params)
        if unrecognized_params:
            warnings.warn(
                "At least one of the parameters to the api call: '%s' is "
                "unrecognized. Allowed parameters are: '%s'. Unrecognized "
                "parameters are: '%s'." % 
                (uri, ', '.join(allowed_params), ', '.join(unrecognized_parasm)), 
                WePayWarning)
        if self._batch_mode:
            call = {
                'call': uri
            }
            if not self._access_token is None:
                call['authorization'] = self._access_token
            if not self._reference_id is None:
                call['reference_id'] = self._reference_id
            if params:
                call['parameters'] = params
            return call
        hander = self._handler or WePayHandler(
            production=self._production, access_token=self._access_token)
        return handler.call(uri, params=params, access_token=self._access_token)



class OAuth2(Call):
    prefix = '/oauth2'

    def authorize(self, client_id, redirect_uri, scope, 
                  state=None, user_name=None, user_email=None):
        """
        This is the endpoint that you send the user to so they can grant your application permission to make calls on their behalf. It is not an API call but an actual uri that you send the user to. You can either do a full redirect to this uri OR if you want to keep the user on your site, you can open the uri in a popup with our JS library.
        This method provides a full redirect option.
        The easiest implementation for OAuth2 is to redirect the user to WePay's OAuth2 authorization uri. The following parameters should be uri encoded to the endpoint uri:
        :param client_id: The client id issued to the app, found on your application's dashboard.
        :type client_id: int
        :param redirect_uri: The uri the user will be redirected to after authorization. Must have the same domain as the application.
        :type redirect_uri: string
        :param scope: A comma separated string list of permissions. Click here for a list of permissions.
        :type scope: string
        :param state: The opaque value the client application uses to maintain state.
        :type state: string
        :param user_name: The user name used to pre-fill the authorization form
        :type user_name: string
        :param user_email: The user email used to pre-fill the authorization form
        :type user_email: string
        :returns: string -- uri with the request parameters uri encoded.
        """

        options = {}
        if not user_name is None:
            options['user_name'] = user_name
        if not user_email is None:
            options['user_email'] = user_email
        if not state is None:
            options['state'] = state
        return self._handler.get_authorization_url(redirect_uri, client_id, 
                                                   options=options, scope=scope)

    def token(self, client_id, redirect_uri, client_secret, code, **kwargs):
        """
        Once you have sent the user through the authorization end point and they have returned with a code, you can use that code to retrieve an access token for that user. The redirect uri will need to be the same as in the in :func:`~djwepay.core.OAuth2.authorize` step
        Note that when you request a new access_token with this call, we will automatically revoke all previously issued access_token for this user. Make sure you update the access_token you are using for a user each time you make this call.
        """
        allowed_params = [
            'client_id', 'redirect_uri', 'client_secret', 'code', 'callback_uri',
        ]
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'client_secret': client_secret,
            'code': code
        }
        params.update(kwargs)
        return self._call('/token', params=params, allowed_params=allowed_params)

class App(Call):
    prefix = '/app'

    def __call__(self, client_id, client_secret, **kwargs):
        allowed_params = ['client_id', 'client_secret']
        params = {
            'client_id': client_id,
            'client_secret': cient_secret
        }
        params.update(kwargs)
        return self._call(params=params, allowed_params=allowed_params)

    def modify(self, client_id, client_secret, theme_object=None, gaq_domains=None):
        allowed_params = [
            'client_id', 'client_secret', 'theme_object', 'gaq_domains'
        ]
        params = {
            'client_id': client_id,
            'client_secret': cient_secret
        }
        return self._call('/modify', params, allowed_params=allowed_params)

class User(Call):
    prefix = '/user'
    
    def __call__(self, **kwargs):
        return self._handler.call(self.prefix, params=kwargs)

    def modify(self, **kwargs):
        allowed_params = ['callback_uri']
        return self._call('/modify', params=kwargs, allowed_params=allowed_params)

    def register(self, *args, **kwargs):
        raise NotImplementedError(
            "'%s/register' call is depricated and is not supported by this app" % \
            self.prefix)

    def resend_confirmation(self, *args, **kwargs):
        raise NotImplementedError(
            "'%s/resend_confirmation' call is depricated and is not supported by "
            "this app" % self.prefix)


class Account(Call):
    prefix = '/account'

    def __call__(self, account_id, **kwargs):
        allowed_params = ['account_id']
        params = {
            'account_id': account_id
        }
        params.update(kwargs)
        return self._call(params=params, allowed_params=allowed_params)

    def find(self, **kwargs):
        allowed_params = ['name', 'reference_id', 'sort_order']
        return self._call('/find', params=kwargs, allowed_params=allowed_params)

    def create(self, name, description, **kwargs):
        allowed_params = [
            'name', 'description', 'reference_id', 'type', 'image_uri',
            'gaq_domains', 'theme_object', 'mcc', 'callback_uri'
        ]
        params = {
            'name': name,
            'description': description
        }
        params.update(kwargs)
        return self._call('/create', params=params, allowed_params=allowed_params)

    def modify(self, account_id, **kwargs):
        allowed_params = [
            'account_id', 'name', 'description', 'reference_id', 'image_uri', 
            'gaq_domains', 'theme_object', 'callback_uri'
        ]
        params = {
            'account_id': account_id
        }
        params.update(kwargs)
        return self._call('/modify', params=params, allowed_params=allowed_params)

    def delete(self, account_id, **kwargs):
        allowed_params = ['account_id', 'reason']
        params = {
            'account_id': account_id
        }
        params.update(kwargs)
        return self._call('/delete', params=params, allowed_params=allowed_params)

    def balance(self, account_id, **kwargs):
        allowed_params = ['account_id']
        params = {
            'account_id': account_id
        }
        params.update(kwargs)
        return self._call('/balance', params, allowed_params=allowed_params)
        
    def add_bank(self, account_id, **kwargs):
        allowed_params = ['account_id', 'mode', 'redirect_uri']
        params = {
            'account_id': account_id
        }
        params.update(kwargs)
        return self._call('/add_bank', params=params, allowed_params=allowed_params)
        
    def set_tax(self, account_id, taxes, **kwargs):
        allowed_params = ['account_id', 'taxes']
        params = {
            'account_id': account_id,
            'taxes': taxes
        }
        params.update(kwargs)
        return self._call('/set_tax', params=params, allowed_params=allowed_params)

    def get_tax(self, account_id, **kwargs):
        allowed_params = ['account_id']
        params = {
            'account_id': account_id
        }
        params.update(kwargs)
        return self._call('/get_tax', params=params, allowed_params=allowed_params)

class Checkout(Call):
    prefix = '/checkout'

    def __call__(self, checkout_id, **kwargs):
        allowed_params = ['checkout_id']
        params = {
            'checkout_id': checkout_id
        }
        params.update(kwargs)
        return self._call(params=params, allowed_params=allowed_params)

    def find(self, account_id, **kwargs):
        allowed_params = [
            'account_id', 'start', 'limit', 'reference_id', 'state', 
            'preapproval_id', 'start_time', 'end_time', 'sort_order', 'shipping_fee'
        ]
        params = {
            'account_id': account_id
        }
        params.update(kwargs)
        return self._call('/find', params=params, allowed_params=allowed_params)

    def create(self, account_id, short_description, type, amount, **kwargs):
        allowed_params = [
            'account_id', 'short_description', 'type', 'amount', 'long_description', 
            'payer_email_message', 'payee_email_message', 'reference_id', 'app_fee',
            'fee_payer', 'redirect_uri', 'callback_uri', 'fallback_uri', 
            'auto_capture', 'require_shipping', 'shipping_fee', 'charge_tax', 'mode',
            'preapproval_id', 'prefill_info', 'funding_sources', 'payment_method_id',
            'payment_method_type'
        ]
        params = {
            'account_id': account_id,
            'short_description': short_description,
            'type': type,
            'amount': amount
        }
        params.update(kwargs)
        return self._call('/create', params=params, allowed_params=allowed_params)

    def cancel(self, checkout_id, **kwargs):
        allowed_params = ['checkout_id', 'cancel_reason']
        params = {
            'checkout_id': checkout_id
        }
        params.update(kwargs)
        return self._call('/cancel', params=params, allowed_params=allowed_params)

    def refund(self, checkout_id, **kwargs):
        allowed_params = [
            'checkout_id', 'refund_reason', 'amount', 'app_fee',
            'payer_email_message', 'payee_email_message'
        ]
        params = {
            'checkout_id': checkout_id
        }
        params.update(kwargs)
        return self._call('/refund', params=params, allowed_params=allowed_params)

    def capture(self, checkout_id, **kwargs):
        allowed_params = ['checkout_id']
        params = {
            'checkout_id': checkout_id
        }
        params.update(kwargs)
        return self._call('/capture', params=params, allowed_params=allowed_params)

    def modify(self, checkout_id, **kwargs):
        allowed_params = ['checkout_id', 'callback_uri']
        params = {
            'checkout_id': checkout_id
        }
        params.update(kwargs)
        return self._call('/modify', params=params, allowed_params=allowed_params)


class Preapproval(Call):
    prefix = '/preapproval'

    def __call__(self, preapproval_id, **kwargs):
        allowed_params = ['preapproval_id']
        params = {
            'preapproval_id': preapproval_id
        }
        params.update(kwargs)
        return self._call(params=params, allowed_params=allowed_params)

    def find(self, **kwargs):
        allowed_params = [
            'account_id', 'state', 'reference_id', 'start', 'limit', 'sort_order', 
            'last_checkout_id', 'shipping_fee'
        ]
        return self._call('/find', params=kwargs, allowed_params=allowed_params)

    def create(self, short_description, period, **kwargs):
        allowed_params = [
            'account_id', 'amount', 'short_description', 'period', 'reference_id', 
            'app_fee', 'fee_payer', 'redirect_uri', 'callback_uri', 'fallback_uri', 
            'require_shipping', 'shipping_fee', 'charge_tax', 'payer_email_message',
            'long_description', 'frequency', 'start_time','end_time', 'auto_recur',
            'mode', 'prefill_info', 'funding_sources', 'payment_method_id',
            'payment_method_type'
        ]
        params = {
            'short_description': short_description,
            'period': period
        }
        params.update(kwargs)
        return self._call('/create', params=params, allowed_params=allowed_params)

    def cancel(self, preapproval_id, **kwargs):
        allowed_params = ['preapproval_id']
        params = {
            'preapproval_id': preapproval_id
        }
        params.update(kwargs)
        return self._call('/cancel', params=params, allowed_params=allowed_params)

    def modify(self, preapproval_id, **kwargs):
        allowed_params = ['preapproval_id', 'callback_uri']
        params = {
            'preapproval_id': preapproval_id
        }
        params.update(kwargs)
        return self._call('/modify', params=params, allowed_params=allowed_params)

class Withdrawal(Call):
    prefix = '/withdrawal'

    def __call__(self, withdrawal_id, **kwargs):
        allowed_params = ['withdrawal_id']
        params = {
            'withdrawal_id': withdrawal_id
        }
        params.update(kwargs)
        return self._call(params=params, allowed_params=allowed_params)

    def find(self, account_id, **kwargs):
        allowed_params = ['account_id', 'limit', 'start', 'sort_order']
        params = {
            'account_id': account_id
        }
        params.update(kwargs)
        return self._call('/find', params=params, allowed_params=allowed_params)

    def create(self, account_id, **kwargs):
        allowed_params = [
            'account_id', 'redirect_uri', 'callback_uri', 'note', 'mode'
        ]
        params = {
            'account_id': account_id
        }
        params.update(kwargs)
        return self._call('/create', params=params, allowed_params=allowed_params)

    def modify(self, withdrawal_id, **kwargs):
        allowed_params = ['withdarwal_id', 'callback_uri']
        params = {
            'withdrawal_id': withdrawal_id
        }
        params.update(kwargs)
        return self._call('/modify', params=params, allowed_params=allowed_params)


class CreaditCard(Call):
    prefix = '/cedit_card'
    
    def __call__(self, client_id, client_secret, credit_card_id, **kwargs):
        allowed_params = ['client_id', 'client_secret', 'credit_card_id']
        params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'credit_card_id': credit_card_id
        }
        params.update(kwargs)
        return self._call(params=params, allowed_params=allowed_params)

    def create(self, client_id, cc_number, cvv, expiration_month, expiration_year,
               user_name, email, address, **kwargs):
        allowed_params = [
            'client_id', 'cc_number', 'cvv', 'expiration_month', 'expiration_year',
            'user_name', 'email', 'address'
        ]
        params = {
            'client_id': client_id,
            'cc_number': cc_number, 
            'cvv': cvv,
            'expiration_month': expiration_month,
            'expiration_year': expiration_year,
            'user_name': user_name,
            'email': email,
            'address': address
        }
        params.update(kwargs)
        return self._call('/create', params=params, allowed_params=allowed_params)

    def authorize(self, client_id, client_secret, credit_card_id, **kwargs):
        allowed_params = ['client_id', 'client_secret', 'credit_card_id']
        params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'credit_card_id': credit_card_id
        }
        params.update(kwargs)
        return self._call('/autorize', params=params, allowed_params=allowed_params)

    def find(self, client_id, client_secret, **kwargs):
        allowed_params = [
            'client_id', 'client_secret', 'reference_id', 'limit', 'start', 
            'sort_order'
        ]
        params = {
            'client_id': client_id,
            'client_secret': client_secret
        }
        params.update(kwargs)
        return self._call('/find', params=params, allowed_params=allowed_params)

    def delete(self, client_id, client_secret, credit_card_id, **kwargs):
        allowed_params = ['client_id', 'client_secret', 'credit_card_id']
        params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'credit_card_id': credit_card_id
        }
        params.update(kwargs)
        return self._call('/delete', params=params, allowed_params=allowed_params)

class Batch(Call):
    prefix = '/batch'
    batch_calls = []

    def create(self, client_id, client_secret, calls=None, **kwargs):
        allowed_params = ['client_id', 'client_secret', 'calls']
        if not calls is None:
            self.batch_calls.extend(calls)
        params = {
            'client_id', client_id,
            'client_secret': client_secret,
            'calls': self.batch_calls
        }
        params.update(kwargs)
        response = self._call('/create', params=params, allowed_params=allowed_params)
        self.bacth_calls = []

    def add_call(self, call, authorization=None, reference_id=None, 
                 args=None, kwargs=None):
        call_class = None
        call_suffix = None
        if isinstance(call, basestring):
            call_ls = call.split('.')
            call_class = getattr(__name__, call_ls[0])
            try:
                call_suffix = call_ls[1]
            except IndexError: pass
        else:
            raise AttributeError(
                "'call' parameter should be a string ex: 'Account.create'")
        call_obj = call_class(access_token=authorization, batch_mode=True,
                              reference_id=reference_id)
        call_func = call_obj if call_suffix is None else \
                    getattr(call_obj, call_suffix)
        batch_calls.append(call_func(*args, **kwargs))

