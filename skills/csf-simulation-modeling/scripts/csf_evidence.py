"""Aggregate independent simulation repetitions; preserve failures and paired differences."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import re
import statistics
from collections import defaultdict
from pathlib import Path


def validate(records):
    if not isinstance(records, list) or not records:
        raise ValueError("records must be a nonempty list")
    seen, definitions = set(), {}
    for i, r in enumerate(records):
        if not isinstance(r, dict):
            raise ValueError(f"record {i}: expected object")
        for field in ("method", "scenario", "metric", "unit"):
            if not isinstance(r.get(field), str) or not r[field].strip():
                raise ValueError(f"record {i}: missing/non-string {field}")
        if type(r.get("seed")) is not int:
            raise ValueError(f"record {i}: seed must be an integer replicate id")
        if r.get("direction") not in ("min", "max"):
            raise ValueError(f"record {i}: direction must be min or max")
        if r.get("status") not in ("ok", "failed", "truncated"):
            raise ValueError(f"record {i}: invalid status")
        if "shared_event_sha256" in r and (not isinstance(r["shared_event_sha256"], str) or
                                            re.fullmatch(r"[0-9a-f]{64}", r["shared_event_sha256"]) is None):
            raise ValueError(f"record {i}: shared_event_sha256 must be a lowercase SHA256 hex digest")
        if "value" not in r:
            raise ValueError(f"record {i}: missing value")
        value = r["value"]
        if r["status"] == "ok":
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError(f"record {i}: ok value must be a finite number")
        elif value is not None:
            raise ValueError(f"record {i}: failed/truncated value must be null")
        key = tuple(r[k] for k in ("method", "scenario", "metric", "seed"))
        if key in seen:
            raise ValueError(f"duplicate replicate: {key}")
        seen.add(key)
        definition = (r["unit"], r["direction"])
        if r["metric"] in definitions and definitions[r["metric"]] != definition:
            raise ValueError(f"inconsistent unit/direction for {r['metric']}")
        definitions[r["metric"]] = definition
    return records


def estimate(values):
    n = len(values)
    mean = statistics.mean(values) if n else None
    std = statistics.stdev(values) if n > 1 else None
    se = std / math.sqrt(n) if std is not None else None
    ci = None
    if se is not None:
        from scipy.stats import t
        half = float(t.ppf(0.975, n - 1)) * se
        ci = [mean - half, mean + half]
    return {"n": n, "mean": mean, "std": std, "se": se, "ci95": ci,
            "values": values, "interval_method": "Student-t mean CI; independent repetitions"}


def summarize(records, compare=None, require_shared_events=False):
    validate(records)
    if require_shared_events and not compare:
        raise ValueError("require_shared_events needs a comparison")
    groups = defaultdict(list)
    for r in records:
        groups[(r["method"], r["scenario"], r["metric"])].append(r)
    output = {"schema_version": 1, "groups": [], "comparisons": []}
    for (method, scenario, metric), rows in sorted(groups.items()):
        rows = sorted(rows, key=lambda r: r["seed"])
        good = [r for r in rows if r["status"] == "ok"]
        output["groups"].append({
            "method": method, "scenario": scenario, "metric": metric,
            "unit": rows[0]["unit"], "direction": rows[0]["direction"],
            "n_total": len(rows), "n_failed": sum(r["status"] == "failed" for r in rows),
            "n_truncated": sum(r["status"] == "truncated" for r in rows),
            "successful_seeds": [r["seed"] for r in good],
            "unsuccessful_runs": [r for r in rows if r["status"] != "ok"],
            "estimand": "mean conditional on successful runs",
            **estimate([r["value"] for r in good])})
    if compare:
        a, b = compare
        if a == b:
            raise ValueError("comparison needs two different methods")
        keys_a = {(s, m) for method, s, m in groups if method == a}
        keys_b = {(s, m) for method, s, m in groups if method == b}
        if not keys_a or keys_a != keys_b:
            raise ValueError("comparison methods must cover identical scenario/metric sets")
        for scenario, metric in sorted(keys_a):
            left = {r["seed"]: r for r in groups[(a, scenario, metric)]}
            right = {r["seed"]: r for r in groups[(b, scenario, metric)]}
            if left.keys() != right.keys():
                raise ValueError(f"unmatched replicate ids: {scenario}/{metric}")
            matched_event_seeds = []
            for seed in sorted(left):
                a_hash, b_hash = left[seed].get("shared_event_sha256"), right[seed].get("shared_event_sha256")
                if a_hash is not None or b_hash is not None or require_shared_events:
                    if not a_hash or a_hash != b_hash:
                        raise ValueError(f"missing/mismatched shared event hashes: {scenario}/{metric}/{seed}")
                    matched_event_seeds.append(seed)
            included = [s for s in sorted(left) if left[s]["status"] == right[s]["status"] == "ok"]
            sample = next(iter(left.values()))
            output["comparisons"].append({
                "difference": f"{a} - {b}", "scenario": scenario, "metric": metric,
                "unit": sample["unit"], "direction": sample["direction"],
                "paired_seeds": included, "excluded_seeds": sorted(set(left) - set(included)),
                "matched_event_hash_seeds": matched_event_seeds,
                "event_hash_caveat": "hash declarations checked, not underlying event files or policy use",
                "pairing_requirement": "shared exogenous scenario/events; ids alone do not establish pairing",
                "estimand": "paired mean difference conditional on both methods succeeding",
                **estimate([left[s]["value"] - right[s]["value"] for s in included])})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compare", nargs=2, metavar=("METHOD_A", "METHOD_B"))
    parser.add_argument("--require-shared-events", action="store_true",
                        help="require matching declared external-event hashes for every pair")
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("output must not overwrite raw input")
        raw = args.input.read_bytes()
        payload = json.loads(raw.decode("utf-8-sig"))
        result = summarize(payload.get("records") if isinstance(payload, dict) else payload,
                           args.compare, args.require_shared_events)
        import scipy
        result["provenance"] = {"source": str(args.input.resolve()),
                                "sha256": hashlib.sha256(raw).hexdigest(),
                                "python": platform.python_version(), "scipy": scipy.__version__}
        text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    except (ValueError, OSError, ImportError) as error:
        parser.exit(2, f"ERROR: {error}\n")
    print(f"Saved {len(result['groups'])} groups and {len(result['comparisons'])} comparisons -> {args.output}")


if __name__ == "__main__":
    main()
