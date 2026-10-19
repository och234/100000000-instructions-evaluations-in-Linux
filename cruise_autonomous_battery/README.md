# Autonomous-mode battery drain

Given a single car's battery log, compute:

1. total time spent in autonomous mode
2. average hourly battery drain while in autonomous mode

Each input row is `timestamp battery_percentage mode`, space separated:

```
1 10 autonomous
2 20 manual
3 20 autonomous
```

## Assumptions

The prompt leaves several things open. These are the defaults; each one that
could reasonably go the other way can be changed with a flag.

| Question | Decision |
|---|---|
| Which mode covers the time between rows? | **Zero-order hold:** row *i*'s mode holds until row *i+1*, so `[t_i, t_{i+1})` counts as `mode_i` and its drain is `b_i - b_{i+1}`. Rows are state samples, so this counts transition intervals correctly. The alternative ("both endpoints must be autonomous") drops every interval where the car switches mode. |
| What about the last row? | It has no successor, so it adds **no time**. We don't know how long that state lasted. |
| Timestamp units? | Seconds by default. Use `--seconds-per-unit 3600` if timestamps are hours. |
| What if the battery goes up during an autonomous interval? | `net` (default): the signed delta counts, so regen offsets drain. That gives the true range metric. `discharge-only`: increases are ignored. |
| What about long gaps (car parked, logger down)? | Counted by default. `--max-gap N` drops intervals longer than N units, because the mode during an outage is unknown. |
| Unsorted rows? | `analyze` sorts by timestamp. The streaming accumulator rejects out-of-order samples. |
| Unknown modes (`charging`, `idle`)? | Treated as not autonomous. Mode matching ignores case. |
| No autonomous time? | Hourly drain is `None` / `n/a`, never a divide-by-zero. |
| Bad input? | Rejected with the 1-based line number (wrong field count, non-numeric value, battery outside [0, 100], non-finite timestamp). Blank lines are skipped. |

## Algorithm

```
sort samples by timestamp
for each consecutive pair (prev, cur):
    if prev.mode == autonomous and (no max_gap or dt <= max_gap):
        time  += cur.t - prev.t
        drain += prev.battery - cur.battery      # or max(0, ...) for discharge-only
hourly_drain = drain / (time * seconds_per_unit / 3600)
```

- **Time:** O(n log n) to sort. If the input is already ordered, it is one O(n) pass.
- **Memory:** `AutonomyAccumulator` uses O(1) state (previous sample plus two sums),
  so a log of any size can be streamed through it. `analyze` holds the whole
  log only because it sorts.

For the example above: `[1,2)` is autonomous and the battery goes 10 → 20, so
autonomous time is 1 unit and net drain is -10 (0 with `discharge-only`). A
battery increase while autonomous is physically a charge, so in real data it
points to a mislabeled mode or a sensor glitch. That ambiguity is why the
policy is configurable.

## Usage

```bash
python3 battery_log.py log.txt
cat log.txt | python3 battery_log.py --max-gap 900 --drain-policy discharge-only
```

```
autonomous time:   3600 units (1.0000 h)
battery drained:   10 %
avg hourly drain:  10.0000 %/h
est. hours/charge: 10.00 h
```

`est. hours/charge` is `100 / hourly_drain`. It answers the motivating question
directly: how long the car can drive autonomously on a full charge.

As a library:

```python
from battery_log import analyze, AutonomyAccumulator, parse_log

report = analyze(open("log.txt"))
report.autonomous_time, report.drain_pct_per_hour

acc = AutonomyAccumulator()          # streaming / unbounded input
for sample in parse_log(stream):
    acc.add(sample)
acc.report()
```

## Tests

```bash
cd cruise_autonomous_battery && python3 -m unittest -v
```

Standard library only; no dependencies.

## Likely follow-ups

- **Many cars:** add a `car_id` column and keep one accumulator per car in a
  dict. Memory is O(cars).
- **Fleet scale (batch):** partition by `car_id`, sort within each partition,
  and fold. In SQL, `LEAD(ts) / LEAD(battery) OVER (PARTITION BY car_id ORDER BY ts)`
  gives each row its next sample. Then sum over `mode = 'autonomous'`.
- **Out-of-order streams:** buffer with a watermark (allowed lateness) before
  feeding the accumulator, or bucket by time window and merge.
- **Better rate estimate:** time-weighted average across segments (what this
  computes) vs. per-trip rates; report percentiles and exclude idle-while-autonomous.
  Battery drain is non-linear in SoC, so condition on SoC band or temperature
  if the number feeds range prediction.
