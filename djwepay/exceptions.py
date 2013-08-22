from wepay.exceptions import WePayError as WePayErrorAPI

class WePayError(WePayErrorAPI):
    def __init__(self, error_type, message, error_code):
        WePayErrorAPI.__init__(self, error_type, message)
        self.error_code = error_code
