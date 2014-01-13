from django import forms

from djwepay.api import get_wepay_model

class AppForm(forms.ModelForm):
    def save(self, *args, **kwargs):
        if self.instance:
            self.instance.api_app()
        return super(AppForm, self).save(*args, **kwargs)

    class Meta:
        model = get_wepay_model('app')

ACCOUNT_TYPE_CHOICES = (
    ('personal', u"Personal"),
    ('nonprofit', u"Non-profit Organization"),
    ('business', u"Business"),
)

class AccountCreateForm(forms.Form):
    name = forms.CharField(max_length=255, required=True,
                           help_text=u"The name of the account you want to create.")
    description = forms.CharField(
        max_length=255, required=True, help_text=u"The description of the account "
        "you want to create.", widget=forms.Textarea)
    type = forms.ChoiceField(required=False, choices=ACCOUNT_TYPE_CHOICES)

    def clean_name(self):
        name = self.cleaned_data['name']
        if name.lower().rfind("wepay") >= 0:
            raise forms.ValidationError("Account name cannot contain 'wepay'.")
        return name
