import json
from typing import Any, Dict, List, Optional

from aiohttp import web
from austin.aio import AsyncAustin
from austin.stats import Frame, Sample
import psutil


class WebFrame:
    """Frame class designed to work nicely with d3-flame-graph."""

    __slots__ = ["name", "value", "children", "index", "parent", "height"]

    def __init__(self, name: Any, value: int) -> None:
        self.name: str = str(name)
        self.value: int = value
        self.children: List["WebFrame"] = []
        self.index: Dict[str, "WebFrame"] = {}
        self.parent: Optional["WebFrame"] = None
        self.height: int = 1

    def __add__(self, other: "WebFrame") -> "WebFrame":
        """Update the values by merging the right frame into the left one."""
        if self.name != other.name:
            if not self.parent:
                raise ValueError("Parent missing in non-root WebFrame")
            self.parent.add_child(other)
            self.parent.height = max(self.height, other.height) + 1
        else:
            self.value += other.value
            if other.height > self.height:
                self.height = other.height
            for child in other.children:
                try:
                    self.index[child.name] += child
                except KeyError:
                    self.add_child(child)

        return self

    def add_child(self, frame: "WebFrame") -> None:
        """Add child frame to the frame."""
        self.index[frame.name] = frame
        frame.parent = self
        self.children.append(frame)

    @staticmethod
    def parse(text: str) -> "WebFrame":
        """Create a frame from an Austin collapsed sample."""

        def build_frame(frames: List[Frame]) -> "WebFrame":
            first, *tail = frames
            frame = WebFrame(str(first), sample.metrics.time)
            if tail:
                child = build_frame(tail)
                frame.add_child(child)
                frame.height = child.height + 1
            else:
                frame.value = sample.metrics.time
            return frame

        sample = Sample.parse(text)
        process_frame = WebFrame(sample.pid, sample.metrics.time)
        thread_frame = WebFrame(sample.thread, sample.metrics.time)

        if sample.frames:
            thread_frame.add_child(build_frame(sample.frames))

        thread_frame.height = len(sample.frames) + 1

        process_frame.add_child(thread_frame)
        process_frame.height = thread_frame.height + 1

        root = WebFrame.new_root()
        root.add_child(process_frame)
        root.value = process_frame.value
        root.height = process_frame.height + 1

        return root

    @staticmethod
    def new_root() -> "WebFrame":
        """Create a new root frame."""
        return WebFrame("root", 0)

    def to_dict(self) -> dict:
        """Return the frame data in the form of a ``dict``."""
        return {
            "name": self.name,
            "value": self.value,
            "children": [c.to_dict() for c in self.children],
        }

    def __repr__(self) -> str:
        """The frame representation of its fields."""
        return (
            type(self).__name__
            + f"({ {s: getattr(self, s) for s in ['name', 'value', 'children', 'height']} })"
        )


class DataPool:
    """Data collection pool to serve each client handler.

    When the data is sent, the content of the pool is reset to just a root
    node. Each received sample should be added to each data pool so that each
    client can get the data that was seen from the moment they connected.
    """

    def __init__(self, austin: AsyncAustin) -> None:
        self._austin = austin
        self.max = 0
        self.data = WebFrame.new_root()
        self.samples = 0

    def add(self, frame: WebFrame) -> None:
        """Add frame to the data pool."""
        self.data += frame
        self.samples += 1

    async def send(self, ws: web.WebSocketResponse) -> bool:
        """Send profiling data to websocket asynchronously.

        Returns ``True`` on success, ``False`` otherwise.
        """
        try:
            cpu = self._austin.get_child_process().cpu_percent()
            memory = self._austin.get_child_process().memory_full_info()[0] >> 20
        except psutil.NoSuchProcess:
            return False

        data = self.data.to_dict()

        if self.data.height > self.max:
            self.max = self.data.height

        payload = {
            "type": "sample",
            "data": data,
            "height": self.max,
            "samples": self.samples,
            "cpu": cpu,
            "memory": memory,
        }

        await ws.send_str(json.dumps(payload))

        self.data = WebFrame.new_root()

        return True
