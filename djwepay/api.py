from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db.models.loading import get_model

from djwepay.exceptions import WePayError
from djwepay.signals import state_changed

__all__ = ['AppApi', 'UserApi', 'AccountApi', 'CheckoutApi', 'PreapprovalApi',
           'WithdrawalApi', 'CreditCardApi', 
           'get_wepay_model', 'get_wepay_model_name']

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

def get_wepay_model_name(obj_name):
    return dict(DEFAULT_MODELS + MODELS).get(obj_name)

def get_wepay_model(obj_name):
    model_name = get_wepay_model_name(obj_name)
    if model_name is None:
        return None
    return get_model(*model_name.split('.'))

def is_abstract(obj_name):
    return not get_wepay_model_name(obj_name) == dict(DEFAULT_MODELS).get(obj_name)
    

class Api(object):

    def _api_create(self, obj_name, response, update, commit):
        object_id_key = "%s_id" % obj_name
        model = get_wepay_model(obj_name)
        try:
            obj = model.objects.get(pk=response[object_id_key])
            obj._api_update(response)
            if not obj.active():
                obj.undelete()
        except model.DoesNotExist:
            obj = model(**response)
        if update:
            call_method = getattr(self.api, obj_name)
            params = {
                'access_token': self.access_token
            }
            if obj_name == 'user':
                params = {
                    'access_token': response['access_token']
                }
            elif obj_name != 'credit_card':
                params = {
                    'access_token': self.access_token,
                    object_id_key: response[object_id_key]
                }
            response = obj._api_update(
                call_method(**params), should_update=update)
        if commit and update:
            obj.save()
        return (obj, response)
        
    def _api_update(self, response, should_update=True):
        if should_update:
            previous_state = None
            for key, value in response.iteritems():
                if key == 'state' and value != self.state:
                    previous_state = self.state
                setattr(self, key, value)
            if not previous_state is None:
                state_changed.send(sender=self.__class__, instance=self, 
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

    def _api_callback_uri(self, obj_name, **kwargs):
        return self.api.get_full_uri(
            reverse('wepay:ipn:%s' % obj_name, kwargs=kwargs))

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
        update = kwargs.pop('update', True)
        commit = kwargs.pop('commit', True)
        if 'callback_uri' not in kwargs:
            kwargs['callback_uri'] = self.api.get_full_uri(
                reverse('wepay:ipn:user'))
        else:
            kwargs.update({
                'callback_uri': self.api.get_full_uri(kwargs['callback_uri'])
            })
        response = self.api.oauth2_token(
            self.api.get_full_uri(redirect_uri), code, **kwargs)
        return self._api_create('user', response, update, commit)

    def api_preapproval_create(self, *args, **kwargs):
        update = kwargs.pop('update', True)
        commit = kwargs.pop('commit', True)
        if not self._api_uri_modifier(kwargs):
            kwargs['callback_uri'] = self._api_callback_uri('preapproval')
        self._api_uri_modifier(kwargs, name='redirect_uri')
        self._api_uri_modifier(kwargs, name='fallback_uri')
        response = self.api.preapproval_create(
            self.client_id, *args, access_token=self.client_secret, **kwargs)
        return self._api_create('preapproval', response, update, commit)

    def api_preapproval_find(self, **kwargs):
        return self.api.preapproval_find(**kwargs)

    def api_credit_card_create(self, *args, **kwargs):
        update = kwargs.pop('update', True)
        commit = kwargs.pop('commit', True)
        response = self.api.credit_card_create(*args, **kwargs)
        return self._api_create('credit_card', response, update, commit)

    def api_credit_card_find(self, **kwargs):
        return self.api.credit_card_find(**kwargs)

class UserApi(Api):

    def get_callback_uri(self):
        return reverse('wepay:ipn:user')

    def api_user(self, **kwargs):
        return self._api_update(
            self.api.user(access_token=self.access_token, **kwargs))

    def api_user_modify(self, **kwargs):
        callback_uri = self._api_uri_modifier(kwargs)
        response = self._api_update(self.api.user_modify(
            access_token=self.access_token, **kwargs))
        if callback_uri:
            self.save()
        return response

    def api_account_create(self, *args, **kwargs):
        update = kwargs.pop('update', True)
        commit = kwargs.pop('commit', True)
        if not self._api_uri_modifier(kwargs):
            kwargs['callback_uri'] = self._api_callback_uri(
                'account', user_id=self.pk)
        response = self.api.account_create(
            *args, access_token=self.access_token, **kwargs)
        account, response = self._api_create('account', response, update, False)
        account.user = self
        if commit:
            account.save()
        return account, response

    def api_account_find(self, **kwargs):
        return self.api.account_find(
            access_token=self.access_token, **kwargs)

class AccountApi(Api):

    @property
    def access_token(self):
        return self._api_property_getter(
            '_access_token', lambda inst: inst.user.access_token)

    @access_token.setter
    def access_token(self, value):
        self._access_token = value

    @property
    def pending_balance(self):
        return self._api_property_getter(
            '_pending_balance', updater=self.api_account_balance)

    @pending_balance.setter
    def pending_balance(self, value):
        self._pending_balance = value

    @property
    def available_balance(self):
        return self._api_property_getter(
            '_available_balance', updater=self.api_account_balance)

    @available_balance.setter
    def available_balance(self, value):
        self._available_balance = value

    @property
    def pending_amount(self):
        return self._api_property_getter(
            '_pending_amount', updater=self.api_account_balance)

    @pending_amount.setter
    def pending_amount(self, value):
        self._pending_amount = value

    @property
    def reserved_amount(self):
        return self._api_property_getter(
            '_reserved_amount', updater=self.api_account_balance)

    @reserved_amount.setter
    def reserved_amount(self, value):
        self._reserved_amount = value

    @property
    def disputed_amount(self):
        return self._api_property_getter(
            '_disputed_amount', updater=self.api_account_balance)

    @disputed_amount.setter
    def disputed_amount(self, value):
        self._disputed_amount = value

    currency = "USD" # for now only USD is supported


    def get_callback_uri(self):
        return self._api_callback_uri('account', user_id = self.user_id)

    def api_account(self, **kwargs):
        try:
            return self._api_update(self.api.account(
                self.pk, access_token=self.access_token, **kwargs))
        except WePayError, e:
            if e.code == 3003: # The account has been deleted
                self.state = 'deleted'
                self.save()
            raise

    def api_account_modify(self, **kwargs):
        callback_uri = self._api_uri_modifier(kwargs)
        image_uri = self._api_uri_modifier(kwargs, name='image_uri')
        response = self._api_update(self.api.account_modify(
            self.pk, access_token=self.access_token, **kwargs))
        if callback_uri or image_uri: # after the call is successfull, update model
            self.save()
        return response
        
    def api_account_delete(self, **kwargs):
        response = self._api_update(self.api.account_delete(
            self.pk, access_token=self.access_token, **kwargs))
        self.save() # save deleted status right away
        return response

    def api_account_balance(self, **kwargs):
        return self._api_update(self.api.account_balance(
            self.pk, access_token=self.access_token, **kwargs))
        
    def api_account_add_bank(self, **kwargs):
        self._api_uri_modifier(kwargs, name='redirect_uri')
        return self._api_update(self.api.account_add_bank(
            self.pk, access_token=self.access_token, **kwargs))

    def api_account_set_tax(self, *args, **kwargs):
        return self.api.account_set_tax(
            self.pk, *args, access_token=self.access_token, **kwargs)

    def api_account_get_tax(self, **kwargs):
        return self.api.account_get_tax(
            self.pk, access_token=self.access_token, **kwargs)

    def _api_account_object_create(self, obj_name, *args, **kwargs):
        update = kwargs.pop('update', True)
        commit = kwargs.pop('commit', True)
        if not self._api_uri_modifier(kwargs):
            kwargs['callback_uri'] = self._api_callback_uri(
                obj_name, user_id=self.user_id)
        self._api_uri_modifier(kwargs, name='redirect_uri')
        method_create = getattr(self.api, "%s_create" % obj_name)
        response = method_create(
            self.pk, *args, access_token=self.access_token, **kwargs)
        obj, response = self._api_create(obj_name, response, update, False)
        obj.account = self
        if commit:
            obj.save()
        return obj, response


    def api_checkout_create(self, *args, **kwargs):
        preapproval = kwargs.pop('preapproval', None)
        if not preapproval is None and isinstance(type(preapproval), Preapproval):
            kwargs['preapproval_id'] = preapproval.pk
        return self._api_account_object_create('checkout', *args, **kwargs)

    def api_preapproval_create(self, *args,  **kwargs):
        return self._api_account_object_create('preapproval', *args, **kwargs)

    def api_withdrawal_create(self, *args,  **kwargs):
        return self._api_account_object_create('withdrawal', *args, **kwargs)

    def api_checkout_find(self, **kwargs):
        return self.api.checkout_find(
            self.pk, access_token=self.access_token, **kwargs)

    def api_preapproval_find(self, **kwargs):
        return self.api.preapproval_find(
            account_id=self.pk, access_token=self.access_token, **kwargs)

    def api_withdrawal_find(self, **kwargs):
        return self.api.withdrawal_find(
            self.pk, access_token=self.access_token, **kwargs)

class CheckoutApi(Api):

    @property
    def access_token(self):
        if not hasattr(self, '_access_token'):
            self._access_token = self.account.access_token
        return self._access_token

    @access_token.setter
    def access_token(self, value):
        self._access_token = value
        
    def __str__(self):
        return "%s - %s" % (self.pk, self.short_description)

    def get_callback_uri(self):
        return self._api_callback_uri('checkout', user_id = self.account.user_id)

    def api_checkout(self, **kwargs):
        return self._api_update(self.api.checkout(
            self.pk, access_token=self.access_token, **kwargs))

    def api_checkout_cancel(self, *args, **kwargs):
        return self._api_update(self.api.checkout_cancel(
            self.pk, *args, access_token=self.access_token, **kwargs))

    def api_checkout_refund(self, *args, **kwargs):
        return self._api_update(self.api.checkout_refund(
            self.pk, *args, access_token=self.access_token, **kwargs))

    def api_checkout_capture(self, **kwargs):
        return self._api_update(self.api.checkout_capture(
            self.pk, access_token=self.access_token, **kwargs))

    def api_checkout_modify(self, **kwargs):
        callback_uri = self._api_uri_modifier(kwargs)
        response = self._api_update(self.api.checkout_modify(
            self.pk, access_token=self.access_token, **kwargs))
        if callback_uri:
            self.save()
        return response


class PreapprovalApi(Api):
    @property
    def access_token(self):
        if not hasattr(self, '_access_token'):
            self._access_token = self.account.access_token
        return self._access_token

    @access_token.setter
    def access_token(self, value):
        self._access_token = value

    def __str__(self):
        return "%s - %s" % (self.pk, self.short_description)

    def get_callback_uri(self):
        return self._api_callback_uri('preapproval', user_id = self.account.user_id)

    def api_preapproval(self, **kwargs):
        return self._api_update(self.api.preapproval(
            self.pk, access_token=self.access_token, **kwargs))

    def api_preapproval_cancel(self, **kwargs):
        return self._api_update(self.api.preapproval_cancel(
            self.pk, access_token=self.access_token, **kwargs))

    def api_preapproval_modify(self, **kwargs):
        callback_uri = self._api_uri_modifier(kwargs)
        response = self._api_update(self.api.preapproval_modify(
            self.pk, access_token=self.access_token, **kwargs))
        if callback_uri:
            self.save()
        return response


class WithdrawalApi(Api):
    @property
    def withdrawal_uri(self):
        return self._api_property_getter(
            '_withdrawal_uri', updater=self.api_withdrawal)

    @withdrawal_uri.setter
    def withdrawal_uri(self, value):
        self._withdrawal_uri = value

    @property
    def access_token(self):
        if not hasattr(self, '_access_token'):
            self._access_token = self.account.access_token
        return self._access_token

    @access_token.setter
    def access_token(self, value):
        self._access_token = value

    def __str__(self):
        return "%s - %s" % (self.pk, self.amount)

    def get_callback_uri(self):
        return self._api_callback_uri('withdrawal', user_id = self.account.user_id)

    def api_withdrawal(self, **kwargs):
        return self._api_update(self.api.withdrawal(
            self.pk, access_token=self.access_token, **kwargs))

    def api_withdrawal_modify(self, **kwargs):
        callback_uri = self._api_uri_modifier(kwargs)
        response = self._api_update(self.api.withdrawal_modify(
            self.pk, access_token=self.access_token, **kwargs))
        if callback_uri:
            self.save()
        return response


class CreditCardApi(Api):
    def api_credit_card(self, **kwargs):
        return self._api_update(self.api.credit_card(self.pk, **kwargs))

    def api_credit_card_authorize(self, **kwargs):
        return self._api_update(self.api.credit_card_authorize(self.pk, **kwargs))

    def api_credit_card_delete(self, **kwargs):
        return self._api_update(self.api.credit_card_delete(self.pk, **kwargs))

