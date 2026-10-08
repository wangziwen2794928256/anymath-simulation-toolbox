"""Prerequisite and independent simulation-verification regression cases."""
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/csf-simulation-modeling/scripts"
sys.path.insert(0, str(SCRIPTS))
import csf_applicability as applicability
import csf_select

spec = importlib.util.spec_from_file_location("validated_dispatch_model", ROOT / "examples/validated-dispatch/model.py")
dispatch = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dispatch
spec.loader.exec_module(dispatch)


class ApplicabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.methods = csf_select.load(csf_select.LIB)["methods"]
        cls.rules = applicability.load_rules()

    def context(self, **facts):
        return {"schema_version": 1, "facts": {
            key: {"value": value, "basis": "synthetic test declaration"} for key, value in facts.items()}}

    def one(self, mid, context):
        method = next(m for m in self.methods if m["id"] == mid)
        return applicability.assess([method], context, self.rules)[0]

    def test_rule_coverage_matches_whole_library(self):
        self.assertEqual(applicability.check_rules(self.rules, [m["id"] for m in self.methods]), [])

    def test_missing_facts_stay_pending(self):
        item = self.one("CTDE", self.context())
        self.assertEqual(item["status"], "pending")
        self.assertTrue(all(c["declared_value"] is None for c in item["checks"]))

    def test_no_training_budget_conflicts_even_with_other_unknown_facts(self):
        self.assertEqual(self.one("CTDE", self.context(training_workflow_available=False))["status"], "conflict")

    def test_met_prerequisites_do_not_claim_validated(self):
        item = self.one("CTDE", self.context(training_workflow_available=True,
                                            environment_interface_defined=True, central_training_information=True))
        self.assertEqual(item["status"], "compatible_with_declared_facts")
        self.assertTrue(item["manual_checks"])

    def test_deterministic_sensitivity_is_not_rejected(self):
        self.assertEqual(self.one("SENSITIVITY", self.context(parameters_to_vary=True,
                                                             stochastic_inputs=False))["status"],
                         "compatible_with_declared_facts")

    def test_typo_string_bool_and_unjustified_fact_rejected(self):
        bad = [self.context(training_workflow_availble=True), self.context(training_workflow_available="false"),
               {"schema_version": 1, "facts": {"training_workflow_available": {"value": True}}}]
        for context in bad:
            with self.subTest(context=context), self.assertRaises(ValueError):
                self.one("CTDE", context)

    def test_missing_mechanism_library_cannot_pass_check(self):
        with patch.object(csf_select, "mech_ids", return_value=set()):
            self.assertTrue(any("机理卡库" in problem for problem in csf_select.check(csf_select.load(csf_select.LIB))))

    def test_conflicted_method_is_not_an_action_step(self):
        lib = csf_select.load(csf_select.LIB)
        report = applicability.report(self.methods, self.context(training_workflow_available=False))
        text = csf_select.plan(lib, ["多智能体", "协同"], report)
        self.assertIn("CTDE: 前提冲突", text)
        self.assertNotIn("▸ CTDE", text)

    def test_unknown_prerequisites_are_not_action_steps(self):
        lib = csf_select.load(csf_select.LIB)
        report = applicability.report(self.methods, self.context())
        text = csf_select.plan(lib, ["多智能体", "协同"], report)
        self.assertIn("CTDE: 信息待补", text)
        self.assertNotIn("▸ CTDE", text)

    def test_cli_report_does_not_overwrite_input(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "context.json"
            original = json.dumps(self.context(training_workflow_available=False))
            path.write_text(original, encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPTS / "csf_select.py"), "--context", str(path),
                                     "--report", str(path)], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_scaffold_generates_pending_context_and_quoted_title(self):
        with tempfile.TemporaryDirectory() as td:
            subprocess.run([sys.executable, str(SCRIPTS / "csf_scaffold.py"), "--outdir", td,
                            "--title", 'A "quoted" title'], check=True, capture_output=True)
            ctx = json.loads((Path(td) / "method-context.json").read_text(encoding="utf-8"))
            self.assertEqual(set(ctx["facts"]), set(self.rules["fields"]))
            self.assertTrue(all(v is None for v in ctx["facts"].values()))
            json.loads((Path(td) / "claims.json").read_text(encoding="utf-8"))

    def test_modeling_stage_defers_paper_and_preserves_model_on_upgrade(self):
        with tempfile.TemporaryDirectory() as td:
            command = [sys.executable, str(SCRIPTS / "csf_scaffold.py"), "--outdir", td, "--title", "fixture"]
            subprocess.run(command + ["--stage", "modeling"], check=True, capture_output=True)
            self.assertFalse((Path(td) / "paper").exists())
            self.assertFalse((Path(td) / "claims.json").exists())
            model_path = Path(td) / "core/model.py"
            model_path.write_text("# user implementation\n", encoding="utf-8")
            subprocess.run(command + ["--stage", "paper"], check=True, capture_output=True)
            self.assertEqual(model_path.read_text(encoding="utf-8"), "# user implementation\n")
            self.assertTrue((Path(td) / "paper/paper-en.tex").is_file())


class DispatchTests(unittest.TestCase):
    def test_hand_case_attains_capacity_bound(self):
        jobs = [dispatch.Job(i, 0) for i in range(6)]
        self.assertEqual(dispatch.simulate(jobs, [2, 1], "first")["makespan"], 12)
        self.assertEqual(dispatch.simulate(jobs, [2, 1], "earliest_finish")["makespan"], 4)
        self.assertEqual(dispatch.capacity_lower_bound(6, [2, 1]), 4)

    def test_empty_single_and_equal_time_completion(self):
        self.assertEqual(dispatch.simulate([], [2, 1])["mean_wait"], 0)
        trace = dispatch.simulate([dispatch.Job(0, 0), dispatch.Job(1, 2)], [2])["trace"]
        self.assertEqual([e["wait"] for e in trace], [0, 0])
        self.assertEqual(dispatch.simulate([dispatch.Job(0, 3)], [2, 1], "earliest_finish")["makespan"], 4)

    def test_mutations_are_rejected_independently(self):
        jobs = [dispatch.Job(i, 0) for i in range(3)]
        good = dispatch.simulate(jobs, [2])["trace"]
        bad_capacity = copy.deepcopy(good)
        bad_capacity[1].update(start=0, finish=2, wait=0)
        bad_duration = copy.deepcopy(good); bad_duration[0]["finish"] += 1
        bad_wait = copy.deepcopy(good); bad_wait[1]["wait"] = -1
        bad_arrival = copy.deepcopy(good); bad_arrival[0]["arrival"] = 1
        for trace in (bad_capacity, bad_duration, bad_wait, bad_arrival, good[:-1], good + [good[0]]):
            with self.subTest(trace=trace), self.assertRaises(ValueError):
                dispatch.audit(jobs, [2], trace)

    def test_bad_model_parameters_are_rejected(self):
        for durations in ([], [0], [-1], [float("nan")], [True]):
            with self.subTest(durations=durations), self.assertRaises(ValueError):
                dispatch.simulate([], durations)
        with self.assertRaises(ValueError):
            dispatch.simulate([dispatch.Job(0, 0), dispatch.Job(0, 1)], [1])

    def test_permutation_tie_break_is_reproducible(self):
        jobs = [dispatch.Job(i, 0) for i in range(8)]
        self.assertEqual(dispatch.simulate(jobs, [2, 1], "earliest_finish"),
                         dispatch.simulate(list(reversed(jobs)), [2, 1], "earliest_finish"))

    def test_random_workloads_preserve_capacity_and_lower_bound(self):
        import random
        for seed in range(20):
            rng = random.Random(seed)
            jobs = [dispatch.Job(i, rng.uniform(0, 10)) for i in range(20)]
            durations = [1, 2, 3]
            for policy in ("first", "earliest_finish"):
                result = dispatch.simulate(jobs, durations, policy)
                self.assertTrue(dispatch.audit(jobs, durations, result["trace"])["capacity"])
                self.assertGreaterEqual(result["makespan"], dispatch.capacity_lower_bound(len(jobs), durations))


if __name__ == "__main__":
    unittest.main()
