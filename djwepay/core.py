

__all__ = ["OAuth2Call", "AppCall", "UserCall", "AccountCall", "CheckoutCall", 
           "PreapprovalCall", "WithdrawalCall", "CreditCardCall", "BatchCall"]

class Call(object):
    _m = None

    def __init__(self, production=None, access_token=None):
        self._production = production,
        self._access_token = access_token
        self.m = WePayManager(production=production, access_token=access_token)

    @property
    def m(self):
        if self._m is None:
            raise ImproperlyConfigured(
                "Manager is not set. Calls should only be used from the WePay manger")
        return self._m
    
    @m.setter
    def m(self, value):
        self._m = value

    def _call(self, suffix=None, params=None):
        uri = self.prefix 
        if not suffix is None:
            uri+= suffix
        return self._handler.call(uri, params=params, access_token=None)



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

    def token(self, client_id, redirect_uri, client_secret, code, 
              callback_uri=None):
        """
        Once you have sent the user through the authorization end point and they have returned with a code, you can use that code to retrieve an access token for that user. The redirect uri will need to be the same as in the in :func:`~djwepay.core.OAuth2.authorize` step
        Note that when you request a new access_token with this call, we will automatically revoke all previously issued access_token for this user. Make sure you update the access_token you are using for a user each time you make this call.
        """

        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'client_secret': cient_secret,
            'code': code
        }
        if not callback_uri is None:
            params['callback_uri'] = callback_uri
        return self._call('/token', params)

class App(Call):
    prefix = '/app'

    def __call__(self, client_id, client_secret):
        params = {
            'client_id': client_id,
            'client_secret': cient_secret
        }
        return self._call(params=params)

    def modify(self, client_id, client_secret, theme_object=None, gaq_domains=None):
        params = {
            'client_id': client_id,
            'client_secret': cient_secret
        }
        if not theme_object is None:
            params['theme_object'] = theme_object
        if not gaq_domains is None:
            params['gaq_domains'] = gaq_domains
        return self._call('/modify', params)

class User(Call):
    prefix = '/user'
    
    def __call__(self):
        return self._handler.call(self.prefix)

    def modify(self, callback_uri=None):
        params = {} if callback_uri is None else {'callback_uri': callback_uri}
        return self._call('/modify', params)

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

    def __call__(self, account_id):
        return self._call(params={'account_id': account_id})

    def find(self, name=None, reference_id=None, sort_order=None):
        params = {}
        if not name is None:
            params['name'] = name
        if not reference_id is None:
            params['reference_id'] = reference_id
        if not sort_order is None:
            params['sort_order'] = sort_order
        return self._call('/find', params)

    def create(self, name, description, reference_id=None, type=None, image_uri=None,
               gaq_domains=None, theme_object=None, mcc=None, callback_uri=None):
        params = {
            'name': name,
            'description': description
        }
        if not reference_id is None:
            params['reference_id'] = reference_id
        if not type is None:
            params['type'] = type
        if not image_uri is None:
            params['image_uri'] = image_uri
        if not gaq_domains is None:
            params['gaq_domains'] = gaq_domains
        if not theme_object is None:
            params['theme_object'] = theme_object
        if not mcc is None:
            params['mcc'] = mcc
        if not callback_uri is None:
            params['callback_uri'] = callback_uri
        return self._call('/create', params)

    def modify(self, account_id, name=None, description=None, reference_id=None, 
               image_uri=None, gaq_domains=None, theme_object=None, 
               callback_uri=None):
        params = {
            'account_id': account_id
        }
        if not name is None:
            params['name'] = name
        if not description is None:
            params['description'] = description
        if not reference_id is None:
            params['reference_id'] = reference_id
        if not image_uri is None:
            params['image_uri'] = image_uri
        if not gaq_domains is None:
            params['gaq_domains'] = gaq_domains
        if not theme_object is None:
            params['theme_object'] = theme_object
        if not callback_uri is None:
            params['callback_uri'] = callback_uri
        return self._call('/modify', params)

    def delete(self, account_id, reason=None):
        params = {
            'account_id': account_id
        }
        if not reason is None:
            params['reason'] = reason
        return self._call('/delete', params)

    def balance(self, account_id):
        params = {
            'account_id': account_id
        }
        return self._call('/balance', params)
        
    def add_bank(self, account_id, mode=None, redirect_uri=None):
        params = {
            'account_id': account_id
        }
        if not mode is None:
            params['mode'] = mode
        if not redirect_uri is None:
            params['redirect_uri'] = redirect_uri
        return self._call('/add_bank', params)
        
    def set_tax(self, account_id, taxes):
        params = {
            'account_id': account_id,
            'taxes': taxes
        }
        return self._call('/set_tax', params)

    def get_tax(self, account_id):
        params = {
            'account_id': account_id
        }
        return self._call('/get_tax', params)

class Checkout(Call):
    prefix = '/checkout'

    def __call__(self, checkout_id):
        return self._call(params={'checkout_id': checkout_id})

    def find(self, account_id, start=None, limit=None, reference_id=None, 
             state=None, preapproval_id=None, start_time=None, end_time=None,
             sort_order=None, shipping_fee=None):
        params = {
            'account_id': account_id
        }
        if not start is None:
            params['start'] = start
        if not limit is None:
            params['limit'] = limit
        if not reference_id is None:
            params['reference_id'] = reference_id
        if not state is None:
            params['state'] = state
        if not preapproval_id is None:
            params['preapproval_id'] = preapproval_id
        if not start_time is None:
            params['start_time'] = start_time
        if not end_time is None:
            params['end_time'] = end_time
        if not sort_order is None:
            params['sort_order'] = sort_order
        if not shipping_fee is None:
            params['shipping_fee'] = shipping_fee
        return self._call('/find', params)

    def create(self, account_id, short_description, type, amount,
               long_description=None, payer_email_message=None, 
               payee_email_message=None, reference_id=None, app_fee=None, 
               fee_payer=None, redirect_uri=None, callback_uri=None, 
               fallback_uri=None, auto_capture=None, require_shipping=None,
               shipping_fee=None, charge_tax=None, mode=None, preapproval_id=None,
               prefill_info=None, funding_sources=None, payment_method_id=None,
               payment_method_type=None):
        params = {
            'account_id': account_id,
            'short_description': short_description,
            'type': type,
            'amount': amount
        }
        if not long_description is None:
            params['long_description'] = long_description
        if not payer_email_message is None:
            params['payer_email_message'] = payer_email_message
        if not payee_email_message is None:
            params['payee_email_message'] = payee_email_message
        if not reference_id is None:
            params['reference_id'] = reference_id
        if not callback_uri is None:
            params['callback_uri'] = callback_uri
        if not fallback_uri is None:
            params['fallback_uri'] = fallback_uri
        if not auto_capture is None:
            params['auto_capture'] = auto_capture
        if not require_shipping is None:
            params['require_shipping'] = require_shipping
        if not shipping_fee is None:
            params['shipping_fee'] = shipping_fee
        if not charge_tax is None:
            params['charge_tax'] = charge_tax
        if not mode is None:
            params['mode'] = mode
        if not preapproval_id is None:
            params['preapproval_id'] = preapproval_id
        if not prefill_info is None:
            params['prefill_info'] = prefill_info
        if not funding_sources is None:
            params['funding_sources'] = funding_sources
        if not payment_method_id is None:
            params['payment_method_id'] = payment_method_id
        if not payment_method_type is None:
            params['payment_method_type'] = payment_method_type
        return self._call('/create', params)

    def cancel(self, checkout_id, cancel_reason=None):
        params = {
            'checkout_id': checkout_id
        }
        if not cancel_reason is None:
            params['cancel_reason'] = cancel_reason
        return self._call('/cancel', params)

    def refund(self, checkout_id, refund_reason=None, amount=None, app_fee=None,
               payer_email_message=None, payee_email_message=None):
        params = {
            'checkout_id': checkout_id
        }
        if not refund_reason is None:
            params['refund_reason'] = refund_reason
        if not app_fee is None:
            params['app_fee'] = app_fee
        if not payer_email_message is None:
            params['payer_email_message'] = payer_email_message
        if not payee_email_message is None:
            params['payee_email_message'] = payee_email_message
        return self._call('/refund', params)

    def capture(self, checkout_id):
        params = {
            'checkout_id': checkout_id
        }
        return self._call('/capture', params)

    def modify(self, checkout_id, callback_uri=None):
        params = {
            'checkout_id': checkout_id
        }
        if not callback_uri is None:
            params['callback_uri'] = callback_uri
        return self._call('/modify', params)


class Preapproval(Call):
    prefix = '/preapproval'

    def __call__(self, preapproval_id):
        return self._call(params={'preapproval_id': preapproval_id})


class Withdrawal(Call):
    pass

class CreaditCard(Call):
    pass

class Batch(Call):
    pass
