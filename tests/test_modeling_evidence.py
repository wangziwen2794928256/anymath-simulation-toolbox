"""Behavioral regressions for evidence integrity and figure contract routing."""
import ast
import importlib.util
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/csf-simulation-modeling/scripts"))
from csf_evidence import summarize


def row(method="rule", seed=1, value=10, status="ok"):
    return dict(method=method, seed=seed, value=value, status=status,
                scenario="small", metric="time", unit="s", direction="min")


class EvidenceTests(unittest.TestCase):
    def test_sample_std_and_student_t_interval(self):
        g = summarize([row(seed=i, value=v) for i, v in enumerate([1, 2, 3])])["groups"][0]
        self.assertEqual(g["mean"], 2)
        self.assertEqual(g["std"], 1)
        self.assertAlmostEqual(g["se"], 1 / math.sqrt(3))
        self.assertAlmostEqual(g["ci95"][1], 4.4841377117)

    def test_one_run_is_not_zero_uncertainty(self):
        g = summarize([row()])["groups"][0]
        self.assertIsNone(g["std"])
        self.assertIsNone(g["ci95"])

    def test_failure_is_retained_not_imputed(self):
        g = summarize([row(), row(seed=2, value=None, status="failed")])["groups"][0]
        self.assertEqual((g["n_total"], g["n"], g["n_failed"], g["mean"]), (2, 1, 1, 10))
        self.assertEqual(g["unsuccessful_runs"][0]["seed"], 2)

    def test_all_failures_have_no_mean(self):
        self.assertIsNone(summarize([row(value=None, status="truncated")])["groups"][0]["mean"])

    def test_duplicate_nan_boolean_and_mixed_unit_rejected(self):
        changed = row(seed=2)
        changed["unit"] = "min"
        for records in ([row(), row()], [row(value=float("nan"))], [row(value=True)],
                        [row(), changed], [row(status="failed")]):
            with self.subTest(records=records), self.assertRaises(ValueError):
                summarize(records)

    def test_pair_by_seed_not_input_order(self):
        records = [row("ours", 2, 20), row("rule", 1, 13), row("ours", 1, 10), row("rule", 2, 24)]
        c = summarize(records, ("ours", "rule"))["comparisons"][0]
        self.assertEqual(c["values"], [-3, -4])
        self.assertEqual(c["paired_seeds"], [1, 2])

    def test_unmatched_pairs_fail(self):
        with self.assertRaises(ValueError):
            summarize([row("ours", 1), row("rule", 2)], ("ours", "rule"))

    def test_failed_pair_exclusion_is_explicit(self):
        c = summarize([row("ours", 1), row("rule", 1), row("ours", 2, None, "failed"),
                       row("rule", 2)], ("ours", "rule"))["comparisons"][0]
        self.assertEqual(c["excluded_seeds"], [2])
        self.assertEqual(c["n"], 1)

    def test_shared_event_hashes_match_or_fail(self):
        records = [row("ours"), row("rule")]
        for r in records: r["shared_event_sha256"] = "a" * 64
        result = summarize(records, ("ours", "rule"), require_shared_events=True)
        self.assertEqual(result["comparisons"][0]["matched_event_hash_seeds"], [1])
        records[1]["shared_event_sha256"] = "b" * 64
        with self.assertRaises(ValueError):
            summarize(records, ("ours", "rule"))

    def test_missing_and_invalid_event_hashes_rejected_when_required(self):
        with self.assertRaises(ValueError):
            summarize([row("ours"), row("rule")], ("ours", "rule"), require_shared_events=True)
        bad = row(); bad["shared_event_sha256"] = "not-a-hash"
        with self.assertRaises(ValueError):
            summarize([bad])


class FigureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "skills/csf-figure-forge/scripts"))
        import csf_fig
        cls.check = staticmethod(csf_fig.figure_contract_check)

    def test_validation_does_not_need_hero(self):
        contract = dict(conclusion="model check", role_in_paper="validation", evidence_level="validation",
                        integrity_risks=["synthetic data"], panels=[dict(id="a", role="validation",
                        source="runs.json#/records", units="s", claim="matches analytical result")])
        self.assertEqual(self.check(contract), [])
        contract["evidence_level"] = "hero"
        self.assertTrue(any("hero/main" in p for p in self.check(contract)))

    def test_three_formats_and_malformed_panels(self):
        contract = dict(conclusion="x", role_in_paper="x", evidence_level="validation",
                        integrity_risks=["x"], panels=[dict(role="validation", source="x", units="s", claim="x")])
        self.assertTrue(any("svg" in p for p in self.check(contract, {"pdf": "x", "png": "x"})))
        contract["panels"] = [None]
        self.assertTrue(self.check(contract))


class EnvironmentTemplateTests(unittest.TestCase):
    def test_unimplemented_environment_fails_instead_of_fabricating_rollout(self):
        path = ROOT / "skills/csf-simulation-modeling/assets/code-template/gym_env.py"
        spec = importlib.util.spec_from_file_location("test_gym_template", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        from types import SimpleNamespace
        with self.assertRaises(NotImplementedError):
            module.SimulationEnv(SimpleNamespace(seed=2026))
        env = module.SimulationEnv.__new__(module.SimulationEnv)
        with self.assertRaises(NotImplementedError):
            env.step(0)

    def evaluator(self):
        # Test evaluation logic without downloading the unrelated Torch training stack.
        path = ROOT / "skills/csf-simulation-modeling/assets/code-template/train_marl.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "evaluate")
        import numpy as np
        namespace = {"np": np}
        exec(compile(ast.Module(body=[func], type_ignores=[]), str(path), "exec"), namespace)
        return namespace["evaluate"]

    def test_evaluation_uses_held_out_seeds_and_closes_env(self):
        class Env:
            def __init__(self): self.seed = None; self.closed = False
            def reset(self, seed): self.seed = seed; return [0], {}
            def step(self, action): return [0], 2.0, True, False, {}
            def close(self): self.closed = True
        class Model:
            def predict(self, obs, deterministic): return 0, None
        envs = []
        def factory(seed):
            env = Env(); envs.append(env)
            return lambda: env
        mean, std, length = self.evaluator()(Model(), factory, n_episodes=2)
        self.assertEqual((mean, std, length), (2.0, 0.0, 1.0))
        self.assertEqual([e.seed for e in envs], [20000, 20001])
        self.assertTrue(all(e.closed for e in envs))

    def test_evaluation_timeout_fails_and_closes_env(self):
        class Env:
            closed = False
            def reset(self, seed): return [0], {}
            def step(self, action): return [0], 0.0, False, False, {}
            def close(self): self.closed = True
        class Model:
            def predict(self, obs, deterministic): return 0, None
        env = Env()
        with self.assertRaises(RuntimeError):
            self.evaluator()(Model(), lambda seed: lambda: env, n_episodes=1, max_steps=2)
        self.assertTrue(env.closed)


if __name__ == "__main__":
    unittest.main()
