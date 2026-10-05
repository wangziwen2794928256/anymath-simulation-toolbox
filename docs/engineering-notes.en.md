> These notes are for **maintainers**. They record the empirical evidence behind every design decision,
> including first versions that were overturned by counterexamples.
> Their value: the same pitfall should never be stepped into twice. User-facing documentation is the
> root [README.md](../README.md) / [README.en.md](../README.en.md).
>
> **Cleanup before open-source release (recorded for the record)**: the following was removed prior to
> release; references to it elsewhere in these notes are **historical** — `archive/早期工作站/`;
> `reference/papers/` (including a CUMCM award-winning paper PDF, 1.7 MB); `reference/analysis/`;
> `examples/{2018B-RGV, 2025A-流水车间, comparison-RGV, _scaffold-demo}` (≈2 MB total, all general
> math-modeling material unrelated to this repo's A-track multi-agent simulation theme); `p5.svg`;
> `docs/win-mac差异.md`; and 34 superseded figures in `examples/礼堂疏散/figures/` (only the 3 actually
> cited in the text are kept).
> Rationale: they were **iteration debris**; keeping them would leave readers unable to tell what the
> current state actually looks like.

# Engineering Notes (design decisions · pitfalls · acceptance criteria)

## 1. Goal

Build a dedicated skill for the "2026 2nd National Undergraduate Simulation Modeling Application
Challenge · Track A (multi-agent complex-system simulation)", enabling an AI to produce a
**submission-grade** paper end-to-end (modeling → simulation → figures → LaTeX → PDF). Currently being
further optimized by another agent.

## 2. The three skills and how they are invoked

Installed to `~/.codex/skills/` (identical directories are also archived in this workspace).

| Skill | Responsibility | When to invoke | Typical phrasing |
|---|---|---|---|
| `csf-simulation-modeling` | Contest-specific: **mechanism-card matching**, scientific reasoning chain, modeling & method selection, simulation experiments, figures, paper blueprint, **P0 gates** | On receiving the problem statement: query mechanism cards first → reasoning chain + blueprint → modeling | "Use csf-simulation-modeling to give me the scientific reasoning chain and paper blueprint for this problem" |
| `csf-figure-forge` | **Figure closed loop** (P1): semantic colors, auto-sizing component library, visual QA, vector + 300-dpi triple export | Every figure | "Produce the figure with csf_fig and run visual review" |
| `csf-paper-polish` | Chinese paper polishing, **top-venue narrative shell**, **`csfstyle.sty` layout shell**, LaTeX typesetting, final audit | After modeling results exist, polish into a paper | "Use csf-paper-polish to polish the results into paper.tex + PDF" |
| `math-modeling-contest` | General math-modeling pipeline (G1–G6 gates, DOCX/PDF, Nature-style figures) | When general math-modeling capability or a comparison is needed | "Use math-modeling-contest for this problem" |

**Recommended invocation chain (after the P0→P4 refactor)**:
```
csf_mechanism query cards → reasoning chain (doc 11) → blueprint (doc 00) → modeling + simulation (results in results/*.json)
→ csf_fig figures + visual QA → csf-paper-polish narrative + layout → csf_gate gates → compile + page-by-page acceptance
```

## 2-supplement. Executable gates (failing any blocks delivery)

### Language route (the biggest change of this round — read this first)

**Write natively in English; translate only at the end.** The old workflow "draft a Chinese contest
paper, then translate into English" had two independent defects. The larger one is not translation
but the **document class**: `cumcmthesis.cls` carries contest-flavored metrics, line spacing,
paragraph styles, title casing, caption formats, and the "problem restatement / notation" front-matter
structure — no matter how good the English, it never looks like a top-venue paper. The second,
smaller defect is rhetoric (Chinese "general–specific–general + evaluative" style literally translated
into subjectless passive sentences with firstly/secondly).
Therefore arguments must be constructed **directly in the target rhetoric**; the Chinese version is a
mechanical derivative of the frozen English final draft.

| Gate | Command | Function |
|---|---|---|
| Prose | `python skills/csf-paper-polish/scripts/csf_prose.py --tex paper.tex` | Four check classes (translation loss T / hype H / structural actions S / LaTeX mechanics M). **Calibrated bidirectionally**: good English → 0 hits; literal Chinese translation → 18 ERRORs |
| Build | `python skills/csf-paper-polish/scripts/csf_build.py --tex paper.tex` | Engine auto-selected by language (English LuaLaTeX / Chinese XeLaTeX), enough passes + BibTeX; **success judged by empirical criteria, not exit code** |
| Mechanism cards | `python skills/csf-simulation-modeling/scripts/csf_mechanism.py --fingerprint <phenomena>` | 18 mechanism cards; `--check` validates that every cited literature key really exists |
| Skeleton/numbers | `csf_gate.py --tex paper.tex --lang {zh,en}` | Section quotas, figure/table quotas, MAS elements, orphan figures, broken references, duplicate rows, number freezing. **With `--lang en` quotas are counted in prose words**; the Chinese path is byte-for-byte unchanged (verified by diff: same 10 ERRORs / 5 WARNs) |
| Readiness | `csf_readiness.py --tex paper.tex --lang en` | Top-venue contract: seeds/variance/baseline genealogy/limitations section/compute/vector figures. English body length counted in words (the old version counted Chinese characters, so an English draft always scored 0) |
| Method selection | `csf_select.py --plan` | 23 methods / 10 rules, five-step program |
| Cross-language parity | `csf_parity.py` | Python↔Julia numerical parity (deterministic policies must match exactly) |
| zh–en parity | `csf_localize.py` | Numbers/references/labels/figure-table counts/claim set must be strictly equal; only word order and articles may differ |
| Figures | `csf_method_templates.py --make all --lang en` | Five-domain English method-figure templates; `--check-parity` validates the zh/en versions item by item |
| Visual closed loop | `csf_fig.use_style(...)` + `read_image` per figure + `pdftoppm` per page | Render → read → fix; two-level acceptance (individual figure and whole page) |

### Defects found this round by "render to pixels and look" (the log showed 0 errors)

This is the most valuable experience of the round: **no `!` in the log does not mean the parameter took effect**.

| # | Symptom | Root cause | Criterion |
|---|---|---|---|
| 1 | Italics / small caps **silently degraded to upright** | Font set did not declare slanted glyphs | 260-dpi crop: `\textsl` and `\textup` **pixel-identical** |
| 2 | Caption label styling **completely ineffective** | caption package silently dropped the font list in `labelfont` (while `labelsep` from the same option set worked) | Switched to `\DeclareCaptionLabelFormat` writing literal code |
| 3 | **All preset dimensions dropped**, text block fell back to article default 6.5in | geometry's key parser does **not expand** its argument first; `\geometry{\csf@geometry}` was treated as a single key name | `\typeout{textwidth=...}` probe to **measure**: after the fix, 397.48499pt = 5.5in |
| 4 | Floats landing **above the paper title** | Page-1 top float area sits above the title block | `\suppressfloats[t]` at the end of `\csftitle` |
| 5 | Section headings **crashing into** the box above | Official heading pre-spacing is negative (NeurIPS −2.0ex), tuned assuming a paragraph precedes | Box `after skip` must exceed the maximum negative pre-spacing (16pt chosen; 8pt exactly cancels) |
| 6 | `Design rationale..` with two periods | run-in heading after-code appends a period automatically | Automatic period removed; the author writes it |

> The debugging procedure is now fixed: `pdftoppm -png -r 260 -x -y -W -H` to **crop regions** and
> inspect at high magnification; plus **print probes** for parameters that "should have taken effect".

## 3. Reference files of csf-simulation-modeling (by priority)
- `references/mechanisms.json` (+ `13-mechanism-cards.md`): **mechanism card library (P2)**, 18 cards, each with "phenomenon fingerprint → mechanism → mathematical form → falsifiable computable prediction → modeling choice → minimal experiment → anti-patterns → sources" — **before everything else**
- `references/11-scientific-reasoning.md`: scientific reasoning chain (phenomenon → essence → mechanism → falsifiable hypothesis → model selection for the hypothesis → progressive experiments → interpreting success/failure)
- `references/12-figure-pipeline.md`: **figure closed loop (P1)**, including three SciencePlots/CJK integration pitfalls and five iron rules
- `references/00-paper-blueprint.md`: paper blueprint (macro model + section/figure blueprint + content volume)
- `references/10-ai-conference-style.md`: AI top-venue figure conventions
- `references/08-domain-playbook.md`: Track-A five-domain standard models + real parameters
- `references/07-methods-library.md`: full method library + selection matrix
- `references/09-a-track-paper-depth.md`: 18-page depth standard (its quotas are enforced by `csf_gate.py`)
- Remaining 01–06: modeling paradigms, code standards, paper grading, journal extension, literature library (including the source list of the mechanism library in section J)


## 4. Directory layout (refactored; partitioned into skills/examples/reference/archive)
```
skills/                      # 3 skills
examples/                    # self-contained examples: 礼堂疏散/ 2018B-RGV/ 2025A-流水车间/ comparison-RGV
  └── <name>/code/           #   simulation/experiment code and data json per example
reference/                   # papers/ + analysis/ (skill comparison, framework narrative samples)
docs/                        # win/mac differences, etc.
archive/早期工作站/           # deprecated 01–04 skeletons
```

## 5. Experiment code and data (key point)
**All prior simulation/experiment code lived in /tmp, outside the workspace. This round it was consolidated into `实验代码/`:**
- Evacuation simulation: `evac_sim.py` (core run()), `evac_deep.py` (density/velocity), `evac_ablation.py` (frequency/λ ablation), `evac_methods.py` (6-method comparison)
- RGV scheduling: `rgv3.py` (multi-step lookahead, scored 366/281/375), `rgv_sim.py`/`rgv2.py` (greedy)
- Learning-based: `dqn_exit.py` (linear Q), `climbing.py` (Climbing Game IQL vs QMIX), `vdn_*.py`/`qmix_mpe.py` (value-decomposition attempts, did not converge)
- Figure scripts: `fig*.py`/`ai_figs.py`/`rgv_figs.py`/`evac_figs*.py`
- Data: `evac_*.json`, `dqn_results.json`, `climbing.json`, `rgv_results.json`, etc.

**Known issues (disclosed honestly)**:
1. `vdn_iql.py/vdn_fast.py/vdn2.py/qmix_mpe.py`: hand-written value decomposition **did not converge** (homogeneous shared policies cannot break symmetry). The correct approach is EPyMARL/PyMARLzoo+; do not hand-roll.
2. RGV group 2 efficiency is only 76% (RGV critical-path bottleneck; a real result, not a bug).
3. Figure scripts depend on json files in /tmp; these have been consolidated together — verify paths before running.
4. **In `evac_methods.json`, `nearest` / `shortest_queue` / `static_cong` have byte-identical values** —
   investigation showed this is a **mathematical necessity** (all queues are zero at t=0, so both
   degenerate to "nearest exit"), not a bug.
   But the paper's `tab:main` presented them as three independent evaluations side by side — a
   **presentation-level integrity problem** that must be rewritten (see §7, P4 TODO).

## 6. Current status and next steps
- Done: three-layer skills, scientific reasoning chain (doc 11), AI figure conventions (doc 10), domain playbook (doc 08), two sample papers (evacuation 11 pages / 0 TODOs; RGV 7 pages / lookahead 95%).
- User verdict: current output is "still worse than just using nature skills"; stronger modeling capability needed.

### P0→P4 refactor progress (this round completed P0/P1/P2/P3 + toolchain)

| Phase | Status | Deliverable |
|---|---|---|
| **P0** executable gates | ✅ | `csf-simulation-modeling/scripts/csf_gate.py`; measured on the sample paper: **10 ERRORs + 5 WARNs**, all hitting real defects |
| **P1** figure closed loop | ✅ | `csf-figure-forge/scripts/csf_fig.py` (semantic colors / auto-sizing component library / triple export) + `references/12-figure-pipeline.md`; example figure 1 redone, **5 defects fixed over 4 look-at-image iterations** |
| **P2** mechanism card library | ✅ | `references/mechanisms.json` (18 cards) + `scripts/csf_mechanism.py` (query/validate/generate md) + `13-mechanism-cards.md`; `--check` passes (all 78 literature keys resolvable) |
| **P3** layout shell + narrative shell | ✅ | `csf-paper-polish/assets/latex-template/csfstyle.sty` (6 semantic boxes, smoke test passes twice with exit 0) + `references/conference-narrative.md` (seven-sentence abstract pattern, related-work method-family table) |
| **Toolchain** | ✅ | MiKTeX per-user install; `xelatex` compiled the sample paper → **11 pages** (Track-A standard is 18 pages); `miktex-pdftoppm` page-by-page image reading works |
| **P4** sample paper rebuild | ⏳ TODO | see below |

### Whole-page defects found this round by "reading the PDF page by page" (invisible to per-figure review)
1. **Duplicate figure captions**: figures 1 and 5 had titles burned into the image *and* repeated in `\caption` → every such figure labeled twice;
2. **Bold table captions triggered font fallback**: `Font shape 'TU/SimSun/b/n' undefined`, caption line spacing doubled;
3. **Measured 11 pages vs the 18-page standard**: the gate's "insufficient content" conclusion was physically confirmed;
4. **Table 2's three identical rows** are glaring on paper.

### Contest and platform facts (verified 2026-02)

| Item | Content | Source |
|---|---|---|
| Organizers | Chinese Association for System Simulation (national first-tier society) + Jilin University of Finance and Economics | contest announcement |
| Technical support | Beijing GeruiNa Electronics (**AnyMath**), with AnyMath special awards (Excellence/Innovation/Elite/Rising: ¥4000/3000/2000/1000) | contest announcement |
| Contest window | **2026-10-16 20:00 → 10-20 20:00 (4 days)** | contest announcement |
| Track A positioning | Multi-agent co-evolution, complex dynamic-system simulation; for **collective, networked, scheduling-type** complex systems: digital modeling, dynamic deduction and optimization, **uncovering operating mechanisms of complex systems** | track description |
| Submission content | model construction + simulation deduction + **solution design** + results report (+ supporting materials including complete runnable source code and environment description) | contest announcement |
| Platform language | AnyMath documentation site `engee.com/helpcenter`; base language is **Julia (`jl`/`ngscript`)**, `ipynb` also supported; has "code generation" and "general language" chapters | AnyMath docs |

### New capabilities this round (round 2): figure archetype library + top-venue contract gates

| Deliverable | Function |
|---|---|
| `skills/csf-figure-forge/scripts/csf_archetypes.py` | **Four parameterized figure archetypes**: `method_figure` (method overview) / `result_panels` (composite results) / `comparison_table` (main experiment table, produces .tex+.csv+three image formats) / `ablation_matrix` (ablation matrix, auto-computes % degradation vs baseline) |
| `skills/csf-figure-forge/SKILL.md` | Figure-forge entry: three iron rules, five-step visual QA closed loop, six measured integration pitfalls |
| `skills/csf-figure-forge/references/topvenue-contracts.md` | **Top-venue figure and writing contract** (each item with evidence source and URL) + 20 anti-patterns + 28-item checklist |
| `skills/csf-paper-polish/scripts/csf_readiness.py` | **Top-venue readiness gate**: abstract gap sentence/numbers, ICML 4–6 sentences, standalone assumptions and limitations sections, error-bar semantics, seed count, compute, four-type baseline genealogy, bolding criteria, N/A annotation, fairness isolation, ODD, vector figures |
| `_vendor/fetch_repo.py` | Multi-channel (codeload → api zipball → raw) auto-degrading repo fetcher with `PROVENANCE.md` provenance |
| `_vendor/{cheatsheets, paper-tips-and-tricks, annotated_latex_equations, arxiv-style, pymarl, epymarl, smac, PettingZoo, diagrams}` | figure/annotated-equation/LaTeX-template/MARL training frameworks |

**The archetype library's automatic checks** (all bought with measured defects): unregistered semantic
roles error out immediately; missing glyphs raise (no tofu blocks ever shipped); module overlap /
out-of-bounds detection; **method-figure topology anti-pattern self-check** (cross-layer cut-through /
same-layer reverse flow / upward layer-backreference drawn with solid lines); auto-sizing by text
length; arrow anchor snapping to box edges; **cross-layer orthogonal polyline routing** (no diagonal
cut-through); arrow-label candidate-position avoidance.

### P4 TODO (next round — note the contest is approaching)

1. **Flesh out the sample paper skeleton to the 18-page budget** until `csf_gate.py` passes — but
   **do not polish the sample paper**; it exists only to validate the skill's constraint power. The
   skeleton files are ready: `examples/礼堂疏散/paper/sec1-front.tex`, `sec3-formalization.tex`,
   `sec4-model.tex`, `sec5-exp.tex`.
2. **`eval_methods_fixed.py` has had two substantive errors fixed** (static-policy equivalence,
   standard Gini definition); `code/results/sweeps.json` is the single source of numerical truth;
   the paper's numbers must be synced from that file.
3. **Train QMIX/MAPPO for real with EPyMARL** to add learning-based coordination (`_vendor/epymarl`
   is in place); until then, fabricating coordination results is forbidden.
4. **AnyMath landing**: wait for the AnyMath documentation subagent's report (platform capabilities
   and Python→Julia porting risk table), then write the "local Python validation → AnyMath
   reproduction" migration checklist.

---

## 7. This round's (round 3) delivery: the native-English route

The user's judgment was "the translation loss between Chinese papers and English top venues makes
the result look bad". **This judgment is half right**: the main cause of the bad look is the
document class (see §2-supplement); rhetorical loss is real but a secondary layer. This round fixes
both layers by construction.

### New / modified files

| File | Nature | Notes |
|---|---|---|
| `skills/csf-paper-polish/assets/latex-en/csfstyle-en.sty` | New, 49 KB | Neutral English top-venue shell, 6 venue presets + 4 font sets; **every value of neurips/icml/aaai transcribed from the official .sty with line numbers** |
| `skills/csf-paper-polish/assets/latex-en/paper-en.tex` | New | Compilable English template (4 pages), organized in top-venue argument order, with `\csfclaim`/`\csfevi`/`\csffigplaceholder` |
| `skills/csf-paper-polish/assets/latex-en/refs.bib` | New | 6 real seed references (**volume/issue/page numbers must be verified item by item before use**) |
| `skills/csf-paper-polish/assets/latex-en/showcase/*.png` | New | Rendered baselines for the single-column (NeurIPS) and two-column (ICML) presets |
| `skills/csf-paper-polish/scripts/csf_prose.py` | New, 44 KB | Prose gate, 40+ rules in four classes, **every hit comes with a suggested rewrite** |
| `skills/csf-paper-polish/scripts/csf_build.py` | New | Build driver, success judged by empirical criteria |
| `skills/csf-paper-polish/scripts/csf_localize.py` | New | Mechanical localization parity after the Chinese final draft |
| `skills/csf-paper-polish/references/english-narrative.md` | New | Prose contract: five-paragraph funnel, five-action abstract, thirteen zh→en failure modes with rewrites |
| `skills/csf-paper-polish/references/venue-style-specs.md` | New, 43 KB | Parameter tables extracted by a subagent from the **official .sty files** (13 UNVERIFIED annotations) |
| `skills/csf-paper-polish/references/latex-workflow.md` | Expanded | English-shell workflow added + pitfalls 6–10 |
| `skills/csf-paper-polish/SKILL.md` | Rewritten | Language route promoted to first principle |
| `skills/csf-figure-forge/scripts/*.py` | Modified | `lang="en"`; text ledger `labels.json`; `--check-parity` |
| `skills/csf-figure-forge/examples/templates-en/` | New | Five-domain English method figures + ledgers |
| `skills/csf-simulation-modeling/scripts/csf_gate.py`、`csf_readiness.py` | Modified | `--lang {zh,en}`; Chinese path byte-for-byte unchanged |
| `_vendor/venue-styles/` | New | Official style files for NeurIPS/ICML/AAAI/ACM/IEEE (`fetch_styles.py` can re-fetch) |

### Explicit capability boundaries (do not overstate)

- The `nature`/`elsevier` presets are **stylized** implementations, not official classes (neither
  publisher ships a general LaTeX class); `aamas` approximates acmart/sigconf (the official 2025
  bundle was behind Cloudflare 403).
- The shell is a **writing tool**, not a compliance checker. For actual submission use the official
  classes under `_vendor/venue-styles/` (the AAAI class issues `\PackageError` for 16 packages,
  including `geometry` and `hyperref`).
- Class S of `csf_prose.py` covers only the **reliably judgeable** subset; missing articles,
  number–noun agreement, etc. are **deliberately not checked** (an unreliable gate gets switched
  off) — see `english-narrative.md` §10.
- Visual details of figures (an occasional label touching a line, slight cropping of layer labels)
  are **intentionally unpolished** — per user requirement, figures are responsible only for
  placement and narrative; vector redrawing and annotation are done by hand. The ledger exists
  exactly for that step.

### Next steps

1. **Pre-contest stress test**: run a brand-new Track-A problem end-to-end with the skill
   (query cards → select methods → skeleton → English final draft → parity), timing it and
   recording pain points.
2. Run one zh–en parity pass with `csf_localize.py` to validate the freeze/parity chain.
3. Only after `_vendor/epymarl` has trained QMIX/MAPPO for real may learning-based coordination
   results be written.
4. AnyMath's free license is "20 hours per month" and the original text excludes scientific
   research use → **license applicability must be confirmed with the organizers before the
   contest**.
