from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.options import FieldDoesNotExist

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


class ObjectManager(models.Manager):

    def create_from_response(self, commit, response, **kwargs):
        pk = response[self.model._meta.pk.attname]
        try:
            obj = self.get(pk=pk)
        except self.model.DoesNotExist:
            obj = self.model(pk=pk, **kwargs)
        return obj.instance_update(response, commit=commit)

class UserManager(ObjectManager):

    def accessible(self):
        return self.exclude(access_token=None)


class AccountManager(ObjectManager):

    def accessible(self):
        return self.exclude(user__access_token=None)

    def active(self):
        return self.accessible().filter(state='active')


class AccountObjectsManager(ObjectManager):

    def accessible(self):
        return self.exclude(account__user__access_token=None)


class PreapprovalManager(AccountObjectsManager):

    def create_from_response(self, commit, response, **kwargs):
        preapproval = super(PreapprovalManager, self).create_from_response(
            False, response, **kwargs)
        if response.get('last_checkout_id', None):
            # Here is some necessary evil. It can happen that we are retrieving 
            # an existing preapproval, that was used already to create a checkout.
            # So in order to prevent IntegrityError we get that Checkout from WePay
            # and save it db, but only after we commit Preapproval without last_checkout
            # This will not work if it is an App level Preapproval, since access_token
            # will be different between the two.
            try:
                checkout_field = self.model._meta.get_field('last_checkout')
                Checkout = checkout_field.rel.to
                if not Checkout.objects.filter(pk=response['last_checkout_id']).exists():
                    if preapproval.account:
                        checkout = Checkout(checkout_id=response['last_checkout_id'],
                                            account=preapproval.account)
                        preapproval.last_checkout = None
                        preapproval.save()
                        checkout.api_checkout()
                        preapproval.last_checkout = checkout
            except FieldDoesNotExist: 
                # if it is a custom Preapproval model without last_checkout field, 
                # we don't need to worry about it and can proceed as normal
                pass
        if commit:
            preapproval.save()
        return preapproval


class SubscriptionManager(ObjectManager):

    def accessible(self):
        return self.exclude(subscription_plan__account__user__access_token=None)


class SubscriptionChargeManager(ObjectManager):

    def accessible(self):
        return self.exclude(subscription_plan__account__user__access_token=None)


