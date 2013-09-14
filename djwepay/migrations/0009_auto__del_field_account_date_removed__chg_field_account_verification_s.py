# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Account.date_removed'
        db.delete_column(u'djwepay_account', 'date_removed')


        # Changing field 'Account.verification_state'
        db.alter_column('djwepay_account', 'verification_state', self.gf('django.db.models.fields.CharField')(max_length=255))

        # Changing field 'Account.state'
        db.alter_column('djwepay_account', 'state', self.gf('django.db.models.fields.CharField')(max_length=255))

        # Changing field 'Account.callback_uri'
        db.alter_column('djwepay_account', 'callback_uri', self.gf('django.db.models.fields.URLField')(max_length=2083))
        # Deleting field 'App.date_removed'
        db.delete_column(u'djwepay_app', 'date_removed')

        # Deleting field 'Preapproval.date_removed'
        db.delete_column(u'djwepay_preapproval', 'date_removed')

        # Deleting field 'Preapproval.payer'
        db.delete_column(u'djwepay_preapproval', 'payer_id')

        # Deleting field 'Preapproval.payee'
        db.delete_column(u'djwepay_preapproval', 'payee_id')


        # Changing field 'Preapproval.period'
        db.alter_column('djwepay_preapproval', 'period', self.gf('django.db.models.fields.CharField')(max_length=255))

        # Changing field 'Preapproval.state'
        db.alter_column('djwepay_preapproval', 'state', self.gf('django.db.models.fields.CharField')(max_length=255))

        # Changing field 'Preapproval.fee_payer'
        db.alter_column('djwepay_preapproval', 'fee_payer', self.gf('django.db.models.fields.CharField')(max_length=255))

        # Changing field 'Preapproval.mode'
        db.alter_column('djwepay_preapproval', 'mode', self.gf('django.db.models.fields.CharField')(max_length=255))

        # Changing field 'Preapproval.callback_uri'
        db.alter_column('djwepay_preapproval', 'callback_uri', self.gf('django.db.models.fields.URLField')(max_length=2083))
        # Deleting field 'Withdrawal.date_removed'
        db.delete_column(u'djwepay_withdrawal', 'date_removed')

        # Deleting field 'Withdrawal.initiator'
        db.delete_column(u'djwepay_withdrawal', 'initiator_id')


        # Changing field 'Withdrawal.state'
        db.alter_column('djwepay_withdrawal', 'state', self.gf('django.db.models.fields.CharField')(max_length=255))

        # Changing field 'Withdrawal.type'
        db.alter_column('djwepay_withdrawal', 'type', self.gf('django.db.models.fields.CharField')(max_length=255))

        # Changing field 'Withdrawal.callback_uri'
        db.alter_column('djwepay_withdrawal', 'callback_uri', self.gf('django.db.models.fields.URLField')(max_length=2083))
        # Deleting field 'CreditCard.date_removed'
        db.delete_column('djwepay_credit_card', 'date_removed')

        # Removing M2M table for field auth_users on 'CreditCard'
        db.delete_table(db.shorten_name('djwepay_credit_card_auth_users'))


        # Changing field 'CreditCard.state'
        db.alter_column('djwepay_credit_card', 'state', self.gf('django.db.models.fields.CharField')(max_length=255))
        # Deleting field 'Checkout.date_removed'
        db.delete_column(u'djwepay_checkout', 'date_removed')

        # Deleting field 'Checkout.payer'
        db.delete_column(u'djwepay_checkout', 'payer_id')

        # Deleting field 'Checkout.payee'
        db.delete_column(u'djwepay_checkout', 'payee_id')


        # Changing field 'Checkout.fee_payer'
        db.alter_column('djwepay_checkout', 'fee_payer', self.gf('django.db.models.fields.CharField')(max_length=255))

        # Changing field 'Checkout.mode'
        db.alter_column('djwepay_checkout', 'mode', self.gf('django.db.models.fields.CharField')(max_length=255))

        # Changing field 'Checkout.callback_uri'
        db.alter_column('djwepay_checkout', 'callback_uri', self.gf('django.db.models.fields.URLField')(max_length=2083))
        # Deleting field 'User.date_removed'
        db.delete_column(u'djwepay_user', 'date_removed')

        # Deleting field 'User.callback_uri'
        db.delete_column(u'djwepay_user', 'callback_uri')

        # Removing M2M table for field auth_users on 'User'
        db.delete_table(db.shorten_name(u'djwepay_user_auth_users'))


        # Changing field 'User.access_token'
        db.alter_column('djwepay_user', 'access_token', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'User.expires_in'
        db.alter_column('djwepay_user', 'expires_in', self.gf('django.db.models.fields.BigIntegerField')(null=True))

        # Changing field 'User.state'
        db.alter_column('djwepay_user', 'state', self.gf('django.db.models.fields.CharField')(max_length=255))

    def backwards(self, orm):
        # Adding field 'Account.date_removed'
        db.add_column(u'djwepay_account', 'date_removed',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)


        # Changing field 'Account.verification_state'
        db.alter_column('djwepay_account', 'verification_state', self.gf('django.db.models.fields.CharField')(max_length=15))

        # Changing field 'Account.state'
        db.alter_column('djwepay_account', 'state', self.gf('django.db.models.fields.CharField')(max_length=15))

        # Changing field 'Account.callback_uri'
        db.alter_column('djwepay_account', 'callback_uri', self.gf('django.db.models.fields.URLField')(max_length=200))
        # Adding field 'App.date_removed'
        db.add_column(u'djwepay_app', 'date_removed',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Preapproval.date_removed'
        db.add_column(u'djwepay_preapproval', 'date_removed',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Preapproval.payer'
        db.add_column(u'djwepay_preapproval', 'payer',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='wepay_payer_preapprovals', null=True, to=orm['accounts.User']),
                      keep_default=False)

        # Adding field 'Preapproval.payee'
        db.add_column(u'djwepay_preapproval', 'payee',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='wepay_payee_preapprovals', null=True, to=orm['accounts.User']),
                      keep_default=False)


        # Changing field 'Preapproval.period'
        db.alter_column('djwepay_preapproval', 'period', self.gf('django.db.models.fields.CharField')(max_length=15))

        # Changing field 'Preapproval.state'
        db.alter_column('djwepay_preapproval', 'state', self.gf('django.db.models.fields.CharField')(max_length=15))

        # Changing field 'Preapproval.fee_payer'
        db.alter_column('djwepay_preapproval', 'fee_payer', self.gf('django.db.models.fields.CharField')(max_length=15))

        # Changing field 'Preapproval.mode'
        db.alter_column('djwepay_preapproval', 'mode', self.gf('django.db.models.fields.CharField')(max_length=15))

        # Changing field 'Preapproval.callback_uri'
        db.alter_column('djwepay_preapproval', 'callback_uri', self.gf('django.db.models.fields.URLField')(max_length=200))
        # Adding field 'Withdrawal.date_removed'
        db.add_column(u'djwepay_withdrawal', 'date_removed',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Withdrawal.initiator'
        db.add_column(u'djwepay_withdrawal', 'initiator',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='wepay_initiator_withdrawals', null=True, to=orm['accounts.User']),
                      keep_default=False)


        # Changing field 'Withdrawal.state'
        db.alter_column('djwepay_withdrawal', 'state', self.gf('django.db.models.fields.CharField')(max_length=15))

        # Changing field 'Withdrawal.type'
        db.alter_column('djwepay_withdrawal', 'type', self.gf('django.db.models.fields.CharField')(max_length=15))

        # Changing field 'Withdrawal.callback_uri'
        db.alter_column('djwepay_withdrawal', 'callback_uri', self.gf('django.db.models.fields.URLField')(max_length=200))
        # Adding field 'CreditCard.date_removed'
        db.add_column('djwepay_credit_card', 'date_removed',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)

        # Adding M2M table for field auth_users on 'CreditCard'
        m2m_table_name = db.shorten_name('djwepay_credit_card_auth_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('creditcard', models.ForeignKey(orm[u'djwepay.creditcard'], null=False)),
            ('user', models.ForeignKey(orm[u'accounts.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['creditcard_id', 'user_id'])


        # Changing field 'CreditCard.state'
        db.alter_column('djwepay_credit_card', 'state', self.gf('django.db.models.fields.CharField')(max_length=15))
        # Adding field 'Checkout.date_removed'
        db.add_column(u'djwepay_checkout', 'date_removed',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Checkout.payer'
        db.add_column(u'djwepay_checkout', 'payer',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='wepay_payer_checkouts', null=True, to=orm['accounts.User']),
                      keep_default=False)

        # Adding field 'Checkout.payee'
        db.add_column(u'djwepay_checkout', 'payee',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name='wepay_payee_checkouts', null=True, to=orm['accounts.User']),
                      keep_default=False)


        # Changing field 'Checkout.fee_payer'
        db.alter_column('djwepay_checkout', 'fee_payer', self.gf('django.db.models.fields.CharField')(max_length=15))

        # Changing field 'Checkout.mode'
        db.alter_column('djwepay_checkout', 'mode', self.gf('django.db.models.fields.CharField')(max_length=15))

        # Changing field 'Checkout.callback_uri'
        db.alter_column('djwepay_checkout', 'callback_uri', self.gf('django.db.models.fields.URLField')(max_length=200))
        # Adding field 'User.date_removed'
        db.add_column(u'djwepay_user', 'date_removed',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'User.callback_uri'
        db.add_column(u'djwepay_user', 'callback_uri',
                      self.gf('django.db.models.fields.URLField')(default='', max_length=200, blank=True),
                      keep_default=False)

        # Adding M2M table for field auth_users on 'User'
        m2m_table_name = db.shorten_name(u'djwepay_user_auth_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_user', models.ForeignKey(orm[u'djwepay.user'], null=False)),
            ('to_user', models.ForeignKey(orm[u'accounts.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['from_user_id', 'to_user_id'])


        # User chose to not deal with backwards NULL issues for 'User.access_token'
        raise RuntimeError("Cannot reverse this migration. 'User.access_token' and its values cannot be restored.")

        # Changing field 'User.expires_in'
        db.alter_column('djwepay_user', 'expires_in', self.gf('django.db.models.fields.PositiveIntegerField')(null=True))

        # Changing field 'User.state'
        db.alter_column('djwepay_user', 'state', self.gf('django.db.models.fields.CharField')(max_length=15))

    models = {
        u'djwepay.account': {
            'Meta': {'object_name': 'Account'},
            'account_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'callback_uri': ('django.db.models.fields.URLField', [], {'max_length': '2083', 'blank': 'True'}),
            'create_time': ('django.db.models.fields.BigIntegerField', [], {}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'gaq_domains': ('json_field.fields.JSONField', [], {'default': "u'null'"}),
            'image_uri': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'mcc': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'payment_limit': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'reference_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'theme_object': ('json_field.fields.JSONField', [], {'default': "u'null'"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['djwepay.User']"}),
            'verification_state': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'djwepay.app': {
            'Meta': {'object_name': 'App'},
            'access_token': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'client_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'client_secret': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'gaq_domains': ('json_field.fields.JSONField', [], {'default': "u'null'"}),
            'production': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'theme_object': ('json_field.fields.JSONField', [], {'default': "u'null'"})
        },
        u'djwepay.checkout': {
            'Meta': {'object_name': 'Checkout'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['djwepay.Account']"}),
            'amount': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'amount_refunded': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'app_fee': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'auto_capture': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'callback_uri': ('django.db.models.fields.URLField', [], {'max_length': '2083', 'blank': 'True'}),
            'cancel_reason': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'checkout_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'create_time': ('django.db.models.fields.BigIntegerField', [], {}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'fee': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'fee_payer': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'gross': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'long_description': ('django.db.models.fields.CharField', [], {'max_length': '2047', 'blank': 'True'}),
            'mode': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'payer_email': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'blank': 'True'}),
            'payer_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'preapproval': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['djwepay.Preapproval']", 'null': 'True'}),
            'reference_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'refund_reason': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'require_shipping': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'shipping_address': ('json_field.fields.JSONField', [], {'default': "u'null'", 'null': 'True'}),
            'short_description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'tax': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'})
        },
        u'djwepay.creditcard': {
            'Meta': {'object_name': 'CreditCard', 'db_table': "'djwepay_credit_card'"},
            'credit_card_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'credit_card_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'reference_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user_name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'djwepay.preapproval': {
            'Meta': {'object_name': 'Preapproval'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['djwepay.Account']"}),
            'amount': ('djwepay.fields.MoneyField', [], {'max_digits': '11', 'decimal_places': '2'}),
            'app_fee': ('djwepay.fields.MoneyField', [], {'max_digits': '11', 'decimal_places': '2'}),
            'auto_recur': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'callback_uri': ('django.db.models.fields.URLField', [], {'max_length': '2083', 'blank': 'True'}),
            'create_time': ('django.db.models.fields.BigIntegerField', [], {}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.BigIntegerField', [], {}),
            'fee_payer': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'frequency': ('django.db.models.fields.IntegerField', [], {}),
            'last_checkout': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': u"orm['djwepay.Checkout']"}),
            'last_checkout_time': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'long_description': ('django.db.models.fields.CharField', [], {'max_length': '2047', 'blank': 'True'}),
            'mode': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'next_due_time': ('django.db.models.fields.BigIntegerField', [], {}),
            'payer_email': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'blank': 'True'}),
            'payer_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'period': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'preapproval_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'reference_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'shipping_address': ('json_field.fields.JSONField', [], {'default': "u'null'", 'null': 'True'}),
            'shipping_fee': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'short_description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'start_time': ('django.db.models.fields.BigIntegerField', [], {}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'tax': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'})
        },
        u'djwepay.user': {
            'Meta': {'object_name': 'User'},
            'access_token': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '255'}),
            'expires_in': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'user_name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'djwepay.withdrawal': {
            'Meta': {'object_name': 'Withdrawal'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['djwepay.Account']"}),
            'amount': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'callback_uri': ('django.db.models.fields.URLField', [], {'max_length': '2083', 'blank': 'True'}),
            'create_time': ('django.db.models.fields.BigIntegerField', [], {}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'recipient_confirmed': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'withdrawal_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['djwepay']