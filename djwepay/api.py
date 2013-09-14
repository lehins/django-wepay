from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db.models.loading import get_model
from django.utils.functional import LazyObject

from djwepay.decorators import cached_property
from djwepay.exceptions import WePayError
from djwepay.signals import state_changed
from djwepay.utils import from_string_import

__all__ = ['AppApi', 'UserApi', 'AccountApi', 'CheckoutApi', 'PreapprovalApi',
           'WithdrawalApi', 'CreditCardApi', 
           'get_wepay_model', 'get_wepay_model_name', 'is_abstract']

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
            state_changed.send(sender=type(self), instance=self, 
                               previous_state=previous_state)
        return response

    def _api_uri_modifier(self, kwargs, name='callback_uri'):
        if name in kwargs:
            uri = self.api.get_full_uri(kwargs[name])
            setattr(self, name, uri)
            kwargs.update({
                name: uri
            })
            return uri
        return None

    def _api_callback_uri(self, **kwargs):
        return self.api.get_full_uri(
            reverse('wepay:ipn', kwargs=kwargs))

    def _api_property_getter(self, prop_name, getter=None, updater=None):
        if getattr(self, prop_name, None) is None:
            if not getter is None and callable(getter):
                setattr(self, prop_name, getter(self))
            elif not updater is None and callable(updater):
                updater()
            else:
                raise ImproperlyConfigured(
                    "Needs either getter or updater params as a callable")
        return getattr(self, prop_name, None)

class AppApi(Api):

    def api_app(self, **kwargs):
        return self._api_update(self.api.app(**kwargs))

    def api_app_modify(self, **kwargs):
        return self._api_update(self.api.app_modify(**kwargs))

    def api_oauth2_authorize(self, redirect_uri, **kwargs):
        return self.api.oauth2_authorize(
            self.api.get_full_uri(redirect_uri), **kwargs)

    def api_oauth2_token(self, redirect_uri, code, **kwargs):
        if not self._api_uri_modifier(kwargs):
            kwargs['callback_uri'] = self._api_callback_uri(obj_name='user')
        response = self.api.oauth2_token(
            self.api.get_full_uri(redirect_uri), code, **kwargs)
        return self._api_create('user', response)

    def api_preapproval_create(self, *args, **kwargs):
        if not self._api_uri_modifier(kwargs):
            kwargs['callback_uri'] = self._api_callback_uri(obj_name='preapproval')
        self._api_uri_modifier(kwargs, name='redirect_uri')
        self._api_uri_modifier(kwargs, name='fallback_uri')
        response = self.api.preapproval_create(
            self.client_id, *args, access_token=self.client_secret, **kwargs)
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
        self._api_uri_modifier(kwargs) # update relative callback_uri
        response = self._api_update(self.api.user_modify(
            access_token=self.access_token, **kwargs))
        return response

    def api_account_create(self, *args, **kwargs):
        if not self._api_uri_modifier(kwargs):
            kwargs['callback_uri'] = self._api_callback_uri(
                obj_name='account', user_id=self.user_id)
        response = self.api.account_create(
            *args, access_token=self.access_token, **kwargs)
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
        return self.api_account_add_bank().get('account_uri', None)

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
                self.account_id, access_token=self.access_token, **kwargs))
        except WePayError, e:
            if e.code == 3003: # The account has been deleted
                self.state = 'deleted'
                self.save()
            raise

    def api_account_modify(self, **kwargs):
        callback_uri = self._api_uri_modifier(kwargs)
        image_uri = self._api_uri_modifier(kwargs, name='image_uri')
        response = self._api_update(self.api.account_modify(
            self.account_id, access_token=self.access_token, **kwargs))
        if callback_uri or image_uri: # after the call is successfull, update model
            self.save()
        return response
        
    def api_account_delete(self, **kwargs):
        response = self._api_update(self.api.account_delete(
            self.account_id, access_token=self.access_token, **kwargs))
        self.save() # save deleted status right away
        return response

    def api_account_balance(self, **kwargs):
        return self._api_update(self.api.account_balance(
            self.account_id, access_token=self.access_token, **kwargs))
        
    def api_account_add_bank(self, **kwargs):
        self._api_uri_modifier(kwargs, name='redirect_uri')
        return self._api_update(self.api.account_add_bank(
            self.account_id, access_token=self.access_token, **kwargs))

    def api_account_set_tax(self, *args, **kwargs):
        return self.api.account_set_tax(
            self.account_id, *args, access_token=self.access_token, **kwargs)

    def api_account_get_tax(self, **kwargs):
        return self.api.account_get_tax(
            self.account_id, access_token=self.access_token, **kwargs)

    def _api_account_object_create(self, obj_name, *args, **kwargs):
        if not self._api_uri_modifier(kwargs):
            kwargs['callback_uri'] = self._api_callback_uri(
                obj_name=obj_name, user_id=self.user_id)
        self._api_uri_modifier(kwargs, name='redirect_uri')
        method_create = getattr(self.api, "%s_create" % obj_name)
        response = method_create(
            self.account_id, *args, access_token=self.access_token, **kwargs)
        obj, response = self._api_create(obj_name, response)
        obj.account = self
        return (obj, response)


    def api_checkout_create(self, *args, **kwargs):
        return self._api_account_object_create('checkout', *args, **kwargs)

    def api_preapproval_create(self, *args,  **kwargs):
        return self._api_account_object_create('preapproval', *args, **kwargs)

    def api_withdrawal_create(self, *args,  **kwargs):
        return self._api_account_object_create('withdrawal', *args, **kwargs)

    def api_checkout_find(self, **kwargs):
        return self.api.checkout_find(
            self.account_id, access_token=self.access_token, **kwargs)

    def api_preapproval_find(self, **kwargs):
        return self.api.preapproval_find(
            account_id=self.account_id, access_token=self.access_token, **kwargs)

    def api_withdrawal_find(self, **kwargs):
        return self.api.withdrawal_find(
            self.account_id, access_token=self.access_token, **kwargs)

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
            self.checkout_id, access_token=self.access_token, **kwargs))

    def api_checkout_cancel(self, *args, **kwargs):
        return self._api_update(self.api.checkout_cancel(
            self.checkout_id, *args, access_token=self.access_token, **kwargs))

    def api_checkout_refund(self, *args, **kwargs):
        return self._api_update(self.api.checkout_refund(
            self.checkout_id, *args, access_token=self.access_token, **kwargs))

    def api_checkout_capture(self, **kwargs):
        return self._api_update(self.api.checkout_capture(
            self.checkout_id, access_token=self.access_token, **kwargs))

    def api_checkout_modify(self, **kwargs):
        self._api_uri_modifier(kwargs)
        response = self._api_update(self.api.checkout_modify(
            self.checkout_id, access_token=self.access_token, **kwargs))
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
            self.pk, access_token=self.access_token, **kwargs))

    def api_preapproval_cancel(self, **kwargs):
        return self._api_update(self.api.preapproval_cancel(
            self.pk, access_token=self.access_token, **kwargs))

    def api_preapproval_modify(self, **kwargs):
        self._api_uri_modifier(kwargs)
        response = self._api_update(self.api.preapproval_modify(
            self.pk, access_token=self.access_token, **kwargs))
        return response


class WithdrawalApi(Api):

    @cached_property
    def access_token(self):
        return self.account.access_token

    @property
    def withdrawal_uri(self):
        return self.api_withdrawal().get('withdrawal_uri', None)

    @property
    def redirect_uri(self):
        return self.api_withdrawal().get('redirect_uri', None)

    @property
    def callback_uri(self):
        return self.api_withdrawal().get('callback_uri', None)


    def api_withdrawal(self, **kwargs):
        return self._api_update(self.api.withdrawal(
            self.pk, access_token=self.access_token, **kwargs))

    def api_withdrawal_modify(self, **kwargs):
        self._api_uri_modifier(kwargs)
        return self._api_update(self.api.withdrawal_modify(
            self.pk, access_token=self.access_token, **kwargs))
        

class CreditCardApi(Api):
    def api_credit_card(self, **kwargs):
        return self._api_update(self.api.credit_card(self.pk, **kwargs))

    def api_credit_card_authorize(self, **kwargs):
        return self._api_update(self.api.credit_card_authorize(self.pk, **kwargs))

    def api_credit_card_delete(self, **kwargs):
        return self._api_update(self.api.credit_card_delete(self.pk, **kwargs))

