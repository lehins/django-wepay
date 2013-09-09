from django.conf.urls import patterns, include, url

from djwepay.models import *
from djwepay.views import *

ipn_patterns = patterns('',
    url(r'^user/$', 
        IPNView.as_view(model=User, obj_name='user'), name="user"),
    url(r'^account/(?P<user_id>\d+)/$', 
        IPNView.as_view(model=Account, obj_name='account'), name="account"),
    url(r'^checkout/(?P<user_id>\d+)/$', 
        IPNView.as_view(model=Checkout, obj_name='checkout'), name="checkout"),
    url(r'^preapproval/(?:(?P<user_id>\d+)/)?$', 
        IPNView.as_view(model=Preapproval, obj_name='preapproval'), 
        name="preapproval"),
    url(r'^withdrawal/(?P<user_id>\d+)/$', 
        IPNView.as_view(model=Withdrawal, obj_name='withdrawal'), name="withdrawal"),
)

urlpatterns = patterns('',
    url(r'^ipn/', include(ipn_patterns, namespace='ipn')),
    url(r'^tests_callback/$', TestsCallbackView.as_view(), name="tests_callback"),
)
