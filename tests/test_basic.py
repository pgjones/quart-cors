import re
from datetime import timedelta
from typing import Pattern, Union

import pytest
from quart import Blueprint, Quart
from werkzeug.datastructures import HeaderSet

from quart_cors import cors, route_cors


@pytest.fixture(name="route_cors_app")
def _route_cors_app() -> Quart:
    app = Quart(__name__)

    @app.route("/")
    @route_cors(max_age=timedelta(seconds=5))
    async def index() -> str:
        return "Hello"

    return app


async def test_simple_cross_origin_request(route_cors_app: Quart) -> None:
    test_client = route_cors_app.test_client()
    response = await test_client.get("/", headers={"Origin": "https://quart.com"})
    assert response.access_control_allow_origin == "*"


async def test_preflight_request(route_cors_app: Quart) -> None:
    test_client = route_cors_app.test_client()
    response = await test_client.options(
        "/", headers={"Origin": "https://quart.com", "Access-Control-Request-Method": "DELETE"}
    )
    assert response.access_control_allow_origin == "*"
    assert response.access_control_allow_methods == HeaderSet(
        ["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"]
    )
    assert response.access_control_max_age == 5


@pytest.mark.parametrize("kind", ("no-header", "empty-header"))
async def test_bad_preflight_request(route_cors_app: Quart, kind: str) -> None:
    test_client = route_cors_app.test_client()
    # Missing Access-Control-Request-Method header
    headers = {"Origin": "https://quart.com"}
    if kind == "empty-header":
        headers["Access-Control-Request-Method"] = ""
    response = await test_client.options("/", headers=headers)
    assert response.access_control_allow_origin == "*"
    assert response.access_control_allow_methods is None
    assert response.access_control_max_age is None


async def test_app_cors() -> None:
    app = Quart(__name__)

    @app.route("/")
    async def index() -> str:
        return "Hello"

    app = cors(app)

    test_client = app.test_client()
    response = await test_client.get("/", headers={"Origin": "https://quart.com"})
    assert response.access_control_allow_origin == "*"


async def test_blueprint_cors() -> None:
    app = Quart(__name__)

    blueprint = Blueprint("name", __name__)

    blueprint = cors(blueprint)

    @blueprint.route("/")
    async def index() -> str:
        return "Hello"

    app.register_blueprint(blueprint)

    test_client = app.test_client()
    response = await test_client.get("/", headers={"Origin": "https://quart.com"})
    assert response.access_control_allow_origin == "*"


@pytest.mark.parametrize(
    "allowed_origin, expected",
    [
        ("*", "*"),
        ("https://quart.com", "https://quart.com"),
        (re.compile(r"https:\/\/.*\.?quart\.com"), "https://quart.com"),
    ],
)
async def test_regex_matching(allowed_origin: Union[Pattern, str], expected: str) -> None:
    app = Quart(__name__)
    app.config["QUART_CORS_ALLOW_ORIGIN"] = [allowed_origin]

    @app.route("/")
    async def index() -> str:
        return "Hello"

    app = cors(app)

    test_client = app.test_client()
    response = await test_client.get("/", headers={"Origin": "https://quart.com"})
    assert response.access_control_allow_origin == expected
