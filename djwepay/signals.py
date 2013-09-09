from django.dispatch import Signal

__all__ = ['ipn_processed', 'state_changed']

ipn_processed = Signal(providing_args=['instance'])

state_changed = Signal(providing_args=['instance', 'previous_state'])
