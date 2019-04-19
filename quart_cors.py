from datetime import timedelta
from functools import partial, wraps
from typing import Any, Callable, Iterable, Optional, TypeVar, Union

from quart import Blueprint, current_app, make_response, Quart, request, Response
from quart.datastructures import HeaderSet, RequestAccessControl

__all__ = ("cors",)

DEFAULTS = {
    "QUART_CORS_ALLOW_CREDENTIALS": False,
    "QUART_CORS_ALLOW_HEADERS": ["*"],
    "QUART_CORS_ALLOW_METHODS": ["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"],
    "QUART_CORS_ALLOW_ORIGIN": ["*"],
    "QUART_CORS_EXPOSE_HEADERS": [""],
    "QUART_CORS_MAX_AGE": None,
}


def route_cors(
    *,
    allow_credentials: Optional[bool] = None,
    allow_headers: Optional[Iterable[str]] = None,
    allow_methods: Optional[Iterable[str]] = None,
    allow_origin: Optional[Iterable[str]] = None,
    expose_headers: Optional[Iterable[str]] = None,
    max_age: Optional[Union[timedelta, float, str]] = None,
    provide_automatic_options: bool = True,
) -> Callable:
    """A decorator to add the CORS access control headers.

    This should be used to wrap a route handler (or view function) to
    apply CORS headers to the route. Note that it is important that
    this decorator be wrapped by the route decorator and not vice,
    versa, as below.

    .. code-block:: python

        @app.route('/')
        @route_cors()
        async def index():
            ...

    Arguments:
        allow_credentials: If set the allow credentials header will
            be set, thereby allowing credentials to be shared. Note
            that this does not work with a wildcard origin
            argument.
        allow_headers: A list of headers, a regex or single header
            name, a cross origin request is allowed to access.
        allow_methods: The methods (list) or method (str) that a cross
            origin request can use.
        allow_origin: The origins from which cross origin requests are
            accepted. This is either a list, a regex or a single
            domain. Note the full domain including scheme is required.
        expose_headers: The additional headers (list) or header (str)
            to expose to the client of a cross origin request.
        max_age: The maximum time the response can be cached by the
            client.
        provide_automatic_options: If set the automatic OPTIONS
            response created by Quart will be overwriten by one
            created by Quart-CORS.

        send_wildcard: If set the allow origin response header is
            replaced with a wildcard rather than the actual
            origin. Requires the origins argument to also be '*'.
        vary_header: If set the Vary header will include Origin,
            allowing caching services to understand when to cache the
        always_send: Always send the access control headers on
            response, including when the request is missing an origin
            header.
            headers.

    """

    def decorator(func: Callable) -> Callable:
        if provide_automatic_options:
            func.required_methods = getattr(func, "required_methods", set())  # type: ignore
            func.required_methods.add("OPTIONS")  # type: ignore
            func.provide_automatic_options = False  # type: ignore

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal allow_credentials, allow_headers, allow_methods, allow_origin, expose_headers
            nonlocal max_age

            method = request.method
            access_control = request.access_control

            if provide_automatic_options and method == "OPTIONS":
                response = await current_app.make_default_options_response()
            else:
                response = await make_response(await func(*args, **kwargs))

            allow_credentials = allow_credentials or _get_config_or_default(
                "QUART_CORS_ALLOW_CREDENTIALS"
            )
            allow_headers = _sanitise_header_set(allow_headers, "QUART_CORS_ALLOW_HEADERS")
            allow_methods = _sanitise_header_set(allow_methods, "QUART_CORS_ALLOW_METHODS")
            allow_origin = _sanitise_header_set(allow_origin, "QUART_CORS_ALLOW_ORIGIN")
            expose_headers = _sanitise_header_set(expose_headers, "QUART_CORS_EXPOSE_HEADERS")
            max_age = _sanitise_max_age(max_age, "QUART_CORS_MAX_AGE")
            response = _apply_cors(
                access_control,
                method,
                response,
                allow_credentials=allow_credentials,
                allow_headers=allow_headers,
                allow_methods=allow_methods,
                allow_origin=allow_origin,
                expose_headers=expose_headers,
                max_age=max_age,
            )
            return response

        return wrapper

    return decorator


T = TypeVar("T", Blueprint, Quart)


def cors(
    app_or_blueprint: T,
    *,
    allow_credentials: Optional[bool] = None,
    allow_headers: Optional[Iterable[str]] = None,
    allow_methods: Optional[Iterable[str]] = None,
    allow_origin: Optional[Iterable[str]] = None,
    expose_headers: Optional[Iterable[str]] = None,
    max_age: Optional[Union[timedelta, float, str]] = None,
) -> T:
    """Apply the CORS access control headers to all routes.

    This should be used on a Quart (app) instance or a Blueprint
    instance to apply CORS headers to the associated routes.

    .. code-block:: python

        app = cors(app)
        blueprint = cors(blueprint)

    Arguments:
        allow_credentials: If set the allow credentials header will
            be set, thereby allowing credentials to be shared. Note
            that this does not work with a wildcard origin
            argument.
        allow_headers: A list of headers, a regex or single header
            name, a cross origin request is allowed to access.
        allow_methods: The methods (list) or method (str) that a cross
            origin request can use.
        allow_origin: The origins from which cross origin requests are
            accepted. This is either a list, a regex or a single
            domain. Note the full domain including scheme is required.
        expose_headers: The additional headers (list) or header (str)
            to expose to the client of a cross origin request.
        max_age: The maximum time the response can be cached by the
            client.

    """
    app_or_blueprint.after_request(
        partial(
            _after_request,
            allow_credentials=allow_credentials,
            allow_headers=allow_headers,
            allow_methods=allow_methods,
            allow_origin=allow_origin,
            expose_headers=expose_headers,
            max_age=max_age,
        )
    )
    return app_or_blueprint


async def _after_request(
    response: Optional[Response],
    *,
    allow_credentials: Optional[bool] = None,
    allow_headers: Optional[Iterable[str]] = None,
    allow_methods: Optional[Iterable[str]] = None,
    allow_origin: Optional[Iterable[str]] = None,
    expose_headers: Optional[Iterable[str]] = None,
    max_age: Optional[Union[timedelta, float, str]] = None,
) -> Optional[Response]:
    allow_credentials = allow_credentials or _get_config_or_default("QUART_CORS_ALLOW_CREDENTIALS")
    allow_headers = _sanitise_header_set(allow_headers, "QUART_CORS_ALLOW_HEADERS")
    allow_methods = _sanitise_header_set(allow_methods, "QUART_CORS_ALLOW_METHODS")
    allow_origin = _sanitise_header_set(allow_origin, "QUART_CORS_ALLOW_ORIGIN")
    expose_headers = _sanitise_header_set(expose_headers, "QUART_CORS_EXPOSE_HEADERS")
    max_age = _sanitise_max_age(max_age, "QUART_CORS_MAX_AGE")

    method = request.method
    access_control = request.access_control

    return _apply_cors(
        access_control,
        method,
        response,
        allow_credentials=allow_credentials,
        allow_headers=allow_headers,
        allow_methods=allow_methods,
        allow_origin=allow_origin,
        expose_headers=expose_headers,
        max_age=max_age,
    )


def _apply_cors(
    access_control: RequestAccessControl,
    method: str,
    response: Response,
    *,
    allow_credentials: bool,
    allow_headers: HeaderSet,
    allow_methods: HeaderSet,
    allow_origin: HeaderSet,
    expose_headers: HeaderSet,
    max_age: Optional[float],
) -> Response:
    # Logic follows https://www.w3.org/TR/cors/
    if "*" in allow_origin and allow_credentials:
        raise ValueError("Cannot allow credentials with wildcard allowed origins")

    if getattr(response, "_QUART_CORS_APPLIED", False):
        return response

    origin = _get_origin_if_valid(access_control.origin, allow_origin)
    if origin is not None:
        response.access_control.allow_origin = origin
        response.access_control.allow_credentials = allow_credentials
        response.access_control.expose_headers = expose_headers
        if method == "OPTIONS" and (
            access_control.request_method in allow_methods or "*" in allow_methods
        ):
            if "*" in allow_headers:
                response.access_control.allow_headers = access_control.request_headers
            else:
                response.access_control.allow_headers = allow_headers.intersection(
                    access_control.request_headers
                )
            response.access_control.allow_methods = allow_methods
            response.access_control.max_age = max_age
        if "*" not in origin:
            response.vary.add("Origin")
    setattr(response, "_QUART_CORS_APPLIED", True)
    return response


def _sanitise_header_set(value: Optional[Iterable[str]], config_key: str) -> HeaderSet:
    if value is None:
        value = _get_config_or_default(config_key)
    elif isinstance(value, str):
        value = [value]
    return HeaderSet(value)


def _sanitise_max_age(value: Optional[Union[timedelta, float, str]], config_key: str) -> float:
    if value is None:
        value = _get_config_or_default(config_key)
    elif isinstance(value, timedelta):
        value = value.total_seconds()
    return value  # type: ignore


def _get_config_or_default(config_key: str) -> Any:
    return current_app.config.get(config_key, DEFAULTS[config_key])


def _get_origin_if_valid(origin: str, allow_origin: HeaderSet) -> Optional[HeaderSet]:
    if origin == "":
        return None
    elif "*" in allow_origin:
        return HeaderSet(["*"])
    elif origin in allow_origin:
        return HeaderSet([origin])
    else:
        return None
