import time, logging, warnings
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache

from djwepay.decorators import batchable, CACHE_BATCH_TIMEOUT
from djwepay.utils import make_batch_key
from wepay import WePay as PythonWePay
from wepay.exceptions import WePayError


__all__ = ['WePay']

DEBUG = getattr(settings, 'WEPAY_DEBUG', False)

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
        super(WePay, self).__init__(production=self._app.production, 
                                    access_token=self._app.access_token, timeout=45)

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

   
    def oauth2_authorize(self, **kwargs):
        redirect_uri = kwargs.pop('redirect_uri')
        return super(WePay, self).oauth2_authorize(
            self._app.client_id, redirect_uri, DEFAULT_SCOPE, **kwargs)

    @batchable
    def oauth2_token(self, **kwargs):
        redirect_uri = kwargs.pop('redirect_uri')
        code = kwargs.pop('code')
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
    def account(self, **kwargs):
        return super(WePay, self).account(**kwargs)

    @batchable
    def account_find(self, **kwargs):
        return super(WePay, self).account_find(**kwargs)

    @batchable
    def account_create(self, **kwargs):
        name = kwargs.pop('name')
        description = kwargs.pop('description')
        return super(WePay, self).account_create(
            name, description, **kwargs)

    @batchable
    def account_modify(self, **kwargs):
        account_id = kwargs.pop('account_id')
        return super(WePay, self).account_modify(account_id, **kwargs)

    @batchable
    def account_delete(self, **kwargs):
        account_id = kwargs.pop('account_id')
        return super(WePay, self).account_delete(account_id, **kwargs)

    @batchable
    def account_balance(self, **kwargs):
        account_id = kwargs.pop('account_id')
        return super(WePay, self).account_balance(account_id, **kwargs)
        
    @batchable
    def account_add_bank(self, **kwargs):
        account_id = kwargs.pop('account_id')
        return super(WePay, self).account_add_bank(account_id, **kwargs)
        
    @batchable
    def account_set_tax(self, **kwargs):
        account_id = kwargs.pop('account_id')
        taxes = kwargs.pop('taxes')
        return super(WePay, self).account_set_tax(account_id, taxes, **kwargs)

    @batchable
    def account_get_tax(self, **kwargs):
        account_id = kwargs.pop('account_id')
        return super(WePay, self).account_get_tax(account_id, **kwargs)


    @batchable
    def checkout(self, **kwargs):
        checkout_id = kwargs.pop('checkout_id')
        return super(WePay, self).checkout(checkout_id, **kwargs)

    @batchable
    def checkout_find(self, **kwargs):
        account_id = kwargs.pop('account_id')
        return super(WePay, self).checkout_find(account_id, **kwargs)

    @batchable
    def checkout_create(self, **kwargs):
        account_id = kwargs.pop('account_id')
        short_description = kwargs.pop('short_description')
        type = kwargs.pop('type')
        amount = kwargs.pop('amount')
        return super(WePay, self).checkout_create(
            account_id, short_description, type, amount, **kwargs)

    @batchable
    def checkout_cancel(self, **kwargs):
        checkout_id = kwargs.pop('checkout_id')
        cancel_reason = kwargs.pop('cancel_reason')
        return super(WePay, self).checkout_cancel(
            checkout_id, cancel_reason, **kwargs)

    @batchable
    def checkout_refund(self, **kwargs):
        checkout_id = kwargs.pop('checkout_id')
        refund_reason = kwargs.pop('refund_reason')
        return super(WePay, self).checkout_refund(
            checkout_id, refund_reason, **kwargs)

    @batchable
    def checkout_capture(self, **kwargs):
        checkout_id = kwargs.pop('checkout_id')
        return super(WePay, self).checkout_capture(checkout_id, **kwargs)

    @batchable
    def checkout_modify(self, **kwargs):
        checkout_id = kwargs.pop('checkout_id')
        return super(WePay, self).checkout_modify(checkout_id, **kwargs)


    @batchable
    def preapproval(self, **kwargs):
        preapproval_id = kwargs.pop('preapproval_id')
        return super(WePay, self).preapproval(preapproval_id, **kwargs)

    @batchable
    def preapproval_find(self, **kwargs):
        return super(WePay, self).preapproval_find(**kwargs)

    @batchable
    def preapproval_create(self, **kwargs):
        short_description = kwargs.pop('short_description')
        period = kwargs.pop('period')
        return super(WePay, self).preapproval_create(
            short_description, period, **kwargs)

    @batchable
    def preapproval_cancel(self, **kwargs):
        preapproval_id = kwargs.pop('preapproval_id')
        return super(WePay, self).preapproval_cancel(preapproval_id, **kwargs)

    @batchable
    def preapproval_modify(self, **kwargs):
        preapproval_id = kwargs.pop('preapproval_id')
        return super(WePay, self).preapproval_modify(preapproval_id, **kwargs)


    @batchable
    def withdrawal(self, **kwargs):
        withdrawal_id = kwargs.pop('withdrawal_id')
        return super(WePay, self).withdrawal(withdrawal_id, **kwargs)

    @batchable
    def withdrawal_find(self, **kwargs):
        account_id = kwargs.pop('account_id')
        return super(WePay, self).withdrawal_find(account_id, **kwargs)

    @batchable
    def withdrawal_create(self, **kwargs):
        account_id = kwargs.pop('account_id')
        return super(WePay, self).withdrawal_create(account_id, **kwargs)

    @batchable
    def withdrawal_modify(self, **kwargs):
        withdrawal_id = kwargs.pop('withdrawal_id')
        return super(WePay, self).withdrawal_modify(withdrawal_id, **kwargs)


    @batchable
    def credit_card(self, **kwargs):
        credit_card_id = kwargs.pop('credit_card_id')
        return super(WePay, self).credit_card(
            self._app.client_id, self._app.client_secret, credit_card_id, **kwargs)

    @batchable
    def credit_card_create(self, *args, **kwargs):
        return super(WePay, self).credit_card_create(
            self._app.client_id, *args, **kwargs)

    @batchable
    def credit_card_authorize(self, **kwargs):
        credit_card_id = kwargs.pop('credit_card_id')
        return super(WePay, self).credit_card_authorize(
            self._app.client_id, self._app.client_secret, credit_card_id, **kwargs)

    @batchable
    def credit_card_find(self, **kwargs):
        return super(WePay, self).credit_card_find(
            self._app.client_id, self._app.client_secret, **kwargs)

    @batchable
    def credit_card_delete(self, **kwargs):
        credit_card_id = kwargs.pop('credit_card_id')
        return super(WePay, self).credit_card_delete(
            self._app.client_id, self._app.client_secret, credit_card_id, **kwargs)


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
