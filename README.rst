Quart-CORS
==========

|Build Status| |pypi| |python| |license|

Quart-CORS is an extension for `Quart
<https://gitlab.com/pgjones/quart>`_ to handle `Cross Origin Resource
Sharing <http://www.w3.org/TR/cors/>`_, CORS (also known as access
control).

CORS is required to share resources in browsers due to the `Same
Origin Policy <https://en.wikipedia.org/wiki/Same-origin_policy>`_
which prevents resources being read and limits write actions from a
different origin. An origin in this case is defined as the scheme,
host and port combination.

In practice the Same Origin Policy means that a browser visiting
``http://quart.com`` will prevent the response of ``GET
http://api.com`` being read. It will also prevent requests such as
``POST http://api.com``. Note that embedding is allowed e.g. ``<img
src="http://api.com/img.gif">``.

CORS allows the server to indicate to the browser that certain
resources can be used. It does so for GET requests by returning
headers that indicate the origins that can use the resource whereas
for other requests the browser will send a preflight OPTIONS request
and then inspect the headers in the response.

Simple (GET) requests should return CORS headers specifying the
allowed origins (which can be any origin, ``*``) and whether
credentials should be shared. If credentials can be shared the origins
must be specific and not a wildcard.

Preflight requests should return CORS headers specifying the allowed
origins, methods and headers in the request, whehter credentials
should be shared and what response headers should be exposed.

Usage
-----

To add CORS access control headers to all of the routes in the
application, simply apply the ``cors`` function to the application,

.. code-block:: python

    app = Quart(__name__)
    app = cors(app)

alternatively if you wish to add CORS selectively either apply the
``cors`` function to a blueprint or the ``route_cors`` function to
a route,

.. code-block:: python

    blueprint = Blueprint(__name__)
    blueprint = cors(blueprint)

    @blueprint.route('/')
    @route_cors()
    async def handler():
        ...

In addition defaults can be specified in the application
configuration,

============================ ========
Configuration key            type
---------------------------- --------
QUART_CORS_ALLOW_CREDENTIALS bool
QUART_CORS_ALLOW_HEADERS     Set[str]
QUART_CORS_ALLOW_METHODS     Set[str]
QUART_CORS_ALLOW_ORIGIN      Set[str]
QUART_CORS_EXPOSE_HEADERS    Set[str]
QUART_CORS_MAX_AGE           float
============================ ========

Both the ``cors`` and ``route_cors`` functions take these arguments,

================= ===========================
Argument          type
----------------- ---------------------------
allow_credentials bool
allow_headers     Union[Set[str], str]
allow_methods     Union[Set[str], str]
allow_origin      Union[Set[str], str]
expose_headers    Union[Set[str], str]
max_age           Union[int, flot, timedelta]
================= ===========================

.. note::

   The Same Origin Policy does not apply to websockets, and hence this
   extension does not add CORS headers to websocket routes. In
   addition the ``route_cors`` function should not be used on a
   websocket route.

Contributing
------------

Quart-CORS is developed on `GitLab
<https://gitlab.com/pgjones/quart-cors>`_. You are very welcome to
open `issues <https://gitlab.com/pgjones/quart-cors/issues>`_ or
propose `merge requests
<https://gitlab.com/pgjones/quart-cors/merge_requests>`_.

Testing
~~~~~~~

The best way to test Quart-CORS is with Tox,

.. code-block:: console

    $ pipenv install tox
    $ tox

this will check the code style and run the tests.

Help
----

This README is the best place to start, after that try opening an
`issue <https://gitlab.com/pgjones/quart-cors/issues>`_.


.. |Build Status| image:: https://gitlab.com/pgjones/quart-cors/badges/master/build.svg
   :target: https://gitlab.com/pgjones/quart-cors/commits/master

.. |pypi| image:: https://img.shields.io/pypi/v/quart-cors.svg
   :target: https://pypi.python.org/pypi/Quart-CORS/

.. |python| image:: https://img.shields.io/pypi/pyversions/quart-cors.svg
   :target: https://pypi.python.org/pypi/Quart-CORS/

.. |license| image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://gitlab.com/pgjones/quart-cors/blob/master/LICENSE
