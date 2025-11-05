from collections.abc import Awaitable, Callable, Iterable
from datetime import timedelta
from functools import partial, wraps
from re import Pattern
from typing import Any, cast, ParamSpec, TypeVar

from quart import (
    abort,
    Blueprint,
    current_app,
    make_response,
    Quart,
    request,
    Response,
    ResponseReturnValue,
    websocket,
)
from quart.typing import RouteCallable, WebsocketCallable
from werkzeug.datastructures import HeaderSet

__all__ = ("cors", "route_cors", "websocket_cors", "cors_exempt")

OriginType = Pattern | str

DEFAULTS = {
    "QUART_CORS_ALLOW_CREDENTIALS": False,
    "QUART_CORS_ALLOW_HEADERS": ["*"],
    "QUART_CORS_ALLOW_METHODS": ["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"],
    "QUART_CORS_ALLOW_ORIGIN": ["*"],
    "QUART_CORS_EXPOSE_HEADERS": [""],
    "QUART_CORS_MAX_AGE": None,
    "QUART_CORS_SEND_ORIGIN_WILDCARD": True,
}

QUART_CORS_EXEMPT_ATTRIBUTE = "_quart_cors_exempt"

P = ParamSpec("P")


def route_cors(
    *,
    allow_credentials: bool | None = None,
    allow_headers: Iterable[str] | None = None,
    allow_methods: Iterable[str] | None = None,
    allow_origin: OriginType | Iterable[OriginType] | None = None,
    expose_headers: Iterable[str] | None = None,
    max_age: timedelta | float | str | None = None,
    send_origin_wildcard: bool | None = None,
    provide_automatic_options: bool = True,
) -> Callable[
    [Callable[P, ResponseReturnValue] | Callable[P, Awaitable[ResponseReturnValue]]],
    Callable[P, Awaitable[Response]],
]:
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
            accepted. This is either a list of re.complied regex or
            strings, or a single re.compiled regex or string, or the
            wildward string, `*`. Note the full domain including scheme
            is required.
        expose_headers: The additional headers (list) or header (str)
            to expose to the client of a cross origin request.
        max_age: The maximum time the response can be cached by the
            client.
        send_origin_wildcard: Send wildcard, "*", as the allow origin
            were appropriate (or echo the request origin).
        provide_automatic_options: If set the automatic OPTIONS
            response created by Quart will be overwriten by one
            created by Quart-CORS.

    """

    def decorator(
        func: Callable[P, ResponseReturnValue] | Callable[P, Awaitable[ResponseReturnValue]],
    ) -> Callable[P, Awaitable[Response]]:
        if provide_automatic_options:
            func.required_methods = getattr(func, "required_methods", set())  # type: ignore
            func.required_methods.add("OPTIONS")  # type: ignore
            func.provide_automatic_options = False  # type: ignore

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Response:
            nonlocal allow_credentials, allow_headers, allow_methods, allow_origin, expose_headers
            nonlocal max_age, send_origin_wildcard

            method = request.method

            if provide_automatic_options and method == "OPTIONS":
                response = await current_app.make_default_options_response()
            else:
                response = cast(
                    Response,
                    await make_response(await current_app.ensure_async(func)(*args, **kwargs)),
                )

            allow_credentials = allow_credentials or _get_config_or_default(
                "QUART_CORS_ALLOW_CREDENTIALS"
            )
            allow_headers = _sanitise_header_set(allow_headers, "QUART_CORS_ALLOW_HEADERS")
            allow_methods = _sanitise_header_set(allow_methods, "QUART_CORS_ALLOW_METHODS")
            allow_origin = _sanitise_origin_set(allow_origin, "QUART_CORS_ALLOW_ORIGIN")
            expose_headers = _sanitise_header_set(expose_headers, "QUART_CORS_EXPOSE_HEADERS")
            max_age = _sanitise_max_age(max_age, "QUART_CORS_MAX_AGE")
            send_origin_wildcard = send_origin_wildcard or _get_config_or_default(
                "QUART_CORS_SEND_ORIGIN_WILDCARD"
            )
            response = _apply_cors(
                request.origin,
                request.access_control_request_headers,
                request.access_control_request_method,
                method,
                response,
                allow_credentials=allow_credentials,
                allow_headers=allow_headers,
                allow_methods=allow_methods,
                allow_origin=allow_origin,
                expose_headers=expose_headers,
                max_age=max_age,
                send_origin_wildcard=send_origin_wildcard,
            )
            return response

        return wrapper

    return decorator


V = TypeVar("V", bound=ResponseReturnValue | None)


def websocket_cors(
    *,
    allow_origin: OriginType | Iterable[OriginType] | None = None,
    send_origin_wildcard: bool | None = None,
) -> Callable[[Callable[P, V | Awaitable[V]]], Callable[P, Awaitable[V]]]:
    """A decorator to control CORS websocket requests.

    This should be used to wrap a websocket handler (or view function)
    to control CORS access to the websocket. Note that it is important
    that this decorator be wrapped by the websocket decorator and not
    vice, versa, as below.

    .. code-block:: python

        @app.websocket('/')
        @websocket_cors()
        async def index():
            ...

    Arguments:
        allow_origin: The origins from which cross origin requests are
            accepted. This is either a list of re.complied regex or
            strings, or a single re.compiled regex or string, or the
            wildward string, `*`. Note the full domain including scheme
            is required.
        send_origin_wildcard: Send wildcard, "*", as the allow origin
            were appropriate (or echo the request origin).

    """

    def decorator(func: Callable[P, V | Awaitable[V]]) -> Callable[P, Awaitable[V]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> V:
            # Will abort if origin is invalid
            _apply_websocket_cors(
                allow_origin=allow_origin, send_origin_wildcard=send_origin_wildcard
            )

            return await current_app.ensure_async(func)(*args, **kwargs)  # type: ignore

        return wrapper

    return decorator


U = TypeVar("U", bound=RouteCallable | WebsocketCallable)


def cors_exempt(func: U) -> U:
    """A decorator to exempt a websocket handler or view function from CORS control.

    This can be used in conjunction with the `cors` function to mark a
    single websocket handler or view function as exempt from CORS
    i.e. don't add CORS headers to responses and don't check the
    origin.

     .. code-block:: python

        @app.websocket('/')
        @cors_exempt
        async def index():
            ...
    """
    setattr(func, QUART_CORS_EXEMPT_ATTRIBUTE, True)
    return func


T = TypeVar("T", bound=Blueprint | Quart)


def cors(
    app_or_blueprint: T,
    *,
    allow_credentials: bool | None = None,
    allow_headers: Iterable[str] | None = None,
    allow_methods: Iterable[str] | None = None,
    allow_origin: OriginType | Iterable[OriginType] | None = None,
    expose_headers: Iterable[str] | None = None,
    max_age: timedelta | float | str | None = None,
    send_origin_wildcard: bool | None = None,
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
            accepted. This is either a list of re.complied regex or
            strings, or a single re.compiled regex or string, or the
            wildward string, `*`. Note the full domain including scheme
            is required.
        expose_headers: The additional headers (list) or header (str)
            to expose to the client of a cross origin request.
        max_age: The maximum time the response can be cached by the
            client.
        send_origin_wildcard: Send wildcard, "*", as the allow origin
            were appropriate (or echo the request origin).

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
            send_origin_wildcard=send_origin_wildcard,
        )
    )
    app_or_blueprint.before_websocket(
        partial(
            _before_websocket, allow_origin=allow_origin, send_origin_wildcard=send_origin_wildcard
        )
    )
    return app_or_blueprint


async def _before_websocket(
    *,
    allow_origin: OriginType | Iterable[OriginType] | None = None,
    send_origin_wildcard: bool | None = None,
) -> None:
    view_func = current_app.view_functions.get(websocket.endpoint)
    if not getattr(view_func, QUART_CORS_EXEMPT_ATTRIBUTE, False):
        return _apply_websocket_cors(
            allow_origin=allow_origin, send_origin_wildcard=send_origin_wildcard
        )


async def _after_request(
    response: Response | None,
    *,
    allow_credentials: bool | None = None,
    allow_headers: Iterable[str] | None = None,
    allow_methods: Iterable[str] | None = None,
    allow_origin: OriginType | Iterable[OriginType] | None = None,
    expose_headers: Iterable[str] | None = None,
    max_age: timedelta | float | str | None = None,
    send_origin_wildcard: bool | None = None,
) -> Response | None:
    allow_credentials = allow_credentials or _get_config_or_default("QUART_CORS_ALLOW_CREDENTIALS")
    allow_headers = _sanitise_header_set(allow_headers, "QUART_CORS_ALLOW_HEADERS")
    allow_methods = _sanitise_header_set(allow_methods, "QUART_CORS_ALLOW_METHODS")
    allow_origin = _sanitise_origin_set(allow_origin, "QUART_CORS_ALLOW_ORIGIN")
    expose_headers = _sanitise_header_set(expose_headers, "QUART_CORS_EXPOSE_HEADERS")
    max_age = _sanitise_max_age(max_age, "QUART_CORS_MAX_AGE")
    send_origin_wildcard = send_origin_wildcard or _get_config_or_default(
        "QUART_CORS_SEND_ORIGIN_WILDCARD"
    )

    method = request.method

    view_func = current_app.view_functions.get(request.endpoint)
    if not getattr(view_func, QUART_CORS_EXEMPT_ATTRIBUTE, False):
        return _apply_cors(
            request.origin,
            request.access_control_request_headers,
            request.access_control_request_method,
            method,
            response,
            allow_credentials=allow_credentials,
            allow_headers=allow_headers,
            allow_methods=allow_methods,
            allow_origin=allow_origin,
            expose_headers=expose_headers,
            max_age=max_age,
            send_origin_wildcard=send_origin_wildcard,
        )
    else:
        return response


def _apply_cors(
    request_origin: str | None,
    request_headers: HeaderSet | None,
    request_method: str | None,
    method: str,
    response: Response,
    *,
    allow_credentials: bool,
    allow_headers: HeaderSet,
    allow_methods: HeaderSet,
    allow_origin: set[OriginType],
    expose_headers: HeaderSet,
    max_age: int | None,
    send_origin_wildcard: bool,
) -> Response:
    # Logic follows https://www.w3.org/TR/cors/
    if "*" in allow_origin and allow_credentials:
        raise ValueError("Cannot allow credentials with wildcard allowed origins")

    if getattr(response, "_QUART_CORS_APPLIED", False):
        return response

    origin = _get_origin_if_valid(request_origin, allow_origin, send_origin_wildcard)
    if origin is not None:
        response.access_control_allow_origin = origin
        response.access_control_allow_credentials = allow_credentials
        response.access_control_expose_headers = expose_headers
        if (
            method == "OPTIONS"
            and request_method
            and (request_method in allow_methods or "*" in allow_methods)
        ):
            if request_headers is None:
                request_headers = HeaderSet()
            if "*" in allow_headers:
                response.access_control_allow_headers = request_headers
            else:
                response.access_control_allow_headers = HeaderSet(
                    allow_headers.as_set().intersection(request_headers.as_set())
                )
            response.access_control_allow_methods = allow_methods
            if max_age is not None:
                response.access_control_max_age = max_age
    if origin is None or "*" not in origin:
        response.vary.add("Origin")
    setattr(response, "_QUART_CORS_APPLIED", True)
    return response


def _apply_websocket_cors(
    *,
    allow_origin: OriginType | Iterable[OriginType] | None = None,
    send_origin_wildcard: bool | None = None,
) -> None:
    allow_origin = _sanitise_origin_set(allow_origin, "QUART_CORS_ALLOW_ORIGIN")
    send_origin_wildcard = send_origin_wildcard or _get_config_or_default(
        "QUART_CORS_SEND_ORIGIN_WILDCARD"
    )
    origin = _get_origin_if_valid(websocket.origin, allow_origin, send_origin_wildcard)
    if origin is None:
        abort(400)


def _sanitise_origin_set(
    value: OriginType | Iterable[OriginType] | None, config_key: str
) -> set[OriginType]:
    if value is None:
        value = _get_config_or_default(config_key)
    elif isinstance(value, (Pattern, str)):
        value = [value]
    return set(value)  # type: ignore


def _sanitise_header_set(value: str | Iterable[str] | None, config_key: str) -> HeaderSet:
    if value is None:
        value = _get_config_or_default(config_key)
    elif isinstance(value, str):
        value = [value]
    return HeaderSet(value)


def _sanitise_max_age(value: timedelta | float | str | None, config_key: str) -> int:
    if value is None:
        value = _get_config_or_default(config_key)
    elif isinstance(value, timedelta):
        value = value.total_seconds()
    if value is not None:
        return int(value)  # type: ignore
    return None


def _get_config_or_default(config_key: str) -> Any:
    return current_app.config.get(config_key, DEFAULTS[config_key])


def _get_origin_if_valid(
    origin: str | None, allow_origin: set[OriginType], send_wildcard: bool
) -> str | None:
    if origin is None or origin == "":
        return None

    for allowed in allow_origin:
        if allowed == "*":
            if send_wildcard:
                return "*"
            else:
                return origin
        if isinstance(allowed, Pattern) and allowed.match(origin):
            return origin
        elif origin == allowed:
            return origin

    return None
