from django.conf.urls import patterns, url

urlpatterns = patterns('django_wepay.views',
    url(r'^ipn/user/$', 'ipn_user', name="wepay_ipn_user"),
    url(r'^ipn/account/$', 'ipn_account', name="wepay_ipn_account"),
    url(r'^ipn/checkout/$', 'ipn_checkout', name="wepay_ipn_checkout"),
    url(r'^ipn/preapproval/$', 'ipn_preapproval', name="wepay_ipn_preapproval"),
    url(r'^ipn/withdrawal/$', 'ipn_withdrawal', name="wepay_ipn_withdrawal"),
    url(r'^testing_callback/$', 'testing_callback', name="testing_callback"),
)
