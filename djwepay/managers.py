from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models

from djwepay.api import get_wepay_model

__all__ = [
    'AppManager', 'UserManager', 'AccountManager', 'AccountObjectsManager',
    'PreapprovalManager', 'SubscriptionManager'
]

APP_CACHE = {}


class AppManager(models.Manager):

    def get_current(self):
        """Returns the current :class:`App` based on the :ref:`WEPAY_APP_ID` in the
        project's settings. The :class:`App` object is cached the first time
        it's retrieved from the database.

        """
        try:
            app_id = settings.WEPAY_APP_ID
        except AttributeError:
            raise ImproperlyConfigured(
                "You're using the Django WePay application without having set the "
                "WEPAY_APP_ID setting. Create an app in your database and set the "
                "WEPAY_APP_ID setting to fix this error.")
        try:
            current_app = APP_CACHE[app_id]
        except KeyError:
            current_app = self.get(pk=app_id)
            APP_CACHE[app_id] = current_app
        return current_app


    def clear_cache(self):
        """Clears the ``App`` object cache."""
        global APP_CACHE
        APP_CACHE = {}



class UserManager(models.Manager):

    def create_from_response(self, app, response, **kwargs):
        try:
            user = self.get(pk=response['user_id'])
        except self.model.DoesNotExist:
            user = self.model(app=app)
        return user.instance_update(response, **kwargs)

    def accessible(self):
        return self.exclude(access_token=None)



class AccountManager(models.Manager):

    def create_from_response(self, user, response, **kwargs):
        account = self.model(user=user)
        return account.instance_update(response, **kwargs)

    def accessible(self):
        return self.exclude(user__access_token=None)

    def active(self):
        return self.accessible().filter(state='active')



class AccountObjectsManager(models.Manager):

    def create_from_response(self, account, response, **kwargs):
        obj = self.model(account=account)
        return obj.instance_update(response, **kwargs)

    def accessible(self):
        return self.exclude(account__user__access_token=None)



class PreapprovalManager(AccountObjectsManager):

    def create_from_response(self, app_or_account, response, **kwargs):
        if isinstance(app_or_account, get_wepay_model('app')):
            preapproval = self.model(app=app_or_account)
            return preapproval.instance_update(response, **kwargs)
        return super(PreapprovalManager, self).create_from_response(
            app_or_account, response, **kwargs)



class SubscriptionManager(models.Manager):

    def create_from_response(self, subscription_plan, response, **kwargs):
        obj = self.model(subscription_plan=subscription_plan)
        return obj.instance_update(response, **kwargs)

    def accessible(self):
        return self.exclude(subscription_plan__account__user__access_token=None)


