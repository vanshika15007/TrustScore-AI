import re
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse

from fastapi import HTTPException, status

API_KEY = __import__("os").environ.get("TRUSTSCORE_API_KEY")
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 30
_request_log: dict[str, deque[float]] = defaultdict(deque)


class TaskState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskRecord:
    task_id: str
    url: str
    state: TaskState
    result: dict | None = None
    error: str | None = None


class InMemoryTaskStore:
    """Track background scan jobs in memory so the UI can poll for status."""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskRecord] = {}

    def create(self, url: str, state: TaskState, result: dict | None = None) -> TaskRecord:
        task = TaskRecord(task_id=uuid.uuid4().hex, url=url, state=state, result=result)
        self._tasks[task.task_id] = task
        return task

    def get(self, task_id: str) -> TaskRecord | None:
        return self._tasks.get(task_id)

    def update(self, task_id: str, *, state: TaskState, result: dict | None = None, error: str | None = None) -> None:
        task = self._tasks[task_id]
        task.state = state
        task.result = result
        task.error = error

    def size(self) -> int:
        return len(self._tasks)


def normalize_url(raw_url: str) -> str:
    url = raw_url.strip()
    if not url:
        raise ValueError("Invalid URL: value is empty.")
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Invalid URL: please enter a proper website address.")
    return url


def domain_from_url(url: str) -> str:
    return urlparse(url).netloc.lower()


def spam_ratio(text: str) -> float:
    words = re.findall(r"\b\w+\b", text.lower())
    if not words:
        return 1.0

    spam_words = {"free", "money", "urgent", "winner", "bonus", "click", "offer", "limited"}
    hits = sum(word in spam_words for word in words)
    repeated = len(words) - len(set(words))
    return min(1.0, (hits / len(words)) + (repeated / max(len(words), 1)) * 0.2)


def text_length_score(length: int) -> float:
    if length >= 6000:
        return 1.0
    if length >= 3000:
        return 0.82
    if length >= 1500:
        return 0.64
    if length >= 700:
        return 0.42
    return 0.18


def enforce_api_key(provided_key: str | None) -> None:
    if API_KEY and provided_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )


def rate_limit(client_id: str) -> None:
    now = time.time()
    bucket = _request_log[client_id]

    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW:
        bucket.popleft()

    if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before making more requests.",
        )

    bucket.append(now)
