from datetime import timedelta

import pytest
from quart import Blueprint, Quart

from quart_cors import cors, route_cors


@pytest.fixture(name="route_cors_app")
def _route_cors_app() -> Quart:
    app = Quart(__name__)

    @app.route("/")
    @route_cors(max_age=timedelta(seconds=5))
    async def index() -> str:
        return "Hello"

    return app


@pytest.mark.asyncio
async def test_simple_cross_origin_request(route_cors_app: Quart) -> None:
    test_client = route_cors_app.test_client()
    response = await test_client.get("/", headers={"Origin": "https://quart.com"})
    assert response.access_control.allow_origin == {"*"}


@pytest.mark.asyncio
async def test_preflight_request(route_cors_app: Quart) -> None:
    test_client = route_cors_app.test_client()
    response = await test_client.options(
        "/", headers={"Origin": "https://quart.com", "Access-Control-Request-Method": "DELETE"}
    )
    assert response.access_control.allow_origin == {"*"}
    assert response.access_control.allow_methods == {
        "GET",
        "HEAD",
        "POST",
        "OPTIONS",
        "PUT",
        "PATCH",
        "DELETE",
    }
    assert response.access_control.max_age == 5.0


@pytest.mark.asyncio
async def test_app_cors() -> None:
    app = Quart(__name__)

    @app.route("/")
    async def index() -> str:
        return "Hello"

    app = cors(app)

    test_client = app.test_client()
    response = await test_client.get("/", headers={"Origin": "https://quart.com"})
    assert response.access_control.allow_origin == {"*"}


@pytest.mark.asyncio
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
    assert response.access_control.allow_origin == {"*"}
