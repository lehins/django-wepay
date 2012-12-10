import django
from django.db import models
from django.core.cache import cache

try:
    from django_localflavor_us.models import USStateField
except ImportError:
    from django.contrib.localflavor.us.models import USStateField


from django_wepay import forms, settings

import importlib

USER_STATE_CHOICES = (
    ('registered', u"Registered"),
    ('pending', u"Pending"),
)

ACCOUNT_STATE_CHOICES = (
    ('unverified', u"Unverified"),
    ('pending', u"Pending"),
    ('verified', u"Verified"),
)

ACCOUNT_TYPE_CHOICES = (
    ('personal', u"Personal"),
    ('nonprofit', u"Non-profit Organization"),
    ('business', u"Business"),
    ('membership', u"Membership Organization"),
)

CHECKOUT_TYPE_CHOICES = (
    ('GOODS', u"Goods"),
    ('SERVICE', u"Service"),
    ('DONATION', u"Donation"),
    ('EVENT', u"Event"),
    ('PERSONAL', u"Personal"),
)

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

CURRENCY_CHOICES = (
    ('USD', u"US Dollars"),
)

FEE_PAYER_CHOICES = (
    ('payer', u"Payer"),
    ('payee', u"Payee"),
)

PREAPPROVAL_STATE_CHOICES = (
    ('new', u"New"),
    ('approved', u"Approved"),
    ('revoked', u"Revoked"),
    ('expired', u"Expired"),
    ('canceled', u"Canceled"),
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

MODE_CHOICES = (
    ('regular', u"Regular"),
    ('iframe', u"iFrame"),
)

FUNDING_SOURCES = (
    ('bank,cc', u"Bank Account and Credit Card"),
    ('cc,bank', u"Bank Account and Credit Card"),
    ('bank', u"Only Bank Account"),
    ('cc', u"Only Credit Card"),
)

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

class MoneyField(models.DecimalField):
    def __init__(self, *args, **kwargs):
        if not 'decimal_places' in kwargs:
            kwargs['decimal_places'] = 2
        if not 'max_digits' in kwargs:
            kwargs['max_digits'] = 11
        super(MoneyField, self).__init__(*args, **kwargs)
    
    def formfield(self, **kwargs):
        defaults = {
            'max_digits': self.max_digits,
            'decimal_places': self.decimal_places,
            'form_class': forms.MoneyField,
        }
        defaults.update(kwargs)
        return super(MoneyField, self).formfield(**defaults)

class URLField(models.URLField):
    def __init__(self, *args, **kwargs):
        if not 'max_length' in kwargs:
            kwargs['max_length'] = 2083
        super(URLField, self).__init__(*args, **kwargs)

if 'south' in getattr(django.conf.settings, 'INSTALLED_APPS'):
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^django_wepay\.models_base\.%s" % f 
                                 for f in ["MoneyField", "URLField"]])



class BlankExtra(models.Model):
    class Meta:
        abstract = True

class BlankFull(models.Model):
    class Meta:
        abstract = True


class WPThemeManager(models.Manager):
    def get_default(self, *args, **kwargs):
        if 'name' in kwargs and 'default_theme' == kwargs['name']:
            if 'default_theme' in cache:
                query = cache.get('default_theme')
            else:
                query = self.get(*args, **kwargs)
                cache.set('deafult_theme', query)
        else:
            query = self.get(*args, **kwargs)
        return query
                
class WPThemeBase(models.Model):
    theme_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=141)
    primary_color = models.CharField(max_length=7)
    secondary_color = models.CharField(max_length=7)
    background_color = models.CharField(max_length=7)
    button_color = models.CharField(max_length=7)

    objects = WPThemeManager()

    class Meta:
        abstract = True
    """
    class WPApp(models.Model):
    client_id = models.IntegerField()
    client_secret = models.CharField(max_length=128)
    state = models.CharField(max_length=32)
    theme_object = models.ForeignKey(WPTheme)
    gaq_domains - Array
    """

class WPUserRest(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    scope = models.CharField(max_length=127, blank=True)
    class Meta:
        abstract = True


class WPAccountRest(models.Model):
    reference_id = models.CharField(max_length=127, blank=True)
    image_uri = URLField()
    callback_uri = URLField()

    class Meta:
        abstract = True
    

class WPPreapprovalRest(models.Model):
    short_description = models.CharField(max_length=127)
    long_description = models.CharField(max_length=2047)
    redirect_uri = URLField()
    callback_uri = URLField()
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    frequency = models.SmallIntegerField(default=1)
    auto_recur = models.BooleanField(default=False)
    mode = models.CharField(max_length=7, choices=MODE_CHOICES)
    funding_sources = models.CharField(max_length=8, choices=FUNDING_SOURCES)
    reference_id = models.CharField(max_length=127, blank=True)
    shipping_fee = MoneyField(default=0)
    tax = MoneyField(default=0)
    charge_tax = models.BooleanField(default=False)
    payer_email_message = models.CharField(max_length=255, blank=True)
    payee_email_message = models.CharField(max_length=255, blank=True)
    
    class Meta:
        abstract = True


class WPCheckoutRest(models.Model):
    short_description = models.CharField(max_length=127)
    long_description = models.CharField(max_length=2047)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    redirect_uri = URLField()
    callback_uri = URLField()
    tax = MoneyField()
    type = models.CharField(max_length=8, choices=CHECKOUT_TYPE_CHOICES)
    payer_email_message = models.CharField(max_length=255)
    payee_email_message = models.CharField(max_length=255)
    reference_id = models.CharField(max_length=127, blank=True)
    shipping_fee = MoneyField()
    mode = models.CharField(max_length=7, choices=MODE_CHOICES)
    funding_sources = models.CharField(max_length=8, choices=FUNDING_SOURCES)
    charge_tax = models.BooleanField(default=False)

    class Meta:
        abstract = True

class WPWithdrawalRest(models.Model):
    redirect_uri = URLField()
    callback_uri = URLField()

    class Meta:
        abstract = True

# setting up the models with extra fields
if settings.WEPAY_EXTRA_MODELS_MODULE:
    extra_models_module = importlib.import_module(settings.WEPAY_EXTRA_MODELS_MODULE)
    extra_models = dict(settings.WEPAY_EXTRA_MODELS)

    WPAddressExtra = BlankExtra if 'WPAddress' not in extra_models else \
        getattr(extra_models_module, extra_models.get('WPAddress'))
    WPUserExtra = BlankExtra if 'WPUser' not in extra_models else \
        getattr(extra_models_module, extra_models.get('WPUser'))
    WPAccountExtra = BlankExtra if 'WPAccount' not in extra_models else \
        getattr(extra_models_module, extra_models.get('WPAccount'))
    WPPreapprovalExtra = BlankExtra if 'WPPreapproval' not in extra_models else \
        getattr(extra_models_module, extra_models.get('WPPreapproval'))
    WPCheckoutExtra = BlankExtra if 'WPCheckout' not in extra_models else \
        getattr(extra_models_module, extra_models.get('WPCheckout'))
    WPWithdrawalExtra = BlankExtra if 'WPWithdrawal' not in extra_models else \
        getattr(extra_models_module, extra_models.get('WPWithdrawal'))
else:
    WPAddressExtra = BlankExtra
    WPUserExtra = BlankExtra
    WPAccountExtra = BlankExtra
    WPCheckoutExtra = BlankExtra
    WPPreapprovalExtra = BlankExtra
    WPWithdrawalExtra = BlankExtra

# applying the rest of the fields
WPUserFull = BlankFull if 'WPUser' not in settings.WEPAY_FULL_MODELS \
    else WPUserRest
WPAccountFull = BlankFull if 'WPAccount' not in settings.WEPAY_FULL_MODELS \
    else WPAccountRest
WPCheckoutFull = BlankFull if 'WPCheckout' not in settings.WEPAY_FULL_MODELS \
    else WPCheckoutRest
WPPreapprovalFull = BlankFull if 'WPPreapproval' not in settings.WEPAY_FULL_MODELS \
    else WPPreapprovalRest
WPWithdrawalFull = BlankFull if 'WPWithdrawal' not in settings.WEPAY_FULL_MODELS \
    else WPWithdrawalRest

