from django_wepay.models_base import *
from django_wepay.settings import WEPAY_RETAIN_RECORDS

__all__ = ['WPAddress', 'WPUser', 'WPAccount', 'WPCheckout', 'WPPreapproval',
           'WPWithdrawal']

class WPQuerySet(models.query.QuerySet):

    def create(self, **kwargs):
        fields = self.model._meta.get_all_field_names()
        kwargs = dict([(x, kwargs[x]) for x in fields if x in kwargs])
        kwargs = self.concat_fields(**kwargs)
        shipping_address = kwargs.pop('shipping_address', None)
        if shipping_address:
            kwargs['shipping_address'] = self.model._meta.get_field(
                'shipping_address').rel.to.objects.create_revive(**shipping_address)
        return super(WPQuerySet, self).create(**kwargs)

    def create_revive(self, **kwargs):
        fields = self.model._meta.get_all_field_names()
        kwargs = dict([(x, kwargs[x]) for x in fields if x in kwargs])
        kwargs = self.concat_fields(**kwargs)
        kwargs.update({'deleted': False})
        shipping_address = kwargs.pop('shipping_address', None)
        obj = self.model(**kwargs)
        self._for_write = True
        obj.save()
        if shipping_address:
            if obj.shipping_address:
                obj.shipping_address.update(**shipping_address)
            else:
                obj.shipping_address = self.model._meta.get_field(
                'shipping_address').rel.to.objects.create(**shipping_address)
                obj.save()
        return obj

    def update(self, **kwargs):
        fields = self.model._meta.get_all_field_names()
        kwargs = dict([(x, kwargs[x]) for x in fields if x in kwargs])
        kwargs = self.concat_fields(**kwargs)
        return super(WPQuerySet, self).update(**kwargs)

    def concat_fields(self, **kwargs):
        """
        Makes sure all CharField will not receive None or a string longer then 
        max_length set for the field.
        """
        for key in kwargs:
            val = kwargs.get(key)
            field = self.model._meta.get_field(key)
            if isinstance(field, models.CharField):
                if val is None:
                    val = ''
                else:
                    kwargs.update({key: val[:field.max_length]})
        return kwargs

    def filter(self, *args, **kwargs):
        if not 'deleted' in kwargs:
            kwargs['deleted'] = False
        return super(WPQuerySet, self).filter(*args, **kwargs)


class WPManager(models.Manager):

    def create_revive(self, *args, **kwargs):
        return self.get_query_set().create_revive(*args, **kwargs)

    def get_query_set(self):
        return WPQuerySet(self.model, using=self._db)


class WPBaseModel(models.Model):
    deleted = models.BooleanField(default=False)
    
    objects = WPManager()
    
    def delete(self, *args, **kwargs):
        try:
            db_delete = kwargs.pop('db_delete')
        except KeyError:
            db_delete = not WEPAY_RETAIN_RECORDS
        if db_delete:
            super(WPBaseModel, self).delete(*args, **kwargs)
        else:
            self.deleted = True
            self.save()

    def update(self, **kwargs):
        fields = self.__class__._meta.get_all_field_names()
        for f in fields:
            if f in kwargs:
                val = kwargs[f]
                field = self.__class__._meta.get_field(f)
                if isinstance(field, models.CharField):
                    if val is None:
                        val = ''
                    else:
                        val = val[:field.max_length]
                elif f == 'shipping_address':
                    if self.shipping_address:
                        val = self.shipping_address.update(**val)
                    else:
                        val = field.rel.to.objects.create(**val)
                setattr(self, f, val)
                self.save()
        return self

    class Meta:
        abstract = True

        

# Concrete Models Below

class WPAddress(WPBaseModel, WPAddressExtra):
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255)
    state = USStateField()
    zip = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name
    
    class Meta(WPAddressExtra.Meta):
        db_table = "django_wepay_address"


class WPUser(WPBaseModel, WPUserFull, WPUserExtra):
    user_id = models.BigIntegerField(primary_key=True)
    access_token = models.CharField(max_length=255)
    user_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    state = models.CharField(max_length=255, choices=USER_STATE_CHOICES)
    
    def __str__(self):
        return self.user_name

    def delete(self, *args, **kwargs):
        for account in self.wpaccount_set.all():
            account.delete(db_delete=kwargs.get('db_delete'))
        super(WPUser, self).delete(*args, **kwargs)
                           
    class Meta(WPUserExtra.Meta):
        db_table = "django_wepay_user"


class WPAccount(WPBaseModel, WPAccountFull, WPAccountExtra):
    account_id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    account_uri = models.URLField(max_length=255)
    payment_limit = MoneyField(null=True)
    verification_state = models.CharField(
        max_length=255, choices=ACCOUNT_STATE_CHOICES)
    type = models.CharField(
        max_length=255, choices = ACCOUNT_TYPE_CHOICES)
    pending_balance = MoneyField(default=0)
    available_balance = MoneyField(default=0)
    user = models.ForeignKey(WPUser)
    verification_uri = models.URLField(max_length=255, blank=True)

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        for preapproval in self.wppreapproval_set.all():
            preapproval.delete(db_delete=kwargs.get('db_delete'))
        for checkout in self.wpcheckout_set.all():
            checkout.delete(db_delete=kwargs.get('db_delete'))
        super(WPAccount, self).delete(*args, **kwargs)

    class Meta(WPAccountExtra.Meta):
        db_table = "django_wepay_account"


class WPPreapproval(WPBaseModel, WPPreapprovalFull, WPPreapprovalExtra):
    preapproval_id = models.BigIntegerField(primary_key=True)
    preapproval_uri = URLField(max_length=255)
    manage_uri = URLField(max_length=255)
    account = models.ForeignKey(WPAccount)
    amount = MoneyField()
    fee_payer = models.CharField(
        max_length=5, default='payer', choices=FEE_PAYER_CHOICES)
    state = models.CharField(max_length=255, choices=PREAPPROVAL_STATE_CHOICES)
    app_fee = MoneyField()
    period = models.CharField(
        max_length=255, choices=PREAPPROVAL_PERIOD_CHOICES, default='once')
    start_time = models.BigIntegerField()
    end_time = models.BigIntegerField()
    payer_email = models.EmailField(max_length=255, blank=True)
    payer_name = models.CharField(max_length=255)
    require_shipping = models.BooleanField(default=False)
    shipping_address = models.ForeignKey(WPAddress, null=True)
    create_time = models.BigIntegerField()

    def __str__(self):
        return self.pk

    class Meta(WPPreapprovalExtra.Meta):
        db_table = "django_wepay_preapproval"


class WPCheckout(WPBaseModel, WPCheckoutFull, WPCheckoutExtra):
    checkout_id = models.BigIntegerField(primary_key=True)
    account = models.ForeignKey(WPAccount)
    state = models.CharField(max_length=255, choices=CHECKOUT_STATE_CHOICES)
    amount = MoneyField()
    fee = MoneyField(null=True)
    gross = MoneyField(null=True)
    app_fee = MoneyField()
    fee_payer = models.CharField(max_length=255, choices=FEE_PAYER_CHOICES)
    payer_email = models.EmailField(max_length=255, blank=True)
    payer_name = models.CharField(max_length=255, blank=True)
    cancel_reason = models.CharField(max_length=255, blank=True)
    refund_reason = models.CharField(max_length=255, blank=True)
    auto_capture = models.BooleanField(default=True)
    require_shipping = models.BooleanField(default=False)
    shipping_address = models.ForeignKey(WPAddress, null=True)
    amount_refunded = MoneyField(null=True)
    create_time = models.BigIntegerField()
    preapproval = models.ForeignKey(WPPreapproval, null=True)

    def __str__(self):
        return self.pk

    class Meta(WPCheckoutExtra.Meta):
        db_table = "django_wepay_checkout"


class WPWithdrawal(WPBaseModel, WPWithdrawalFull, WPWithdrawalExtra):
    withdrawal_id = models.BigIntegerField(primary_key=True)
    account = models.ForeignKey(WPAccount)
    state = models.CharField(max_length=255, choices=WITHDRAWAL_STATE_CHOICES)
    withdrawal_uri = URLField(max_length=255)
    amount = MoneyField(null=True)
    note = models.CharField(max_length=255)
    recipient_confirmed = models.BooleanField(default=True)
    create_time = models.BigIntegerField()

    def __str__(self):
        return self.pk

    class Meta(WPWithdrawalExtra.Meta):
        db_table = "django_wepay_withdrawal"



