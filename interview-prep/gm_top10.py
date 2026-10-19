"""Reference solutions for the GM top-10 coding list (see gm-top-10-coding-questions.md).

Ordered by the frequency x recency ranking from score_questions.py, plus one wildcard.
Run `python3 gm_top10.py` to execute the self-checks (including brute-force cross-checks).
"""

import heapq
import itertools
import random
from collections import Counter, defaultdict, deque
from typing import Dict, List, Optional


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


# 7b. Follow-up (pipeline framing): every task has a duration, unlimited workers ->
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

    # 7
    order = find_order(4, [[1, 0], [2, 0], [3, 1], [3, 2]])
    pos = {t: i for i, t in enumerate(order)}
    assert len(order) == 4 and pos[0] < pos[1] < pos[3] and pos[0] < pos[2] < pos[3]
    assert find_order(2, [[0, 1], [1, 0]]) == [] and not can_finish(2, [[0, 1], [1, 0]])
    assert can_finish(3, []) and can_finish(0, [])
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
