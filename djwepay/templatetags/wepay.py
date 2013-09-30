import copy

from django.template.base import Node, token_kwargs, TemplateSyntaxError
from django.template.defaulttags import register
from django.utils import six

from djwepay.api import get_wepay_model, DEFAULT_SCOPE

APP = get_wepay_model('app').objects.get_current()

class AuthorizeNode(Node):
    template = '<script src="%(browser_js)s" ' \
               'type="text/javascript"></script><script type="text/javascript">' \
               'function oauth2_authorize(){'\
               'WePay.set_endpoint("%(endpoint)s"); ' \
               'WePay.OAuth2.button_init(document.getElementById("%(elem_id)s"), {' \
               '"client_id": "%(client_id)d",' \
               '"scope": %(scope)r,' \
               '"user_name": "%(user_name)s",' \
               '"user_email": "%(user_email)s",' \
               '"redirect_uri": "%(redirect_uri)s",' \
               '"top": %(top)d,' \
               '"left": %(left)d,' \
               '"state": "%(state)s",' \
               '"callback": %(callback)s });}' \
               'if(window.addEventListener)' \
               'window.addEventListener("load", oauth2_authorize);' \
               'else window.attachEvent("onload", oauth2_authorize);' \
               '</script>' \

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
        APP._api_uri_modifier(params, 'redirect_uri')
        return self.template % params
        
        


@register.tag('oauth2_authorize')
def oauth2_authorize(parser, token):
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
