import asyncio

import aiohttp

from austin_web.__main__ import AustinWeb
from austin_web.__main__ import _main


class AustinWebTest(AustinWeb):
    async def start_server(self):
        await super().start_server()
        await self.send_request()

        self.terminate()

        asyncio.get_event_loop().stop()

    async def send_request(self):
        async with aiohttp.ClientSession() as session:
            response = await session.get("http://localhost:5000")
            assert response.status == 200

            content = await response.read()
            assert b'<div id="chart"' in content


def test_serve():
    _main(AustinWebTest, ["--port", "5000", "python", "test/target.py"])
