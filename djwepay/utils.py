from django.conf import settings


CACHE_BATCH_KEY_PREFIX = getattr(
    settings, 'WEPAY_CACHE_BATCH_KEY_PREFIX', 'wepay-cache-batch-key')

def make_batch_key(batch_id):
    return "%s-%s" % (CACHE_BATCH_KEY_PREFIX, batch_id)
