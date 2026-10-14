"""Credit ledger with out-of-order credit grants and expiration.

Problem (OpenAI onsite, "Credits"):
    create_grant(timestamp, grant_id, amount, expiration_timestamp)
    subtract(timestamp, amount)
    get_balance(timestamp) -> int | None

Calls can arrive in any order with respect to their timestamps. A subtract
logged at t=50 may arrive before the grant logged at t=10 that pays for it.
get_balance(t) must answer as if every known event had been applied in
timestamp order.

Semantics (confirm these with the interviewer, since they change the answer):
  * A grant is usable on the half-open interval [timestamp, expiration_timestamp).
  * When several events share a timestamp, apply them in this order:
    expirations first, then grants, then subtracts.
  * A subtract spends from the grant that expires soonest first. This keeps
    the most credit alive.
  * If the active grants cannot cover a subtract, the ledger is overdrawn
    from that point on, and get_balance returns None for every t at or after
    it. Out-of-order grants are replayed, so a late-arriving grant with an
    earlier timestamp can clear the overdraft.

Complexity (n = number of events, g = number of grants live at t):
  * create_grant / subtract: O(n) worst case for the sorted insert. A
    SortedList brings this down to O(log n).
  * get_balance: O(k log n + g), where k is the number of events since the
    cached checkpoint. In-order traffic (the common case) is amortised
    O(log n) per event. An out-of-order write at or before the checkpoint
    forces one full replay, O(n log n).
"""
from __future__ import annotations

import bisect
import heapq
import itertools
from dataclasses import dataclass, field
from typing import Optional

_GRANT, _SUBTRACT = 0, 1  # tie-break: grants before subtracts at equal ts


@dataclass
class _State:
    """Ledger state after applying every event with ts <= `time`."""
    time: float = float("-inf")
    next_idx: int = 0                     # first unapplied index in _events
    heap: list = field(default_factory=list)  # [expiry, seq, grant_id, remaining]
    overdrawn: bool = False

    def copy(self) -> "_State":
        return _State(self.time, self.next_idx, [e[:] for e in self.heap], self.overdrawn)


class Credits:
    def __init__(self) -> None:
        # Sorted by (ts, kind, seq). seq keeps sorting stable and avoids comparing payloads.
        self._events: list[tuple] = []
        self._grant_ids: set[str] = set()
        self._seq = itertools.count()
        self._checkpoint: Optional[_State] = None

    # ------------------------------------------------------------------ writes
    def create_grant(self, timestamp: int, grant_id: str, amount: int,
                     expiration_timestamp: int) -> None:
        if grant_id in self._grant_ids:
            raise ValueError(f"duplicate grant_id {grant_id!r}")
        if amount < 0:
            raise ValueError("amount must be non-negative")
        if expiration_timestamp < timestamp:
            raise ValueError("expiration before grant timestamp")
        self._grant_ids.add(grant_id)
        self._insert((timestamp, _GRANT, next(self._seq), grant_id, amount, expiration_timestamp))

    def subtract(self, timestamp: int, amount: int) -> None:
        if amount < 0:
            raise ValueError("amount must be non-negative")
        self._insert((timestamp, _SUBTRACT, next(self._seq), amount))

    def _insert(self, event: tuple) -> None:
        bisect.insort(self._events, event)
        # An event at or before the checkpoint changes history the checkpoint
        # already summarised, so drop the checkpoint. Later events stay valid
        # because they sort at or after next_idx.
        if self._checkpoint is not None and event[0] <= self._checkpoint.time:
            self._checkpoint = None

    # ------------------------------------------------------------------- reads
    def get_balance(self, timestamp: int) -> Optional[int]:
        cp = self._checkpoint
        if cp is not None and cp.time <= timestamp:
            state = cp.copy()
        else:
            state = _State()  # query is before the checkpoint, or no checkpoint: replay

        self._advance(state, timestamp)

        # Keep the furthest point we have computed, so in-order traffic stays incremental.
        if cp is None or state.time >= cp.time:
            self._checkpoint = state.copy()

        if state.overdrawn:
            return None
        return sum(e[3] for e in state.heap)

    def _advance(self, state: _State, until: int) -> None:
        events, heap = self._events, state.heap
        i = state.next_idx
        while i < len(events) and events[i][0] <= until:
            ev = events[i]
            ts = ev[0]
            self._expire(heap, ts)
            if ev[1] == _GRANT:
                _, _, seq, gid, amount, expiry = ev
                if expiry > ts and amount > 0:
                    heapq.heappush(heap, [expiry, seq, gid, amount])
            else:
                need = ev[3]
                while need and heap:
                    top = heap[0]
                    take = min(need, top[3])
                    top[3] -= take
                    need -= take
                    if top[3] == 0:
                        heapq.heappop(heap)
                if need:
                    state.overdrawn = True
            i += 1
        self._expire(heap, until)
        state.next_idx = i
        state.time = max(state.time, until)

    @staticmethod
    def _expire(heap: list, now: int) -> None:
        while heap and heap[0][0] <= now:
            heapq.heappop(heap)
