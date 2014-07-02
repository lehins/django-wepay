from django.conf import settings
from django.utils import unittest

from djwepay.models import get_wepay_model
from djwepay.signals import state_changed
from wepay_app.models import WePayApp

class AppTestCase(unittest.TestCase):

    def setUp(self):
        App = get_wepay_model('app')
        self.app = App.objects.get_current()

    def test_initial(self):
        self.assertIs(get_wepay_model('app'), WePayApp)
        self.assertEqual(self.app.pk, settings.WEPAY_APP_ID)

    def test_app_lookup(self):
        App = get_wepay_model('app')
        self.app.api.expected_response = {'state': 'revoked'}
        states = {
            'old': None,
            'new': None
        }
        def test_state_change_receiver(sender, instance, previous_state=None, **kwargs):
            states.update({
                'old': previous_state,
                'new': instance.state
            })
        state_changed.connect(test_state_change_receiver, sender=App, weak=False)
        self.app.api_app(commit=False)
        self.assertEqual(states['old'], 'active')
        self.assertEqual(states['new'], 'revoked')
        self.assertEqual(self.app.state, 'revoked')
        # make sure Test Backend behaves properly
        self.assertRaises(ValueError, lambda: self.app.api.expected_response)
        # reset cached app
        App.objects.clear_cache()
        self.app = App.objects.get_current()
        # check that previous call didn't affect db
        self.assertEqual(self.app.state, 'active')


    def test_app_lookup_persistent(self):
        App = get_wepay_model('app')
        self.app.api.expected_response = {'gaq_domains': ['UA-23421-02']}
        self.app.api_app()
        from djwepay.managers import APP_CACHE
        # make sure cache is cleared upon app lookup and db contains new version
        self.assertEqual(APP_CACHE, {})
        self.app = App.objects.get_current()
        self.assertEqual(self.app.gaq_domains, ['UA-23421-02'])


    def test_app_modify(self):
        App = get_wepay_model('app')
        self.app.api.expected_response = {'theme_object': None}
        self.app.api_app_modify(theme_object=None)
        from djwepay.managers import APP_CACHE
        self.assertEqual(APP_CACHE, {})
        self.app = App.objects.get_current()
        self.assertEqual(self.app.theme_object, None)
