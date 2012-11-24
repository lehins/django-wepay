from django.dispatch import Signal
from django.core.cache import cache

from django_wepay.settings import WEPAY_IPN_LIMIT

__all__ = ['ipn_received', 'user_deleted', 'checkout_state_changed', 
           'preapproval_state_changed', 'withdrawal_state_changed']

ipn_received = Signal(providing_args=['request', 'instance'])

user_deleted = Signal(providing_args=['user'])

checkout_state_changed = Signal(
    providing_args=['checkout', 'previous_state', 'response'])

preapproval_state_changed = Signal(
    providing_args=['preapproval', 'previous_state', 'response'])

withdrawal_state_changed = Signal(
    providing_args=['withdrawal', 'previous_state', 'response'])

def throttle_ipn_protect(sender, **kwargs):
    key = "django_wepay_ipn_count"
    count = cache.get(key, 0)
    if count >= WEPAY_IPN_LIMIT[0]:
        raise Exception("IPN limit Exceded")
    count+= 1
    cache.set(key, count, timeout=WEPAY_IPN_LIMIT[1])

ipn_received.connect(throttle_ipn_protect)
