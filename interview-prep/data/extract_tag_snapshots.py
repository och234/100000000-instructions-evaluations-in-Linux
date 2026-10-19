"""Extract every GM/Cruise LeetCode company-tag snapshot from community repos' git history.
Usage: extract2.py OUT.csv LIQUIDSLR SNEHASISHROY KRISHNADEY30 HXU296"""
import csv, io, re, subprocess, sys

OUT, LQ, SN, KD, HX = sys.argv[1:6]
def git(repo, *a):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, check=True).stdout

# (repo, label, path regex -> company, explicit commit -> data-as-of date)
SOURCES = [
    (LQ, "liquidslr", {r"^General Motors/": "GM", r"^Cruise/": "Cruise"}, None),
    (SN, "snehasishroy", {r"^general-motors/": "GM", r"^cruise-automation/": "Cruise"},
     {"fba277f": "2026-07-12", "a09d3ba": "2026-05-24", "bbfccaa": "2026-02-21",
      "3a998c2": "2025-11-22", "b4c547f": "2025-07-12"}),
    # 2023 commit only added headers; data is as of the 2020-08-11 import
    (KD, "krishnadey30", {r"^cruise-automation_": "Cruise", r"^general-motors_": "GM"}, {"fb5f78b": "2020-08-11"}),
    (HX, "hxu296", {r"^companies/Cruise Automation\.csv$": "Cruise", r"^companies/General Motors\.csv$": "GM"}, {"e3c6e6a": "2022-05-10"}),
]
WINDOWS = [("thirty", "30d"), ("three", "3mo"), ("more-than-six", ">6mo"), ("more than six", ">6mo"),
           ("six", "6mo"), ("_6months", "6mo"), ("_1year", "1y"), ("_2year", "2y"), ("alltime", "all")]
def window_of(path):
    p = path.lower()
    return next((w for k, w in WINDOWS if k in p), "all")

rows = []
for repo, label, dirs, asof_map in SOURCES:
    paths = [p for p in git(repo, "ls-tree", "-r", "--name-only", "HEAD").split("\n")]
    if asof_map is None:  # commit date == data date; only commits that touched company files
        dirs_paths = sorted({p.split("/")[0] for p in paths if any(re.search(rx, p) for rx in dirs)})
        log = git(repo, "log", "--format=%h %cs", "--", *dirs_paths).split("\n")
        asof_map = dict(l.split() for l in log if l)
    for sha, asof in asof_map.items():
        for path in git(repo, "ls-tree", "-r", "--name-only", sha).split("\n"):
            comp = next((c for rx, c in dirs.items() if re.search(rx, path)), None)
            if not comp or not path.endswith(".csv"):
                continue
            text = git(repo, "show", f"{sha}:{path}")
            for r in csv.DictReader(io.StringIO(text)):
                r = {(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}
                url = r.get("url") or r.get("link") or r.get("leetcode question link") or r.get("problem_link") or ""
                title = r.get("title") or r.get("problem_name") or ""
                slug = url.rstrip("/").split("/problems/")[-1].split("/")[0]
                if not slug:
                    continue
                freq = (r.get("frequency") or r.get("frequency %") or r.get("num_occur") or "").rstrip("%")
                rows.append(dict(dataset=label, asof=asof, company=comp, window=window_of(path),
                                 slug=slug, title=title, difficulty=(r.get("difficulty") or "").title(), frequency=freq))
seen, out = set(), []
for r in rows:
    k = (r["dataset"], r["asof"], r["company"], r["window"], r["slug"])
    if k not in seen:
        seen.add(k); out.append(r)
out.sort(key=lambda r: (r["company"], r["slug"], r["asof"], r["dataset"], r["window"]))
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print(len(out), "rows written to", OUT)
