from optparse import make_option
from django.core.management.base import BaseCommand

from djwepay.api import get_wepay_model, DEFAULT_MODELS

from wepay.exceptions import WePayHTTPError, WePayConnectionError

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--objects', default='', dest='objects',
                    help="Comma separated object names that need their callback_uri updated"),
        make_option('--users', default='', dest='users',
                    help="Comma separated object user ids that need to be retrieved."),
    )
    supported_objects = [
        'account', 'checkout', 'preapproval', 'withdrawal', 'credit_card'
        'subscription_plan', 'subscription', 'subscription_charge'
    ]
    retrieve_errors = None

    def retrieve_objects(self, obj_name, parent, parent_name, **kwargs):
        start = 0
        limit = 5
        api_find = getattr(parent, "api_%s_find" % obj_name)
        responses = api_find(
            start=start, limit=limit, timeout=3*60, **kwargs)[1]
        model = get_wepay_model(obj_name)
        objects = []
        while responses:
            for response in responses:
                if model.objects.filter(pk=response[model._meta.pk.attname]).exists():
                    action = "Updated"
                else:
                    action = "Retrieved"
                try:
                    obj = model.objects.create_from_response(
                        True, response, **{parent_name: parent})
                except BaseException:
                    print(response) # useful for debugging
                    raise
                objects.append(obj)
                print("%s: %s" % (action ,obj))
            start+= limit
            try:
                responses = api_find(
                    start=start, limit=limit, timeout=3*60, **kwargs)[1]
            except (WePayHTTPError, WePayConnectionError) as e:
                print("Error: %s" % e)
                self.retrieve_errors.append({
                    'call': "api_%s_find" % obj_name, 
                    'params': "start=%s, limit=%s" % (start, limit),
                    'error': e
                })
        return objects
            
    def handle(self, objects='', users='', **kwargs):
        self.retrieve_errors = []
        supported_objects = []
        for obj_name in self.supported_objects:
            try:
                get_wepay_model(obj_name)
                supported_objects.append(obj_name)
            except LookupError:
                pass
        if objects:
            objects = [o.strip() for o in objects.split(',') if o]
            unsupported_objects = set(objects) - set(supported_objects)
            assert not unsupported_objects, \
                "Unsupported objects: %s" % ','.join(unsupported_objects)
        else:
            objects = supported_objects
        filters = {}
        if users:
            user_pks = [pk.strip() for pk in users.split() if pk.strip()]
            filters = {'user_id__in': user_pks}
        users = get_wepay_model('user').objects.exclude(access_token=None)
        if filters:
            user = users.filter(**filters)
        for user in users:
            if 'account' in objects:
                responses = user.api_account_find()[1]
                accounts = []
                Account = get_wepay_model('account')
                for response in responses:
                    if Account.objects.filter(pk=response['account_id']).exists():
                        action = "Updated"
                    else:
                        action = "Retrieved"
                    account = Account.objects.create_from_response(
                        True, response, user=user)
                    print("%s: %s" % (action, account))
                    if account.state != 'deleted':
                        accounts.append(account)
            else:
                accounts = user.accounts.exclude(state='deleted')
            if 'preapproval' in objects:
                for account in accounts:
                    self.retrieve_objects('preapproval', account, 'account')
            if 'checkout' in objects:
                for account in accounts:
                    self.retrieve_objects('checkout', account, 'account')
            if 'withdrawal' in objects:
                for account in accounts:
                    self.retrieve_objects('withdrawal', account, 'account')
            if 'subscription_plan' in objects:
                for account in accounts:
                    subscription_plans = self.retrieve_objects(
                        'subscription_plan', account, 'account')
                    if 'subscription' in objects:
                        for subscription_plan in subscription_plans:
                            self.retrieve_objects(
                                'subscription', subscription_plan, 'subscription_plan')
                    if 'subscription_charge' in objects:
                        for subscription_plan in subscription_plans:
                            self.retrieve_objects(
                                'subscription_charge', subscription_plan, 'subscription_plan')
        app = get_wepay_model('app').objects.get_current()
        #if 'preapproval' in objects:
        #    self.retrieve_objects('preapproval', app, 'app', account_id=0)
        if 'credit_card' in objects:
            self.retrieve_objects('credit_card', app, 'app')
        if self.retrieve_errors:
            print("THERE WERE ERRORS:")
            print(self.retrieve_errors)