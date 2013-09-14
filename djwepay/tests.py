import cookielib, mechanize, urllib, urllib2, urlparse, random, time
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings

from djwepay.exceptions import WePayError
from djwepay.api import get_wepay_model
from djwepay.signals import *

TEST_LOGIN = getattr(settings, 'WEPAY_TESTS_LOGIN', '')
TEST_PASSWORD = getattr(settings, 'WEPAY_TESTS_PASSWORD', '')
TEST_APP_ID = getattr(settings, 'WEPAY_TESTS_APP_ID')
TEST_USER_ID = getattr(settings, 'WEPAY_TESTS_USER_ID')
TEST_ACCOUNT_ID = getattr(settings, 'WEPAY_TESTS_ACCOUNT_ID')
TEST_THEME = {
    'name': 'Test Theme',
    'primary_color': '000001',
    'secondary_color': '000002',
    'background_color': '000003',
    'button_color': '000004'
}
TEST_GAQ_DOMAINS = [
    'UA-23421-01',
    'UA-23421-02'
]
TEST_CC = {
    'nameOnCard': "Test Dude",
    'number': "4003830171874018",
    'expMonth': "02",
    'expYear': "17",
    'cvv2': "123",
}
TEST_ADDRESS = {
    'address1': "123 Main Stret",
    'city': "Albuquerque",
    'state': "NM",
    'zip': "87108",
    'country': "US"
}

App = get_wepay_model('app')
User = get_wepay_model('user')
Account = get_wepay_model('account')
Checkout = get_wepay_model('checkout')
Preapproval = get_wepay_model('preapproval')
Withdrawal = get_wepay_model('withdrawal')
CreditCard = get_wepay_model('credit_card')



@override_settings(WEPAY_APP_ID=TEST_APP_ID)
class WePayTestCase(TestCase):
    fixtures = ['djwepay_testdata.json']

    @staticmethod
    def browser_create():
        browser = mechanize.Browser()
        cj = cookielib.LWPCookieJar()
        browser.set_cookiejar(cj)
        browser.set_handle_equiv(True)
        # browser.set_handle_gzip(True)
        browser.set_handle_redirect(True)
        browser.set_handle_referer(True)
        browser.set_handle_robots(False)
        browser.set_handle_refresh(
            mechanize._http.HTTPRefreshProcessor(), max_time=1)
        # debugging stuff
        #browser.set_debug_redirects(True)
        #browser.set_debug_responses(True)
        #browser.set_debug_http(True)
        browser.addheaders = [
            ('User-Agent' , 
             "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/28.0.1500.71 Chrome/28.0.1500.71 Safari/537.36")
             #"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.4 (KHTML, like Gecko)"
             #" Chrome/22.0.1229.94 Safari/537.4")
        ]
        return browser

    @classmethod
    def setUpClass(cls):
        call_command('loaddata', 'djwepay_testdata')
        try:
            cls.app = App.objects.get_current()
            cls.user = User.objects.get(pk=TEST_USER_ID)
            cls.account = Account.objects.get(pk=TEST_ACCOUNT_ID)
        except App.DoesNotExist, e:
            raise ImproperlyConfigured(
                "There is no test data in the database. Reference the documentation. "
                "Error: %s" % e)
        if cls.app.production or not cls.app.access_token.startswith('STAGE_'):
            raise ImproperlyConfigured(
                "Set WEPAY_TESTS_APP_ID to an id of a non production App. "
                "Cannot run tests with App.production set to True.")
        cls.browser = cls.browser_create()
        cls.test_uri = reverse('wepay:tests_callback')
        cls.client = Client()


    @classmethod
    def tearDownClass(cls):
        # if any of the tests where temporary objects are created fails, 
        # tearDownClass performs the best attempt in removing them from WePay system
        accs = cls.user.api_account_find()
        acc_ids = [x['account_id'] for x in accs 
                   if x['account_id'] != TEST_ACCOUNT_ID]
        for acc_id in acc_ids:
            try:
                cls.user.api.account_delete(
                    account_id=acc_id, access_token=cls.user.access_token)
            except WePayError: pass

    def _reference_id(self):
        return random.randint(1, 10000000)

    def _validate_equality(self, obj, response):
        for key, value in response.iteritems():
            if hasattr(obj, key):
                self.assertEqual(value, getattr(obj, key))

    def test_app(self):
        response = self.app.api_app()
        self.app.save()
        self._validate_equality(self.app, response)

    def test_app_modify(self):
        self.app.api_app()
        self.app.save()
        gaq_domains = self.app.gaq_domains
        theme_object = self.app.theme_object
        if not theme_object is None:
            theme_object.pop('theme_id', None)
        response = self.app.api_app_modify(
            theme_object=TEST_THEME, gaq_domains=TEST_GAQ_DOMAINS)
        self.app.save()
        self._validate_equality(self.app, response)
        # modify test passed, lets change back the values
        response = self.app.api_app_modify(
            theme_object=theme_object, gaq_domains=gaq_domains)
        self.app.save()
        self._validate_equality(self.app, response)
        
    def test_oauth2(self):
        """ Tests calls: /oauth2/authorize, /oauth2/token, /user/modify."""
        if TEST_LOGIN and TEST_PASSWORD:
            # get authentication url
            auth_url = self.app.api_oauth2_authorize(redirect_uri=self.test_uri)
            self.browser.open(auth_url)
            # fillout the form
            self.browser.select_form(nr=0)
            self.browser.form['email'] = TEST_LOGIN
            self.browser.form['password'] = TEST_PASSWORD
            self.browser.form.set_all_readonly(False)
            self.browser.form['form'] = 'login'
            try:
            # submit form and in case any Http errors occur will catch them 
            # and still extract a code from url
                self.browser.submit()
            except mechanize.HTTPError: pass
            url = self.browser.response().geturl()
            self.assertTrue(url.startswith(self.app.api.get_full_uri(self.test_uri)))
            code = urlparse.parse_qs(urlparse.urlparse(url).query)['code'][0]
            user, response = self.app.api_oauth2_token(
                redirect_uri=self.test_uri, code=code)
            user.api_user_modify(callback_uri=self.test_uri)
            self.assertEqual(TEST_LOGIN, user.email)
            self._validate_equality(user, response)
        else:
            print "Cannot test OAuth2 calls, set 'WEPAY_TESTS_LOGIN' and " \
                "'WEPAY_TESTS_PASSWORD' constants in settings."

    def test_user(self):
        """Tests calls: /user, IPNs: User, signals:ipn_received, state_changed"""
        self.user.user_name = 'foo bar'
        self.user.first_name = 'foo'
        self.user.last_name = 'bar'
        callback_uri = self.user.callback_uri or ''
        response = self.user.api_user()
        self.user.save()
        self._validate_equality(self.user, response)
        # testing IPN and signals
        correct_state = self.user.state
        incorrect_state = 'pending' if correct_state == 'registered' else 'registered'
        signals_received = {
            'ipn_processed': False,
            'state_changed': False
        }
        def ipn_tester(instance, **kwargs):
            signals_received.update({'ipn_processed': True})
            self.assertEqual(instance.state, correct_state)
        ipn_processed.connect(ipn_tester, sender=User, weak=False)
        def state_tester(instance, previous_state, **kwargs):
            signals_received.update({'state_changed': True})
            self.assertEqual(instance.state, correct_state)
            self.assertEqual(previous_state, incorrect_state)
        state_changed.connect(state_tester, sender=User, weak=False)
        self.user.state = incorrect_state
        self.user.save()
        # imitate IPN
        response = self.client.post(
            reverse('wepay:ipn', kwargs={'obj_name':'user'}), 
            {'user_id': self.user.pk})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(signals_received['ipn_processed'])
        self.assertTrue(signals_received['state_changed'])

    def test_account(self):
        """Tests calls: /account/create, /account/modify, /account/add_bank
        /account/set_tax, /account/get_tax, /account/balance, /account/delete
        """
        name = "Runtime Test Account"
        acc, response = self.user.api_account_create(
            name=name, description="Account created during running of the "
            "django-wepay tests, it wasn't deleted probably due to a failing "
            "test case. You can safely remove it.", 
            reference_id=self._reference_id(), type='nonprofit',
            image_uri='http://www.placekitten.com/500/500',
            gaq_domains=TEST_GAQ_DOMAINS, theme_object=TEST_THEME, mcc=7299)
        self.assertIsNotNone(acc.account_uri)
        self.assertIsNotNone(acc.verification_uri)
        self._validate_equality(acc, response)
        self.assertEqual(
            acc.api.get_full_uri(reverse(
                'wepay:ipn', kwargs={'obj_name':'account', 'user_id':self.user.pk})),
            acc.callback_uri)
        name_modified = name + " - Modified"
        acc.api_account_modify(
            name=name_modified, description="description modified", 
            reference_id=self._reference_id(), callback_uri=self.test_uri, 
            image_uri='http://www.placekitten.com/450/450',
            gaq_domains=TEST_GAQ_DOMAINS, theme_object=TEST_THEME
        )
        self.assertEqual(acc.api.get_full_uri(self.test_uri), acc.callback_uri)

        self.assertEqual(name_modified, acc.name)

        self.assertIsNotNone(acc.pending_balance)
        self.assertIsNotNone(acc.available_balance)
        self.assertIsNotNone(acc.pending_amount)
        self.assertIsNotNone(acc.reserved_amount)
        self.assertIsNotNone(acc.disputed_amount)
        
        response = acc.api_account_add_bank(mode='iframe', redirect_uri=self.test_uri)
        self._validate_equality(acc, response)
        
        taxes = [
            {u"percent":9, u"country": u"US", u"state": u"CA", u"zip": 94025},
            {u"percent":7, u"country": u"US", u"state": u"CA", u"zip": None},
            {u"percent":5, u"country": u"US", u"state": None, u"zip": None},
        ]
        response = acc.api_account_set_tax(taxes=taxes)
        self.assertEqual(taxes, response)
        response = acc.api_account_get_tax()
        self.assertEqual(taxes, response)

        acc.api_account_delete(reason='test finished')

      
    def test_checkout(self):
        checkout, response = self.account.api_checkout_create(
            short_description="Test Checkout", type="DONATION", amount=1010, 
            long_description="Long description testing Checkout",
            payer_email_message="test@example.com", payee_email_message="Ssup",
            reference_id=self._reference_id(), app_fee=2, fee_payer='payee',
            redirect_uri=self.test_uri, auto_capture=True, require_shipping=True,
            shipping_fee=2, charge_tax=True, mode='iframe', prefill_info={
            "name": "Bill Clerico", "phone_number": "855-469-3729"},
            funding_sources='bank')
        self._validate_equality(checkout, response)
        self.assertIsNotNone(checkout.redirect_uri)
        self.assertIsNotNone(checkout.callback_uri)
        #self.assertIsNotNone(checkout.dispute_uri) - empty on new checkouts
        response = checkout.api_checkout_modify(callback_uri=self.test_uri)
        self.assertEqual(
            checkout.api.get_full_uri(self.test_uri), checkout.callback_uri)
        try:
            checkout.api_checkout_capture()
        except WePayError, e:
            self.assertEqual(e.code, 4004)
        try:
            checkout.api_checkout_refund(refund_reason="test refund reason")
        except WePayError, e:
            self.assertEqual(e.code, 4004)
        try:
            checkout.api_checkout_cancel(cancel_reason="test cancel reason")
        except WePayError, e:
            self.assertEqual(e.code, 4004)

    def test_finds(self):
        self.user.api_account_find(
            name='some name', reference_id=12345, sort_order='DESC')

        self.account.api_checkout_find(
            start=0, limit=10, reference_id=12345, state='new',
            preapproval_id=12345, start_time=int(time.time()-1000),
            end_time=int(time.time()), sort_order='ASC', shipping_fee=3)

        self.account.api_preapproval_find(
            state='new', reference_id=12355, start=int(time.time()-1000),
            sort_order='ASC', last_checkout_id=65865, shipping_fee=3)

        self.account.api_withdrawal_find(
            limit=5, start=int(time.time()-1000), sort_order='ASC')
            
        self.app.api_credit_card_find(reference_id=12345, limit=6, 
                                      start=int(time.time()-1000), sort_order='ASC')
        

    def test_preapproval(self):
        """Tests calls: /preapproval, /preapproval/create, /preapproval/modify,
        /preapproval/cancel
        """
        preapproval, reposnse = self.account.api_preapproval_create(
            short_description="Testing preapprovals", period="daily", 
            amount=Decimal('1000.00'), reference_id=self._reference_id(),
            app_fee=Decimal('99.99'), fee_payer="payee_from_app",
            redirect_uri=self.test_uri, callback_uri=self.test_uri,
            fallback_uri=self.test_uri, require_shipping=True,
            shipping_fee=Decimal('5.00'), charge_tax=True,
            payer_email_message="Testin preapproval message for payer",
            long_description="Very long description testing preapprovals",
            frequency=60, start_time=int(time.time()+600), 
            end_time=int(time.time()+5000000), auto_recur=True, mode="iframe",
            prefill_info={'name': "Joe Blow"}, funding_sources="bank,cc")
        self.assertIsNotNone(preapproval.preapproval_uri)
        self.assertIsNotNone(preapproval.manage_uri)
        self.assertIsNotNone(preapproval.redirect_uri)
        self.assertIsNotNone(preapproval.callback_uri)
        preapproval.api_preapproval_modify(callback_uri=self.test_uri)
        preapproval.api_preapproval_cancel()

        
    def test_withdrawal(self):
        """Tests calls: /withdrawal, /withdrawal/create, /withdrawal/modify"""
        try:
            withdrawal, response = self.account.api_withdrawal_create(
                redirect_uri=self.test_uri, callback_uri=self.test_uri,
                note="Short description, testing withdrawal create.", mode="iframe")
        except WePayError, e:
            self.assertEqual(e.code, 3005)
            return
        self.assertIsNotNone(withdrawal.redirect_uri)
        self.assertIsNotNone(withdrawal.callback_uri)
        self.assertIsNotNone(withdrawal.withdrawal_uri)
        test_uri_modified = self.test_uri + "?modified=True"
        withdrawal.api_withdrawal_modify(callback_uri=test_uri_modified)
        self.assertEqual(
            withdrawal.api.get_full_uri(test_uri_modified), withdrawal.callback_uri)


    def test_credit_card(self):
        cc, response = self.app.api_credit_card_create(
            TEST_CC['number'], TEST_CC['cvv2'], TEST_CC['expMonth'], 
            TEST_CC['expYear'], TEST_CC['nameOnCard'], 'test@example.com',
            TEST_ADDRESS)
        cc.api_credit_card()
        self.assertEqual(cc.user_name, TEST_CC['nameOnCard'])
        cc.api_credit_card_authorize()
        cc.api_credit_card_delete()
