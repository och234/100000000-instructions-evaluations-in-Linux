# GM (AV / Embodied AI ML Infra): Top 10 Coding Questions to Expect

Tested reference solutions for all ten are in [`gm_top10.py`](gm_top10.py). Run `python3 gm_top10.py` to check them.

## How this list was built

Each question is ranked by how much evidence points to it, not by how hard it is.

1. **GM's LeetCode company tag.** These are community snapshots of LeetCode Premium frequency data, last updated mid-2025.
2. **Cruise's tag and Cruise screen reports.** GM moved Cruise's AV engineering into GM in 2025, so the AV and embodied-AI interview loop comes largely from Cruise.
3. **Glassdoor, Blind, and Jointaro reports for GM SWE and AV roles.** Candidates describe several LeetCode-style rounds, mostly medium difficulty. A January 2026 senior SWE report described six rounds, and three of them were coding.
4. **What the role's day-to-day work suggests.** Expect DAGs and pipelines, time windows, grids and maps, and caches.

| # | Problem | LC | Pattern | Evidence |
|---|---------|----|---------|----------|
| 1 | Merge Intervals | [56](https://leetcode.com/problems/merge-intervals) | Sort + sweep | GM tag (most recent, 6-mo window); Cruise |
| 2 | Number of Connected Components in an Undirected Graph | [323](https://leetcode.com/problems/number-of-connected-components-in-an-undirected-graph) | Union-Find / BFS | GM tag #1 all-time |
| 3 | LRU Cache | [146](https://leetcode.com/problems/lru-cache) | Hashmap + DLL | GM tag; Glassdoor (infotainment) |
| 4 | Minimum Path Sum → weighted grid w/ obstacles | [64](https://leetcode.com/problems/minimum-path-sum) → [1631](https://leetcode.com/problems/path-with-minimum-effort) | DP → Dijkstra | GM tag; Jointaro; Cruise "weighted traversal cost" |
| 5 | Course Schedule I/II | [207](https://leetcode.com/problems/course-schedule)/[210](https://leetcode.com/problems/course-schedule-ii) | Topological sort | Cruise tag |
| 6 | Robot grid simulation (turn right when blocked; stop at goal or loop) | ~[874](https://leetcode.com/problems/walking-robot-simulation)/[1041](https://leetcode.com/problems/robot-bounded-in-circle)/[489](https://leetcode.com/problems/robot-room-cleaner) | Simulation + state cycle detection | Cruise screen (Interview Query) |
| 7 | Implement Trie | [208](https://leetcode.com/problems/implement-trie-prefix-tree) | Trie | GM tag |
| 8 | Dot Product of Two Sparse Vectors | [1570](https://leetcode.com/problems/dot-product-of-two-sparse-vectors) | Two pointers / hashmap | GM tag |
| 9 | Synonymous Sentences | [1258](https://leetcode.com/problems/synonymous-sentences) | Union-Find + backtracking | Cruise tag #1 |
| 10 | Serialize and Deserialize Binary Tree | [297](https://leetcode.com/problems/serialize-and-deserialize-binary-tree) | Preorder + null markers | GM tag (Hard) |

**Next five, if you have time:**
- [First Missing Positive (41)](https://leetcode.com/problems/first-missing-positive)
- [Maximum Sum of 3 Non-Overlapping Subarrays (689)](https://leetcode.com/problems/maximum-sum-of-3-non-overlapping-subarrays)
- [Gas Station (134)](https://leetcode.com/problems/gas-station) (a variant was reported on Glassdoor)
- [Word Ladder (127)](https://leetcode.com/problems/word-ladder) (Cruise)
- [Maximum Number of Events That Can Be Attended (1353)](https://leetcode.com/problems/maximum-number-of-events-that-can-be-attended) (Cruise)

---

## Per-question notes: likely AV/ML-infra twist and follow-ups

### 1. Merge Intervals
- **Twist:** Merge overlapping time windows from drive logs, such as disengagements, sensor dropouts, or GPU reservation windows.
- **Follow-ups:**
  - The intervals arrive as a stream. Keep a sorted structure, or bisect into a list.
  - Insert one new interval ([LC 57](https://leetcode.com/problems/insert-interval)).
  - Find the free gaps between intervals ([LC 759](https://leetcode.com/problems/employee-free-time)).
  - What is the most windows open at the same time? Use a sweep line or a heap ([LC 253](https://leetcode.com/problems/meeting-rooms-ii)).
- **Complexity:** O(n log n).

### 2. Number of Connected Components
- **Twist:** Cluster lidar points that sit within distance *d* of each other, or count connected subgraphs in a service or dataset dependency graph.
- **Follow-ups:**
  - Edges arrive online. Union-Find handles this naturally ([LC 305](https://leetcode.com/problems/number-of-islands-ii)).
  - Explain path compression plus union by rank or size, and the α(n) bound.
  - Compare BFS and DFS against Union-Find on space use and on how each handles dynamic edges.

### 3. LRU Cache
- **Twist:** A cache of model artifacts or feature shards.
- **Follow-ups:**
  - Per-entry TTL.
  - Capacity counted in bytes rather than entries.
  - Thread safety. Start with one lock, then talk about lock striping.
  - LFU instead of LRU ([LC 460](https://leetcode.com/problems/lfu-cache)).
- **What they check:** Write the doubly linked list yourself. `OrderedDict` is fine to *mention*, but not to submit.

### 4. Minimum Path Sum, then a weighted grid with obstacles
- **Start:** With right/down moves only, a 1-D DP solves it in O(mn) time and O(n) space.
- **Twist:** Allow 4-directional moves, add obstacles, and give each cell a terrain cost. Now it is Dijkstra, O(mn log mn). The Cruise version of this asks for the "shortest collision-free path with dynamic obstacles."
- **Follow-ups:**
  - A* with a Manhattan heuristic.
  - An unknown map (Robot Room Cleaner / [LC 1778](https://leetcode.com/problems/shortest-path-in-a-hidden-grid)).
  - Obstacles that change over time. Add time to the state.

### 5. Course Schedule I/II
- **Twist:** This is the closest match to the ML-infra role. Schedule training or eval pipeline stages that depend on each other, and reject DAGs that contain a cycle.
- **Follow-ups:**
  - Each task has a duration and you have unlimited workers. Find the critical path ([LC 1136](https://leetcode.com/problems/parallel-courses), [LC 2050](https://leetcode.com/problems/parallel-courses-iii)).
  - You have only *k* workers. Use a priority queue simulation.
  - Report *which* cycle blocks the schedule. Use DFS with three colors.

### 6. Robot grid simulation
- **Setup:** The robot starts at (0,0) facing east. It moves forward if it can, and turns right otherwise. Return its path until it reaches the goal or starts repeating.
- **Key insight:** A loop means a repeated *(row, col, heading)* state, not just a repeated cell. There are at most 4·R·C states, which bounds the run.
- **Follow-ups:**
  - Count how many distinct cells it cleans ([LC 2061](https://leetcode.com/problems/number-of-spaces-cleaning-robot-cleaned)).
  - Let it turn left as well.
  - Run several robots at once and handle collisions.

### 7. Implement Trie
- **Twist:** Prefix search over ROS topic names, log paths, or dataset keys.
- **Follow-ups:**
  - Autocomplete the top *k* by frequency. Cache the top *k* at each node.
  - Wildcard search ([LC 211](https://leetcode.com/problems/design-add-and-search-words-data-structure)).
  - Delete.
  - Memory: dict children compared with fixed arrays.

### 8. Sparse Vector Dot Product
- **Twist:** Sparse feature vectors or embeddings.
- **Follow-ups:**
  - One vector is dense and one is sparse. Iterate over the sparse side only.
  - The two vectors differ greatly in size. Binary-search into the larger one for O(k_small · log k_large).
  - Why store sorted pairs instead of a hashmap? Hashing has a cost, and sorted pairs give better locality.

### 9. Synonymous Sentences
- **Approach:** Use Union-Find to group synonyms, sort each group, then backtrack over the word positions.
- **Follow-ups:**
  - The output grows exponentially. Talk about streaming results through a generator.
  - Return only the count of sentences, which is a product of group sizes.

### 10. Serialize / Deserialize Binary Tree
- **Follow-ups:**
  - Make it iterative so very deep trees don't overflow the recursion stack. The reference solution does this.
  - BST-only variant: no null markers are needed ([LC 449](https://leetcode.com/problems/serialize-and-deserialize-bst)).
  - N-ary trees ([LC 428](https://leetcode.com/problems/serialize-and-deserialize-n-ary-tree)).
  - Use a compact binary format instead of strings.

---

## How to run the coding rounds (senior/staff bar)

- **Clarify first.** Ask about input size, whether data arrives as a stream or a batch, what invalid input looks like, and which output order is required. AV interviewers look for this habit.
- **Say the complexity before you code.** Once the code passes, name the next bottleneck and how you would fix it.
- **Write your own small tests as you go.** Cover empty input, a single element, duplicates, a cycle, and an unreachable target.
- **Expect a follow-up that moves into infrastructure.** Common ones: what changes if the data doesn't fit in memory, if it arrives from many producers, or if it needs to be thread-safe.
- **Prepare in both Python and C++.** Python is the default for ML infra. C++ came up in GM's embedded and AV loops, so confirm the language with your recruiter.

## Sources

- [LeetCode company-wise problem lists (General Motors and Cruise folders)](https://github.com/liquidslr/leetcode-company-wise-problems)
- [Glassdoor: GM Senior Software Engineer interview reports](https://www.glassdoor.com/Interview/General-Motors-GM-Senior-Software-Engineer-Interview-Questions-EI_IE279.0,17_KO18,42.htm)
- [Interview Query: Cruise Software Engineer guide (robot grid question)](https://www.interviewquery.com/interview-guides/cruise-software-engineer)
- [Dataford: Cruise Software Engineer guide (weighted and dynamic-obstacle grid paths)](https://dataford.io/interview-guides/cruise/software-engineer)
- [Dataford: GM Software Engineer guide](https://dataford.io/interview-guides/general-motors-gm/software-engineer)
- [Jointaro: GM Senior SWE experience, Sept 2025 (minimum path sum)](https://www.jointaro.com/interviews/companies/general-motors/experiences/senior-software-engineer-united-states-september-1-2025-declined-offer-negative-d625bc6c/)
- [Blind: GM interview discussions (AV org coding round is LeetCode-style)](https://www.teamblind.com/company/General-Motors/posts/general-motors-interview)
- [GM job posting: AV ML Infrastructure (team scope: Embodied AI, simulation)](https://www.themuse.com/jobs/generalmotors/2026-summer-intern-aiml-engineer-av-ml-infrastructure-bachelors)
