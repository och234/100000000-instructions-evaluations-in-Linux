# GM Embodied AI ML Infra (ex-Cruise) Screen: Top 10 Coding Questions

**Target:** The 1-hour "Technical/Functional Assessment" screen for *Senior ML Infrastructure Engineer, Embodied AI Scaling Foundations* (JR-202601904). The screen runs live on Codility, and the team is the former Cruise group now inside GM.

**Ranked by:** How often each question was asked, combined with how recently. Run [`score_questions.py`](score_questions.py) to reproduce the ranking.

**Solutions:** Tested solutions for all ten, plus the wildcard, are in [`gm_top10.py`](gm_top10.py). Run `python3 gm_top10.py`; the run includes brute-force cross-checks.

## The ranking (as of 2026-10-19, recency half-life 365 days)

| # | Question | Source | Est. last asked | Freq | Recency | Score | Rank at 180/365/730-day half-life |
|---|---|---|---|---|---|---|---|
| 1 | [Number of Connected Components in an Undirected Graph (323)](https://leetcode.com/problems/number-of-connected-components-in-an-undirected-graph) | GM | 2025-11 | 1.00 | 0.53 | 0.533 | 4 / 1 / 1 |
| 2 | [Number of Steps to Reduce a Number in Binary Representation to One (1404)](https://leetcode.com/problems/number-of-steps-to-reduce-a-number-in-binary-representation-to-one) | GM | 2026-04 | 0.68 | 0.70 | 0.473 | 1 / 2 / 2 |
| 3 | [Maximum Sum of 3 Non-Overlapping Subarrays (689)](https://leetcode.com/problems/maximum-sum-of-3-non-overlapping-subarrays), Hard | GM | 2026-04 | 0.65 | 0.70 | 0.456 | 2 / 3 / 3 |
| 4 | [Merge Intervals (56)](https://leetcode.com/problems/merge-intervals) | GM + Cruise | 2026-05 | 0.56 | 0.75 | 0.418 | 3 / 4 / 5 |
| 5 | [Minimum Path Sum (64)](https://leetcode.com/problems/minimum-path-sum) | GM | 2025-09 | 0.80 | 0.46 | 0.367 | 6 / 5 / 4 |
| 6 | [LRU Cache (146)](https://leetcode.com/problems/lru-cache) | GM + Cruise | 2025-09 | 0.71 | 0.46 | 0.326 | 7 / 6 / 6 |
| 7 | [Minimum Deletions to Make Character Frequencies Unique (1647)](https://leetcode.com/problems/minimum-deletions-to-make-character-frequencies-unique) | GM | 2026-04 | 0.41 | 0.70 | 0.282 | 5 / 7 / 10 |
| 8 | [Course Schedule I/II (207/210)](https://leetcode.com/problems/course-schedule) | Cruise | 2025-04 | 0.76 | 0.35 | 0.264 | 9 / 8 / 7 |
| 9 | [Implement Trie (208)](https://leetcode.com/problems/implement-trie-prefix-tree) | GM + Cruise | 2025-08 | 0.56 | 0.45 | 0.250 | 8 / 9 / 8 |
| 10 | [Synonymous Sentences (1258)](https://leetcode.com/problems/synonymous-sentences) | Cruise | 2024-10 | 0.72 | 0.25 | 0.180 | 10 / 10 / 9 |

- **Stability:** The same ten questions make up the top 10 at every half-life from 180 to 730 days. Only their order changes.
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
- **Candidate reports:** 24 GM and Cruise reports from Glassdoor, Jointaro, LeetCode Discuss, Blind and 1point3acres, dated where possible, in [`data/reports.csv`](data/reports.csv).

**Per-question formula**

- **Est. last asked:** Each snapshot puts a question inside a time window (30 days, 3 months, 6 months, 1 year or 2 years). Take the midpoint of each window and keep the latest one, or a later dated report if there is one.
- **Recency:** `0.5 ^ (age_days / 365)`.
- **Frequency:** `0.5 * LeetCode within-company frequency (normalized) + 0.5 * repeat appearances (log-scaled)`.
- **Score:** `frequency * recency`.

**Caveats**

- **GM's tag covers every GM team**, including IT and infotainment, not only the AV team. Cruise's tag is the team's own history, but it is older. Neither one is "this interviewer's question bank."
- **Questions seen only in all-time lists** get an assumed last-asked date (first seen minus one year).
- **Undated reports** are treated as three years old.

## What to prepare for each question

The bullet under each question is the ML-infra follow-up the interviewer is likely to push toward.

1. **Connected Components (323).** Union-Find with path compression and union by size, about O(E·α(V)).
   - *Infra twist:* Edges arrive online, as in [305](https://leetcode.com/problems/number-of-islands-ii). Or cluster sensor points that sit within distance d of each other.
2. **Steps to Reduce Binary to One (1404).** Scan right to left with a carry. An odd bit adds 2 steps and sets carry=1; an even bit adds 1 step. O(n), with no big-int conversion.
   - *Twist:* The string has 10⁶ bits. Explain why `int(s, 2)` with simulation becomes O(n²).
3. **Max Sum of 3 Non-Overlapping Subarrays (689).** Compute window sums. Build a best-left argmax array (strict `>`) and a best-right argmax array (`>=`) so ties go to the leftmost index. Then sweep the middle window. O(n).
   - *Twist:* Generalize to m windows with an O(n·m) DP.
4. **Merge Intervals (56).** Sort, then sweep.
   - *Twist:* Intervals arrive as a stream or out of order ([352](https://leetcode.com/problems/data-stream-as-disjoint-intervals), [715](https://leetcode.com/problems/range-module)).
   - Other follow-ups: [Insert Interval (57)](https://leetcode.com/problems/insert-interval), and the peak number of concurrent jobs ([Meeting Rooms II, 253](https://leetcode.com/problems/meeting-rooms-ii)).
5. **Minimum Path Sum (64).** 1-D DP.
   - *Twist:* 4-directional moves with obstacles and weighted cells make it Dijkstra (`min_cost_path`). A* is the next step.
6. **LRU Cache (146).** Hashmap plus a doubly linked list you write yourself. A 2020 Cruise screen disallowed `OrderedDict`.
   - *Twist:* Per-entry TTL; capacity in bytes; thread safety (one lock, then striping); [LFU (460)](https://leetcode.com/problems/lfu-cache).
7. **Min Deletions for Unique Frequencies (1647).** Count characters, sort the counts descending, and decrement each one until it reaches an unused count. 0 is always allowed.
8. **Course Schedule I/II (207/210).** Kahn's algorithm; a cycle means no valid order.
   - *Twist:* A pipeline DAG where each stage has a duration. The makespan is the critical path ([2050](https://leetcode.com/problems/parallel-courses-iii)); see `min_makespan`. Next, *k* workers, simulated with a heap.
9. **Implement Trie (208).** Nested dicts with an end marker.
   - *Twist:* Top-k autocomplete ([642](https://leetcode.com/problems/design-search-autocomplete-system)) and wildcard search ([211](https://leetcode.com/problems/design-add-and-search-words-data-structure)).
10. **Synonymous Sentences (1258).** Union-Find to group synonyms, sort each group, backtrack over word positions, then sort the output.
    - *Twist:* Return only the count, which is the product of group sizes.

**Wildcard: nested-transaction KV store**

- **Design:** Keep a stack of dict layers and mark deletes with a tombstone. `commit` merges the innermost layer into its parent; `rollback` pops it. `get` is O(depth).
- **Say your commit semantics out loud.** Ask whether `commit` merges one level or flushes every level.
- **Follow-up:** Make `get` O(1) with an undo log.
- **Watch for the failure seen in the 2021 report:** copying instead of layering, or using a shallow copy.

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
  - [Glassdoor GM, Jan 2026](https://www.glassdoor.com/Interview/General-Motors-GM-Interview-RVW80151828.htm)
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
