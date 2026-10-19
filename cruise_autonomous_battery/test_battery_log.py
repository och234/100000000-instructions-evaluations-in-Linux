import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from battery_log import AutonomyAccumulator, AutonomyReport, DrainPolicy, analyze, main, parse_log


class AnalyzeTest(unittest.TestCase):
    def test_prompt_example(self):
        # [1,2) is autonomous (10 -> 20), [2,3) is manual, and the final row has
        # no successor, so it adds no time.
        log = "1 10 autonomous\n2 20 manual\n3 20 autonomous"
        r = analyze(log)
        self.assertEqual(r.autonomous_time, 1)
        self.assertEqual(r.drain_pct, -10)
        self.assertEqual(analyze(log, drain_policy=DrainPolicy.DISCHARGE_ONLY).drain_pct, 0)

    def test_hourly_rate_with_second_timestamps(self):
        log = """
            0    100 autonomous
            1800  95 autonomous
            3600  90 manual
            7200  90 manual
        """
        r = analyze(log)
        self.assertEqual(r.autonomous_time, 3600)
        self.assertEqual(r.drain_pct, 10)
        self.assertAlmostEqual(r.autonomous_hours, 1.0)
        self.assertAlmostEqual(r.drain_pct_per_hour, 10.0)
        self.assertAlmostEqual(r.hours_to_empty, 10.0)

    def test_multiple_autonomous_segments_exclude_manual_drain(self):
        log = """
            0     100 autonomous
            3600   90 manual
            7200   85 autonomous
            9000   80 autonomous
            10800  77 manual
        """
        # Autonomous: [0,3600) 10%, [7200,9000) 5%, [9000,10800) 3%.
        # The manual 90 -> 85 drop is excluded.
        r = analyze(log)
        self.assertEqual(r.autonomous_time, 7200)
        self.assertEqual(r.drain_pct, 18)
        self.assertAlmostEqual(r.drain_pct_per_hour, 9.0)

    def test_unsorted_input_matches_sorted(self):
        rows = ["0 100 autonomous", "3600 90 manual", "7200 85 autonomous", "9000 80 manual"]
        self.assertEqual(analyze(rows), analyze(list(reversed(rows))))

    def test_no_autonomous_time(self):
        r = analyze("0 100 manual\n3600 90 manual")
        self.assertEqual(r.autonomous_time, 0)
        self.assertEqual(r.drain_pct, 0)
        self.assertIsNone(r.drain_pct_per_hour)
        self.assertIsNone(r.hours_to_empty)

    def test_empty_and_single_row(self):
        for log in ["", "\n\n", "5 50 autonomous"]:
            with self.subTest(log=log):
                r = analyze(log)
                self.assertEqual((r.autonomous_time, r.drain_pct), (0, 0))
                self.assertIsNone(r.drain_pct_per_hour)

    def test_mode_is_case_insensitive_and_unknown_modes_are_not_autonomous(self):
        log = "0 100 AUTONOMOUS\n3600 90 Charging\n7200 100 autonomous\n10800 95 idle"
        r = analyze(log)
        self.assertEqual(r.autonomous_time, 7200)
        self.assertEqual(r.drain_pct, 15)

    def test_regen_net_vs_discharge_only(self):
        log = "0 80 autonomous\n1800 78 autonomous\n2700 79 autonomous\n3600 76 manual"
        self.assertEqual(analyze(log).drain_pct, 4)
        self.assertEqual(analyze(log, drain_policy=DrainPolicy.DISCHARGE_ONLY).drain_pct, 5)

    def test_max_gap_drops_outage_intervals(self):
        # The logger is silent overnight; that gap shouldn't count as driving.
        log = "0 90 autonomous\n600 89 autonomous\n50000 89 autonomous\n50600 88 manual"
        self.assertEqual(analyze(log).autonomous_time, 50600)
        r = analyze(log, max_gap=3600)
        self.assertEqual(r.autonomous_time, 1200)
        self.assertEqual(r.drain_pct, 2)

    def test_seconds_per_unit(self):
        r = analyze("0 100 autonomous\n2 80 manual", seconds_per_unit=3600)
        self.assertAlmostEqual(r.autonomous_hours, 2.0)
        self.assertAlmostEqual(r.drain_pct_per_hour, 10.0)

    def test_duplicate_timestamps_add_no_time(self):
        r = analyze("0 100 autonomous\n0 100 manual\n3600 90 manual")
        self.assertEqual(r.autonomous_time, 0)
        self.assertIsNone(r.drain_pct_per_hour)

    def test_invalid_config(self):
        with self.assertRaises(ValueError):
            AutonomyReport(1, 1, seconds_per_unit=0)
        with self.assertRaises(ValueError):
            AutonomyAccumulator(max_gap=-1)


class ParseTest(unittest.TestCase):
    def test_skips_blank_lines_and_reports_physical_line_numbers(self):
        with self.assertRaisesRegex(ValueError, r"^line 3: expected 3 fields"):
            list(parse_log("0 100 autonomous\n\n1 99\n"))

    def test_rejects_bad_values(self):
        cases = {
            "x 50 autonomous": "non-numeric",
            "0 abc autonomous": "non-numeric",
            "0 101 autonomous": r"outside \[0, 100\]",
            "0 -1 autonomous": r"outside \[0, 100\]",
            "0 nan autonomous": r"outside \[0, 100\]",
            "inf 50 autonomous": "finite",
            "0 50 autonomous extra": "expected 3 fields",
        }
        for line, msg in cases.items():
            with self.subTest(line=line), self.assertRaisesRegex(ValueError, msg):
                list(parse_log(line))


class AccumulatorTest(unittest.TestCase):
    def test_streaming_matches_batch(self):
        log = "0 100 autonomous\n1800 95 manual\n3600 92 autonomous\n5400 88 manual"
        acc = AutonomyAccumulator()
        for sample in parse_log(log):
            acc.add(sample)
        self.assertEqual(acc.report(), analyze(log))

    def test_rejects_out_of_order_samples(self):
        acc = AutonomyAccumulator()
        samples = list(parse_log("10 50 autonomous\n5 49 autonomous"))
        acc.add(samples[0])
        with self.assertRaisesRegex(ValueError, "out-of-order"):
            acc.add(samples[1])


class CliTest(unittest.TestCase):
    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_reports_metrics(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d, "log.txt")
            path.write_text("0 100 autonomous\n3600 90 manual\n")
            code, out, _ = self.run_cli(str(path))
        self.assertEqual(code, 0)
        self.assertIn("autonomous time:   3600 units (1.0000 h)", out)
        self.assertIn("avg hourly drain:  10.0000 %/h", out)
        self.assertIn("est. hours/charge: 10.00 h", out)

    def test_bad_input_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d, "log.txt")
            path.write_text("0 100 autonomous\noops\n")
            code, _, err = self.run_cli(str(path))
        self.assertEqual(code, 1)
        self.assertIn("line 2", err)

    def test_missing_file_exits_nonzero(self):
        code, _, err = self.run_cli("/nonexistent/log.txt")
        self.assertEqual(code, 1)
        self.assertIn("error:", err)


if __name__ == "__main__":
    unittest.main()
