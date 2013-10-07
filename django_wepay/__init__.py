from django_wepay.api import DjangoWePay

# Major, minor, revision

VERSION = (0, 0, 1)

def get_version():
    return "%s.%s.%s" % VERSION

__version__ = get_version()
