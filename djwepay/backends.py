import time
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache

from wepay import WePay as PythonWePay
from djwepay.decorators import batchable, CACHE_BATCH_TIMEOUT
from djwepay.utils import make_batch_key


__all__ = ['WePay']

# default is full access
DEFAULT_SCOPE = getattr(
    settings, 'WEPAY_DEFAULT_SCOPE', "manage_accounts,collect_payments,"
    "view_balance,view_user,preapprove_payments,send_money")

THROTTLE_PROTECT = getattr(settings, 'WEPAY_THROTTLE_PROTECT', False)
THROTTLE_CALL_LIMIT = getattr(settings, 'WEPAY_THROTTLE_CALL_LIMIT', 30)
THROTTLE_TIMEOUT = getattr(settings, 'WEPAY_THROTTLE_TIMEOUT', 10)
THROTTLE_CALL_KEY = 'wepay-throttle-call'
BLOCKING_KEY = THROTTLE_CALL_KEY + '-blocked'

class WePay(PythonWePay):

    def __init__(self, app):
        self._app = app
        self.site_uri = "https://%s" % str(Site.objects.get_current())
        super(WePay, self).__init__(
            production=self._app.production, access_token=self._app.access_token)

    def call(self, *args, **kwargs):
        if THROTTLE_PROTECT:
            # TODO add a logger and a notifier
            blocked = cache.add(BLOCKING_KEY, True)
            if not blocked:
                time.sleep(1)
                return self.call(*args, **kwargs)
            now = int(time.time())
            unexpired_timestamp = now - THROTTLE_TIMEOUT
            unexpired_calls = [x for x in cache.get(THROTTLE_CALL_KEY, [])
                               if x >= unexpired_timestamp]
            if len(unexpired_calls) >= THROTTLE_CALL_LIMIT:
                cache.delete(BLOCKING_KEY)
                sleep_time = THROTTLE_TIMEOUT + unexpired_calls[0] - now + 1
                time.sleep(sleep_time)
                return self.call(*args, **kwargs)
            else:
                unexpired_calls.append(now)
                cache.set(
                    THROTTLE_CALL_KEY, unexpired_calls, THROTTLE_TIMEOUT)
                cache.delete(BLOCKING_KEY)
                return super(WePay, self).call(*args, **kwargs)
        else:
            return super(WePay, self).call(*args, **kwargs)

    def get_full_uri(self, uri):
        """
        Used to builed callback uri's. Make sure you have SITE_FULL_URL in 
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

   
    def oauth2_authorize(self, redirect_uri, **kwargs):
        return super(WePay, self).oauth2_authorize(
            self._app.client_id, redirect_uri, DEFAULT_SCOPE, **kwargs)

    @batchable
    def oauth2_token(self, redirect_uri, code, **kwargs):
        return super(WePay, self).oauth2_token(
            self._app.client_id, redirect_uri, self._app.client_secret, code, 
            **kwargs)


    @batchable
    def app(self, **kwargs):
        return super(WePay, self).app(
            self._app.client_id, self._app.client_secret, **kwargs)

    @batchable
    def app_modify(self, **kwargs):
        return super(WePay, self).app_modify(
            self._app.client_id, self._app.client_secret, **kwargs)


    @batchable
    def user(self, **kwargs):
        return super(WePay, self).user(**kwargs)

    @batchable
    def user_modify(self, **kwargs):
        return super(WePay, self).user_modify(**kwargs)


    @batchable
    def account(self, *args, **kwargs):
        return super(WePay, self).account(*args, **kwargs)

    @batchable
    def account_find(self, **kwargs):
        return super(WePay, self).account_find(**kwargs)

    @batchable
    def account_create(self, *args, **kwargs):
        return super(WePay, self).account_create(*args, **kwargs)

    @batchable
    def account_modify(self, *args, **kwargs):
        return super(WePay, self).account_modify(*args, **kwargs)

    @batchable
    def account_delete(self, *args, **kwargs):
        return super(WePay, self).account_delete(*args, **kwargs)

    @batchable
    def account_balance(self, *args, **kwargs):
        return super(WePay, self).account_balance(*args, **kwargs)
        
    @batchable
    def account_add_bank(self, *args, **kwargs):
        return super(WePay, self).account_add_bank(*args, **kwargs)
        
    @batchable
    def account_set_tax(self, *args, **kwargs):
        return super(WePay, self).account_set_tax(*args, **kwargs)

    @batchable
    def account_get_tax(self, *args, **kwargs):
        return super(WePay, self).account_get_tax(*args, **kwargs)


    @batchable
    def checkout(self, *args, **kwargs):
        return super(WePay, self).checkout(*args, **kwargs)

    @batchable
    def checkout_find(self, *args, **kwargs):
        return super(WePay, self).checkout_find(*args, **kwargs)

    @batchable
    def checkout_create(self, *args, **kwargs):
        return super(WePay, self).checkout_create(*args, **kwargs)

    @batchable
    def checkout_cancel(self, *args, **kwargs):
        return super(WePay, self).checkout_cancel(*args, **kwargs)

    @batchable
    def checkout_refund(self, *args, **kwargs):
        return super(WePay, self).checkout_refund(*args, **kwargs)

    @batchable
    def checkout_capture(self, *args, **kwargs):
        return super(WePay, self).checkout_capture(*args, **kwargs)

    @batchable
    def checkout_modify(self, *args, **kwargs):
        return super(WePay, self).checkout_modify(*args, **kwargs)


    @batchable
    def preapproval(self, *args, **kwargs):
        return super(WePay, self).preapproval(*args, **kwargs)

    @batchable
    def preapproval_find(self, **kwargs):
        return super(WePay, self).preapproval_find(**kwargs)

    @batchable
    def preapproval_create(self, *args, **kwargs):
        return super(WePay, self).preapproval_create(*args, **kwargs)

    @batchable
    def preapproval_cancel(self, *args, **kwargs):
        return super(WePay, self).preapproval_cancel(*args, **kwargs)

    @batchable
    def preapproval_modify(self, *args, **kwargs):
        return super(WePay, self).preapproval_modify(*args, **kwargs)


    @batchable
    def withdrawal(self, *args, **kwargs):
        return super(WePay, self).withdrawal(*args, **kwargs)

    @batchable
    def withdrawal_find(self, *args, **kwargs):
        return super(WePay, self).withdrawal_find(*args, **kwargs)

    @batchable
    def withdrawal_create(self, *args, **kwargs):
        return super(WePay, self).withdrawal_create(*args, **kwargs)

    @batchable
    def withdrawal_modify(self, *args, **kwargs):
        return super(WePay, self).withdrawal_modify(*args, **kwargs)


    @batchable
    def credit_card(self, *args, **kwargs):
        return super(WePay, self).credit_card(
            self._app.client_id, self._app.client_secret, *args, **kwargs)

    @batchable
    def credit_card_create(self, *args, **kwargs):
        return super(WePay, self).credit_card_create(
            self._app.client_id, *args, **kwargs)

    @batchable
    def credit_card_authorize(self, *args, **kwargs):
        return super(WePay, self).credit_card_authorize(
            self._app.client_id, self._app.client_secret, *args, **kwargs)

    @batchable
    def credit_card_find(self, **kwargs):
        return super(WePay, self).credit_card_find(
            self._app.client_id, self._app.client_secret, **kwargs)

    @batchable
    def credit_card_delete(self, *args, **kwargs):
        return super(WePay, self).credit_card_delete(
            self._app.client_id, self._app.client_secret, *args, **kwargs)


    def batch_create(self, batch_id, **kwargs):
        batch_key = make_batch_key(batch_id)
        calls = cache.get(batch_key)
        calls_response = []
        while calls:
            cur_calls = calls[:50]
            cache.set(batch_key, calls[50:], CACHE_BATCH_TIMEOUT)
            response = super(WePay, self).batch_create(
                self._app.client_id, self._app.client_secret, calls, **kwargs)
            calls_response.extend(response['calls'])
            calls = cache.get(batch_key)            
        return {'calls': calls_response}

    def batch_clear(self, batch_id):
        cache.delete(make_batch_key(batch_id))

    def batch_get_calls(self, batch_id):
        return cache.get(make_batch_key(batch_id))

    def batch_set_calls(self, batch_id, calls):
        cache.set(make_batch_key(batch_id), calls, CACHE_BATCH_TIMEOUT)
