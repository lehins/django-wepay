from django.conf import settings
from django.utils import unittest

from djwepay.models import get_wepay_model

class AppTestCase(unittest.TestCase):
    #fixtures = ['initial_data.json']

    def test_initial(self):
        App = get_wepay_model('app')
        app = App.objects.get_current()
        self.assertEqual(app.pk, settings.WEPAY_APP_ID)