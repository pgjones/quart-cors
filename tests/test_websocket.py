import pytest
from quart import Quart, websocket
from quart.testing import WebsocketResponse

from quart_cors import websocket_cors


@pytest.fixture(name="websocket_cors_app")
def _websocket_cors_app() -> Quart:
    app = Quart(__name__)

    @app.websocket("/")
    @websocket_cors(allow_origin=["https://quart.com"])
    async def ws() -> None:
        await websocket.send(b"a")

    return app


@pytest.mark.asyncio
async def test_websocket_allowed(websocket_cors_app: Quart) -> None:
    test_client = websocket_cors_app.test_client()
    async with test_client.websocket(
        "/", headers={"Origin": "https://quart.com"}
    ) as test_websocket:
        data = await test_websocket.receive()
    assert data == b"a"


@pytest.mark.asyncio
async def test_websocket_blocked(websocket_cors_app: Quart) -> None:
    test_client = websocket_cors_app.test_client()
    try:
        async with test_client.websocket("/") as test_websocket:
            await test_websocket.send(b"a")
    except WebsocketResponse as error:
        assert error.response.status_code == 400
