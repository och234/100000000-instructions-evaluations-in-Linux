"""Reference solutions for the GM top-10 coding list (see gm-top-10-coding-questions.md).

Run `python3 gm_top10.py` to execute the self-checks at the bottom.
"""

import heapq
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple


# 1. Merge Intervals (LC 56) -- O(n log n) time, O(n) space
def merge_intervals(intervals: List[List[int]]) -> List[List[int]]:
    merged: List[List[int]] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


# 2. Number of Connected Components in an Undirected Graph (LC 323)
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


# 3. LRU Cache (LC 146) -- hashmap + doubly linked list, O(1) get/put
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


# 4a. Minimum Path Sum (LC 64) -- right/down only, 1-D DP, O(mn) time, O(n) space
def min_path_sum(grid: List[List[int]]) -> int:
    cols = len(grid[0])
    dp = [float("inf")] * cols
    dp[0] = 0
    for row in grid:
        dp[0] += row[0]
        for c in range(1, cols):
            dp[c] = min(dp[c], dp[c - 1]) + row[c]
    return dp[-1]


# 4b. Follow-up: 4-directional moves, non-negative cell costs, -1 = obstacle -> Dijkstra
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


# 5. Course Schedule II (LC 210) -- Kahn's topological sort, O(V + E).
#    Returns [] when the dependency graph has a cycle.
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


# 6. Robot grid simulation (reported Cruise screen question).
#    Robot starts at (0, 0) facing east. Each step: move forward if the next cell is in
#    bounds and open (0); otherwise turn right 90 degrees. Stop on reaching `target` or
#    when a (row, col, heading) state repeats (the robot is in a loop).
#    O(rows * cols * 4) time/space -- there are only that many distinct states.
def simulate_robot(grid: List[List[int]], target: Tuple[int, int]) -> Tuple[bool, List[Tuple[int, int]]]:
    dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # E, S, W, N (clockwise = turn right)
    rows, cols = len(grid), len(grid[0])
    r, c, h = 0, 0, 0
    path = [(r, c)]
    seen = set()
    while (r, c) != target:
        if (r, c, h) in seen:
            return False, path
        seen.add((r, c, h))
        dr, dc = dirs[h]
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
            r, c = nr, nc
            path.append((r, c))
        else:
            h = (h + 1) % 4
    return True, path


# 7. Implement Trie (LC 208) -- O(L) per op
class Trie:
    def __init__(self):
        self.root: Dict = {}

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            node = node.setdefault(ch, {})
        node["$"] = True

    def _walk(self, s: str) -> Optional[Dict]:
        node = self.root
        for ch in s:
            node = node.get(ch)
            if node is None:
                return None
        return node

    def search(self, word: str) -> bool:
        node = self._walk(word)
        return node is not None and "$" in node

    def starts_with(self, prefix: str) -> bool:
        return self._walk(prefix) is not None


# 8. Dot Product of Two Sparse Vectors (LC 1570)
#    Store (index, value) pairs sorted by index; two-pointer merge is O(k1 + k2).
#    Follow-up (one dense, one sparse): iterate the sparse side, or binary-search into the
#    longer list for O(k_small * log k_large).
class SparseVector:
    def __init__(self, nums: List[int]):
        self.pairs = [(i, v) for i, v in enumerate(nums) if v != 0]

    def dot_product(self, other: "SparseVector") -> int:
        a, b = self.pairs, other.pairs
        i = j = total = 0
        while i < len(a) and j < len(b):
            if a[i][0] == b[j][0]:
                total += a[i][1] * b[j][1]
                i += 1
                j += 1
            elif a[i][0] < b[j][0]:
                i += 1
            else:
                j += 1
        return total


# 9. Synonymous Sentences (LC 1258) -- union-find groups + DFS over word positions.
#    Output is every sentence, lexicographically sorted.
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


# 10. Serialize and Deserialize Binary Tree (LC 297) -- preorder with null markers, O(n)
class TreeNode:
    def __init__(self, val: int = 0, left: "TreeNode" = None, right: "TreeNode" = None):
        self.val, self.left, self.right = val, left, right


class Codec:
    NULL = "#"

    def serialize(self, root: Optional[TreeNode]) -> str:
        out: List[str] = []
        stack = [root]
        while stack:  # iterative preorder: no recursion-depth limit on skewed trees
            node = stack.pop()
            if node is None:
                out.append(self.NULL)
                continue
            out.append(str(node.val))
            stack.append(node.right)
            stack.append(node.left)
        return ",".join(out)

    def deserialize(self, data: str) -> Optional[TreeNode]:
        tokens = iter(data.split(","))
        first = next(tokens)
        if first == self.NULL:
            return None
        root = TreeNode(int(first))
        # stack of (node, which_child_to_fill_next): 0 = left, 1 = right
        stack = [[root, 0]]
        for tok in tokens:
            node = None if tok == self.NULL else TreeNode(int(tok))
            parent = stack[-1]
            if parent[1] == 0:
                parent[0].left = node
                parent[1] = 1
            else:
                parent[0].right = node
                stack.pop()
            if node is not None:
                stack.append([node, 0])
        return root


# ---------------------------------------------------------------------------
# Self-checks
# ---------------------------------------------------------------------------
def _tree_equal(a: Optional[TreeNode], b: Optional[TreeNode]) -> bool:
    if a is None or b is None:
        return a is b
    return a.val == b.val and _tree_equal(a.left, b.left) and _tree_equal(a.right, b.right)


def _run_checks() -> None:
    # 1
    assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
    assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]
    assert merge_intervals([[1, 10], [2, 3]]) == [[1, 10]]
    assert merge_intervals([]) == []

    # 2
    assert count_components(5, [[0, 1], [1, 2], [3, 4]]) == 2
    assert count_components(5, [[0, 1], [1, 2], [2, 3], [3, 4]]) == 1
    assert count_components(3, []) == 3

    # 3
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

    # 4
    assert min_path_sum([[1, 3, 1], [1, 5, 1], [4, 2, 1]]) == 7
    assert min_path_sum([[1, 2, 3], [4, 5, 6]]) == 12
    assert min_cost_path([[1, 3, 1], [1, 5, 1], [4, 2, 1]]) == 7
    # going up/left is required to route around the obstacles
    assert min_cost_path([[1, 1, 1], [-1, -1, 1], [1, 1, 1], [1, -1, -1], [1, 1, 1]]) == 11
    assert min_cost_path([[1, -1], [-1, 1]]) == -1

    # 5
    order = find_order(4, [[1, 0], [2, 0], [3, 1], [3, 2]])
    pos = {t: i for i, t in enumerate(order)}
    assert len(order) == 4 and pos[0] < pos[1] < pos[3] and pos[0] < pos[2] < pos[3]
    assert find_order(2, [[0, 1], [1, 0]]) == []

    # 6
    grid = [
        [0, 0, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 0, 0],
        [0, 1, 0, 0],
    ]
    reached, path = simulate_robot(grid, (3, 3))
    assert reached and path[-1] == (3, 3)
    reached, _ = simulate_robot([[0, 0], [0, 0]], (5, 5))  # unreachable target -> loops
    assert not reached
    reached, path = simulate_robot([[0, 0, 0], [0, 0, 0], [0, 0, 0]], (1, 1))  # perimeter loop
    assert not reached and (1, 1) not in path

    # 7
    trie = Trie()
    trie.insert("apple")
    assert trie.search("apple") and not trie.search("app") and trie.starts_with("app")
    trie.insert("app")
    assert trie.search("app") and not trie.starts_with("b")

    # 8
    assert SparseVector([1, 0, 0, 2, 3]).dot_product(SparseVector([0, 3, 0, 4, 0])) == 8
    assert SparseVector([0, 1, 0, 0, 0]).dot_product(SparseVector([0, 0, 0, 0, 2])) == 0

    # 9
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

    # 10
    codec = Codec()
    root = TreeNode(1, TreeNode(2), TreeNode(3, TreeNode(4), TreeNode(5)))
    assert _tree_equal(codec.deserialize(codec.serialize(root)), root)
    assert codec.deserialize(codec.serialize(None)) is None
    skewed = TreeNode(0)
    node = skewed
    for i in range(1, 5000):  # deep tree: proves no recursion-limit crash
        node.left = TreeNode(i)
        node = node.left
    assert codec.serialize(codec.deserialize(codec.serialize(skewed))) == codec.serialize(skewed)

    print("all 10 problems: checks passed")


if __name__ == "__main__":
    _run_checks()
