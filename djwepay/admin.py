from django.contrib import admin

from ajax_select import make_ajax_form
from ajax_select.admin import AjaxSelectAdmin

from djwepay.api import get_wepay_model, is_abstract

class AppAdmin(admin.ModelAdmin):
    list_display = ('client_id', 'status', 'production')
    list_filter = ('status', 'production', 'date_created', 'date_removed')
    readonly_fields = ('status', 'date_created', 'date_modified', 'date_removed')
    search_fields = ('status', 'theme_object', 'gaq_domain')

if not is_abstract('app'):
    admin.site.register(get_wepay_model('app'), AppAdmin)

class UserAdmin(AjaxSelectAdmin):
    list_display = ('user_id', 'user_name', 'email', 'state')
    list_filter = ('state', 'date_created', 'date_removed')
    readonly_fields = ('user_id', 'user_name', 'first_name', 'last_name', 'email', 'access_token', 'expires_in', 'state', 'date_created', 'date_modified', 'date_removed')
    search_fields = ('user_id', 'user_name', 'email', 'state')

    form = make_ajax_form(User, {'auth_users':'user'})

if not is_abstract('user'):
    admin.site.register(get_wepay_model('user'), UserAdmin)

class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_id', 'name', 'user', 'state', 'reference_id',
                    'verification_state', 'type')
    list_filter = ('state', 'verification_state', 'type', 'date_created',
                   'date_removed')
    readonly_fields = (
        'account_id', 'user', 'state', 'payment_limit', 'verification_state', 
        'type', 'create_time', 'date_created', 'date_modified', 'date_removed')

if not is_abstract('account'):
    admin.site.register(get_wepay_model('account'), AccountAdmin)
