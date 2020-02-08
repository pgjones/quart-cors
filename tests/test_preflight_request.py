import pytest
from quart import Quart
from werkzeug.datastructures import HeaderSet

from quart_cors import route_cors


@pytest.fixture(name="app", scope="function")
def _app() -> Quart:
    app = Quart(__name__)

    @app.route("/")
    @route_cors()
    async def index() -> str:
        return "Hello"

    return app


# These tests are based on https://www.w3.org/TR/cors section 6.2, and
# follow the logic given.


@pytest.mark.asyncio
async def test_no_origin(app: Quart) -> None:
    test_client = app.test_client()
    response = await test_client.options("/")
    assert "Access-Control-Allow-Origin" not in response.headers


@pytest.mark.asyncio
@pytest.mark.parametrize("origin", ["http://notquart.com", "http://Quart.com"])
async def test_origin_doesnt_match(app: Quart, origin: str) -> None:
    test_client = app.test_client()
    app.config["QUART_CORS_ALLOW_ORIGIN"] = ["http://quart.com"]
    response = await test_client.options("/", headers={"Origin": origin})
    assert "Access-Control-Allow-Origin" not in response.headers


@pytest.mark.asyncio
async def test_request_method_doesnt_match(app: Quart) -> None:
    test_client = app.test_client()
    app.config["QUART_CORS_ALLOW_METHODS"] = ["GET", "POST"]
    response = await test_client.options(
        "/", headers={"Origin": "http://quart.com", "Access-Control-Request-Method": "DELETE"}
    )
    assert response.access_control_allow_origin == "*"
    assert "Access-Control-Allow-Headers" not in response.headers


@pytest.mark.asyncio
async def test_request_method_match(app: Quart) -> None:
    test_client = app.test_client()
    app.config["QUART_CORS_ALLOW_METHODS"] = ["GET", "POST"]
    response = await test_client.options(
        "/", headers={"Origin": "http://quart.com", "Access-Control-Request-Method": "POST"}
    )
    assert response.access_control_allow_origin == "*"
    assert response.access_control_allow_methods == HeaderSet(["GET", "POST"])


@pytest.mark.asyncio
async def test_request_headers(app: Quart) -> None:
    test_client = app.test_client()
    app.config["QUART_CORS_ALLOW_HEADERS"] = ["X-Match", "X-Other"]
    response = await test_client.options(
        "/",
        headers={
            "Origin": "http://quart.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-Match, X-No-Match",
        },
    )
    assert response.access_control_allow_origin == "*"
    assert response.access_control_allow_headers == HeaderSet(["X-Match"])
