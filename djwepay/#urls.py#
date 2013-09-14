from django.conf.urls import patterns, include, url

from djwepay.models import *
from djwepay.views import *


urlpatterns = patterns('',
    url(r'^ipn/(?P<obj_name>user|account|checkout|preapproval|withdrawal)/'
        '(?:(?P<user_id>\d+)/)?$', IPNView.as_view(), name="ipn"),
    url(r'^tests_callback/$', TestsCallbackView.as_view(), name="tests_callback"),
)
