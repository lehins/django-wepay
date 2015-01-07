from django.conf import settings
from django.db import models

# Add MoneyField to 'south', so migrations are possible
try:
    if 'south' in getattr(settings, 'INSTALLED_APPS'):
        from south.modelsinspector import add_introspection_rules
        add_introspection_rules([], ["^djwepay\.fields\.MoneyField"])
except ImportError: pass

class MoneyField(models.DecimalField):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('decimal_places', 2)
        kwargs.setdefault('max_digits', 11) # ~1 billion USD, should be enough for now
        super(MoneyField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        try:
            name, path, args, kwargs = super(MoneyField, self).deconstruct()
            if self.decimal_places != 2:
                kwargs['decimal_places'] = self.decimal_places
            if self.max_digits != 11:
                kwargs['max_digits'] = self.max_digits
            return name, path, args, kwargs
        except AttributeError: pass