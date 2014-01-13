import importlib
from django.conf import settings


CACHE_BATCH_KEY_PREFIX = getattr(
    settings, 'WEPAY_CACHE_BATCH_KEY_PREFIX', 'wepay-cache-batch-key')

def make_batch_key(batch_id):
    return "%s-%s" % (CACHE_BATCH_KEY_PREFIX, batch_id)

def make_callback_key(batch_key, reference_id):
    return "%s-%s" % (batch_key, reference_id)

def from_string_import(string):
    """
    Returns the attribute from a module, specified by a string.
    """
    module, attrib = string.rsplit('.', 1)
    return getattr(importlib.import_module(module), attrib)
