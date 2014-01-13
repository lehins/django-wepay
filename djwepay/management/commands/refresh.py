from django.core.management.base import BaseCommand

from djwepay.api import get_wepay_model

from optparse import make_option

from wepay.exceptions import WePayError

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--object_name', default='', dest='obj_name',
                    help='Provide the name of the object you want to refresh. '
                    'Ex. --object_name=credit_card'),
        make_option('--ids', default='', dest='ids', help='Provide comma separated '
                    'ids of the objects you want to refresh. All by default'),
    )
    help = 'Retrieves current information from WePay and updates objects'

    def handle(self, *args, **kwargs):
        obj_name = kwargs.get('obj_name')
        ids = kwargs.get('ids', '')
        model = get_wepay_model(obj_name)
        if model is None:
            print "Unrecognized object name: %s " % obj_name
            exit()
        pks = [int(x) for x in ids.split(',') if x]
        if hasattr(model.objects, 'accessible'):
            objects = model.objects.accessible()
        else:
            objects = model.objects.all()
        if pks:
            objects.filter(pk__in=pks)
        for obj in objects:
            method = getattr(obj, "api_%s" % obj_name)
            try:
                method()
                print "Updated object with id: %s" % obj.pk
            except WePayError, e:
                if e.code == 1011:
                    if obj_name == 'user':
                        obj.access_token = None
                        obj.save()
                    print "access token revoked for the object with id: %s" % obj.pk
                else:
                    print "problem updating object with id: %s" % obj.pk
                print e
