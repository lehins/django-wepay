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

    class Meta:
        abstract = True
        ordering = ['-date_created']

class AppManager(models.Manager):

    def get_current(self):
        """
        Returns the current ``App`` based on the ``WEPAY_APP_ID`` in the
        project's settings. The ``App`` object is cached the first
        time it's retrieved from the database.
        """
        try:
            app_id = settings.WEPAY_APP_ID
        except AttributeError:
            raise ImproperlyConfigured(
                "You're using the Django WePay application without having set the "
                "WEPAY_APP_ID setting. Create a site in your database and set the "
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
    Due to the fact that mostly only a single app will be used with a django instance
    App model is abstract and is here for pure consistency with a mapping of 
    WePay objects to django models. If necessary can be extended as a concrete model
    and it might be converted to a concrete model in future.
    """
    client_id = models.BigIntegerField(primary_key=True)
    status = models.CharField(max_length=255)
    theme_object = JSONField()
    gaq_domains = JSONField()

    client_secret = models.CharField(max_length=255)
    access_token = models.CharField(max_length=255)
    production = models.BooleanField(default=True)

    objects = AppManager()

    class Meta:
        abstract = is_abstract('app')
        db_table = 'djwepay_app'
        verbose_name = 'WePay App'

class UserManager(models.Manager):
    
    def active(self):
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

    class Meta:
        abstract = is_abstract('user')
        db_table = 'djwepay_user'
        verbose_name = 'WePay User'


class Account(AccountApi, BaseModel):
    account_id = models.BigIntegerField(primary_key=True)
    user = models.ForeignKey(get_wepay_model_name('user'))
    name = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    reference_id = models.CharField(max_length=255)
    payment_limit = MoneyField(null=True)
    gaq_domains = JSONField()
    theme_object = JSONField()
    verification_state = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    create_time = models.BigIntegerField()

    
    def __str__(self):
        return "%s - %s" % (self.pk, self.name)

    class Meta:
        abstract = is_abstract('account')
        db_table = 'djwepay_account'
        verbose_name = 'WePay Account'


class Checkout(CheckoutApi, BaseModel):
    checkout_id = models.BigIntegerField(primary_key=True)
    account = models.ForeignKey(get_wepay_model_name('account'))
    preapproval = models.ForeignKey(get_wepay_model_name('preapproval'), null=True)
    state = models.CharField(max_length=255)
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
    create_time = models.BigIntegerField()
    mode = models.CharField(max_length=255)

    def __str__(self):
        return "%s - %s" % (self.pk, self.short_description)

    class Meta:
        abstract = is_abstract('checkout')
        db_table = 'djwepay_checkout'
        verbose_name = 'WePay Checkout'


class Preapproval(PreapprovalApi, BaseModel):
    preapproval_id = models.BigIntegerField(primary_key=True)
    account = models.ForeignKey(get_wepay_model_name('account'))
    short_description = models.CharField(max_length=255)
    long_description = models.CharField(max_length=2047, blank=True)
    currency = "USD"
    amount = MoneyField()
    fee_payer = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    app_fee = MoneyField()
    period = models.CharField(max_length=255)
    frequency = models.IntegerField(null=True)
    start_time = models.BigIntegerField(null=True)
    end_time = models.BigIntegerField(null=True)
    reference_id = models.CharField(max_length=255)
    shipping_address = JSONField(null=True)
    shipping_fee = MoneyField(null=True)
    tax = MoneyField(null=True)
    auto_recur = models.BooleanField()
    payer_name = models.CharField(max_length=255)
    payer_email = models.EmailField(max_length=255, blank=True)
    create_time = models.BigIntegerField(null=True)
    next_due_time = models.BigIntegerField(null=True)
    last_checkout = models.ForeignKey(
        get_wepay_model_name('checkout'), null=True, related_name='+')
    last_checkout_time = models.BigIntegerField(null=True)
    mode = models.CharField(max_length=255)

    def __str__(self):
        return "%s - %s" % (self.pk, self.short_description)

    class Meta:
        abstract = is_abstract('preapproval')
        db_table = 'djwepay_preapproval'
        verbose_name = 'WePay Preapproval'


class Withdrawal(WithdrawalApi, BaseModel):
    withdrawal_id = models.BigIntegerField(primary_key=True)
    account = models.ForeignKey(get_wepay_model_name('account'))
    state = models.CharField(max_length=255)
    amount = MoneyField(null=True)
    note = models.CharField(max_length=255)
    recipient_confirmed = models.NullBooleanField()
    type = models.CharField(max_length=255)
    create_time = models.BigIntegerField()

    def __str__(self):
        return "%s - %s" % (self.pk, self.amount)

    class Meta:
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

    class Meta:
        abstract = is_abstract('credit_card')
        db_table = 'djwepay_credit_card'
        verbose_name = 'WePay Credit Card'
