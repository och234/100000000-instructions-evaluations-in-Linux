# GM Embodied AI ML Infra (ex-Cruise) Screen: Top 10 Coding Questions

**Target:** The 1-hour "Technical/Functional Assessment" screen for *Senior ML Infrastructure Engineer, Embodied AI Scaling Foundations* (JR-202601904). The screen runs live on Codility, and the team is the former Cruise group now inside GM.

**Ranked by:** How often each question was asked, combined with how recently. Run [`score_questions.py`](score_questions.py) to reproduce the ranking.

**Solutions:** Tested solutions for all ten, plus the wildcard, are in [`gm_top10.py`](gm_top10.py). Run `python3 gm_top10.py`; the run includes brute-force cross-checks.

## The ranking (as of 2026-10-19, recency half-life 365 days)

| # | Question | Source | Est. last asked | Freq | Recency | Score | Rank at 180/365/730-day half-life |
|---|---|---|---|---|---|---|---|
| 1 | [Number of Connected Components in an Undirected Graph (323)](https://leetcode.com/problems/number-of-connected-components-in-an-undirected-graph) | GM | 2025-10 | 1.00 | 0.49 | 0.489 | 3 / 1 / 1 |
| 2 | [Number of Steps to Reduce a Number in Binary Representation to One (1404)](https://leetcode.com/problems/number-of-steps-to-reduce-a-number-in-binary-representation-to-one) | GM | 2026-02 | 0.68 | 0.61 | 0.416 | 2 / 2 / 3 |
| 3 | [Merge Intervals (56)](https://leetcode.com/problems/merge-intervals) | GM + Cruise | 2026-05 | 0.53 | 0.75 | 0.391 | 1 / 3 / 6 |
| 4 | [Maximum Sum of 3 Non-Overlapping Subarrays (689)](https://leetcode.com/problems/maximum-sum-of-3-non-overlapping-subarrays), Hard | GM | 2026-01 | 0.65 | 0.59 | 0.384 | 4 / 4 / 4 |
| 5 | [Minimum Path Sum (64)](https://leetcode.com/problems/minimum-path-sum) | GM | 2025-09 | 0.80 | 0.46 | 0.367 | 5 / 5 / 2 |
| 6 | [LRU Cache (146)](https://leetcode.com/problems/lru-cache) | GM + Cruise | 2025-09 | 0.71 | 0.46 | 0.325 | 7 / 6 / 5 |
| 7 | [Course Schedule (207)](https://leetcode.com/problems/course-schedule); prepare [210](https://leetcode.com/problems/course-schedule-ii) as the follow-up | Cruise | 2025-04 | 0.76 | 0.35 | 0.264 | 9 / 7 / 7 |
| 8 | [Minimum Deletions to Make Character Frequencies Unique (1647)](https://leetcode.com/problems/minimum-deletions-to-make-character-frequencies-unique) | GM | 2026-01 | 0.41 | 0.61 | 0.245 | 6 / 8 / 10 |
| 9 | [Implement Trie (208)](https://leetcode.com/problems/implement-trie-prefix-tree) | GM + Cruise | 2025-07 | 0.56 | 0.41 | 0.229 | 8 / 9 / 8 |
| 10 | [Synonymous Sentences (1258)](https://leetcode.com/problems/synonymous-sentences) | Cruise | 2024-08 | 0.72 | 0.22 | 0.160 | 11 / 10 / 9 |

- **Stability:** The same ten questions make up the top 10 at every half-life from 185 to 730 days. Only their order changes. At 180–184 days, [Guess the Word (843)](https://leetcode.com/problems/guess-the-word) narrowly takes #10 from Synonymous Sentences.
- **Just outside the top 10:** Widest Vertical Area (1637), Guess the Word (843), Serialize/Deserialize Binary Tree (297), and Dot Product of Sparse Vectors (1570).

### Wildcard: outside the formula, but rehearse it once

**In-memory key-value store with nested, isolated transactions** (begin / set / get / delete / commit / rollback).

- **Where it ranks:** #28 by the formula. Its last report is from 2021, so recency pulls it down.
- **Why rehearse it anyway:** It is the most-reported *1-hour Cruise screen* question. There are three reports:
  - a 2021 phone screen
  - a 2021 senior tech assessment, where the candidate failed on a missing deep copy
  - a 2019 onsite "Transactional Map"
- **Fit for this screen:** The team is ex-Cruise and the round is 1 hour, so it fits well. It is also already in your notes, so one timed run is enough.

## How the score works

**Data**

- **Tag snapshots:** 19 dated snapshots of the GM and Cruise LeetCode company-tag lists, from 2020-08 to 2026-08. They come from the git history of four community repos, extracted by [`data/extract_tag_snapshots.py`](data/extract_tag_snapshots.py) into [`data/tag_snapshots.csv`](data/tag_snapshots.csv).
- **Candidate reports:** 24 GM and Cruise reports, dated where possible, in [`data/reports.csv`](data/reports.csv). They come from Glassdoor, Jointaro, LeetCode Discuss, Blind, 1point3acres, InterviewSense, and Interview Query (one aggregator listing, origin unverified).

**Per-question formula**

- **Est. last asked:** combines positive and negative evidence.
  - *Positive:* A snapshot that lists the question in a time window (30 days, 3 months, 6 months, 1 year or 2 years) means it was asked inside that window.
  - *Negative:* A snapshot that still lists the question all-time but leaves it out of a published window means it was *not* asked in that window.
  - *Estimate:* Remove the negative windows from the positive ones and take the midpoint of the latest piece left. If snapshots contradict each other and nothing is left, use the window's earliest date. A later dated report overrides both.
- **Recency:** `0.5 ^ (age_days / 365)`.
- **Frequency:** `0.5 * LeetCode within-company frequency (normalized) + 0.5 * repeat appearances (log-scaled)`.
  - The LeetCode term uses each dataset's latest snapshot, averaged across datasets.
  - Questions known only from reports get a 0.5 prior for that term.
- **Score:** `frequency * recency`.

**Caveats**

- **GM's tag covers every GM team**, including IT and infotainment, not only the AV team. Cruise's tag is the team's own history, but it is older. Neither one is "this interviewer's question bank."
- **Questions seen only in untimed lists** ("all-time" or "more than six months") get an assumed last-asked date: first seen minus one year.
- **Undated reports** are treated as three years old.

## What to prepare for each question

The bullet under each question is the ML-infra follow-up the interviewer is likely to push toward.

1. **Connected Components (323).** Union-Find with path compression and union by size, about O(E·α(V)).
   - *Infra twist:* Edges arrive online, as in [305](https://leetcode.com/problems/number-of-islands-ii). Or cluster sensor points that sit within distance d of each other.
2. **Steps to Reduce Binary to One (1404).** Scan right to left with a carry. An odd bit adds 2 steps and sets carry=1; an even bit adds 1 step. O(n), with no big-int conversion.
   - *Twist:* The string has 10⁶ bits. Explain why `int(s, 2)` with simulation becomes O(n²).
3. **Merge Intervals (56).** Sort, then sweep.
   - *Twist:* Intervals arrive one at a time and out of order; see `StreamingIntervals`. Each add is an O(log n) search plus a list splice (O(log n) amortized with SortedList), and you can flush finished intervals by watermark. Related: [352](https://leetcode.com/problems/data-stream-as-disjoint-intervals) and [715](https://leetcode.com/problems/range-module).
   - Other follow-ups: [Insert Interval (57)](https://leetcode.com/problems/insert-interval), and the peak number of concurrent jobs ([Meeting Rooms II, 253](https://leetcode.com/problems/meeting-rooms-ii)).
4. **Max Sum of 3 Non-Overlapping Subarrays (689).** Compute window sums. Build a best-left argmax array (strict `>`) and a best-right argmax array (`>=`) so ties go to the leftmost index. Then sweep the middle window. O(n).
   - *Twist:* Generalize to m windows with an O(n·m) DP.
5. **Minimum Path Sum (64).** 1-D DP.
   - *Twist:* 4-directional moves with obstacles and weighted cells make it Dijkstra (`min_cost_path`). A* is the next step.
6. **LRU Cache (146).** Hashmap plus a doubly linked list you write yourself. A 2020 Cruise screen disallowed `OrderedDict`.
   - *Twist:* Per-entry TTL; capacity in bytes; thread safety (one lock, then striping); [LFU (460)](https://leetcode.com/problems/lfu-cache).
7. **Course Schedule I/II (207/210).** Kahn's algorithm; a cycle means no valid order.
   - *Twist:* The no-durations follow-ups are the minimum number of stages ([1136](https://leetcode.com/problems/parallel-courses)) and reporting the cycle. Durations turn it into a different problem ([2050](https://leetcode.com/problems/parallel-courses-iii)). See the follow-up prompts below.
8. **Min Deletions for Unique Frequencies (1647).** Count characters, sort the counts descending, and decrement each one until it reaches an unused count. 0 is always allowed.
9. **Implement Trie (208).** Nested dicts with an end marker.
   - *Twist:* Top-k autocomplete ([642](https://leetcode.com/problems/design-search-autocomplete-system)) and wildcard search ([211](https://leetcode.com/problems/design-add-and-search-words-data-structure)).
10. **Synonymous Sentences (1258).** Union-Find to group synonyms, sort each group, backtrack over word positions, then sort the output.
    - *Twist:* Return only the count. Multiply, over every word in the sentence, that word's group size (1 if it has no synonyms).

**Wildcard: nested-transaction KV store**

- **Design:** Keep a stack of dict layers and mark deletes with a tombstone. `commit` merges the innermost layer into its parent; `rollback` pops it. `get` is O(depth).
- **Say your commit semantics out loud.** Ask whether `commit` merges one level or flushes every level.
- **Follow-up:** Make `get` O(1) with an undo log.
- **Watch for the failure seen in the 2021 report:** copying instead of layering, or using a shallow copy.

## Minimum Path Sum (#5): follow-up prompts to rehearse

GM reports from 2025 name only "Minimum Path Sum". The prompts below are the likely ways an interviewer would extend it, based on Dataford's Cruise prompts ("grid with weighted traversal costs", "collision-free path considering dynamic obstacles"). Every answer below was checked by running it.

1. **4 directions, blocked cells, weighted cells.** "The vehicle can move up, down, left or right. Each cell's value is the cost to enter it, and the start cell counts. Cells marked -1 are blocked. Return the minimum cost from top-left to bottom-right, or -1 if unreachable."
   - `[[1,9,1,1,1],[1,9,1,9,1],[1,1,1,9,1]]` → **11**. The right/down DP gives 15, because the best path has to go up.
   - `[[1,1,1],[-1,-1,1],[1,1,1],[1,-1,-1],[1,1,1]]` → **11**.
   - `[[1,-1],[-1,1]]` → **-1**.
   - *Answer:* With moves in 4 directions the grid has cycles, so a DP has no fill order. Costs are non-negative, so use Dijkstra, O(mn log mn). See `min_cost_path`.
2. **Return the path.** Store a parent pointer each time you relax a neighbor, then walk back from the target.
3. **Obstacles that clear over time** ([LC 2577](https://leetcode.com/problems/minimum-time-to-visit-a-cell-in-a-grid)). "Each move takes 1 second. A cell can be entered only at time >= `grid[r][c]`, and you must keep moving. What is the earliest arrival time?"
   - `[[0,1,3,2],[5,1,2,5],[4,3,8,6]]` → **7**.
   - `[[0,2,4],[3,2,1],[1,0,4]]` → **-1**.
   - *Answer:* Run Dijkstra on arrival time. If a cell isn't open yet, bounce back and forth to wait, so you arrive at `open + ((open - (t+1)) % 2)`.
   - *Impossible case:* both `(0,1)` and `(1,0)` are greater than 1.
4. **Probing questions:**
   - Costs only 0 or 1 → 0-1 BFS.
   - Negative costs → Bellman-Ford.
   - Faster search → A* with heuristic Manhattan distance × smallest cell cost.
   - Map doesn't fit in memory → load tiles lazily during the search.
   - Many queries to the same target → one Dijkstra backwards from the target.

## Course Schedule (#7): follow-up prompts to rehearse

**Evidence check:**
- **Course Schedule (207) itself:** The only source is LeetCode's *Cruise* company tag. It appears in the 3-month window in [Mar 2025](https://github.com/liquidslr/leetcode-company-wise-problems/blob/15beb6a5d1536debb5051c2c01ba1a6ddc103107/Cruise/2.%20Three%20Months.csv) and in the 6-month window through [Jul 2025](https://github.com/snehasishroy/leetcode-companywise-interview-questions/blob/b4c547f8c16b4ea74d8d301caeb8cba46ee5be71/cruise-automation/six-months.csv). Tags are anonymous and give no role, team or round.
- **Write-ups:** No first-hand report (Glassdoor, Blind, LeetCode Discuss, 1point3acres) names it for Cruise or GM.
- **GM's tag:** It has never listed it.
- **The follow-ups below:** None of them have been reported for GM or Cruise. They are my guesses at how an ML-infra interviewer would extend it.

[207](https://leetcode.com/problems/course-schedule) and [210](https://leetcode.com/problems/course-schedule-ii) have **no durations**: each course is a node and each prerequisite is an edge. Follow-ups 1–5 keep that model. Only #6 adds hours, and at that point it is a different problem. Every answer below was checked by running it.

1. **Return an order** (210). "Return any order that finishes all courses, or `[]` if that's impossible."
   - `n=4, [[1,0],[2,0],[3,1],[3,2]]` → `[0,1,2,3]` (or `[0,2,1,3]`).
   - *Answer:* Kahn's algorithm, O(V+E). See `find_order`.
2. **Which dependencies block the schedule?** "If it can't be done, return one cycle so the user can fix it."
   - `n=3, [[1,0],[2,1],[0,2]]` → `[0,1,2,0]`.
   - *Answer:* Kahn's algorithm only tells you a cycle exists. To return one, run a 3-color DFS and walk parent pointers back from the back edge. See `find_cycle`.
3. **Minimum number of semesters with unlimited parallelism** ([1136](https://leetcode.com/problems/parallel-courses)). "Any number of courses whose prerequisites are done can run in the same semester. What is the fewest number of semesters? Return -1 if impossible."
   - `n=3, relations=[[1,3],[2,3]]` → **2**.
   - A cycle → **-1**.
   - *Pipeline framing:* There's still only one unit of time per job. The 8-job pipeline (ingest → decode → {eval-set, replay, label} → train → eval → report) needs **6 stages**.
   - *Answer:* Run BFS level by level. The number of levels equals the longest chain, counted in courses. See `min_stages`.
4. **At most k courses per semester** ([1494](https://leetcode.com/problems/parallel-courses-ii)).
   - `n=4, [[2,1],[3,1],[1,4]], k=2` → **3**.
   - `n=5, [[2,1],[3,1],[4,1],[1,5]], k=2` → **4**.
   - *Answer:* Greedy is not always optimal. LeetCode caps n at 15, which allows a bitmask DP over the set of finished courses.
5. **Prerequisite queries** ([1462](https://leetcode.com/problems/course-schedule-iv)). "Answer many queries of the form: is `a` a (direct or indirect) prerequisite of `b`?"
   - `n=3, [[1,2],[1,0],[2,0]], queries=[[1,0],[1,2]]` → `[true,true]`.
   - *Answer:* Propagate a reachability bitset along topological order, then each query is O(1).
   - *Gotcha:* In 1462, `[a,b]` means a comes **before** b, which is the reverse of 207's convention.
6. **Durations: a different problem** ([2050](https://leetcode.com/problems/parallel-courses-iii)). "Each course takes `time[i]` months and there are unlimited workers. What is the minimum total time?"
   - *Answer:* The longest path weighted by time: `finish[j] = time[j] + max(finish[dep])` in topological order. See `min_makespan`.
   - Adding k workers with durations makes it an NP-hard scheduling problem. Say so, then use critical-path-first list scheduling as the heuristic.
7. **Probing questions:**
   - Lexicographically smallest order → swap the queue for a min-heap.
   - Recursion depth limits → use iterative DFS, or just Kahn's algorithm.
   - The dependency graph changes online → recheck the cycle locally from the new edge.
   - Edges are given by name rather than id → map names to ids first, and check for unknown names and duplicates.

## The 1-hour live Codility format

- **Run your code early and often.** Codility Interview lets you run code as many times as you like and add your own test cases. Python 3.12 is supported for algorithmic tasks.
- **Assume hidden tests:** If the session uses library tasks, hidden tests can also check performance against Big-O, so state complexity before you code.
- **AI tools may be enabled:** Interviewers can switch AI tools on for an interview. If they are on, review every line the AI suggests before accepting it.
- **Time:** Plan for one medium-hard problem with follow-ups, or two mediums.
- **"Functional" topics may fill the rest of the hour:**
  - your ML evaluation platform end to end, including lineage
  - DAG orchestration with idempotent retries
  - GPU job scheduling and utilization
  - caching dataset shards and artifacts
  - Python details: GIL, generators, and shallow vs deep copy

## Sources

- **Tag data repos:**
  - [liquidslr/leetcode-company-wise-problems](https://github.com/liquidslr/leetcode-company-wise-problems)
  - [snehasishroy/leetcode-companywise-interview-questions](https://github.com/snehasishroy/leetcode-companywise-interview-questions)
  - [krishnadey30/LeetCode-Questions-CompanyWise](https://github.com/krishnadey30/LeetCode-Questions-CompanyWise)
  - [hxu296/leetcode-company-wise-problems-2022](https://github.com/hxu296/leetcode-company-wise-problems-2022)
- **GM candidate reports:**
  - [Jointaro, Apr 2025](https://www.jointaro.com/interviews/companies/general-motors/experiences/software-engineer-united-states-april-1-2025-no-offer-neutral-a5196136/)
  - [Jointaro, Aug 2025](https://www.jointaro.com/interviews/companies/general-motors/experiences/staff-software-engineer-sunnyvale-california-august-1-2025-no-offer-negative-44d7a066/)
  - [Jointaro, Sept 2025](https://www.jointaro.com/interviews/companies/general-motors/experiences/senior-software-engineer-united-states-september-1-2025-declined-offer-negative-d625bc6c/)
  - [Glassdoor GM, Jan 2026](https://www.glassdoor.com/Interview/General-Motors-GM-Interview-RVW80151828.htm) (Codility round format only; not scored)
- **Cruise transactional KV store reports:**
  - [LeetCode Discuss, 2021](https://leetcode.com/discuss/interview-question/1617100/phone-screen-cruise/)
  - [Glassdoor Cruise Senior SWE](https://www.glassdoor.com/Interview/Cruise-Senior-Software-Engineer-Interview-Questions-EI_IE977351.0,6_KO7,31.htm)
  - [LeetCode Discuss, 2019](https://leetcode.com/discuss/interview-question/421107/cruise-automation-onsite-transactional-map/)
- **Codility:**
  - [Candidate interface](https://support.codility.com/hc/en-us/articles/360043827893-Candidate-Interface)
  - [Scoring](https://support.codility.com/hc/en-us/articles/360043318374)
  - [Supported technologies](https://support.codility.com/hc/en-us/articles/360043823713-What-technologies-does-Codility-support)
  - [AI in interviews](https://www.codility.com/ai-info/)
- **Every report used in the score:** listed with its URL in [`data/reports.csv`](data/reports.csv).
