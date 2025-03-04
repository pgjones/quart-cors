0.8.0 2024-12-27
----------------

* Add the ability to control origin wildcard sending as a wildcard
  seen in the allow origin header can be considered dangerous by some.
* Add ``cors_exempt`` to top level package import.
* Improve the typing througout.
* Support Python 3.13, and 3.12 drop Python 3.8 and 3.7.

0.7.0 2023-09-23
----------------

* Send Vary: Origin for non-CORS requests.

0.6.0 2023-01-21
----------------

* Add the ability to exempt routes/websockets from cors.
* Ensure header name comparison is based on lowercased header names.
* Much improve the typing, leading to more accurate type checking.
* Officially support Python 3.10, and Python 3.11.
* Switch to GitHub rather than GitLab.

0.5.0 2021-05-11
----------------

* Support Quart 0.15 as the minimum version.

0.4.0 2021-03-09
----------------

* Support Python 3.9.
* Allow the allowed origin to be a regex pattern (or iterable
  thereof).
* Bugfix crash when sending OPTIONS with missing
  Access-Control-Allow-Origin header.

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
