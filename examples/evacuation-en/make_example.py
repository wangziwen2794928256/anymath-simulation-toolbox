#!/usr/bin/env python3
"""Regenerate the flagship figures, table and LaTeX numbers from tracked raw seeds."""
from __future__ import annotations
import csv
import importlib.util
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "skills/csf-figure-forge/scripts"))
import csf_fig
import csf_archetypes as A

spec = importlib.util.spec_from_file_location("paper_numbers", ROOT / "examples/礼堂疏散/code/make_paper_numbers.py")
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)
BLUE, GREY, GOLD, INK = "#2563A6", "#7C8796", "#C27D27", "#24364B"


def export(fig, folder, name, takeaway):
    A._export(fig, str(HERE / folder), name, lang="en", reproducible=True,
              narrative_role="worked simulation example", takeaway=takeaway)
    plt.close(fig)


def method_figure(data):
    fig = plt.figure(figsize=(7.2, 4.5), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1]); ax.set(xlim=(0, 10.3), ylim=(0, 4.9)); ax.axis("off")
    ax.text(.35, 4.5, "A congestion-aware exit-choice simulation", fontsize=14, weight="bold", color=INK)
    ax.text(.35, 4.12, "Implemented rules, service timing, and traceable evidence", fontsize=9, color=GREY)
    def box(x, y, w, h, title, body, color=BLUE):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12,rounding_size=0.08",
                                   facecolor="#F3F6FA", edgecolor=color, linewidth=1.2))
        ax.text(x+.14, y+h-.29, title, fontsize=10, weight="bold", color=color)
        ax.text(x+.14, y+h-.60, body, fontsize=8.5, linespacing=1.5, va="top", color=INK)
    box(.45, 1.8, 2.65, 1.82, "1  Synthetic scene", "400 agents; 24 x 16 m hall\nThree starting clusters\nEvery agent: 1.34 m/s\nExit widths (m):\n1.6 / 1.2 / 0.8")
    box(3.85, 1.8, 2.65, 1.82, "2  Exit choice", "Observe distance and queues\nMinimize distance\n  + weight x queue\nStatic: choose at t = 0\nDynamic: choose each step")
    box(7.25, 1.8, 2.55, 1.82, "3  Service + motion", "Step: 0.1 s; service first\nMove toward chosen exit\nJoin within 0.5 m\nFIFO exit queues\nFractional service quotas")
    for left in (3.18, 6.58):
        ax.add_patch(FancyArrowPatch((left, 2.75), (left+.54, 2.75), arrowstyle="-|>", mutation_scale=17, color=BLUE, linewidth=1.7))
    ax.add_patch(FancyBboxPatch((.45, .45), 9.35, .84, boxstyle="round,pad=0.12,rounding_size=0.08",
                               facecolor="#EDF3F9", edgecolor="none"))
    ax.text(.65, 1.0, "4  Evidence pipeline", fontsize=10, weight="bold", color=BLUE)
    ax.text(.65, .68, "5 seeds  >  raw times + hashes  >  sample SD / 95% CI  >  figures, table, paper", fontsize=9, color=INK)
    ax.text(.45, .08, "Synthetic model; no collisions, learned policy, or real-world calibration.", fontsize=8.5, color=GREY)
    export(fig, "figures", "fig1_method", "The diagram describes the implemented simulator, not an untrained MARL template.")


def error(record):
    return np.array([record["T"] - record["T_ci95"][0], record["T_ci95"][1] - record["T"]])


def observations(ax, x, records, color):
    for xx, record in zip(x, records):
        ax.scatter(xx + np.linspace(-.065, .065, record["n"]), record["T_seeds"],
                   s=13, color=color, alpha=.5, zorder=4, edgecolors="none")


def result_figure(data):
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.6))
    fig.subplots_adjust(left=.08, right=.97, bottom=.13, top=.86, hspace=.48, wspace=.27)
    fig.text(.08, .965, "Decision timing changes clearance time", fontsize=15, color=INK, weight="bold")
    fig.text(.08, .918, "5 synthetic runs  |  dots: raw seeds  |  intervals: mean 95% CI", fontsize=9, color=GREY)
    ref = data["setup"]["T_ref_s"]
    for i, ax in enumerate(axes.flat):
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#E2E8EF", linewidth=.7); ax.set_axisbelow(True)
        ax.set_ylabel("Clearance time (s)")
        ax.text(-.14, 1.08, "abcd"[i], transform=ax.transAxes, fontsize=13, weight="bold", color=BLUE)
        ax.tick_params(labelsize=9)
    ax = axes[0, 0]
    lam = data["lambda_sweep"]["records"]; keys = sorted(lam, key=float)
    x = np.arange(len(keys)); records = [lam[k] for k in keys]
    ax.errorbar(x, [r["T"] for r in records], yerr=np.column_stack([error(r) for r in records]),
                fmt="o-", color=BLUE, capsize=3, lw=1.6, ms=4, label="Dynamic rule")
    observations(ax, x, records, BLUE)
    ax.axhline(ref, color=GOLD, ls="--", lw=1.2, label="Continuous capacity reference")
    ax.set(xticks=x, xticklabels=[f"{float(k):g}" for k in keys], xlabel=r"Congestion weight $\lambda$ (m/person)", ylim=(110, 465))
    near = " and ".join(f"{v:g}" for v in data["lambda_sweep"]["observed_within_3pct"])
    ax.set_title(f"Sampled weights within 3%: {near}", loc="left", fontsize=9, pad=14)
    ax.legend(fontsize=7.5, loc="upper right", frameon=False)
    ax = axes[0, 1]
    records = list(data["freq_ablation"].values()); x = np.arange(len(records))
    ax.bar(x, [r["T"] for r in records], color=[GREY, "#A9BDD3", "#7BA2CA", "#4B82B8", BLUE], width=.64,
           yerr=np.column_stack([error(r) for r in records]), capsize=3, error_kw={"elinewidth":1.2})
    observations(ax, x, records, INK)
    ax.set(xticks=x, xticklabels=["0", "25", "50", "75", "100"], xlabel="Agents using the dynamic rule (%)", ylim=(0, 470))
    ax.set_title("Share using dynamic decisions", loc="left", fontsize=9, pad=14)
    ax = axes[1, 0]
    scale = data["scale_sweep"]; ns = sorted(scale, key=int)
    for policy, label, color, marker in (("nearest", "Nearest once", GREY, "s"), ("ours", "Dynamic rule", BLUE, "o")):
        records = [scale[k][policy] for k in ns]
        ax.errorbar([int(k) for k in ns], [r["T"] for r in records], yerr=np.column_stack([error(r) for r in records]),
                    color=color, marker=marker, capsize=3, lw=1.6, ms=4, label=label)
        for n, r in zip(ns, records):
            ax.scatter(int(n)+np.linspace(-3, 3, r["n"]), r["T_seeds"], s=13, color=color, alpha=.5)
    ax.set(xlabel="Number of agents", xticks=[int(k) for k in ns], ylim=(40, 590))
    ax.set_title("Population-size comparison", loc="left", fontsize=9, pad=14)
    ax.legend(fontsize=9, frameon=False, loc="upper left")
    ax = axes[1, 1]
    records = [data["main"][k] for k in ("random_once", "static_rules_once", "dynamic_cong")]; x=np.arange(3)
    ax.bar(x, [r["T"] for r in records], color=["#A9B3BF", GREY, BLUE], width=.58,
           yerr=np.column_stack([error(r) for r in records]), capsize=4, error_kw={"elinewidth":1.2})
    observations(ax, x, records, INK)
    ax.axhline(ref, color=GOLD, ls="--", lw=1.2)
    ax.set(xticks=x, xticklabels=["Random\nonce", "Nearest\nonce*", "Dynamic\nrule"], xlabel="Policy", ylim=(0, 470))
    ratio = data["main"]["dynamic_cong"]["ratio_ref"]
    ax.set_title(f"Dynamic mean / reference = {ratio:.2f}", loc="left", fontsize=9, pad=14)
    fig.text(.08, .042, "* Empty initial queues make the three static initialization rules equivalent.", fontsize=8, color=GREY)
    fig.text(.08, .016, "Reference ignores travel and discrete timing; no global optimum is established.", fontsize=8, color=GREY)
    export(fig, "figures", "fig2_main", "Raw seed points and mean confidence intervals support descriptive comparisons of implemented rules.")


def table_and_numbers(data):
    folder = HERE / "tables"; folder.mkdir(exist_ok=True)
    keys = ("random_once", "static_rules_once", "static_rules_on_arrival", "dynamic_cong")
    labels = ("Random once", "Nearest once (3 equivalent rules)", "Shortest queue on arrival", "Dynamic distance + queue")
    rows = [[label, f"{data['main'][key]['T']:.2f}", f"{data['main'][key]['T_std']:.2f}",
             f"{data['main'][key]['T_ci95'][0]:.2f} to {data['main'][key]['T_ci95'][1]:.2f}",
             f"{data['main'][key]['ratio_ref']:.2f}"] for key, label in zip(keys, labels)]
    headers = ["Policy", "Mean (s)", "Sample SD (s)", "95% CI of mean (s)", "Mean / ref."]
    with (folder / "tab_main.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n"); writer.writerow(headers); writer.writerows(rows)
    tex = "\\begin{tabular}{lrrrr}\n\\toprule\n" + " & ".join(h.replace("%", r"\%") for h in headers) + " \\\\\n\\midrule\n"
    tex += "".join(" & ".join(row) + " \\\\\n" for row in rows) + "\\bottomrule\n\\end{tabular}\n"
    (folder / "tab_main.tex").write_text(tex, encoding="utf-8", newline="\n")
    fig, ax = plt.subplots(figsize=(10.6, 2.25)); ax.axis("off")
    ax.set_title("Main comparison: five complete synthetic runs per policy", loc="left", weight="bold", fontsize=13, color=INK, pad=16)
    tab = ax.table(cellText=rows, colLabels=headers, loc="center", cellLoc="center", colWidths=[.35,.12,.15,.24,.14])
    tab.auto_set_font_size(False); tab.set_fontsize(9); tab.scale(1, 1.9)
    for (r,c), cell in tab.get_celld().items():
        cell.set_edgecolor("white"); cell.set_facecolor("#EDF3F9" if r == 0 or r == 4 else "#F7F9FC")
        if r == 0: cell.set_text_props(weight="bold", color=INK)
        if c == 0: cell.set_text_props(ha="left")
    export(fig, "tables", "tab_main", "Statistics are recomputed from raw seeds; intervals quantify uncertainty in the mean.")
    near = data["lambda_sweep"]["observed_within_3pct"]
    macro = {"StaticMean": data["main"]["static_rules_once"]["T"], "StaticSD": data["main"]["static_rules_once"]["T_std"],
             "DynamicMean": data["main"]["dynamic_cong"]["T"], "DynamicSD": data["main"]["dynamic_cong"]["T_std"],
             "CapacityRef": data["setup"]["T_ref_s"], "DynamicRatio": data["main"]["dynamic_cong"]["ratio_ref"]}
    text = "% Generated from tracked raw results; do not hand-edit.\n"
    text += "".join(f"\\newcommand{{\\{k}}}{{{v:.2f}}}\n" for k,v in macro.items())
    text += "\\newcommand{\\NearWeights}{" + ", ".join(f"{v:g}" for v in near) + "}\n"
    (HERE / "results/numbers.tex").write_text(text, encoding="utf-8", newline="\n")


def main():
    data = source.build()
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results/paper_numbers.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    contracts = [
        {"figure_id": "fig1_method", "conclusion": "The diagram documents implemented rules and timing.",
         "role_in_paper": "model", "evidence_level": "method",
         "panels": [{"id": "pipeline", "role": "method", "source": "examples/礼堂疏散/code/eval_methods_fixed.py",
                     "units": "m, s, persons", "claim": "Rule-based simulation followed by raw-seed evidence."}],
         "integrity_risks": ["No learned policy or empirical calibration; diagram is not an execution trace."]},
        {"figure_id": "fig2_main", "conclusion": "The saved synthetic runs support descriptive policy comparisons.",
         "role_in_paper": "main comparison and sensitivity", "evidence_level": "main",
         "panels": [{"id": key, "role": role, "source": f"paper_numbers.json:{record}",
                     "units": "clearance time (s)", "claim": claim}
                    for key, role, record, claim in (("a", "sensitivity", "lambda_sweep", "Sampled near-minimum weights form a discrete set."),
                                                    ("b", "ablation", "freq_ablation", "Dynamic-share comparison with mean intervals."),
                                                    ("c", "scaling", "scale_sweep", "Policy comparisons at four sizes."),
                                                    ("d", "main", "main", "Mean divided by continuous capacity reference."))],
         "integrity_risks": ["95% mean intervals are not SD or significance tests.", "Weight settings are equally spaced as discrete categories.",
                             "Five synthetic seeds; capacity reference is not an attainable optimum."]}]
    for contract in contracts:
        issues = csf_fig.figure_contract_check(contract)
        if issues:
            raise ValueError(issues)
    (HERE / "results/figure_contracts.json").write_text(json.dumps(contracts, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    csf_fig.use_style("nature", cjk=False, lang="en", font_size=9)
    method_figure(data); result_figure(data); table_and_numbers(data)
    print("Figures, table and LaTeX numeric macros regenerated from raw seed records")


if __name__ == "__main__":
    main()
