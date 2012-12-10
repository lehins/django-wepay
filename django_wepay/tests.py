from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site

from django_wepay.api import DjangoWePay
from wepay.exceptions import WePayError

from decimal import Decimal
import cookielib, mechanize, urllib, urllib2

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
    # browser.set_debug_redirects(True)
    # browser.set_debug_responses(True)
    # browser.set_debug_http(True)
    browser.addheaders = [
        ('User-Agent' , 
         "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.4 (KHTML, like Gecko)"
         " Chrome/22.0.1229.94 Safari/537.4")]
    return browser

class DjangoWePayTestCase(TestCase):

    @classmethod
    def setUpClass(self):
        Site.objects.create(id=2, domain="test.example.com", name="test site")
        self.dwepay = DjangoWePay()
        self.testcc = "4003830171874018"
        browser = browser_create()
        self.test_uri = reverse('testing_callback')
        auth_url = self.dwepay.get_authorization_url(self.test_uri)
        browser.open(auth_url)
        browser.select_form(nr=0)
        self.email = ""
        self.pwd = ""
        browser.form['email'] = self.email
        browser.form['password'] = self.pwd
        browser.submit()
        url = browser.response().geturl()
        code = url.split('/')[-1].split('=')[-1]
        self.user = self.dwepay.user_create(
            code, self.test_uri, callback_uri=self.test_uri)
        accounts = self.user.wpaccount_set.all()
        print len(accounts)
        print len(self.dwepay.mWPPreapproval.objects.all())
        print len(self.dwepay.mWPCheckout.objects.all())
        self.account = self.dwepay.account_create(
            "name:Test Account", "descr:Test Account", callback_uri=self.test_uri)
        self.user.save()
        self.account.save()

    @classmethod
    def tearDownClass(self):
        # best attempt of cleanup after tests
        accounts = self.user.wpaccount_set.all()
        checkouts = self.dwepay.mWPCheckout.objects.all()
        preapprovals = self.dwepay.mWPPreapproval.objects.all()
        for checkout in checkouts:
            try:
                self.dwepay.checkout_refund(checkout, "Cleanup")
            except WePayError: pass
        for account in accounts:
            try:
                self.dwepay.account_delete(account)
            except WePayError: pass
        for preapproval in preapprovals:
            try:
                self.dwepay.preapproval_cancel(preapproval)
            except WePayError: pass
        

    def _preapproval_create(self, test_amount):
        optional_params={'mode': 'regular',
                         'redirect_uri': self.test_uri,
                         'callback_uri': self.test_uri,
                         'require_shipping': True,
                         'amount': test_amount}
        preapproval = self.dwepay.preapproval_create(
            self.account, "Create preapproval test", "once", **optional_params)
        browser = browser_create()
        browser.open(preapproval.preapproval_uri)
        browser.select_form(nr=1)
        browser.form['nameOnCard'] = "Test Name"
        browser.form['number'] = self.testcc
        browser.form['expirationMonth'] = "02"
        browser.form['expirationYear'] = "17"
        browser.form['cvv2'] = "123"
        browser.form['address[address1]'] = "123 Main Str"
        browser.form['address[city]'] = "Albuquerque"
        browser.form['address[address1]'] = "123 Main Str"
        browser.form['address[state]'] = ["NM"]
        browser.form['address[zip]'] = "87121"
        browser.submit()
        browser.select_form(nr=0)
        browser.form['name'] = "Test Shipping Name"
        browser.form['shipping_address[address1]'] = "123 Main Str"
        browser.form['shipping_address[city]'] = "Albuquerque"
        browser.form['shipping_address[address1]'] = "123 Main Str"
        browser.form['shipping_address[state]'] = ["NM"]
        browser.form['shipping_address[zip]'] = "87121"
        browser.form['phone'] = "5055551234"
        browser.submit()
        browser.select_form(nr=0)
        browser.form['email'] = self.email
        browser.form['save_info'] = False
        browser.submit()
        return preapproval

    def test_account_modify(self):
        new_name = "name:Test Account Modify"
        self.dwepay.account_modify(self.account, name=new_name)
        self.assertEqual(self.account.name, new_name)

    def test_account_modify_from_local(self):
        new_descr = "descr:Test Account Modify from local"
        self.account.description = new_descr
        self.account.save()
        self.dwepay.account_modify_from_local(self.account)
        self.assertEqual(self.account.description, new_descr)

    def test_preapproval_create(self):
        preapproval = self._preapproval_create(Decimal('2.17'))
        self.assertEqual(preapproval.state, "new")
        response = self.client.post(reverse('wepay_ipn_preapproval'),
                         {'preapproval_id': preapproval.pk})
        self.assertEqual(response.status_code, 200)
        preapproval = self.dwepay.mWPPreapproval.objects.get(pk=preapproval.pk)
        self.assertEqual(preapproval.state, "approved")
        self.assertIsNotNone(preapproval.shipping_address)

    def test_checkout_create_from_preapproval(self):
        preapproval = self._preapproval_create(Decimal('2.18'))
        checkout = self.dwepay.checkout_create_from_preapproval(
            preapproval, "DONATION")
        self.assertEqual(checkout.state, "authorized")
        response = self.client.post(reverse('wepay_ipn_checkout'),
                         {'checkout_id': checkout.pk})
        self.assertEqual(response.status_code, 200)
        checkout = self.dwepay.mWPCheckout.objects.get(pk=checkout.pk)
        preapproval = self.dwepay.mWPPreapproval.objects.get(pk=preapproval.pk)
        self.assertEqual(checkout.preapproval, preapproval)
