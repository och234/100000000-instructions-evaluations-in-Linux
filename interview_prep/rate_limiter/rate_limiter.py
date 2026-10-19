"""Per-client rate limiters.

Each client may make at most ``limit`` requests per ``window`` time units.
Clients are tracked independently, and only admitted requests count toward
the limit.

The original prompt does not say which window semantics it wants (see
README.md), so both common ones are provided behind the same interface:

* SlidingWindowRateLimiter: exact. A request at time t is admitted iff fewer
  than ``limit`` requests were admitted in the half-open interval
  (t - window, t].
* FixedWindowRateLimiter: time is cut into buckets [k*window, (k+1)*window)
  and each client gets ``limit`` requests per bucket. O(1) memory per client,
  but a client can get up to 2*limit requests across a bucket boundary.
"""

from __future__ import annotations

import math
import threading
import time
from abc import ABC, abstractmethod
from collections import deque
from numbers import Real
from typing import Callable, Deque, Dict, Hashable, Optional


def _is_number(x) -> bool:
    # bool is a subclass of int, so RateLimiter(True, 10) would otherwise be
    # accepted as limit=1. Treat it as the bug it almost certainly is.
    return isinstance(x, Real) and not isinstance(x, bool)


def _check_limit(limit) -> int:
    if not _is_number(limit) or not isinstance(limit, int) or limit < 1:
        raise ValueError(f"limit must be a positive int, got {limit!r}")
    return limit


def _check_window(window):
    if not _is_number(window) or not math.isfinite(window) or window <= 0:
        raise ValueError(f"window must be a positive finite number, got {window!r}")
    return window


def _check_timestamp(now) -> None:
    if not _is_number(now) or not math.isfinite(now):
        raise ValueError(f"timestamp must be a finite number, got {now!r}")


def _check_client_id(client_id) -> None:
    if client_id is None or client_id == "":
        raise ValueError("client_id must be a non-empty identifier")
    try:
        hash(client_id)
    except TypeError:
        raise ValueError(
            f"client_id must be hashable, got {type(client_id).__name__}"
        ) from None


class RateLimiter(ABC):
    """Admit at most ``limit`` requests per ``window`` for each client.

    Timestamps can be passed to ``allow`` explicitly (deterministic; what
    tests use) or taken from ``clock``. Units are whatever the caller uses
    consistently; the default clock is time.monotonic, i.e. seconds. Prefer
    integer units (e.g. milliseconds) when exact boundaries matter, since
    float arithmetic can misplace them (0.3 // 0.1 == 2.0).
    """

    def __init__(
        self,
        limit: int,
        window: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limit = _check_limit(limit)
        self.window = _check_window(window)
        if not callable(clock):
            raise ValueError("clock must be callable")
        self._clock = clock
        # Checking the count and recording the request must be one atomic
        # step; otherwise two callers can both see count == limit - 1 and
        # both be admitted.
        self._lock = threading.Lock()
        self._clients: Dict[Hashable, object] = {}

    def allow(self, client_id: Hashable, now: Optional[float] = None) -> bool:
        """Record and admit the request if ``client_id`` is under its limit.

        Returns False, without recording anything, if the client is at its
        limit. Raises ValueError for an invalid client_id or timestamp, or a
        timestamp earlier than this client's previous one; state is left
        unchanged in that case.
        """
        _check_client_id(client_id)
        with self._lock:
            # Read the clock under the lock so timestamps are non-decreasing
            # in the order requests are actually processed.
            if now is None:
                now = self._clock()
            _check_timestamp(now)

            state = self._clients.get(client_id)
            if state is None:
                state = self._clients[client_id] = self._new_state()
            elif now < state.last_seen:
                raise ValueError(
                    f"timestamp {now!r} for client {client_id!r} is earlier "
                    f"than its previous one ({state.last_seen!r})"
                )
            state.last_seen = now
            return self._admit(state, now)

    @abstractmethod
    def _new_state(self):
        """Return empty per-client state with a ``last_seen`` attribute."""

    @abstractmethod
    def _admit(self, state, now) -> bool:
        """Decide on one request and update ``state``. Called under the lock."""


class _SlidingState:
    __slots__ = ("last_seen", "admitted")

    def __init__(self) -> None:
        self.last_seen = -math.inf
        # Timestamps of admitted requests still inside the window, oldest first.
        self.admitted: Deque[float] = deque()


class SlidingWindowRateLimiter(RateLimiter):
    """Exact sliding window, kept as a log of admitted timestamps.

    A request at t is admitted iff fewer than ``limit`` requests were
    admitted in (t - window, t]; a request exactly ``window`` old has
    expired. O(limit) memory per client, amortised O(1) per call (each
    timestamp is appended once and popped once).
    """

    def _new_state(self) -> _SlidingState:
        return _SlidingState()

    def _admit(self, state: _SlidingState, now) -> bool:
        admitted = state.admitted
        cutoff = now - self.window
        while admitted and admitted[0] <= cutoff:
            admitted.popleft()
        if len(admitted) < self.limit:
            admitted.append(now)
            return True
        return False


class _FixedState:
    __slots__ = ("last_seen", "bucket", "count")

    def __init__(self) -> None:
        self.last_seen = -math.inf
        self.bucket = None
        self.count = 0


class FixedWindowRateLimiter(RateLimiter):
    """Fixed window counter.

    Time is split into buckets [k*window, (k+1)*window) aligned to 0, and
    each client gets ``limit`` requests per bucket. O(1) memory and time per
    call, but a client can get up to 2*limit requests in a span shorter than
    ``window`` by bursting at the end of one bucket and the start of the next.
    """

    def _new_state(self) -> _FixedState:
        return _FixedState()

    def _admit(self, state: _FixedState, now) -> bool:
        bucket = now // self.window
        if bucket != state.bucket:
            state.bucket = bucket
            state.count = 0
        if state.count < self.limit:
            state.count += 1
            return True
        return False
