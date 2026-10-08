"""Run internally verified dispatch fixtures and shared-input synthetic replications."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import platform
import random
from pathlib import Path

from model import Job, audit, capacity_lower_bound, simulate


def fixture_checks():
    durations = [2.0, 1.0]
    jobs = [Job(i, 0.0) for i in range(6)]
    baseline = simulate(jobs, durations, "first")
    balanced = simulate(jobs, durations, "earliest_finish")
    bound = capacity_lower_bound(6, durations)
    if baseline["makespan"] != 12 or balanced["makespan"] != 4 or bound != 4:
        raise ValueError("hand-calculated six-job fixture failed")
    if simulate([], durations)["makespan"] != 0:
        raise ValueError("empty-system fixture failed")
    if simulate([Job(0, 3)], durations, "earliest_finish")["makespan"] != 4:
        raise ValueError("single-job fixture failed")
    corrupted = copy.deepcopy(baseline["trace"])
    corrupted[1].update(start=0.0, finish=2.0, wait=0.0)
    try:
        audit(jobs, durations, corrupted)
    except ValueError as error:
        if "capacity" not in str(error):
            raise
    else:
        raise ValueError("negative control did not detect overlapping service")
    return {"scope": "internal verification only; synthetic assumptions, no external validation",
            "empty_system": "passed", "single_job": "passed", "six_job_hand_reference": "passed",
            "capacity_bound": {"lower_bound": bound, "greedy_makespan": balanced["makespan"],
                               "attained_in_this_fixture_only": True},
            "corrupted_trace_capacity_violation": "correctly_rejected"}


def generate_jobs(seed, n_jobs=60):
    rng = random.Random(seed)
    time = 0.0
    jobs = []
    for i in range(n_jobs):
        time += rng.expovariate(0.8)
        jobs.append(Job(i, time))
    return jobs


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(2026, 2031)))
    args = parser.parse_args()
    if len(args.seeds) != len(set(args.seeds)):
        parser.error("seed ids must be unique")
    verification = fixture_checks()
    args.outdir.mkdir(parents=True, exist_ok=True)
    durations = [2.0, 1.0]
    records, manifests = [], []
    for seed in args.seeds:
        jobs = generate_jobs(seed)
        events = {"seed": seed, "service_times_s": durations,
                  "jobs": [{"id": job.id, "arrival_s": job.arrival} for job in jobs]}
        encoded = json.dumps(events, sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
        write_json(args.outdir / f"events-{seed}.json", events)
        manifests.append({"seed": seed, "event_table": f"events-{seed}.json",
                          "canonical_event_sha256": digest})
        for method in ("first", "earliest_finish"):
            result = simulate(jobs, durations, method)
            write_json(args.outdir / f"trace-{method}-{seed}.json", result)
            for metric in ("makespan", "mean_wait"):
                records.append(dict(method=method, scenario="synthetic_dispatch", metric=metric,
                                    seed=seed, value=result[metric], status="ok", unit="s", direction="min",
                                    shared_event_sha256=digest))
    write_json(args.outdir / "runs.json", {"records": records})
    verification.update({"generation": "60 task agents; interarrival Exp(rate=0.8/s); fixed service 2s/1s",
                         "parameter_source": "synthetic assumptions, not measurements",
                         "python": platform.python_version(), "shared_events": manifests,
                         "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                           for p in (Path(__file__), Path(__file__).with_name("model.py"))}})
    write_json(args.outdir / "verification.json", verification)
    print(f"Internal fixtures verified; wrote {len(records)} KPI records -> {args.outdir}")


if __name__ == "__main__":
    main()
