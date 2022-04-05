import pytest
from quart import Quart, websocket
from quart.testing import WebsocketResponseError

from quart_cors import cors, cors_exempt


@pytest.fixture(name="websocket_cors_app")
def _websocket_cors_app() -> Quart:
    app = Quart(__name__)

    cors(app, allow_origin=["https://quart.com"])

    @app.websocket("/")
    async def ws() -> None:
        await websocket.send(b"a")

    @app.websocket("/exempt")
    @cors_exempt
    async def ws_exempt() -> None:
        await websocket.send(b"a")

    return app


async def test_websocket_allowed(websocket_cors_app: Quart) -> None:
    test_client = websocket_cors_app.test_client()
    async with test_client.websocket(
        "/", headers={"Origin": "https://quart.com"}
    ) as test_websocket:
        data = await test_websocket.receive()
    assert data == b"a"  # type: ignore


async def test_websocket_blocked(websocket_cors_app: Quart) -> None:
    test_client = websocket_cors_app.test_client()
    try:
        async with test_client.websocket("/") as test_websocket:
            await test_websocket.send(b"a")
    except WebsocketResponseError as error:
        assert error.response.status_code == 400


async def test_websocket_exempt(websocket_cors_app: Quart) -> None:
    test_client = websocket_cors_app.test_client()
    async with test_client.websocket("/exempt") as test_websocket:
        data = await test_websocket.receive()
    assert data == b"a"  # type: ignore
