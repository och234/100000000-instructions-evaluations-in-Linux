"""Autonomous-mode time and battery drain from a single car's battery log.

Input rows are ``<timestamp> <battery_percentage> <mode>``, whitespace separated,
one per line.

Interval semantics (zero-order hold): a row's mode holds until the next row, so
the interval [t_i, t_{i+1}) is attributed to mode_i and its drain is
battery_i - battery_{i+1}. The final row has no successor and contributes no
time, since how long that state lasted is unknown.
"""

from __future__ import annotations

import argparse
import enum
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional

AUTONOMOUS = "autonomous"
SECONDS_PER_HOUR = 3600.0


@dataclass(frozen=True)
class Sample:
    timestamp: float
    battery: float  # percent, 0-100
    mode: str  # lower-cased


class DrainPolicy(enum.Enum):
    # Signed delta per interval: regenerative braking offsets consumption.
    # This is the right input for a range estimate.
    NET = "net"
    # Only decreases count; any increase within an interval is ignored.
    DISCHARGE_ONLY = "discharge-only"


@dataclass(frozen=True)
class AutonomyReport:
    autonomous_time: float  # in input timestamp units
    drain_pct: float  # percentage points consumed while autonomous
    seconds_per_unit: float = 1.0

    def __post_init__(self) -> None:
        if not self.seconds_per_unit > 0:
            raise ValueError(f"seconds_per_unit must be > 0, got {self.seconds_per_unit}")

    @property
    def autonomous_hours(self) -> float:
        return self.autonomous_time * self.seconds_per_unit / SECONDS_PER_HOUR

    @property
    def drain_pct_per_hour(self) -> Optional[float]:
        """Average drain while autonomous; None when there was no autonomous time."""
        hours = self.autonomous_hours
        return self.drain_pct / hours if hours > 0 else None

    @property
    def hours_to_empty(self) -> Optional[float]:
        """Autonomous hours a full charge lasts at the observed rate."""
        rate = self.drain_pct_per_hour
        return 100.0 / rate if rate is not None and rate > 0 else None


def parse_line(line: str, lineno: int) -> Sample:
    fields = line.split()
    if len(fields) != 3:
        raise ValueError(f"line {lineno}: expected 3 fields, got {len(fields)}: {line.strip()!r}")
    ts_raw, battery_raw, mode = fields
    try:
        timestamp = float(ts_raw)
        battery = float(battery_raw)
    except ValueError:
        raise ValueError(f"line {lineno}: non-numeric timestamp or battery: {line.strip()!r}") from None
    if not math.isfinite(timestamp):
        raise ValueError(f"line {lineno}: timestamp must be finite, got {ts_raw!r}")
    if not 0.0 <= battery <= 100.0:
        raise ValueError(f"line {lineno}: battery {battery_raw!r} outside [0, 100]")
    return Sample(timestamp, battery, mode.lower())


def parse_log(lines: str | Iterable[str]) -> Iterator[Sample]:
    """Yield samples, skipping blank lines. Line numbers in errors are 1-based."""
    if isinstance(lines, str):
        lines = lines.splitlines()
    for lineno, line in enumerate(lines, start=1):
        if line.strip():
            yield parse_line(line, lineno)


class AutonomyAccumulator:
    """Single-pass, O(1)-memory aggregator. Samples must arrive in time order.

    Use this directly for streaming or very large logs; ``analyze`` wraps it for
    the batch case.
    """

    def __init__(self, drain_policy: DrainPolicy = DrainPolicy.NET, max_gap: Optional[float] = None) -> None:
        if max_gap is not None and max_gap < 0:
            raise ValueError(f"max_gap must be >= 0, got {max_gap}")
        self._policy = drain_policy
        self._max_gap = max_gap
        self._prev: Optional[Sample] = None
        self._time = 0.0
        self._drain = 0.0

    def add(self, sample: Sample) -> None:
        prev = self._prev
        if prev is not None:
            dt = sample.timestamp - prev.timestamp
            if dt < 0:
                raise ValueError(f"out-of-order sample: t={sample.timestamp:g} after t={prev.timestamp:g}")
            # An interval longer than max_gap is a logging outage (car parked,
            # logger down); its mode is unknown, so it's attributed to nothing.
            if prev.mode == AUTONOMOUS and (self._max_gap is None or dt <= self._max_gap):
                self._time += dt
                delta = prev.battery - sample.battery
                self._drain += delta if self._policy is DrainPolicy.NET else max(delta, 0.0)
        self._prev = sample

    def report(self, seconds_per_unit: float = 1.0) -> AutonomyReport:
        return AutonomyReport(self._time, self._drain, seconds_per_unit)


def analyze(
    log: str | Iterable[str],
    *,
    seconds_per_unit: float = 1.0,
    drain_policy: DrainPolicy = DrainPolicy.NET,
    max_gap: Optional[float] = None,
) -> AutonomyReport:
    """Batch entry point. Sorts by timestamp, so unordered logs are fine."""
    acc = AutonomyAccumulator(drain_policy, max_gap)
    for sample in sorted(parse_log(log), key=lambda s: s.timestamp):
        acc.add(sample)
    return acc.report(seconds_per_unit)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Autonomous-mode time and hourly battery drain from a battery log.")
    parser.add_argument("logfile", nargs="?", default="-", help="log file path, or - for stdin (default)")
    parser.add_argument(
        "--seconds-per-unit",
        type=float,
        default=1.0,
        help="seconds per timestamp unit (default 1, i.e. epoch seconds; use 3600 if timestamps are hours)",
    )
    parser.add_argument(
        "--max-gap",
        type=float,
        default=None,
        help="drop intervals longer than this many timestamp units (logging outages)",
    )
    parser.add_argument(
        "--drain-policy",
        choices=[p.value for p in DrainPolicy],
        default=DrainPolicy.NET.value,
    )
    args = parser.parse_args(argv)

    try:
        text = sys.stdin.read() if args.logfile == "-" else Path(args.logfile).read_text()
        report = analyze(
            text,
            seconds_per_unit=args.seconds_per_unit,
            drain_policy=DrainPolicy(args.drain_policy),
            max_gap=args.max_gap,
        )
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    rate = report.drain_pct_per_hour
    to_empty = report.hours_to_empty
    print(f"autonomous time:   {report.autonomous_time:g} units ({report.autonomous_hours:.4f} h)")
    print(f"battery drained:   {report.drain_pct:g} %")
    print(f"avg hourly drain:  {'n/a (no autonomous time)' if rate is None else f'{rate:.4f} %/h'}")
    print(f"est. hours/charge: {'n/a' if to_empty is None else f'{to_empty:.2f} h'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
