import time, logging
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.mail import mail_admins

from djwepay.utils import make_batch_key, make_callback_key
from wepay import calls, WePay as PythonWePay
from wepay.exceptions import WePayError, WePayHTTPError, WePayConnectionError
from wepay.utils import cached_property


__all__ = ['WePay']

DEBUG = getattr(settings, 'WEPAY_DEBUG', getattr(settings, 'DEBUG'))

THROTTLE_PROTECT = getattr(settings, 'WEPAY_THROTTLE_PROTECT', True)
THROTTLE_CALL_LIMIT = getattr(settings, 'WEPAY_THROTTLE_CALL_LIMIT', 30)
THROTTLE_TIMEOUT = getattr(settings, 'WEPAY_THROTTLE_TIMEOUT', 10)
THROTTLE_CALL_KEY = getattr(settings, 'WEPAY_THROTTLE_CALL_KEY', 'wepay-throttle-call')
BLOCKING_KEY = THROTTLE_CALL_KEY + '-blocked'
DOMAIN = getattr(settings, 'WEPAY_SITE_DOMAIN', None)
WEPAY_MAIL_ADMIN = getattr(settings, 'WEPAY_MAIL_ADMINS', not DEBUG)


BATCH_CALLS_NUMBER = getattr(settings, 'WEPAY_BATCH_CALLS_NUMBER', 50)
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
            return (None, call) # all api calls are expected to return a tuple
        else:
            response = super(Call, self).make_call(func, params, extra_kwargs)
            processed = None
            if callback is not None and callable(callback):
                processed = callback(response)
            return (processed, response)


    def complete_uris(self, names, kwargs):
        """Converts to full uri and updates kwargs"""
        for name in names:
            if name in kwargs:
                kwargs[name] = self._api.get_full_uri(kwargs[name])




class OAuth2(Call, calls.OAuth2):


    def authorize(self, cleint_id, redirect_uri, scope, **kwargs):
        return super(OAuth2, self).authorize(
            cleint_id, self._api.get_full_uri(redirect_uri), scope, **kwargs)


    def token(self, *args, **kwargs):
        self.complete_uris(['redirect_uri', 'callback_uri'], kwargs)
        return super(OAuth2, self).token(*args, **kwargs)



class App(Call, calls.App):
    pass



class User(Call, calls.User):

    def modify(self, *args, **kwargs):
        self.complete_uris(['callback_uri'], kwargs)
        return super(User, self).modify(*args, **kwargs)


    def register(self, *args, **kwargs):
        self.complete_uris(['redirect_uri', 'callback_uri'], kwargs)
        return super(User, self).register(*args, **kwargs)



class Account(Call, calls.Account):

    def create(self, *args, **kwargs):
        self.complete_uris(['image_uri', 'callback_uri'], kwargs)
        return super(Account, self).create(*args, **kwargs)


    def modify(self, *args, **kwargs):
        self.complete_uris(['image_uri', 'callback_uri'], kwargs)
        return super(Account, self).modify(*args, **kwargs)


    def get_update_uri(self, *args, **kwargs):
        self.complete_uris(['redirect_uri'], kwargs)
        return super(Account, self).get_update_uri(*args, **kwargs)



class Checkout(Call, calls.Checkout):

    def create(self, *args, **kwargs):
        self.complete_uris(
            ['redirect_uri', 'callback_uri', 'fallback_uri'], kwargs)
        return super(Checkout, self).create(*args, **kwargs)


    def modify(self, *args, **kwargs):
        self.complete_uris(['callback_uri'], kwargs)
        return super(Checkout, self).modify(*args, **kwargs)



class Preapproval(Call, calls.Preapproval):

    def create(self, *args, **kwargs):
        self.complete_uris(
            ['redirect_uri', 'callback_uri', 'fallback_uri'], kwargs)
        return super(Preapproval, self).create(*args, **kwargs)


    def modify(self, *args, **kwargs):
        self.complete_uris(['callback_uri'], kwargs)
        return super(Preapproval, self).modify(*args, **kwargs)



class Withdrawal(Call, calls.Withdrawal):

    def create(self, *args, **kwargs):
        self.complete_uris(
            ['redirect_uri', 'callback_uri', 'fallback_uri'], kwargs)
        return super(Withdrawal, self).create(*args, **kwargs)


    def modify(self, *args, **kwargs):
        self.complete_uris(['callback_uri'], kwargs)
        return super(Withdrawal, self).modify(*args, **kwargs)



class CreditCard(Call, calls.CreditCard):
    pass



class SubscriptionPlan(Call, calls.SubscriptionPlan):

    def create(self, *args, **kwargs):
        self.complete_uris(['callback_uri'], kwargs)
        return super(SubscriptionPlan, self).create(*args, **kwargs)


    def modify(self, *args, **kwargs):
        self.complete_uris(['callback_uri'], kwargs)
        return super(SubscriptionPlan, self).modify(*args, **kwargs)



class Subscription(Call, calls.Subscription):

    def create(self, *args, **kwargs):
        self.complete_uris(['redirect_uri', 'callback_uri'], kwargs)
        return super(Subscription, self).create(*args, **kwargs)


    def modify(self, *args, **kwargs):
        self.complete_uris(['redirect_uri', 'callback_uri'], kwargs)
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
                processed = WePayError(response['error'], response['error_code'],
                                       response['error_description'])
            elif not reference_id is None:
                callback_key = make_callback_key(batch_key, reference_id)
                callbacks = BATCH_CALLBACKS.get(batch_key, None)
                callback = None
                if callbacks:
                    callback = callbacks.get(reference_id, None)
                if not callback is None and callable(callback):
                    processed = callback(response)
            call['processed'] = processed
            processed_calls.append(call)
        return processed_calls


    def create(self, batch_id, client_id, client_secret, max_calls=None, **kwargs):
        """Retrieves queued calls, sequentially sends /batch/create API calls in
        chunks of up to `max_calls`, which defaults to
        `WEPAY_BATCH_CALLS_NUMBER` setting and then processes any callbacks
        set. Consider raising `timeout` kwarg, since batch calls can take a
        while, also if you start getting HTTP 404 errors, try lowering
        `max_calls` value.

        """
        max_calls = max_calls or BATCH_CALLS_NUMBER
        assert 0 < max_calls and max_calls <= 50, \
            """max_calls should be a positive number no greater then 50, it is
            also WePay's limitation"""
        batch_key = make_batch_key(batch_id)
        calls = BATCH_CALLS_CACHE.get(batch_key)
        calls_response = []
        while calls:
            cur_calls = calls[:max_calls]
            response = super(Batch, self).create(
                client_id, client_secret, cur_calls, **kwargs)[1]
            calls_response.extend(response['calls'])
            calls = calls[max_calls:]
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

    def __init__(self, **kwargs):
        domain = DOMAIN
        if domain is None:
            domain = Site.objects.get_current().domain
        self.site_uri = "https://%s" % domain
        kwargs['timeout'] = kwargs.get('timeout', 45)
        super(WePay, self).__init__(**kwargs)


    @cached_property
    def oauth2(self):
        return OAuth2(self)
 

    @cached_property
    def app(self):
        return App(self)


    @cached_property
    def user(self):
        return User(self)
        

    @cached_property
    def account(self):
       return Account(self)


    @cached_property
    def checkout(self):
        return Checkout(self)


    @cached_property
    def preapproval(self):
        return Preapproval(self)


    @cached_property
    def withdrawal(self):
        return Withdrawal(self)


    @cached_property
    def credit_card(self):
        return CreditCard(self)


    @cached_property
    def subscription_plan(self):
        return SubscriptionPlan(self)


    @cached_property
    def subscription(self):
       return Subscription(self)


    @cached_property
    def subscription_charge(self):
        return SubscriptionCharge(self)


    @cached_property
    def batch(self):
        return Batch(self)


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
        except (WePayHTTPError, WePayConnectionError) as e:
            self._log_error(e, uri, kwargs.get('params', {}))
            mail_admins(
                "WePayError", """
                There was a problem with making an API call: %s
                Params: %s
                Timeout: %s
                Error received: %s""" % (
                    uri, kwargs.get('params', None), kwargs.get('timeout', None), e),
                fail_silently=not DEBUG
            )
            raise
        if DEBUG:
            self._log_debug(uri, kwargs.get('params', {}), response)
        return response


    def get_full_uri(self, uri):
        """
        Used to build callback uri's. Make sure you have WEPAY_SITE_DOMAIN in
        settings or Site app enabled and configured.
        :param str uri: last part of url
        """
        if uri.startswith('http'):
            return uri
        return '%s%s' % (self.site_uri, uri)


    def get_login_uri(self):
        """
        Returns WePay login url. Just in case if someone needs it.
        """
        return '%s/login' % self.browser_uri

