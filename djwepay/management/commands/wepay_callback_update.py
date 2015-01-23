from optparse import make_option
from django.core.management.base import BaseCommand

from djwepay.api import get_wepay_model, DEFAULT_MODELS

from wepay.exceptions import WePayHTTPError, WePayConnectionError

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--objects', default='', dest='objects',
                    help="Comma separated object names that need their callback_uri updated"),
    )
    supported_objects = [
        'user', 'account', 'checkout', 'preapproval', 'withdrawal', 
        'subscription_plan', 'subscription'
    ]
    
    def handle(self, objects='', **kwargs):
        update_errors = []
        if objects:
            objects = [o.strip() for o in objects.split(',') if o]
            unknown_objects = set(objects) - set(self.supported_objects)
            assert not unknown_objects, "Unknown objects: %s" % ','.join(unknown_objects)
        else:
            objects = self.supported_objects
        models = []
        for obj_name in objects:
            try:
                models.append((obj_name, get_wepay_model(obj_name)))
            except LookupError:
                pass
        for obj_name, model in models:
            obj = None
            for obj in model.objects.accessible():
                try:
                    api_modify = getattr(obj, "api_%s_modify" % obj_name)
                    print("Modified: %s" % api_modify(callback_uri=obj.get_callback_uri())[0])
                except (WePayHTTPError, WePayConnectionError) as e:
                    update_errors.append({
                        'call': "api_%s_modify" % obj_name, 
                        'object': obj,
                        'params': "callback_uri=%s" % obj.get_callback_uri(),
                        'error': e
                    })
        if update_errors:
            print("THERE WERE ERRORS:")
            print(update_errors)