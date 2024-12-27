Quart-CORS
==========

|Build Status| |pypi| |python| |license|

Quart-CORS is an extension for `Quart
<https://github.com/pgjones/quart>`_ to enable and control `Cross
Origin Resource Sharing <http://www.w3.org/TR/cors/>`_, CORS (also
known as access control).

CORS is required to share resources in browsers due to the `Same
Origin Policy <https://en.wikipedia.org/wiki/Same-origin_policy>`_
which prevents resources being used from a different origin. An origin
in this case is defined as the scheme, host and port combined and a
resource corresponds to a path.

In practice the Same Origin Policy means that a browser visiting
``http://quart.com`` will prevent the response of ``GET
http://api.com`` being read. It will also prevent requests such as
``POST http://api.com``. Note that CORS applies to browser initiated
requests, non-browser clients such as ``requests`` are not subject to
CORS restrictions.

CORS allows a server to indicate to a browser that certain resources
can be used, contrary to the Same Origin Policy. It does so via
access-control headers that inform the browser how the resource can be
used. For GET requests these headers are sent in the response. For
non-GET requests the browser must ask the server for the
access-control headers before sending the actual request, it does so
via a preflight OPTIONS request.

The Same Origin Policy does not apply to WebSockets, and hence there
is no need for CORS. Instead the server alone is responsible for
deciding if the WebSocket is allowed and it should do so by inspecting
the WebSocket-request origin header.

Simple (GET) requests should return CORS headers specifying the
origins that are allowed to use the resource (response). This can be
any origin, ``*`` (wildcard), or a list of specific origins. The
response should also include a CORS header specifying whether
response-credentials e.g. cookies can be used. Note that if credential
sharing is allowed the allowed origins must be specific and not a
wildcard.

Preflight requests should return CORS headers specifying the origins
allowed to use the resource, the methods and headers allowed to be
sent in a request to the resource, whether response credentials can be
used, and finally which response headers can be used.

Note that certain actions are allowed in the Same Origin Policy such
as embedding e.g. ``<img src="http://api.com/img.gif">`` and simple
POSTs. For the purposes of this readme though these complications are
ignored.

The CORS access control response headers are,

================================ ===========================================================
Header name                      Meaning
-------------------------------- -----------------------------------------------------------
Access-Control-Allow-Origin      Origins that are allowed to use the resource.
Access-Control-Allow-Credentials Can credentials be shared.
Access-Control-Allow-Methods     Methods that may be used in requests to the resource.
Access-Control-Allow-Headers     Headers that may be sent in requests to the resource.
Access-Control-Expose-Headers    Headers that may be read in the response from the resource.
Access-Control-Max-Age           Maximum age to cache the CORS headers for the resource.
================================ ===========================================================

Quart-CORS uses the same naming (without the Access-Control prefix)
for it's arguments and settings when they relate to the same meaning.


Installation
------------

Quart-CORS can be installed using pip or your favorite python package manager:

.. code-block:: console

    pip install quart-cors


Usage
-----

To add CORS access control headers to all of the routes in the
application, simply apply the ``cors`` function to the application, or
to a specific blueprint,

.. code-block:: python

    from quart_cors import cors

    app = Quart(__name__)
    app = cors(app, **settings)

    blueprint = Blueprint(__name__)
    blueprint = cors(blueprint, **settings)

alternatively if you wish to add CORS selectively by resource, apply
the ``route_cors`` function to a route, or the ``websocket_cors``
function to a WebSocket,

.. code-block:: python

    from quart_cors import route_cors

    @app.route('/')
    @route_cors(**settings)
    async def handler():
        ...

    @app.websocket('/')
    @websocket_cors(allow_origin=...)
    async def handler():
        ...

The ``settings`` are these arguments,

==================== ====================================================
Argument             type
-------------------- ----------------------------------------------------
allow_origin         Union[Set[Union[Pattern, str]], Union[Pattern, str]]
allow_credentials    bool
allow_methods        Union[Set[str], str]
allow_headers        Union[Set[str], str]
expose_headers       Union[Set[str], str]
max_age              Union[int, flot, timedelta]
send_origin_wildcard bool
==================== ====================================================

which correspond to the CORS headers noted above (bar
``send_origin_wildcard``). The ``send_origin_wildcard`` argument
specifies whether to send a wildcard or echo the request origin in the
allow origin header. Note that all settings are optional and defaults
can be specified in the application configuration,

=============================== ========================
Configuration key               type
------------------------------- ------------------------
QUART_CORS_ALLOW_ORIGIN         Set[Union[Pattern, str]]
QUART_CORS_ALLOW_CREDENTIALS    bool
QUART_CORS_ALLOW_METHODS        Set[str]
QUART_CORS_ALLOW_HEADERS        Set[str]
QUART_CORS_EXPOSE_HEADERS       Set[str]
QUART_CORS_MAX_AGE              float
QUART_CORS_SEND_ORIGIN_WILDCARD bool
=============================== ========================

The ``websocket_cors`` decorator only takes ``allow_origin`` and
``send_origin_wildcard`` arguments which defines the origins that are
allowed to use the WebSocket and whether a wildcard should be sent in
the allow origin header. A WebSocket request from a disallowed origin
will be responded to with a 400 response.

The ``allow_origin`` origins should be the origin only (no path, query
strings or fragments) i.e. ``https://quart.com`` not
``https://quart.com/``.

The ``cors_exempt`` decorator can be used in conjunction with ``cors``
to exempt a websocket handler or view function from cors. You can find
a usage example in "Simple examples" section down below.

Simple examples
~~~~~~~~~~~~~~~

To allow an app to be used from any origin (not recommended as it is
too permissive),

.. code-block:: python

    app = Quart(__name__)
    app = cors(app, allow_origin="*")

To allow a route or WebSocket to be used from another specific domain,
``https://quart.com``,

.. code-block:: python

    @app.route('/')
    @route_cors(allow_origin="https://quart.com")
    async def handler():
        ...

    @app.websocket('/')
    @websocket_cors(allow_origin="https://quart.com")
    async def handler():
        ...

To allow a route or WebSocket to be used from any subdomain (but not
the domain itself) of ``quart.com``,

.. code-block:: python

    @app.route('/')
    @route_cors(allow_origin=re.compile(r"https:\/\/.*\.quart\.com"))
    async def handler():
        ...

    @app.websocket('/')
    @websocket_cors(allow_origin=re.compile(r"https:\/\/.*\.quart\.com"))
    async def handler():
        ...

To exempt a WebSocket handler from CORS,

.. code-block:: python

    @app.websocket('/')
    @cors_exempt
    async def handler():
        ...

To allow a JSON POST request to an API route, from ``https://quart.com``,

.. code-block:: python

    @app.route('/', methods=["POST"])
    @route_cors(
        allow_headers=["content-type"],
        allow_methods=["POST"],
        allow_origin=["https://quart.com"],
    )
    async def handler():
        data = await request.get_json()
        ...

Contributing
------------

Quart-CORS is developed on `GitHub
<https://github.com/pgjones/quart-cors>`_. You are very welcome to
open `issues <https://github.com/pgjones/quart-cors/issues>`_ or
propose `merge requests
<https://github.com/pgjones/quart-cors/merge_requests>`_.

Testing
~~~~~~~

The best way to test Quart-CORS is with Tox,

.. code-block:: console

    $ pip install tox
    $ tox

this will check the code style and run the tests.

Help
----

This README is the best place to start, after that try opening an
`issue <https://github.com/pgjones/quart-cors/issues>`_.


.. |Build Status| image:: https://github.com/pgjones/quart-cors/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/pgjones/quart-cors/commits/main

.. |pypi| image:: https://img.shields.io/pypi/v/quart-cors.svg
   :target: https://pypi.python.org/pypi/Quart-CORS/

.. |python| image:: https://img.shields.io/pypi/pyversions/quart-cors.svg
   :target: https://pypi.python.org/pypi/Quart-CORS/

.. |license| image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://github.com/pgjones/quart-cors/blob/main/LICENSE
