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
        if not 'decimal_places' in kwargs:
            kwargs['decimal_places'] = 2
        if not 'max_digits' in kwargs:
            kwargs['max_digits'] = 11 # ~1 billion USD, should be enough for now
        super(MoneyField, self).__init__(*args, **kwargs)

