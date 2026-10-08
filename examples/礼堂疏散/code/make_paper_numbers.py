#!/usr/bin/env python3
"""Derive publishable statistics from saved per-seed simulations, never rounded means."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path
from scipy.stats import t

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DEFAULT_OUT = ROOT / "examples/evacuation-en/results/paper_numbers.json"


def summarize(record: dict, seeds: list[int]) -> dict:
    values = record.get("T_seeds")
    if record.get("completed_all") is not True:
        raise ValueError("Incomplete runs must be reported separately, not as clearance times")
    if not isinstance(values, list) or len(values) != len(seeds) or len(values) < 2:
        raise ValueError("Every seed must have a raw clearance time; at least two are required")
    if any(isinstance(v, bool) or not isinstance(v, (int, float))
           or not math.isfinite(v) or v <= 0 for v in values):
        raise ValueError("Clearance times must be finite positive numbers")
    mean, sd = statistics.mean(values), statistics.stdev(values)
    half = float(t.ppf(.975, len(values) - 1)) * sd / math.sqrt(len(values))
    return {"T": mean, "T_std": sd, "T_ci95": [mean - half, mean + half],
            "T_seeds": values, "n": len(values), "unit": "s", "completed_all": True}


def build() -> dict:
    sources = {"methods": HERE / "evac_methods_fixed.json", "sweeps": HERE / "results/sweeps.json"}
    methods, sweeps = (json.loads(sources[k].read_text(encoding="utf-8")) for k in ("methods", "sweeps"))
    meta = methods["meta"]
    seeds = meta["seed_list"]
    if (not isinstance(seeds, list) or len(seeds) < 2 or len(set(seeds)) != len(seeds)
            or any(type(s) is not int for s in seeds) or meta["seeds"] != len(seeds)):
        raise ValueError("Invalid independent seed identifiers")
    if any(meta[k] != sweeps["meta"][k] for k in ("n", "mu")) or seeds != sweeps["meta"]["seeds"]:
        raise ValueError("Main comparison and sweep configurations differ")
    reference = meta["n"] / sum(meta["mu"])
    m = methods["methods"]
    for key in ("shortest_queue_once", "static_cong_once"):
        if m[key]["T_seeds"] != m["nearest_once"]["T_seeds"]:
            raise ValueError("Static baseline equivalence no longer holds")
    main = {}
    for target, original in (("random_once", "random_once"), ("static_rules_once", "nearest_once"),
                             ("static_rules_on_arrival", "shortest_queue_arrival"), ("dynamic_cong", "dynamic_cong")):
        record = m[original]
        main[target] = {**summarize(record, seeds), "gini": record["gini_mean"], "flow": record["flow_mean"],
                        "ratio_ref": statistics.mean(record["T_seeds"]) / reference,
                        "reassign": None if target == "dynamic_cong" else record["reassign_count_mean"]}
    lam = {k: summarize(v, seeds) for k, v in sweeps["lambda_sweep"].items()}
    best = min(lam, key=lambda k: lam[k]["T"])
    near = [float(k) for k in sorted(lam, key=float) if lam[k]["T"] <= lam[best]["T"] * 1.03]
    return {"schema_version": 2,
            "_source": {k: {"path": p.relative_to(ROOT).as_posix(), "hash_normalization": "CRLF to LF",
                             "sha256": hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()}
                        for k, p in sources.items()},
            "statistics": {"independent_unit": "simulation seed", "std_ddof": 1,
                           "interval": "two-sided Student-t 95% CI of the mean",
                           "warning": "Five synthetic runs; post-hoc best is not a proven optimum. No significance test."},
            "setup": {"N": meta["n"], "seeds": seeds, "mu_per_s": meta["mu"], "lambda_main": meta["lam"],
                      "dt_s": sweeps["meta"]["dt"], "T_ref_s": reference,
                      "discrete_capacity_bound_s": reference - sweeps["meta"]["dt"]},
            "main": main,
            "lambda_sweep": {"records": lam, "best_lambda": float(best), "best_T": lam[best]["T"], "observed_within_3pct": near},
            "freq_ablation": {k: summarize(v, seeds) for k, v in sweeps["freq_ablation"].items()},
            "scale_sweep": {k: {p: summarize(v[p], seeds) for p in ("ours", "nearest")}
                            for k, v in sweeps["scale_sweep"].items()},
            "speed_sweep": {k: summarize(v, seeds) for k, v in sweeps["speed_sweep"].items()}}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="Fail if the published derived artifact is stale")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    data = build()
    if args.check:
        if not args.out.exists() or not equivalent(json.loads(args.out.read_text(encoding="utf-8")), data):
            ap.exit(1, f"Stale or missing artifact: {args.out}\n")
        print("Raw-seed statistics and source hashes match the published artifact")
    else:
        protected = {HERE / "evac_methods_fixed.json", HERE / "results/sweeps.json", Path(__file__)}
        if args.out.resolve() in {p.resolve() for p in protected}:
            ap.error("Output cannot overwrite an input or generator")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(args.out)
    return 0


def equivalent(saved, current):
    """Strict structure/provenance; tolerate only numerical library round-off."""
    if isinstance(current, dict):
        return isinstance(saved, dict) and saved.keys() == current.keys() and all(equivalent(saved[k], v) for k, v in current.items())
    if isinstance(current, list):
        return isinstance(saved, list) and len(saved) == len(current) and all(equivalent(a, b) for a, b in zip(saved, current))
    if isinstance(current, float):
        return type(saved) in (int, float) and math.isclose(saved, current, rel_tol=1e-12, abs_tol=1e-10)
    return type(saved) is type(current) and saved == current


if __name__ == "__main__":
    raise SystemExit(main())
