from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db.models.loading import get_model
from django.utils.functional import LazyObject, curry

from djwepay.signals import state_changed
from djwepay.utils import from_string_import
from wepay.exceptions import WePayError
from wepay.utils import cached_property


__all__ = ['AppApi', 'UserApi', 'AccountApi', 'CheckoutApi', 'PreapprovalApi',
           'WithdrawalApi', 'CreditCardApi', 'SubscriptionPlanApi',
           'SubscriptionApi', 'SubscriptionChargeApi', 'DEFAULT_SCOPE',
           'get_wepay_model', 'get_wepay_model_name', 'is_abstract']


# default is full access
DEFAULT_SCOPE = getattr(
    settings, 'WEPAY_DEFAULT_SCOPE', "manage_accounts,collect_payments,"
    "view_user,preapprove_payments,manage_subscriptions,send_money")


DEFAULT_MODELS = dict([
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
])


MODELS = dict(getattr(settings, 'WEPAY_MODELS', ()))


API_BACKEND = getattr(settings, 'WEPAY_API_BACKEND', 'djwepay.backends.default.WePay')


def get_wepay_model_name(obj_name):
    """Always returns a string path to the model, even if object was turned off."""
    name = MODELS.get(obj_name, None)
    if name is None:
        name = DEFAULT_MODELS.get(obj_name)
    return name


def get_wepay_model(obj_name):
    """Always returns a model, even if object was turned off."""
    model_name = get_wepay_model_name(obj_name)
    if model_name is None:
        return None
    return get_model(*model_name.split('.'))


def is_abstract(obj_name):
    """Returns ``True`` if object is turned off or if custom model was specified."""
    return (MODELS.get(obj_name, '') is None or 
            get_wepay_model_name(obj_name) != DEFAULT_MODELS.get(obj_name))



class WePayLazy(LazyObject):

    def _setup(self):
        backend = from_string_import(API_BACKEND)
        app = get_wepay_model('app').objects.get_current()
        self._wrapped = backend(production=getattr(settings, 'WEPAY_PRODUCTION', False), 
                                access_token=app.access_token)



class Api(object):

    api = WePayLazy()

    def instance_update(self, response, commit=True):
        has_state_changed = False
        previous_state = getattr(self, 'state', '')
        new_state = response.get('state', '')
        for key, value in response.iteritems():
            # required for app level preapprovals
            if value == 0 and key.endswith('_id'):
                value = None
            setattr(self, key, value)
        if new_state and new_state != previous_state:
            # using cache we eliminate duplicate calls to state_changed,
            # which has a chance of happening in multithreaded environment
            cache_key = "wepay-state-changed-%s-%s" % (type(self).__name__, self.pk)
            added = cache.add(cache_key, new_state)
            has_state_changed = True
            if not added:
                stored_state = cache.get(cache_key)
                if stored_state == new_state:
                    has_state_changed = False
                cache.set(cache_key, new_state)
        if commit:
            self.save()
        if has_state_changed:
            state_changed.send(sender=self.__class__, instance=self,
                               previous_state=previous_state)
        return self


    def instance_identity(self, response):
        return self


    def get_callback_uri(self, **kwargs):
        return reverse('wepay:ipn', kwargs=kwargs)



class AppApi(Api):
    """App model mixin object that helps making related Api calls"""

    @cached_property
    def access_token(self):
        if self.user:
            return self.user.access_token
        return None


    def api_app(self, commit=True, **kwargs):
        app, response = self.api.app(
            client_id=self.client_id,
            client_secret=self.client_secret,
            callback=curry(self.instance_update, commit=commit), **kwargs)
        if commit: # clear cached in case current app has changed
            App = get_wepay_model('app')
            App.objects.clear_cache()
        return app, response


    def api_app_modify(self, commit=True, **kwargs):
        app, response = self.api.app.modify(
            client_id=self.client_id,
            client_secret=self.client_secret,
            callback=curry(self.instance_update, commit=commit), **kwargs)
        if commit: # clear cached in case current app has changed
            App = get_wepay_model('app')
            App.objects.clear_cache()
        return app, response


    def api_oauth2_authorize(self, redirect_uri, **kwargs):
        return self.api.oauth2.authorize(
            self.client_id, redirect_uri, kwargs.pop('scope', DEFAULT_SCOPE),
            **kwargs)


    def api_oauth2_token(self, commit=True, **kwargs):
        User = get_wepay_model('user')
        return self.api.oauth2.token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            callback_uri=self.get_callback_uri(obj_name='user'),
            callback=curry(User.objects.create_from_response, self, commit=commit),
            **kwargs)


    def api_user_register(self, commit=True, **kwargs):
        User = get_wepay_model('user')
        return self.api.user.register(
            client_id=self.client_id,
            client_secret=self.client_secret,
            scope=kwargs.pop('scope', DEFAULT_SCOPE),
            callback_uri=self.get_callback_uri(obj_name='user'),
            callback=curry(User.objects.create_from_response, self, commit=commit),
            **kwargs)


    def api_preapproval_create(self, commit=True, **kwargs):
        Preapproval = get_wepay_model('preapproval')
        return self.api.preapproval.create(
            client_id=self.client_id,
            client_secret=self.client_secret,
            callback_uri = self.get_callback_uri(obj_name='preapproval'),
            callback=curry(Preapproval.objects.create_from_response, self, commit=commit),
            **kwargs)


    def api_preapproval_find(self, **kwargs):
        return self.api.preapproval.find(**kwargs)


    def api_credit_card_create(self, commit=True, **kwargs):
        CreditCard = get_wepay_model('credit_card')
        return self.api.credit_card.create(
            client_id=self.client_id,
            callback=curry(CreditCard.objects.create_from_response, commit=commit),
            **kwargs)


    def api_credit_card_find(self, **kwargs):
        return self.api.credit_card.find(
            client_id=self.client_id,
            client_secret=self.client_secret, **kwargs)


    def api_subscription_plan_find(self, **kwargs):
        return self.api.subscription_plan.find(**kwargs)


    def api_batch_create(self, batch_id, **kwargs):
        return self.api.batch.create(
            batch_id, self.client_id, self.client_secret, **kwargs)



class UserApi(Api):

    @cached_property
    def callback_uri(self):
        return self.api_user()[1].get('callback_uri', None)


    def api_user(self, commit=True, **kwargs):
        return self.api.user(
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_user_modify(self, commit=True, **kwargs):
        return self.api.user.modify(
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_user_resend_confirmation(self, commit=True, **kwargs):
        return self.api.user.resend_confirmation(
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_account_create(self, commit=True, **kwargs):
        Account = get_wepay_model('account')
        return self.api.account.create(
            access_token=self.access_token,
            callback_uri=self.get_callback_uri(
                obj_name='account', user_id=self.pk),
            callback=curry(Account.objects.create_from_response, self, commit=commit),
            **kwargs)


    def api_account_find(self, **kwargs):
        return self.api.account.find(
            access_token=self.access_token, **kwargs)



class AccountApi(Api):

    @cached_property
    def access_token(self):
        if self.user:
            return self.user.access_token
        return None

    @cached_property
    def uri(self):
        return self.api_account_get_update_uri()[1].get('uri', None)


    @cached_property
    def callback_uri(self):
        return self.api_account()[1].get('callback_uri', None)


    def api_account(self, commit=True, **kwargs):
        try:
            return self.api.account(
                account_id=self.pk,
                access_token=self.access_token,
                callback=curry(self.instance_update, commit=commit), **kwargs)
        except WePayError as e:
            if e.code == 3003: # The account has been deleted
                self.state = 'deleted'
                self.save()
            raise


    def api_account_modify(self, commit=True, **kwargs):
        return self.api.account.modify(
            account_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_account_delete(self, commit=True, **kwargs):
        return self.api.account.delete(
            account_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_account_get_update_uri(self, commit=False, **kwargs):
        return self.api.account.get_update_uri(
            account_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_account_get_reserve_details(self, commit=True, **kwargs):
        return self.api.account.get_reserve_details(
            account_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_checkout_create(self, commit=True, **kwargs):
        Checkout = get_wepay_model('checkout')
        return self.api.checkout.create(
            account_id=self.pk,
            access_token=self.access_token,
            callback_uri=self.get_callback_uri(
                obj_name='checkout', user_id=self.user.pk),
            callback=curry(Checkout.objects.create_from_response, self, commit=commit),
            **kwargs)


    def api_preapproval_create(self, commit=True, **kwargs):
        Preapproval = get_wepay_model('preapproval')
        return self.api.preapproval.create(
            account_id=self.pk,
            access_token=self.access_token,
            callback_uri=self.get_callback_uri(
                obj_name='preapproval', user_id=self.user.pk),
            callback=curry(Preapproval.objects.create_from_response, self, commit=commit),
            **kwargs)


    def api_withdrawal_create(self, commit=True, **kwargs):
        Withdrawal = get_wepay_model('withdrawal')
        return self.api.withdrawal.create(
            account_id=self.pk,
            access_token=self.access_token,
            callback_uri=self.get_callback_uri(
                obj_name='withdrawal', user_id=self.user.pk),
            callback=curry(Withdrawal.objects.create_from_response, self, commit=commit),
            **kwargs)


    def api_subscription_plan_create(self, commit=True, **kwargs):
        SubscriptionPlan = get_wepay_model('subscription_plan')
        return self.api.subscription_plan.create(
            account_id=self.pk,
            access_token=self.access_token,
            callback_uri=self.get_callback_uri(
                obj_name='subscription_plan', user_id=self.user.pk),
            callback=curry(SubscriptionPlan.objects.create_from_response, self, commit=commit),
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


    def api_checkout(self, commit=True, **kwargs):
        return self.api.checkout(
            checkout_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_checkout_cancel(self, commit=True, **kwargs):
        return self.api.checkout.cancel(
            checkout_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_checkout_refund(self, commit=True, **kwargs):
        return self.api.checkout.refund(
            checkout_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_checkout_capture(self, commit=True, **kwargs):
        return self.api.checkout.capture(
            checkout_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_checkout_modify(self, commit=True, **kwargs):
        return self.api.checkout.modify(
            checkout_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)



class PreapprovalApi(Api):

    @cached_property
    def access_token(self):
        if self.account is not None:
            return self.account.access_token
        elif self.app is not None:
            return self.app.access_token

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


    def api_preapproval(self, commit=True, **kwargs):
        return self.api.preapproval(
            preapproval_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_preapproval_cancel(self, commit=True, **kwargs):
        return self.api.preapproval.cancel(
            preapproval_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_preapproval_modify(self, commit=True, **kwargs):
        return self.api.preapproval.modify(
            preapproval_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_checkout_create(self, account=None, commit=True, **kwargs):
        """Create a checkout using this preapproval. In case that preapproval
        was authorized to send money to any account, account instance should be
        supplied as a keyword argument.

        """
        assert bool(account) != bool(self.account), \
            "You should supply account instance if preapproval was created on the App level"
        Checkout = get_wepay_model('checkout')
        account = account or self.account
        return self.api.checkout.create(
            account_id=account.pk,
            access_token=account.access_token,
            preapproval_id=self.pk,
            callback_uri=self.get_callback_uri(
                obj_name='checkout', user_id=account.user.pk),
            callback=curry(Checkout.objects.create_from_response, account, commit=commit),
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


    def api_withdrawal(self, commit=True, **kwargs):
        return self.api.withdrawal(
            withdrawal_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_withdrawal_modify(self, commit=True, **kwargs):
        return self.api.withdrawal.modify(
            withdrawal_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)



class CreditCardApi(Api):

    def api_credit_card(self, commit=True, **kwargs):
        return self.api.credit_card(
            client_id=self.app.client_id,
            client_secret=self.app.client_secret,
            credit_card_id=self.pk,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_credit_card_authorize(self, commit=True, **kwargs):
        return self.api.credit_card.authorize(
            client_id=self.app.client_id,
            client_secret=self.app.client_secret,
            credit_card_id=self.pk,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_credit_card_delete(self, commit=True, **kwargs):
        return self.api.credit_card.delete(
            client_id=self.app.client_id,
            client_secret=self.app.client_secret,
            credit_card_id=self.pk,
            callback=curry(self.instance_update, commit=commit), **kwargs)



class SubscriptionPlanApi(Api):

    @cached_property
    def access_token(self):
        return self.account.access_token

    @cached_property
    def callback_uri(self):
        return self.api_subscription_plan()[1].get('callback_uri', None)


    def api_subscription_plan(self, commit=True, **kwargs):
        return self.api.subscription_plan(
            subscription_plan_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_subscription_plan_delete(self, commit=True, **kwargs):
        return self.api.subscription_plan.delete(
            subscription_plan_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_subscription_plan_get_button(self, **kwargs):
        return self.api.subscription_plan.get_button(
            account_id=self.account.pk,
            button_type='subscription_plan',
            subscription_plan_id=self.pk,
            access_token=self.access_token,
            callback=self.instance_identity, **kwargs)


    def api_subscription_plan_modify(self, commit=True, **kwargs):
        return self.api.subscription_plan.modify(
            subscription_plan_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_subscription_create(self, commit=True, **kwargs):
        Subscription = get_wepay_model('subscription')
        return self.api.subscription.create(
            subscription_plan_id=self.pk,
            callback_uri=self.get_callback_uri(
                obj_name='subscription', user_id=self.account.user.pk),
            callback=curry(Subscription.objects.create_from_response, self, commit=commit),
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


    def api_subscription(self, commit=True, **kwargs):
        return self.api.subscription(
            subscription_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_subscription_cancel(self, commit=True, **kwargs):
        return self.api.subscription.cancel(
            subscription_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_subscription_modify(self, commit=True, **kwargs):
        return self.api.subscription.modify(
            subscription_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_subscription_charge_find(self, **kwargs):
        return self.api.subscription_charge.find(
            subscription_id=self.pk,
            access_token=self.access_token, **kwargs)



class SubscriptionChargeApi(Api):

    @cached_property
    def access_token(self):
        return self.subscription_plan.access_token


    def api_subscription_charge(self, commit=True, **kwargs):
        return self.api.subscription_charge(
            subscription_charge_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)


    def api_subscription_charge_refund(self, commit=True, **kwargs):
        return self.api.subscription_charge.refund(
            subscription_charge_id=self.pk,
            access_token=self.access_token,
            callback=curry(self.instance_update, commit=commit), **kwargs)
