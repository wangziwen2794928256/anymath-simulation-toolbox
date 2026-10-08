"""Finite synthetic dispatch model: task agents select one of single-server stations.

No physical evacuation model, training, or real-world validation is implied.
Intervals are half-open [start, finish); completions precede starts at equal times.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    id: int
    arrival: float


def validate_inputs(jobs, service_times):
    if not service_times or any(type(t) not in (int, float) or not math.isfinite(t) or t <= 0
                                for t in service_times):
        raise ValueError("each station must have a finite positive service duration")
    ids = set()
    for job in jobs:
        if type(job.id) is not int or job.id in ids:
            raise ValueError("job ids must be unique integers")
        if type(job.arrival) not in (int, float) or not math.isfinite(job.arrival) or job.arrival < 0:
            raise ValueError("arrival times must be finite and nonnegative")
        ids.add(job.id)


def choose_station(policy, arrival, next_free, service_times):
    """Only current reservation state and known durations are visible; no future jobs."""
    if policy == "first":
        return 0
    if policy == "earliest_finish":
        return min(range(len(next_free)), key=lambda j: (max(arrival, next_free[j]) + service_times[j], j))
    raise ValueError(f"unknown policy: {policy}")


def simulate(jobs, service_times, policy="first"):
    validate_inputs(jobs, service_times)
    if policy not in {"first", "earliest_finish"}:
        raise ValueError(f"unknown policy: {policy}")
    next_free = [0.0] * len(service_times)
    trace = []
    for job in sorted(jobs, key=lambda job: (job.arrival, job.id)):
        station = choose_station(policy, job.arrival, next_free, service_times)
        start = max(job.arrival, next_free[station])
        finish = start + service_times[station]
        if not math.isfinite(finish):
            raise ValueError("simulation time overflow")
        next_free[station] = finish
        trace.append(dict(job_id=job.id, station=station, arrival=job.arrival,
                          start=start, finish=finish, wait=start - job.arrival))
    audit(jobs, service_times, trace)
    return {"policy": policy, "n_jobs": len(jobs), "trace": trace,
            "makespan": max((event["finish"] for event in trace), default=0.0),
            "mean_wait": sum(event["wait"] for event in trace) / len(trace) if trace else 0.0}


def audit(jobs, service_times, trace, atol=1e-9):
    """Check emitted intervals independently of dispatching and reservation updates."""
    validate_inputs(jobs, service_times)
    if type(atol) not in (int, float) or not math.isfinite(atol) or atol < 0:
        raise ValueError("atol must be finite and nonnegative")
    by_id = {job.id: job for job in jobs}
    seen = set()
    intervals = [[] for _ in service_times]
    for event in trace:
        job_id, station = event["job_id"], event["station"]
        if type(job_id) is not int or job_id not in by_id or job_id in seen:
            raise ValueError("missing/duplicate/unknown job in trace")
        if type(station) is not int or not 0 <= station < len(service_times):
            raise ValueError("invalid station in trace")
        seen.add(job_id)
        arrival, start, finish, wait = (event[k] for k in ("arrival", "start", "finish", "wait"))
        if any(type(t) not in (int, float) or not math.isfinite(t) for t in (arrival, start, finish, wait)):
            raise ValueError("nonfinite or nonnumeric trace")
        if (abs(arrival - by_id[job_id].arrival) > atol or start < arrival - atol or finish <= start
                or wait < -atol or abs(wait - (start - arrival)) > atol
                or abs((finish - start) - service_times[station]) > atol):
            raise ValueError("arrival, duration or waiting-time invariant violated")
        intervals[station].append((start, finish))
    if seen != set(by_id):
        raise ValueError("job conservation violated")
    for station_intervals in intervals:
        previous_finish = -math.inf
        for start, finish in sorted(station_intervals):
            if start < previous_finish - atol:
                raise ValueError("single-server capacity exceeded")
            previous_finish = finish
    return {"job_conservation": True, "capacity": True, "nonnegative_wait": True,
            "service_duration": True, "input_arrivals_preserved": True, "atol": atol}


def capacity_lower_bound(n_jobs, service_times):
    """From t=0, N jobs require at least N/sum(1/d_j) seconds of capacity.

    Ignores release dates and integer packing; it need not be achievable.
    """
    validate_inputs([], service_times)
    if type(n_jobs) is not int or n_jobs < 0:
        raise ValueError("n_jobs must be a nonnegative integer")
    return n_jobs / sum(1 / t for t in service_times)
