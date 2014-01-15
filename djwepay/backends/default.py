import time, logging
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache

from djwepay.utils import make_batch_key, make_callback_key
from wepay import WePay as PythonWePay
from wepay import calls
from wepay.exceptions import WePayError


__all__ = ['WePay']

DEBUG = getattr(settings, 'WEPAY_DEBUG', getattr(settings, 'DEBUG'))

THROTTLE_PROTECT = getattr(settings, 'WEPAY_THROTTLE_PROTECT', False)
THROTTLE_CALL_LIMIT = getattr(settings, 'WEPAY_THROTTLE_CALL_LIMIT', 30)
THROTTLE_TIMEOUT = getattr(settings, 'WEPAY_THROTTLE_TIMEOUT', 10)
THROTTLE_CALL_KEY = getattr(settings, 'WEPAY_THROTTLE_CALL_KEY', 'wepay-throttle-call')
BLOCKING_KEY = THROTTLE_CALL_KEY + '-blocked'
DOMAIN = getattr(settings, 'WEPAY_DOMAIN', None)

BATCH_CALLS_CACHE = {}
BATCH_CALLBACKS = {}

class Call(calls.base.Call):

    def make_call(self, func, params, extra_kwargs):
        callback = extra_kwargs.pop('callback', None)
        if extra_kwargs.get('batch_mode', False):
            batch_key = make_batch_key(extra_kwargs.pop('batch_id'))
            reference_id = extra_kwargs.get('batch_reference_id', None)
            call = super(Call, self).make_call(func, params, extra_kwargs)
            if not callback is None and callable(callback):
                # put callback in the cache
                assert not reference_id is None, \
                    "'batch_reference_id' is required when 'callback' is provided"
                callbacks = BATCH_CALLBACKS.get(batch_key, {})
                callbacks[reference_id] = callback
                BATCH_CALLBACKS[batch_key] = callbacks
            # put the actual call in the cache
            calls = BATCH_CALLS_CACHE.get(batch_key, [])
            calls.append(call)
            BATCH_CALLS_CACHE[batch_key] = calls
            return None
        else:
            response = super(Call, self).make_call(func, params, extra_kwargs)
            processed = None
            if not callback is None and callable(callback):
                processed = callback(response)
            return (processed, response)

class OAuth2(Call, calls.OAuth2):

    def authorize(self, cleint_id, redirect_uri, scope, **kwargs):
        return super(OAuth2, self).authorize(
            cleint_id, self.api.get_full_uri(redirect_uri), scope, **kwargs)
    
    def token(self, *args, **kwargs):
        self.api.complete_uri('redirect_uri', kwargs)
        self.api.complete_uri('callback_uri', kwargs)
        return super(OAuth2, self).token(*args, **kwargs)

class App(Call, calls.App):
    pass

class User(Call, calls.User):
    def modify(self, *args, **kwargs):
        self.api.complete_uri('callback_uri', kwargs)
        return super(User, self).modify(*args, **kwargs)

    def register(self, *args, **kwargs):
        self.api.complete_uri('redirect_uri', kwargs)
        self.api.complete_uri('callback_uri', kwargs)
        return super(User, self).register(*args, **kwargs)

class Account(Call, calls.Account):
    def create(self, *args, **kwargs):
        self.api.complete_uri('image_uri', kwargs)
        self.api.complete_uri('callback_uri', kwargs)
        return super(Account, self).create(*args, **kwargs)

    def modify(self, *args, **kwargs):
        self.api.complete_uri('image_uri', kwargs)
        self.api.complete_uri('callback_uri', kwargs)
        return super(Account, self).modify(*args, **kwargs)

    def get_update_uri(self, *args, **kwargs):
        self.api.complete_uri('redirect_uri', kwargs)
        return super(Account, self).get_update_uri(*args, **kwargs)

class Checkout(Call, calls.Checkout):
    
    def create(self, *args, **kwargs):
        self.api.complete_uri('redirect_uri', kwargs)
        self.api.complete_uri('callback_uri', kwargs)
        self.api.complete_uri('fallback_uri', kwargs)
        return super(Checkout, self).create(*args, **kwargs)

    def modify(self, *args, **kwargs):
        self.api.complete_uri('callback_uri', kwargs)
        return super(Checkout, self).modify(*args, **kwargs)


class Preapproval(Call, calls.Preapproval):
    
    def create(self, *args, **kwargs):
        self.api.complete_uri('redirect_uri', kwargs)
        self.api.complete_uri('callback_uri', kwargs)
        self.api.complete_uri('fallback_uri', kwargs)
        return super(Preapproval, self).create(*args, **kwargs)

    def modify(self, *args, **kwargs):
        self.api.complete_uri('callback_uri', kwargs)
        return super(Preapproval, self).modify(*args, **kwargs)

class Withdrawal(Call, calls.Withdrawal):
    
    def create(self, *args, **kwargs):
        self.api.complete_uri('redirect_uri', kwargs)
        self.api.complete_uri('callback_uri', kwargs)
        self.api.complete_uri('fallback_uri', kwargs)
        return super(Withdrawal, self).create(*args, **kwargs)

    def modify(self, *args, **kwargs):
        self.api.complete_uri('callback_uri', kwargs)
        return super(Withdrawal, self).modify(*args, **kwargs)

class CreditCard(Call, calls.CreditCard):
    pass

class SubscriptionPlan(Call, calls.SubscriptionPlan):
    
    def create(self, *args, **kwargs):
        self.api.complete_uri('callback_uri', kwargs)
        return super(SubscriptionPlan, self).create(*args, **kwargs)

    def modify(self, *args, **kwargs):
        self.api.complete_uri('callback_uri', kwargs)
        return super(SubscriptionPlan, self).modify(*args, **kwargs)


class Subscription(Call, calls.Subscription):
    
    def create(self, *args, **kwargs):
        self.api.complete_uri('redirect_uri', kwargs)
        self.api.complete_uri('callback_uri', kwargs)
        return super(Subscription, self).create(*args, **kwargs)

    def modify(self, *args, **kwargs):
        self.api.complete_uri('redirect_uri', kwargs)
        self.api.complete_uri('callback_uri', kwargs)
        return super(Subscription, self).modify(*args, **kwargs)

class SubscriptionCharge(Call, calls.SubscriptionCharge):
    pass

class Batch(Call, calls.Batch):

    def process_calls(self, batch_key, calls):
        """Checks if there are any callbacks associated with calls'
        reference_id in cache. Invokes if such present.

        """
        processed_calls = []
        for call in calls:
            reference_id = call.get('reference_id', None)
            response = call['response']
            processed = None
            if 'error' in response:
                call['error'] = WePayError(response['error'], 
                                           response['error_description'], 
                                           response['error_code'])
            elif not reference_id is None:
                callback_key = make_callback_key(batch_key, reference_id)
                callback = cache.get(callback_key, None)
                if not callback is None and callable(callback):
                    processed = callback(response)
            call['processed'] = processed
            processed_calls.append(call)
        return processed_calls

    
    def create(self, batch_id, **kwargs):
        """Retrieves calls from cache, sequentially send /batch/create API calls
        in chunks of up to 50 and then processes any callbacks set.

        """
        batch_key = make_batch_key(batch_id)
        calls = BATCH_CALLS_CACHE.get(batch_key)
        calls_response = []
        while calls:
            cur_calls = calls[:50]
            response = super(Batch, self).create(calls=cur_calls, **kwargs)[1]
            calls_response.extend(response['calls'])
            calls = calls[50:]
        response = (None, {'calls': self.process_calls(batch_key, calls_response)})
        self.del_calls(batch_id)
        return response

    def del_calls(self, batch_id):
        batch_key = make_batch_key(batch_id)
        try:
            del BATCH_CALLBACKS[batch_key]
        except KeyError: pass
        try:
            del BATCH_CALLS_CACHE[batch_key]
        except KeyError: pass

    def get_calls(self, batch_id):
        return BATCH_CALLS_CACHE.get(make_batch_key(batch_id))

    def set_calls(self, batch_id, calls):
        BATCH_CALLS_CACHE[make_batch_key(batch_id)] = calls


class WePay(PythonWePay):
    
    supported_calls = [
        OAuth2, App, User, Account, Checkout, Preapproval, Withdrawal, CreditCard,
        SubscriptionPlan, Subscription, SubscriptionCharge, Batch
    ]

    def __init__(self, **kwargs):
        domain = DOMAIN
        if domain is None:
            domain = str(Site.objects.get_current())
        self.site_uri = "https://%s" % domain
        super(WePay, self).__init__(**kwargs)

    def _log_error(self, error, uri, params):
        logger = logging.getLogger('djwepay.api.error')
        logger.error("\nCall: '%s' with params: '%s' produced an error: '%s'"
                           "\n%s" % (uri, params, error, '='*70))
        
    def _log_debug(self, uri, params, response):
        logger = logging.getLogger('djwepay.api.debug')
        logger.debug(
            "\nCall: '%s' was placed with params: '%s' and received a response: "
            "'%s'\n%s" % (uri, params, response, '='*70))

    def _call_protected(self, uri, **kwargs):
        blocked = cache.add(BLOCKING_KEY, True)
        if not blocked:
            time.sleep(1)
            return self._call_protected(uri, **kwargs)
        now = int(time.time())
        unexpired_timestamp = now - THROTTLE_TIMEOUT
        unexpired_calls = [x for x in cache.get(THROTTLE_CALL_KEY, [])
                           if x >= unexpired_timestamp]
        if len(unexpired_calls) >= THROTTLE_CALL_LIMIT:
            cache.delete(BLOCKING_KEY)
            sleep_time = THROTTLE_TIMEOUT + unexpired_calls[0] - now + 1
            time.sleep(sleep_time)
            return self._call_protected(uri, **kwargs)
        else:
            unexpired_calls.append(now)
            cache.set(
                THROTTLE_CALL_KEY, unexpired_calls, THROTTLE_TIMEOUT)
            cache.delete(BLOCKING_KEY)
            return super(WePay, self).call(uri, **kwargs)

    def call(self, uri, **kwargs):
        try:
            if THROTTLE_PROTECT:
                response = self._call_protected(uri, **kwargs)
            else:
                response = super(WePay, self).call(uri, **kwargs)
        except WePayError, e:
            self._log_error(e, uri, kwargs.get('params', {}))
            raise
        if DEBUG:
            self._log_debug(uri, kwargs.get('params', {}), response)
        return response

    def get_full_uri(self, uri):
        """
        Used to build callback uri's. Make sure you have SITE_FULL_URL in 
        settings or Site app enabled.
        :param str last part of url
        """
        return '%s%s' % (self.site_uri, uri)

    def get_login_uri(self):
        """
        Returns WePay login url. Better place for users then account uri, 
        less confusing.
        """
        uri_list = self.browser_endpoint.split('/')[:-1]
        uri_list.append('login')
        return '/'.join(uri_list)

    def complete_uri(self, keyword, kwargs):
        """Converts to full uri and updates kwargs"""
        if keyword in kwargs:
            uri = self.get_full_uri(kwargs[keyword])
            kwargs[keyword] = uri
            return uri
        return None
   


