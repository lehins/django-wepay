from django.forms.widgets import TextInput

from decimal import Decimal

class MoneyInput(TextInput):
    def render(self, name, value, attrs=None):
        if (type(value) == unicode or type(value) == str) and value:
            value = value.replace(',', '')
            value = value.replace('$', '')
            try:
                value = Decimal(value)
            except:
                pass
        if type(value) == Decimal:
            value = '$' + '{:,}'.format(value)
        return super(MoneyInput, self).render(name, value, attrs)
