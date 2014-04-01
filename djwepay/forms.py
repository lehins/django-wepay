from django import forms
from django.utils.functional import curry

from djwepay.api import get_wepay_model
from wepay.exceptions import WePayError

class AppForm(forms.ModelForm):

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
