# Sparse Matrix Class: interview question and reference solution

`sparse_matrix.py` holds the solution, and `test_sparse_matrix.py` holds its tests. Both use only the Python 3 standard library.

```bash
cd sparse_matrix
python3 -m unittest -v        # or: python3 test_sparse_matrix.py
```

---

## 1. The question

> Most entries of a matrix are zero. Storing it as a dense 2-D array wastes
> memory, and the waste grows with `rows × cols`. Design and implement a
> `SparseMatrix` class whose storage grows only with the number of non-zero
> entries.
>
> The input is either a dense 2-D array or a list of `(row, col, value)`
> triples. The triples can arrive in any order.
>
> Implement:
>
> 1. **Construction.** `SparseMatrix(rows, cols)`, plus a builder for each
>    input format (dense array and triples).
> 2. **Lookup.** `get(r, c)` returns the value at `(r, c)`, or `0` if the
>    entry is not stored.
> 3. **Insert or update.** `set(r, c, value)`.
> 4. **Delete.** `delete(r, c)` removes an entry.
> 5. **Addition.** `add(other)` returns `self + other` as a new sparse
>    matrix.
> 6. **Tests.** Write tests you can run in the interview to show the class
>    works, edge cases included.
>
> Explain why you chose your storage format and give the time and space
> complexity of every operation.

Follow-ups reported for this question, roughly from most to least common:

- **Multiply** two sparse matrices, without converting to dense.
- How would the design change if the matrix were **built once and then
  read many times**?
- **Iterate** over the non-zero entries in a deterministic order.
- Values are **floats**, and a sum cancels to `1e-17` instead of `0`. What
  happens?

### Clarifying questions to ask, and what this solution assumes

| Question | Assumption here |
|---|---|
| Is the matrix mutated a lot, or built once? | Mixed, with updates and deletes (the prompt says so). Hash-based storage is used. |
| Out-of-range or negative index? | `IndexError`. Python-style negative indexing is **not** supported. |
| `set(r, c, 0)`? | Deletes the entry. An explicit zero is never stored. |
| `delete` of an entry that isn't stored? | Does nothing and returns `False`. Every cell of a matrix exists, so deleting an implicit zero is not an error. |
| Duplicate coordinates in the triples? | The last one wins, the same as calling `set` again. (Summing them is the other common choice; ask which they want.) |
| Shapes don't match for `add` or `multiply`? | `ValueError`. |
| Does `add` mutate an operand? | No. It returns a new matrix, and the result shares no storage with either operand. |
| Value type? | Any numeric type. Zero is tested with `== 0`, exactly. |

---

## 2. Design

### Storage choice

The data is stored as **row-indexed dictionaries of keys**: `{row: {col: value}}`, holding only the non-zero entries.

| Format | get / set / delete | Row scan | Add | Multiply | Fits |
|---|---|---|---|---|---|
| Dense 2-D array | O(1) | O(C) | O(R·C) | O(R·C·K) | Small or dense matrices only |
| COO: list of `(r, c, v)` | O(nnz) | O(nnz) | O(nnz log nnz) | Poor | Ingest or interchange format |
| Flat DOK: `{(r, c): v}` | O(1) avg | **O(nnz)** | O(nnz) | Poor: you can't find "row k of B" | Random access only |
| **Row DOK: `{r: {c: v}}`** | **O(1) avg** | **O(nnz(row))** | **O(nnz)** | **Good** | **Mixed reads, writes and arithmetic. Used here.** |
| CSR: `indptr`, `indices`, `data` arrays | O(log nnz(row)) get, **O(nnz)** insert or delete | O(nnz(row)), cache-friendly | O(nnz) merge | Best | Built once, read many times, and the hot numeric kernels |

The extra row level is what makes multiplication cheap. To compute `A @ B`, each non-zero `A[i][k]` needs only row `k` of `B`, and row DOK gives that row in O(1). Flat DOK would need a scan of all of `B`.

### Invariants (enforced on every mutating path)

1. **No explicit zeros.** This holds for `set(.., 0)`, for cancellation in `add` (`1 + -1`), and for cancellation in `multiply` (`1·2 + 1·-2`). Because of it, `nnz` is exact and `__eq__` can compare storage directly.
2. **No empty row dictionaries.** When a row's last entry is deleted, the row's dictionary is freed. Memory is therefore O(nnz), not O(rows ever touched).
3. **`nnz` is kept as a counter**, so reading it is O(1).

### Complexity

| Operation | Time | Notes |
|---|---|---|
| `get`, `set`, `delete`, `m[r, c]` | O(1) average | Hash lookups |
| `nnz`, `shape` | O(1) | |
| `from_triples(t)` | O(t) | |
| `from_dense`, `to_dense` | O(R·C) | Intrinsic to the dense side |
| `items()` (row-major order) | O(nnz log nnz) | Sorts the keys; storage is unordered |
| `add` | O(nnz(A) + nnz(B)) | Copies A, then merges B |
| `multiply` (`@`) | O(Σ over non-zero A[i][k] of nnz(B row k)) | Doesn't depend on R, C or K. Empty rows cost nothing. |
| Space | O(nnz + non-empty rows) | A 10⁹ × 10⁹ matrix with 2 entries stores 2 entries |

---

## 3. Talking points for the follow-ups

- **Built once, read many times, i.e. performance-critical.** Build the matrix in row DOK, then freeze it into CSR. CSR stores each row as contiguous `indices` and `data` arrays, so a row scan is a sequential stream with no pointer-chasing through hash buckets. That makes far better use of the cache and the prefetcher. scipy uses the same pattern: `dok_matrix` or `lil_matrix` to construct, then `tocsr()` for arithmetic. Inserting into CSR costs O(nnz), so it is the wrong format while the matrix is still changing.
- **Floating-point cancellation.** An exact `== 0` keeps values like `1e-17` as non-zeros. Fixing this needs an `atol` threshold (prune when `abs(v) <= atol`), and that is an API decision, because it silently changes values. It is not on by default here.
- **Column access, or computing `Aᵀ @ B`.** Either keep a second, column-indexed map (writes cost twice as much, column scans become cheap), or build the transpose once in O(nnz).
- **Thread safety.** The class is not thread-safe. Wrap it in a single writer lock, or make it immutable (CSR) and share it freely.
- **Matrices that don't fit on one machine.** Split them into row blocks or 2-D tiles. Addition then splits cleanly by block. Multiplication becomes a shuffle-and-join on the shared index `k`, which is the MapReduce SpGEMM pattern.

---

## 4. Test strategy (`test_sparse_matrix.py`, 39 tests)

- **Unit tests.** Construction with valid and invalid shapes, 0×N shapes, and ragged dense input. Insert, update, delete, `set(.., 0)`, deleting an entry that isn't stored, bounds errors, wrong index types, row-major iteration, and equality.
- **Invariant tests.** Cancellation in `add` and `multiply` leaves no stored zeros. Empty rows are freed. The result of `add` shares no storage with its operands: mutating the result leaves A and B unchanged.
- **Scale tests.** 10⁹ × 10⁹ and 10⁶ × 10⁶ matrices with a handful of entries run instantly. These would run out of memory if anything in the code were dense.
- **Randomised comparison against a plain dense matrix.** There are 5,000 seeded random `set`, `delete` and `get` steps, checked against a dense model after every step. There are also 200 random shape and density trials of `add` and `@`, checked against straightforward dense implementations. The seeds are fixed, so the results are the same on every run.

The suite was checked by planting bugs on purpose: copying A's rows by reference in `add`, storing zeros after cancellation in `add`, keeping empty rows, and keeping zeros in the product of `multiply`. The suite fails for each of the four.

---

## 5. Where the question comes from

The statement in §1 combines the reported versions of this question. **It is not the verbatim wording of any single report.**

- **Amazon, Glassdoor, Nov 2012** ([report](https://www.glassdoor.com.au/Interview/Amazon-Interview-E6036-RVW2426743.htm)). In a phone screen with a senior engineer, the candidate was given entries as a `(xi, xj, value)` class. They were asked to put the sparse matrix into a more efficient data structure and to provide a way to get values back out of it.
- **Pinterest, Glassdoor, 2022 and later.** The reported variants ask candidates to store a sparse matrix and implement **addition and multiplication** from scratch, without matrix libraries. These are the source of the multiply follow-up.
- The Senior SDE and 2023 full-time and internship reports cited for this question could not be retrieved: their host did not resolve from the environment where this was written. The specifics in those reports, such as exact method names or input sizes, may differ from §1.
