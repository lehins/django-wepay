from django.core.cache import cache
from django.conf import settings

__all__ = ['cached_property']


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
