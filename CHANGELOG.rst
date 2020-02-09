0.3.0 2020-02-09
----------------

* Support Python 3.8.
* Support Quart >= 0.11.1 - with this only a single origin (or
  wildcard) can be returned as the Access-Control-Allow-Origin header,
  as per the specification.

0.2.0 2019-08-02
----------------

* Move files to within a quart_cors folder to ensure the py.typed file
  is picked up.
* Drop support for Python 3.6.
* Add a websocket_cors function that checks the origin and will
  respond with 400 if not an allowed origin.

0.1.3 2019-04-22
----------------

* Add py.typed for PEP 561 compliance.

0.1.2 2019-01-29
----------------

* Bugfix allow all request_headers when allow_headers is set to "*".

0.1.1 2018-12-09
----------------

* Bumped minimum Quart version to 0.6.11 due to a bug in Quart.

0.1.0 2018-06-11
----------------

* Released initial alpha version.
