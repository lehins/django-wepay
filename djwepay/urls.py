from django.conf.urls import patterns, include, url

from djwepay.views import IPNView


urlpatterns = patterns('',
    url(r'^ipn/(?P<obj_name>user|account|checkout|preapproval|withdrawal|'
        'subscription_plan|subscription)/(?:(?P<user_id>\d+)/)?$', 
        IPNView.as_view(), name="ipn"),
)
