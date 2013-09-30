from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db.models.loading import get_model
from django.utils.functional import LazyObject

from djwepay.decorators import cached_property
from djwepay.signals import state_changed
from djwepay.utils import from_string_import
from wepay.exceptions import WePayError

__all__ = ['AppApi', 'UserApi', 'AccountApi', 'CheckoutApi', 'PreapprovalApi',
           'WithdrawalApi', 'CreditCardApi', 'DEFAULT_SCOPE', 
           'get_wepay_model', 'get_wepay_model_name', 'is_abstract']

# default is full access
DEFAULT_SCOPE = getattr(
    settings, 'WEPAY_DEFAULT_SCOPE', "manage_accounts,collect_payments,"
    "view_balance,view_user,preapprove_payments,send_money")

DEFAULT_MODELS = (
    ('app', 'djwepay.App'),
    ('user', 'djwepay.User'),
    ('account', 'djwepay.Account'),
    ('checkout', 'djwepay.Checkout'),
    ('preapproval', 'djwepay.Preapproval'),
    ('withdrawal', 'djwepay.Withdrawal'),
    ('credit_card', 'djwepay.CreditCard')
)

MODELS = getattr(settings, 'WEPAY_MODELS', ())

API_BACKEND = getattr(settings, 'WEPAY_API_BACKEND', 'djwepay.backends.WePay')

def get_wepay_model_name(obj_name):
    return dict(DEFAULT_MODELS + MODELS).get(obj_name)

def get_wepay_model(obj_name):
    model_name = get_wepay_model_name(obj_name)
    if model_name is None:
        return None
    return get_model(*model_name.split('.'))

def is_abstract(obj_name):
    return not get_wepay_model_name(obj_name) == dict(DEFAULT_MODELS).get(obj_name)
    

class WePayLazy(LazyObject):
    def _setup(self):
        backend = from_string_import(API_BACKEND)
        self._wrapped = backend(get_wepay_model('app').objects.get_current())


class Api(object):

    api = WePayLazy()

    def _api_create(self, obj_name, response):
        model = get_wepay_model(obj_name)
        if obj_name == 'user':
            try:
                obj = model.objects.get(pk=response['user_id'])
            except model.DoesNotExist:
                pass
        obj = model()
        for key, value in response.iteritems():
            setattr(obj, key, value)
        return (obj, response)
        
    def _api_update(self, response):
        previous_state = getattr(self, 'state', '') # app object doesn't have state
        new_state = response.get('state', '')
        for key, value in response.iteritems():
            setattr(self, key, value)
        if new_state and new_state != previous_state:
            # using cache we eliminate duplicate calls to state_changed,
            # which has a chance of happening in multithreaded environment
            cache_key = "state_changed_%s_%s" % (type(self).__name__, self.pk)
            added = cache.add(cache_key, new_state)
            if not added:
                stored_state = cache.get(cache_key)
                if stored_state == new_state:
                    return response
            added = cache.set(cache_key, new_state)                
            state_changed.send(sender=type(self), instance=self, 
                               previous_state=previous_state)
        return response

    def _api_uri_modifier(self, kwargs, name):
        if name in kwargs:
            uri = self.api.get_full_uri(kwargs[name])
            kwargs.update({
                name: uri
            })
            return uri
        return None

    def _api_callback_uri(self, **kwargs):
        return self.api.get_full_uri(
            reverse('wepay:ipn', kwargs=kwargs))
    
    def api_batch_create(self, *args, **kwargs):
        return self.api.batch_create(*args, **kwargs)

class AppApi(Api):
    """ App model mixin object that helps making related Api calls"""

    def api_app(self, **kwargs):
        return self._api_update(self.api.app(**kwargs))

    def api_app_modify(self, **kwargs):
        return self._api_update(self.api.app_modify(**kwargs))

    def api_oauth2_authorize(self, **kwargs):
        """
        Returns url where user can be send off to in order to grant access.
        """
        self._api_uri_modifier(kwargs, 'redirect_uri')
        return self.api.oauth2_authorize(**kwargs)

    def api_oauth2_token(self, **kwargs):
        if not self._api_uri_modifier(kwargs, 'callback_uri'):
            kwargs['callback_uri'] = self._api_callback_uri(obj_name='user')
        self._api_uri_modifier(kwargs, 'redirect_uri')
        response = self.api.oauth2_token( **kwargs)
        return self._api_create('user', response)

    def api_preapproval_create(self, **kwargs):
        if not self._api_uri_modifier(kwargs, 'callback_uri'):
            kwargs['callback_uri'] = self._api_callback_uri(obj_name='preapproval')
        self._api_uri_modifier(kwargs, 'redirect_uri')
        self._api_uri_modifier(kwargs, 'fallback_uri')
        response = self.api.preapproval_create(
            client_id=self.client_id, client_secret=self.client_secret, **kwargs)
        return self._api_create('preapproval', response)

    def api_preapproval_find(self, **kwargs):
        return self.api.preapproval_find(**kwargs)

    def api_credit_card_create(self, *args, **kwargs):
        response = self.api.credit_card_create(*args, **kwargs)
        return self._api_create('credit_card', response)

    def api_credit_card_find(self, **kwargs):
        return self.api.credit_card_find(**kwargs)

class UserApi(Api):

    callback_uri = None

    def api_user(self, **kwargs):
        return self._api_update(
            self.api.user(access_token=self.access_token, **kwargs))

    def api_user_modify(self, **kwargs):
        self._api_uri_modifier(kwargs, 'callback_uri') # update relative callback_uri
        response = self._api_update(self.api.user_modify(
            access_token=self.access_token, **kwargs))
        return response

    def api_account_create(self, **kwargs):
        self._api_uri_modifier(kwargs, 'image_uri')
        if not self._api_uri_modifier(kwargs, 'callback_uri'):
            kwargs['callback_uri'] = self._api_callback_uri(
                obj_name='account', user_id=self.user_id)
        response = self.api.account_create(access_token=self.access_token, **kwargs)
        account, repsponse = self._api_create('account', response)
        account.user = self
        return (account, response)

    def api_account_find(self, **kwargs):
        return self.api.account_find(
            access_token=self.access_token, **kwargs)

class AccountApi(Api):
    
    @cached_property
    def access_token(self):
        return self.user.access_token

    @cached_property
    def account_uri(self):
        return self.api_account().get('account_uri', None)

    @cached_property
    def verification_uri(self):
        return self.api_account().get('verification_uri', None)

    @cached_property
    def add_bank_uri(self):
        return self.api_account_add_bank().get('add_bank_uri', None)

    @cached_property
    def pending_balance(self):
        return self.api_account_balance().get('pending_balance', None)

    @cached_property
    def available_balance(self):
        return self.api_account_balance().get('available_balance', None)

    @cached_property
    def pending_amount(self):
        return self.api_account_balance().get('pending_amount', None)

    @cached_property
    def reserved_amount(self):
        return self.api_account_balance().get('reserved_amount', None)

    @cached_property
    def disputed_amount(self):
        return self.api_account_balance().get('disputed_amount', None)

    currency = "USD" # for now only USD is supported

    def api_account(self, **kwargs):
        try:
            return self._api_update(self.api.account(
                account_id=self.pk, access_token=self.access_token, **kwargs))
        except WePayError, e:
            if e.code == 3003: # The account has been deleted
                self.state = 'deleted'
                self.save()
            raise

    def api_account_modify(self, **kwargs):
        self._api_uri_modifier(kwargs, 'callback_uri')
        self._api_uri_modifier(kwargs, 'image_uri')
        response = self._api_update(self.api.account_modify(
            account_id=self.pk, access_token=self.access_token, **kwargs))
        return response
        
    def api_account_delete(self, **kwargs):
        response = self._api_update(self.api.account_delete(
            account_id=self.pk, access_token=self.access_token, **kwargs))
        self.save() # save deleted status right away
        return response

    def api_account_balance(self, **kwargs):
        return self._api_update(self.api.account_balance(
            account_id=self.pk, access_token=self.access_token, **kwargs))
        
    def api_account_add_bank(self, **kwargs):
        self._api_uri_modifier(kwargs, 'redirect_uri')
        return self._api_update(self.api.account_add_bank(
            account_id=self.pk, access_token=self.access_token, **kwargs))

    def api_account_set_tax(self, **kwargs):
        return self.api.account_set_tax(
            account_id=self.pk, access_token=self.access_token, **kwargs)

    def api_account_get_tax(self, **kwargs):
        return self.api.account_get_tax(
            account_id=self.pk, access_token=self.access_token, **kwargs)

    def _api_account_object_create(self, obj_name, **kwargs):
        if not self._api_uri_modifier(kwargs, 'callback_uri'):
            kwargs['callback_uri'] = self._api_callback_uri(
                obj_name=obj_name, user_id=self.user_id)
        self._api_uri_modifier(kwargs, 'redirect_uri')
        method_create = getattr(self.api, "%s_create" % obj_name)
        response = method_create(
            account_id=self.pk, access_token=self.access_token, **kwargs)
        obj, response = self._api_create(obj_name, response)
        obj.account = self
        return (obj, response)


    def api_checkout_create(self, **kwargs):
        return self._api_account_object_create('checkout', **kwargs)

    def api_preapproval_create(self, **kwargs):
        self._api_uri_modifier(kwargs, 'fallback_uri')
        return self._api_account_object_create('preapproval', **kwargs)

    def api_withdrawal_create(self,  **kwargs):
        return self._api_account_object_create('withdrawal', **kwargs)

    def api_checkout_find(self, **kwargs):
        return self.api.checkout_find(
            account_id=self.pk, access_token=self.access_token, **kwargs)

    def api_preapproval_find(self, **kwargs):
        return self.api.preapproval_find(
            account_id=self.account_id, access_token=self.access_token, **kwargs)

    def api_withdrawal_find(self, **kwargs):
        return self.api.withdrawal_find(
            account_id=self.pk, access_token=self.access_token, **kwargs)

class CheckoutApi(Api):

    @cached_property
    def access_token(self):
        return self.account.access_token

    @cached_property
    def redirect_uri(self):
        return self.api_checkout().get('redirect_uri', None)

    @cached_property
    def callback_uri(self):
        return self.api_checkout().get('callback_uri', None)

    @cached_property
    def dispute_uri(self):
        return self.api_checkout().get('dispute_uri', None)
        
    def api_checkout(self, **kwargs):
        return self._api_update(self.api.checkout(
            checkout_id=self.pk, access_token=self.access_token, **kwargs))

    def api_checkout_cancel(self, **kwargs):
        return self._api_update(self.api.checkout_cancel(
            checkout_id=self.pk, access_token=self.access_token, **kwargs))

    def api_checkout_refund(self, **kwargs):
        return self._api_update(self.api.checkout_refund(
            checkout_id=self.pk, access_token=self.access_token, **kwargs))

    def api_checkout_capture(self, **kwargs):
        return self._api_update(self.api.checkout_capture(
            checkout_id=self.pk, access_token=self.access_token, **kwargs))

    def api_checkout_modify(self, **kwargs):
        self._api_uri_modifier(kwargs, 'callback_uri')
        response = self._api_update(self.api.checkout_modify(
            checkout_id=self.pk, access_token=self.access_token, **kwargs))
        return response


class PreapprovalApi(Api):

    @cached_property
    def access_token(self):
        return self.account.access_token

    @cached_property
    def preapproval_uri(self):
        return self.api_preapproval().get('preapproval_uri', None)

    @cached_property
    def manage_uri(self):
        return self.api_preapproval().get('manage_uri', None)

    @cached_property
    def redirect_uri(self):
        return self.api_preapproval().get('redirect_uri', None)

    @cached_property
    def callback_uri(self):
        return self.api_preapproval().get('callback_uri', None)


    def api_preapproval(self, **kwargs):
        return self._api_update(self.api.preapproval(
            preapproval_id=self.pk, access_token=self.access_token, **kwargs))

    def api_preapproval_cancel(self, **kwargs):
        return self._api_update(self.api.preapproval_cancel(
            preapproval_id=self.pk, access_token=self.access_token, **kwargs))

    def api_preapproval_modify(self, **kwargs):
        self._api_uri_modifier(kwargs, 'callback_uri')
        response = self._api_update(self.api.preapproval_modify(
            preapproval_id=self.pk, access_token=self.access_token, **kwargs))
        return response


class WithdrawalApi(Api):

    @cached_property
    def access_token(self):
        return self.account.access_token

    @cached_property
    def withdrawal_uri(self):
        return self.api_withdrawal().get('withdrawal_uri', None)

    @cached_property
    def redirect_uri(self):
        return self.api_withdrawal().get('redirect_uri', None)

    @cached_property
    def callback_uri(self):
        return self.api_withdrawal().get('callback_uri', None)


    def api_withdrawal(self, **kwargs):
        return self._api_update(self.api.withdrawal(
            withdrawal_id=self.pk, access_token=self.access_token, **kwargs))

    def api_withdrawal_modify(self, **kwargs):
        self._api_uri_modifier(kwargs, 'callback_uri')
        return self._api_update(self.api.withdrawal_modify(
            withdrawal_id=self.pk, access_token=self.access_token, **kwargs))
        

class CreditCardApi(Api):
    def api_credit_card(self, **kwargs):
        return self._api_update(self.api.credit_card(
            credit_card_id=self.pk, **kwargs))

    def api_credit_card_authorize(self, **kwargs):
        return self._api_update(self.api.credit_card_authorize(
            credit_card_id=self.pk, **kwargs))

    def api_credit_card_delete(self, **kwargs):
        return self._api_update(self.api.credit_card_delete(
            credit_card_id=self.pk, **kwargs))

