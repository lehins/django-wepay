from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View

from djwepay.models import User
from djwepay.signals import ipn_processed
from djwepay.api import get_wepay_model
from wepay.exceptions import WePayError

__all__ = ['IPNView', 'OAuth2Mixin', 'TestsCallbackView']

class IPNView(View):
    http_method_names = ['post']

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(IPNView, self).dispatch(*args, **kwargs)

    def post(self, request, obj_name=None, user_id=None, **kwargs):
        model = get_wepay_model(obj_name)
        obj_id_name = "%s_id" % obj_name
        user = None
        try:
            obj_id = request.POST[obj_id_name]
        except KeyError:
            return HttpResponse(
                "Missing object_id in POST: %s" % obj_id_name, status=501)
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
        

class OAuth2Mixin(object):
    """
    Mixin for Django generic style views that is helpfull for WePay OAuth2 process
    """

    app = get_wepay_model('app').objects.get_current()
    
    def get_redirect_uri(self):
        """
        Returns current view's url. Overide this method to supply a different
        redirect_uri for oauth2 calls.
        """

        return self.request.path

    def get_authorization_url(self, user=None, **kwargs):
        """
        Calls :meth:`djwepay.api.AppApi.api_oauth2_authorize` and returns a url where
        user can be sent off to in order to grand access. Prefills ``redirect_uri``
        by calling :func:`get_redirect_uri`. ``user_name`` and ``user_email`` 
        parameters are prefilled by using information from django :attr:`user`
        object, which can be passed as a keyword argument otherwise it defaults to 
        ``self.request.user``, in order to prevent that behavior pass ``user=False``. 
        Any extra keywords will be passed along to the api call.

        :keyword django.contrib.auth.models.User user: Will be used to 
            prefill ``user_name`` and ``user_email``, set ``user`` to ``False`` 
            in order to prevent it. Defaults to ``self.request.user``.
            
        """

        if user != False:
            user = user or self.request.user
            if not user.is_anonymous():
                if not 'user_name' in kwargs:
                    kwargs['user_name'] = user.get_full_name()
                if not 'user_email' in kwargs:
                    kwargs['user_email'] = user.email
        return self.app.api_oauth2_authorize(
            redirect_uri=self.get_redirect_uri(), **kwargs)

    def get_token(self, **kwargs):
        """
        Calls :func:`djwepay.api.App.api_oauth2_token`
        """
        if 'error' in request.GET and request.GET['error'] == "access_denied":
            return {
                'error': request.GET['error'],
                'error_code': None,
                'error_description': request.GET.get('error_description', '')
            }
        try:
            code = self.request.GET['code']
        except KeyError:
            return {
                'error': 'code_missing',
                'error_code': None,
                'error_description': "'code' is missing from GET parameters"
            }
        try:
            user, response = self.app.api_oauth2_token(
                code=code, redirect_uri=self.get_redirect_uri(), **kwargs)
            return {
                'user': user,
                'response': response,
                'access_token': response['access_token']
            }
        except WePayError, e:
            if e.code == 1012: # the code has expired
                return {
                    'error': e.error,
                    'error_code': e.code,
                    'error_description': e.message
                }
            raise



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

