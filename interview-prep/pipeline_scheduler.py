"""Course Schedule -> ML pipeline scheduler follow-up (Parts 1-4), in Kahn's-algorithm style.

deps are (task, depends_on) pairs, like prerequisites[i] = [course, prereq].
Run `python3 pipeline_scheduler.py` for the self-checks (example answers + randomized checks).
"""

import heapq
import itertools
import random
from collections import deque


def build_graph(tasks, deps):
    degree = {t: 0 for t in tasks}  # number of unfinished dependencies
    neighbor = {t: [] for t in tasks}  # dep -> tasks waiting on it
    for task, dep in deps:
        degree[task] += 1
        neighbor[dep].append(task)
    return degree, neighbor


# Part 1: a valid execution order (LC 210). Same loop as LC 207, but keep the order.
def run_order(tasks, deps):
    degree, neighbor = build_graph(tasks, deps)
    q = deque(t for t in tasks if degree[t] == 0)
    order = []
    while q:
        node = q.popleft()
        order.append(node)
        for nei in neighbor[node]:
            degree[nei] -= 1
            if degree[nei] == 0:
                q.append(nei)
    if len(order) != len(tasks):  # same check as visited == numCourses
        raise ValueError("pipeline has a dependency cycle")
    return order


# Part 2: durations + unlimited workers -> minimum total time and the critical path.
# New vs Part 1: a task's earliest start is the max finish time of its dependencies, and we
# remember which dependency produced that max so the critical path can be walked back.
def plan(durations, deps):
    degree, neighbor = build_graph(durations, deps)
    start = {t: 0 for t in durations}  # earliest start
    parent = {t: None for t in durations}  # dependency that finished last
    finish = {}
    q = deque(t for t in durations if degree[t] == 0)
    while q:
        node = q.popleft()
        finish[node] = start[node] + durations[node]
        for nei in neighbor[node]:
            if finish[node] > start[nei]:
                start[nei] = finish[node]
                parent[nei] = node
            degree[nei] -= 1
            if degree[nei] == 0:
                q.append(nei)
    if len(finish) != len(durations):
        raise ValueError("pipeline has a dependency cycle")
    if not finish:
        return 0, []
    end = max(finish, key=finish.get)
    total = finish[end]
    path = []
    while end is not None:
        path.append(end)
        end = parent[end]
    return total, path[::-1]


# Part 3: slack = how long each task can slip without delaying the pipeline.
# Forward pass (Part 2) gives earliest start; a backward pass over the reversed topological
# order gives latest start: a task must finish before any task waiting on it has to start.
def slack(durations, deps):
    degree, neighbor = build_graph(durations, deps)
    start = {t: 0 for t in durations}
    order = []
    q = deque(t for t in durations if degree[t] == 0)
    while q:
        node = q.popleft()
        order.append(node)
        for nei in neighbor[node]:
            start[nei] = max(start[nei], start[node] + durations[node])
            degree[nei] -= 1
            if degree[nei] == 0:
                q.append(nei)
    if len(order) != len(durations):
        raise ValueError("pipeline has a dependency cycle")
    total = max((start[t] + durations[t] for t in durations), default=0)

    latest_start = {}
    for node in reversed(order):  # every task waiting on `node` is already done
        latest_finish = min((latest_start[nei] for nei in neighbor[node]), default=total)
        latest_start[node] = latest_finish - durations[node]
    return {t: latest_start[t] - start[t] for t in durations}


# Part 4: only k workers. The big change from your Course Schedule loop: a dependency is
# released when a task FINISHES, not when it is popped, so it becomes an event simulation:
#   ready   = heap of tasks whose dependencies are all done, highest priority first
#   running = heap of (finish_time, task); jump the clock to the next finish
# Priority = longest remaining path to the end (critical-path first). Exact k-worker
# scheduling is NP-hard; this greedy is within (2 - 1/k) x optimal (Graham's bound).
def run_with_k_workers(durations, deps, k):
    if k < 1:
        raise ValueError("need at least one worker")
    order = run_order(list(durations), deps)  # also rejects cycles
    degree, neighbor = build_graph(durations, deps)

    remaining = {}  # duration of the longest chain starting at this task
    for node in reversed(order):
        remaining[node] = durations[node] + max((remaining[nei] for nei in neighbor[node]), default=0)

    ready = [(-remaining[t], t) for t in durations if degree[t] == 0]
    heapq.heapify(ready)
    running = []
    started = {}
    time = 0
    while ready or running:
        while ready and len(running) < k:  # fill every free worker
            _, node = heapq.heappop(ready)
            started[node] = time
            heapq.heappush(running, (time + durations[node], node))
        time, node = heapq.heappop(running)  # next completion
        finished = [node]
        while running and running[0][0] == time:  # everything finishing at this instant
            finished.append(heapq.heappop(running)[1])
        for node in finished:
            for nei in neighbor[node]:
                degree[nei] -= 1
                if degree[nei] == 0:
                    heapq.heappush(ready, (-remaining[nei], nei))
    return time, started


# ---------------------------------------------------------------------------
# Self-checks
# ---------------------------------------------------------------------------
EXAMPLE_DURATIONS = {"extract": 10, "validate": 5, "label": 30, "featurize": 20,
                     "train": 60, "eval": 15, "export": 5}
EXAMPLE_DEPS = [("validate", "extract"), ("label", "extract"), ("featurize", "validate"),
                ("train", "label"), ("train", "featurize"), ("eval", "train"), ("export", "train")]


def _is_topological(order, tasks, deps):
    pos = {t: i for i, t in enumerate(order)}
    return sorted(order) == sorted(tasks) and all(pos[d] < pos[t] for t, d in deps)


def _longest_path(durations, deps):
    """Independent reference: memoized DFS over dependencies."""
    parents = {t: [] for t in durations}
    for t, d in deps:
        parents[t].append(d)
    memo = {}

    def finish(t):
        if t not in memo:
            memo[t] = durations[t] + max((finish(p) for p in parents[t]), default=0)
        return memo[t]

    return max((finish(t) for t in durations), default=0)


def _random_dag(rng, n):
    tasks = [f"t{i}" for i in range(n)]
    durations = {t: rng.randint(1, 9) for t in tasks}
    deps = [(tasks[j], tasks[i]) for i, j in itertools.combinations(range(n), 2) if rng.random() < 0.35]
    perm = tasks[:]
    rng.shuffle(perm)  # hide the generation order
    durations = {t: durations[t] for t in perm}
    return durations, deps


def _check_k_schedule(durations, deps, k, total, started):
    """Feasible, never more than k busy, and no worker idles while a task is ready."""
    finish = {t: started[t] + durations[t] for t in durations}
    assert set(started) == set(durations) and total == max(finish.values(), default=0)
    for t, d in deps:
        assert started[t] >= finish[d]
    events = sorted(set(started.values()))
    for time in events:
        busy = sum(1 for t in durations if started[t] <= time < finish[t])
        assert busy <= k
        ready_waiting = [t for t in durations if started[t] > time
                         and all(finish[d] <= time for tt, d in deps if tt == t)]
        assert not (ready_waiting and busy < k), "worker idle while a task was ready"


def _run_checks():
    # Part 1
    order = run_order(list(EXAMPLE_DURATIONS), EXAMPLE_DEPS)
    assert _is_topological(order, list(EXAMPLE_DURATIONS), EXAMPLE_DEPS)
    try:
        run_order(["a", "b", "c"], [("b", "a"), ("c", "b"), ("a", "c")])
        raise AssertionError("expected a cycle error")
    except ValueError:
        pass

    # Part 2
    assert plan(EXAMPLE_DURATIONS, EXAMPLE_DEPS) == (115, ["extract", "label", "train", "eval"])
    assert plan({}, []) == (0, [])

    # Part 3
    assert slack(EXAMPLE_DURATIONS, EXAMPLE_DEPS) == {
        "extract": 0, "validate": 5, "label": 0, "featurize": 5, "train": 0, "eval": 0, "export": 10}

    # Part 4
    assert run_with_k_workers(EXAMPLE_DURATIONS, EXAMPLE_DEPS, 1)[0] == 145
    assert run_with_k_workers(EXAMPLE_DURATIONS, EXAMPLE_DEPS, 2)[0] == 115
    assert run_with_k_workers({"a": 3, "b": 3, "c": 2, "d": 2, "e": 2}, [], 2)[0] == 7  # optimum is 6
    # priority matters: starting short task c first unlocks the long task d early (FIFO gives 16)
    assert run_with_k_workers({"a": 5, "b": 5, "c": 1, "d": 10}, [("d", "c")], 2)[0] == 11

    rng = random.Random(42)
    for _ in range(3000):
        durations, deps = _random_dag(rng, rng.randint(1, 8))
        tasks = list(durations)
        assert _is_topological(run_order(tasks, deps), tasks, deps)

        total, path = plan(durations, deps)
        assert total == _longest_path(durations, deps)
        assert sum(durations[t] for t in path) == total  # the path really is critical
        assert all((b, a) in set(map(tuple, deps)) for a, b in zip(path, path[1:]))

        s = slack(durations, deps)
        for t in tasks:  # slipping by exactly the slack is free; one more minute is not
            assert s[t] >= 0
            assert _longest_path({**durations, t: durations[t] + s[t]}, deps) == total
            assert _longest_path({**durations, t: durations[t] + s[t] + 1}, deps) == total + 1

        for k in range(1, len(tasks) + 2):
            k_total, started = run_with_k_workers(durations, deps, k)
            _check_k_schedule(durations, deps, k, k_total, started)
            assert k_total >= max(total, -(-sum(durations.values()) // k))  # lower bounds
        assert run_with_k_workers(durations, deps, 1)[0] == sum(durations.values())
        assert run_with_k_workers(durations, deps, len(tasks))[0] == total

    print("pipeline scheduler: all checks passed")


if __name__ == "__main__":
    _run_checks()
