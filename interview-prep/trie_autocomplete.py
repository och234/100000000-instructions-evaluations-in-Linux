"""Implement Trie (LC 208) extended for the autocomplete follow-up (LC 642).

Built on a TrieNode/children/is_end style Trie. Two versions:
  AutocompleteSystem        -- trie + DFS under the prefix node (the version to write first)
  AutocompleteSystemCached  -- each node caches its top-3, so a keystroke is O(1)
Run `python3 trie_autocomplete.py` for brute-force cross-checks.
"""

import heapq
import random
from collections import defaultdict
from typing import List, Optional


class TrieNode:
    def __init__(self, char=""):
        self.char = char
        self.children = {}
        self.is_end = False
        self.count = 0      # NEW: hot degree = times this exact sentence was typed
        self.word = None    # NEW: full sentence stored at its end node (no path rebuild in DFS)
        self.top = []       # NEW (cached version only): best 3 sentences under this prefix


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str, times: int = 1) -> None:  # CHANGED: accepts a count
        node = self.root
        for c in word:
            if c not in node.children:
                node.children[c] = TrieNode(c)
            node = node.children[c]
        node.is_end = True
        node.word = word
        node.count += times

    def _find(self, prefix: str) -> Optional[TrieNode]:  # NEW: shared prefix walk
        node = self.root
        for c in prefix:
            if c not in node.children:
                return None
            node = node.children[c]
        return node

    def search(self, word: str) -> bool:
        node = self._find(word)
        return node is not None and node.is_end

    def startsWith(self, prefix: str) -> bool:
        return self._find(prefix) is not None

    def collect(self, node: TrieNode) -> List[tuple]:  # NEW: every sentence under node
        out, stack = [], [node]
        while stack:  # iterative DFS: no recursion limit on long sentences
            cur = stack.pop()
            if cur.is_end:
                out.append((-cur.count, cur.word))  # sort key: hottest first, then ASCII
            stack.extend(cur.children.values())
        return out

    def top_k(self, prefix: str, k: int = 3) -> List[str]:  # NEW: LC 1268-style query
        node = self._find(prefix)
        if node is None:
            return []
        return [w for _, w in heapq.nsmallest(k, self.collect(node))]


class AutocompleteSystem:
    """LC 642. input(c): O(1) cursor step + O(subtree) DFS + O(m log 3) selection."""

    def __init__(self, sentences: List[str], times: List[int]):
        self.trie = Trie()
        for s, t in zip(sentences, times):
            self.trie.insert(s, t)
        self.prefix = ""
        self.node = self.trie.root  # cursor: never re-walk the typed prefix

    def input(self, c: str) -> List[str]:
        if c == "#":
            self.trie.insert(self.prefix)  # store the finished sentence (+1)
            self.prefix, self.node = "", self.trie.root
            return []
        self.prefix += c
        if self.node is not None:
            self.node = self.node.children.get(c)
        if self.node is None:  # dead prefix stays dead until '#'
            return []
        return [w for _, w in heapq.nsmallest(3, self.trie.collect(self.node))]


class AutocompleteSystemCached(AutocompleteSystem):
    """Follow-up: O(1) per keystroke. insert becomes O(L * k log k).

    Safe because counts only ever increase: a sentence that falls out of a node's top-3
    can only get back in by being typed again, and that insert walks its whole path and
    refreshes every node on it. (With deletes or decreasing counts this breaks; you would
    need to recompute from children's caches or keep a lazy-deletion heap.)
    """

    K = 3

    def __init__(self, sentences: List[str], times: List[int]):
        super().__init__([], [])
        for s, t in zip(sentences, times):
            self._insert(s, t)

    def _insert(self, sentence: str, times: int = 1) -> None:
        self.trie.insert(sentence, times)
        hot = self.trie._find(sentence).count
        node = self.trie.root
        for c in sentence:
            node = node.children[c]
            top = [(h, w) for h, w in node.top if w != sentence]
            top.append((-hot, sentence))
            top.sort()
            node.top = top[: self.K]

    def input(self, c: str) -> List[str]:
        if c == "#":
            self._insert(self.prefix)
            self.prefix, self.node = "", self.trie.root
            return []
        self.prefix += c
        if self.node is not None:
            self.node = self.node.children.get(c)
        return [w for _, w in self.node.top] if self.node is not None else []


# ---------------------------------------------------------------------------
# Self-checks
# ---------------------------------------------------------------------------
def _brute(hist, prefix):
    return sorted((s for s in hist if s.startswith(prefix)), key=lambda s: (-hist[s], s))[:3]


def _run_checks() -> None:
    # Original LC 208 behaviour is unchanged
    t = Trie()
    t.insert("apple")
    assert t.search("apple") and not t.search("app") and t.startsWith("app")
    t.insert("app")
    assert t.search("app")
    assert t.top_k("ap") == ["app", "apple"] and t.top_k("b") == []

    for cls in (AutocompleteSystem, AutocompleteSystemCached):
        # LC 642 example
        a = cls(["i love you", "island", "iroman", "i love leetcode"], [5, 3, 2, 2])
        assert a.input("i") == ["i love you", "island", "i love leetcode"]
        assert a.input(" ") == ["i love you", "i love leetcode"]
        assert a.input("a") == []
        assert a.input("#") == []
        assert a.input("i") == ["i love you", "island", "i love leetcode"]  # "i a" has count 1
        # randomized sessions vs brute force (tiny alphabet -> lots of shared prefixes and ties)
        rng = random.Random(1)
        for _ in range(400):
            sents = ["".join(rng.choice("ab ") for _ in range(rng.randint(1, 4))) for _ in range(6)]
            times = [rng.randint(1, 3) for _ in sents]
            ac, hist = cls(sents, times), defaultdict(int)
            for s, n in zip(sents, times):
                hist[s] += n
            for _ in range(6):
                typed = "".join(rng.choice("ab ") for _ in range(rng.randint(1, 4)))
                for i, ch in enumerate(typed):
                    assert ac.input(ch) == _brute(hist, typed[: i + 1]), (cls.__name__, sents, typed)
                assert ac.input("#") == []
                hist[typed] += 1
    print("trie autocomplete: LC 642 example + 4800 randomized sessions match brute force (both versions)")


if __name__ == "__main__":
    _run_checks()
