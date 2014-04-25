from djwepay.api import get_wepay_model

def wepay(request):
    app = get_wepay_model('app').objects.get_current()
    base_url = "https://wepay.com" if app.production else "https://stage.wepay.com"
    return {
        'WEPAY_APP': app,
        'WEPAY_LOGIN_URL': "%s/login" % base_url,
        'WEPAY_TOS_URL': "%s/legal/terms-of-service" % base_url,
        'WEPAY_PRIVACY_URL': "%s/legal/privacy-policy" % base_url
    }
