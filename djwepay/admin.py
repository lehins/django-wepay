from django.contrib import admin

from djwepay.api import get_wepay_model, is_abstract
from djwepay.forms import AppForm

__all__ = ['AppAdmin', 'UserAdmin', 'AccountAdmin']


class AppAdmin(admin.ModelAdmin):
    list_display = ('client_id', 'user', 'account', 'status', 'state')
    list_filter = ('status', 'state', 'date_created')
    search_fields = ('state', 'status', 'theme_object', 'gaq_domain')
    form = AppForm

    def get_readonly_fields(self, request, obj=None):
        fields = [
            'state', 'status', 'date_created', 'date_modified', 'theme_object',
        ]
        if obj:
            fields.extend(['user', 'client_id', 'account'])
        return fields

if not is_abstract('app'):
    admin.site.register(get_wepay_model('app'), AppAdmin)

class UserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'user_name', 'email', 'state')
    list_filter = ('state', 'date_created')
    readonly_fields = (
        'user_id', 'user_name', 'first_name', 'last_name', 'email', 'state',
        'access_token', 'expires_in', 'date_created', 'date_modified'
    )
    search_fields = ('user_id', 'user_name', 'email', 'state')

if not is_abstract('user'):
    admin.site.register(get_wepay_model('user'), UserAdmin)

class AccountAdmin(admin.ModelAdmin):
    list_display = (
        'account_id', 'name', 'user', 'state', 'type'
    )
    list_filter = ('state', 'type', 'date_created')
    readonly_fields = (
        'account_id', 'user', 'state', 'country',
        'type', 'create_time', 'date_created', 'date_modified'
    )

if not is_abstract('account'):
    admin.site.register(get_wepay_model('account'), AccountAdmin)
