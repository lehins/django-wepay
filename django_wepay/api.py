from django.core.urlresolvers import reverse
from django.forms.models import model_to_dict
from django.contrib.sites.models import Site
from django.db.models import Q

from wepay import WePay
from wepay.exceptions import WePayError

from django_wepay import settings
from django_wepay.models import *
from django_wepay.signals import preapproval_state_changed, checkout_state_changed,\
    withdrawal_state_changed

from decimal import Decimal
import urllib, urllib2, json, decimal, copy

__all__ = ['DjangoWePay', 'WePayError']

class DjangoWePay(WePay):
    """
    A django client for the WePay API. All configuration is pulled from settings
    module
    """
    def __init__(self, access_token=None, user=None, account=None, 
                 extended_models={}):
        """
        In order for API calls to work access_token is necessary, so having 
        all objects cached locally we can use either one to decide on an 
        access_token.
        In multiple calls you can define differrent access_tokens for the call
        as an option, if you don't default one will be used in the order of 
        precedence:
        None of the three parameters are required. Although if some, all or 
        none are supplied the order of precedence is following: 
        user, account, access_token, application access_token
        :param str access_token: 
        :param WPUser user: 
        :param WPAccount account: 
        """
        self.client_id = settings.WEPAY_CLIENT_ID
        self.client_secret = settings.WEPAY_CLIENT_SECRET
        self.account_id = settings.WEPAY_ACCOUNT_ID
        self.site_uri = settings.SITE_FULL_URL
        if not self.site_uri:
            self.site_uri = ''.join(["https://", str(Site.objects.get_current())])
        self.defaults = settings.WEPAY_OBJECTS_DEFAULTS
        self.user = user
        if user:
            access_token = user.access_token
        elif account:
            self.user = account.user
            access_token = account.user.access_token
        elif not access_token:
            access_token = settings.WEPAY_ACCESS_TOKEN
        self.mWPUser = extended_models.get('WPUser', WPUser)
        self.mWPAccount = extended_models.get('WPAccount', WPAccount)
        self.mWPCheckout = extended_models.get('WPCheckout', WPCheckout)
        self.mWPPreapproval = extended_models.get('WPPreapproval', WPPreapproval)
        self.mWPWithdrawal = extended_models.get('WPWithdrawal', WPWithdrawal)
        super(DjangoWePay, self).__init__(production=settings.WEPAY_PRODUCTION, 
                                          access_token=access_token)
    
    def _format_uri(self, uri):
        """
        Used to builed callback uri's. Make sure you have SITE_FULL_URL in 
        settings or Site app enabled.
        :param str last part of url
        """
        return ''.join([self.site_uri, uri])

    def get_login_uri(self):
        """
        Returns WePay login url. Better place for users then account uri, 
        less confusing.
        """
        uri = self.browser_endpoint
        uri_list = uri.split('/')[:-1]
        uri_list.append('login')
        return '/'.join(uri_list)

    def call(self, uri, params=None):
        """
        Same call function as python API. Except header is changed to
        Django WePay SDK and no error on empty params.
        Basically this is the place for all api calls.
        :param str uri API uri to call
        :param dict params to include in the call
        :param str access_token to use for the call, mostly omitted.
        """
        headers = {'Content-Type' : 'application/json', 
                   'User-Agent' : 'Django WePay SDK'}
        url = self.api_endpoint + uri
        
        headers['Authorization'] = 'Bearer ' + self.access_token
            
        if params:
            for key, value in params.iteritems():
                if isinstance(params[key], decimal.Decimal):
                    params[key] = float(params[key])
            params = json.dumps(params)

        request = urllib2.Request(url, params, headers)
        try:
            response = urllib2.urlopen(request).read()
            return json.loads(response)
        except urllib2.HTTPError as e:
            response = json.loads(e.read())
            print response['error'] + " - " + response['error_description']
            raise WePayError(response['error'], response['error_description'])
            
    def get_authorization_url(self, redirect_uri, client_id=None, scope=None,
                              state=None, user_name=None, user_email=None):
        """
        API doc at: https://www.wepay.com/developer/reference/oauth2
        This is the endpoint that you send the user to so they can grant your 
        application permission to make calls on their behalf. It is not an API call 
        but an actual uri that you send the user to.
        'oauth2/authorize' uri.
        :param str redirect_uri (required) The uri the user will be redirected to 
        after authorization. Must have the same domain as the application.
        :param str client_id The client id issued to the app, found on your 
        application's dashboard.
        :param str scope A comma separated list of permissions. Default pemissions 
        are pulled from settings.py by name WEPAY_DEFAULT_SCOPE 
        :param str state The opaque value the client application uses to maintain 
        state.
        :param str user_namer The user name used to pre-fill the authorization form
        :param str user_email The user email used to pre-fill the authorization form
        """
        if not scope:
            scope = settings.WEPAY_DEFAULT_SCOPE
        if not client_id:
            client_id = self.client_id
        options = {}
        if state:
            options.update({'state': state})
        if user_name:
            options.update({'user_name': user_name})
        if user_email:
            options.update({'user_email': user_email})
        redirect_uri = self._format_uri(redirect_uri)
        return super(DjangoWePay, self).get_authorization_url(
            redirect_uri, client_id=client_id, options=options, scope=scope)

    
    def get_token(self, redirect_uri, code, client_id=None, client_secret=None, 
                  callback_uri=None):
        """
        API doc: https://www.wepay.com/developer/reference/oauth2#token
        :param str redirect_uri (required) The uri the user will be redirected to 
        after authorization. Must be the same as passed in /v2/oauth2/authorize
        :param str code (required) The code returned by /v2/oauth2/authorize
        :param str callback_uri A callback_uri you want to receive IPNs for this 
        user on. 
        """
        if not callback_uri:
            callback_uri = reverse('wepay_ipn_user')
        if not client_id:
            client_id = self.client_id
        if not client_secret:
            client_secret = self.client_secret
        callback_uri = self._format_uri(callback_uri)
        redirect_uri = self._format_uri(redirect_uri)
        params = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'callback_uri': callback_uri,
        }
        return self.call('/oauth2/token', params)

    def user_get(self):
        """
        API doc: https://www.wepay.com/developer/reference/user#lookup
        Return the user associated with access token.
        """
        return self.call('/user')

    def user_create(self, code, redirect_uri, callback_uri=None):
        """
        API doc: https://www.wepay.com/developer/reference/oauth2#authorize
        Creates the user on WePay and locally. If user already in the db as deleted 
        revives him, but none of the other objects associated with user.
        :param str code The code returned by /v2/oauth2/authorize
        :param str redirect_uri The uri the user will be redirected to after 
        authorization. Must be the same as passed in /v2/oauth2/authorize (get_token)
        :param str callback_uri A callback_uri you want to receive IPNs.
        """
        if not callback_uri:
            callback_uri = reverse('wepay_ipn_user')
        callback_uri = self._format_uri(callback_uri)
        oauth2_token_response = self.get_token(
            redirect_uri, code, callback_uri=callback_uri)
        user_id = oauth2_token_response['user_id']
        self.access_token = oauth2_token_response['access_token']
        user_response = self.user_get()
        user_response.update(oauth2_token_response)
        self.user = self.mWPUser.objects.create_revive(**user_response)
        self._handle_users_past_records()
        return self.user

    def _handle_users_past_records(self):
        accounts = self.account_find()
        for account in accounts:
            account = self.account_update_local(
                account['account_id'], response=account)
            self.account_balance_update_local(account)
            preapprovals = self.preapproval_find(account)
            for preapproval in preapprovals:
                preapproval['account'] = account
                self.preapproval_update_local(
                    preapproval['preapproval_id'], response=preapproval)
            checkouts = self.checkout_find(account)
            for checkout in checkouts:
                checkout['account'] = account
                self.checkout_update_local(
                    checkout['checkout_id'], response=checkout)
            withdrawals = self.withdrawal_find(account)
            for withdrawal in withdrawals:
                withdrawal['account'] = account
                self.withdrawal_update_local(
                    withdrawal['withdrawal_id'], response=withdrawal)

    def user_modify(self, callback_uri):
        """
        API doc: https://www.wepay.com/developer/reference/user#modify
        The way to set a callback uri dor the user.
        :param str callback_uri A callback_uri you want to receive IPNs.
        """
        callback_uri = self._format_uri(callback_uri)
        return self.call('/user', params={'callback_uri': callback_uri})

    def account_get(self, account):
        """
        API doc: https://www.wepay.com/developer/reference/account#lookup
        This call allows you to lookup the details of the a payment account 
        on WePay. The payment account must belong to the user associated with 
        the access token used to make the call.
        :param int account The WPAccount instance or account_id you want to look up.
        """
        if isinstance(account, self.mWPAccount):
            account_id = account.pk
        else:
            account_id = account
        return self.call("/account", {'account_id': account_id})

    def account_find(self, name=None, reference_id=None):
        """
        API doc: https://www.wepay.com/developer/reference/account#find
        This call lets you search the accounts of the user associated with the 
        access token used to make the call. You can search by name or reference_id, 
        and the response will be an array of all the matching accounts. If both 
        name and reference_id are blank, this will return an array of all of the 
        user's accounts.
        :param str name The name of the account you are searching for.
        :param str reference_id	The reference ID of the account you are searching 
        for (set by the app in in /account/create or /account/modify).
        """
        params = {}
        if name: params.update({'name': name})
        if reference_id: params.update({'reference_id': reference_id})
        return self.call("/account/find", params=params)

    def account_create(self, name, description, **kwargs):
        """
        API doc: https://www.wepay.com/developer/reference/account#create
        Creates a new payment account for the user associated with the access token
        used to make this call. If reference_id is passed, it MUST be unique for the 
        application/user pair or an error will be returned. NOTE: You cannot create
        an account with the word 'wepay' in it. This is to prevent phishing attacks.
        :param str name	The name of the account you want to create.
        :param str description The description of the account you want to create.
        """
        params = self.defaults.get('account', {})
        params.update({
                'name': name,
                'description': description,
                'theme_object': self.defaults['theme_object'],
                'callback_uri': reverse('wepay_ipn_account')})
        if kwargs:
            params.update(kwargs)
        params.update({'callback_uri': self._format_uri(params['callback_uri'])})
        response = self.call("/account/create", params)
        kwargs = {}
        kwargs.update(params)
        if not self.user:
            try:
                self.user = self.mWPUser.objects.get(access_token=self.access_token)
            except self.mWPUser.DoesNotExist: pass
        kwargs.update(self.account_get(response['account_id']))
        kwargs.update({'user': self.user})
        return self.mWPAccount.objects.create(**kwargs)
        
    def account_delete(self, account):
        """
        API doc: https://www.wepay.com/developer/reference/account#delete
        Deletes the account specified. The use associated with the access token 
        used must have permission to delete the account. An account may not be 
        deleted if it has a balance, pending bills, pending payments, or has 
        ordered a debit card.
        The account will NOT be deleted locally unless db_delete is True, although 
        it will be treated as one.
        :param int account_id The unique ID of the account you want to delete.
        """
        if isinstance(account, self.mWPAccount):
            account_id = account.pk
            account.delete()
        else:
            account_id = account
            try:
                self.mWPAccount.objects.get(account_id=account_id).delete()
            except self.mWPAccount.DoesNotExist: pass # nothing to delete
        return self.call("/account/delete", params={'account_id': account_id})

    def account_modify(self, account, **kwargs):
        """
        API doc: https://www.wepay.com/developer/reference/account#modify
        Updates the specified properties both remotly and locally.
        Account param has to be either WPAccount model instance or an account_id
        :param int or WPAccount account The unique ID of the account you want to 
        modify.
        """
        if isinstance(account, self.mWPAccount):
            account_id = account.pk
        else:
            account_id = account
        params = {'account_id': account_id,
                  'callback_uri': reverse('wepay_ipn_account')}
        if kwargs:
            params.update(kwargs)
        params.update({'callback_uri': self._format_uri(params['callback_uri'])})
        response = self.call("/account/modify", params=params)
        return self.account_update_local(account, response=response)
        
    def account_balance(self, account):
        if isinstance(account, self.mWPAccount):
            account_id = account.pk
        else:
            account_id = account
        return self.call("/account/balance", params={'account_id': account_id})

    def account_set_tax(self, account, taxes):
        if isinstance(account, self.mWPAccount):
            account_id = account.pk
        else:
            account_id = account
        return self.call("/account/set_tax", params={
                'account_id': account_id, 'taxes': taxes})

    def account_get_tax(self, account):
        if isinstance(account, self.mWPAccount):
            account_id = account.pk
        else:
            account_id = account
        return self.call("/account/get_tax", params={'account_id': account_id})

    def account_modify_from_local(self, account):
        params_allowed = ['name', 'description', 'reference_id', 'image_uri',
                          'gaq_domains', 'theme_object', 'call_back_uri']
        account_dict = model_to_dict(account)
        params = dict([(x, account_dict[x]) for x in params_allowed 
                       if x in account_dict])
        return self.account_modify(account.pk, **params)

    def account_update_local(self, account, response=None):
        if isinstance(account, self.mWPAccount):
            account_id = account.pk
        else:
            account_id = account
            try:
                account = self.mWPAccount.objects.get(pk=account_id)
            except self.mWPAccount.DoesNotExist:
                if response:
                    response['user'] = self.user
                    return self.mWPAccount.objects.create_revive(**response)
        if not response:
            response = self.account_get(account_id)
        return account.update(**response)

    def account_balance_update_local(self, account):
        if isinstance(account, self.mWPAccount):
            account_id = account.pk
        else:
            account_id = account
        response = self.account_balance(account_id)
        return self.account_update_local(account, response)


    def preapproval_get(self, preapproval):
        if isinstance(preapproval, self.mWPPreapproval):
            preapproval_id = preapproval.pk
        else:
            preapproval_id = preapproval
        return self.call("/preapproval", params={'preapproval_id': preapproval_id})

    def preapproval_find(self, account, state=None, reference_id=None):
        if isinstance(account, self.mWPAccount):
            account_id = account.pk
        else:
            account_id = account
        params = {'account_id': account_id}
        if state: params.update({'state': state})
        if reference_id: params.update({'reference_id': reference_id})
        return self.call("/preapproval/find", params=params)

    def preapproval_create(self, account, short_description, period, **kwargs):
        """
        -------------------------------------------------------------------------
        TODO: Implement the documented ability:
          App Level Pre-approvals
          If you want to get authorization to send money to any account you can 
          make the /preapproval/create call with your client_id and client_secret 
          instead of the account_id and access_token.
          The preapproval will then be able to authorize payments to any account 
          you have set up for your users.
        """
        if isinstance(account, int):
            account = self.mWPAccount.objects.get(pk=account)
        params = self.defaults.get('preapproval', {})
        params.update({
                'account_id': account.pk,
                'short_description': short_description,
                'period': period,
                'callback_uri': reverse('wepay_ipn_preapproval')})
        if kwargs:
            params.update(kwargs)
        params.update({'callback_uri': self._format_uri(params['callback_uri'])})
        if 'redirect_uri' in params:
            params.update({'redirect_uri': self._format_uri(params['redirect_uri'])})
        response = self.call("/preapproval/create", params=params)
        kwargs = {}
        kwargs.update(params)
        kwargs.update(self.preapproval_get(response['preapproval_id']))
        kwargs.update({'account': account})
        return self.mWPPreapproval.objects.create(**kwargs)

    def preapproval_cancel(self, preapproval):
        if isinstance(preapproval, self.mWPPreapproval):
            preapproval_id = preapproval.pk
        else:
            preapproval_id = preapproval
        response = self.call("/preapproval/cancel", 
                         params={'preapproval_id': preapproval_id})
        return self.preapproval_update_local(preapproval, response=response)

    def preapproval_modify(self, preapproval, callback_uri):
        if isinstance(preapproval, self.mWPPreapproval):
            preapproval_id = preapproval.pk
        else:
            preapproval_id = preapproval
        callback_uri = self._format_uri(callback_uri)
        params = {'preapproval_id': preapproval_id,
                  'callback_uri': callback_uri}
        return self.call("/preapproval/modify", params=params)

    def preapproval_update_local(self, preapproval, response=None):
        if isinstance(preapproval, self.mWPPreapproval):
            preapproval_id = preapproval.pk
        else:
            preapproval_id = preapproval
            try:
                preapproval = self.mWPPreapproval.objects.get(pk=preapproval_id)
            except self.mWPPreapproval.DoesNotExist:
                if response:
                    return self.mWPPreapproval.objects.create_revive(**response)
        if not response:
            response = self.preapproval_get(preapproval_id)
        if preapproval.state != response['state']:
            previous_state = preapproval.state
            preapproval.update(**response)
            preapproval_state_changed.send(
                sender=self.mWPPreapproval, preapproval=preapproval,
                previous_state=previous_state, response=response)
            return preapproval
        return preapproval.update(**response)


    def checkout_get(self, checkout):
        if isinstance(checkout, self.mWPCheckout):
            checkout_id = checkout.pk
        else:
            checkout_id = checkout
        return self.call("/checkout", params={'checkout_id': checkout_id})

    def checkout_find(self, account, **kwargs):
        if isinstance(account, self.mWPAccount):
            account_id = account.pk
        else:
            account_id = account
        params = {'account_id': account_id}
        if kwargs:
            params.update(kwargs)
        return self.call("/checkout/find", params=params)

    def checkout_create(self, account, short_description, type, amount, **kwargs):
        if isinstance(account, self.mWPAccount):
            account_id = account.pk
        else:
            account_id = account
            account = self.mWPAccount.objects.get(pk=account_id)
        params = self.defaults.get('checkout', {})
        params.update({
                'account_id': account_id,
                'short_description': short_description,
                'type': type,
                'amount': amount,
                'callback_uri': reverse('wepay_ipn_checkout')})
        preapproval = None
        if 'preapproval' in kwargs:
            preapproval = kwargs.pop('preapproval')
            if isinstance(preapproval, self.mWPPreapproval):
                preapproval_id = preapproval.pk
            else:
                preapproval_id = preapproval
                preapproval = self.mWPPreapproval.objects.get(pk=preapproval_id)
            params.update({'preapproval_id': preapproval.preapproval_id})
        if kwargs:
            params.update(kwargs)
        params.update({'callback_uri': self._format_uri(params['callback_uri'])})
        if 'redirect_uri' in params:
            params.update({'redirect_uri': self._format_uri(params['redirect_uri'])})
        response = self.call("/checkout/create", params=params)
        kwargs = {}
        kwargs.update(params)
        kwargs.update(response)
        kwargs.update(self.checkout_get(response['checkout_id']))
        kwargs.update({'account': account})
        if preapproval:
            kwargs.update({'preapproval': preapproval})
            # avoid recreating another instance of the same address for checkout
            if preapproval.shipping_address and 'shipping_address' in kwargs:
                shipping_address = kwargs['shipping_address']
                shipping_address['id'] = preapproval.shipping_address.id
        return self.mWPCheckout.objects.create(**kwargs)
        
    def checkout_cancel(self, checkout, cancel_reason):
        if isinstance(checkout, self.mWPCheckout):
            checkout_id = checkout.pk
        else:
            checkout_id = checkout
        response = self.call("/checkout/cancel", params={
                'checkout_id': checkout_id,
                'cancel_reason': cancel_reason
                })
        return self.checkout_update_local(checkout_id, response=response)

    def checkout_refund(self, checkout, refund_reason, amount=None, app_fee=None):
        if isinstance(checkout, self.mWPCheckout):
            checkout_id = checkout.pk
        else:
            checkout_id = checkout
        params={'checkout_id': checkout_id,
                'refund_reason': refund_reason}
        if amount:
            params.update({'amount': amount})
        if app_fee:
            params.update({'app_fee': app_fee})
        self.call("/checkout/refund", params=params)
        return self.checkout_update_local(checkout_id)

    def checkout_capture(self, checkout):
        if isinstance(checkout, self.mWPCheckout):
            checkout_id = checkout.pk
        else:
            checkout_id = checkout
        response = self.call("/checkout/capture", params={'checkout_id': checkout_id})
        return self.checkout_update_local(checkout, response)

    def checkout_modify(self, checkout, callback_uri):
        if isinstance(checkout, self.mWPCheckout):
            checkout_id = checkout.pk
        else:
            checkout_id = checkout
        callback_uri = self._format_uri(reverse('wepay_ipn_checkout'))
        params = {'checkout_id': checkout_id,
                  'callback_uri': callback_uri}
        return self.call("/checkout/modify", params=params)

    def checkout_update_local(self, checkout, response=None):
        if isinstance(checkout, self.mWPCheckout):
            checkout_id = checkout.pk
        else:
            checkout_id = checkout
            try:
                checkout = self.mWPCheckout.objects.get(pk=checkout_id)
            except self.mWPCheckout.DoesNotExist:
                if response:
                    return self.mWPCheckout.objects.create_revive(**response)
        if not response:
            response = self.checkout_get(checkout_id)
        if checkout.state != response['state']:
            previous_state = checkout.state
            checkout.update(**response)
            checkout_state_changed.send(
                sender=self.mWPCheckout, checkout=checkout, 
                previous_state=previous_state, response=response)
            return checkout
        return checkout.update(**response)

    def checkout_create_from_preapproval(self, preapproval, type, amount=None):
        if isinstance(preapproval, int):
            preapproval = self.mWPPreapproval.objects.get(pk=preapproval)
        if amount is None:
            amount = preapproval.amount
        # description is irrelevant, preapproval description will be used anyways
        return self.checkout_create(
            preapproval.account, 'empty', type, amount, preapproval=preapproval)
    

    def withdrawal_get(self, withdrawal):
        if isinstance(withdrawal, self.mWPWithdrawal):
            withdrawal_id = withdrawal.pk
        else:
            withdrawal_id = withdrawal
        return self.call("/withdrawal", params={'withdrawal_id': withdrawal_id})

    def withdrawal_find(self, account, state=None, limit=None, start=None):
        if isinstance(account, self.mWPAccount):
            account_id = account.pk
        else:
            account_id = account
            account = self.mWPAccount.objects.get(pk=account_id)
        params = {'account_id': account_id}
        if state: params.update({'state': state})
        if limit: params.update({'limit': limit})
        if start: params.update({'start': start})
        return self.call("/withdrawal/find", params=params)

    def withdrawal_create(self, account, **kwargs):
        params = self.defaults.get('withdrawal', {})
        if isinstance(account, self.mWPAccount):
            account_id = account.pk
        else:
            account_id = account
            account = self.mWPAccount.objects.get(pk=account_id)
        params.update({
                'account_id': account_id,
                'callback_uri': reverse('wepay_ipn_withdrawal')})
        if kwargs:
            params.update(kwargs)
        params.update({'callback_uri': self._format_uri(params['callback_uri'])})
        if 'redirect_uri' in params:
            params.update({'redirect_uri': self._format_uri(params['redirect_uri'])})
        response = self.call("/withdrawal/create", params=params)
        kwargs = {}
        kwargs.update(params)
        kwargs.update(self.withdrawal_get(response['withdrawal_id']))
        kwargs.update({'account': account})
        return self.mWPWithdrawal.objects.create(**kwargs)

    def withdrawal_modify(self, withdrawal, callback_uri):
        if isinstance(account, self.mWPWithdrawal):
            withdrawal_id = withdrawal.pk
        else:
            withdrawal_id = withdrawal
        callback_uri = self._format_uri(reverse('wepay_ipn_withdrawal'))
        params = {'withdrawal_id': withdrawal_id,
                  'callback_uri': callback_uri}
        return self.call("/withdrawal/modify", params=params)

    def withdrawal_update_local(self, withdrawal, response=None):
        if isinstance(account, self.mWPWithdrawal):
            withdrawal_id = withdrawal.pk
        else:
            withdrawal_id = withdrawal
            try:
                withdrawal = self.mWPWithdrawal.objects.get(pk=withdrawal_id)
            except self.mWPWithdrawal.DoesNotExist:
                if response:
                    return self.mWPWithdrawal.objects.create_revive(**response)
        if not response:
            response = self.withdrawal_get(withdrawal_id)
        if withdrawal.state != response['state']:
            previous_state = withdrawal.state
            withdrawal.update(**response)
            withdrawal_state_changed(
                sender=self.mWPWithdrawal, withdrawal=withdrawal,
                previous_state=previous_state, response=response)
            return withdrawal
        return withdrawal.update(**response)
        

