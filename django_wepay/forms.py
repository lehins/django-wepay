from django import forms

class MoneyField(forms.DecimalField):
    def __init__(self, *args, **kwargs):
        if not 'label' in kwargs:
            kwargs['label'] = u'Amount'
        if not 'decimal_places' in kwargs:
            kwargs['decimal_places'] = 2
        if not 'max_digits' in kwargs:
            kwargs['max_digits'] = 11
        if not 'widget' in kwargs:
            kwargs['widget'] = MoneyInput(attrs={'size':'17'})
        super(MoneyField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        value = value.replace(',', '')
        value = value.replace('$', '')
        return super(MoneyField, self).to_python(value)
