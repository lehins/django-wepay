######################################################################
django-wepay
######################################################################

**Django App for WePay http://www.wepay.com**

About
-----

If you start using WePay API you realize that there is a bunch of stuff needs to
be stored locally, so that was an actual motivation for creation of this
app. There is functionality for storing information for all objects in the
database. For each object you can choose to store only minimal fields,
all fields and/or add custom fields required for your app. It also handles `IPN
(instant payment notifications) <https://www.wepay.com/developer/tutorial/ipn>`_
for all supported objects. 

Status
------

Beta. Although it is used in production, some objects like credit card and
subscriptions haven't been thoroughly tested.

TODO
----

* Full Documentation.
* Rewrite all tests (first attempt at it was not great).
* Admin pages for all objects.

Requirements
------------

* Registered Application with WePay. (tailored for versions >= '2014-01-08')
* `Python WePay SDK <https://github.com/lehins/python-wepay>`_
* `Django >= 1.4 <https://www.djangoproject.com/>`_
* Cache framework properly configured for django

Features
--------

* Supports all WePay API calls.
* Customizable models for all objects.
* Ability to make API calls right from the model instance (prefills all known params).
* All lookup and create API calls automatically save changes in the database.
* IPN calls handling for all objects. 
* Signals are sent upon state change of all objects as well as upon an IPN call.
* Ability to change backend (communication module with WePay). Default backend features:
  * Protection from throttling (threadsafe with memcache)
  * Automatic storing of batch calls for later invocation.
  * Logging of WePay erros and/or all calls with params
  * Validation of all params before they are sent over to WePay.

Configuration
-------------

* Add 'djwepay' to ``INSTALLED_APPS``
* (Optionally) Extend and customize models, point to their location in
  ``WEPAY_MODELS``, run syncdb (or migrations). If this step omitted all models
  will be created.
* Add your WePay ``App`` to database by running (with --production flag for Production)::
    
    ./manage.py wepay_app_create
    
* Set ``WEPAY_APP_ID`` to the Client ID present in database.


Settings
--------

**Required:**

* ``WEPAY_APP_ID`` - WePay Application Client ID (required App model isntance
  stored in database for this id, use ``./manage.py wepay_app_create`` for that).

**Optional:**

* ``WEPAY_MODELS`` - a list of tuples ('object_name', 'app_name.ModelName') for
  objects you will be working with, ex

.. code-block:: python

    WEPAY_MODELS = (
        ('app', 'myapp.WePayApp'),
        ('user', 'myapp.WePayUser'),
        ('account', 'myapp.WePayAccount'),
        ('checkout', 'myapp.WePayCheckout'),
        ('preapproval', 'myapp.WePayPreapproval'),
        ('withdrawal', 'myapp.WePayWithdrawal'),
        # ('credit_card', 'djwepay.CreditCard), # if ommited default model will be used
        ('subscription_plan', None), # None - turns off the object. No db tables will be created.
        ('subscription', None),
        ('subscription_charge', None)
    )

* ``API_BACKEND`` - backend to be used for communication with WePay. Default is
  'djwepay.backends.default.WePay'
* ``DEFAULT_SCOPE`` - default WePay permissions, full by default.

**Default backend settings**

* ``WEPAY_DEBUG`` - if set to True and logging is setup will log every API
  call. Defaults to the ``DEBUG`` setting.
* ``WEPAY_THROTTLE_PROTECT`` - turns on/off throttle protection (default is True).
* ``WEPAY_THROTTLE_CALL_LIMIT`` - number of calls before your app will be
  throttled after. Default is 30.
* ``WEPAY_THROTTLE_TIMEOUT`` - throttle timespan. Default is 10 seconds.
* ``WEPAY_THROTTLE_CALL_KEY`` - cache key for storing throttling info.
* ``WEPAY_CACHE_BATCH_KEY_PREFIX`` - cache key prefix for storing batch calls
  and associated callbacks in cache, for later processing.
* ``WEPAY_DOMAIN`` - your site's domain, if ``None`` will use django's `sites` app.

