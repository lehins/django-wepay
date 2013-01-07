# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'WPAddress.city'
        db.alter_column('django_wepay_address', 'city', self.gf('django.db.models.fields.CharField')(max_length=63))

        # Changing field 'WPAddress.name'
        db.alter_column('django_wepay_address', 'name', self.gf('django.db.models.fields.CharField')(max_length=127))

        # Changing field 'WPAddress.address1'
        db.alter_column('django_wepay_address', 'address1', self.gf('django.db.models.fields.CharField')(max_length=63))

        # Changing field 'WPAddress.address2'
        db.alter_column('django_wepay_address', 'address2', self.gf('django.db.models.fields.CharField')(max_length=63))

        # Changing field 'WPAddress.country'
        db.alter_column('django_wepay_address', 'country', self.gf('django.db.models.fields.CharField')(max_length=63))

        # Changing field 'WPWithdrawal.state'
        db.alter_column('django_wepay_withdrawal', 'state', self.gf('django.db.models.fields.CharField')(max_length=15))

        # Changing field 'WPUser.access_token'
        db.alter_column('django_wepay_user', 'access_token', self.gf('django.db.models.fields.CharField')(max_length=127))

        # Changing field 'WPUser.state'
        db.alter_column('django_wepay_user', 'state', self.gf('django.db.models.fields.CharField')(max_length=15))

        # Changing field 'WPAccount.verification_state'
        db.alter_column('django_wepay_account', 'verification_state', self.gf('django.db.models.fields.CharField')(max_length=15))

        # Changing field 'WPAccount.type'
        db.alter_column('django_wepay_account', 'type', self.gf('django.db.models.fields.CharField')(max_length=15))

        # Changing field 'WPAccount.name'
        db.alter_column('django_wepay_account', 'name', self.gf('django.db.models.fields.CharField')(max_length=127))

        # Changing field 'WPCheckout.fee_payer'
        db.alter_column('django_wepay_checkout', 'fee_payer', self.gf('django.db.models.fields.CharField')(max_length=15))

        # Changing field 'WPCheckout.state'
        db.alter_column('django_wepay_checkout', 'state', self.gf('django.db.models.fields.CharField')(max_length=15))

        # Changing field 'WPPreapproval.period'
        db.alter_column('django_wepay_preapproval', 'period', self.gf('django.db.models.fields.CharField')(max_length=15))

        # Changing field 'WPPreapproval.state'
        db.alter_column('django_wepay_preapproval', 'state', self.gf('django.db.models.fields.CharField')(max_length=15))

    def backwards(self, orm):

        # Changing field 'WPAddress.city'
        db.alter_column('django_wepay_address', 'city', self.gf('django.db.models.fields.CharField')(max_length=64))

        # Changing field 'WPAddress.name'
        db.alter_column('django_wepay_address', 'name', self.gf('django.db.models.fields.CharField')(max_length=128))

        # Changing field 'WPAddress.address1'
        db.alter_column('django_wepay_address', 'address1', self.gf('django.db.models.fields.CharField')(max_length=64))

        # Changing field 'WPAddress.address2'
        db.alter_column('django_wepay_address', 'address2', self.gf('django.db.models.fields.CharField')(max_length=64))

        # Changing field 'WPAddress.country'
        db.alter_column('django_wepay_address', 'country', self.gf('django.db.models.fields.CharField')(max_length=32))

        # Changing field 'WPWithdrawal.state'
        db.alter_column('django_wepay_withdrawal', 'state', self.gf('django.db.models.fields.CharField')(max_length=16))

        # Changing field 'WPUser.access_token'
        db.alter_column('django_wepay_user', 'access_token', self.gf('django.db.models.fields.CharField')(max_length=128))

        # Changing field 'WPUser.state'
        db.alter_column('django_wepay_user', 'state', self.gf('django.db.models.fields.CharField')(max_length=16))

        # Changing field 'WPAccount.verification_state'
        db.alter_column('django_wepay_account', 'verification_state', self.gf('django.db.models.fields.CharField')(max_length=11))

        # Changing field 'WPAccount.type'
        db.alter_column('django_wepay_account', 'type', self.gf('django.db.models.fields.CharField')(max_length=11))

        # Changing field 'WPAccount.name'
        db.alter_column('django_wepay_account', 'name', self.gf('django.db.models.fields.CharField')(max_length=128))

        # Changing field 'WPCheckout.fee_payer'
        db.alter_column('django_wepay_checkout', 'fee_payer', self.gf('django.db.models.fields.CharField')(max_length=5))

        # Changing field 'WPCheckout.state'
        db.alter_column('django_wepay_checkout', 'state', self.gf('django.db.models.fields.CharField')(max_length=16))

        # Changing field 'WPPreapproval.period'
        db.alter_column('django_wepay_preapproval', 'period', self.gf('django.db.models.fields.CharField')(max_length=9))

        # Changing field 'WPPreapproval.state'
        db.alter_column('django_wepay_preapproval', 'state', self.gf('django.db.models.fields.CharField')(max_length=8))

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'django_wepay.wpaccount': {
            'Meta': {'ordering': "['-create_datetime']", 'object_name': 'WPAccount', 'db_table': "'django_wepay_account'"},
            'account_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'account_uri': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'available_balance': ('django_wepay.models_base.MoneyField', [], {'default': '0', 'max_digits': '11', 'decimal_places': '2'}),
            'create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '2047'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'payment_limit': ('django_wepay.models_base.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'pending_balance': ('django_wepay.models_base.MoneyField', [], {'default': '0', 'max_digits': '11', 'decimal_places': '2'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['django_wepay.WPUser']"}),
            'verification_state': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'verification_uri': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        u'django_wepay.wpaddress': {
            'Meta': {'object_name': 'WPAddress', 'db_table': "'django_wepay_address'"},
            'address1': ('django.db.models.fields.CharField', [], {'max_length': '63'}),
            'address2': ('django.db.models.fields.CharField', [], {'max_length': '63', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '63'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '63'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '127', 'blank': 'True'}),
            'state': ('django_localflavor_us.models.USStateField', [], {'max_length': '2'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        u'django_wepay.wpcheckout': {
            'Meta': {'ordering': "['-create_time']", 'object_name': 'WPCheckout', 'db_table': "'django_wepay_checkout'"},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['django_wepay.WPAccount']"}),
            'amount': ('django_wepay.models_base.MoneyField', [], {'max_digits': '11', 'decimal_places': '2'}),
            'amount_refunded': ('django_wepay.models_base.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'app_fee': ('django_wepay.models_base.MoneyField', [], {'max_digits': '11', 'decimal_places': '2'}),
            'auto_capture': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cancel_reason': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'checkout_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'create_time': ('django.db.models.fields.IntegerField', [], {}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'fee': ('django_wepay.models_base.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'fee_payer': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'gross': ('django_wepay.models_base.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'payer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'}),
            'payer_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'payer_name': ('django.db.models.fields.CharField', [], {'max_length': '61'}),
            'preapproval': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['django_wepay.WPPreapproval']", 'null': 'True'}),
            'refund_reason': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'require_shipping': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'shipping_address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['django_wepay.WPAddress']", 'null': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        u'django_wepay.wppreapproval': {
            'Meta': {'ordering': "['-create_time']", 'object_name': 'WPPreapproval', 'db_table': "'django_wepay_preapproval'"},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['django_wepay.WPAccount']"}),
            'amount': ('django_wepay.models_base.MoneyField', [], {'max_digits': '11', 'decimal_places': '2'}),
            'app_fee': ('django_wepay.models_base.MoneyField', [], {'max_digits': '11', 'decimal_places': '2'}),
            'create_time': ('django.db.models.fields.IntegerField', [], {}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'end_time': ('django.db.models.fields.IntegerField', [], {}),
            'fee_payer': ('django.db.models.fields.CharField', [], {'default': "'payer'", 'max_length': '5'}),
            'manage_uri': ('django_wepay.models_base.URLField', [], {'max_length': '2083'}),
            'payer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'}),
            'payer_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'payer_name': ('django.db.models.fields.CharField', [], {'max_length': '61'}),
            'period': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'preapproval_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'preapproval_uri': ('django_wepay.models_base.URLField', [], {'max_length': '2083'}),
            'require_shipping': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'shipping_address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['django_wepay.WPAddress']", 'null': 'True'}),
            'start_time': ('django.db.models.fields.IntegerField', [], {}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        u'django_wepay.wpuser': {
            'Meta': {'ordering': "['-create_datetime']", 'object_name': 'WPUser', 'db_table': "'django_wepay_user'"},
            'access_token': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'create_datetime': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'expires': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'owners': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'user_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'user_name': ('django.db.models.fields.CharField', [], {'max_length': '61'})
        },
        u'django_wepay.wpwithdrawal': {
            'Meta': {'ordering': "['-create_time']", 'object_name': 'WPWithdrawal', 'db_table': "'django_wepay_withdrawal'"},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['django_wepay.WPAccount']"}),
            'amount': ('django_wepay.models_base.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'create_time': ('django.db.models.fields.IntegerField', [], {}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'recipient_confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'withdrawal_id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'withdrawal_uri': ('django_wepay.models_base.URLField', [], {'max_length': '2083'})
        }
    }

    complete_apps = ['django_wepay']