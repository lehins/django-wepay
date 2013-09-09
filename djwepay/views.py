from django.http import Http404, HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View

from djwepay.models import User
from djwepay.exceptions import WePayError
from djwepay.signals import ipn_processed #, state_changed

__all__ = ['IPNView', 'TestsCallbackView']

class IPNView(View):
    http_method_names = ['post']
    model = None
    obj_name = None

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(IPNView, self).dispatch(*args, **kwargs)

    def post(self, request, **kwargs):
        obj_id_name = "%s_id" % self.obj_name
        user = None
        try:
            obj_id = request.POST[obj_id_name]
        except KeyError:
            return HttpResponse(
                "Not recognized or not implemented object IPN. %s" % 
                obj_id_name, status=501)
        try:
            obj = self.model.objects.get(pk=obj_id)
        except self.modelDoesNotExist:
            if self.obj_name == 'user':
                raise Http404("User object with user_id: '%s' not found." % obj_id)
            obj = self.model(pk=obj_id)
        # all IPN objects have state,  there is no need to chack for attribute
        cur_state = obj.state
        if 'user_id' in kwargs:
            user = User.objects.get(pk=kwargs['user_id'])
            obj.access_token = user.access_token
        try:
            api_call = getattr(obj, "api_%s" % self.obj_name)
            api_call()
            obj.save()
            if user and not user.active():
                # if a call went through successfully, but user was revoked before,
                # we can recover that user and all objects associated
                user.undelete()
        except WePayError, e:
            if e.code == 1011:
                # mark revoked users and objects associated as deleted
                if user:
                    user.delete()
                else:
                    obj.delete()
            else:
                return HttpResponse(
                    "WePay error on update. Type: '%s', Code: '%s', Message: '%s'" % 
                    (e.type, e.code, e.message), status=500)
        ipn_processed.send(sender=self.model, instance=obj)
        #if obj.state != cur_state:
        #    state_changed.send(
        #        sender=self.model, instance=obj, previous_state=cur_state)
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
