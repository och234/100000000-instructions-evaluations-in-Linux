"""Tests for SparseMatrix. Stdlib only.

Run from this directory:  python3 -m unittest -v
or:                       python3 test_sparse_matrix.py
"""

import random
import unittest

from sparse_matrix import SparseMatrix


def dense_add(a, b):
    return [[x + y for x, y in zip(ra, rb)] for ra, rb in zip(a, b)]


def dense_matmul(a, b):
    n_inner = len(b)
    n_cols = len(b[0]) if b else 0
    return [[sum(row[k] * b[k][j] for k in range(n_inner)) for j in range(n_cols)] for row in a]


def random_dense(rng, n_rows, n_cols, density):
    return [[rng.randint(-5, 5) if rng.random() < density else 0 for _ in range(n_cols)] for _ in range(n_rows)]


class TestConstruction(unittest.TestCase):
    def test_empty_matrix(self):
        m = SparseMatrix(3, 4)
        self.assertEqual(m.shape, (3, 4))
        self.assertEqual(m.nnz, 0)
        self.assertEqual(m.get(2, 3), 0)
        self.assertEqual(list(m.items()), [])

    def test_zero_dimensions_allowed(self):
        self.assertEqual(SparseMatrix(0, 0).shape, (0, 0))
        self.assertEqual(SparseMatrix(0, 5).to_dense(), [])

    def test_invalid_dimensions(self):
        for bad in [(-1, 2), (2, -1), (1.5, 2), ("3", 2), (True, 2)]:
            with self.subTest(dims=bad), self.assertRaises(ValueError):
                SparseMatrix(*bad)

    def test_huge_shape_costs_nothing_until_populated(self):
        # A dense 10^9 x 10^9 matrix is impossible; sparse storage is O(nnz).
        n = 10**9
        m = SparseMatrix(n, n)
        m[n - 1, n - 1] = 7
        m[0, 123_456_789] = -2
        self.assertEqual(m.nnz, 2)
        self.assertEqual(m[n - 1, n - 1], 7)
        self.assertEqual(m[500, 500], 0)

    def test_from_dense_round_trip(self):
        grid = [[0, 1, 0], [0, 0, 0], [2.5, 0, -3]]
        m = SparseMatrix.from_dense(grid)
        self.assertEqual(m.shape, (3, 3))
        self.assertEqual(m.nnz, 3)
        self.assertEqual(m.to_dense(), grid)

    def test_from_dense_rejects_ragged(self):
        with self.assertRaises(ValueError):
            SparseMatrix.from_dense([[1, 2], [3]])

    def test_from_dense_empty(self):
        self.assertEqual(SparseMatrix.from_dense([]).shape, (0, 0))
        self.assertEqual(SparseMatrix.from_dense([[]]).shape, (1, 0))

    def test_from_triples_unsorted_duplicates_and_zeros(self):
        m = SparseMatrix.from_triples(3, 3, [(2, 2, 9), (0, 1, 4), (2, 2, 5), (1, 1, 0)])
        self.assertEqual(m.nnz, 2)
        self.assertEqual(m[2, 2], 5, "duplicate coordinate: last write wins")
        self.assertEqual(m[1, 1], 0)

    def test_from_triples_validates_bounds(self):
        with self.assertRaises(IndexError):
            SparseMatrix.from_triples(2, 2, [(2, 0, 1)])


class TestElementOps(unittest.TestCase):
    def setUp(self):
        self.m = SparseMatrix(4, 5)

    def test_insert_and_lookup(self):
        self.m.set(1, 2, 3.5)
        self.assertEqual(self.m.get(1, 2), 3.5)
        self.assertEqual(self.m.nnz, 1)

    def test_update_does_not_change_nnz(self):
        self.m[1, 2] = 3
        self.m[1, 2] = 8
        self.assertEqual(self.m[1, 2], 8)
        self.assertEqual(self.m.nnz, 1)

    def test_set_zero_deletes(self):
        self.m[1, 2] = 3
        self.m[1, 2] = 0
        self.assertEqual(self.m[1, 2], 0)
        self.assertEqual(self.m.nnz, 0)

    def test_set_zero_on_absent_is_noop(self):
        self.m[1, 2] = 0
        self.assertEqual(self.m.nnz, 0)

    def test_delete_reports_whether_anything_was_removed(self):
        self.m[3, 4] = 1
        self.assertTrue(self.m.delete(3, 4))
        self.assertFalse(self.m.delete(3, 4))
        self.assertEqual(self.m.nnz, 0)

    def test_del_operator(self):
        self.m[0, 0] = 1
        del self.m[0, 0]
        self.assertEqual(self.m[0, 0], 0)
        del self.m[0, 0]  # idempotent, no KeyError

    def test_empty_rows_are_released(self):
        # White-box check of the storage invariant: deleting the last entry of
        # a row must free the row, or memory grows with churn instead of nnz.
        self.m[2, 0] = 1
        self.m[2, 3] = 1
        self.m.delete(2, 0)
        self.assertIn(2, self.m._rows)
        self.m.delete(2, 3)
        self.assertNotIn(2, self.m._rows)

    def test_out_of_range(self):
        for r, c in [(4, 0), (0, 5), (-1, 0), (0, -1)]:
            with self.subTest(r=r, c=c):
                with self.assertRaises(IndexError):
                    self.m.get(r, c)
                with self.assertRaises(IndexError):
                    self.m.set(r, c, 1)
                with self.assertRaises(IndexError):
                    self.m.delete(r, c)

    def test_non_int_indices(self):
        for r, c in [(1.0, 0), (0, "1"), (True, 0), (None, 0)]:
            with self.subTest(r=r, c=c), self.assertRaises(TypeError):
                self.m.get(r, c)

    def test_items_row_major_order(self):
        for r, c, v in [(3, 1, 5), (0, 4, 1), (3, 0, 2), (1, 2, 7), (0, 0, 9)]:
            self.m[r, c] = v
        self.assertEqual(
            list(self.m.items()),
            [(0, 0, 9), (0, 4, 1), (1, 2, 7), (3, 0, 2), (3, 1, 5)],
        )
        self.assertEqual(list(self.m), list(self.m.items()))


class TestAddition(unittest.TestCase):
    def test_basic(self):
        a = SparseMatrix.from_dense([[1, 0, 0], [0, 2, 0]])
        b = SparseMatrix.from_dense([[0, 3, 0], [0, 4, 5]])
        self.assertEqual((a + b).to_dense(), [[1, 3, 0], [0, 6, 5]])

    def test_cancellation_leaves_no_explicit_zeros(self):
        a = SparseMatrix.from_dense([[1, 0], [0, -2]])
        b = SparseMatrix.from_dense([[-1, 0], [0, 2]])
        s = a + b
        self.assertEqual(s.nnz, 0)
        self.assertEqual(s._rows, {})
        self.assertEqual(s, SparseMatrix(2, 2))

    def test_partial_cancellation(self):
        a = SparseMatrix.from_dense([[1, 1], [0, 0]])
        b = SparseMatrix.from_dense([[-1, 0], [0, 4]])
        s = a + b
        self.assertEqual(s.to_dense(), [[0, 1], [0, 4]])
        self.assertEqual(s.nnz, 2)

    def test_operands_are_not_mutated_or_aliased(self):
        a = SparseMatrix.from_dense([[1, 2], [0, 0]])
        b = SparseMatrix.from_dense([[0, 0], [3, 0]])
        a_before, b_before = a.to_dense(), b.to_dense()
        s = a + b
        s[0, 0] = 100
        s[1, 0] = 0
        self.assertEqual(a.to_dense(), a_before)
        self.assertEqual(b.to_dense(), b_before)

    def test_add_empty(self):
        a = SparseMatrix.from_dense([[0, 7], [8, 0]])
        self.assertEqual(a + SparseMatrix(2, 2), a)
        self.assertEqual(SparseMatrix(2, 2) + a, a)

    def test_commutative(self):
        rng = random.Random(1)
        a = SparseMatrix.from_dense(random_dense(rng, 6, 7, 0.3))
        b = SparseMatrix.from_dense(random_dense(rng, 6, 7, 0.3))
        self.assertEqual(a + b, b + a)

    def test_shape_mismatch(self):
        with self.assertRaises(ValueError):
            SparseMatrix(2, 3) + SparseMatrix(3, 2)

    def test_type_mismatch(self):
        with self.assertRaises(TypeError):
            SparseMatrix(2, 2) + 1
        with self.assertRaises(TypeError):
            SparseMatrix(2, 2).add([[0, 0], [0, 0]])


class TestMultiplication(unittest.TestCase):
    def test_basic(self):
        a = SparseMatrix.from_dense([[1, 0, 0], [-1, 0, 3]])
        b = SparseMatrix.from_dense([[7, 0, 0], [0, 0, 0], [0, 0, 1]])
        self.assertEqual((a @ b).to_dense(), [[7, 0, 0], [-7, 0, 3]])

    def test_non_square_shapes(self):
        a = SparseMatrix.from_dense([[1, 2, 0]])        # 1x3
        b = SparseMatrix.from_dense([[1], [0], [4]])    # 3x1
        self.assertEqual((a @ b).to_dense(), [[1]])
        self.assertEqual((b @ a).to_dense(), [[1, 2, 0], [0, 0, 0], [4, 8, 0]])

    def test_identity(self):
        rng = random.Random(2)
        a = SparseMatrix.from_dense(random_dense(rng, 5, 5, 0.4))
        eye = SparseMatrix.from_triples(5, 5, [(i, i, 1) for i in range(5)])
        self.assertEqual(a @ eye, a)
        self.assertEqual(eye @ a, a)

    def test_cancellation_leaves_no_explicit_zeros(self):
        a = SparseMatrix.from_dense([[1, 1]])
        b = SparseMatrix.from_dense([[2], [-2]])
        p = a @ b
        self.assertEqual(p.nnz, 0)
        self.assertEqual(p._rows, {})

    def test_shape_mismatch(self):
        with self.assertRaises(ValueError):
            SparseMatrix(2, 3) @ SparseMatrix(2, 3)

    def test_large_sparse_product(self):
        n = 10**6
        a = SparseMatrix.from_triples(n, n, [(0, 5, 2), (999_999, 42, 3)])
        b = SparseMatrix.from_triples(n, n, [(5, 999_999, 10), (42, 0, -1)])
        p = a @ b
        self.assertEqual(list(p.items()), [(0, 999_999, 20), (999_999, 0, -3)])


class TestEquality(unittest.TestCase):
    def test_equal_regardless_of_insertion_order(self):
        a = SparseMatrix.from_triples(3, 3, [(0, 0, 1), (2, 1, 5)])
        b = SparseMatrix.from_triples(3, 3, [(2, 1, 5), (0, 0, 1)])
        self.assertEqual(a, b)

    def test_shape_matters(self):
        self.assertNotEqual(SparseMatrix(2, 3), SparseMatrix(3, 2))

    def test_not_equal_to_other_types(self):
        self.assertNotEqual(SparseMatrix(1, 1), [[0]])

    def test_unhashable(self):
        with self.assertRaises(TypeError):
            hash(SparseMatrix(1, 1))


class TestAgainstDenseReference(unittest.TestCase):
    """Randomised differential tests: every op must agree with a dense model."""

    def test_random_mutations(self):
        rng = random.Random(42)
        n_rows, n_cols = 8, 6
        dense = [[0] * n_cols for _ in range(n_rows)]
        m = SparseMatrix(n_rows, n_cols)
        for step in range(5000):
            r, c = rng.randrange(n_rows), rng.randrange(n_cols)
            op = rng.random()
            if op < 0.5:
                v = rng.choice([0, rng.randint(-9, 9)])
                m.set(r, c, v)
                dense[r][c] = v
            elif op < 0.75:
                m.delete(r, c)
                dense[r][c] = 0
            else:
                self.assertEqual(m.get(r, c), dense[r][c], f"step {step}")
            expected_nnz = sum(v != 0 for row in dense for v in row)
            self.assertEqual(m.nnz, expected_nnz, f"step {step}")
        self.assertEqual(m.to_dense(), dense)
        self.assertTrue(all(m._rows.values()), "no empty row dicts retained")

    def test_random_add_and_multiply(self):
        rng = random.Random(7)
        for trial in range(200):
            p, q, s = rng.randint(1, 7), rng.randint(1, 7), rng.randint(1, 7)
            density = rng.choice([0.0, 0.1, 0.3, 0.8])
            da = random_dense(rng, p, q, density)
            db = random_dense(rng, p, q, density)
            dc = random_dense(rng, q, s, density)
            a, b, c = (SparseMatrix.from_dense(d) for d in (da, db, dc))
            with self.subTest(trial=trial):
                self.assertEqual((a + b).to_dense(), dense_add(da, db))
                self.assertEqual((a @ c).to_dense(), dense_matmul(da, dc))
                expected_nnz = sum(v != 0 for row in dense_matmul(da, dc) for v in row)
                self.assertEqual((a @ c).nnz, expected_nnz)


if __name__ == "__main__":
    unittest.main()
