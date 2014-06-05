import copy

from django.conf import settings
from django.template.base import Node, token_kwargs, TemplateSyntaxError
from django.template.defaulttags import register
from django.utils import six

from djwepay.api import get_wepay_model, DEFAULT_SCOPE

APP = get_wepay_model('app').objects.get_current()

class AuthorizeNode(Node):
    template = """
    <script src="%(browser_js)s" type="text/javascript"></script>
    <script type="text/javascript">
      function oauth2_authorize(){
        if(document.documentMode && document.documentMode >= 10){ 
          return false; // disable for gte IE10
        }
        WePay.set_endpoint("%(endpoint)s");
        var button = document.getElementById("%(elem_id)s");
        WePay.OAuth2.button_init(button, {
          "client_id": "%(client_id)d",
          "scope": %(scope)r,
          "user_name": "%(user_name)s",
          "user_email": "%(user_email)s",
          "redirect_uri": "%(redirect_uri)s",
          "top": %(top)d,
          "left": %(left)d,
          "state": "%(state)s",
          "callback": %(callback)s 
        });
        if (window.addEventListener) {
	  button.addEventListener("click", function(){return false;}, false);
	} else if (window.attachEvent) {
	  button.attachEvent("onclick", function(){return false;}, false);
	}
      }
      if(window.addEventListener) window.addEventListener("load", oauth2_authorize);
      else window.attachEvent("onload", oauth2_authorize);
    </script>
    """

    default_params = {
        'browser_js': APP.api.browser_js,
        'endpoint': "production" if APP.api.production else "stage",
        'elem_id': "",
        'client_id': APP.client_id,
        'scope': DEFAULT_SCOPE.split(','),
        'user_name': "",
        'user_email': "",
        'redirect_uri': "",
        'top': 100,
        'left': 100,
        'state': "",
        'callback': "",
    }
    def __init__(self, params={}):
        unrecognized = set(params) - set(self.default_params)
        if unrecognized:
            raise TemplateSyntaxError("authorize received unrecognized tokens: %r" %
                                      ','.join(unrecognized))
        self.params = params

    def __repr__(self):
        return "<AuthorizeNode>"

    def render(self, context):
        custom_params = dict((key, val.resolve(context)) for key, val in
                      six.iteritems(self.params))
        params = copy.copy(self.default_params)
        params.update(custom_params)
        APP.api.app.complete_uri('redirect_uri', params)
        return self.template % params
        
        


@register.tag('wepay_oauth2')
def wepay_oauth2(parser, token):
    bits = token.contents.split()
    remaining_bits = bits[1:]
    params = token_kwargs(remaining_bits, parser, support_legacy=True)
    if not params or not ('redirect_uri' in params and 'callback' in params 
                          and 'elem_id' in params):
        raise TemplateSyntaxError(
            "%r expected at least three variables namely: "
            "'elem_id', 'redirect_uri' and 'callback'" % bits[0])
    if remaining_bits:
        raise TemplateSyntaxError("%r received an invalid token: %r" %
                                  (bits[0], remaining_bits[0]))
    return AuthorizeNode(params)


DEFAULT_TITLES = (
    ('action_required', "Action Required"),
    ('kyc', "Know Your Customer Information"),
    ('bank_account', "Bank Account Information"),    
)

TITLES = dict(DEFAULT_TITLES + getattr(settings, 'WEPAY_TITLES', ()))

@register.filter('wepay_title', safe=True)
def wepay_title(value):
    if not value:
        return ''
    return TITLES.get(value, None) or value.title()

    