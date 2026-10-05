# Venue style specs — hard typographic parameters read out of the official style files

Reference for building a **neutral English top-venue style shell**. Every row below is traceable to a
line in a downloaded file or to a URL that was actually fetched. Anything not verifiable is marked
`UNVERIFIED`. Nothing here is inferred from memory of how a venue "usually" looks.

Downloaded kits live in `_vendor/venue-styles/<venue>/_raw/`. Machine-readable provenance
(URL, byte count, sha256, UTC timestamp, extracted file list) is in
`_vendor/venue-styles/_download-manifest.json`, plus a per-venue `PROVENANCE.md`.

Retrieval date for all downloads: **2026-10-05 (UTC)**. Repository-root-relative links below are
written from the workspace root `D:\anymath-and-simulation`.

---

## 0. What was obtained, and from where

| Venue | Local path | Source URL | Bytes | sha256 (first 16) |
|---|---|---|---|---|
| NeurIPS 2025 | `_vendor/venue-styles/neurips/_raw/neurips_2025.sty` (+ `.tex`, `.pdf`) | `https://media.neurips.cc/Conferences/NeurIPS2025/Styles.zip` | 188,273 | `72032130232955b7` |
| NeurIPS 2024 | `_vendor/venue-styles/neurips/_raw/Styles/neurips_2024.sty` | `https://media.neurips.cc/Conferences/NeurIPS2024/Styles.zip` | 186,748 | `67a5a2e6ef6af3f1` |
| NeurIPS checklist | `_vendor/venue-styles/neurips/_raw/PaperChecklist.html` | `https://neurips.cc/public/guides/PaperChecklist` | 72,778 | `61af30299c78e101` |
| NeurIPS author instructions | `_vendor/venue-styles/neurips/_raw/CallForPapers.html` | `https://neurips.cc/Conferences/2025/CallForPapers` | 70,061 | `b66cb7816a1e3802` |
| ICML 2025 | `_vendor/venue-styles/icml/_raw/icml2025.sty`, `icml2025.bst`, `example_paper.tex/.pdf` | `https://media.icml.cc/Conferences/ICML2025/Styles/icml2025.zip` | 258,356 | `9fe6c79d886fb20b` |
| ICML 2025 example PDF | `_vendor/venue-styles/icml/_raw/example_paper.pdf` | `https://media.icml.cc/Conferences/ICML2025/Styles/example_paper.pdf` | 226,607 | `b48806aeb46b12e4` |
| ICML 2024 | `_vendor/venue-styles/icml/_raw/icml2024/icml2024.sty` | `https://media.icml.cc/Conferences/ICML2024/Styles/icml2024.zip` | 263,601 | `7969210731472bf6` |
| ICML author instructions | `_vendor/venue-styles/icml/_raw/AuthorInstructions.html` | `https://icml.cc/Conferences/2025/AuthorInstructions` | 85,912 | `ae6cabed64d14b24` |
| AAAI-25 author kit | `_vendor/venue-styles/aaai/_raw/CameraReady/LaTeX/aaai25.sty`, `aaai25.bst` | `https://aaai.org/authorkit25-2/` (serves `AuthorKit25/…zip`) | 6,782,486 | `3782e57817aa2ddc` |
| AAAI-25 author instructions | `_vendor/venue-styles/aaai/_raw/CameraReady/LaTeX/Formatting-Instructions-LaTeX-2025.tex` | (same kit) | — | — |
| AAMAS (see §4 caveat) | `_vendor/venue-styles/aamas/_raw/aamas.cls`, `ACM-Reference-Format.bst`, `main.tex` | `https://codeload.github.com/furushchev/aamas-paper-template/zip/refs/heads/master` | 810,098 | — |
| AAMAS 2023 instructions PDF | `_vendor/venue-styles/_probe/overleaf-aamas2023-instructions.pdf` | `https://ja.overleaf.com/latex/templates/aamas-2023-formatting-instructions/jgqscwyyrhwf.pdf` | 611,576 | — |
| ACM `acmart` v2.20 | `_vendor/venue-styles/acm-acmart/_raw/acmart.dtx`, `ACM-Reference-Format.bst`, `samples/` | `https://mirrors.ctan.org/macros/latex/contrib/acmart.zip` | 15,106,903 | `93933ce58fbeffa1` |
| IEEE `IEEEtran` V1.8b | `_vendor/venue-styles/ieee-ieeetran/_raw/IEEEtran.cls`, `bibtex/IEEEtran.bst`, `bare_conf.tex` | `https://mirrors.ctan.org/macros/latex/contrib/IEEEtran.zip` | 1,727,001 | `e0cd4f5afbd42c80` |
| `arxiv-style` | `_vendor/venue-styles/arxiv-style/_raw/arxiv.sty` | `https://codeload.github.com/kourgeorge/arxiv-style/zip/refs/heads/master` | 205,020 | `ebc60796732a6ee3` |
| SAGE journals (`sageep`) | `_vendor/venue-styles/sage-sageep/_raw/sageep.dtx`, `sageep.bst` | `https://mirrors.ctan.org/macros/latex/contrib/sageep.zip` | 357,661 | `f53febf05689ff58` |

Note: `_vendor/arxiv-style/` already existed in this repo from an earlier fetch. Its `arxiv.sty` is
**byte-identical** (sha256 `5ca551dbda415732…`) to the copy downloaded here, so the duplicate under
`_vendor/venue-styles/arxiv-style/_raw/` is harmless and self-consistent.

**Could NOT obtain (tried all channels, all failed):**

| Target | Channels tried | Result |
|---|---|---|
| **AAMAS official `aamas.cls` / author kit** | `www.ifaamas.org/Proceedings/aamas2025/…` (imagined paths), `aamas2025.org/…` (site), Overleaf 2025 template | `ifaamas.org` paths → 404; `aamas2025.org` → **HTTP 403 Cloudflare**; Overleaf 2025 slug → 404. Only a third-party GitHub mirror was reachable — see §4. |
| **JASSS** (Journal of Artificial Societies and Social Simulation) | `mirrors.ctan.org/…/jasss.zip`, `www.jasss.org/JASSS/` | 404 — **no LaTeX style package exists**; JASSS publishes HTML/PDF from its own site templates. Not a LaTeX venue. |
| **Simulation (SAGE journal, `SIM`)** | `mirrors.ctan.org/…/simulation.zip`, `journals.sagepub.com/author-instructions/SIM`, `us.sagepub.com/…` | 404 / **403**. No journal-specific LaTeX package on CTAN. The generic **SAGE `sageep`** class *was* obtained as the closest available proxy (§8). |
| **`github.com/borisveytsman/acmart` `/zip/refs/heads/main` · `/zip/refs/heads/master`** | codeload | 404 — the repo's default branch is **`primary`**. Not needed: CTAN `acmart.zip` is the released version and is what was verified. |
| `NeurIPS/NeurIPS-2025`, `mlresearch/icml2025`, `aaai/aaai25` (guessed GitHub repos) | codeload + api.github.com | 404 — **these repositories do not exist**. Official kits are only distributed from the conference media servers. Do not invent these URLs. |
| NeurIPS 2023/2022/2021 `Styles.zip` | `media.neurips.cc` | 404 (only 2025, 2024, 2020 still resolve). 2024 is present locally as the fallback. |
| Overleaf official templates (NeurIPS/ICML/AAAI) | `www.overleaf.com/latex/templates/…` | 404 for the guessed slugs; Overleaf's *AAMAS 2023* PDF did resolve and is cited in §4. |

### Network channels that actually worked
- `media.neurips.cc`, `media.icml.cc`, `neurips.cc`, `icml.cc`, `aaai.org`, `mirrors.ctan.org` — direct HTTPS, no rate limit.
- `codeload.github.com` — works, but **the branch must be exact** (`refs/heads/master` vs `…/main`). A wrong branch returns `404: Not Found`, which is easily misread as "repo does not exist".
- `api.github.com` — works, 60 req/h unauthenticated; `search/code` is **401 Requires authentication** without a token, so `filename:` code search is unavailable.
- Blocked/403: `aamas2025.org` (Cloudflare), `journals.sagepub.com`.
- The harness Python's `ssl` cannot verify `arxiv.org` (`CERTIFICATE_VERIFY_FAILED`).

---

## 1. Quick table A — page geometry and columns

| Parameter | NeurIPS 2025 | ICML 2025 | AAAI-25 | ACM acmart sigconf | IEEEtran `conference` | SAGE sageep | arxiv-style |
|---|---|---|---|---|---|---|---|
| Paper size | US letter (`letterpaper`) | 8.5 × 11 in | 8.5 × 11 in US letter | 8.5 × 11 in | US letter default (`a4paper` option exists) | inherits `article` default | US letter |
| Columns | 2 (inherited `article`) | 2 (`\twocolumn`) | 2 (`\twocolumn`) | 2 | 2 (`\twocolumn` default) | **1** | **1** |
| `\textwidth` | **5.5 in** | **6.75 in** | **7.0 in** | not set directly (see geometry row) | **43 pc** = 2×21 pc + 1 pc | not set (geometry margins) | **6.5 in** |
| `\textheight` | **9 in** | **9.0 in** (=650.43 pt asserted) | **9.0 in** | not set directly | **9.25 in** (conference); 58 pc journal | not set (geometry margins) | **9 in** |
| Geometry / margins | `top=1in, headheight=12pt, headsep=25pt, footskip=30pt` | `\oddsidemargin \evensidemargin -0.23in`; `\topmargin` −20 pt then −0.29 in; `headheight 10pt`, `headsep 10pt`, `footskip 25.0pt` | `\topmargin -0.25in`, `\oddsidemargin -0.25in`; prose states top .75 in, left .75 in, right .75 in, **bottom 1.25 in** | `top=57pt, bottom=73pt, inner=54pt, outer=54pt`, `head=13pt`, `includeheadfoot` | `\IEEEsettopmargin{t}{0.75in}`, `\headheight 12pt`, `\headsep 18pt`, side margins centred | `top=0.75in, left=0.75in, right=0.75in, bottom=1in` | `top=1in, headheight=14pt, headsep=25pt, footskip=30pt` |
| `\columnsep` | not set (class default 10 pt) | **0.25 in** | **0.375 in** | **2 pc**, `columnsep=2pc` | **1 pc** | n/a | n/a |
| Column width | ≈2.65 in (derived; not stated) | ≈3.25 in (derived; not stated) | prose: "**3.3 inches wide** (slightly more than 3.25 inches)" | derived | 21 pc | n/a | n/a |
| Bottom-flush / sloppy | `\flushbottom`, `\sloppy`, `\widowpenalty=10000`, `\clubpenalty=10000` | `\flushbottom \twocolumn`, `\sloppy` | `\flushbottom \twocolumn \sloppy` | — | — | — | `\flushbottom`, `\sloppy`, same penalties |

Defining lines:
- NeurIPS: [`neurips_2025.sty:115-124`](_vendor/venue-styles/neurips/_raw/neurips_2025.sty) — `\usepackage[verbose=true,letterpaper]{geometry}` … `textheight=9in, textwidth=5.5in, top=1in, headheight=12pt, headsep=25pt, footskip=30pt`
- ICML: [`icml2025.sty:185-226`](_vendor/venue-styles/icml/_raw/icml2025.sty) — `\paperwidth=8.5in`, `\paperheight=11in`, `\oddsidemargin -0.23in`, `\setlength\textheight{9.0in}`, `\setlength\textwidth{6.75in}`, `\setlength\columnsep{0.25in}`; layout is **asserted and policed** at `icml2025.sty:250-276` (`\ifdim\textwidth=487.8225pt \else … marginsmessedwithtrue`), so any change is detected and reported.
- AAAI: [`aaai25.sty:34-41`](_vendor/venue-styles/aaai/_raw/CameraReady/LaTeX/aaai25.sty) — `\setlength\topmargin{-0.25in} \setlength\oddsidemargin{-0.25in}` / `\setlength\textheight{9.0in} \setlength\textwidth{7.0in}` / `\setlength\columnsep{0.375in}` / `\flushbottom \twocolumn \sloppy`. Margin prose at [`Formatting-Instructions-LaTeX-2025.tex:395-409`](_vendor/venue-styles/aaai/_raw/CameraReady/LaTeX/Formatting-Instructions-LaTeX-2025.tex).
- ACM sigconf: [`acmart.dtx:3806-3810`](_vendor/venue-styles/acm-acmart/_raw/acmart.dtx) — `\or % sigconf` / `\geometry{twoside=true, head=13pt, paperwidth=8.5in, paperheight=11in, includeheadfoot, columnsep=2pc, top=57pt, bottom=73pt, inner=54pt, outer=54pt, marginparwidth=2pc,heightrounded}`. Format menu documented at [`acmart.dtx:313-341`](_vendor/venue-styles/acm-acmart/_raw/acmart.dtx) (`sigconf` = "Proceedings format for most ACM conferences … and all ICPS volumes"; `sigchi`/`sigchi-a` retired 2020 and auto-switch to `sigconf`).
- IEEEtran: [`IEEEtran.cls:1722-1750`](_vendor/venue-styles/ieee-ieeetran/_raw/IEEEtran.cls) — `\textheight 58pc  % 9.63in, 696pt`, `\columnsep 1pc`, `\textwidth 43pc   % 2 x 21pc + 1pc = 43pc`, and under `\ifCLASSOPTIONconference`: `\textheight 9.25in % The standard for conferences (668.4975pt)`, `\IEEEsettopmargin{t}{0.75in}`.
- sageep: [`sageep.dtx:335,357`](_vendor/venue-styles/sage-sageep/_raw/sageep.dtx) — `\LoadClass[12pt]{article}`, `\RequirePackage[top=0.75in, left=0.75in, right=0.75in, bottom=1in]{geometry}`.
- arxiv-style: [`arxiv.sty:10-20`](_vendor/venue-styles/arxiv-style/_raw/arxiv.sty) — `textheight=9in, textwidth=6.5in, top=1in, headheight=14pt`.

---

## 2. Quick table B — typography, headings, captions

| Parameter | NeurIPS 2025 | ICML 2025 | AAAI-25 | ACM sigconf | IEEEtran conference | SAGE sageep | arxiv-style |
|---|---|---|---|---|---|---|---|
| Body size / leading | **10 pt on 11 pt** | **10 pt on 11 pt** | **10 pt on 12 pt** (prose) / class: `\@xpt{11}` | base class default (**10 pt**) | 10 pt on **11.0476 pt**, quantized | **12 pt** (`article` 12pt) | 10 pt on 11 pt |
| Body family | **Times** (`\rmdefault=ptm`), sans `phv` | article default (**Computer Modern**) — `UNVERIFIED` for serif family | **Times / Nimbus** mandated; Courier for sans; no Computer Modern text | **Linux Libertine** (`libertine` + `zi4` + `newtxmath`) | Times (`\rmdefault` times) | article default | **Times** (`ptm`) / `phv` |
| `\baselineskip` explicit | via `\@setfontsize\normalsize\@xpt\@xipt` | `\@normalsize{\@setsize\normalsize{11pt}\xpt\@xpt}` | `\def\normalsize{\@setfontsize\normalsize\@xpt{11}}` | (class) | `\@setfontsize{\normalsize}{10}{12.00pt}` in the `\@ptsize=0` branch | (class) | `\@setfontsize\normalsize\@xpt\@xipt` |
| `\parindent` / `\parskip` | **0 pt** / **5.5 pt** (block paragraphs, no indent) | `\@afterindenttrue` — section first paragraph **is** indented | `\parindent 10pt` | `\normalparindent` (acmart-defined) | — | — | — |
| Section `\section` | `\large\bf\raggedright`, before `-2.0ex`, after `1.5ex`, numbered | `\large\bf\raggedright`, before `-0.12in`, after `0.02in`, numbered | `\Large\bf\centering`, before `-2.0ex`, after `3pt`, **unnumbered** (`secnumdepth=0`) | `\bfseries\Large\section@raggedright`, before `-.75\baselineskip`, after `.25\baselineskip`, numbered to depth 3 | class default `\section` (numbering controlled by `\IEEEaftertitletext`/class; `UNVERIFIED` here) | `\large\bfseries\centering`, before `\baselineskip`, after `\baselineskip` | `\large\bf\raggedright`, numbered |
| `\subsection` | `\normalsize\bf\raggedright`, `-1.8ex` / `0.8ex` | `\normalsize\bf\raggedright`, `-0.10in` / `0.01in` | `\large\bf\raggedright`, `-2.0ex` / `3pt` | `\bfseries\Large\section@raggedright` (**same size as `\section`**), `-.75\baselineskip` / `.25\baselineskip` | — | `\normalsize\itshape\bfseries`, after `1sp` | — |
| `\subsubsection` | `\normalsize\bf\raggedright`, `-1.5ex` / `0.5ex` | **`\normalsize\sc\raggedright` (small caps)**, `-0.08in` / `0.01in` | `\normalsize\bf`, run-in (`-1em`) | `\sffamily\itshape` + dot, after `-3.5pt` | — | — | — |
| Heading case | As typed (not uppercased) | **Content words capitalized, NOT all caps** (mandated) | As typed | As typed since v2.08 ("Deleted uppercasing") | — | Title uppercased: `\MakeUppercase{\@title}` | As typed |
| Caption label | default LaTeX → `Figure 1:` bold; prose says the label follows the figure | `\def\fnum@figure{Figure \thefigure}` → "**Figure 1**", **label italic**, `\small\sl #1.~` and a **period** (not colon) | "figures **1**" lowercase style; caption text must be **10 pt roman**, not bold/italic | `\captionsetup[table]{position=top}`, `labelfont={bf}`, `textfont={bf}`, **`labelsep=colon`** | `\figurename{Fig.}` (non-compsoc), `\tablename{TABLE}`; caption set `\normalfont\footnotesize`; **long captions are parboxed flush-left**, **short captions centred in conference mode**, flush-left in journal mode | `\captionsetup{labelfont=bf, indent=0pt, singlelinecheck=off}`; `\captionsetup[table]{position=above}` | default `article` |
| Caption size | default (same as body → 10 pt) | subscript line `\footnotesize` (10 pt) with `\baselineskip 11pt`; short form `\small` | **10 pt roman** exactly | inherits body (10 pt), bold | `\footnotesize` = **9 pt** in 10 pt docs | inherits body (12 pt) | body size |
| Caption placement | figure caption **below**, table title **above** (prose) | figure caption below (standard `\@makecaption` above the float's `\abovecaptionskip`) | **both figure AND table captions BELOW** (author instructions; this diverges from the .sty default) | table caption **above**; figure caption below | table caption above, figure caption below | table caption above | — |
| Caption justification | — | long captions: label box then wrapped body, left-aligned; short captions `\centerline` | — | `margin=\z@` (full width) | conference: centred; journal: left | `singlelinecheck=off` (never auto-centre short captions) | — |
| Abstract heading | `\large\bf Abstract`, **centred** (`\centerline`), preceded by `\vskip 0.075in`, body in `quote` | `\centerline{\large\bf Abstract}`, then `\vspace{-0.12in}\begin{quote}` | `\bf Abstract`, **centred** (`\centerline`), `\vspace{0.5ex}`, `\leftmargini 10pt`, body `\small` | abstract must **precede** `\maketitle`; styling from `caption`/class defaults, not a fixed size here | class default | class default | class default |
| Indent / width of abstract | prose: **½ inch (3 pc)** both sides, **10 pt on 11 pt**, headed by 12 pt bold "Abstract", 2 blank lines before, **one paragraph only** | prose: starts `0.4 in` below final address, heading centred bold **11 pt**, body **10 pt on 11 pt**, indented `0.25 in` extra each side, `0.4 in` blank after, **one paragraph, ~4–6 sentences** | body `\small` (**9 pt**), indented `10 pt` | — | — | — | — |
| Abstract length limit | one paragraph (prose) | one paragraph, ideally 4–6 sentences (prose) | — | — | IEEE journals have a 150–250 word limit but this is journal policy, not in `IEEEtran.cls` → `UNVERIFIED` | — | — |

Defining lines:
- NeurIPS fonts/headings/abstract: [`neurips_2025.sty:91-93, 136-144, 161-196, 227-229, 345-358`](_vendor/venue-styles/neurips/_raw/neurips_2025.sty) — `\renewcommand{\rmdefault}{ptm}`, `\renewcommand{\sfdefault}{phv}`, `\@setfontsize\normalsize\@xpt\@xipt`, `\@startsection{section}{1}{\z@}{-2.0ex …}{1.5ex …}{\large\bf\raggedright}`, `\setlength{\parindent}{\z@}`, `\setlength{\parskip}{5.5\p@}`, `\renewenvironment{abstract}{\vskip 0.075in\centerline{\large\bf Abstract}\vspace{0.5ex}\begin{quote}}`.
- NeurIPS caption skips: [`neurips_2025.sty:208-219`](_vendor/venue-styles/neurips/_raw/neurips_2025.sty) — above-caption skip **7 pt**, below **0 pt**, and **swapped for `table`** so table titles sit above.
- NeurIPS abstract + page-limit prose: [`neurips_2025.tex:109-115`](_vendor/venue-styles/neurips/_raw/neurips_2025.tex), `:127-132`.
- NeurIPS figure/table guidance: [`neurips_2025.tex:317-358`](_vendor/venue-styles/neurips/_raw/neurips_2025.tex) — caption *after* the figure, one line space before/after, caption lower-case except first word/proper nouns, colour allowed but must survive B/W printing, tables **must not contain vertical rules** (booktabs recommended).
- NeurIPS reference allowance: [`neurips_2025.tex:470-477`](_vendor/venue-styles/neurips/_raw/neurips_2025.tex) — unnumbered first-level heading, **font may be reduced to `\small` (9 pt)**, references excluded from page limit.
- ICML geometry/captions/sections/abstract: [`icml2025.sty:326, 579-586, 639-650, 696-705, 707-724`](_vendor/venue-styles/icml/_raw/icml2025.sty).
- ICML section/caption/abstract prose: [`example_paper.tex:329-360`](_vendor/venue-styles/icml/_raw/example_paper.tex) — "The heading 'Abstract' should be centered, bold, and in 11 point type. The abstract body should use 10 point type, with a vertical spacing of 11 points, and should be indented 0.25 inches more than normal…"; "Section headings should be numbered, flush left, and set in 11 pt bold type with the content words capitalized. Leave 0.25 inches of space before the heading and 0.15 inches after"; "subsection headings … 10 pt bold … 0.2 inches before, 0.13 inches afterward"; "subsubsection headings … 10 pt small caps … 0.18 inches before, 0.1 inches after"; "Please use no more than three levels of headings."
- ICML language requirements (fetched page, see §5): section headings must be **Title Case, not ALL CAPS**; **US letter mandatory**; **citation font size must equal body font size**.
- AAAI: [`aaai25.sty:133-143`](_vendor/venue-styles/aaai/_raw/CameraReady/LaTeX/aaai25.sty) (abstract), `:162-173` (sections + `\setcounter{secnumdepth}{0}`), `:216-225` (font sizes incl. `% 10 point on 11`).
- AAAI caption/figure rules: [`Formatting-Instructions-LaTeX-2025.tex:510, 585, 594, 599, 606, 609`](_vendor/venue-styles/aaai/_raw/CameraReady/LaTeX/Formatting-Instructions-LaTeX-2025.tex).
- ACM sigconf captions: [`acmart.dtx:4222-4251`](_vendor/venue-styles/acm-acmart/_raw/acmart.dtx) — `\captionsetup[table]{position=top}`; non-journal branch `\captionsetup{labelfont={bf}, textfont={bf}, labelsep=colon, margin=\z@}`; per-format overrides (siggraph italic text, sigplan period separator, sigchi small sans labels).
- ACM sigconf section fonts: [`acmart.dtx:8405-8429, 8464-8502`](_vendor/venue-styles/acm-acmart/_raw/acmart.dtx) — `\renewcommand\section{\def\@toclevel{1}\@startsection{section}{1}{\z@}{-.75\baselineskip …}{.25\baselineskip}{\ACM@NRadjust\@secfont}}`, and for `sigconf`: `\def\@secfont{\bfseries\Large\section@raggedright}`, `\def\@subsecfont{\bfseries\Large\section@raggedright}`, `\def\@subsubsecfont{\sffamily\itshape}`, `\def\@parfont{\itshape}`, `\setcounter{secnumdepth}{3}`.
- ACM abstract ordering: [`acmart.dtx:1058-1061`](_vendor/venue-styles/acm-acmart/_raw/acmart.dtx) — "The environment `abstract` must *precede* the `\maketitle` command… Putting `abstract` after `\maketitle` will trigger an error."
- IEEEtran captions: [`IEEEtran.cls:2693-2706, 2773-2793`](_vendor/venue-styles/ieee-ieeetran/_raw/IEEEtran.cls) — `\setlength\abovecaptionskip{0.5\baselineskip}`, `\setlength\belowcaptionskip{0pt}`, and the non-compsoc `\@makecaption` quoted above. Figure/table names at `:2607-2609`.
- sageep: [`sageep.dtx:412, 438-448, 460-470`](_vendor/venue-styles/sage-sageep/_raw/sageep.dtx) — `\MakeUppercase{\@title}`, `\renewcommand\section{\@startsection{section}{1}{0pt}{\baselineskip}{\baselineskip}{\normalfont\centering\large\bfseries}}`, `\captionsetup{labelfont=bf, indent=0pt, singlelinecheck=off}`, `\captionsetup[table]{position=above}`.

---

## 3. Page limits, statements, reproducibility (from fetched instruction pages / author kits)

| Venue | Content page limit | Excluded from limit | Required statements | Source |
|---|---|---|---|---|
| **NeurIPS 2025** | **9 content pages** incl. all figures and tables; **+1 page** allowed for camera-ready | references, **paper checklist**, optional technical appendices | **Paper checklist is mandatory and part of the submission** ("forms part of the paper submission, but does not count towards the page limit"); camera-ready must include a **funding disclosure**; `ack` environment hides acknowledgments at submission; `\answerYes/\answerNo/\answerNA/\answerTODO` macros provided | [`CallForPapers.html`](_vendor/venue-styles/neurips/_raw/CallForPapers.html) ("The main text of a submitted paper is limited to **nine content pages**…"), [`neurips_2025.sty:361-365`](_vendor/venue-styles/neurips/_raw/neurips_2025.sty), [`PaperChecklist.html`](_vendor/venue-styles/neurips/_raw/PaperChecklist.html) |
| **ICML 2025** | submission **8 pages** main body; camera-ready **9 pages** | references, appendices, acknowledgements, **impact statement** | **Mandatory impact statement in an unnumbered section just before the bibliography** for camera-ready; optional acknowledgements also unnumbered; **lay summary** required in OpenReview (new 2025) | [`AuthorInstructions.html`](_vendor/venue-styles/icml/_raw/AuthorInstructions.html) — "the length limit of the paper body is **9 pages**, followed by any acknowledgements, the impact statement, and references"; "mandatory impact statement in an unnumbered section just before the bibliography" |
| **AAAI-25** | not stated in the LaTeX instructions file (AAAI uses a **page fee** model: "you may … pay the extra page charge (if it is offered)") | — | no reproducibility checklist file in the kit; **copyright form, photo release, video distribution** forms are in the kit (`Copyright/`) | [`Formatting-Instructions-LaTeX-2025.tex:411-415`](_vendor/venue-styles/aaai/_raw/CameraReady/LaTeX/Formatting-Instructions-LaTeX-2025.tex) |
| **ACM acmart (sigconf)** | not set by the class — **the individual conference sets it** | — | `acks` environment starts an unnumbered Acknowledgments section; `\grantsponsor`/`\grantnum` for funding; `CCS` concepts required by ACM submission software; `\setcopyright{…}` mandatory | [`acmart.dtx:1601-1649`](_vendor/venue-styles/acm-acmart/_raw/acmart.dtx), `:916` (CCS tool URL), `:965-1034` (copyright menu) |
| **IEEEtran** | not set by the class — journal/conference policy | — | class supports `\begin{IEEEkeywords}`, `\thanks`, `\markboth`; **conference mode locks out `\thanks`** | [`IEEEtran.cls`](_vendor/venue-styles/ieee-ieeetran/_raw/IEEEtran.cls), [`bare_conf.tex:346-349`](_vendor/venue-styles/ieee-ieeetran/_raw/bare_conf.tex) |
| **AAMAS** | `UNVERIFIED` (site 403) | — | — | — |
| **SAGE sageep** | not set by the class | — | — | — |

NeurIPS checklist mechanics (verified in [`PaperChecklist.html`](_vendor/venue-styles/neurips/_raw/PaperChecklist.html)): it is a numbered list of questions with `[Yes]/[No]/[NA]/[TODO]` answers; the style file defines the answer macros and colours (blue / orange / grey / red-bold) at [`neurips_2025.sty:360-365`](_vendor/venue-styles/neurips/_raw/neurips_2025.sty).

---

## 4. AAMAS — partially verified only (read this before using it)

AAMAS's official style kit could **not** be downloaded: `aamas2025.org` returns **403 (Cloudflare)** for
every path and the Overleaf 2025 template slug 404s. `www.ifaamas.org` (the publisher) serves the
proceedings HTML but all probed kit paths 404.

What *was* obtained and read is a **third-party GitHub mirror**,
`furushchev/aamas-paper-template`, which ships a docstrip-generated `aamas.cls`
(`\ProvidesClass{aamas}` / `\ProvidesClass… [2017/07/09 v1.43 Typesetting articles for Association of
Computing Machinery, variant for AAMAS conference]`). Parameters below are read out of that file and
are marked accordingly. **Treat as `UNVERIFIED against the official AAMAS 2025 kit`** — it is a 2017
class generation, and `sample-aamas18.pdf` in the same repo dates it to AAMAS 2018.

| Parameter | Value / defining line | Confidence |
|---|---|---|
| Base class | `\LoadClass[\ACM@fontsize, reqno]{amsart}` — a fork of **`acmart`**, not a from-scratch class ([`aamas.cls:191`](_vendor/venue-styles/aamas/_raw/aamas.cls)) | verified in the mirror |
| Declared format | default `\setkeys{aamas.cls}{format=sigconf}` ([`aamas.cls:139`](_vendor/venue-styles/aamas/_raw/aamas.cls)); the sample uses `\documentclass[sigconf]{aamas}  % do not change this line!` ([`main.tex:11`](_vendor/venue-styles/aamas/_raw/main.tex)) | verified in the mirror |
| Geometry (= ACM `sigconf`) | `\geometry{twoside=true, head=13pt, paperwidth=8.5in, paperheight=11in, includeheadfoot, columnsep=2pc, top=57pt, bottom=73pt, inner=54pt, outer=54pt, marginparwidth=2pc,heightrounded}` ([`aamas.cls:504-510`](_vendor/venue-styles/aamas/_raw/aamas.cls)) | verified in the mirror |
| Fonts | Libertine + `zi4` + `newtxmath`, T1 encoded — same block as `acmart` ([`aamas.cls:604-632`](_vendor/venue-styles/aamas/_raw/aamas.cls)) | verified in the mirror |
| Captions | `\captionsetup[table]{position=top}`; non-journal branch `\captionsetup{labelfont={bf}, textfont={bf}, labelsep=colon, margin=\z@}` ([`aamas.cls:636-644`](_vendor/venue-styles/aamas/_raw/aamas.cls)) | verified in the mirror |
| Sections | `\renewcommand\section{\@startsection{section}{1}{\z@}{-.75\baselineskip \@plus -2\p@ \@minus -.2\p@}{.25\baselineskip}…}` ([`aamas.cls:2269-2283`](_vendor/venue-styles/aamas/_raw/aamas.cls)) | verified in the mirror |
| Bibliography style | `\bibliographystyle{ACM-Reference-Format}  % do not change this line!` ([`main.tex:201`](_vendor/venue-styles/aamas/_raw/main.tex)); `ACM-Reference-Format.bst` ships in the mirror | verified in the mirror |
| Copyright | `\setcopyright{ifaamas}`; class defines the `ifaamas` copyright mode text "International Foundation for Autonomous Agents and Multiagent Systems (www.ifaamas.org). All rights reserved." ([`aamas.cls:1275, 1352-1353`](_vendor/venue-styles/aamas/_raw/aamas.cls)) | verified in the mirror |
| AAMAS 2025 page limit, camera-ready rules, figure guidance | — | **UNVERIFIED** (official site 403) |
| AAMAS 2023 formatting instructions PDF | `https://ja.overleaf.com/latex/templates/aamas-2023-formatting-instructions/jgqscwyyrhwf.pdf` → saved to `_vendor/venue-styles/_probe/overleaf-aamas2023-instructions.pdf` (611,576 B, HTTP 200). Not machine-read here; available if prose rules are needed. | fetched, not extracted |

---

## 5. Reference style file per venue, and requirements worth knowing

| Venue | Bib style | Notes / gotchas |
|---|---|---|
| NeurIPS 2025 | **no fixed style** — "Any choice of citation style is acceptable as long as you are consistent." | `natbib` is auto-loaded unless `[nonatbib]`; reference font may drop to `\small` (9 pt); `\usepackage{times}` is auto-loadable. [`neurips_2025.sty:109-112`](_vendor/venue-styles/neurips/_raw/neurips_2025.sty), [`neurips_2025.tex:473-476`](_vendor/venue-styles/neurips/_raw/neurips_2025.tex) |
| ICML 2025 | **`icml2025.bst`** (ships in the zip) | `\setcitestyle{authoryear,round,citesep={;},aysep={,},yysep={;}}` at [`icml2025.sty:577`](_vendor/venue-styles/icml/_raw/icml2025.sty); author instructions demand replacing arXiv citations with peer-reviewed versions and brace-protecting proper nouns in BibTeX; **citation font size must match body size**. Camera-ready uses `\usepackage[accepted]{icml2025}`. |
| AAAI-25 | **`aaai25.bst`** (ships in the kit) | `\bibliographystyle{aaai25}` is forced by the style file when `natbib` is loaded ([`aaai25.sty:227-236`](_vendor/venue-styles/aaai/_raw/CameraReady/LaTeX/aaai25.sty)); in-text citations are author-year, `(Newell 1980)`, 4+ authors → "et al." ([instructions:513](_vendor/venue-styles/aaai/_raw/CameraReady/LaTeX/Formatting-Instructions-LaTeX-2025.tex)) |
| ACM acmart | **`ACM-Reference-Format.bst`**, or BibLaTeX `acmnumeric.bbx` / `acmauthoryear.bbx` | numeric is the default ([`acmart.dtx:3305`](_vendor/venue-styles/acm-acmart/_raw/acmart.dtx)); both `.bst` and `.bbx/.cbx` ship in the CTAN zip |
| IEEEtran | **`IEEEtran.bst`** (+ `IEEEtranN/S/SA/SN` variants) | variant matrix ships in `bibtex/`; `IEEEtran_bst_HOWTO.pdf` included |
| SAGE sageep | **`sageep.bst`** | ships in the CTAN zip |
| AAMAS | **`ACM-Reference-Format.bst`** | from the mirror only |

---

## 6. Figure / table guidance stated in the author instructions

| Venue | Vector vs raster | Font size inside figures | Colour |
|---|---|---|---|
| **NeurIPS 2025** | Not mandated. Artwork must be "neat, clean, and legible"; lines "dark enough for purposes of reproduction". `xfig` "patterned" shapes and `\bbold` are called out as **bitmap-font (Type 3) offenders**; PDFs must contain **Type 1 or embedded TrueType fonts** | — | "You may use color figures. However, it is best for the figure captions and the paper body to be legible if the paper is printed in either black/white or in color." |
| **ICML 2025** | **Prefer vector** — "If possible, please use **vector graphics (eps or pdf figures)** for experimental results such as line plots and bar plots to maximize readability, and only use **bitmap graphics** for certain illustrations and visualizations that cannot be easily represented by vector graphics." | — | "review guidelines for accessibility to color-blind and visually impaired" |
| **AAAI-25** | Figures **must be `.jpg`, `.png`, or `.pdf`**; **`.gif`, `.ps`, `.eps` forbidden**; **300 dpi** when incorporated; no clipping in LaTeX (`trim`/`clip`/bounding-box edits forbidden — crop outside LaTeX); `pgfplots` output must be exported to PDF first | "Labels and other text with the actual illustration must be at least **nine-point** type"; figure captions exactly **10 pt roman**; table captions **10 pt roman, below the table**; math font may not drop below **6.5 pt** | Colour **figures only**, must be **WCAG 2.0 compliant (contrast > 4.5:1)**, must be **CMYK not RGB**, never in text; paper must be decipherable without colour |
| **ACM acmart** | — | — | Dedicated accessibility section: "ensure that your article is still readable when printed in greyscale"; CVD guidance; recommends the ACE colour evaluator ([`acmart.dtx:2045-2073`](_vendor/venue-styles/acm-acmart/_raw/acmart.dtx)) |
| **IEEEtran** | Journal guidance in `IEEEtran_HOWTO.pdf` / `bare_conf.tex` — `UNVERIFIED` here (not machine-read) | — | — |
| **AAMAS** | — | — | — |

AAAI extra structural rules worth copying into a neutral shell: **no `hyperref`** (the style file raises `\PackageError`), **no `bbm`** (Type 3 fonts), no negative `\vspace`/`\vskip` around captions/figures/headings/references, no packages altering floats/margins/fonts/sizing/linespacing, algorithm and listing captions go in a **header between horizontal rules** ([`aaai25.sty:237-243`](_vendor/venue-styles/aaai/_raw/CameraReady/LaTeX/aaai25.sty), [instructions:210-216, 621-649](_vendor/venue-styles/aaai/_raw/CameraReady/LaTeX/Formatting-Instructions-LaTeX-2025.tex)).

---

## 7. How the venues actually diverge, numerically

Sorted so the appearance-changing parameters are adjacent:

| | NeurIPS | ICML | AAAI | ACM sigconf | IEEE conf | SAGE |
|---|---|---|---|---|---|---|
| text width (in) | **5.50** | **6.75** | **7.00** | ≈7.03 (8.5 in − 2×54 pt) | **5.97** (43 pc) | 7.0 (8.5 − 1.5) |
| text height (in) | **9.00** | **9.00** | **9.00** | ≈9.39 (11 in − 57 pt − 73 pt) | **9.25** | 9.25 (11 − 0.75 − 1.0) |
| gutter (in) | 0.14 (10 pt) | **0.25** | **0.375** | 0.33 (2 pc) | **0.167** (1 pc) | n/a |
| body pt | 10 | 10 | 10 | 10 | 10 | **12** |
| leading pt | 11 | 11 | 12 (prose) / 11 (class) | 12 | **11.05** | — |
| columns | 2 | 2 | 2 | 2 | 2 | **1** |
| section font | `\large\bf` | `\large\bf` | `\Large\bf` **centred, unnumbered** | `\bfseries\Large` | — | `\large\bfseries` **centred**, title **UPPERCASE** |
| caption label | "Figure 1:" bold (default) | "Figure 1" **italic + period** | "Figure 1." 10 pt roman | bold + **colon** (`labelsep=colon`) | "Fig. 1." `\footnotesize`, centred short captions | bold label, `singlelinecheck=off` |
| table caption | **above** | above | **below** (per instructions) | **above** | **above** | **above** |

Derived numbers above are arithmetic on the quoted lengths; where a value is derived it is marked by the `≈` and should be re-derived if the source kit is upgraded.

---

## 8. Cross-venue common core

Parameters on which **all** of the obtained official styles agree (NeurIPS, ICML, AAAI, ACM sigconf, IEEEtran conference; SAGE sageep differs on the single-column and 12 pt points):

1. **US Letter paper, 8.5 × 11 in.** Mandated explicitly by ICML ("Your paper must be in US letter size (i.e., not A4 or other sizes)") and AAAI ("The paper size for final submission must be US letter without exception"); hard-coded as `paperwidth=8.5in, paperheight=11in` in acmart/`aamas.cls`, as `letterpaper` default in NeurIPS geometry and IEEEtran.
2. **10 pt body type.** `\@setfontsize\normalsize\@xpt…` in NeurIPS, ICML, AAAI; IEEEtran `{10}{12.00pt}`/`{10}{11.0476pt}`; acmart default base class size 10 pt.
3. **Times-class serif body.** NeurIPS `\rmdefault=ptm`; AAAI mandates "Times or Nimbus … may not use Computer Modern for the text of your paper"; IEEEtran Times; arxiv-style `ptm`. (ACM/acmart is the one exception: Linux Libertine.)
4. **Two columns** for every conference venue; **9 in of text height** for NeurIPS, ICML and AAAI (IEEE conference = 9.25 in, ACM sigconf ≈9.39 in).
5. **`\flushbottom` and `\sloppy`**, with `\widowpenalty`/`\clubpenalty` set to 10000 in NeurIPS, ICML and the NIPS-derived arxiv-style.
6. **Reduced leading** ("font sizes with reduced leading", ICML "Less leading in most fonts (due to the narrow columns)") — body leading is 10–12 pt for a 10 pt body, i.e. **1.0–1.2 ×**, never 1.5 ×.
7. **Left-aligned, bold, numbered section headings** — with the single exception of AAAI, which centres its unnumbered section headings. Heading font size is `\large` (12 pt) or `\Large` (14 pt), never larger.
8. **Section numbering by default**, with `secnumdepth` set explicitly (acmart `3`, AAAI `0`).
9. **A distinct, smaller, centred abstract heading** with an indented (quote-block) abstract body and a **one-paragraph** rule (NeurIPS and ICML state this in prose).
10. **Caption text is not larger than body text** — 9 pt in IEEE, 10 pt in AAAI/ICML, inherited 10 pt in NeurIPS/ACM — and the figure label is **bold** (or bold-italic in ICML).
11. **Figure caption below the figure; table caption above the table** — NeurIPS, IEEEtran, ACM sigconf, SAGE all agree; AAAI's *author instructions* contradict its own class default and demand the table caption **below**.
12. **Small captions are centred, long captions are set flush and wrap** (IEEEtran states the rule explicitly; ICML implements the same with a `\centerline` short branch and a label-box + wrapped-body long branch).
13. **Authors / affiliations / email are set centred in the full text width above the two-column body**, using the `\twocolumn[…title…]` idiom (AAAI `\twocolumn[\@maketitle]`, ICML `\twocolumn[...]`, AAMAS/acmart `\twocolumn[\box\mktitle@bx]`); NeurIPS instead puts centring inside `\@maketitle` with `\hsize\textwidth`.
14. **The reference list does not count toward the page limit** in every venue that states a limit (NeurIPS, ICML), and the reference font may be reduced (NeurIPS: to `\small` = 9 pt).
15. **A camera-ready / preprint switch is a class or package option**, never an edited style file: NeurIPS `[final]`, `[preprint]`, `[nonatbib]`; ICML `[accepted]`, `[nohyperref]`; AAAI `\showauthors@on`; acmart `review`/`anonymous`/`authordraft`.
16. **Layout is policed, not merely suggested.** ICML explicitly detects altered `\textwidth`/`\textheight`/`\paperwidth`/`\paperheight`/margins and prints "The page layout violates the ICML style."; NeurIPS warns and overwrites if `fullpage` is loaded; AAAI forbids `geometry` and lists `\columnsep, \float, \topmargin, \topskip, \textheight, \textwidth, \oddsidemargin, \evensidemargin` as forbidden.

## 9. Venue-specific divergences

Divergences that **change appearance** and therefore need a per-venue branch in a neutral shell:

| # | Divergence | NeurIPS | ICML | AAAI | ACM sigconf | IEEEtran conf | Notes |
|---|---|---|---|---|---|---|---|
| D1 | **Text width** | 5.5 in | 6.75 in | 7.0 in | ≈7.03 in | 5.97 in | The single largest appearance difference; a 1.5 in spread. |
| D2 | **Column gutter** | 10 pt (class default) | 0.25 in | 0.375 in | 2 pc (24 pt) | 1 pc (12 pt) | AAAI's gutter is 1.5× ICML's. |
| D3 | **Section heading position** | flush left | flush left | **centred** | flush left | class default | AAAI is the outlier. |
| D4 | **Section numbering** | on | on | **off** (`secnumdepth=0`) | on (depth 3) | class-dependent | |
| D5 | **Subsubsection style** | bold roman | **small caps** | bold run-in | `\sffamily\itshape` + dot | — | Three different treatments. |
| D6 | **Caption label separator** | `:` (default) | **`.`** | `.` | **`:` via `labelsep=colon`** | `.` (caption built as `{#1.}…`) | |
| D7 | **Caption label face** | bold (default) | **italic** (`\small\sl`) | **10 pt roman, explicitly not bold/italic** | **bold, text also bold** | roman `\footnotesize`, table text `\scshape` | AAAI is the only venue forbidding a bold label. |
| D8 | **Table caption placement** | above (swapped skips) | above | **below** | above | above | AAAI author instructions vs. all others. |
| D9 | **Body serif family** | Times | Computer Modern (`UNVERIFIED`) | Times/Nimbus **mandated** | **Linux Libertine** | Times | |
| D10 | **Abstract body size** | 10 pt, ½ in inset | 10 pt, 0.25 in extra inset, heading 11 pt | `\small` = **9 pt** | class default | class default | |
| D11 | **Reference font** | may drop to 9 pt | must match body | — | class default | class default | |
| D12 | **Title casing rule** | none stated | **Title Case mandated; ALL CAPS forbidden** | none stated | none stated (uppercasing removed in v2.08) | none stated | SAGE sageep does the opposite: `\MakeUppercase{\@title}`. |
| D13 | **`\parindent`** | **0 pt** (block paragraphs, `\parskip` 5.5 pt) | indented first paragraph after headings (`\@afterindenttrue`) | 10 pt | `\normalparindent` | — | NeurIPS is the notable block-paragraph venue. |
| D14 | **Colour policy** | "best if legible in B/W or color" | accessibility-oriented | **CMYK only, WCAG 2.0, figures only, never text** | greyscale-legibility guidance | — | AAAI is by far the strictest. |
| D15 | **Figure file formats** | Type 1 / embedded TrueType required | prefer **vector (eps/pdf)** | **jpg/png/pdf only**; gif/ps/eps banned; 300 dpi | — | — | Mutually incompatible: a shell cannot satisfy all three with one setting. |
| D16 | **In-figure minimum type** | — | — | **≥9 pt labels, 10 pt captions, ≥6.5 pt math** | — | — | Only AAAI states a numeric floor. |
| D17 | **Mandatory extra artefacts** | **paper checklist** + funding disclosure | **impact statement** + lay summary | copyright/photo/video release forms | CCS concepts + copyright block | — | |
| D18 | **Forbidden packages** | `fullpage` (warning + overwritten) | `geometry`, `savetrees`, `fullpage` (detected via length assertions) | `hyperref`, `bbm`, `authblk`, `balance`, `CJK`, `flushend`, `fontenc`, `fullpage`, `geometry`, `grffile`, `navigator`, `savetrees`, `setspace`, `stfloats`, `tabu`, `titlesec` — each raises `\PackageError`; plus `epsf`, `epsfig`, `euler`, `float`, `title sec` per the instructions | none (class tolerates most; `amssymb` discouraged, [`acmart.dtx:2161`](_vendor/venue-styles/acm-acmart/_raw/acmart.dtx)) | `subfig` only with `caption=false`, else IEEE captions break | AAAI is the strictest by a wide margin — its `.sty` actively `\PackageError`s 16 packages. |
| D19 | **Single-column outlier** | — | — | — | — | — | `sageep` (SAGE) is 12 pt **single column**; `arxiv-style` is 10 pt single column at 6.5 in text width — both are preprint/journal shapes, not conference shapes. |

---

## 10. Reproduction commands

The downloader is kept next to the kits so the table can be re-derived after a venue releases a new kit:

```
python _vendor\venue-styles\_scripts\fetch_styles.py       # re-download + rewrite manifest/PROVENANCE
python _vendor\venue-styles\_scripts\probe.py              # reachability probe (codeload/raw/CTAN)
python _vendor\venue-styles\_scripts\probe2.py             # codeload branch diagnosis + api rate_limit
python _vendor\venue-styles\_scripts\probe3.py             # conference-site / CTAN URL probes
python _vendor\venue-styles\_scripts\probe4.py             # NeurIPS & ICML media URL probes
python _vendor\venue-styles\_scripts\discover.py           # GitHub API repo discovery (rate limited)
python _vendor\venue-styles\_scripts\hunt_aamas.py         # AAMAS style-file hunt (documents the 403s)
```

Python used: `C:\Users\wzw\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe` (3.12.14).

---

## 11. Verification ledger

| Claim | Status |
|---|---|
| All geometry, font-size, section and caption rows in §1, §2, §7 | **VERIFIED** — quoted from the downloaded `.sty`/`.cls`/`.dtx` files, with line numbers |
| Page limits and statement requirements in §3 for NeurIPS and ICML | **VERIFIED** — from the fetched `CallForPapers` and `AuthorInstructions` pages saved locally |
| AAAI figure/colour/caption rules in §6 | **VERIFIED** — from `Formatting-Instructions-LaTeX-2025.tex` |
| NeurIPS 2025 checklist content and macros | **VERIFIED** — `PaperChecklist.html` + `neurips_2025.sty:360-365` |
| Derived column widths (NeurIPS 2.65 in, ICML 3.25 in, ACM ≈7.03 in, IEEE 5.97 in) | **DERIVED** by arithmetic from quoted `\textwidth`/margins/`\columnsep`; not printed by any style file |
| ICML body serif family | **UNVERIFIED** — `icml2025.sty` never sets `\rmdefault`, so the family comes from the loaded `article` class |
| IEEEtran `\section`/`\subsection` typographic parameters | **UNVERIFIED** — `IEEEtran.cls` uses the base class sectioning with `\IEEEaftertitletext` hooks; the exact `\@startsection` arguments were not located in this pass |
| IEEEtran journal figure-resolution and word-limit policy | **UNVERIFIED** — lives in `IEEEtran_HOWTO.pdf`, not machine-read |
| AAMAS 2025 official geometry, fonts, captions, page limit | **UNVERIFIED** — `aamas2025.org` HTTP 403; values in §4 come from a third-party 2017/2018-era `aamas.cls` mirror |
| Overleaf AAMAS 2023 instructions content | **FETCHED, NOT EXTRACTED** — PDF saved locally, prose not machine-read |
| JASSS LaTeX style | **DOES NOT EXIST** — no CTAN package, site is HTML-based |
| Simulation (SAGE) journal-specific LaTeX style | **NOT AVAILABLE** — CTAN 404, publisher 403; generic `sageep` used as proxy |
| `NeurIPS/NeurIPS-2025`, `mlresearch/icml2025`, `aaai/aaai25` GitHub repos | **CONFIRMED NON-EXISTENT** — 404 from both codeload and `api.github.com/repos/...`; do not use these URLs |
