# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'WPAddress'
        db.create_table('django_wepay_address', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('address1', self.gf('django.db.models.fields.CharField')(max_length=63)),
            ('address2', self.gf('django.db.models.fields.CharField')(max_length=63, blank=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=63)),
            ('state', self.gf('django_localflavor_us.models.USStateField')(max_length=2)),
            ('zip', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=63)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=127, blank=True)),
        ))
        db.send_create_signal(u'django_wepay', ['WPAddress'])

        # Adding model 'WPUser'
        db.create_table('django_wepay_user', (
            ('create_datetime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('user_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('access_token', self.gf('django.db.models.fields.CharField')(max_length=127)),
            ('user_name', self.gf('django.db.models.fields.CharField')(max_length=61)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('expires', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal(u'django_wepay', ['WPUser'])

        # Adding M2M table for field owners on 'WPUser'
        m2m_table_name = db.shorten_name('django_wepay_user_owners')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('wpuser', models.ForeignKey(orm[u'django_wepay.wpuser'], null=False)),
            ('user', models.ForeignKey(orm[u'accounts.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['wpuser_id', 'user_id'])

        # Adding model 'WPAccount'
        db.create_table('django_wepay_account', (
            ('create_datetime', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('account_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=127)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=2047, blank=True)),
            ('account_uri', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('payment_limit', self.gf('django_wepay.models_base.MoneyField')(null=True, max_digits=11, decimal_places=2)),
            ('verification_state', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('pending_balance', self.gf('django_wepay.models_base.MoneyField')(default=0, max_digits=11, decimal_places=2)),
            ('available_balance', self.gf('django_wepay.models_base.MoneyField')(default=0, max_digits=11, decimal_places=2)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django_wepay.WPUser'])),
            ('verification_uri', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
        ))
        db.send_create_signal(u'django_wepay', ['WPAccount'])

        # Adding model 'WPPreapproval'
        db.create_table('django_wepay_preapproval', (
            ('payer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.User'], null=True)),
            ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('preapproval_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('preapproval_uri', self.gf('django_wepay.models_base.URLField')(max_length=2083)),
            ('manage_uri', self.gf('django_wepay.models_base.URLField')(max_length=2083)),
            ('account', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django_wepay.WPAccount'])),
            ('amount', self.gf('django_wepay.models_base.MoneyField')(max_digits=11, decimal_places=2)),
            ('fee_payer', self.gf('django.db.models.fields.CharField')(default='payer', max_length=5)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('app_fee', self.gf('django_wepay.models_base.MoneyField')(max_digits=11, decimal_places=2)),
            ('period', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('start_time', self.gf('django.db.models.fields.IntegerField')()),
            ('end_time', self.gf('django.db.models.fields.IntegerField')()),
            ('payer_email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('payer_name', self.gf('django.db.models.fields.CharField')(max_length=61)),
            ('require_shipping', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('shipping_address', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django_wepay.WPAddress'], null=True)),
            ('create_time', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'django_wepay', ['WPPreapproval'])

        # Adding model 'WPCheckout'
        db.create_table('django_wepay_checkout', (
            ('payer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.User'], null=True)),
            ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('checkout_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('account', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django_wepay.WPAccount'])),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('amount', self.gf('django_wepay.models_base.MoneyField')(max_digits=11, decimal_places=2)),
            ('fee', self.gf('django_wepay.models_base.MoneyField')(null=True, max_digits=11, decimal_places=2)),
            ('gross', self.gf('django_wepay.models_base.MoneyField')(null=True, max_digits=11, decimal_places=2)),
            ('app_fee', self.gf('django_wepay.models_base.MoneyField')(max_digits=11, decimal_places=2)),
            ('fee_payer', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('payer_email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('payer_name', self.gf('django.db.models.fields.CharField')(max_length=61)),
            ('cancel_reason', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('refund_reason', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('auto_capture', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('require_shipping', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('shipping_address', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django_wepay.WPAddress'], null=True)),
            ('amount_refunded', self.gf('django_wepay.models_base.MoneyField')(null=True, max_digits=11, decimal_places=2)),
            ('create_time', self.gf('django.db.models.fields.IntegerField')()),
            ('preapproval', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django_wepay.WPPreapproval'], null=True)),
        ))
        db.send_create_signal(u'django_wepay', ['WPCheckout'])

        # Adding model 'WPWithdrawal'
        db.create_table('django_wepay_withdrawal', (
            ('deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('withdrawal_id', self.gf('django.db.models.fields.IntegerField')(primary_key=True)),
            ('account', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django_wepay.WPAccount'])),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('withdrawal_uri', self.gf('django_wepay.models_base.URLField')(max_length=2083)),
            ('amount', self.gf('django_wepay.models_base.MoneyField')(null=True, max_digits=11, decimal_places=2)),
            ('note', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('recipient_confirmed', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('create_time', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'django_wepay', ['WPWithdrawal'])


    def backwards(self, orm):
        # Deleting model 'WPAddress'
        db.delete_table('django_wepay_address')

        # Deleting model 'WPUser'
        db.delete_table('django_wepay_user')

        # Removing M2M table for field owners on 'WPUser'
        db.delete_table(db.shorten_name('django_wepay_user_owners'))

        # Deleting model 'WPAccount'
        db.delete_table('django_wepay_account')

        # Deleting model 'WPPreapproval'
        db.delete_table('django_wepay_preapproval')

        # Deleting model 'WPCheckout'
        db.delete_table('django_wepay_checkout')

        # Deleting model 'WPWithdrawal'
        db.delete_table('django_wepay_withdrawal')


    models = {
        u'accounts.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('crowdsite.models.fields.CrowdSmartImageField', [], {'max_length': '100', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
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
            'description': ('django.db.models.fields.CharField', [], {'max_length': '2047', 'blank': 'True'}),
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
            'payer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.User']", 'null': 'True'}),
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
            'payer': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.User']", 'null': 'True'}),
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
            'owners': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['accounts.User']", 'symmetrical': 'False'}),
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