# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Account.callback_uri'
        db.add_column('djwepay_account', 'callback_uri',
                      self.gf('django.db.models.fields.URLField')(default='', max_length=200, blank=True),
                      keep_default=False)

        # Adding field 'Preapproval.callback_uri'
        db.add_column('djwepay_preapproval', 'callback_uri',
                      self.gf('django.db.models.fields.URLField')(default='', max_length=200, blank=True),
                      keep_default=False)

        # Adding field 'Withdrawal.callback_uri'
        db.add_column('djwepay_withdrawal', 'callback_uri',
                      self.gf('django.db.models.fields.URLField')(default='', max_length=200, blank=True),
                      keep_default=False)

        # Adding field 'Checkout.callback_uri'
        db.add_column('djwepay_checkout', 'callback_uri',
                      self.gf('django.db.models.fields.URLField')(default='', max_length=200, blank=True),
                      keep_default=False)

        # Adding field 'User.callback_uri'
        db.add_column('djwepay_user', 'callback_uri',
                      self.gf('django.db.models.fields.URLField')(default='', max_length=200, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Account.callback_uri'
        db.delete_column('djwepay_account', 'callback_uri')

        # Deleting field 'Preapproval.callback_uri'
        db.delete_column('djwepay_preapproval', 'callback_uri')

        # Deleting field 'Withdrawal.callback_uri'
        db.delete_column('djwepay_withdrawal', 'callback_uri')

        # Deleting field 'Checkout.callback_uri'
        db.delete_column('djwepay_checkout', 'callback_uri')

        # Deleting field 'User.callback_uri'
        db.delete_column('djwepay_user', 'callback_uri')


    models = {
        u'accounts.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '75'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'geolocation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['gisgmaps.GeoLocation']", 'null': 'True'}),
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
        u'djwepay.account': {
            'Meta': {'object_name': 'Account'},
            'account_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'available_balance': ('djwepay.fields.MoneyField', [], {'default': '0', 'max_digits': '11', 'decimal_places': '2'}),
            'callback_uri': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'create_time': ('django.db.models.fields.BigIntegerField', [], {}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'date_removed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'disputed_amount': ('djwepay.fields.MoneyField', [], {'default': '0', 'max_digits': '11', 'decimal_places': '2'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'payment_limit': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'pending_amount': ('djwepay.fields.MoneyField', [], {'default': '0', 'max_digits': '11', 'decimal_places': '2'}),
            'pending_balance': ('djwepay.fields.MoneyField', [], {'default': '0', 'max_digits': '11', 'decimal_places': '2'}),
            'reference_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'reserved_amount': ('djwepay.fields.MoneyField', [], {'default': '0', 'max_digits': '11', 'decimal_places': '2'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['djwepay.User']"}),
            'verification_state': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        u'djwepay.app': {
            'Meta': {'object_name': 'App'},
            'access_token': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'client_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'client_secret': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'date_removed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'gaq_domains': ('json_field.fields.JSONField', [], {'default': "u'null'", 'blank': 'True'}),
            'production': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'theme_object': ('json_field.fields.JSONField', [], {'default': "u'null'", 'blank': 'True'})
        },
        u'djwepay.checkout': {
            'Meta': {'object_name': 'Checkout'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['djwepay.Account']"}),
            'amount': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'amount_refunded': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'app_fee': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'auto_capture': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'callback_uri': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'cancel_reason': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'checkout_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'create_time': ('django.db.models.fields.BigIntegerField', [], {}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'date_removed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'fee': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'fee_payer': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'gross': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'long_description': ('django.db.models.fields.CharField', [], {'max_length': '2047', 'blank': 'True'}),
            'mode': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'payee': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'wepay_payee_checkouts'", 'null': 'True', 'to': u"orm['accounts.User']"}),
            'payer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'wepay_payer_checkouts'", 'null': 'True', 'to': u"orm['accounts.User']"}),
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
            'auth_users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'wepay_credit_card'", 'null': 'True', 'to': u"orm['accounts.User']"}),
            'credit_card_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'credit_card_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'date_removed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'reference_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'user_name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'djwepay.preapproval': {
            'Meta': {'object_name': 'Preapproval'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['djwepay.Account']"}),
            'amount': ('djwepay.fields.MoneyField', [], {'max_digits': '11', 'decimal_places': '2'}),
            'app_fee': ('djwepay.fields.MoneyField', [], {'max_digits': '11', 'decimal_places': '2'}),
            'auto_recur': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'callback_uri': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'create_time': ('django.db.models.fields.BigIntegerField', [], {}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'date_removed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.BigIntegerField', [], {}),
            'fee_payer': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'frequency': ('django.db.models.fields.IntegerField', [], {}),
            'last_checkout': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'to': u"orm['djwepay.Checkout']"}),
            'last_checkout_time': ('django.db.models.fields.BigIntegerField', [], {}),
            'long_description': ('django.db.models.fields.CharField', [], {'max_length': '2047', 'blank': 'True'}),
            'mode': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'next_due_time': ('django.db.models.fields.BigIntegerField', [], {}),
            'payee': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'wepay_payee_preapprovals'", 'null': 'True', 'to': u"orm['accounts.User']"}),
            'payer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'wepay_payer_preapprovals'", 'null': 'True', 'to': u"orm['accounts.User']"}),
            'payer_email': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'blank': 'True'}),
            'payer_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'period': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'preapproval_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'reference_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'shipping_address': ('json_field.fields.JSONField', [], {'default': "u'null'", 'null': 'True'}),
            'shipping_fee': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'short_description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'start_time': ('django.db.models.fields.BigIntegerField', [], {}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'tax': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'})
        },
        u'djwepay.user': {
            'Meta': {'object_name': 'User'},
            'access_token': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'auth_users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'wepay_users'", 'symmetrical': 'False', 'to': u"orm['accounts.User']"}),
            'callback_uri': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'date_removed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '255'}),
            'expires_in': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'user_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'user_name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'djwepay.withdrawal': {
            'Meta': {'object_name': 'Withdrawal'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['djwepay.Account']"}),
            'amount': ('djwepay.fields.MoneyField', [], {'null': 'True', 'max_digits': '11', 'decimal_places': '2'}),
            'callback_uri': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'create_time': ('django.db.models.fields.BigIntegerField', [], {}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'date_removed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'initiator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'wepay_initiator_withdrawals'", 'null': 'True', 'to': u"orm['accounts.User']"}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'recipient_confirmed': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'withdrawal_id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'})
        },
        u'gisgmaps.geolocation': {
            'Meta': {'object_name': 'GeoLocation'},
            'bounds_ne': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True'}),
            'bounds_sw': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True'}),
            'formatted_address': ('django.db.models.fields.CharField', [], {'max_length': '252', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'point': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'subcounty': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigerline.SubCounty']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'tigerline.county': {
            'Meta': {'object_name': 'County'},
            'aland': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'fips_55_class_code': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'fips_code': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'functional_status': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'kml_file': ('smart_fields.models.fields.SmartKMLField', [], {'max_length': '100', 'null': 'True'}),
            'legal_statistical_description': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'mpoly': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_and_description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigerline.State']", 'null': 'True'}),
            'state_fips_code': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        u'tigerline.state': {
            'Meta': {'ordering': "['name']", 'object_name': 'State'},
            'aland': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'division': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'fips_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '2'}),
            'id': ('django.db.models.fields.PositiveSmallIntegerField', [], {'primary_key': 'True'}),
            'kml_file': ('smart_fields.models.fields.SmartKMLField', [], {'max_length': '100', 'null': 'True'}),
            'mpoly': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'region': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'usps_code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '2', 'db_index': 'True'})
        },
        u'tigerline.subcounty': {
            'Meta': {'object_name': 'SubCounty'},
            'aland': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'county': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigerline.County']", 'null': 'True'}),
            'county_fips_code': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'fips_55_class_code': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'fips_code': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'functional_status': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'kml_file': ('smart_fields.models.fields.SmartKMLField', [], {'max_length': '100', 'null': 'True'}),
            'legal_statistical_description': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'mpoly': ('django.contrib.gis.db.models.fields.MultiPolygonField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name_and_description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['tigerline.State']", 'null': 'True'}),
            'state_fips_code': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        }
    }

    complete_apps = ['djwepay']