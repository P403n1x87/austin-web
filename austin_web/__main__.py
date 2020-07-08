# This file is part of "austin-tui" which is released under GPL.
#
# See file LICENCE or go to http://www.gnu.org/licenses/ for full license
# details.
#
# austin-tui is top-like Web for Austin.
#
# Copyright (c) 2018-2020 Gabriele N. Tornetta <phoenix1987@gmail.com>.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import json
from os import environ as env
import sys
import weakref

from aiohttp import web
from aiohttp.test_utils import unused_port
from austin import AustinError
from austin.aio import AsyncAustin
from austin.cli import AustinArgumentParser
from pyfiglet import Figlet

from austin_web.data import DataPool, WebFrame
from austin_web.html import load_site


class AustinWebArgumentParser(AustinArgumentParser):
    def __init__(self):
        super().__init__(name="austin-tui", full=False)


class AustinWeb(AsyncAustin):
    def __init__(self):
        super().__init__()

        self._args = AustinWebArgumentParser().parse_args()
        self._pools = weakref.WeakSet()
        self._runner = None
        self._global_stats = None

    def on_ready(self, *args, **kwargs):
        asyncio.get_event_loop().create_task(self.start_server())

    def on_sample_received(self, text):
        for data_pool in self._pools:
            data_pool.add(WebFrame.parse(text))

    def on_terminate(self, stats):
        self._global_stats = stats
        asyncio.get_event_loop().create_task(self.stop_server())
        self.shutdown()

    def new_data_pool(self):
        data_pool = DataPool(self)
        self._pools.add(data_pool)
        return data_pool

    def discard_data_pool(self, data_pool):
        self._pools.discard(data_pool)

    async def handle_home(self, request):
        return web.Response(body=self.html, content_type="text/html")

    async def handle_websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        data_pool = self.new_data_pool()

        try:
            payload = {
                "type": "info",
                "pid": self.get_process().pid,
                "command": self.get_command_line(),
                "metric": "m" if self._args.memory else "t",
            }

            await ws.send_str(json.dumps(payload))

            async for msg in ws:
                if not await data_pool.send(ws):
                    break

            self.discard_data_pool(data_pool)

        except AustinError:
            pass

        return ws

    async def start_server(self):
        app = web.Application()
        app.add_routes(
            [web.get("/", self.handle_home), web.get("/ws", self.handle_websocket)]
        )

        port = int(env.get("WEBAUSTIN_PORT", 0)) or unused_port()
        host = env.get("WEBAUSTIN_HOST") or "localhost"

        self.html = load_site()

        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, host, port)
        await site.start()

        # web.run_app(app, host=host, port=port, print=None)

        print(Figlet(font="speed", width=240).renderText("* Austin Web *"))
        print(
            f"* Sampling process with PID {self.get_process().pid} ({self.get_command_line()})"
        )
        print(f"* Austin Web is running on http://{host}:{port}. Press Ctrl+C to stop.")

    async def stop_server(self):
        await self._runner.cleanup()

    def run(self):
        loop = asyncio.get_event_loop()

        try:
            loop.create_task(self.start(AustinWebArgumentParser.to_list(self._args)))
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self):
        for task in asyncio.Task.all_tasks():
            task.cancel()

        pending = [task for task in asyncio.Task.all_tasks() if not task.done()]
        if pending:
            try:
                done, _ = asyncio.get_event_loop().run_until_complete(
                    asyncio.wait(pending)
                )
                for t in done:
                    res = t.result()
                    if res:
                        print(res)
            except (AustinError, asyncio.CancelledError):
                pass

        if self._global_stats:
            print(self._global_stats)


def main():
    if sys.platform == "win32":
        asyncio.set_event_loop(asyncio.ProactorEventLoop())

    AustinWeb().run()


if __name__ == "__main__":
    main()
