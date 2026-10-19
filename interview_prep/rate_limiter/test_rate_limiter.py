import math
import random
import sys
import threading
import unittest

from rate_limiter import FixedWindowRateLimiter, SlidingWindowRateLimiter

BOTH = (SlidingWindowRateLimiter, FixedWindowRateLimiter)


class ConfigValidationTest(unittest.TestCase):
    def test_rejects_bad_limit(self):
        for cls in BOTH:
            for limit in (0, -1, 1.5, 2.0, "3", None, True):
                with self.subTest(cls=cls.__name__, limit=limit):
                    with self.assertRaises(ValueError):
                        cls(limit, 10)

    def test_rejects_bad_window(self):
        for cls in BOTH:
            for window in (0, -1, -0.5, math.nan, math.inf, "10", None, True):
                with self.subTest(cls=cls.__name__, window=window):
                    with self.assertRaises(ValueError):
                        cls(5, window)

    def test_rejects_non_callable_clock(self):
        for cls in BOTH:
            with self.subTest(cls=cls.__name__):
                with self.assertRaises(ValueError):
                    cls(5, 10, clock=123)

    def test_accepts_smallest_valid_config(self):
        for cls in BOTH:
            with self.subTest(cls=cls.__name__):
                limiter = cls(1, 0.001)
                self.assertEqual((limiter.limit, limiter.window), (1, 0.001))


class CommonBehaviourTest(unittest.TestCase):
    def test_admits_up_to_limit_then_denies(self):
        for cls in BOTH:
            with self.subTest(cls=cls.__name__):
                limiter = cls(3, 10)
                results = [limiter.allow("a", t) for t in (0, 1, 2, 3, 4)]
                self.assertEqual(results, [True, True, True, False, False])

    def test_clients_are_independent(self):
        for cls in BOTH:
            with self.subTest(cls=cls.__name__):
                limiter = cls(2, 10)
                self.assertTrue(limiter.allow("a", 0))
                self.assertTrue(limiter.allow("a", 1))
                self.assertFalse(limiter.allow("a", 2))
                self.assertTrue(limiter.allow("b", 2))
                self.assertTrue(limiter.allow("b", 3))
                self.assertFalse(limiter.allow("b", 4))
                self.assertFalse(limiter.allow("a", 5))

    def test_rejects_invalid_client_id(self):
        for cls in BOTH:
            limiter = cls(1, 10)
            for client_id in (None, "", ["a"]):
                with self.subTest(cls=cls.__name__, client_id=client_id):
                    with self.assertRaises(ValueError):
                        limiter.allow(client_id, 0)

    def test_rejects_invalid_timestamp(self):
        for cls in BOTH:
            limiter = cls(1, 10)
            for now in (math.nan, math.inf, -math.inf, "5", True):
                with self.subTest(cls=cls.__name__, now=now):
                    with self.assertRaises(ValueError):
                        limiter.allow("a", now)

    def test_rejects_time_going_backwards_without_changing_state(self):
        for cls in BOTH:
            with self.subTest(cls=cls.__name__):
                limiter = cls(2, 10)
                self.assertTrue(limiter.allow("a", 5))
                with self.assertRaises(ValueError):
                    limiter.allow("a", 4)
                # The rejected call recorded nothing: one slot is still free.
                self.assertTrue(limiter.allow("a", 5))
                self.assertFalse(limiter.allow("a", 5))
                # Ordering is per client; another client may be behind.
                self.assertTrue(limiter.allow("b", 1))

    def test_uses_injected_clock_when_no_timestamp_given(self):
        for cls in BOTH:
            with self.subTest(cls=cls.__name__):
                now = [0]
                limiter = cls(1, 10, clock=lambda: now[0])
                self.assertTrue(limiter.allow("a"))
                self.assertFalse(limiter.allow("a"))
                now[0] = 10
                self.assertTrue(limiter.allow("a"))

    def test_concurrent_callers_never_exceed_limit(self):
        # Force very frequent thread switches; at the default interval the GIL
        # almost never preempts between the check and the record, and this
        # test would pass even without the lock.
        self.addCleanup(sys.setswitchinterval, sys.getswitchinterval())
        sys.setswitchinterval(1e-6)
        # A client only races at the moment it reaches its limit, so every
        # thread sweeps the same many clients: each one is a fresh race.
        threads_n, clients_n, limit = 8, 3000, 2
        for cls in BOTH:
            with self.subTest(cls=cls.__name__):
                limiter = cls(limit, 60, clock=lambda: 0)
                barrier = threading.Barrier(threads_n)
                admitted = []

                def worker():
                    barrier.wait()
                    admitted.append(
                        sum(limiter.allow(c) for c in range(clients_n) for _ in range(limit))
                    )

                threads = [threading.Thread(target=worker) for _ in range(threads_n)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
                self.assertEqual(sum(admitted), clients_n * limit)


class SlidingWindowTest(unittest.TestCase):
    def test_request_exactly_one_window_old_has_expired(self):
        limiter = SlidingWindowRateLimiter(2, 10)
        self.assertTrue(limiter.allow("a", 0))
        self.assertTrue(limiter.allow("a", 5))
        self.assertFalse(limiter.allow("a", 9.999))
        self.assertTrue(limiter.allow("a", 10))   # t=0 expired
        self.assertFalse(limiter.allow("a", 14))  # 5 and 10 still in window
        self.assertTrue(limiter.allow("a", 15))   # t=5 expired

    def test_rejected_requests_do_not_consume_quota(self):
        limiter = SlidingWindowRateLimiter(1, 10)
        self.assertTrue(limiter.allow("a", 0))
        for t in range(1, 10):
            self.assertFalse(limiter.allow("a", t))
        # If denials counted, the one at t=9 would block this until t=19.
        self.assertTrue(limiter.allow("a", 10))

    def test_no_burst_across_window_boundary(self):
        limiter = SlidingWindowRateLimiter(2, 10)
        results = [limiter.allow("a", t) for t in (9, 9, 10, 10)]
        self.assertEqual(results, [True, True, False, False])


class FixedWindowTest(unittest.TestCase):
    def test_count_resets_at_bucket_boundary(self):
        limiter = FixedWindowRateLimiter(2, 10)
        self.assertTrue(limiter.allow("a", 8))
        self.assertTrue(limiter.allow("a", 9))
        self.assertFalse(limiter.allow("a", 9.5))
        self.assertTrue(limiter.allow("a", 10))  # bucket [10, 20)
        self.assertTrue(limiter.allow("a", 11))
        self.assertFalse(limiter.allow("a", 19))

    def test_allows_burst_across_window_boundary(self):
        # The known trade-off: 2*limit requests within 1 time unit.
        limiter = FixedWindowRateLimiter(2, 10)
        results = [limiter.allow("a", t) for t in (9, 9, 10, 10)]
        self.assertEqual(results, [True, True, True, True])


def _reference(strategy, limit, window, events):
    """Obviously-correct O(n^2) model of both strategies."""
    history = {}
    out = []
    for client, t in events:
        admitted = history.setdefault(client, [])
        if strategy is SlidingWindowRateLimiter:
            in_window = [x for x in admitted if t - window < x <= t]
        else:
            in_window = [x for x in admitted if x // window == t // window]
        ok = len(in_window) < limit
        if ok:
            admitted.append(t)
        out.append(ok)
    return out


class ReferenceModelTest(unittest.TestCase):
    def test_matches_reference_on_random_traffic(self):
        rng = random.Random(1234)
        for _ in range(2000):
            limit = rng.randint(1, 5)
            window = rng.randint(1, 10)
            t = rng.randint(0, 20)
            events = []
            for _ in range(rng.randint(1, 60)):
                t += rng.choice((0, 0, 1, 2, 5))
                events.append((rng.choice("abc"), t))
            for cls in BOTH:
                limiter = cls(limit, window)
                got = [limiter.allow(c, ts) for c, ts in events]
                self.assertEqual(
                    got,
                    _reference(cls, limit, window, events),
                    f"{cls.__name__} limit={limit} window={window} events={events}",
                )


if __name__ == "__main__":
    unittest.main()
