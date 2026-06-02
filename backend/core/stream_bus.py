from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections import deque
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, AsyncIterator


class StreamEventType(str, Enum):
    SESSION = "session"
    CONTENT = "content"
    THINKING = "thinking"
    STAGE_START = "stage_start"
    STAGE_END = "stage_end"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    SOURCES = "sources"
    PROGRESS = "progress"
    RESULT = "result"
    ERROR = "error"
    DONE = "done"


@dataclass
class StreamEvent:
    type: StreamEventType
    data: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            **self.data,
        }

    def to_sse(self) -> str:
        return f"data: {json.dumps(self.to_dict(), ensure_ascii=False)}\n\n"


class StreamBus:
    """基于 asyncio.Queue 的发布-订阅事件总线。"""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[StreamEvent | None] = asyncio.Queue()
        self._history: deque = deque(maxlen=1000)

    # ---------- 生产者接口 ----------

    def emit(self, event: StreamEvent) -> None:
        self._history.append(event)
        self._queue.put_nowait(event)

    def content(self, text: str) -> None:
        self.emit(StreamEvent(StreamEventType.CONTENT, {"text": text}))

    def thinking(self, text: str) -> None:
        self.emit(StreamEvent(StreamEventType.THINKING, {"text": text}))

    def stage_start(self, stage: str, description: str = "") -> None:
        self.emit(StreamEvent(StreamEventType.STAGE_START, {"stage": stage, "description": description}))

    def stage_end(self, stage: str) -> None:
        self.emit(StreamEvent(StreamEventType.STAGE_END, {"stage": stage}))

    def progress(self, current: int, total: int, message: str = "") -> None:
        self.emit(StreamEvent(StreamEventType.PROGRESS, {"current": current, "total": total, "message": message}))

    def sources(self, sources: list[dict]) -> None:
        self.emit(StreamEvent(StreamEventType.SOURCES, {"sources": sources}))

    def result(self, data: dict) -> None:
        self.emit(StreamEvent(StreamEventType.RESULT, data))

    def error(self, message: str) -> None:
        self.emit(StreamEvent(StreamEventType.ERROR, {"message": message}))

    def done(self) -> None:
        self.emit(StreamEvent(StreamEventType.DONE, {}))
        self._queue.put_nowait(None)

    # ---------- 消费者接口 ----------

    async def subscribe(self) -> AsyncIterator[StreamEvent]:
        while True:
            event = await self._queue.get()
            if event is None:
                break
            yield event

    @property
    def history(self) -> list[StreamEvent]:
        return list(self._history)
