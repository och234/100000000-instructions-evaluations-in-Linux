"""Reference solutions for the GM top-10 coding list (see gm-top-10-coding-questions.md).

Ordered by the frequency x recency ranking from score_questions.py, plus one wildcard.
Run `python3 gm_top10.py` to execute the self-checks (including brute-force cross-checks).
"""

import bisect
import heapq
import itertools
import random
import threading
import time
from collections import Counter, defaultdict, deque
from typing import Callable, Dict, List, Optional


# 1. Number of Connected Components in an Undirected Graph (LC 323)
#    Union-Find with path halving + union by size -- ~O(E * alpha(V))
def count_components(n: int, edges: List[List[int]]) -> int:
    parent = list(range(n))
    size = [1] * n

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    components = n
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra == rb:
            continue
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]
        components -= 1
    return components


# 2. Number of Steps to Reduce a Number in Binary Representation to One (LC 1404)
#    Scan right-to-left with a carry instead of converting to int -- O(n) time, O(1) space
def num_steps(s: str) -> int:
    steps = carry = 0
    for i in range(len(s) - 1, 0, -1):
        bit = int(s[i]) + carry
        if bit == 1:  # odd: +1 (carries out), then /2
            steps += 2
            carry = 1
        else:  # 0 or 2 -> even: just /2, carry unchanged
            steps += 1
    return steps + carry


# 3. Merge Intervals (LC 56) -- O(n log n) time, O(n) space
def merge_intervals(intervals: List[List[int]]) -> List[List[int]]:
    merged: List[List[int]] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


# 3b. Follow-up: intervals stream in one at a time, out of order (GM AV report).
#     Keep the merged set as two parallel sorted lists. add() is O(log n) to locate plus
#     O(n) list splice (memmove); use sortedcontainers.SortedList for O(log n) amortized.
#     Each stored interval is absorbed at most once, so merging is amortized O(1) per add.
class StreamingIntervals:
    def __init__(self):
        self.starts: List[int] = []  # disjoint closed intervals, sorted (so ends are sorted too)
        self.ends: List[int] = []
        self.total_covered = 0  # covered time of everything seen, including flushed intervals

    def add(self, start: int, end: int) -> None:
        i = bisect.bisect_left(self.ends, start)  # first stored interval with end >= start
        j = bisect.bisect_right(self.starts, end)  # first stored interval with start > end
        if i < j:  # stored intervals i..j-1 overlap or touch the new one
            self.total_covered -= sum(self.ends[k] - self.starts[k] for k in range(i, j))
            start, end = min(start, self.starts[i]), max(end, self.ends[j - 1])
        self.starts[i:j] = [start]
        self.ends[i:j] = [end]
        self.total_covered += end - start

    def get_intervals(self) -> List[List[int]]:
        return [[s, e] for s, e in zip(self.starts, self.ends)]

    def flush(self, watermark: int) -> List[List[int]]:
        """Caller promises no future interval starts before `watermark`: emit and drop the
        intervals that can no longer change, so memory stays bounded on an endless stream."""
        k = bisect.bisect_left(self.ends, watermark)  # end < watermark -> final
        done = [[s, e] for s, e in zip(self.starts[:k], self.ends[:k])]
        del self.starts[:k], self.ends[:k]
        return done


# 4. Maximum Sum of 3 Non-Overlapping Subarrays (LC 689)
#    Window sums + best-left / best-right index arrays, sweep the middle window.
#    Ties resolve to the lexicographically smallest answer. O(n) time, O(n) space.
def max_sum_of_three_subarrays(nums: List[int], k: int) -> List[int]:
    w = [0] * (len(nums) - k + 1)
    cur = sum(nums[:k])
    w[0] = cur
    for i in range(1, len(w)):
        cur += nums[i + k - 1] - nums[i - 1]
        w[i] = cur
    left = [0] * len(w)  # argmax of w[0..i], leftmost on ties
    for i in range(1, len(w)):
        left[i] = i if w[i] > w[left[i - 1]] else left[i - 1]
    right = [len(w) - 1] * len(w)  # argmax of w[i..], leftmost on ties
    for i in range(len(w) - 2, -1, -1):
        right[i] = i if w[i] >= w[right[i + 1]] else right[i + 1]
    best_total, best = -1, []
    for j in range(k, len(w) - k):
        a, c = left[j - k], right[j + k]
        total = w[a] + w[j] + w[c]
        if total > best_total:  # strict: keeps the earliest (lexicographically smallest) j
            best_total, best = total, [a, j, c]
    return best


# 5a. Minimum Path Sum (LC 64) -- right/down only, 1-D DP, O(mn) time, O(n) space
def min_path_sum(grid: List[List[int]]) -> int:
    cols = len(grid[0])
    dp = [float("inf")] * cols
    dp[0] = 0
    for row in grid:
        dp[0] += row[0]
        for c in range(1, cols):
            dp[c] = min(dp[c], dp[c - 1]) + row[c]
    return dp[-1]


# 5b. Follow-up: 4-directional moves, non-negative cell costs, -1 = obstacle -> Dijkstra
#     O(mn log(mn)). Returns -1 if unreachable.
def min_cost_path(grid: List[List[int]]) -> int:
    rows, cols = len(grid), len(grid[0])
    if grid[0][0] < 0 or grid[-1][-1] < 0:
        return -1
    dist = [[float("inf")] * cols for _ in range(rows)]
    dist[0][0] = grid[0][0]
    heap = [(grid[0][0], 0, 0)]
    while heap:
        d, r, c = heapq.heappop(heap)
        if (r, c) == (rows - 1, cols - 1):
            return d
        if d > dist[r][c]:
            continue
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] >= 0:
                nd = d + grid[nr][nc]
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heapq.heappush(heap, (nd, nr, nc))
    return -1


# 6. LRU Cache (LC 146) -- hashmap + hand-written doubly linked list, O(1) get/put
class _Node:
    __slots__ = ("key", "val", "prev", "next")

    def __init__(self, key: int = 0, val: int = 0):
        self.key, self.val = key, val
        self.prev: Optional["_Node"] = None
        self.next: Optional["_Node"] = None


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.map: Dict[int, _Node] = {}
        self.head, self.tail = _Node(), _Node()  # sentinels: head.next is MRU, tail.prev is LRU
        self.head.next, self.tail.prev = self.tail, self.head

    def _unlink(self, node: _Node) -> None:
        node.prev.next, node.next.prev = node.next, node.prev

    def _push_front(self, node: _Node) -> None:
        node.prev, node.next = self.head, self.head.next
        self.head.next.prev = node
        self.head.next = node

    def get(self, key: int) -> int:
        node = self.map.get(key)
        if node is None:
            return -1
        self._unlink(node)
        self._push_front(node)
        return node.val

    def put(self, key: int, value: int) -> None:
        if key in self.map:
            node = self.map[key]
            node.val = value
            self._unlink(node)
            self._push_front(node)
            return
        if len(self.map) == self.capacity:
            lru = self.tail.prev
            self._unlink(lru)
            del self.map[lru.key]
        node = _Node(key, value)
        self.map[key] = node
        self._push_front(node)


# 6b. Follow-up: TTL + thread safety + single-flight loads (Cruise "LRU using timestamps").
#     - Expired entries are never returned. get() drops them lazily; put() first purges
#       every expired entry (min-heap of expiry times, lazy deletion), then evicts the LRU.
#     - One lock guards every operation: get() moves nodes, so readers mutate too
#       (a read/write lock buys nothing here). Scale-out answer: shard by hash(key).
#     - get_or_load(): only one thread runs the loader for a missing key; the others wait.
#       The loader runs outside the lock, so slow I/O never blocks the whole cache.
#     get O(1); put O(log n) amortized because of the heap (O(1) if every entry shares
#     one TTL: expiry order == insertion order, so a second linked list replaces the heap).
class _TTLNode(_Node):
    __slots__ = ("expires_at",)


class TTLLRUCache:
    def __init__(self, capacity: int, default_ttl: float, clock: Callable[[], float] = time.monotonic):
        self.capacity, self.default_ttl, self.clock = capacity, default_ttl, clock
        self.map: Dict[object, _TTLNode] = {}
        self.head, self.tail = _TTLNode(), _TTLNode()
        self.head.next, self.tail.prev = self.tail, self.head
        self.expiry_heap: List = []  # (expires_at, seq, key); stale rows skipped on pop
        self.seq = itertools.count()
        self.lock = threading.Lock()
        self.inflight: Dict[object, list] = {}  # key -> [Event, result, error]

    # --- linked-list helpers (caller holds the lock) ---
    def _unlink(self, node):
        node.prev.next, node.next.prev = node.next, node.prev

    def _push_front(self, node):
        node.prev, node.next = self.head, self.head.next
        self.head.next.prev = node
        self.head.next = node

    def _remove(self, node):
        self._unlink(node)
        del self.map[node.key]

    def _purge_expired(self, now):
        heap = self.expiry_heap
        while heap and heap[0][0] <= now:
            expires_at, _, key = heapq.heappop(heap)
            node = self.map.get(key)
            if node is not None and node.expires_at == expires_at:  # skip stale heap rows
                self._remove(node)
        if len(heap) > 2 * len(self.map) + 16:  # bound memory used by stale rows
            self.expiry_heap = [(n.expires_at, next(self.seq), k) for k, n in self.map.items()]
            heapq.heapify(self.expiry_heap)

    # --- public API ---
    def get(self, key, default=-1):
        with self.lock:
            node = self.map.get(key)
            if node is None:
                return default
            if node.expires_at <= self.clock():
                self._remove(node)
                return default
            self._unlink(node)
            self._push_front(node)
            return node.val

    def put(self, key, value, ttl: Optional[float] = None) -> None:
        with self.lock:
            self._put_locked(key, value, ttl)

    def _put_locked(self, key, value, ttl):
        now = self.clock()
        self._purge_expired(now)
        expires_at = now + (self.default_ttl if ttl is None else ttl)
        node = self.map.get(key)
        if node is not None:
            node.val, node.expires_at = value, expires_at
            self._unlink(node)
        else:
            if len(self.map) >= self.capacity:
                self._remove(self.tail.prev)  # every entry left is live: evict the LRU
            node = _TTLNode(key, value)
            node.expires_at = expires_at
            self.map[key] = node
        self._push_front(node)
        heapq.heappush(self.expiry_heap, (expires_at, next(self.seq), key))

    def get_or_load(self, key, loader: Callable[[object], object], ttl: Optional[float] = None):
        _missing = object()
        with self.lock:
            node = self.map.get(key)
            if node is not None and node.expires_at > self.clock():
                self._unlink(node)
                self._push_front(node)
                return node.val
            slot = self.inflight.get(key)
            leader = slot is None
            if leader:
                slot = self.inflight[key] = [threading.Event(), _missing, None]
        if not leader:
            slot[0].wait()
            if slot[2] is not None:
                raise slot[2]
            return slot[1]
        try:
            value = loader(key)  # slow I/O happens outside the lock
        except BaseException as exc:  # failures are shared with waiters, never cached
            with self.lock:
                slot[2] = exc
                del self.inflight[key]
            slot[0].set()
            raise
        with self.lock:
            self._put_locked(key, value, ttl)
            slot[1] = value
            del self.inflight[key]
        slot[0].set()
        return value


# 7. Course Schedule I / II (LC 207 / 210) -- Kahn's topological sort, O(V + E).
#    find_order returns [] when the dependency graph has a cycle.
def find_order(num_tasks: int, prerequisites: List[List[int]]) -> List[int]:
    graph = defaultdict(list)
    indegree = [0] * num_tasks
    for task, dep in prerequisites:
        graph[dep].append(task)
        indegree[task] += 1
    queue = deque(t for t in range(num_tasks) if indegree[t] == 0)
    order = []
    while queue:
        t = queue.popleft()
        order.append(t)
        for nxt in graph[t]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    return order if len(order) == num_tasks else []


def can_finish(num_tasks: int, prerequisites: List[List[int]]) -> bool:
    return len(find_order(num_tasks, prerequisites)) == num_tasks


# 7b. Follow-up without durations: minimum number of stages if every job takes one
#     stage and a stage runs any number of ready jobs (LC 1136 Parallel Courses).
#     BFS level by level = longest chain counted in jobs. Returns -1 on a cycle. O(V + E).
def min_stages(num_tasks: int, prerequisites: List[List[int]]) -> int:
    graph = defaultdict(list)
    indegree = [0] * num_tasks
    for task, dep in prerequisites:
        graph[dep].append(task)
        indegree[task] += 1
    level = [t for t in range(num_tasks) if indegree[t] == 0]
    stages = done = 0
    while level:
        stages += 1
        done += len(level)
        nxt = []
        for t in level:
            for child in graph[t]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    nxt.append(child)
        level = nxt
    return stages if done == num_tasks else -1


# 7c. Follow-up: report the cycle that blocks the schedule (iterative 3-color DFS).
#     Returns [v, ..., u, v] following dependency -> task edges, or [] if acyclic.
def find_cycle(num_tasks: int, prerequisites: List[List[int]]) -> List[int]:
    graph = defaultdict(list)
    for task, dep in prerequisites:
        graph[dep].append(task)
    color = [0] * num_tasks  # 0 = unvisited, 1 = on the DFS stack, 2 = finished
    parent = [-1] * num_tasks
    for start in range(num_tasks):
        if color[start]:
            continue
        color[start] = 1
        stack = [(start, iter(graph[start]))]
        while stack:
            u, children = stack[-1]
            v = next(children, None)
            if v is None:
                color[u] = 2
                stack.pop()
            elif color[v] == 0:
                color[v], parent[v] = 1, u
                stack.append((v, iter(graph[v])))
            elif color[v] == 1:  # back edge u -> v closes a cycle
                cycle = [u]
                while cycle[-1] != v:
                    cycle.append(parent[cycle[-1]])
                return cycle[::-1] + [v]
    return []


# 7d. Follow-up (pipeline framing): every task has a duration, unlimited workers ->
#     minimum makespan = longest path in the DAG (LC 2050 Parallel Courses III). O(V + E).
def min_makespan(durations: List[int], prerequisites: List[List[int]]) -> int:
    order = find_order(len(durations), prerequisites)
    if len(order) != len(durations):
        raise ValueError("dependency cycle")
    deps = defaultdict(list)
    for task, dep in prerequisites:
        deps[task].append(dep)
    finish = [0] * len(durations)
    for t in order:
        finish[t] = durations[t] + max((finish[d] for d in deps[t]), default=0)
    return max(finish, default=0)


# 8. Minimum Deletions to Make Character Frequencies Unique (LC 1647)
#    Greedy: largest counts first, decrement until an unused count (0 is always allowed).
def min_deletions(s: str) -> int:
    used, deletions = set(), 0
    for f in sorted(Counter(s).values(), reverse=True):
        while f > 0 and f in used:
            f -= 1
            deletions += 1
        used.add(f)
    return deletions


# 9. Implement Trie (LC 208) -- O(L) per op
_END = object()  # end-of-word marker that can never collide with a character key


class Trie:
    def __init__(self):
        self.root: Dict = {}

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            node = node.setdefault(ch, {})
        node[_END] = True

    def _walk(self, s: str) -> Optional[Dict]:
        node = self.root
        for ch in s:
            node = node.get(ch)
            if node is None:
                return None
        return node

    def search(self, word: str) -> bool:
        node = self._walk(word)
        return node is not None and _END in node

    def starts_with(self, prefix: str) -> bool:
        return self._walk(prefix) is not None


# 10. Synonymous Sentences (LC 1258) -- union-find groups + DFS over word positions.
#     Output is every sentence, lexicographically sorted.
def generate_sentences(synonyms: List[List[str]], text: str) -> List[str]:
    parent: Dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in synonyms:
        parent[find(a)] = find(b)

    groups = defaultdict(list)
    for word in list(parent):
        groups[find(word)].append(word)
    for words in groups.values():
        words.sort()

    tokens = text.split()
    result: List[str] = []

    def dfs(i: int, built: List[str]) -> None:
        if i == len(tokens):
            result.append(" ".join(built))
            return
        word = tokens[i]
        options = groups[find(word)] if word in parent else [word]
        for option in options:
            built.append(option)
            dfs(i + 1, built)
            built.pop()

    dfs(0, [])
    return sorted(result)


# Wildcard. In-memory key-value store with nested, isolated transactions
#    (Cruise's most-reported 1-hour screen question, 2019-2021).
#    A stack of per-transaction layers; deletes are tombstones so "deleted in this
#    transaction" differs from "never touched". get is O(depth); set/delete are O(1);
#    commit merges the innermost layer into its parent in O(size of that layer).
_TOMBSTONE = object()


class TransactionalKV:
    def __init__(self):
        self._base: Dict[str, object] = {}
        self._layers: List[Dict[str, object]] = []

    def get(self, key: str):
        for layer in reversed(self._layers):
            if key in layer:
                value = layer[key]
                return None if value is _TOMBSTONE else value
        return self._base.get(key)

    def set(self, key: str, value) -> None:
        (self._layers[-1] if self._layers else self._base)[key] = value

    def delete(self, key: str) -> None:
        if self._layers:
            self._layers[-1][key] = _TOMBSTONE
        else:
            self._base.pop(key, None)

    def begin(self) -> None:
        self._layers.append({})

    def rollback(self) -> None:
        if not self._layers:
            raise RuntimeError("no transaction")
        self._layers.pop()

    def commit(self) -> None:
        """Commit the innermost transaction into its parent (or into the store)."""
        if not self._layers:
            raise RuntimeError("no transaction")
        top = self._layers.pop()
        if self._layers:
            self._layers[-1].update(top)  # tombstones propagate to the parent layer
            return
        for key, value in top.items():
            if value is _TOMBSTONE:
                self._base.pop(key, None)
            else:
                self._base[key] = value


# ---------------------------------------------------------------------------
# Self-checks
# ---------------------------------------------------------------------------
def _bf_steps(s: str) -> int:
    n, c = int(s, 2), 0
    while n != 1:
        n = n // 2 if n % 2 == 0 else n + 1
        c += 1
    return c


def _bf_three(nums: List[int], k: int) -> List[int]:
    n, best = len(nums), None
    for a in range(n - k + 1):
        for b in range(a + k, n - k + 1):
            for c in range(b + k, n - k + 1):
                t = sum(nums[a:a + k]) + sum(nums[b:b + k]) + sum(nums[c:c + k])
                if best is None or t > best[0]:  # ascending loops -> first max is lexicographically smallest
                    best = (t, [a, b, c])
    return best[1]


def _bf_deletions(s: str) -> int:
    fs = list(Counter(s).values())
    best = None
    for targets in itertools.product(*[range(f + 1) for f in fs]):
        nonzero = [t for t in targets if t]
        if len(nonzero) == len(set(nonzero)):
            cost = sum(fs) - sum(targets)
            best = cost if best is None else min(best, cost)
    return best


class _SnapshotKV:
    """Brute-force reference: every transaction is a deep copy of the whole store."""

    def __init__(self):
        self.stack = [{}]

    def get(self, k):
        return self.stack[-1].get(k)

    def set(self, k, v):
        self.stack[-1][k] = v

    def delete(self, k):
        self.stack[-1].pop(k, None)

    def begin(self):
        self.stack.append(dict(self.stack[-1]))

    def rollback(self):
        if len(self.stack) == 1:
            raise RuntimeError("no transaction")
        self.stack.pop()

    def commit(self):
        if len(self.stack) == 1:
            raise RuntimeError("no transaction")
        top = self.stack.pop()
        self.stack[-1] = top


def _run_checks() -> None:
    rng = random.Random(7)

    # 1
    assert count_components(5, [[0, 1], [1, 2], [3, 4]]) == 2
    assert count_components(5, [[0, 1], [1, 2], [2, 3], [3, 4]]) == 1
    assert count_components(3, []) == 3
    assert count_components(4, [[0, 1], [1, 0], [0, 1]]) == 3  # duplicate / reversed edges

    # 2
    assert num_steps("1101") == 6 and num_steps("10") == 1 and num_steps("1") == 0
    for n in range(1, 4096):
        assert num_steps(bin(n)[2:]) == _bf_steps(bin(n)[2:])

    # 4
    assert max_sum_of_three_subarrays([1, 2, 1, 2, 6, 7, 5, 1], 2) == [0, 3, 5]
    assert max_sum_of_three_subarrays([1, 2, 1, 2, 1, 2, 1, 2, 1], 2) == [0, 2, 4]
    for _ in range(2000):
        k = rng.randint(1, 3)
        nums = [rng.randint(1, 4) for _ in range(rng.randint(3 * k, 3 * k + 7))]  # many ties
        assert max_sum_of_three_subarrays(nums, k) == _bf_three(nums, k), (nums, k)

    # 3
    assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
    assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
    assert merge_intervals([[1, 10], [2, 3]]) == [[1, 10]]
    assert merge_intervals([]) == []
    stream = StreamingIntervals()
    for iv in ([8, 10], [1, 3], [15, 18], [2, 6], [6, 8]):  # out of order; [6, 8] bridges two
        stream.add(*iv)
    assert stream.get_intervals() == [[1, 10], [15, 18]] and stream.total_covered == 12
    for _ in range(2000):  # vs. re-merging everything seen so far
        stream, seen, flushed, watermark = StreamingIntervals(), [], [], 0
        for _ in range(rng.randint(0, 25)):
            if rng.random() < 0.15:
                watermark += rng.randint(0, 6)
                flushed += stream.flush(watermark)
                continue
            a = watermark + rng.randint(0, 30)
            iv = [a, a + rng.randint(0, 6)]
            seen.append(iv)
            stream.add(*iv)
            merged = merge_intervals([list(x) for x in seen])
            assert flushed + stream.get_intervals() == merged
            assert stream.total_covered == sum(e - b for b, e in merged)

    # 5
    assert min_path_sum([[1, 3, 1], [1, 5, 1], [4, 2, 1]]) == 7
    assert min_path_sum([[1, 2, 3], [4, 5, 6]]) == 12
    assert min_cost_path([[1, 3, 1], [1, 5, 1], [4, 2, 1]]) == 7
    # going up/left is required to route around the obstacles
    assert min_cost_path([[1, 1, 1], [-1, -1, 1], [1, 1, 1], [1, -1, -1], [1, 1, 1]]) == 11
    assert min_cost_path([[1, -1], [-1, 1]]) == -1

    # 6
    cache = LRUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    assert cache.get(1) == 1
    cache.put(3, 3)  # evicts 2
    assert cache.get(2) == -1
    cache.put(4, 4)  # evicts 1
    assert cache.get(1) == -1 and cache.get(3) == 3 and cache.get(4) == 4
    cache.put(3, 30)  # update moves to MRU
    cache.put(5, 5)  # evicts 4
    assert cache.get(4) == -1 and cache.get(3) == 30

    # 8
    assert min_deletions("aab") == 0 and min_deletions("aaabbbcc") == 2 and min_deletions("ceabaacb") == 2
    for _ in range(2000):
        s = "".join(rng.choice("abcd") for _ in range(rng.randint(1, 12)))
        assert min_deletions(s) == _bf_deletions(s), s

    # 6b: TTL semantics under a fake clock, cross-checked against a brute-force model
    class _Clock:
        def __init__(self):
            self.t = 0.0

        def __call__(self):
            return self.t

    clk = _Clock()
    c = TTLLRUCache(2, default_ttl=10, clock=clk)
    c.put("a", 1)
    clk.t = 5
    c.put("b", 2, ttl=1)
    assert c.get("a") == 1 and c.get("b") == 2
    clk.t = 6  # b expires exactly at t=6 (expires_at <= now)
    assert c.get("b") == -1
    c.put("c", 3)
    c.put("d", 4)  # full with a, c live -> evicts LRU a
    assert c.get("a") == -1 and c.get("c") == 3 and c.get("d") == 4
    clk.t = 100  # everything expired: put must purge, not evict a live entry
    c.put("e", 5)
    assert len(c.map) == 1 and c.get("e") == 5

    for _ in range(300):
        clk = _Clock()
        cap = rng.randint(1, 4)
        fast = TTLLRUCache(cap, default_ttl=5, clock=clk)
        model = {}  # key -> [value, expires_at, last_used]
        tick = itertools.count()
        for _ in range(80):
            clk.t += rng.choice([0, 0, 1, 2, 3])
            key = rng.choice("abcdef")
            now = clk.t
            if rng.random() < 0.5:
                got = fast.get(key)
                ent = model.get(key)
                if ent and ent[1] > now:
                    ent[2] = next(tick)
                    assert got == ent[0]
                else:
                    model.pop(key, None)
                    assert got == -1
            else:
                v, ttl = rng.randint(0, 9), rng.choice([None, 1, 2, 4])
                fast.put(key, v, ttl)
                for k in [k for k, e in model.items() if e[1] <= now]:
                    del model[k]
                if key not in model and len(model) >= cap:
                    del model[min(model, key=lambda k: model[k][2])]
                model[key] = [v, now + (5 if ttl is None else ttl), next(tick)]
            live = {k for k, e in model.items() if e[1] > now}
            assert {k for k, n in fast.map.items() if n.expires_at > now} == live

    # 6b: thread safety -- hammer one cache from 8 threads, then check invariants
    shared, bad_reads = TTLLRUCache(32, default_ttl=1e9), []

    def hammer(seed):  # exceptions in threads don't fail the run, so record them instead
        r = random.Random(seed)
        for _ in range(5000):
            k = r.randint(0, 100)
            if r.random() < 0.5:
                shared.put(k, k * 10)
            elif shared.get(k) not in (-1, k * 10):
                bad_reads.append(k)

    threads = [threading.Thread(target=hammer, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not bad_reads
    walk, node = 0, shared.head.next
    while node is not shared.tail:
        assert shared.map[node.key] is node and node.next.prev is node
        walk, node = walk + 1, node.next
    assert walk == len(shared.map) <= 32

    # 6b: single-flight -- 16 threads miss the same key, the loader runs exactly once
    calls, barrier = [], threading.Barrier(16)
    sf = TTLLRUCache(4, default_ttl=60)

    def slow_loader(k):
        calls.append(k)
        time.sleep(0.05)
        return f"shard-{k}"

    results = []

    def worker():
        barrier.wait()
        results.append(sf.get_or_load("s3", slow_loader))

    threads = [threading.Thread(target=worker) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert calls == ["s3"] and results == ["shard-s3"] * 16 and sf.get("s3") == "shard-s3"
    # a failing loader propagates to the caller and is not cached
    try:
        sf.get_or_load("bad", lambda k: 1 / 0)
        raise AssertionError("expected ZeroDivisionError")
    except ZeroDivisionError:
        pass
    assert sf.get("bad") == -1 and not sf.inflight

    # 7
    order = find_order(4, [[1, 0], [2, 0], [3, 1], [3, 2]])
    pos = {t: i for i, t in enumerate(order)}
    assert len(order) == 4 and pos[0] < pos[1] < pos[3] and pos[0] < pos[2] < pos[3]
    assert find_order(2, [[0, 1], [1, 0]]) == [] and not can_finish(2, [[0, 1], [1, 0]])
    assert can_finish(3, []) and can_finish(0, [])
    # LC 1136 examples (converted to 0-indexed [task, dependency])
    assert min_stages(3, [[2, 0], [2, 1]]) == 2
    assert min_stages(3, [[1, 0], [2, 1], [0, 2]]) == -1
    for _ in range(2000):
        n = rng.randint(1, 7)
        pairs = [[rng.randrange(n), rng.randrange(n)] for _ in range(rng.randint(0, 10))]
        acyclic = can_finish(n, pairs)
        cycle = find_cycle(n, pairs)
        assert (cycle == []) == acyclic and (min_stages(n, pairs) == -1) == (not acyclic)
        edges = {(dep, task) for task, dep in pairs}
        assert cycle == [] or (cycle[0] == cycle[-1] and all(e in edges for e in zip(cycle, cycle[1:])))
        if acyclic:  # stages == longest chain (in jobs), computed independently
            order, longest = find_order(n, pairs), {}
            for t in order:
                longest[t] = 1 + max((longest[d] for task, d in pairs if task == t), default=0)
            assert min_stages(n, pairs) == max(longest.values())
    # LC 2050 examples, converted to 0-indexed [task, dependency] pairs
    assert min_makespan([3, 2, 5], [[2, 0], [2, 1]]) == 8
    assert min_makespan([1, 2, 3, 4, 5], [[4, 0], [4, 1], [4, 2], [3, 2], [4, 3]]) == 12

    # 9
    trie = Trie()
    trie.insert("apple")
    assert trie.search("apple") and not trie.search("app") and trie.starts_with("app")
    trie.insert("app")
    assert trie.search("app") and not trie.starts_with("b")
    trie.insert("a$")  # arbitrary alphabet: '$' must not collide with the end marker
    assert not trie.search("a") and trie.search("a$") and not trie.search("app$")

    # 10
    assert generate_sentences(
        [["happy", "joy"], ["sad", "sorrow"], ["joy", "cheerful"]],
        "I am happy today but was sad yesterday",
    ) == [
        "I am cheerful today but was sad yesterday",
        "I am cheerful today but was sorrow yesterday",
        "I am happy today but was sad yesterday",
        "I am happy today but was sorrow yesterday",
        "I am joy today but was sad yesterday",
        "I am joy today but was sorrow yesterday",
    ]
    assert generate_sentences([], "a b") == ["a b"]

    # Wildcard: hand-written scenarios
    kv = TransactionalKV()
    kv.set("a", 1)
    kv.begin()
    kv.set("a", 2)
    kv.begin()
    kv.delete("a")
    assert kv.get("a") is None  # deleted in the inner transaction
    kv.rollback()
    assert kv.get("a") == 2  # inner delete discarded
    kv.begin()
    kv.set("b", 5)
    kv.commit()  # b merges into the outer transaction only
    assert kv.get("b") == 5
    kv.rollback()  # outer rollback discards a=2 and b=5
    assert kv.get("a") == 1 and kv.get("b") is None
    for op in (kv.commit, kv.rollback):
        try:
            op()
            raise AssertionError("expected RuntimeError")
        except RuntimeError:
            pass
    # Wildcard: random ops vs the deep-copy reference
    for _ in range(300):
        fast, ref = TransactionalKV(), _SnapshotKV()
        for _ in range(60):
            op = rng.choice(["get", "set", "delete", "begin", "begin", "commit", "rollback"])
            key = rng.choice("xyz")
            if op in ("commit", "rollback"):
                errors = []
                for impl in (fast, ref):
                    try:
                        getattr(impl, op)()
                        errors.append(False)
                    except RuntimeError:
                        errors.append(True)
                assert errors[0] == errors[1]
            elif op == "set":
                v = rng.randint(0, 3)
                fast.set(key, v)
                ref.set(key, v)
            elif op == "begin":
                fast.begin()
                ref.begin()
            else:
                if op == "delete":
                    fast.delete(key)
                    ref.delete(key)
                assert fast.get(key) == ref.get(key)
            for k in "xyz":
                assert fast.get(k) == ref.get(k)

    print("all checks passed (10 problems + wildcard, brute-force cross-checks included)")


if __name__ == "__main__":
    _run_checks()
