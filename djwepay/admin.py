from django.contrib import admin
from django.contrib.auth import get_user_model

from ajax_select import make_ajax_form
from ajax_select.admin import AjaxSelectAdmin

from djwepay.models import *

class AppAdmin(admin.ModelAdmin):
    list_display = ('client_id', 'status', 'production')
    list_filter = ('status', 'production', 'date_created', 'date_removed')
    readonly_fields = ('status', 'date_created', 'date_modified', 'date_removed')
    search_fields = ('status', 'theme_object', 'gaq_domain')

admin.site.register(App, AppAdmin)

class UserAdmin(AjaxSelectAdmin):
    list_display = ('user_id', 'user_name', 'email', 'state')
    list_filter = ('state', 'date_created', 'date_removed')
    readonly_fields = ('user_id', 'user_name', 'first_name', 'last_name', 'email', 'access_token', 'expires_in', 'state', 'date_created', 'date_modified', 'date_removed')
    search_fields = ('user_id', 'user_name', 'email', 'state')

    form = make_ajax_form(User, {'auth_users':'user'})

admin.site.register(User, UserAdmin)

class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_id', 'name', 'user', 'state', 'reference_id',
                    'verification_state', 'type')
    list_filter = ('state', 'verification_state', 'type', 'date_created',
                   'date_removed')
    readonly_fields = (
        'account_id', 'user', 'state', 'payment_limit', 'verification_state', 
        'type', 'create_time', 'date_created', 'date_modified', 'date_removed')

admin.site.register(Account, AccountAdmin)
