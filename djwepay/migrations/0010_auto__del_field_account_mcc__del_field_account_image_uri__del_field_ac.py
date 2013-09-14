# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Account.mcc'
        db.delete_column(u'djwepay_account', 'mcc')

        # Deleting field 'Account.image_uri'
        db.delete_column(u'djwepay_account', 'image_uri')

        # Deleting field 'Account.callback_uri'
        db.delete_column(u'djwepay_account', 'callback_uri')

        # Deleting field 'Preapproval.callback_uri'
        db.delete_column(u'djwepay_preapproval', 'callback_uri')

        # Deleting field 'Withdrawal.callback_uri'
        db.delete_column(u'djwepay_withdrawal', 'callback_uri')

        # Deleting field 'Checkout.callback_uri'
        db.delete_column(u'djwepay_checkout', 'callback_uri')


    def backwards(self, orm):
        # Adding field 'Account.mcc'
        db.add_column(u'djwepay_account', 'mcc',
                      self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'Account.image_uri'
        raise RuntimeError("Cannot reverse this migration. 'Account.image_uri' and its values cannot be restored.")
        # Adding field 'Account.callback_uri'
        db.add_column(u'djwepay_account', 'callback_uri',
                      self.gf('django.db.models.fields.URLField')(default='', max_length=2083, blank=True),
                      keep_default=False)

        # Adding field 'Preapproval.callback_uri'
        db.add_column(u'djwepay_preapproval', 'callback_uri',
                      self.gf('django.db.models.fields.URLField')(default='', max_length=2083, blank=True),
                      keep_default=False)

        # Adding field 'Withdrawal.callback_uri'
        db.add_column(u'djwepay_withdrawal', 'callback_uri',
                      self.gf('django.db.models.fields.URLField')(default='', max_length=2083, blank=True),
                      keep_default=False)

        # Adding field 'Checkout.callback_uri'
        db.add_column(u'djwepay_checkout', 'callback_uri',
                      self.gf('django.db.models.fields.URLField')(default='', max_length=2083, blank=True),
                      keep_default=False)


    models = {
        u'djwepay.account': {
            'Meta': {'object_name': 'Account'},
            'account_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'create_time': ('django.db.models.fields.BigIntegerField', [], {}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'gaq_domains': ('json_field.fields.JSONField', [], {'default': "u'null'"}),
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