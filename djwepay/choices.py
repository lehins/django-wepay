USER_STATE_CHOICES = (
    ('registered', u"Registered"),
    ('pending', u"Pending"),
)


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

CREDIT_CARD_STATE_CHOICES = (
    ('new', u"New"),
    ('authorized', u"Authorized"),
    ('expired', u"Expired"),
    ('deleted', u"Deleted"),
    ('invalid', u"Invalid"),
)

