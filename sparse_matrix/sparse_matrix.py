"""Sparse matrix backed by a row-indexed dictionary of keys.

Storage is ``{row: {col: value}}`` holding only non-zero entries. This gives
O(1) average get/set/delete, O(nnz(row)) row scans, and memory proportional to
the number of non-zeros rather than rows * cols. Rows that become empty are
dropped, so a matrix of any shape with no non-zeros costs O(1) memory.

Invariant: no explicit zero is ever stored, and no empty row dict is ever kept.
Every mutating path (set, delete, add, multiply) preserves it.
"""

from __future__ import annotations

from typing import Dict, Iterable, Iterator, List, Sequence, Tuple

Value = float  # ints are accepted too (PEP 484 numeric tower)
Triple = Tuple[int, int, Value]


class SparseMatrix:
    __slots__ = ("_n_rows", "_n_cols", "_rows", "_nnz")

    def __init__(self, n_rows: int, n_cols: int) -> None:
        for name, dim in (("n_rows", n_rows), ("n_cols", n_cols)):
            if not _is_int(dim) or dim < 0:
                raise ValueError(f"{name} must be a non-negative int, got {dim!r}")
        self._n_rows = n_rows
        self._n_cols = n_cols
        self._rows: Dict[int, Dict[int, Value]] = {}
        self._nnz = 0

    # ------------------------------------------------------------------ build

    @classmethod
    def from_triples(cls, n_rows: int, n_cols: int, triples: Iterable[Triple]) -> SparseMatrix:
        """Build from (row, col, value) triples in any order.

        Duplicate coordinates follow ``set`` semantics: the last one wins.
        Zero values are not stored.
        """
        m = cls(n_rows, n_cols)
        for r, c, v in triples:
            m.set(r, c, v)
        return m

    @classmethod
    def from_dense(cls, grid: Sequence[Sequence[Value]]) -> SparseMatrix:
        n_rows = len(grid)
        n_cols = len(grid[0]) if n_rows else 0
        m = cls(n_rows, n_cols)
        for r, row in enumerate(grid):
            if len(row) != n_cols:
                raise ValueError(f"ragged input: row {r} has {len(row)} columns, expected {n_cols}")
            for c, v in enumerate(row):
                if v != 0:
                    m._put(r, c, v)
        return m

    def to_dense(self) -> List[List[Value]]:
        """Materialise as a list of lists. O(rows * cols) memory: small matrices only."""
        out: List[List[Value]] = [[0] * self._n_cols for _ in range(self._n_rows)]
        for r, row in self._rows.items():
            for c, v in row.items():
                out[r][c] = v
        return out

    # ------------------------------------------------------------ properties

    @property
    def shape(self) -> Tuple[int, int]:
        return self._n_rows, self._n_cols

    @property
    def nnz(self) -> int:
        return self._nnz

    # ---------------------------------------------------------- element ops

    def get(self, r: int, c: int) -> Value:
        self._check_index(r, c)
        row = self._rows.get(r)
        return 0 if row is None else row.get(c, 0)

    def set(self, r: int, c: int, value: Value) -> None:
        """Insert or update. Setting zero removes the entry."""
        self._check_index(r, c)
        if value == 0:
            self._remove(r, c)
        else:
            self._put(r, c, value)

    def delete(self, r: int, c: int) -> bool:
        """Remove the entry at (r, c). Returns True if a non-zero was removed.

        Idempotent: every cell of a matrix exists, so deleting an implicit zero
        is a no-op rather than an error.
        """
        self._check_index(r, c)
        return self._remove(r, c)

    def __getitem__(self, key: Tuple[int, int]) -> Value:
        return self.get(*key)

    def __setitem__(self, key: Tuple[int, int], value: Value) -> None:
        self.set(*key, value)

    def __delitem__(self, key: Tuple[int, int]) -> None:
        self.delete(*key)

    def items(self) -> Iterator[Triple]:
        """Yield non-zero (row, col, value) in row-major order. O(nnz log nnz)."""
        for r in sorted(self._rows):
            row = self._rows[r]
            for c in sorted(row):
                yield r, c, row[c]

    def __iter__(self) -> Iterator[Triple]:
        return self.items()

    # ------------------------------------------------------------ algebra

    def add(self, other: SparseMatrix) -> SparseMatrix:
        """Element-wise sum. O(nnz(self) + nnz(other)); operands are not modified."""
        if not isinstance(other, SparseMatrix):
            raise TypeError(f"cannot add SparseMatrix and {type(other).__name__}")
        if self.shape != other.shape:
            raise ValueError(f"shape mismatch for addition: {self.shape} vs {other.shape}")

        result = SparseMatrix(*self.shape)
        # Row dicts are copied, never shared, so mutating the result cannot
        # leak back into either operand.
        result._rows = {r: dict(row) for r, row in self._rows.items()}
        result._nnz = self._nnz
        for r, other_row in other._rows.items():
            for c, v in other_row.items():
                result._accumulate(r, c, v)
        return result

    def __add__(self, other: object) -> SparseMatrix:
        if not isinstance(other, SparseMatrix):
            return NotImplemented
        return self.add(other)

    def multiply(self, other: SparseMatrix) -> SparseMatrix:
        """Matrix product self @ other.

        For each non-zero A[i][k] only row k of B is visited, so the cost is
        O(sum over non-zeros A[i][k] of nnz(B row k)) -- independent of the
        dense dimensions, and zero work for empty rows of either operand.
        """
        if not isinstance(other, SparseMatrix):
            raise TypeError(f"cannot multiply SparseMatrix and {type(other).__name__}")
        if self._n_cols != other._n_rows:
            raise ValueError(f"shape mismatch for multiplication: {self.shape} @ {other.shape}")

        result = SparseMatrix(self._n_rows, other._n_cols)
        for i, a_row in self._rows.items():
            acc: Dict[int, Value] = {}
            for k, a in a_row.items():
                b_row = other._rows.get(k)
                if b_row is None:
                    continue
                for j, b in b_row.items():
                    acc[j] = acc.get(j, 0) + a * b
            # Partial products can cancel; keep the no-explicit-zero invariant.
            out_row = {j: v for j, v in acc.items() if v != 0}
            if out_row:
                result._rows[i] = out_row
                result._nnz += len(out_row)
        return result

    def __matmul__(self, other: object) -> SparseMatrix:
        if not isinstance(other, SparseMatrix):
            return NotImplemented
        return self.multiply(other)

    # ------------------------------------------------------------ dunder

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SparseMatrix):
            return NotImplemented
        # Valid because of the invariant: equal matrices have identical storage.
        return self.shape == other.shape and self._rows == other._rows

    def __repr__(self) -> str:
        return f"SparseMatrix(shape={self.shape}, nnz={self._nnz})"

    # ------------------------------------------------------------ internals

    def _check_index(self, r: int, c: int) -> None:
        if not (_is_int(r) and _is_int(c)):
            raise TypeError(f"indices must be ints, got ({r!r}, {c!r})")
        if not (0 <= r < self._n_rows and 0 <= c < self._n_cols):
            raise IndexError(f"index ({r}, {c}) out of range for shape {self.shape}")

    def _put(self, r: int, c: int, value: Value) -> None:
        row = self._rows.setdefault(r, {})
        if c not in row:
            self._nnz += 1
        row[c] = value

    def _remove(self, r: int, c: int) -> bool:
        row = self._rows.get(r)
        if row is None or c not in row:
            return False
        del row[c]
        self._nnz -= 1
        if not row:
            del self._rows[r]
        return True

    def _accumulate(self, r: int, c: int, delta: Value) -> None:
        new = self._rows.get(r, {}).get(c, 0) + delta
        if new == 0:
            self._remove(r, c)
        else:
            self._put(r, c, new)


def _is_int(x: object) -> bool:
    # bool is an int subclass; m[True, 0] is almost certainly a bug.
    return isinstance(x, int) and not isinstance(x, bool)
