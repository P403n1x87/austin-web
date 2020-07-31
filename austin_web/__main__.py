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
from typing import Any, List, Optional, Type
import weakref

from aiohttp import web
from aiohttp.test_utils import unused_port
from austin import AustinError
from austin.aio import AsyncAustin
from austin.cli import AustinArgumentParser, AustinCommandLineError
from austin_web.data import DataPool, WebFrame
from austin_web.html import load_compile, load_site
from halo import Halo
from pyfiglet import Figlet


if sys.platform == "win32":
    asyncio.set_event_loop(asyncio.ProactorEventLoop())


class AustinWebError(AustinError):
    """AustinWeb own generic error."""

    pass


class AustinWebArgumentParser(AustinArgumentParser):
    """AustinWeb command line parser."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
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
            help="Compile Austin data into an HTML flame graph visualisation "
            "into the given output file.",
            type=str,
        )


class AustinWebMode(Enum):
    """AustinWeb mode."""

    SERVE = 0
    COMPILE = 1


class AustinWeb(AsyncAustin):
    """AustinWeb subclass of AsyncAustin."""

    def __init__(self, args: Optional[List[str]] = None) -> None:
        super().__init__()

        self._args = AustinWebArgumentParser().parse_args(args)
        if self._args.compile and self._args.serve:
            raise AustinCommandLineError("Incompatible options: compile and serve.", -1)

        self._mode = (
            AustinWebMode.COMPILE if self._args.compile else AustinWebMode.SERVE
        )
        self._pools: weakref.WeakSet = weakref.WeakSet()
        self._pool: Optional[DataPool] = None
        self._runner: Optional[web.AppRunner] = None
        self._global_stats: Optional[str] = None
        self._spinner: Optional[Halo] = None

    def on_ready(self, *args: Any, **kwargs: Any) -> None:
        """Austin ready callback."""
        if self._mode == AustinWebMode.SERVE:
            asyncio.get_event_loop().create_task(self.start_server())
        else:
            self._spinner = Halo(text="Sampling", spinner="dots")
            self._spinner.start()
            self._pool = DataPool(self)

    def on_sample_received(self, text: str) -> None:
        """Austin sample received callback."""
        if self._mode == AustinWebMode.SERVE:
            if not self._pools:
                return
            frame = WebFrame.parse(text)
            for data_pool in self._pools:
                data_pool.add(frame)
        else:
            if not self._pool:
                raise AustinWebError("Data pool is unexpectedly missing")
            self._pool.add(WebFrame.parse(text))

    def on_terminate(self, stats: str) -> None:
        """Austin terminate callback."""
        self._global_stats = stats
        if self._mode == AustinWebMode.COMPILE:
            if self._spinner:
                self._spinner.stop()

            self.compile()

            asyncio.get_event_loop().stop()

    def new_data_pool(self) -> DataPool:
        """Make new data pool for incoming request."""
        data_pool = DataPool(self)
        self._pools.add(data_pool)
        return data_pool

    def discard_data_pool(self, data_pool: DataPool) -> None:
        """Discard no longer used data pool."""
        self._pools.discard(data_pool)

    def compile(self) -> None:
        """Compile collected samples."""
        if self._pool is None:
            return

        with open(self._args.compile, "w") as fout:
            fout.write(
                load_compile(
                    data=json.dumps(self._pool.data.to_dict()),
                    profile_type="Memory" if self._args.memory else "Time",
                )
            )
            print(f"✨🧁✨ Samples compiled into {self._args.compile}")

    async def handle_home(self, request: web.Request) -> web.Response:
        """Home page handler."""
        return web.Response(body=self.html, content_type="text/html")

    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Web socket handler."""
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

    async def start_server(self) -> None:
        """Start the web server asynchronously."""
        app = web.Application()
        app.add_routes(
            [web.get("/", self.handle_home), web.get("/ws", self.handle_websocket)]
        )

        port = self._args.port or unused_port()
        host = self._args.host

        self.html = load_site()

        self._runner = web.AppRunner(app)
        if not self._runner:
            raise AustinWebError("Cannot create web app runner.")
        await self._runner.setup()
        site = web.TCPSite(self._runner, host, port)
        await site.start()

        print(Figlet(font="speed", width=240).renderText("* Austin Web *"))
        print(
            f"⏲️ Sampling process with PID {self.get_process().pid} "
            f"({self.get_command_line()})"
        )
        print(f"🏃 Austin Web is running on http://{host}:{port}. Press Ctrl+C to stop.")

    async def stop_server(self) -> None:
        """Stop the web server asynchronously."""
        if self._runner:
            await self._runner.cleanup()

    async def start(self, args: List[str]) -> None:
        """Start austin and catch any exceptions."""
        try:
            await super().start(args)
        except AustinError as e:
            raise KeyboardInterrupt("Failed to start Austin") from e

    def run(self) -> None:
        """Run Austin Web."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()

        try:
            loop.create_task(self.start(AustinWebArgumentParser.to_list(self._args)))
            loop.run_forever()
        except KeyboardInterrupt as e:
            if e.__cause__:
                print(
                    "❌ Austin failed to start. Please ensure that the Austin binary\n"
                    "is on the PATH environment variable and that the command line\n"
                    "arguments are correct."
                )
            pass
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Shutdown Austin Web."""
        asyncio.get_event_loop().run_until_complete(self.stop_server())

        try:
            all_tasks = asyncio.all_tasks  # Python 3.7+
        except AttributeError:
            all_tasks = asyncio.Task.all_tasks  # Python 3.6

        try:
            for task in all_tasks():
                task.cancel()
        except RuntimeError:
            return

        pending = [task for task in all_tasks() if not task.done()]
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


def _main(cls: Type[AustinWeb], args: List[str]) -> None:
    cls(args).run()


def main() -> None:
    """The main function."""
    try:
        _main(AustinWeb, sys.argv[1:])
    except AustinCommandLineError as e:
        message, *code = e.args
        print(message)
        exit(code[0] if code else -1)


if __name__ == "__main__":
    main()
