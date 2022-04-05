import pytest
from quart import Blueprint, Quart
from werkzeug.datastructures import HeaderSet

from quart_cors import cors, route_cors


@pytest.fixture(name="app")
def _app() -> Quart:
    app = Quart(__name__)
    app = cors(app, allow_origin="http://app.com")
    app.config["QUART_CORS_ALLOW_METHODS"] = ["GET", "POST"]

    blueprint = Blueprint("blue", __name__)
    blueprint = cors(blueprint, allow_origin=["http://blueprint.com"])

    @app.route("/app")
    async def app_route() -> str:
        return "App"

    @app.route("/route")
    @route_cors(allow_origin=["http://route.com"])
    async def route() -> str:
        return "Route"

    @blueprint.route("/blueprint")
    async def blueprint_() -> str:
        return "Blueprint"

    @blueprint.route("/blueprint_route")
    @route_cors(allow_origin=["http://blueprint.route.com"])
    async def blueprint_route() -> str:
        return "Blueprint Route"

    app.register_blueprint(blueprint)

    return app


@pytest.mark.parametrize(
    "origin, path",
    [
        ("http://app.com", "/app"),
        ("http://route.com", "/route"),
        ("http://blueprint.com", "/blueprint"),
        ("http://blueprint.route.com", "/blueprint_route"),
    ],
)
async def test_match(app: Quart, origin: str, path: str) -> None:
    test_client = app.test_client()
    response = await test_client.options(
        path, headers={"Origin": origin, "Access-Control-Request-Method": "POST"}
    )
    assert response.access_control_allow_origin == origin
    assert response.access_control_allow_methods == HeaderSet(["GET", "POST"])


@pytest.mark.parametrize(
    "origin, path",
    [
        ("http://app.com", "/route"),
        ("http://route.com", "/app"),
        ("http://blueprint.com", "/blueprint_route"),
        ("http://blueprint.route.com", "/blueprint"),
    ],
)
async def test_no_match(app: Quart, origin: str, path: str) -> None:
    test_client = app.test_client()
    response = await test_client.options(
        path, headers={"Origin": origin, "Access-Control-Request-Method": "POST"}
    )
    assert "Access-Control-Allow-Origin" not in response.headers
