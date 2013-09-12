import datetime
from django.conf import settings
from django.db import models
from django.utils.functional import LazyObject

from djwepay.api import *
from djwepay.fields import MoneyField
from djwepay.utils import from_string_import

from json_field import JSONField

try:
    if not getattr(settings, 'WEPAY_USE_LOGICALDELETE', True):
        raise ImportError
    from logicaldelete.managers import LogicalDeleteManager as Manager
    USE_LOGICALDELETE = True
except ImportError:
    from django.db.models import Manager
    USE_LOGICALDELETE = False

API_BACKEND = getattr(settings, 'WEPAY_API_BACKEND', 'djwepay.backends.WePay')

__all__ = ['App', 'User', 'Account', 'Checkout', 'Preapproval', 'Withdrawal', 
           'CreditCard']

APP_CACHE = {}

class WePayLazy(LazyObject):
    def _setup(self):
        backend = from_string_import(API_BACKEND)
        self._wrapped = backend(App.objects.get_current())


class BaseModel(models.Model):
    date_created  = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    date_removed  = models.DateTimeField(null=True, blank=True)

    objects = Manager()

    api = WePayLazy()
    
    def __init__(self, *args, **kwargs):
        super(BaseModel, self).__init__(*args)
        self._api_update(kwargs)


    def active(self):
        return self.date_removed == None
    active.boolean = True
    
    def delete(self, db_delete=USE_LOGICALDELETE):
        if db_delete:
            super(BaseModel, self).delete()
        else:
            self.date_removed = datetime.datetime.now()
            self.save()
            
    def undelete(self):
        if not USE_LOGICAL_DELETE:
            raise ImproperlyConfigured(
                "'undelete' can only be used together with 'django-logicaldelete'")
        self.date_removed = None
        self.save()

    class Meta:
        abstract = True
        ordering = ['-date_created']

class AppManager(Manager):

    def get_current(self):
        """
        Returns the current ``App`` based on the WEPAY_APP_ID in the
        project's settings. The ``App`` object is cached the first
        time it's retrieved from the database.
        """
        try:
            app_id = settings.WEPAY_APP_ID
        except AttributeError:
            raise ImproperlyConfigured("You're using the Django \"sites framework\" without having set the SITE_ID setting. Create a site in your database and set the SITE_ID setting to fix this error.")
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
    theme_object = JSONField(blank=True)
    gaq_domains = JSONField(blank=True)

    client_secret = models.CharField(max_length=255)
    access_token = models.CharField(max_length=255)
    production = models.BooleanField(default=True)

    objects = AppManager()


    class Meta:
        abstract = is_abstract('app'))
        db_table = 'djwepay_app'
        verbose_name = 'WePay App'


USER_STATE_CHOICES = (
    ('registered', u"Registered"),
    ('pending', u"Pending"),
)

class User(UserApi, BaseModel):
    user_id = models.BigIntegerField(primary_key=True)
    user_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    state = models.CharField(max_length=15, choices=USER_STATE_CHOICES)

    access_token = models.CharField(max_length=255)
    token_type = "BEARER"
    expires_in = models.BigIntegerField(null=True, blank=True)

    callback_uri = models.URLField(blank=True)
    
    def __str__(self):
        return self.user_name

    def delete(self, db_delete=USE_LOGICALDELETE):
        accounts = Account.objects.filter(user=self)
        for account in accounts:
            account.delete(db_delete=db_delete)
        super(User, self).delete(db_delete=db_delete)

    def undelete(self):
        if not USE_LOGICAL_DELETE:
            raise ImproperlyConfigured(
                "'undelete' can only be used together with 'django-logicaldelete'")
        accounts= Account.objects.only_deleted().filter(user=self)
        for account in accounts:
            account.undelete()
        super(User, self).undelete()

    class Meta:
        abstract = is_abstract('user')
        db_table = 'djwepay_user'
        verbose_name = 'WePay User'


ACCOUNT_STATE_CHOICES = (
    ('active', u"Active"),
    ('disabled', u"Disabled"),
    ('deleted', u"Deleted"),
)
ACCOUNT_VERIFICATION_STATE_CHOICES = (
    ('unverified', u"Unverified"),
    ('pending', u"Pending"),
    ('verified', u"Verified"),
)
ACCOUNT_TYPE_CHOICES = (
    ('personal', u"Personal"),
    ('nonprofit', u"Non-profit Organization"),
    ('business', u"Business"),
)

class Account(AccountApi, BaseModel):
    account_id = models.BigIntegerField(primary_key=True)
    user = models.ForeignKey(get_wepay_model_name('user'))
    name = models.CharField(max_length=255)
    state = models.CharField(max_length=15, choices=ACCOUNT_STATE_CHOICES)
    description = models.CharField(max_length=255)
    reference_id = models.CharField(max_length=255)
    payment_limit = MoneyField(null=True)
    theme_object = JSONField(blank=True)
    gaq_domains = JSONField(blank=True)
    verification_state = models.CharField(
        max_length=15, choices=ACCOUNT_VERIFICATION_STATE_CHOICES)
    type = models.CharField(max_length=255, choices=ACCOUNT_TYPE_CHOICES)
    create_time = models.BigIntegerField()

    image_uri = models.URLField(blank=True)
    mcc = models.PositiveSmallIntegerField(null=True)
    callback_uri = models.URLField(blank=True)

    account_uri = None
    verification_uri = None

    add_bank_uri = None

    def __str__(self):
        return "%s - %s" % (self.pk, self.name)

    def delete(self, db_delete=USE_LOGICALDELETE):
        preapprovals = Preapproval.objects.filter(account=self)
        checkouts = Checkout.objects.filter(account=self)
        withdrawals = Withdrawal.objects.filter(account=self)
        for preapproval in self.preapproval_set.all():
            preapproval.delete(db_delete=db_delete)
        for checkout in self.checkout_set.all():
            checkout.delete(db_delete=db_delete)
        for withdrawal in self.withdrawal_set.all():
            withdrawal.delete(db_delete=db_delete)
        super(Account, self).delete(db_delete=db_delete)

    def undelete(self):
        if not USE_LOGICAL_DELETE:
            raise ImproperlyConfigured(
                "'undelete' can only be used together with 'django-logicaldelete'")
        preapprovals = Preapproval.objects.only_deleted().filter(account=self)
        checkouts = Checkout.objects.only_deleted().filter(account=self)
        withdrawals = Withdrawal.objects.only_deleted().filter(account=self)
        for preapproval in preapprovals:
            preapproval.undelete()
        for checkout in checkouts:
            checkout.undelete()
        for withdrawal in withdrawals:
            withdrawal.undelete()
        super(Account, self).undelete()


    class Meta:
        abstract = is_abstract('account')
        db_table = 'djwepay_account'
        verbose_name = 'WePay Account'


CHECKOUT_STATE_CHOICES = (
    ('new', u"New"),
    ('authorized', u"Authorized"),
    ('reserved', u"Reserved"),
    ('captured', u"Captured"),
    ('settled', u"Settled"),
    ('cancelled', u"Cancelled"),
    ('refunded', u"Refunded"),
    ('charged back', u"Charged Back"),
    ('failed', u"Failed"),
    ('expired', u"Expired"),
)
CHECKOUT_FEE_PAYER_CHOICES = (
    ('payer', u"Payer"),
    ('payee', u"Payee"),
    ('payer_from_app', u"Payer is the App"),
    ('payee_from_app', u"Payee is the App"),
)
CHECKOUT_MODE_CHOICES = (
    ('regular', u"Regular"),
    ('iframe', u"iFrame"),
)

class Checkout(CheckoutApi, BaseModel):
    checkout_id = models.BigIntegerField(primary_key=True)
    account = models.ForeignKey(get_wepay_model_name('account'))
    preapproval = models.ForeignKey(get_wepay_model_name('preapproval'), null=True)
    state = models.CharField(max_length=255, choices=CHECKOUT_STATE_CHOICES)
    short_description = models.CharField(max_length=255)
    long_description = models.CharField(max_length=2047, blank=True)
    currency = "USD"
    amount = MoneyField(null=True)
    fee = MoneyField(null=True)
    gross = MoneyField(null=True)
    app_fee = MoneyField(null=True)
    fee_payer = models.CharField(max_length=15, choices=CHECKOUT_FEE_PAYER_CHOICES)
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
    mode = models.CharField(max_length=15, choices=CHECKOUT_MODE_CHOICES)

    callback_uri = models.URLField(blank=True)
    # all are max_length = 2083
    redirect_uri = None
    dispute_uri = None
    fallback_uri = None # only in create

    class Meta:
        abstract = is_abstract('checkout')
        db_table = 'djwepay_checkout'
        verbose_name = 'WePay Checkout'



PREAPPROVAL_FEE_PAYER_CHOICES = CHECKOUT_FEE_PAYER_CHOICES
PREAPPROVAL_STATE_CHOICES = (
    ('new', u"New"),
    ('approved', u"Approved"),
    ('expired', u"Expired"),
    ('revoked', u"Revoked"),
    ('canceled', u"Canceled"),
    ('stopped', u"Stopped"),
    ('completed', u"Completed"),
    ('retrying', u"Retrying"),
)
PREAPPROVAL_PERIOD_CHOICES = (
    ('hourly', u'Hourly'), 
    ('daily', u'Daily'), 
    ('weekly', u'Weekly'), 
    ('biweekly', u'Biweekly'), 
    ('monthly', u'Monthly'), 
    ('bimonthly', u'Bimonthly'), 
    ('quarterly', u'Quarterly'), 
    ('yearly', u'Yearly'), 
    ('once', u'Once'),
)
PREAPPROVAL_MODE_CHOICES = CHECKOUT_MODE_CHOICES

class Preapproval(PreapprovalApi, BaseModel):
    preapproval_id = models.BigIntegerField(primary_key=True)
    account = models.ForeignKey(get_wepay_model_name('account'))
    short_description = models.CharField(max_length=255)
    long_description = models.CharField(max_length=2047, blank=True)
    currency = "USD"
    amount = MoneyField()
    fee_payer = models.CharField(max_length=15, choices=PREAPPROVAL_FEE_PAYER_CHOICES)
    state = models.CharField(max_length=15, choices=PREAPPROVAL_STATE_CHOICES)
    app_fee = MoneyField()
    period = models.CharField(max_length=15, choices=PREAPPROVAL_PERIOD_CHOICES)
    frequency = models.IntegerField()
    start_time = models.BigIntegerField()
    end_time = models.BigIntegerField()
    reference_id = models.CharField(max_length=255)
    shipping_address = JSONField(null=True)
    shipping_fee = MoneyField(null=True)
    tax = MoneyField(null=True)
    auto_recur = models.BooleanField()
    payer_name = models.CharField(max_length=255)
    payer_email = models.EmailField(max_length=255, blank=True)
    create_time = models.BigIntegerField()
    next_due_time = models.BigIntegerField()
    last_checkout = models.ForeignKey(
        get_wepay_model_name('checkout'), null=True, related_name='+')
    last_checkout_time = models.BigIntegerField(null=True)
    mode = models.CharField(max_length=15, choices=PREAPPROVAL_MODE_CHOICES)

    callback_uri = models.URLField(blank=True)
    preapproval_uri = None
    manage_uri = None
    redirect_uri = None
    fallback_uri = None # only in create

    class Meta:
        abstract = is_abstract('preapproval')
        db_table = 'djwepay_preapproval'
        verbose_name = 'WePay Preapproval'


WITHDRAWAL_STATE_CHOICES = (
    ('new', u"New"),
    ('authorized', u"Authorized"),
    ('started', u"Started"),
    ('captured', u"Captured"),
    ('settled', u"Settled"),
    ('cancelled', u"Cancelled"),
    ('refunded', u"Refunded"),
    ('failed', u"Failed"),
    ('expired', u"Expired"),
    ('NONE', u"Bug inside WePay"),
)
WITHDRAWAL_TYPE_CHOICES = (
    ('check', u"Check"),
    ('ach', u"ACH"),
)

class Withdrawal(WithdrawalApi, BaseModel):
    withdrawal_id = models.BigIntegerField(primary_key=True)
    account = models.ForeignKey(get_wepay_model_name('account'))
    state = models.CharField(max_length=15, choices=WITHDRAWAL_STATE_CHOICES)
    amount = MoneyField(null=True)
    note = models.CharField(max_length=255)
    recipient_confirmed = models.NullBooleanField()
    type = models.CharField(max_length=15, choices=WITHDRAWAL_TYPE_CHOICES)
    create_time = models.BigIntegerField()

    callback_uri = models.URLField(blank=True)
    redirect_uri = None

    class Meta:
        abstract = is_abstract('withdrawal')
        db_table = 'djwepay_withdrawal'
        verbose_name = 'WePay Preapproval'


CREDIT_CARD_STATE_CHOICES = (
    ('new', u"New"),
    ('authorized', u"Authorized"),
    ('expired', u"Expired"),
    ('deleted', u"Deleted"),
    ('invalid', u"Invalid"),
)

class CreditCard(CreditCardApi, BaseModel):
    credit_card_id = models.BigIntegerField(primary_key=True)
    credit_card_name = models.CharField(max_length=255)
    state = models.CharField(max_length=15, choices=CREDIT_CARD_STATE_CHOICES)
    user_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, blank=True)
    reference_id = models.CharField(max_length=255, blank=True)

    class Meta:
        abstract = is_abstract('credit_card')
        db_table = 'djwepay_credit_card'
        verbose_name = 'WePay Credit Card'
