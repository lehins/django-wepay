from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db.models.loading import get_model
from django.utils.functional import LazyObject, curry

from djwepay.decorators import cached_property
from djwepay.signals import state_changed
from djwepay.utils import from_string_import
from wepay.exceptions import WePayError

__all__ = ['AppApi', 'UserApi', 'AccountApi', 'CheckoutApi', 'PreapprovalApi',
           'WithdrawalApi', 'CreditCardApi', 'SubscriptionPlanApi',
           'SubscriptionApi', 'SubscriptionChargeApi', 'DEFAULT_SCOPE',
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
    ('credit_card', 'djwepay.CreditCard'),
    ('subscription_plan', 'djwepay.SubscriptionPlan'),
    ('subscription', 'djwepay.Subscription'),
    ('subscription_charge', 'djwepay.SubscriptionCharge')
)

MODELS = getattr(settings, 'WEPAY_MODELS', ())

API_BACKEND = getattr(settings, 'WEPAY_API_BACKEND', 'djwepay.backends.default.WePay')

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
        app = get_wepay_model('app').objects.get_current()
        self._wrapped = backend(
            production=app.production, access_token=app.access_token, timeout=45)

class AppLazy(LazyObject):
    def _setup(self):
        self._wrapped = get_wepay_model('app').objects.get_current()


class Api(object):

    api = WePayLazy()
    app = AppLazy()

    def instance_update(self, response, commit=True):
        previous_state = getattr(self, 'state', '') # app object doesn't have state?
        new_state = response.get('state', '')
        for key, value in response.iteritems():
            setattr(self, key, value)
        if new_state and new_state != previous_state:
            # using cache we eliminate duplicate calls to state_changed,
            # which has a chance of happening in multithreaded environment
            cache_key = "wepay-state-changed-%s-%s" % (type(self).__name__, self.pk)
            added = cache.add(cache_key, new_state)
            if not added:
                stored_state = cache.get(cache_key)
                if stored_state == new_state:
                    return response
            cache.set(cache_key, new_state)                
            state_changed.send(sender=type(self), instance=self, 
                               previous_state=previous_state)
        if commit:
            self.save()
        return self

    def instance_update_nocommit(self, response):
        return self.instance_update(response, commit=False)

    def instance_identity(self, response):
        return self

    def get_callback_uri(self, **kwargs):
        return reverse('wepay:ipn', kwargs=kwargs)
    
    def api_batch_create(self, **kwargs):
        return self.api.batch.create(client_id=self.app.client_id,
                                     client_secret=self.app.client_secret, **kwargs)

class AppApi(Api):
    """ App model mixin object that helps making related Api calls"""

    def api_app(self, **kwargs):
        return self.api.app(
            client_id=self.client_id,
            client_secret=self.client_secret, 
            callback=self.instance_update, **kwargs)

    def api_app_modify(self, **kwargs):
        return self.api.app.modify(
            client_id=self.client_id,
            client_secret=self.client_secret, 
            callback=self.instance_update, **kwargs)

    def api_oauth2_authorize(self, redirect_uri, **kwargs):
        return self.api.oauth2.authorize(
            self.client_id, redirect_uri, DEFAULT_SCOPE, **kwargs)

    def api_oauth2_token(self, **kwargs):
        User = get_wepay_model('user')
        return self.api.oauth2.token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            callback_uri=self.get_callback_uri(obj_name='user'),
            callback=User.objects.create_from_response, **kwargs)

    def api_user_register(self, **kwargs):
        User = get_wepay_model('user')
        return self.api.user.register(
            client_id=self.client_id,
            client_secret=self.client_secret,
            scope=DEFAULT_SCOPE,
            callback_uri=self.get_callback_uri(obj_name='user'),
            callback=User.objects.create_from_response, **kwargs)


    def api_preapproval_create(self, **kwargs):
        Preapproval = get_wepay_model('preapproval')
        return self.api.preapproval.create(
            client_id=self.client_id, 
            client_secret=self.client_secret,
            callback_uri = self.get_callback_uri(obj_name='preapproval'),
            callback=curry(Preapproval.objects.create_from_response, None), 
            **kwargs)

    def api_preapproval_find(self, **kwargs):
        return self.api.preapproval.find(**kwargs)

    def api_credit_card_create(self, **kwargs):
        CreditCard = get_wepay_model('credit_card')
        return self.api.credit_card.create(
            client_id=self.client_id, 
            callback=CreditCard.objects.create_from_response, **kwargs)

    def api_credit_card_find(self, **kwargs):
        return self.api.credit_card.find(
            client_id=self.client_id,
            client_secret=self.client_secret, **kwargs)

    def api_subscription_plan_find(self, **kwargs):
        return self.api.subscription_plan.find(
            account_id=self.pk,
            access_token=self.access_token, **kwargs)


class UserApi(Api):

    def api_user(self, **kwargs):
        return self.api.user(
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)

    def api_user_modify(self, **kwargs):
        return self.api.user.modify(
            access_token=self.access_token,
            callback=self.instance_update, **kwargs)

    def api_user_resend_confirmation(self, **kwargs):
        return self.api.user.resend_confirmation(
            access_token=self.access_token,
            callback=self.instance_update, **kwargs)

    def api_account_create(self, **kwargs):
        Account = get_wepay_model('account')
        return self.api.account.create(
            access_token=self.access_token,
            callback_uri=self.get_callback_uri(
                obj_name='account', user_id=self.user_id),
            callback=curry(Account.objects.create_from_response, self), **kwargs)

    def api_account_find(self, **kwargs):
        return self.api.account.find(
            access_token=self.access_token, **kwargs)

class AccountApi(Api):

    @cached_property
    def access_token(self):
        return self.user.access_token

    @cached_property
    def uri(self):
        return self.api_account_get_update_uri()[1].get('uri', None)

    def api_account(self, **kwargs):
        try:
            return self.api.account(
                account_id=self.pk, 
                access_token=self.access_token, 
                callback=self.instance_update, **kwargs)
        except WePayError, e:
            if e.code == 3003: # The account has been deleted
                self.state = 'deleted'
                self.save()
            raise

    def api_account_modify(self, **kwargs):
        return self.api.account.modify(
            account_id=self.pk, 
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)
        
    def api_account_delete(self, **kwargs):
        return self.api.account.delete(
            account_id=self.pk, 
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)

    def api_account_get_update_uri(self, **kwargs):
        return self.api.account.get_update_uri(
            account_id=self.pk, 
            access_token=self.access_token, 
            callback=self.instance_update_nocommit, **kwargs)
        
    def api_account_get_reserve_details(self, **kwargs):
        return self.api.account.getreserve_details(
            account_id=self.pk, 
            access_token=self.access_token, 
            callback=self.instance_identity, **kwargs)

    def api_checkout_create(self, **kwargs):
        Checkout = get_wepay_model('checkout')
        return self.api.checkout.create(
            account_id=self.pk,
            access_token=self.access_token,
            callback_uri=self.get_callback_uri(
                obj_name='checkout', user_id=self.user.pk), 
            callback=curry(Checkout.objects.create_from_response, self), 
            **kwargs)

    def api_preapproval_create(self, **kwargs):
        Preapproval = get_wepay_model('preapproval')
        return self.api.preapproval.create(
            account_id=self.pk,
            access_token=self.access_token,
            callback_uri=self.get_callback_uri(
                obj_name='preapproval', user_id=self.user.pk), 
            callback=curry(Preapproval.objects.create_from_response, self), 
            **kwargs)

    def api_withdrawal_create(self, **kwargs):
        Withdrawal = get_wepay_model('withdrawal')
        return self.api.withdrawal.create(
            account_id=self.pk,
            access_token=self.access_token,
            callback_uri=self.get_callback_uri(
                obj_name='withdrawal', user_id=self.user.pk), 
            callback=curry(Withdrawal.objects.create_from_response, self), 
            **kwargs)

    def api_subscription_plan_create(self, **kwargs):
        SubscriptionPlan = get_wepay_model('subscription_plan')
        return self.api.subscription_plan.create(
            account_id=self.pk,
            access_token=self.access_token,
            callback_uri=self.get_callback_uri(
                obj_name='subscription_plan', user_id=self.user.pk), 
            callback=curry(SubscriptionPlan.objects.create_from_response, self), 
            **kwargs)

    def api_checkout_find(self, **kwargs):
        return self.api.checkout.find(
            account_id=self.pk, 
            access_token=self.access_token, **kwargs)

    def api_preapproval_find(self, **kwargs):
        return self.api.preapproval.find(
            account_id=self.account_id, 
            access_token=self.access_token, **kwargs)

    def api_withdrawal_find(self, **kwargs):
        return self.api.withdrawal.find(
            account_id=self.pk, 
            access_token=self.access_token, **kwargs)

    def api_subscription_plan_find(self, **kwargs):
        return self.api.subscription_plan.find(
            account_id=self.pk,
            access_token=self.access_token, **kwargs)

    def api_subscription_plan_get_button(self, **kwargs):
        return self.api.subscription_plan.get_button(
            account_id=self.pk,
            access_token=self.access_token, 
            callback=self.instance_identity, **kwargs)


class CheckoutApi(Api):

    @cached_property
    def access_token(self):
        return self.account.access_token

    @cached_property
    def redirect_uri(self):
        return self.api_checkout()[1].get('redirect_uri', None)

    @cached_property
    def callback_uri(self):
        return self.api_checkout()[1].get('callback_uri', None)

    @cached_property
    def dispute_uri(self):
        return self.api_checkout()[1].get('dispute_uri', None)
        
    def api_checkout(self, **kwargs):
        return self.api.checkout(
            checkout_id=self.pk, 
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)

    def api_checkout_cancel(self, **kwargs):
        return self.api.checkout.cancel(
            checkout_id=self.pk, 
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)

    def api_checkout_refund(self, **kwargs):
        return self.api.checkout.refund(
            checkout_id=self.pk, 
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)

    def api_checkout_capture(self, **kwargs):
        return self.api.checkout.capture(
            checkout_id=self.pk, 
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)

    def api_checkout_modify(self, **kwargs):
        return self.api.checkout.modify(
            checkout_id=self.pk, 
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)


class PreapprovalApi(Api):

    @cached_property
    def access_token(self):
        return self.account.access_token

    @cached_property
    def preapproval_uri(self):
        return self.api_preapproval()[1].get('preapproval_uri', None)

    @cached_property
    def manage_uri(self):
        return self.api_preapproval()[1].get('manage_uri', None)

    @cached_property
    def redirect_uri(self):
        return self.api_preapproval()[1].get('redirect_uri', None)

    @cached_property
    def callback_uri(self):
        return self.api_preapproval()[1].get('callback_uri', None)


    def api_preapproval(self, **kwargs):
        return self.api.preapproval(
            preapproval_id=self.pk, 
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)

    def api_preapproval_cancel(self, **kwargs):
        return self.api.preapproval.cancel(
            preapproval_id=self.pk, 
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)

    def api_preapproval_modify(self, **kwargs):
        return self.api.preapproval.modify(
            preapproval_id=self.pk, 
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)

    def api_checkout_create(self, **kwargs):
        Checkout = get_wepay_model('checkout')
        return self.api.checkout.create(
            account_id=self.account.pk,
            access_token=self.access_token,
            callback_uri=self.get_callback_uri(
                obj_name='checkout', user_id=self.user.pk), 
            callback=curry(Checkout.objects.create_from_response, self.account), 
            **kwargs)


class WithdrawalApi(Api):

    @cached_property
    def access_token(self):
        return self.account.access_token

    @cached_property
    def withdrawal_uri(self):
        return self.api_withdrawal()[1].get('withdrawal_uri', None)

    @cached_property
    def redirect_uri(self):
        return self.api_withdrawal()[1].get('redirect_uri', None)

    @cached_property
    def callback_uri(self):
        return self.api_withdrawal()[1].get('callback_uri', None)


    def api_withdrawal(self, **kwargs):
        return self.api.withdrawal(
            withdrawal_id=self.pk, 
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)

    def api_withdrawal_modify(self, **kwargs):
        return self.api.withdrawal.modify(
            withdrawal_id=self.pk, 
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)
        

class CreditCardApi(Api):
    def api_credit_card(self, **kwargs):
        return self.api.credit_card(
            client_id=self.app.client_id,
            client_secret=self.app.client_secret,
            credit_card_id=self.pk, 
            callback=self.instance_update, **kwargs)

    def api_credit_card_authorize(self, **kwargs):
        return self.api.credit_card.authorize(
            client_id=self.app.client_id,
            client_secret=self.app.client_secret,
            credit_card_id=self.pk, 
            callback=self.instance_update, **kwargs)

    def api_credit_card_delete(self, **kwargs):
        return self.api.credit_card.delete(
            client_id=self.app.client_id,
            client_secret=self.app.client_secret,
            credit_card_id=self.pk, 
            callback=self.instance_update, **kwargs)


class SubscriptionPlanApi(Api):

    @cached_property
    def access_token(self):
        return self.account.access_token
    
    @cached_property
    def callback_uri(self):
        return self.api_subscription_plan()[1].get('callback_uri', None)

    def api_subscription_plan(self, **kwargs):
        return self.api.subscription_plan(
            subscription_plan_id=self.pk,
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)

    def api_subscription_plan_delete(self, **kwargs):
        return self.api.subscription_plan.delete(
            subscription_plan_id=self.pk,
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)
            
    def api_subscription_plan_get_button(self, **kwargs):
        return self.api.subscription_plan.get_button(
            account_id=self.account.pk,
            button_type='subscription_plan',
            subscription_plan_id=self.pk,
            access_token=self.access_token, 
            callback=self.instance_identity, **kwargs)

    def api_subscription_plan_modify(self, **kwargs):
        return self.api.subscription_plan.modify(
            subscription_plan_id=self.pk,
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)

    def api_subscription_create(self, **kwargs):
        Subscription = get_wepay_model('subscription')
        return self.api.subscription.create(
            subscription_plan_id=self.pk,
            callback_uri=self.get_callback_uri(
                obj_name='subscription', user_id=self.account.user.pk),
            callback=curry(Subscription.objects.create_from_response, self),
            access_token=self.access_token, **kwargs)

    def api_subscription_find(self, **kwargs):
        return self.api.subscription.find(
            subscription_plan_id=self.pk,
            access_token=self.access_token, **kwargs)


class SubscriptionApi(Api):

    @cached_property
    def access_token(self):
        return self.subscription_plan.access_token
    
    @cached_property
    def subscription_uri(self):
        return self.api_subscription()[1].get('subscription_uri', None)

    @cached_property
    def callback_uri(self):
        return self.api_subscription()[1].get('callback_uri', None)

    @cached_property
    def redirect_uri(self):
        return self.api_subscription()[1].get('redirect_uri', None)

    def api_subscription(self, **kwargs):
        return self.api.subscription(
            subscription_id=self.pk,
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)

    def api_subscription_cancel(self, **kwargs):
        return self.api.subscription.cancel(
            subscription_id=self.pk,
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)

    def api_subscription_modify(self, **kwargs):
        return self.api.subscription.modify(
            subscription_id=self.pk,
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)

    def api_subscription_charge_find(self, **kwargs):
        return self.api.subscription_charge.find(
            subscription_id=self.pk,
            access_token=self.access_token, **kwargs)



class SubscriptionChargeApi(Api):

    @cached_property
    def access_token(self):
        return self.subscription_plan.access_token
    
    def api_subscription_charge(self, **kwargs):
        return self.api.subscription_charge(
            subscription_charge_id=self.pk,
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)

    def api_subscription_charge_refund(self, **kwargs):
        return self.api.subscription_charge.refund(
            subscription_charge_id=self.pk,
            access_token=self.access_token, 
            callback=self.instance_update, **kwargs)

    