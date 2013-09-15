from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View

from djwepay.models import User
from djwepay.signals import ipn_processed
from djwepay.api import get_wepay_model
from wepay.exceptions import WePayError

__all__ = ['IPNView', 'TestsCallbackView']

class IPNView(View):
    http_method_names = ['post']

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(IPNView, self).dispatch(*args, **kwargs)

    def post(self, request, **kwargs):
        obj_name = kwargs.get('obj_name')
        model = get_wepay_model(obj_name)
        obj_id_name = "%s_id" % obj_name
        user = None
        user_id = kwargs.get('user_id', None)
        try:
            obj_id = request.POST[obj_id_name]
        except KeyError:
            return HttpResponse(
                "Not recognized or not implemented object IPN. %s" % 
                obj_id_name, status=501)
        try:
            obj = model.objects.get(pk=obj_id)
        except model.DoesNotExist:
            if obj_name == 'user':
                raise Http404("User object with user_id: '%s' not found." % obj_id)
            obj = model(pk=obj_id)
        if not user_id is None:
            user = get_object_or_404(get_wepay_model('user'), pk=kwargs['user_id'])
            obj.access_token = user.access_token
        try:
            api_call = getattr(obj, "api_%s" % obj_name)
            api_call()
            obj.save()
        except WePayError, e:
            if e.code == 1011 and not user is None: # acess_token has been revoked
                user.access_token = None
                user.save()
            else:
                return HttpResponse(
                    "WePay error on update. %s" % e, status=500)
        ipn_processed.send(sender=model, instance=obj)
        return HttpResponse("Successfull object update.")
        

class TestsCallbackView(View):
    """
    This view is used whenever the tests for djwepay app are being run.
    All the api calls in the test suite run in a test enviroment (test db, 
    no webserver etc.), but since the calls are made to the actual 
    stage.wepay.com server we cannot give real callback_uri's instead we use this
    fake view to send a 200 response in order to prevent IPN retries.
    """
    http_method_names = ['post', 'get']

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(TestsCallbackView, self).dispatch(*args, **kwargs)

    def post(self, request, **kwargs):
        return HttpResponse("Success.")

    def get(self, request, **kwargs):
        return HttpResponse("Success.")
