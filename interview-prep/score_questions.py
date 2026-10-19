"""Rank likely interview questions by frequency x recency.

Inputs (in ./data):
  tag_snapshots.csv  -- every historical snapshot of the GM and Cruise LeetCode company-tag
                        lists from community repos (built by data/extract_tag_snapshots.py)
  reports.csv        -- candidate interview reports (Glassdoor, Jointaro, ...), dated when known;
                        slug is the LeetCode slug, or "custom:<name>" for non-LeetCode questions

Scoring, per question (GM and Cruise rows merged, since the team is ex-Cruise inside GM):
  last_ask   Estimated date it was last asked. For each snapshot where the question sits in a
             time-bounded window (30d/3mo/6mo/1y/2y), the ask happened in [asof - len, asof];
             take the midpoint, then the max over all snapshots and dated reports. Questions
             seen only in untimed lists ("all", ">6mo") get first_seen - 365d and are flagged.
  recency    0.5 ** (age_days / half_life)            (default half-life 365 days)
  tag_freq   LeetCode's within-company frequency, normalized to [0, 1] per list, from the
             latest snapshot that contains the question (mean across datasets).
  repeat     How many distinct snapshots/reports saw it asked inside a time window,
             log-scaled to [0, 1]. Rewards questions that keep coming back.
  frequency  0.5 * tag_freq + 0.5 * repeat
  score      frequency * recency

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
UNKNOWN_REPORT_AGE = timedelta(days=730)
SENSITIVITY_HALF_LIVES = (180, 365, 730)


def _d(s: str) -> date:
    return date.fromisoformat(s)


def load_rows(name: str):
    path = os.path.join(HERE, "data", name)
    if not os.path.exists(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def build_features(today: date):
    snaps = load_rows("tag_snapshots.csv")
    reports = load_rows("reports.csv")

    # Normalize frequency within each published list.
    list_max = defaultdict(float)
    for r in snaps:
        if r["frequency"]:
            key = (r["dataset"], r["asof"], r["company"], r["window"])
            list_max[key] = max(list_max[key], float(r["frequency"]))

    q = defaultdict(lambda: {
        "title": "", "difficulty": "", "companies": set(), "last_ask": None, "untimed_only": True,
        "first_seen": None, "freq_by_dataset": {}, "repeat_events": set(), "reports": [],
    })
    for r in snaps:
        item = q[r["slug"]]
        item["title"] = item["title"] or r["title"]
        item["difficulty"] = item["difficulty"] or r["difficulty"]
        item["companies"].add(r["company"])
        asof = _d(r["asof"])
        item["first_seen"] = min(item["first_seen"] or asof, asof)
        if r["window"] in WINDOW_DAYS:
            est = asof - timedelta(days=WINDOW_DAYS[r["window"]] / 2)
            item["last_ask"] = max(item["last_ask"] or est, est)
            item["untimed_only"] = False
            item["repeat_events"].add((r["dataset"], r["company"], r["asof"]))
        if r["frequency"] and r["window"] == "all":
            key = (r["dataset"], r["asof"], r["company"], r["window"])
            norm = float(r["frequency"]) / list_max[key] if list_max[key] else 0.0
            prev = item["freq_by_dataset"].get((r["dataset"], r["company"]))
            if prev is None or r["asof"] > prev[0]:
                item["freq_by_dataset"][(r["dataset"], r["company"])] = (r["asof"], norm)

    for rep in reports:
        item = q[rep["slug"]]
        item["title"] = item["title"] or rep["title"]
        item["companies"].add(rep["company"])
        item["reports"].append(rep)
        item["repeat_events"].add(("report", rep["source_url"], rep["date"]))
        if rep["date"]:
            d = _d(rep["date"])
            item["last_ask"] = max(item["last_ask"] or d, d)
            item["untimed_only"] = False

    for item in q.values():
        if item["last_ask"] is None:
            # untimed tag lists only: assume ~1y before first seen; undated reports only: 2y ago
            item["last_ask"] = (item["first_seen"] - UNTIMED_ASSUMED_LAG if item["first_seen"]
                                else today - UNKNOWN_REPORT_AGE)
        freqs = [v for _, v in item["freq_by_dataset"].values()]
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
        age = (today - i["last_ask"]).days
        recency = 0.5 ** (age / half_life)
        out.append({
            "slug": slug, "title": i["title"], "difficulty": i["difficulty"],
            "companies": "+".join(sorted(i["companies"])), "last_ask": i["last_ask"].isoformat(),
            "untimed_only": i["untimed_only"], "age_days": age, "tag_freq": i["tag_freq"],
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
        flag = "*" if r["untimed_only"] else ""
        ranks = "/".join(str(rank_at[h][r["slug"]]) for h in SENSITIVITY_HALF_LIVES)
        print(f"| {r['rank']} | [{r['title']}]({r['link']}) | {r['difficulty'] or '-'} "
              f"| {r['companies']} | {r['last_ask']}{flag} | {r['frequency']:.2f} | {r['recency']:.2f} "
              f"| {r['score']:.3f} | {ranks} |")
    print("\n`*` = only ever seen in untimed lists; last-asked date is an assumption (first seen - 1 year).")


if __name__ == "__main__":
    main()
