import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

try:
    if not getattr(settings, 'WEPAY_USE_LOGICALDELETE', True):
        raise ImportError
    from logicaldelete.managers import LogicalDeleteManager as Manager
    USE_LOGICALDELETE = True
except ImportError:
    from django.db.models import Manager
    USE_LOGICALDELETE = False

# Add MoneyField to 'south', so migrations are possible
try:
    if 'south' in getattr(settings, 'INSTALLED_APPS'):
        from south.modelsinspector import add_introspection_rules
        add_introspection_rules([], ["^djwepay\.models\.MoneyField"])
except ImportError: pass


class MoneyField(models.DecimalField):
    def __init__(self, *args, **kwargs):
        if not 'decimal_places' in kwargs:
            kwargs['decimal_places'] = 2
        if not 'max_digits' in kwargs:
            kwargs['max_digits'] = 11 # ~1 billion USD, should be enough for now
        super(MoneyField, self).__init__(*args, **kwargs)


class BaseModel(models.Model):
    date_created  = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    date_removed  = models.DateTimeField(null=True, blank=True)

    objects = Manager()

    def __init__(self, **kwargs):
        self._create_kwargs = kwargs
        # filter out kwargs that are not model fields
        field_names = self._meta.get_all_field_names()
        field_kwarg = dict([(x, kwargs[x]) for x in field_names if x in kwargs])
        super(BaseModel, self).__init__(**field_kwargs)
        

    def save(self, *args, **kwargs):
        response = None
        if not self.pk:
            response = self.wepay.create(**self._create_kwargs)
            for field_name in self._meta.get_all_field_names():
                if field_name in response:
                    setattr(self, field_name, response.get(field_name))
        super(BaseModel, self).save(*args, **kwargs)
        return response
    
    def active(self):
        return self.date_removed == None
    active.boolean = True
    
    def delete(self, db_delete=USE_LOGICALDELETE):
        if db_delete:
            super(BaseModel, self).delete()
        else:
            self.date_removed = datetime.datetime.now()
            self.save()
    
    class Meta:
        abstract = True
        ordering = ['-date_created']

class Address(BaseModel):
    address1 = models.CharField(max_length=255, blank=True)
    address2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=2, blank=True)
    region = models.CharField(max_length=255, blank=True)
    zip = models.CharField(max_length=255, blank=True)
    postcode = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "djwepay_address"

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
    expires_in = models.PositiveIntegerField(null=True)

    # in case that different django users are using the same login on WePay
    django_users = models.ManyToManyField(
        get_user_model(), related_name='wepay_users') 
    
    def __str__(self):
        return self.user_name

    def delete(self, db_delete=USE_LOGICALDELETE):
        for account in self.account_set.all():
            account.delete(db_delete=db_delete)
        super(User, self).delete(db_delete=db_delete)
                           
    class Meta:
        db_table = "djwepay_user"


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
    verification_state = models.CharField(
        max_length=15, choices=ACCOUNT_VERIFICATION_STATE_CHOICES)
    type = models.CharField(max_length=255, choices=ACCOUNT_TYPE_CHOICES)
    pending_balance = MoneyField(default=0)
    available_balance = MoneyField(default=0)
    pending_amount = MoneyField(default=0)
    reserved_amount = MoneyField(default=0)
    disputed_amount = MoneyField(default=0)

    def __str__(self):
        return self.name

    def delete(self, db_delete=USE_LOGICALDELETE):
        for preapproval in self.preapproval_set.all():
            preapproval.delete(db_delete=db_delete)
        for checkout in self.checkout_set.all():
            checkout.delete(db_delete=db_delete)
        for withdrawal in self.withdrawal_set.all():
            withdrawal.delete(db_delete=db_delete)
        super(Account, self).delete(db_delete=db_delete)

    class Meta:
        db_table = "djwepay_account"


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
    amount = MoneyField()
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
    shipping_address = models.ForeignKey(Address, null=True)
    tax = MoneyField(null=True)
    amount_refunded = MoneyField(null=True)
    create_time = models.BigIntegerField()
    mode = models.CharField(max_length=15, choices=CHECKOUT_MODE_CHOICES)

    # all are max_length = 2083
    redirect_uri = None
    callback_uri = None
    dispute_uri = None
    fallback_uri = None # only in create

    # if it is necessary to track who actually payed or received the payment
    payer = models.ForeignKey(
        get_user_model(), related_name='wepay_payer_checkouts', null=True)
    payee = models.ForeignKey(
        get_user_model(), related_name='wepay_payee_checkouts', null=True)

    def __str__(self):
        return self.short_description

    class Meta:
        db_table = "djwepay_checkout"



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
    shipping_address = models.ForeignKey(Address, null=True)
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

    preapproval_uri = None
    manage_uri = None
    redirect_uri = None
    callback_uri = None
    fallback_uri = None # only in create

    # if it is necessary to track who actually payed or received the payment
    payer = models.ForeignKey(
        get_user_model(), related_name='wepay_payer_preapprovals', null=True)
    payee = models.ForeignKey(
        get_user_model(), related_name='wepay_payee_preapprovals', null=True)

    def __str__(self):
        return self.short_description

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

    redirect_uri = None
    withdrawal_uri = None
    callback_uri = None

    def __str__(self):
        return self.pk

    class Meta:
        db_table = "djwepay_withdrawal"


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

    # in case if necessary to track who used a credit card
    owner = models.ForeignKey(
        get_user_model(), related_name='wepay_owner_credit_cards', null=True)

    class Meta:
        db_table = "djwepay_credit_card"
