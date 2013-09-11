import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.functional import LazyObject

from djwepay.api import WePay
from djwepay.decorators import batchable
from djwepay.fields import MoneyField
from djwepay.signals import state_changed

from json_field import JSONField

try:
    if not getattr(settings, 'WEPAY_USE_LOGICALDELETE', True):
        raise ImportError
    from logicaldelete.managers import LogicalDeleteManager as Manager
    USE_LOGICALDELETE = True
except ImportError:
    from django.db.models import Manager
    USE_LOGICALDELETE = False


__all__ = ['App', 'User', 'Account', 'Checkout', 'Preapproval',
           'Withdrawal', 'CreditCard']

APP_CACHE = {}

class WePayLazy(LazyObject):
    def _setup(self):
        self._wrapped = WePay(App.objects.get_current())


class BaseModel(models.Model):
    date_created  = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    date_removed  = models.DateTimeField(null=True, blank=True)

    objects = Manager()

    api = WePayLazy()
    
    def __init__(self, *args, **kwargs):
        super(BaseModel, self).__init__(*args)
        self._api_update(kwargs)

    def _api_create(self, model, response, update, commit, object_name=None):
        object_name = object_name or model.__name__.lower()
        object_id_key = "%s_id" % object_name
        try:
            obj = model.objects.get(pk=response[object_id_key])
            obj._api_update(response)
            if not obj.active():
                obj.undelete()
        except model.DoesNotExist:
            obj = model(**response)
        if update:
            call_method = getattr(self.api, object_name)
            params = {
                'access_token': self.access_token
            }
            if object_name == 'user':
                params = {
                    'access_token': response['access_token']
                }
            else:
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
        return self.api.get_full_uri(reverse('wepay:ipn:%s', kwargs=kwargs))

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


class App(BaseModel):
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
        return self._api_create(User, response, update, commit)

    def api_preapproval_create(self, *args, **kwargs):
        update = kwargs.pop('update', True)
        commit = kwargs.pop('commit', True)
        if not self._api_uri_modifier(kwargs):
            kwargs['callback_uri'] = self._api_callback_uri('preapproval', obj_name)
        self._api_uri_modifier(kwargs, name='redirect_uri')
        self._api_uri_modifier(kwargs, name='fallback_uri')
        response = self.api.preapproval_create(
            self.client_id, *args, access_token=self.client_secret, **kwargs)
        return self._api_create(Preapproval, response, update, commit)

    def api_preapproval_find(self, **kwargs):
        return self.api.preapproval_find(**kwargs)

    def api_credit_card_create(self, *args, **kwargs):
        update = kwargs.pop('update', True)
        commit = kwargs.pop('commit', True)
        response = self.api.credit_card_create(*args, **kwargs)
        return self._api_create(CreditCard, response, update, commit, 
                                object_name='credit_card')

    def api_credit_card_find(self, **kwargs):
        return self.api.credit_card_find(**kwargs)

    class Meta:
        db_table = 'djwepay_app'
        verbose_name = 'WePay App'


USER_STATE_CHOICES = (
    ('registered', u"Registered"),
    ('pending', u"Pending"),
)

class User(BaseModel):
    user_id = models.BigIntegerField(primary_key=True)
    user_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    state = models.CharField(max_length=15, choices=USER_STATE_CHOICES)

    access_token = models.CharField(max_length=255)
    token_type = "BEARER"
    expires_in = models.PositiveIntegerField(null=True, blank=True)

    callback_uri = models.URLField(blank=True)
    # in case that different django users are using the same WePay user
    auth_users = models.ManyToManyField(
        get_user_model(), related_name='wepay_users') 
    
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
        if 'callback_uri' not in kwargs:
            kwargs['callback_uri'] = self.api.get_full_uri(
                reverse('wepay:ipn:account', 
                        kwargs={'user_id': self.pk}))
        else:
            kwargs.update({
                'callback_uri': self.api.get_full_uri(kwargs['callback_uri'])
            })
        response = self.api.account_create(
            *args, access_token=self.access_token, **kwargs)
        account, response = self._api_create(Account, response, update, False)
        account.user = self
        if commit:
            account.save()
        return account, response

    def api_account_find(self, **kwargs):
        return self.api.account_find(
            access_token=self.access_token, **kwargs)

    class Meta:
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

class Account(BaseModel):
    account_id = models.BigIntegerField(primary_key=True)
    user = models.ForeignKey(User)
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

    def get_callback_uri(self):
        return self._api_callback_uri('account', user_id = self.user_id)

    def api_account(self, **kwargs):
        try:
            return self._api_update(self.api.account(
                self.pk, access_token=self.access_token, *args, **kwargs))
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

    def _api_account_object_create(self, model, *args, **kwargs):
        obj_name = model.__name__.lower()
        update = kwargs.pop('update', True)
        commit = kwargs.pop('commit', True)
        if not self._api_uri_modifier(kwargs):
            kwargs['callback_uri'] = self._api_callback_uri(
                obj_name, user_id=self.user_id)
        self._api_uri_modifier(kwargs, name='redirect_uri')
        method_create = getattr(self.api, "%s_create" % obj_name)
        response = method_create(
            self.pk, *args, access_token=self.access_token, **kwargs)
        return self._api_create(model, response, update, commit)


    def api_checkout_create(self, *args, **kwargs):
        preapproval = kwargs.pop('preapproval', None)
        if not preapproval is None and isinstance(type(preapproval), Preapproval):
            kwargs['preapproval_id'] = preapproval.pk
        return self._api_account_object_create(Checkout, *args, **kwargs)

    def api_preapproval_create(self, *args,  **kwargs):
        return self._api_account_object_create(Preapproval, *args, **kwargs)

    def api_withdrawal_create(self, *args,  **kwargs):
        return self._api_account_object_create(Withdrawal, *args, **kwargs)

    def api_checkout_find(self, **kwargs):
        return self.api.checkout_find(
            self.pk, access_token=self.access_token, **kwargs)

    def api_preapproval_find(self, **kwargs):
        return self.api.preapproval_find(
            account_id=self.pk, access_token=self.access_token, **kwargs)

    def api_withdrawal_find(self, **kwargs):
        return self.api.withdrawal_find(
            self.pk, access_token=self.access_token, **kwargs)

    class Meta:
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

class Checkout(BaseModel):
    checkout_id = models.BigIntegerField(primary_key=True)
    account = models.ForeignKey(Account)
    preapproval = models.ForeignKey('djwepay.Preapproval', null=True)
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

    # if it is necessary to track who actually payed or received the payment
    payer = models.ForeignKey(
        get_user_model(), related_name='wepay_payer_checkouts', null=True)
    payee = models.ForeignKey(
        get_user_model(), related_name='wepay_payee_checkouts', null=True)

    # TODO: get _uri attributes to act as properties with dynamically getting values

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

    class Meta:
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

class Preapproval(BaseModel):
    preapproval_id = models.BigIntegerField(primary_key=True)
    account = models.ForeignKey(Account)
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
    last_checkout = models.ForeignKey(Checkout, null=True, related_name='+')
    last_checkout_time = models.BigIntegerField()
    mode = models.CharField(max_length=15, choices=PREAPPROVAL_MODE_CHOICES)

    callback_uri = models.URLField(blank=True)
    preapproval_uri = None
    manage_uri = None
    redirect_uri = None
    fallback_uri = None # only in create

    # if it is necessary to track who actually payed or received the payment
    payer = models.ForeignKey(
        get_user_model(), related_name='wepay_payer_preapprovals', null=True)
    payee = models.ForeignKey(
        get_user_model(), related_name='wepay_payee_preapprovals', null=True)

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

    class Meta:
        db_table = "djwepay_preapproval"


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

class Withdrawal(BaseModel):
    withdrawal_id = models.BigIntegerField(primary_key=True)
    account = models.ForeignKey(Account)
    state = models.CharField(max_length=15, choices=WITHDRAWAL_STATE_CHOICES)
    amount = MoneyField(null=True)
    note = models.CharField(max_length=255)
    recipient_confirmed = models.NullBooleanField()
    type = models.CharField(max_length=15, choices=WITHDRAWAL_TYPE_CHOICES)
    create_time = models.BigIntegerField()

    initiator = models.ForeignKey(
        get_user_model(), related_name='wepay_initiator_withdrawals', null=True)

    callback_uri = models.URLField(blank=True)
    redirect_uri = None

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

    class Meta:
        db_table = 'djwepay_withdrawal'
        verbose_name = 'WePay Preapproval'


CREDIT_CARD_STATE_CHOICES = (
    ('new', u"New"),
    ('authorized', u"Authorized"),
    ('expired', u"Expired"),
    ('deleted', u"Deleted"),
    ('invalid', u"Invalid"),
)

class CreditCard(BaseModel):
    credit_card_id = models.BigIntegerField(primary_key=True)
    credit_card_name = models.CharField(max_length=255)
    state = models.CharField(max_length=15, choices=CREDIT_CARD_STATE_CHOICES)
    user_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, blank=True)
    reference_id = models.CharField(max_length=255, blank=True)

    # in case if necessary to track who owns (can use) the credit card
    auth_users = models.ManyToManyField(
        get_user_model(), related_name='wepay_credit_card', null=True)

    def api_credit_card(self, **kwargs):
        return self._api_update(self.api.credit_card(self.pk, **kwargs))

    def api_credit_card_authorize(self, **kwargs):
        return self._api_update(self.api.credit_card_authorize(self.pk, **kwargs))

    def api_credit_card_delete(self, **kwargs):
        return self._api_update(self.api.credit_card_delete(self.pk, **kwargs))

    
    class Meta:
        db_table = 'djwepay_credit_card'
        verbose_name = 'WePay Credit Card'
