# English narrative contract — how a top-venue simulation paper argues

This file is the **rhetoric half** of the English conversion. Its counterpart is
`assets/latex-en/csfstyle-en.sty`, which handles appearance. Both are needed and
neither substitutes for the other: a perfectly typeset paper that argues like a
contest report still gets discounted in the first paragraph, and a well-argued
paper in `cumcmthesis.cls` still looks like homework.

Machine-checkable rules are marked `[code]` and are enforced by
`scripts/csf_prose.py`. Rules that cannot be judged mechanically are marked
`[human]` and are deliberately *not* automated — a checker that fires on correct
work gets switched off, so this file keeps the unreliable judgements as prose.

---

## 0. Why writing Chinese first fails, stated precisely

The diagnosis "translation loss" is half right, and the half it gets wrong is the
bigger half. Two independent defects were compounding:

1. **Document class (dominant).** `cumcmthesis.cls` is a Chinese contest template:
   SimSun, 1.5 line spacing, two-character first-line indent, wide white space,
   "Problem Restatement / Assumptions / Notation" front matter. The *measure*,
   *leading*, *paragraph style*, *heading case*, *caption style* and *front matter*
   are all contest-flavoured, so no quality of English inside it can look like a
   top-venue paper. Fixed by construction in `csfstyle-en.sty`.

2. **Rhetoric (real, and second).** Chinese contest prose is 总—分—总, evaluative
   and nominalisation-heavy. Translated word-for-word it yields agentless passives,
   `firstly / secondly / finally`, and adjectives with no evidence. This is not
   scattered grammar errors; it is a small enumerable set of patterns, which is why
   it can be gated.

The reason to write English **first** is therefore not convenience. It is that the
Chinese rhetorical structure, once written, *forces* the translation. If the
argument exists only in 总分总 form, the translator has nothing else to render. So:
**the argument must be built in the target rhetoric from the start**, and
localisation becomes a mechanical derivative of a frozen source
(`scripts/csf_localize.py`).

---

## 1. The argument order (do not reorder)

A top-venue simulation paper is not "restate the problem, analyse it, model it".
It is:

> here is a gap → here is the mechanism → here is a method that follows from the
> mechanism → here is the evidence → here is exactly where it breaks

| Position | Section | The move it must make |
|---|---|---|
| 1 | Introduction | Sell the gap in five paragraphs (see §2) |
| 2 | Related Work | Prior work as **contrast**, ending every paragraph on a difference |
| 3 | Problem Formulation | Define the *decision*, with an objective **and constraints** |
| 4 | Model and Method | Every component carries its **design rationale** |
| 5 | Experiments | Setup → baselines → main → mechanism → ablation → sensitivity → failure |
| 6 | Discussion | What the mechanism implies beyond this instance |
| 7 | Limitations | Concrete, with the direction of the induced bias |
| — | Reproducibility / Compute | Mandatory at ICML and increasingly everywhere |

Note what is **absent**: 问题重述 (restatement), 符号说明 as a standalone chapter
before any model, and 模型的优点/缺点 as an evaluative list. A notation table is
fine, but it belongs inside the formulation and must be referenced before it
appears. "Advantages" is not a section; it is what the results show.

---

## 2. Abstract: five moves, 4–6 sentences

ICML 2025 author instructions state the abstract should ideally be 4–6 sentences.
The moves, in order:

1. **Context with stakes**, one clause, with a number if one exists.
2. **The gap, as a mechanism** — not "few studies have considered X" but "the
   quantity being optimised is changed by the act of optimising it".
3. **What we do**, plus the single design decision that drives the result.
4. **The quantitative result**: effect size, comparison, and uncertainty.
5. **The implication**, plainly, without hedging.

`[S01_ABSTRACT_LEN]` sentence count outside 3–6.
`[S02_ABSTRACT_CITE]` no `\cite`/`\ref` — the abstract must be self-contained.
`[S03_ABSTRACT_NO_NUMBER]` no numeral anywhere: move 4 is missing.

**Rewrite pair** (both from the same real content):

> ✗ In recent years, with the rapid development of artificial intelligence,
> evacuation simulation plays an important role. Firstly, existing methods cannot
> handle large-scale scenarios. Secondly, efficiency is low. In order to solve
> these problems, this paper mainly proposes a novel method which significantly
> improves efficiency by 20% and has important significance.

> ✓ Evacuating 400 agents through five unequal exits takes 483.9 min under
> nearest-exit routing, 3.4× the capacity lower bound. Because queues are
> identically zero at the first decision epoch, congestion-aware routing cannot
> help: only the split of demand across stations moves the makespan. We show that a
> capacity-proportional rule closes the gap to 1.10× of the bound, and that an
> ablation attributes the remaining difference to decision frequency rather than to
> cost design. The bottleneck in this class of problem is station packing, not
> route choice.

The ✗ version contains seven separate gate violations and, more importantly, no
information: a reader cannot tell what was measured or what was found.

---

## 3. Introduction: the five-paragraph funnel

| ¶ | Move | Check |
|---|---|---|
| 1 | Domain and **stakes**, with at least one real number and a citation | `[S06_INTRO_NO_NUMBER]`, `[S07_INTRO_NO_CITE]` |
| 2 | The specific problem, narrowed to the decision this paper makes | `[human]` |
| 3 | Why the obvious approach fails, **at the level of mechanism** | `[human]` — the most important paragraph in the paper |
| 4 | Our approach in two sentences, plus the intuition for why it should work | `[human]` |
| 5 | Numbered contributions, each ending in a testable claim | `[S08_NO_CONTRIBUTIONS]` |

Paragraph 3 is what makes the paper science rather than engineering. "Existing
methods have limitations" is not paragraph 3. This is:

> Congestion-aware routing is the natural choice, yet it is self-defeating:
> choosing a station changes the queue length that the choice reads. At the first
> decision epoch every queue is zero, so the rule degenerates to nearest-exit and
> the cost model never binds.

Paragraph 5 is a **contract**. Every contribution must be discharged later, by a
named figure, table or section — which is exactly what `\csfclaim`/`\csfevi`
bind in the source and `[S15_CLAIM_NO_EVIDENCE]` enforces.

---

## 4. Related Work: contrast, never a list

Every paragraph takes one family of prior work and ends on a specific difference:

> X et al. optimise Y under Z. Their formulation assumes ⟨assumption⟩, which fails
> in ⟨our setting⟩ because ⟨mechanism⟩. We therefore ⟨difference⟩.

`[S10_RELATED_NO_CONTRAST]` fails the paper when **no** paragraph contains a
contrast marker, and warns per paragraph that does not. A paragraph that only
summarises is dead weight: delete it. This is where contest drafts most often turn
into an annotated bibliography, because 综述 training rewards coverage rather than
positioning. Coverage is not the goal; the reader needs to know what you did
*differently*.

---

## 5. Method: rationale, not recipe

For each component the pattern is:

> Because ⟨mechanism⟩, the ⟨thing⟩ must satisfy ⟨property⟩, which rules out
> ⟨obvious choice⟩ and leaves ⟨our choice⟩.

A component presented without its *why* is indistinguishable from one copied out of
a textbook. Use run-in `\paragraph{...}` headings for these rationale blocks; they
are far tighter than another numbered level. `[human]` — a machine cannot tell a
rationale from a description.

Two specific traps:

* **Do not dress an observation up as a theorem.** If a claim is empirical, say
  which experiment tests it. `csf_prose.py` will not stop you; a reviewer will.
* **Pseudocode only when prose cannot do it.** A 40-line listing that restates the
  equations is padding, and it is the first thing removed by a page limit.

---

## 6. Experiments

Order, and the reason for the order:

1. **Setup** — instance generation, size, number of independent runs, seed policy,
   hardware, wall-clock. "Mean over 10 seeds" without a seed policy is not
   reproducible.
2. **Baselines by class.** At least three *distinct* classes: a rule/heuristic, a
   single-agent learned method, and a multi-agent learned method. Three variants of
   one family is not a comparison; `csf_readiness.py` fails that.
   A baseline given less information than the proposed method is not a baseline.
3. **Main result.** Caption must state the comparison rule: what is bold, what the
   error bars are, how many runs. Never bold a best value without stating the rule,
   never claim a win inside the noise. Prefer an interval to a p-value — the
   `rliable` line of work argues explicitly against dichotomising at p < 0.05.
4. **Mechanism.** Plot the *intermediate* quantity that carries the effect. This
   subsection is what separates a simulation paper from a benchmark report. Without
   it you have shown *that*, not *why*.
5. **Ablation.** One row per design decision, each removed individually. An
   ablation that changes two things at once explains nothing.
6. **Sensitivity.** "Robust" must come with the range over which it is robust.
7. **Failure.** `[S13_NO_FAILURE_CASE]` — the regime where the method loses, with
   numbers. A paper with no failure case is either trivial or not yet understood.

---

## 7. Figures: position and narrative, in that order

The figures in this project are *not* the final art: they fix the space a panel
occupies and carry the sentence the reader must take away. The art is redrawn by
hand in vector software afterwards. That division has consequences for how the text
is written:

* **The caption states the conclusion, not the contents.** `[S14_CAPTION_DESCRIPTIVE]`
  fires on captions that open with "shows/illustrates/depicts" and contain no claim
  verb.
  > ✗ Figure 3 shows the architecture of the proposed method.
  > ✓ Two capacity constraints bind at different λ; the switch between them is what
  > limits throughput (Sec. 5.3).
* **Freeze the space before the art exists.** `\csffigplaceholder[<width>]{<height>}`
  occupies the exact final size and carries the caption, so line breaking, page
  count and caption length are all final before anything is drawn. Otherwise the
  art lands, the page count moves, and the text is rewritten.
* **Ship a label ledger.** Because the labels are re-set by hand later, each figure
  exports a machine-readable inventory of its text (content, role, position) so
  that wording, casing and terminology stay identical to the paper.
* **Never let one panel serve two claims.** Reusing one figure file for two
  distinct narrative roles is the "figure reuse collapse" that `csf_gate.py` fails.

---

## 8. Hedging, tense, and person

* **Tense.** Present for what the paper claims and what a figure shows ("Figure 3
  shows…", "the bound is tight at λ = 0.02"). Past for what you did in a specific
  run ("we ran ten seeds"). Never mix within one sentence.
* **Person.** "We" for authorial actions is standard at every venue in scope. The
  passive is for the system under study, not for hiding the author.
* **Hedging** must be calibrated to the evidence, not to politeness:
  | Strength | Use when |
  |---|---|
  | "X is Y" | proved, or measured with negligible noise |
  | "X is consistent with Y" | the mechanism is inferred, not isolated |
  | "We conjecture that X" | no evidence yet — put it in Discussion |
  | "X suggests Y" | a trend, single instance, or wide interval |
* **`significant` is a statistical term.** `[H01_SIGNIFICANT]` — using it without a
  test is one of the most common *specific* reviewer objections. Either give the
  test or write "substantially" and give the difference.
* **`novel` is a verdict, not a claim.** `[H03_NOVEL]` — state the difference
  instead ("unlike X, which assumes A, …").

---

## 9. Sentence-level: the Chinese-to-English failure modes

These are the patterns `csf_prose.py` catches, with the rewrite it prescribes.

| Pattern | Code | Rewrite |
|---|---|---|
| `firstly / secondly / lastly` | `T01_FIRSTLY` | Connect by *logic* (Moreover / Because), or use real numbered items |
| `in order to` | `T02_IN_ORDER_TO` | `To` |
| `it is well known that` | `T03_WELL_KNOWN` | Delete, cite, or explain the mechanism |
| `plays an important role` | `T04_IMPORTANT_ROLE` | A testable mechanism statement |
| `in recent years, with the rapid development of` | `T05_RAPID_DEVELOPMENT` | The specific change, with a number and a citation |
| `this paper mainly studies` | `T06_MAINLY` | Delete "mainly"; if you restrict scope, say what is excluded |
| `not only … but also` | `T07_NOT_ONLY` | Two sentences, each with its own evidence |
| `carry out an analysis of` | `T08_NOMINALIZATION` | `analyse` |
| `through the simulation, we can see` | `T10_THROUGH_CAN` | `The simulation shows` — or just `X (Fig. 3)` |
| `respectively` (repeated) | `T11_RESPECTIVELY` | A table; let the reader align columns, not clauses |
| `very / quite / rather` | `T14_VERY` | Delete, or quantify (`3.4× the bound`) |
| `make X become` | `T16_MAKES_BECOME` | `X causes Y to …` |
| `in conclusion` mid-paper | `T17_SUM_UP` | The Conclusion section exists; write the conclusion |
| long sentences (> 40 words) | `T09_LONG_SENTENCE` | Split; Chinese tolerates long sentences, English reviewers do not |

Two LaTeX-level traps that have nothing to do with style but silently destroy
content:

* **`[M01_BARE_PERCENT]`** — `improves by 20% over the baseline` comments out
  " over the baseline". It compiles with no error and the PDF is missing half a
  sentence. Percent signs need `\%`.
* **`[M02_CN_PUNCT]`** — full-width （，。；：） surviving into the English version is
  the clearest "half-translated" tell there is: wider and heavier than their
  half-width counterparts, visible at a glance.

---

## 10. What is deliberately *not* checked

Judged too unreliable to automate, and left to a human reader:

* missing or wrong articles (`a`/`the`) — no reliable detector without a parser;
* subject–verb agreement beyond a few high-confidence idioms
  (`[T19_AGREEMENT]` covers only those);
* whether a rationale is actually a rationale rather than a description;
* whether a stated mechanism is the *right* mechanism;
* whether related work is complete or fairly represented;
* whether the chosen baselines are the ones a reviewer would demand.

The last three are where a paper is actually won or lost. No gate replaces a reader.
