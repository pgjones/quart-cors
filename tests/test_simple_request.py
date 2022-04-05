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


# These tests are based on https://www.w3.org/TR/cors section 6.1, and
# follow the logic given.


async def test_no_origin(app: Quart) -> None:
    test_client = app.test_client()
    response = await test_client.get("/")
    assert "Access-Control-Allow-Origin" not in response.headers


@pytest.mark.parametrize("origin", ["http://notquart.com", "http://Quart.com"])
async def test_origin_doesnt_match(app: Quart, origin: str) -> None:
    test_client = app.test_client()
    app.config["QUART_CORS_ALLOW_ORIGIN"] = ["http://quart.com"]
    response = await test_client.get("/", headers={"Origin": origin})
    assert "Access-Control-Allow-Origin" not in response.headers


async def test_credentials_and_wildcard(app: Quart) -> None:
    test_client = app.test_client()
    app.config["QUART_CORS_ALLOW_CREDENTIALS"] = True
    response = await test_client.get("/", headers={"Origin": "http://quart.com"})
    assert response.status_code == 500


async def test_credentials(app: Quart) -> None:
    test_client = app.test_client()
    app.config["QUART_CORS_ALLOW_ORIGIN"] = ["http://quart.com"]
    app.config["QUART_CORS_ALLOW_CREDENTIALS"] = True
    response = await test_client.get("/", headers={"Origin": "http://quart.com"})
    assert response.access_control_allow_origin == "http://quart.com"
    assert response.vary == HeaderSet(["Origin"])
    assert response.access_control_allow_credentials


async def test_expose_headers(app: Quart) -> None:
    test_client = app.test_client()
    app.config["QUART_CORS_EXPOSE_HEADERS"] = ["X-Special", "X-Other"]
    response = await test_client.get("/", headers={"Origin": "http://quart.com"})
    assert response.access_control_allow_origin == "*"
    assert response.access_control_expose_headers == HeaderSet(["X-Special", "X-Other"])
