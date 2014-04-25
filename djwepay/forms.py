import json

from django import forms
from django.utils.functional import curry

from djwepay.api import get_wepay_model
from wepay.exceptions import WePayError


#class JSONArrayWidget(forms.TextInput):
#    def render(self, name, value, attrs=None):
#        #if value is None:
#        #    return ""
#        if isinstance(value, basestring):
#            value = ', '.join(json.loads(value))
#        return super(JSONArrayWidget, self).render(name, value, attrs)

#class JSONArrayField(JSONFormField):
#
#    def __init__(self, *args, **kwargs):
#        if 'widget' not in kwargs:
#            kwargs['widget'] = JSONArrayWidget
#        super(JSONArrayField, self).__init__(*args, **kwargs)

#    def to_python(self, value):
#        #if value.strip():
#        #    value = "[%s]" % value
#        return super(JSONArrayField, self).to_python(value)




class AppForm(forms.ModelForm):
    client_id = forms.IntegerField(
        required=True, min_value=0, help_text="This is the ID of your API application.")
    client_secret = forms.CharField(
        required=True, max_length=255,
        help_text="This is a secret value for your API application.")
    access_token = forms.CharField(
        required=True, max_length=255, help_text="This is the access_token that grants "
        "this app permission to do things on behalf of user, who is the owner of this App.")

    name = forms.CharField(
        required=False, label="Theme Name", max_length=64,
        help_text="Name for the Color Theme")
    primary_color = forms.CharField(
        required=False, max_length=6, help_text="The hex triplet for the primary "
        "color on important elements such as headers.")
    secondary_color = forms.CharField(
        required=False, max_length=6, help_text="The hex triplet for the secondary "
        "color on elements such as info boxes, and the focus styles on text inputs.")
    background_color = forms.CharField(
        required=False, max_length=6, help_text="The hex triplet for the the background "
        "color for onsite and iframe pages.")
    button_color = forms.CharField(
        required=False, max_length=6, help_text="The hex triplet for the the "
        "color for primary action buttons.")

    #gaq_domains = JSONArrayField(
    #    required=False, label="Google Analytics Domains",
    #    help_text="Comma separated list of Google Analytics "
    #    "domains associated with the app. Example: UA-23421-01, UA-23421-02")

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        instance = kwargs.get('instance', None)
        if instance is not None:
            initial['access_token'] = instance.user.access_token
            if instance.theme_object:
                initial.update(instance.theme_object)
        kwargs.update({
            'initial': initial,
            'instance': instance
        })
        super(AppForm, self).__init__(*args, **kwargs)


    def clean(self):
        # update/create associated account

        account_id = self.data.get('account', None)
        if account_id:
            Account = get_wepay_model('account')
            try:
                account_id = int(account_id)
            except ValueError, exc:
                raise forms.ValidationError(str(exc))
            try:
                try:
                    account = Account.objects.get(pk=account_id)
                    account.api_account()
                except Account.DoesNotExist:
                    account, response = self.instance.api.account(
                        account_id=account_id,
                        callback=curry(Account.objects.create_from_response, None))
                    self.cleaned_data['account'] = account
            except WePayError, exc:
                raise forms.ValidationError(str(exc))
        return super(AppForm, self).clean()

    def save(self, *args, **kwargs):
        self.instance.user.access_token = self.access_token
        return super(AppForm, self).save(*args, **kwargs)

    class Meta:
        model = get_wepay_model('app')
        fields = (
            'client_id', 'client_secret', 'access_token', 'account', 'user',
            'name', 'primary_color', 'secondary_color',
            'background_color', 'button_color', 'gaq_domains'
        )



ACCOUNT_TYPE_CHOICES = (
    ('personal', u"Personal"),
    ('nonprofit', u"Non-profit Organization"),
    ('business', u"Business"),
)

class AccountCreateForm(forms.Form):
    name = forms.CharField(max_length=255, required=True, label="Account Name",
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
