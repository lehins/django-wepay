from djwepay.backends import WePay

from wepay.exceptions import WePayError, WePayConnectionError

class TestWePay(WePay):
    _expected_response = None

    def _get_expected_response(self):
        if self._expected_response is None:
            raise ValueError(
                "expected_respone should not be 'None', every call returns a response.")
        response = self._expected_response
        self._expected_response = None
        return response

    def _set_expected_response(self, value):
        if self._expected_response is not None:
            raise ValueError("expected_respone wasn't cleared, it should be 'None'")
        self._expected_response = value

    expected_response = property(_get_expected_response, _set_expected_response)

    def __init__(self, *args, **kwargs):
        super(TestWePay, self).__init__(*args, **kwargs)
        def fake_post(url, params, headers):
            response = self.expected_response
            if isinstance(response, WePayError) or isinstance(response, WePayConnectionError):
                raise response
            return response
        self._post = fake_post