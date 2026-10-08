"""Catch scientific publication regressions and malformed LLM-generated inputs."""
import copy
import hashlib
import importlib.util
import json
import statistics
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/csf-figure-forge/scripts"))
sys.path.insert(0, str(ROOT / "skills/csf-simulation-modeling/scripts"))
import csf_fig
import csf_applicability


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


numbers = module("flagship_numbers", "examples/礼堂疏散/code/make_paper_numbers.py")
build = module("paper_build", "skills/csf-paper-polish/scripts/csf_build.py")


class PublicationTests(unittest.TestCase):
    def test_roundoff_tolerance_does_not_hide_changed_results_or_hashes(self):
        self.assertTrue(numbers.equivalent({"T": 1.0}, {"T": 1.0+1e-12}))
        self.assertFalse(numbers.equivalent({"T": 1.1}, {"T": 1.0}))
        self.assertFalse(numbers.equivalent({"sha256": "abc"}, {"sha256": "abd"}))
    def test_raw_statistics_not_rounded_summary_and_no_continuous_plateau(self):
        data = numbers.build()
        self.assertAlmostEqual(data["main"]["static_rules_once"]["T"], 426.66)
        raw = data["main"]["static_rules_once"]["T_seeds"]
        self.assertEqual(data["main"]["static_rules_once"]["T_std"], statistics.stdev(raw))
        self.assertEqual(data["lambda_sweep"]["observed_within_3pct"], [3., 8.])
        self.assertNotIn("plateau_range", data["lambda_sweep"])
        self.assertGreater(data["lambda_sweep"]["records"]["5.0"]["T"], 1.03*data["lambda_sweep"]["best_T"])

    def test_saved_provenance_and_all_sweeps_keep_intervals(self):
        data = numbers.build()
        for source in data["_source"].values():
            content = (ROOT / source["path"]).read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(source["sha256"], hashlib.sha256(content).hexdigest())
        for pair in data["scale_sweep"].values():
            for record in pair.values():
                self.assertLess(record["T_ci95"][0], record["T"])
                self.assertGreater(record["T_ci95"][1], record["T"])
        self.assertIsNone(data["main"]["dynamic_cong"]["reassign"])

    def test_incomplete_missing_nonfinite_and_boolean_runs_rejected(self):
        good = {"T_seeds": [1., 2.], "completed_all": True}
        for change in ({"completed_all": False}, {"T_seeds": [1.]},
                       {"T_seeds": [1., float("nan")]}, {"T_seeds": [True, 2.]}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                numbers.summarize({**good, **change}, [1, 2])

    def test_stale_artifact_is_a_failing_check(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "numbers.json"
            out.write_text("{}", encoding="utf-8")
            result = subprocess.run([sys.executable, str(Path(numbers.__file__)), "--check", "--out", str(out)],
                                    capture_output=True)
            self.assertNotEqual(result.returncode, 0)

    def test_malformed_contract_fields_report_instead_of_crashing(self):
        contract = {"conclusion": "claim", "role_in_paper": "diagnostic", "evidence_level": [],
                    "panels": [{"id": "a", "role": {}, "source": "raw", "units": "s", "claim": "test"},
                               {"id": "a", "role": "check", "source": "raw", "units": "s", "claim": "test"}],
                    "integrity_risks": ["synthetic"]}
        self.assertTrue(csf_fig.figure_contract_check(contract, []))
        issues = csf_fig.figure_contract_check(contract)
        self.assertTrue(any("重复" in message for message in issues))

    def test_malformed_assumption_rules_fail_cleanly(self):
        self.assertTrue(csf_applicability.check_rules([], ["DES"]))
        rules = copy.deepcopy(csf_applicability.load_rules())
        rules["methods"]["DES"]["requires"] = "events"
        self.assertTrue(csf_applicability.check_rules(rules, rules["methods"]))

    def build_mock(self, aux, existing_bbl):
        with tempfile.TemporaryDirectory() as td:
            tex = Path(td) / "paper.tex"; tex.write_text("example")
            tex.with_suffix(".aux").write_text(aux)
            tex.with_suffix(".log").write_text("Output written on paper.pdf (1 page, 123 bytes).")
            if existing_bbl: tex.with_suffix(".bbl").write_text("stale bibliography")
            with patch.object(build, "find_tool", side_effect=lambda name: name), patch.object(build, "run", return_value=(0,"ok")) as runner:
                build.build(tex, "lualatex", 2, True)
                return [call.args[0][0] for call in runner.call_args_list]

    def test_unused_bibliography_does_not_invoke_bibtex(self):
        self.assertNotIn("bibtex", self.build_mock(r"\relax", False))

    def test_existing_bibliography_is_refreshed_after_changes(self):
        self.assertIn("bibtex", self.build_mock(r"\bibdata{refs}", True))


if __name__ == "__main__":
    unittest.main()
