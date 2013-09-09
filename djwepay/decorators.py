from django.core.cache import cache
from django.conf import settings

from djwepay.utils import make_batch_key

CACHE_BATCH_TIMEOUT = getattr(settings, 'WEPAY_CACHE_BATCH_TIMEOUT', None)

class batchable(object):
    def __init__(self, func):
        self._func = func

    def __get__(self, obj, type=None):
        return self.__class__(self._func.__get__(obj, type))

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

    def batch(self, batch_id, reference_id=None, parameters=((), {})):
        args, kwargs = parameters
        call = self._func(*args, batch_mode=True, **kwargs)
        if not reference_id is None:
            call['reference_id'] = None
        batch_key = make_batch_key(batch_id)
        calls = cache.get(batch_key, [])
        calls.append(call)
        cache.set(batch_key, calls, CACHE_BATCH_TIMEOUT)
        return call
