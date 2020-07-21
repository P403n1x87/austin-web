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
from enum import Enum
import json
import sys
import weakref

from aiohttp import web
from aiohttp.test_utils import unused_port
from austin import AustinError
from austin.aio import AsyncAustin
from austin.cli import AustinArgumentParser, AustinCommandLineError
from halo import Halo
from pyfiglet import Figlet

from austin_web.data import DataPool, WebFrame
from austin_web.html import load_compile, load_site


class AustinWebArgumentParser(AustinArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(name="austin-tui", full=False, alt_format=False)

        # ---- Serve command ----
        self.add_argument(
            "-S",
            "--serve",
            help="Serve Austin Web for live Austin data visualisation.",
            action="store_true",
        )

        self.add_argument(
            "-H",
            "--host",
            help="Set the host to serve on. Defaults to localhost.",
            type=str,
            default="localhost",
        )
        self.add_argument(
            "-P",
            "--port",
            help="Set the port to serve on. Defaults to an ephemaral port.",
            type=int,
            default=0,
        )

        # ---- Compile command ----
        self.add_argument(
            "-c",
            "--compile",
            help="Compile Austin data into an HTML flame graph visualisation into the given output file.",
            type=str,
        )


class AustinWebMode(Enum):
    SERVE = 0
    COMPILE = 1


class AustinWeb(AsyncAustin):
    def __init__(self):
        super().__init__()

        try:
            self._args = AustinWebArgumentParser().parse_args()
            if self._args.compile and self._args.serve:
                raise AustinCommandLineError(
                    "Incompatible options: compile and serve.", -1
                )
        except AustinCommandLineError as e:
            print(e.args[0])
            exit(e.args[1])

        self._mode = (
            AustinWebMode.COMPILE if self._args.compile else AustinWebMode.SERVE
        )
        self._pools = weakref.WeakSet()
        self._pool = None
        self._runner = None
        self._global_stats = None
        self._spinner = None

    def on_ready(self, *args, **kwargs):
        if self._mode == AustinWebMode.SERVE:
            asyncio.get_event_loop().create_task(self.start_server())
        else:
            self._spinner = Halo(text="Sampling", spinner="dots")
            self._spinner.start()
            self._pool = DataPool(self)

    def on_sample_received(self, text):
        frame = WebFrame.parse(text)
        if self._mode == AustinWebMode.SERVE:
            for data_pool in self._pools:
                data_pool.add(frame)
        else:
            self._pool.add(frame)

    def on_terminate(self, stats):
        self._global_stats = stats
        if self._mode == AustinWebMode.SERVE:
            asyncio.get_event_loop().create_task(self.stop_server())
        else:
            self._spinner.stop()
            with open(self._args.compile, "w") as fout:
                fout.write(
                    load_compile(
                        data=json.dumps(self._pool.data.to_dict()),
                        profile_type="Memory" if self._args.memory else "Time",
                    )
                )
            raise KeyboardInterrupt("Compilation done")

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

        port = self._args.port or unused_port()
        host = self._args.host

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
