"""Rank likely interview questions by frequency x recency.

Inputs (in ./data):
  tag_snapshots.csv  -- every historical snapshot of the GM and Cruise LeetCode company-tag
                        lists from community repos (built by data/extract_tag_snapshots.py)
  reports.csv        -- candidate interview reports (Glassdoor, Jointaro, ...), dated when known;
                        slug is the LeetCode slug, or "custom:<name>" for non-LeetCode questions

Scoring, per question (GM and Cruise rows merged, since the team is ex-Cruise inside GM):
  last_ask   Estimated date it was last asked.
             Positive evidence: a snapshot listing the question in a time-bounded window
             (30d/3mo/6mo/1y/2y) means an ask in [asof - len, asof].
             Negative evidence: a snapshot of the same company that still lists the question
             all-time, publishes a non-empty window list, but leaves the question out of it
             means no ask in (asof - len, asof].
             Each positive interval minus all negative intervals; take the midpoint of the
             latest surviving piece (or, if snapshots contradict each other and nothing
             survives, the window's earliest date), then the max over intervals and dated
             reports. Only-untimed questions ("all", ">6mo") get
             first_seen - 365d; questions known only from undated reports get today - 3y.
  recency    0.5 ** (age_days / half_life)            (default half-life 365 days)
  tag_freq   LeetCode's within-company frequency, normalized to [0, 1] per list. Per dataset,
             take the latest snapshot whose all-time list has the question (max over companies
             in that snapshot), then average across datasets. Report-only questions get a
             0.5 prior (a credible report counts as a mid-frequency signal).
  repeat     How many distinct snapshots/reports saw it asked inside a time window,
             log-scaled to [0, 1]. Rewards questions that keep coming back.
  frequency  0.5 * tag_freq + 0.5 * repeat
  score      frequency * recency
Rows dated after --today are ignored, so the ranking can be back-tested.

Usage: python3 score_questions.py [--today YYYY-MM-DD] [--half-life DAYS] [--top N]
"""

import argparse
import csv
import math
import os
from collections import defaultdict
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
WINDOW_DAYS = {"30d": 30, "3mo": 91, "6mo": 182, "1y": 365, "2y": 730}
UNTIMED_ASSUMED_LAG = timedelta(days=365)
UNKNOWN_REPORT_AGE = timedelta(days=1095)
SENSITIVITY_HALF_LIVES = (180, 365, 730)


def _d(s: str) -> date:
    return date.fromisoformat(s)


def load_rows(name: str):
    path = os.path.join(HERE, "data", name)
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    if any(None in r for r in rows):
        raise ValueError(f"{name}: a row has more fields than the header (unquoted comma?)")
    return rows


def _subtract(lo: int, hi: int, cuts):
    """[lo, hi] minus the union of (c_lo, c_hi] cuts, as inclusive integer-day pieces."""
    pieces = [(lo, hi)]
    for c_lo, c_hi in cuts:
        nxt = []
        for a, b in pieces:
            if c_hi < a or c_lo + 1 > b:
                nxt.append((a, b))
                continue
            if a <= c_lo:
                nxt.append((a, c_lo))
            if c_hi < b:
                nxt.append((c_hi + 1, b))
        pieces = nxt
    return pieces


def _estimate_last_ask(positives, negatives):
    best = None
    for lo, hi in positives:
        pieces = _subtract(lo, hi, negatives)
        if pieces:
            est = (pieces[-1][0] + pieces[-1][1]) // 2
        else:  # snapshots contradict each other -> conservative: the window's earliest date
            est = lo
        best = est if best is None else max(best, est)
    return best


def build_features(today: date):
    snaps = [r for r in load_rows("tag_snapshots.csv") if _d(r["asof"]) <= today]
    reports = [r for r in load_rows("reports.csv") if not r["date"] or _d(r["date"]) <= today]

    # Index every published list.
    lists = defaultdict(set)  # (dataset, asof, company, window) -> slugs
    list_max = defaultdict(float)
    for r in snaps:
        key = (r["dataset"], r["asof"], r["company"], r["window"])
        lists[key].add(r["slug"])
        if r["frequency"]:
            list_max[key] = max(list_max[key], float(r["frequency"]))
    snapshot_windows = defaultdict(set)  # (dataset, asof, company) -> timed windows published
    for dataset, asof, company, window in lists:
        if window in WINDOW_DAYS:
            snapshot_windows[(dataset, asof, company)].add(window)

    q = defaultdict(lambda: {
        "title": "", "difficulty": "", "companies": set(), "first_seen": None,
        "positives": [], "negatives": [], "report_dates": [], "freq": {},
        "repeat_events": set(), "reports": [], "timed": False,
    })
    for r in snaps:
        item = q[r["slug"]]
        item["title"] = item["title"] or r["title"]
        item["difficulty"] = item["difficulty"] or r["difficulty"]
        item["companies"].add(r["company"])
        asof = _d(r["asof"])
        item["first_seen"] = min(item["first_seen"] or asof, asof)
        if r["window"] in WINDOW_DAYS:
            n = asof.toordinal()
            item["positives"].append((n - WINDOW_DAYS[r["window"]], n))
            item["timed"] = True
            item["repeat_events"].add((r["dataset"], r["company"], r["asof"]))
        elif r["window"] == "all":
            # Negative evidence: still listed all-time, but absent from a published window.
            for window in snapshot_windows[(r["dataset"], r["asof"], r["company"])]:
                if r["slug"] not in lists[(r["dataset"], r["asof"], r["company"], window)]:
                    n = asof.toordinal()
                    item["negatives"].append((n - WINDOW_DAYS[window], n))
            if r["frequency"]:
                key = (r["dataset"], r["asof"], r["company"], r["window"])
                norm = float(r["frequency"]) / list_max[key] if list_max[key] else 0.0
                prev = item["freq"].get(r["dataset"])
                if prev is None or r["asof"] > prev[0]:
                    item["freq"][r["dataset"]] = (r["asof"], norm)
                elif r["asof"] == prev[0]:
                    item["freq"][r["dataset"]] = (r["asof"], max(prev[1], norm))

    for rep in reports:
        item = q[rep["slug"]]
        item["title"] = item["title"] or rep["title"]
        item["companies"].add(rep["company"])
        item["reports"].append(rep)
        item["repeat_events"].add(("report", rep["source_url"], rep["date"]))
        if rep["date"]:
            item["report_dates"].append(_d(rep["date"]).toordinal())

    for item in q.values():
        candidates = list(item["report_dates"])
        if item["positives"]:
            candidates.append(_estimate_last_ask(item["positives"], item["negatives"]))
        if candidates:
            item["last_ask"], item["basis"] = date.fromordinal(max(candidates)), ""
        elif item["first_seen"]:
            item["last_ask"], item["basis"] = item["first_seen"] - UNTIMED_ASSUMED_LAG, "*"
        else:
            item["last_ask"], item["basis"] = today - UNKNOWN_REPORT_AGE, "**"
        freqs = [v for _, v in item["freq"].values()]
        if freqs:
            item["tag_freq"] = sum(freqs) / len(freqs)
        else:  # report-only question: a credible report counts as a mid-frequency signal
            item["tag_freq"] = 0.5 if item["reports"] else 0.0
    return q


def score(q, today: date, half_life: float):
    max_repeat = max((len(i["repeat_events"]) for i in q.values()), default=1) or 1
    out = []
    for slug, i in q.items():
        repeat = math.log1p(len(i["repeat_events"])) / math.log1p(max_repeat)
        frequency = 0.5 * i["tag_freq"] + 0.5 * repeat
        age = max(0, (today - i["last_ask"]).days)
        recency = 0.5 ** (age / half_life)
        out.append({
            "slug": slug, "title": i["title"], "difficulty": i["difficulty"],
            "companies": "+".join(sorted(i["companies"])), "last_ask": i["last_ask"].isoformat(),
            "basis": i["basis"], "age_days": age, "tag_freq": i["tag_freq"],
            "repeat_n": len(i["repeat_events"]), "frequency": frequency, "recency": recency,
            "score": frequency * recency, "reports": len(i["reports"]),
            "link": (i["reports"][0]["source_url"] if slug.startswith("custom:") and i["reports"]
                     else f"https://leetcode.com/problems/{slug}"),
        })
    out.sort(key=lambda r: (-r["score"], r["slug"]))
    for rank, r in enumerate(out, 1):
        r["rank"] = rank
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", default="2026-10-19")
    ap.add_argument("--half-life", type=float, default=365)
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()
    today = _d(args.today)

    q = build_features(today)
    ranked = score(q, today, args.half_life)
    rank_at = {h: {r["slug"]: r["rank"] for r in score(q, today, h)} for h in SENSITIVITY_HALF_LIVES}

    print(f"Ranked by frequency x recency (today={today}, half-life={args.half_life:g}d)\n")
    print("| # | Question | Diff | Source | Est. last asked | Freq | Recency | Score | Rank @ 180/365/730d |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in ranked[: args.top]:
        ranks = "/".join(str(rank_at[h][r["slug"]]) for h in SENSITIVITY_HALF_LIVES)
        print(f"| {r['rank']} | [{r['title']}]({r['link']}) | {r['difficulty'] or '-'} "
              f"| {r['companies']} | {r['last_ask']}{r['basis']} | {r['frequency']:.2f} | {r['recency']:.2f} "
              f"| {r['score']:.3f} | {ranks} |")
    print("\n`*` = only seen in untimed lists (all-time / >6mo): last-asked assumed first-seen - 1 year.")
    print("`**` = known only from undated reports: last-asked assumed 3 years ago.")


if __name__ == "__main__":
    main()
