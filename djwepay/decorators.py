from django.core.cache import cache
from django.conf import settings

from djwepay.utils import make_batch_key

__all__ = ['batchable', 'cached_property']

CACHE_BATCH_TIMEOUT = getattr(settings, 'WEPAY_CACHE_BATCH_TIMEOUT', None)

class batchable(object):
    def __init__(self, func):
        self._func = func

    def __get__(self, obj, type=None):
        return self.__class__(self._func.__get__(obj, type))

    def __call__(self, *args, **kwargs):
        kwargs.pop('batch_mode', None)
        return self._func(*args, **kwargs)

    def batch(self, batch_id, reference_id=None, kwargs={}):
        kwargs.pop('batch_mode', None)
        call = self._func(batch_mode=True, **kwargs)
        if not reference_id is None:
            call['reference_id'] = None
        batch_key = make_batch_key(batch_id)
        calls = cache.get(batch_key, [])
        calls.append(call)
        cache.set(batch_key, calls, CACHE_BATCH_TIMEOUT)
        return call

class cached_property(object):
    def __init__(self, fget):
        self.fget = fget
        self.__doc__ = fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__
        self._key = "_%s" % fget.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = getattr(obj, self._key, None)
        if value is None:
            value = self.fget(obj)
            setattr(obj, self._key, value)
        return value

    def __set__(self, obj, value):
        setattr(obj, self._key, value)
