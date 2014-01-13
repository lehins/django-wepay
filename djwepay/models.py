"""All models are direct mappings to the WePay objects. By default only the
fields that correspond to the values returned from WePay lookup calls
(ex. `/account <https://www.wepay.com/developer/reference/account#lookup>`_) are
include in the models. All fields follow the rules outlined in `Storing Data
<https://www.wepay.com/developer/reference/storing_data>`_, unless otherwise
specified in object's documentation. For that reason values, which have there
names end with '_uri' (ex. ``account_uri``) are not included as model fields,
instead they are added as dynamic cached object properties, which are inherited
from Api objects defined in :mod:`djwepay.api`.

"""

import datetime, pytz
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models

from djwepay.api import *
from djwepay.fields import MoneyField

from json_field import JSONField

__all__ = ['App', 'User', 'Account', 'Checkout', 'Preapproval', 'Withdrawal', 
           'CreditCard']

APP_CACHE = {}

class BaseModel(models.Model):
    date_created  = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.date_created:
            self.date_created = datetime.datetime.now(pytz.timezone(settings.TIME_ZONE))
            #datetime.datetime.today()
        self.date_modified = datetime.datetime.now(pytz.timezone(settings.TIME_ZONE))
        return super(BaseModel, self).save(*args, **kwargs)

    class Meta:
        abstract = True
        ordering = ['-date_created']

class AppManager(models.Manager):

    def get_current(self):
        """Returns the current :class:`App` based on the :ref:`WEPAY_APP_ID` in the
        project's settings. The :class:`App` object is cached the first time
        it's retrieved from the database.

        """
        try:
            app_id = settings.WEPAY_APP_ID
        except AttributeError:
            raise ImproperlyConfigured(
                "You're using the Django WePay application without having set the "
                "WEPAY_APP_ID setting. Create an app in your database and set the "
                "WEPAY_APP_ID setting to fix this error.")
        try:
            current_app = APP_CACHE[app_id]
        except KeyError:
            current_app = self.get(pk=app_id)
            APP_CACHE[app_id] = current_app
        return current_app

    def clear_cache(self):
        """Clears the ``App`` object cache."""
        global APP_CACHE
        APP_CACHE = {}

class App(AppApi, BaseModel):
    """
    This model stores all of the relevant WePay application information. Only one
    instance of it at a time is supported per django application, which is 
    controlled by :ref:`WEPAY_APP_ID` setting.
    """
    client_id = models.BigIntegerField(primary_key=True)
    status = models.CharField(max_length=255)
    theme_object = JSONField(null=True, blank=True)
    gaq_domains = JSONField(null=True, blank=True)

    client_secret = models.CharField(max_length=255)
    access_token = models.CharField(max_length=255)
    production = models.BooleanField(default=True)
    state = models.CharField(max_length=255)

    objects = AppManager()

    class Meta(BaseModel.Meta):
        abstract = is_abstract('app')
        db_table = 'djwepay_app'
        verbose_name = 'WePay App'

class UserManager(models.Manager):

    def create_from_response(self, response):
        try:
            user = self.get(pk=response['user_id'])
        except self.model.DoesNotExist:
            user = self.model()
        return user.instance_update(response)
    
    def accessible(self):
        return self.exclude(access_token=None)

class User(UserApi, BaseModel):
    user_id = models.BigIntegerField(primary_key=True)
    user_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    state = models.CharField(max_length=255)

    # access_token=NULL means it has been revoked.
    access_token = models.CharField(null=True, max_length=255)
    token_type = "BEARER"
    expires_in = models.BigIntegerField(null=True, blank=True)

    objects = UserManager()

    def __str__(self):
        return self.user_name

    class Meta(BaseModel.Meta):
        abstract = is_abstract('user')
        db_table = 'djwepay_user'
        verbose_name = 'WePay User'

class AccountManager(models.Manager):
    
    def create_from_response(self, user, response):
        account = self.model(user=user)
        return account.instance_update(response)

    def accessible(self):
        return self.exclude(user__access_token=None)

    def active(self):
        return self.accessible().filter(state='active')


class Account(AccountApi, BaseModel):
    account_id = models.BigIntegerField(primary_key=True)
    user = models.ForeignKey(get_wepay_model_name('user'), related_name='accounts')
    name = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    reference_id = models.CharField(max_length=255)
    gaq_domains = JSONField(null=True, blank=True)
    theme_object = JSONField(null=True, blank=True)
    type = models.CharField(max_length=255)
    create_time = models.BigIntegerField(null=True)
    balances = JSONField(null=True, blank=True)
    statuses = JSONField(null=True, blank=True)
    action_reasons = JSONField(null=True, blank=True)
    country = models.CharField(max_length=2)
    currencies = JSONField(null=True, blank=True)

    objects = AccountManager()
    
    def __str__(self):
        return "%s - %s" % (self.pk, self.name)

    class Meta(BaseModel.Meta):
        abstract = is_abstract('account')
        db_table = 'djwepay_account'
        verbose_name = 'WePay Account'

class AccountObjectsManager(models.Manager):
    
    def create_from_response(self, account, response):
        obj = self.model(account=account)
        return obj.instance_update(response)

    def accessible(self):
        return self.exclude(account__user__access_token=None)


class Checkout(CheckoutApi, BaseModel):
    checkout_id = models.BigIntegerField(primary_key=True)
    account = models.ForeignKey(
        get_wepay_model_name('account'), related_name='checkouts')
    preapproval = models.ForeignKey(
        get_wepay_model_name('preapproval'), related_name='checkouts', null=True)
    state = models.CharField(max_length=255)
    soft_descriptor = models.CharField(max_length=255)
    short_description = models.CharField(max_length=255)
    long_description = models.CharField(max_length=2047, blank=True)
    currency = "USD"
    amount = MoneyField(null=True)
    fee = MoneyField(null=True)
    gross = MoneyField(null=True)
    app_fee = MoneyField(null=True)
    fee_payer = models.CharField(max_length=255)
    reference_id = models.CharField(max_length=255, blank=True)
    payer_email = models.EmailField(max_length=255, blank=True)
    payer_name = models.CharField(max_length=255, blank=True)
    cancel_reason = models.CharField(max_length=255, blank=True)
    refund_reason = models.CharField(max_length=255, blank=True)
    auto_capture = models.BooleanField(default=True)
    require_shipping = models.BooleanField(default=False)
    shipping_address = JSONField(null=True)
    tax = MoneyField(null=True)
    amount_refunded = MoneyField(null=True)
    amount_charged_back = MoneyField(null=True)
    create_time = models.BigIntegerField(null=True)
    mode = models.CharField(max_length=255)

    objects = AccountObjectsManager()

    def __str__(self):
        return "%s - %s" % (self.pk, self.short_description)

    class Meta(BaseModel.Meta):
        abstract = is_abstract('checkout')
        db_table = 'djwepay_checkout'
        verbose_name = 'WePay Checkout'


class Preapproval(PreapprovalApi, BaseModel):
    preapproval_id = models.BigIntegerField(primary_key=True)
    account = models.ForeignKey(
        get_wepay_model_name('account'), related_name='preapprovals')
    short_description = models.CharField(max_length=255)
    long_description = models.CharField(max_length=2047, blank=True)
    currency = "USD"
    amount = MoneyField(null=True)
    fee_payer = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    app_fee = MoneyField(null=True)
    period = models.CharField(max_length=255)
    frequency = models.IntegerField(null=True)
    start_time = models.BigIntegerField(null=True)
    end_time = models.BigIntegerField(null=True)
    reference_id = models.CharField(max_length=255)
    shipping_address = JSONField(null=True)
    shipping_fee = MoneyField(null=True)
    tax = MoneyField(null=True)
    auto_recur = models.BooleanField(default=False)
    payer_name = models.CharField(max_length=255)
    payer_email = models.EmailField(max_length=255, blank=True)
    create_time = models.BigIntegerField(null=True)
    next_due_time = models.BigIntegerField(null=True)
    last_checkout = models.ForeignKey(
        get_wepay_model_name('checkout'), null=True, related_name='+')
    last_checkout_time = models.BigIntegerField(null=True)
    mode = models.CharField(max_length=255)

    objects = AccountObjectsManager()

    def __str__(self):
        return "%s - %s" % (self.pk, self.short_description)

    class Meta(BaseModel.Meta):
        abstract = is_abstract('preapproval')
        db_table = 'djwepay_preapproval'
        verbose_name = 'WePay Preapproval'


class Withdrawal(WithdrawalApi, BaseModel):
    withdrawal_id = models.BigIntegerField(primary_key=True)
    account = models.ForeignKey(
        get_wepay_model_name('account'), related_name='withdrawals')
    state = models.CharField(max_length=255)
    amount = MoneyField(null=True)
    note = models.CharField(max_length=255)
    recipient_confirmed = models.NullBooleanField()
    type = models.CharField(max_length=255)
    create_time = models.BigIntegerField(null=True)

    objects = AccountObjectsManager()

    def __str__(self):
        return "%s - %s" % (self.pk, self.amount)

    class Meta(BaseModel.Meta):
        abstract = is_abstract('withdrawal')
        db_table = 'djwepay_withdrawal'
        verbose_name = 'WePay Preapproval'


class CreditCard(CreditCardApi, BaseModel):
    credit_card_id = models.BigIntegerField(primary_key=True)
    credit_card_name = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    user_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, blank=True)
    reference_id = models.CharField(max_length=255, blank=True)
    create_time = models.BigIntegerField(null=True)

    def __str__(self):
        return self.credit_card_name

    class Meta(BaseModel.Meta):
        abstract = is_abstract('credit_card')
        db_table = 'djwepay_credit_card'
        verbose_name = 'WePay Credit Card'


class SubscriptionPlan(SubscriptionPlanApi, BaseModel):
    subscription_plan_id = models.BigIntegerField(primary_key=True)
    account = models.ForeignKey(
        get_wepay_model_name('account'), related_name='subscription_plans')
    name = models.CharField(max_length=255)
    short_description = models.CharField(max_length=2047)
    currency = models.CharField(max_length=3)
    amount = MoneyField(null=True)
    period = models.CharField(max_length=255)
    app_fee = MoneyField(null=True)
    fee_payer = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    create_time = models.BigIntegerField(null=True)
    number_of_subscriptions = models.BigIntegerField(null=True)
    trial_length = models.BigIntegerField(null=True)
    setup_fee = MoneyField(null=True)
    reference_id = models.CharField(max_length=255)
    
    objects = AccountObjectsManager()

    class Meta(BaseModel.Meta):
        abstract = is_abstract('subscription_plan')
        db_table = 'djwepay_subscription_plan'
        verbose_name = 'WePay Subscription Plan'


class SubscriptionManager(models.Manager):
    
    def create_from_response(self, subscription_plan, response):
        obj = self.model(subscription_plan=subscription_plan)
        return obj.instance_update(response)

    def accessible(self):
        return self.exclude(subscription_plan__account__user__access_token=None)


class Subscription(SubscriptionApi, BaseModel):
    subscription_id = models.BigIntegerField(primary_key=True)
    subscription_plan = models.ForeignKey(
        get_wepay_model_name('subscription_plan'), related_name='subscriptions')
    payer_name = models.CharField(max_length=255)
    payer_email = models.CharField(max_length=255)
    currency = models.CharField(max_length=255)
    amount = MoneyField(null=True)
    period = models.CharField(max_length=255)
    app_fee = MoneyField(null=True)
    fee_payer = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    create_time = models.BigIntegerField(null=True)
    payment_method_id = models.BigIntegerField(null=True)
    payment_method_type = models.CharField(max_length=255)
    quantity = models.BigIntegerField(null=True)
    mode = models.CharField(max_length=255)
    trial_days_remaining = models.BigIntegerField(null=True)
    transition_expire_time = models.BigIntegerField(null=True)
    transition_prorate = models.NullBooleanField()
    transition_quantity = models.BigIntegerField(null=True)
    transition_subscription_plan = models.ForeignKey(
        get_wepay_model_name('subscription_plan'), 
        related_name='transition_subscriptions')
    reference_id = models.CharField(max_length=255)

    objects = SubscriptionManager()

    class Meta(BaseModel.Meta):
        abstract = is_abstract('subscription')
        db_table = 'djwepay_subscription'
        verbose_name = 'WePay Subscription'


class SubscriptionCharge(SubscriptionChargeApi, BaseModel):
    subscription_charge_id = models.BigIntegerField(primary_key=True)
    subscription_plan = models.ForeignKey(
        get_wepay_model_name('subscription_plan'), related_name='subscription_charges')
    subscription = models.ForeignKey(
        get_wepay_model_name('subscription'), related_name='subscription_charges')
    type = models.CharField(max_length=255)
    amount = MoneyField(null=True)
    currency = models.CharField(max_length=3)
    fee = MoneyField(null=True)
    app_fee = MoneyField(null=True)
    gross = MoneyField(null=True)
    quantity = models.BigIntegerField(null=True)
    amount_refunded = MoneyField(null=True)
    amount_charged_back = MoneyField(null=True)
    state = models.CharField(max_length=255)
    create_time = models.BigIntegerField(null=True)
    end_time = models.BigIntegerField(null=True)
    prorate_time = models.BigIntegerField(null=True)

    class Meta(BaseModel.Meta):
        abstract = is_abstract('subscription_charge')
        db_table = 'djwepay_subscription_charge'
        verbose_name = 'WePay Subscription Charge'
