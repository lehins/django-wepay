from djwepay.models import *

__all__ = [
    'WePayApp', 'WePayUser', 'WePayAccount', 'WePayCheckout', 
    'WePayPreapproval', 'WePayWithdrawal', 'WePayCreditCard', 
    'WePaySubscriptionPlan', 'WePaySubscription', 'WePaySubscriptionCharge'
]



class WePayApp(App):
    pass


class WePayUser(User):
    pass


class WePayAccount(Account):    
    pass


class WePayCheckout(Checkout):
    pass


class WePayPreapproval(Preapproval):
    pass


class WePayWithdrawal(Withdrawal):
    pass


class WePayCreditCard(CreditCard):
    pass


class WePaySubscriptionPlan(SubscriptionPlan):
    pass


class WePaySubscription(Subscription):
    pass


class WePaySubscriptionCharge(SubscriptionCharge):
    pass
