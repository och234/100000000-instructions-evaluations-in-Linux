import itertools
import random
import unittest

from credits import Credits


def brute_balance(grants, subs, t):
    """Reference model: rebuild the state at time t from scratch on every query."""
    active = {}  # gid -> [expiry, remaining]
    evs = [(ts, 0, g) for g, (ts, amt, exp) in grants.items()] + \
          [(ts, 1, amt) for ts, amt in subs]
    overdrawn = False
    for ts, kind, x in sorted((e for e in evs if e[0] <= t), key=lambda e: (e[0], e[1])):
        for g in [g for g, v in active.items() if v[0] <= ts]:
            del active[g]
        if kind == 0:
            _, amt, exp = grants[x]
            if exp > ts and amt:
                active[x] = [exp, amt]
        else:
            need = x
            for g in sorted(active, key=lambda g: (active[g][0], grants[g][0])):
                take = min(need, active[g][1])
                active[g][1] -= take
                need -= take
                if active[g][1] == 0:
                    del active[g]
                if not need:
                    break
            if need:
                overdrawn = True
    if overdrawn:
        return None
    return sum(v[1] for v in active.values() if v[0] > t)


class CreditsTest(unittest.TestCase):
    def test_basic_and_expiry(self):
        c = Credits()
        c.create_grant(10, "a", 100, 50)
        self.assertEqual(c.get_balance(9), 0)
        self.assertEqual(c.get_balance(10), 100)
        self.assertEqual(c.get_balance(49), 100)
        self.assertEqual(c.get_balance(50), 0)  # expiry is exclusive

    def test_subtract_arrives_before_grant(self):
        c = Credits()
        c.subtract(30, 40)
        self.assertIsNone(c.get_balance(30))     # overdrawn with what we know so far
        c.create_grant(10, "a", 100, 100)        # arrives late, earlier timestamp
        self.assertEqual(c.get_balance(20), 100)
        self.assertEqual(c.get_balance(30), 60)

    def test_spends_soonest_expiring_first(self):
        c = Credits()
        c.create_grant(0, "long", 50, 1000)
        c.create_grant(0, "short", 50, 100)
        c.subtract(10, 30)
        self.assertEqual(c.get_balance(99), 70)   # 20 short + 50 long
        self.assertEqual(c.get_balance(100), 50)  # short's remaining 20 expired

    def test_same_timestamp_ordering(self):
        c = Credits()
        c.subtract(5, 10)
        c.create_grant(5, "a", 10, 20)  # grant applies before subtract at ts=5
        self.assertEqual(c.get_balance(5), 0)
        c2 = Credits()
        c2.create_grant(0, "a", 10, 5)
        c2.subtract(5, 1)               # grant already expired at ts=5
        self.assertIsNone(c2.get_balance(5))

    def test_duplicate_grant_rejected(self):
        c = Credits()
        c.create_grant(0, "a", 1, 2)
        with self.assertRaises(ValueError):
            c.create_grant(1, "a", 1, 2)

    def test_randomized_against_brute_force(self):
        rng = random.Random(7)
        for _ in range(300):
            c, grants, subs = Credits(), {}, []
            gid = itertools.count()
            for _ in range(rng.randint(1, 40)):
                r = rng.random()
                if r < 0.4:
                    ts = rng.randint(0, 50)
                    g, amt, exp = f"g{next(gid)}", rng.randint(0, 20), ts + rng.randint(0, 30)
                    grants[g] = (ts, amt, exp)
                    c.create_grant(ts, g, amt, exp)
                elif r < 0.7:
                    ts, amt = rng.randint(0, 50), rng.randint(0, 15)
                    subs.append((ts, amt))
                    c.subtract(ts, amt)
                else:
                    t = rng.randint(0, 80)
                    self.assertEqual(c.get_balance(t), brute_balance(grants, subs, t))


if __name__ == "__main__":
    unittest.main()
