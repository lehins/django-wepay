import sys
from optparse import make_option
from django.core.management.base import BaseCommand
from django.utils.six.moves import input

from djwepay.api import get_wepay_model, API_BACKEND
from djwepay.utils import from_string_import

from wepay.exceptions import WePayError

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--production', default=False, action="store_true", dest='production',
                    help='Flag that App is registered in production environment.'),
        make_option('--client_id', default=None, dest='client_id', type="int",
                    help='Client ID of your App.'),
        make_option('--client_secret', default=None, dest='client_secret',
                    help='Client Secret of your App.'),
        make_option('--access_token', default=None, dest='access_token',
                    help='Access Token of the owner of the App.'),
        make_option('--account_id', default=None, dest='account_id', type="int",
                    help='Account ID of the account attached to your App.')
    )

    help = "Add a WePay API Application. All necessary API Keys you can find in your App " \
           "dashboard at https://www.wepay.com/login or at https://stage.wepay.com/login"


    def handle(self, *args, **kwargs):
        production = kwargs.get('production', False)
        client_id = kwargs.get('client_id')
        client_secret = kwargs.get('client_secret')
        access_token = kwargs.get('access_token')
        account_id = kwargs.get('account_id')
        try:
            while not client_id:
                client_id = input("client_id: ")
                try:
                    client_id = int(client_id)
                except (TypeError, ValueError):
                    self.stderr.write(
                        "\n'client_id' has to be an integer not: %s" % client_id)
                    client_id = None
            while not client_secret:
                client_secret = input("client_secret: ")
                if not client_secret:
                    self.stderr.write("\n'client_secret' is required.")
            while not access_token:
                access_token = input("access_token: ")
                if not access_token:
                    self.stderr.write("\n'access_token' is required.")
            while not account_id:
                try:
                    account_id = int(input("account_id: "))
                except (TypeError, ValueError):
                    self.stderr.write(
                        "\n'account_id' has to be an integer not: %s" % account_id)
                    account_id = None
        except KeyboardInterrupt:
            self.stderr.write("\nOperation cancelled.")
            sys.exit(1)

        if (production and access_token.startswith("STAGE_")) or \
           (not production and access_token.startswith("PRODUCTION_")):
            self.stderr.write("\nThere is a conflict: access_token doesn't correspond with "
                              "environment. production=%s and access_token='%s...' "
                              "Flag --production controls the environment."% 
                              (production, access_token[:14]))
            sys.exit(1)
            
        WePayBackend = from_string_import(API_BACKEND)
        api = WePayBackend(production=production, access_token=access_token)

        App = get_wepay_model('app')
        app = App(client_id=client_id, client_secret=client_secret)
        app.access_token = access_token
        app.api = api
        app.api_app()
        self.stdout.write(
            "Retrieved app with client_id: %s and status: %s" % (app.pk, app.status))

        User = get_wepay_model('user')
        user = User(access_token=access_token)
        user.api = api
        user.app = app
        user.api_user()
        self.stdout.write("Retrieved user: %s" % user)

        Account = get_wepay_model('account')
        account = Account(account_id=int(account_id))
        account.user = user
        account.api = api
        account.api_account()
        self.stdout.write("Retrieved account: %s" % account)

        app.user = user
        app.account = account
        app.save()
        self.stdout.write(
            "Successfully added new WePay App. If you choose to use it "
            "please set 'WEPAY_APP_ID=%s' in the settings.py module." % app.pk)
        
        
