# Per-client rate limiter: candidate report and reference solution

Target: GM Senior Software Developer, Codility assessment (candidate report, Jul–Sep 2026).

## 1. What is known and what is reconstructed

| | Status |
|---|---|
| Enforce a request limit over a time window | Public (candidate report) |
| Track clients independently | Public (candidate report) |
| Validate configuration | Public (candidate report) |
| Exact prompt text, class and method names, language | Gated, unknown |
| Fixed vs sliding window | Gated, unknown |
| Error contract (exception type, what counts as invalid) | Gated, unknown |

Searching public candidate forums (Glassdoor, 1point3acres, Blind, Taro) found
nothing GM-specific about this task. GM Codility reports from earlier years describe
two or three easy-to-medium problems, sometimes in any language. **Everything in
section 2 is a reconstruction of the likely task, not the actual prompt text.**

## 2. Reconstructed prompt

> Implement a `RateLimiter` that limits how many requests each client may make.
>
> * `RateLimiter(limit, window)`: each client may make at most `limit` requests
>   per `window` time units.
> * `allow(client_id, timestamp) -> bool`: called once for every incoming
>   request. Returns `true` and records the request if the client is under its
>   limit. Otherwise returns `false`.
> * Clients are independent. One client reaching its limit must not affect any
>   other client.
> * The constructor must reject invalid configuration (for example a
>   non-positive `limit` or `window`) by raising an error.
> * Timestamps are non-decreasing integers.

Example with `limit = 3, window = 10`:

| Call | Sliding | Fixed | Why |
|---|---|---|---|
| `allow("A", 1)` | true | true | A: 1 of 3 |
| `allow("A", 2)` | true | true | A: 2 of 3 |
| `allow("A", 3)` | true | true | A: 3 of 3 |
| `allow("A", 4)` | false | false | A is at its limit |
| `allow("B", 4)` | true | true | B is tracked separately |
| `allow("A", 10)` | **false** | **true** | Sliding: 1, 2 and 3 are all within (0, 10]. Fixed: the bucket [10, 20) is new |
| `allow("A", 11)` | true | true | Sliding: t=1 has expired. Fixed: 2 of 3 in [10, 20) |

The `t=10` row is where the two readings of the prompt disagree. A hidden test
that targets the window semantics will almost certainly probe a boundary like this.

## 3. Decisions on the ambiguities

| Question | Decision | Reason |
|---|---|---|
| Fixed or sliding window? | Both, behind one interface. **Sliding is the primary answer.** | "Over a time window", with no wording about resets, reads as "in any span of length `window`". Sliding is exact; fixed is O(1) memory but allows 2×limit bursts. |
| Window boundary | A request at `t` counts requests in **(t − window, t]**. A request exactly `window` old has expired. | This makes "limit per window" mean exactly that, with no off-by-one in either direction. |
| Do rejected requests count? | **No.** Only admitted requests use quota. | If they counted, a client that keeps retrying under a sliding window would stay locked out indefinitely. |
| Where does time come from? | An optional `now` argument. If omitted, an injected `clock` is used (default `time.monotonic`). | Explicit timestamps make tests deterministic. A monotonic clock is immune to wall-clock jumps (NTP, DST). |
| Timestamps that go backwards | `ValueError` for that client, and its state is left unchanged. | Accepting them silently would break the ordering of the sliding-window log. Ordering is checked per client, not globally. |
| What counts as invalid configuration | `limit` must be an `int` ≥ 1. `window` must be a finite number > 0. `bool` is rejected for both. `clock` must be callable. | `True` is an `int` in Python, so `RateLimiter(True, 10)` would otherwise be accepted as limit 1. It's a bug, not a configuration. |
| Exception type | `ValueError` for everything, including wrong types | Gives callers and graders one exception to catch. This mirrors Java's `IllegalArgumentException`. |
| Invalid client id | `None`, `""` or an unhashable value raises `ValueError` | Better to fail at the boundary than inside a dict lookup. |
| Concurrency | One lock around check-and-record. The clock is read *inside* the lock. | Without the lock, two callers can both see `count == limit - 1` and both be admitted. Reading the clock under the lock keeps timestamps in processing order. |

## 4. Design and complexity

`RateLimiter` (abstract) owns validation, the per-client map, the lock and the
check for timestamps going backwards. Each strategy implements only
`_new_state()` and `_admit(state, now)`.

| Strategy | Time per call | Memory per client | Burst guarantee |
|---|---|---|---|
| `SlidingWindowRateLimiter` (log of admitted timestamps) | amortised O(1) | O(limit) | Never more than `limit` in any span of length `window` |
| `FixedWindowRateLimiter` (counter per bucket `[k·W, (k+1)·W)`) | O(1) | O(1) | Up to `2·limit` across a bucket boundary |

## 5. On the day: map the prompt wording to a strategy

* "in any T-second period", "in the last T ms", "rolling", "sliding" → **sliding**
* "per minute", "per calendar second", "resets every T", "window starts at" → **fixed**
* If a stub is provided, keep its class and method names and signatures. Only
  the bodies change.
* If timestamps are integers, keep all arithmetic in integers. Floats can put
  a boundary in the wrong place (`0.3 // 0.1 == 2.0`).
* If the expected error type is specified, swap `ValueError` for it in one
  place: the `_check_*` helpers.

## 6. Likely senior-level follow-ups

* **Memory and idle clients.** The client map never shrinks. Options: evict a
  client once its log is empty, run a periodic sweep, or use a TTL/LRU cache.
* **Memory at high limits.** A sliding log costs O(limit) per client. A
  *sliding window counter* (the current bucket plus a weighted share of the
  previous one) is O(1) and approximate. A *token bucket* is also O(1) and
  allows controlled bursts.
* **Lock contention.** Replace the single lock with lock striping (N locks,
  chosen by `hash(client_id) % N`) or a lock per client.
* **Distributed deployment.** For a fixed window, Redis `INCR` plus `EXPIRE`.
  For a sliding log, Redis `ZADD`, `ZREMRANGEBYSCORE` and `ZCARD`. In both
  cases run the steps in a Lua script so check-and-record stays atomic.
  Clock skew between nodes argues for using the server's time.
* **Per-client limits** (tiers or plans). Put `limit` and `window` in each
  client's state, with the constructor values as defaults.

## 7. Running the tests

```bash
cd interview_prep/rate_limiter
python3 -m unittest -v
```

The tests need only the standard library. There are 17 tests:

* configuration validation
* client independence
* window boundaries for each strategy
* a test where the two strategies give different answers
* timestamps going backwards
* injected clock
* a concurrency test
* a randomized comparison of both strategies against a brute-force model
  (2,000 cases)

Each of these injected bugs was checked to make the suite fail:

* off-by-one at the boundary
* rejected requests consuming quota
* `limit=0` accepted
* `bool` accepted as a number
* backwards timestamps accepted
* a fixed window that never resets
* a missing lock (failed in 20 of 20 runs)
