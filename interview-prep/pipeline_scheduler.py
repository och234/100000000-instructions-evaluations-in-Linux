# Course Schedule follow-up: ML pipeline scheduler (Parts 1-4)
# deps are (task, depends_on) pairs, same as prerequisites[i] = [course, prereq]
#
# Example used in every part:
#   dur  = {extract: 10, validate: 5, label: 30, featurize: 20, train: 60, eval: 15, export: 5}
#   deps = validate<-extract, label<-extract, featurize<-validate,
#          train<-label, train<-featurize, eval<-train, export<-train
#
# python3 pipeline_scheduler.py  -> runs the checks at the bottom

import heapq
import itertools
import random
from collections import deque


def build_graph(tasks, deps):
    degree = {}      # task -> how many deps it is still waiting on
    neighbor = {}    # dep -> list of tasks that depend on it
    for t in tasks:
        degree[t] = 0
        neighbor[t] = []
    for task, dep in deps:
        degree[task] += 1
        neighbor[dep].append(task)
    return degree, neighbor


# ----------------------------------------------------------------------------
# Part 1: Execution order (LC 210)
# Q: We run ML pipelines as DAGs of tasks. Given the task names and the deps
#    (task, depends_on), return an order the tasks can run in. If the pipeline
#    can't run, raise an error.
#
# - One valid order: extract, label, validate, featurize, train, eval, export.
#   Any topological order is accepted.
# - a->b->c->a should raise an error. Strong follow-up: report the cycle itself,
#   using DFS with three colors.
#
# Approach: same Kahn's loop as Course Schedule. Start with every task that has
# no deps, and each time we run one, decrement its dependents; a dependent goes
# in the queue once its count hits 0. Instead of only counting visited we keep
# the order. If some tasks never reach 0 they are stuck on a cycle.
# Time O(V + E), space O(V + E).
# ----------------------------------------------------------------------------
def get_order(tasks, deps):
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
    if len(order) != len(tasks):    # same idea as visited == numCourses
        raise ValueError("cycle in pipeline")
    return order


# ----------------------------------------------------------------------------
# Part 2: Durations + unlimited workers -> total time and critical path
# Q: Each task now has a duration (minutes) and we have unlimited workers. A task
#    can start as soon as all its deps finish. Return the minimum time for the
#    whole pipeline and the chain of tasks that decides it (the critical path).
#
# - Total time is 115. The critical path is extract -> label -> train -> eval
#   (10 + 30 + 60 + 15).
# - Method: in topological order,
#   earliest_finish[t] = dur[t] + max(earliest_finish of its deps).
#   Keep the dep that gave the max, and follow those back from the last task
#   to recover the path.
#
# Approach: same loop as Part 1. When a task finishes, push its finish time to
# its dependents: a dependent can't start before its slowest dep is done, so
# start = max over deps. The dep that sets that max is its "prev" on the
# critical path. With unlimited workers nothing waits for a free machine, so the
# pop order doesn't matter, only dependency order does.
# Time O(V + E).
# ----------------------------------------------------------------------------
def critical_path(dur, deps):
    degree, neighbor = build_graph(dur, deps)
    # start[t]: earliest time t can begin. Everyone starts at 0, and it only goes
    #           up as we learn when t's deps finish.
    # prev[t]:  the dep of t that finished last, i.e. the one t actually waited on.
    #           None means t has no deps (it starts the chain).
    # finish[t]: start[t] + dur[t], filled in when t is popped.
    start = {}
    prev = {}
    for t in dur:
        start[t] = 0
        prev[t] = None
    finish = {}
    q = deque(t for t in dur if degree[t] == 0)
    while q:
        node = q.popleft()
        finish[node] = start[node] + dur[node]
        for nei in neighbor[node]:
            if finish[node] > start[nei]:    # this dep finishes later -> it decides nei's start
                start[nei] = finish[node]
                prev[nei] = node
            degree[nei] -= 1
            if degree[nei] == 0:
                q.append(nei)
    if len(finish) != len(dur):
        raise ValueError("cycle in pipeline")
    if not finish:
        return 0, []

    last = max(finish, key=finish.get)   # whoever finishes last ends the pipeline
    total = finish[last]
    path = []
    while last is not None:              # walk back through the deps that held things up
        path.append(last)
        last = prev[last]
    return total, path[::-1]


# ----------------------------------------------------------------------------
# Part 3: Slack
# Q: For each task, how many minutes can it be delayed without delaying the
#    whole pipeline?
#
# - Slack is validate 5, featurize 5, export 10. Every task on the critical
#   path has 0.
# - Method: run a backward pass in reverse topological order.
#   latest_finish[t] = min(latest_start of its children), with tasks that have
#   no children getting the total time. Slack = latest start - earliest start.
#
# Approach: forward pass (Part 2) gives earliest start. Then walk the order
# backwards: by the time we reach a task, all its dependents already have their
# latest start, so the task must finish by the earliest of those. Leaf tasks
# can finish as late as the total time. Slack is the gap between latest and
# earliest start.
# Time O(V + E).
# ----------------------------------------------------------------------------
def get_slack(dur, deps):
    degree, neighbor = build_graph(dur, deps)
    start = {}       # earliest start, same as Part 2
    for t in dur:
        start[t] = 0
    order = []
    q = deque(t for t in dur if degree[t] == 0)
    while q:
        node = q.popleft()
        order.append(node)
        for nei in neighbor[node]:
            start[nei] = max(start[nei], start[node] + dur[node])
            degree[nei] -= 1
            if degree[nei] == 0:
                q.append(nei)
    if len(order) != len(dur):
        raise ValueError("cycle in pipeline")
    total = max((start[t] + dur[t] for t in dur), default=0)

    latest = {}                          # latest start without delaying the pipeline
    for node in reversed(order):
        must_finish = min((latest[nei] for nei in neighbor[node]), default=total)
        latest[node] = must_finish - dur[node]
    slack = {}
    for t in dur:
        slack[t] = latest[t] - start[t]
    return slack


# ----------------------------------------------------------------------------
# Part 4: Only k workers
# Q: The cluster now has only k GPU workers. Each task holds one worker for its
#    whole duration. Write a scheduler that starts a ready task whenever a worker
#    is free. Which task do you pick, and what's the total time?
#
# - k=1 gives 145, the sum of all durations.
# - k=2 gives 115, as fast as unlimited workers, if you pick by longest
#   remaining path to the end (critical path first).
# - The trap: five independent tasks of 3, 3, 2, 2, 2 minutes with k=2. Greedy
#   longest-first gives 7; the optimum is 6 (3+3 on one worker, 2+2+2 on the
#   other).
# - What to say: finding the exact best schedule with k workers is NP-hard.
#   Critical-path-first list scheduling is the standard heuristic, and it is
#   guaranteed to be within (2 - 1/k) of the optimum.
# - Implementation: a heap of ready tasks ordered by priority, plus a heap of
#   running tasks ordered by finish time. Cost is O((V+E) log V).
#
# Approach: the big difference from Course Schedule is WHEN deps get released.
# A dependent can only start once the task actually finishes, not when we pop
# it, so this turns into a time simulation:
#   1. fill every free worker from the ready heap (best priority first)
#   2. jump the clock to the next finish time from the running heap
#   3. release dependents of everything that finished at that time
# Priority = longest chain left starting at the task (computed once, backwards
# over the topo order), so long chains get started early.
# ----------------------------------------------------------------------------
def schedule_k_workers(dur, deps, k):
    if k < 1:
        raise ValueError("need at least one worker")
    order = get_order(list(dur), deps)       # also catches cycles
    degree, neighbor = build_graph(dur, deps)

    longest = {}                             # longest chain from this task to the end
    for node in reversed(order):
        longest[node] = dur[node] + max((longest[nei] for nei in neighbor[node]), default=0)

    ready = [(-longest[t], t) for t in dur if degree[t] == 0]   # max-heap via negative
    heapq.heapify(ready)
    running = []                             # (finish_time, task)
    start_at = {}
    time = 0
    while ready or running:
        while ready and len(running) < k:    # step 1: use every free worker
            _, node = heapq.heappop(ready)
            start_at[node] = time
            heapq.heappush(running, (time + dur[node], node))

        time, node = heapq.heappop(running)  # step 2: next task to finish
        done = [node]
        while running and running[0][0] == time:   # others finishing at the same time
            done.append(heapq.heappop(running)[1])

        for node in done:                    # step 3: only now release dependents
            for nei in neighbor[node]:
                degree[nei] -= 1
                if degree[nei] == 0:
                    heapq.heappush(ready, (-longest[nei], nei))
    return time, start_at


# ----------------------------------------------------------------------------
# Checks
# ----------------------------------------------------------------------------
DUR = {"extract": 10, "validate": 5, "label": 30, "featurize": 20,
       "train": 60, "eval": 15, "export": 5}
DEPS = [("validate", "extract"), ("label", "extract"), ("featurize", "validate"),
        ("train", "label"), ("train", "featurize"), ("eval", "train"), ("export", "train")]


def is_valid_order(order, tasks, deps):
    pos = {t: i for i, t in enumerate(order)}
    return sorted(order) == sorted(tasks) and all(pos[d] < pos[t] for t, d in deps)


def slow_total(dur, deps):
    # brute force longest path with memo, to compare against
    parents = {t: [] for t in dur}
    for t, d in deps:
        parents[t].append(d)
    memo = {}

    def end(t):
        if t not in memo:
            memo[t] = dur[t] + max((end(p) for p in parents[t]), default=0)
        return memo[t]

    return max((end(t) for t in dur), default=0)


def random_dag(rng, n):
    names = [f"t{i}" for i in range(n)]
    deps = [(names[j], names[i]) for i, j in itertools.combinations(range(n), 2) if rng.random() < 0.35]
    rng.shuffle(names)
    return {t: rng.randint(1, 9) for t in names}, deps


def check_schedule(dur, deps, k, total, start_at):
    # valid schedule: deps respected, never more than k busy, no idle worker while a task waits
    finish = {t: start_at[t] + dur[t] for t in dur}
    assert set(start_at) == set(dur) and total == max(finish.values(), default=0)
    for t, d in deps:
        assert start_at[t] >= finish[d]
    for time in set(start_at.values()):
        busy = sum(1 for t in dur if start_at[t] <= time < finish[t])
        waiting = [t for t in dur if start_at[t] > time
                   and all(finish[d] <= time for tt, d in deps if tt == t)]
        assert busy <= k and not (waiting and busy < k)


def run_checks():
    # part 1
    assert is_valid_order(get_order(list(DUR), DEPS), list(DUR), DEPS)
    try:
        get_order(["a", "b", "c"], [("b", "a"), ("c", "b"), ("a", "c")])
        raise AssertionError("cycle not caught")
    except ValueError:
        pass

    # part 2
    assert critical_path(DUR, DEPS) == (115, ["extract", "label", "train", "eval"])
    assert critical_path({}, []) == (0, [])

    # part 3
    assert get_slack(DUR, DEPS) == {"extract": 0, "validate": 5, "label": 0, "featurize": 5,
                                    "train": 0, "eval": 0, "export": 10}

    # part 4
    assert schedule_k_workers(DUR, DEPS, 1)[0] == 145
    assert schedule_k_workers(DUR, DEPS, 2)[0] == 115
    assert schedule_k_workers({"a": 3, "b": 3, "c": 2, "d": 2, "e": 2}, [], 2)[0] == 7   # best is 6
    # picking order matters: start c first so d (10 min) unlocks early; FIFO would give 16
    assert schedule_k_workers({"a": 5, "b": 5, "c": 1, "d": 10}, [("d", "c")], 2)[0] == 11

    # random DAGs
    rng = random.Random(42)
    for _ in range(3000):
        dur, deps = random_dag(rng, rng.randint(1, 8))
        tasks = list(dur)
        assert is_valid_order(get_order(tasks, deps), tasks, deps)

        total, path = critical_path(dur, deps)
        assert total == slow_total(dur, deps)
        assert sum(dur[t] for t in path) == total
        assert all((b, a) in set(deps) for a, b in zip(path, path[1:]))

        slack = get_slack(dur, deps)
        for t in tasks:   # delaying by the slack is free, one more minute is not
            assert slow_total({**dur, t: dur[t] + slack[t]}, deps) == total
            assert slow_total({**dur, t: dur[t] + slack[t] + 1}, deps) == total + 1

        for k in range(1, len(tasks) + 2):
            k_total, start_at = schedule_k_workers(dur, deps, k)
            check_schedule(dur, deps, k, k_total, start_at)
            assert k_total >= max(total, -(-sum(dur.values()) // k))
        assert schedule_k_workers(dur, deps, 1)[0] == sum(dur.values())
        assert schedule_k_workers(dur, deps, len(tasks))[0] == total

    print("all checks passed")


if __name__ == "__main__":
    run_checks()
