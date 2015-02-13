from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View, TemplateView

from djwepay.api import get_wepay_model
from djwepay.signals import ipn_processed
from djwepay.forms import AccountEditForm
from wepay.exceptions import WePayHTTPError
from wepay.utils import cached_property

__all__ = ['IPNView', 'OAuth2Mixin', 'AccountMixin', 'AccountEditView']


class IPNView(View):

    http_method_names = ['post']
    supported_objects = [
        'user', 'account', 'checkout', 'preapproval', 'withdrawal', 
        'subscription_plan', 'subscription'
    ]

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(IPNView, self).dispatch(*args, **kwargs)


    def post(self, request, user_id=None, **kwargs):
        model = None
        obj_id = None
        for obj_name in self.supported_objects:
            obj_id_name = "%s_id" % obj_name
            if obj_id_name in request.POST:
                obj_id = request.POST[obj_id_name]
                model = get_wepay_model(obj_name)
                break
        if model is None:
            if obj_id is None:
                return HttpResponse(
                    "Missing object_id in POST.", status=400)
            return HttpResponse(
                "Object '%s' is not supported by this application." % obj_name, status=501)
        user = None
        try:
            obj = model.objects.get(pk=obj_id)
        except model.DoesNotExist:
            if obj_name == 'user':
                # ipn received for user that wasn't created locally, cannot recreate
                # due to lack of info, which is not the case for the rest of the objects
                raise Http404("User object with user_id: '%s' not found." % obj_id)
            obj = model(pk=obj_id)
        if user_id is not None:
            # retrieve access_token from the user object, so we can perform a lookup call
            user = get_object_or_404(get_wepay_model('user'), pk=user_id)
            obj.access_token = user.access_token
        try:
            api_call = getattr(obj, "api_%s" % obj_name)
            api_call()
        except WePayHTTPError as exc:
            if exc.error_code == 1011 and user is not None:
                # acess_token has been revoked, reflect it in db
                user.access_token = None
                user.save()
            else:
                return HttpResponse(
                    "WePay error on update. %s" % exc, status=exc.status_code)
        ipn_processed.send(sender=model, instance=obj)
        return HttpResponse("Successfull %s update." % obj_name)
        


class OAuth2Mixin(object):
    """
    Mixin for Django generic style views that is helpfull for WePay OAuth2 process
    """

    @property
    def app(self):
        return get_wepay_model('app').objects.get_current()
    

    def get_redirect_uri(self):
        """
        Returns current view's url. Override this method to supply a different
        redirect_uri for oauth2 calls.
        """
        return self.request.path


    def get_authorization_url(self, user=None, prefill=True, **kwargs):
        """Calls :meth:`djwepay.api.AppApi.api_oauth2_authorize` and returns a url where
        user can be sent off to in order to grand access. Prefills ``redirect_uri``
        by calling :func:`get_redirect_uri`. ``user_name`` and ``user_email`` 
        parameters are prefilled by using information from django :attr:`user`
        object, which can be passed as a keyword argument otherwise it defaults to 
        ``self.request.user``, in order to prevent that behavior pass ``prefill=False``. 
        Any extra keywords will be passed along to the api call.

        :keyword User user: Will be used to prefill ``user_name`` and
            ``user_email``. Defaults to ``self.request.user``.

        :keyword bool prefill: set to ``False`` in order to prevent user info retrival.

        """

        if prefill:
            user = user or self.request.user
            if not user.is_anonymous():
                if not 'user_name' in kwargs:
                    kwargs['user_name'] = user.get_full_name()
                if not 'user_email' in kwargs:
                    kwargs['user_email'] = user.email
        return self.app.api_oauth2_authorize(
            redirect_uri=self.get_redirect_uri(), **kwargs)


    def get_user(self, **kwargs):
        """
        Calls :func:`djwepay.api.App.api_oauth2_token`
        """
        if 'error' in self.request.GET and \
           self.request.GET['error'] == "access_denied":
            raise AttributeError("%s - %s" % (
                self.request.GET['error'], 
                self.request.GET.get('error_description', '')))
        try:
            if self.request.method == 'POST':
                code = self.request.POST.get('code')
            else:
                code = self.request.GET.get('code')
        except KeyError:
            raise AttributeError("'code' is missing.")
        try:
            user, response = self.app.api_oauth2_token(
                code=code, redirect_uri=self.get_redirect_uri(), **kwargs)
            return user
        except WePayHTTPError as exc:
            if exc.error_code == 1012: # the code has expired
                raise AttributeError(str(e))
            raise


class AccountMixin(object):
    account_id_kwarg_name = 'account_id'
    refresh = True

    @cached_property
    def account(self):
        account_id = self.get_account_id()
        return self.get_account(account_id)

    def has_permission(self, account):
        raise NotImplementedError("For security reasons it is a required method.")

    def get_account_id(self):
        try:
            return self.kwargs[self.account_id_kwarg_name]
        except KeyError: pass
        try:
            if self.request.method == 'POST':
                return int(self.request.POST.get(self.account_id_kwarg_name))
            else:
                return int(self.request.GET.get(self.account_id_kwarg_name))
        except (ValueError, TypeError, KeyError): pass

    def get_redirect_uri(self):
        return self.request.get_full_path()

    def get_account(self, account_id):
        account = get_object_or_404(get_wepay_model('account'), account_id=account_id)
        if not self.has_permission(account):
            raise PermissionDenied
        if self.refresh:
            # best attempt to update all of account's info
            batch_id = 'account-%s-refresh' % account_id
            redirect_uri = self.get_redirect_uri()
            account.api_account(batch_mode=True, batch_id=batch_id, commit=False,
                                batch_reference_id='%s-info' % batch_id)
            account.api_account_get_update_uri(batch_mode=True, batch_id=batch_id, 
                                               batch_reference_id='%s-uri' % batch_id,
                                               redirect_uri=redirect_uri)
            account.api_account_get_reserve_details(batch_mode=True, batch_id=batch_id, 
                                                    batch_reference_id='%s-reserve' % batch_id)
            app = get_wepay_model('app').objects.get_current()
            try:
                app.api_batch_create(batch_id, timeout=20)
            except WePayError: pass
        return account


class AccountView(AccountMixin, TemplateView):
    submit_name = 'btn_account_edit'

    def get_context_data(self, **kwargs):
        kwargs['account'] = self.account
        if 'account_edit_form' not in kwargs:
            kwargs['account_edit_form'] = AccountEditForm(self.account)
        return super(AccountView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        context = {}
        if self.submit_name in request.POST:
            account_edit_form = AccountEditForm(self.account, data=request.POST)
            if account_edit_form.is_valid():
                account_edit_form.save()
            context['account_edit_form'] = account_edit_form
        try:
            kwargs['context'] = context
            return super(AccountView, self).post(request, *args, **kwargs)
        except AttributeError:
            return self.render_to_response(self.get_context_data(**context))
