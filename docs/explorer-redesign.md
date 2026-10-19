# Explorer redesign: finding and comparing bounds

Proposal, 2026-10-19; the maintainer's decisions are recorded under *Decisions* below. Evidence: explorer branch
`feat/result-extra-forms` at d58be0a, built against library extraction a4f8773 (2026-10-18;
4105 declarations, 350 results). An audit script computes every number below from the built
`data.json` and the curation files (Appendix C says how to rerun it). The sample is the rendered
pages in headless Chrome, plus the library's CONTRIBUTING §4 (names) and §6 (docstrings).

## Summary

The maintainer's complaint about RSVD is that HMT 10.6 and Tropp–Webber 8.1 are both bounds on
the expected spectral error. They sit on two pages, under "average" and "expected", and one of
them is hard to find. That is not a one-off. The explorer has one unit, the **Result**, and it is
doing three jobs at once:

1. the identity of a named theorem ("Weyl's inequality");
2. a bucket for every bound an author filed under an algorithm, up to 29 theorems, which
   vary along four or five independent axes;
3. the unit of search hits, graph nodes, collections and Rates links.

A result page has one place to choose a statement, the Variant dropdown, and that dropdown has
one dimension. So **42% of all theorem memberships (315 of 754) cannot be selected as the
statement of their page**. The figure is 56% in Low rank. Those statements are only reachable
by scrolling past Lean blocks. In 13 cases one question, "(algorithm, error measure,
statistic)", is answered on two to four different pages. Half of the comparisons that authors
wrote into docstrings ("incomparable with …") point at a declaration on another result page.

The library's names are systematic enough to fix this without hand curation. On the algorithm
modules, the algorithm, error measure, statistic and sketch law of a bound can be read from
its name and its statement's dependencies for 96–98% of theorems, and the two sources agree
wherever both apply. **Recommendation (architecture C):** keep results as theorem pages with
stable URLs. Give every probabilistic bound a facet record inferred at build time. Then:

- replace the Variant dropdown with a statement table that lists every member;
- add generated comparison views, e.g. RSVD × spectral × expected, and algorithm overview
  pages;
- later, generate the Rates skeleton from the same records.

Stage 1 can ship on its own. It needs no library change and makes Tropp–Webber's 8.1 bounds
findable. §5 lists the decisions for the maintainer.


## Decisions (maintainer, 2026-10-19)

These answer the questions of §5 ("Decisions for the maintainer"). Where they differ from the
proposal's staging, they take precedence.

1. **Architecture: C** (hybrid). Results stay as theorem pages with stable URLs; facets are
   inferred at build time; the explorer keeps an overrides file.
2. **Vocabulary**:
   - "expected error" everywhere; "average" and "mean" are retired for errors;
   - E‖·‖ and E‖·‖² are written as formulas in labels and table headers, never as "squared"
     or "second moment";
   - "tail bound" for probability statements, not "high probability" or "deviation";
   - "late-truncated" for truncation after the algorithm (early truncation keeps its name);
   - titles drop the leading "The".
3. **Merges: fold in.** `randomized-svd-average-spectral-error` goes into
   `randomized-svd-expected-error`, and `randomized-svd-deviation-bound` into
   `randomized-svd-tail`. The old ids keep working as aliases and redirect to the merged page
   with the corresponding statement selected. `etrsvd` and `etgn` are not split.
4. **Facets** are inferred from declaration names (and statement dependencies), with an
   explorer-side overrides file keyed by declaration name. No docstring tag.
5. **Rates**: asymptotic pairs without a reviewed summary will be shown as "pending" (a later
   stage; not part of stage 1).
6. **Sources page**: not decided; left out for now.
7. **Library side**: the bound-name grammar (Appendix B) is to be written into the library's
   CONTRIBUTING (another agent is auditing library naming; the explorer does not edit the
   library). The inference must therefore stay robust to today's naming variants, such as tails
   spelled `measureReal_not_…_le_le` and `measureReal_…_gt_le`, and `measure_` beside
   `measureReal_`.
8. **Scope beyond probability**: facets are to be extended to deterministic results in a later
   stage. The statements table lists every member either way.

Stage 1 is therefore: the facet inference module and `facets.toml`; the statements table in
place of the Variant dropdown, with generated labels in the vocabulary above, driving the
statement, the explicit/asymptotic toggle and the graph focus; statement-level search hits and
deep links; the two merges with redirects; title normalisation; and the retirement of
positional `variant_labels`.

**Stage 1 status** (branch `feat/statements-table`, 2026-10-19): implemented as above, in
`facets.py`, `facets.toml`, `build.py` and `web/app.js`; see the README's "Result pages"
section. Two choices go slightly beyond the text of §4 C: the Lean, notes and references below
the table follow the selected row (instead of listing all members, which made the 10,000 px
panels), and a configured `primary` without an asymptotic form is honoured as the headline.
The audit script is not committed; its parser is the basis of `facets.py`. Library bold names
still say "average" (HMT 10.6) and "mean" in a few places; the explorer shows them as the
library's names of the statements and does not rewrite them.

---

## 1. What a reader comes to do

| # | Task | Example | Today |
|---|---|---|---|
| T1 | Best known bound for one question, with its hypotheses | "Expected spectral error of RSVD with a Gaussian sketch" | The bounds are split over two pages (`randomized-svd-expected-error`, `…-average-spectral-error`). The TW bound is option 4 of a dropdown labelled for Frobenius. |
| T2 | Compare all bounds for quantity X of algorithm Y | "HMT 10.6 vs TW 8.1 for spectral error" | You can't do it side by side. The incomparability note is under *Related*, 7,800 px down a 10,000 px panel. |
| T3 | Which sketch laws have a result of kind Z | "Which sketches have a tail bound for RSVD Frobenius error?" | Seven laws plus three interface-generic forms, all in `randomized-svd-tail`. The SRHT and both sampling bounds are not selectable. *Sketching › Trig* does not mention that RSVD has an SRHT bound. |
| T4 | What a theorem depends on | "What does TW 8.1 (spectral) use?" | The graph node is the whole result: the union over 17 members, 51 dependencies. Choosing a variant does not refocus the graph. |
| T5 | Find a theorem by its source | "Where is Tropp–Webber Theorem 8.1?" | Search finds the results, but never the declaration: members are not indexed as hits. Books covers three books; TW 2023 (143 citations, second most cited key) and HMT 2011 are papers and have no index. |
| T6 | Sample-size requirements | "Sketch size for (1+ε) Frobenius RSVD" | Rates answers this well for 50 of 61 asymptotic pairs. Tail pairs for RSVD/ETRSVD/Hutch++ and all spectral bounds are absent. |
| T7 | Browse a topic like a chapter | "Low-rank approximation, in reading order" | Works for the four curated collections. 211 results (60%) are browsable only by source module. |
| T8 | Cite or link a statement | "Link to the squared-spectral TW bound" | `#d/<name>` opens the result with that declaration scrolled to, but the Statement box still shows the primary. |

T1–T3 and T5 are the tasks the current architecture cannot serve, whatever the curation. They
need a statement-level unit with facets.

## 2. The current model

| Concept | To a reader | To an author | Source of truth | Remarks |
|---|---|---|---|---|
| **Topic / subtopic** | Top-level section of the catalogue | Library directory `NLAlib/<Layer>/<Sub>/` | Directory tree; titles in `topics.toml` | 10 topics. Breadcrumbs always follow the source module. |
| **Module (file)** | "File" page, with supporting API | A `.lean` file with `# Title` | Module docstring | Source browsing stays as a fallback. |
| **Collection / group** | Curated sections inside a topic ("Randomized SVD (RSVD) / range finder") | Hand list of result ids and definitions | `collections.toml` | Only LowRank, Sketching, Regression, Krylov. Low rank groups by algorithm, Sketching by law, so a bound like "RSVD with SRHT" fits neither. |
| **Result** | A "Theorem" page: title, statement, formal statements, graph, notes | `Result: <id>` line in docstrings; any number of declarations | Lean docstrings; title, aliases, primary from `results.toml` | 350 results, 1–29 members. Title from the most common bold name, or `results.toml` (38), or the humanized id (18). |
| **Form / Variant** | The dropdown above the statement; the *Explicit bound* toggle | An `Asymptotic:` link pairs an asymptotic theorem with its explicit target; `extra_forms` adds unpaired explicit members | Docstrings plus `results.toml` (`primary`, `extra_forms`, `variant_labels`) | Only 15 results have a dropdown. Labels are a positional hand list (15 lists), and the build fails if the count is off. |
| **Declaration** | "Formal statement" section (name, statement, Lean); lemma pages | Any public declaration | Extraction | Members of results are not search hits. `#d/` for a multi-result declaration (6) uses the first id. |
| **Definition** | Entry in catalogue and collections; dependency node | `def`/`structure`/`class` | Extraction (+ source bodies) | Support definitions (named constants) are hidden from headlines. |
| **Rates family / guarantee / row** | Filterable comparison of sufficient resources, rows linking to theorems | Hand row per theorem, with facet-like fields (`algorithm`, `variant`, `sketch`, `norm`, `mode`) and a reviewed `statement_hash` | `rates.toml` | 56 rows, 5 families, 15 guarantees. Only asymptotic pairs or `kind = 'exact'` rows. Already a faceted model, but hand-entered. |
| **Book** | Book chapter list, with results citing each numbered item | Citation `[Key, Theorem x]` in docstrings | `books.toml` + citations | Three books. Papers have no equivalent. |
| **Search** | Box on every page | Docstrings, names, aliases, `synonyms.toml` | Built index (`web/app.js`) | Ranks results, definitions, lemmas and files. Never a result member. |
| **Graph** | "Uses / used by" for the page | Proof dependencies | Extraction (`typeDeps`, `valueDeps`) | Nodes are results and definitions. A result node merges all its members (RSVD tail: 78 uses; median result: 7). |

Four places hold facet-like information about the same theorems and never meet:

- **Lean names:** `integral_specNorm_sub_rsvd_sq_le_of_hasLaw_gaussianMatrix`.
- **`variant_labels`:** "Spectral, squared (TW 8.1)".
- **`rates.toml` fields:** `norm = 'Frobenius squared'`, `mode = 'Expectation'`.
- **Collection groups:** by algorithm or by law.

---

## 3. Audit of the whole catalogue

All numbers come from the audit script (Appendix C). The tables are in Appendix A.

### (a) Members you cannot select as the statement

A member is *reachable* if it is one side of a form (a Variant dropdown option), or the single
statement of a result with no forms. Unreachable members still appear further down as
"Formal statements", with name, statement and Lean, but you cannot pick them as the statement
and nothing at the top says they exist.

- **144 of 350 results** have unreachable theorem members. That is **315 of 754 theorem
  memberships (42%)**:
  - 268 of them have their own bold name and 286 cite a source, so they are named theorems
    rather than helpers;
  - 132 are probabilistic bounds.
- By topic: LowRank 56% (121 of 215), Regression 57%, Estimation 50%, Matrix 39% (85 of 217),
  Sketching 35%, Krylov 31%. The problem is catalogue-wide; Low rank is where it hurts most.
- Largest: `randomized-svd-tail` 19 of 29 hidden; `randomized-nystrom-expected-error` 15 of 23;
  `randomized-nystrom-tail` 12 of 13; `davis-kahan` 9 of 10.
- 115 of the 144 have no forms at all, so their top box shows exactly one statement.
- The `extra_forms` stopgap (d58be0a) fixes 3 results by hand. Applying it everywhere would
  mean hand-listing about 300 declarations and their labels.

### (b) One question, several pages

The script groups probabilistic theorems by (algorithm, error measure, statistic), using facets
inferred from names. **44 such cells exist; 13 are split across 2–4 results.** Examples:

- RSVD × spectral × expectation: `randomized-svd-expected-error` (TW 8.1 squared; truncated
  output), `randomized-svd-average-spectral-error` (HMT 10.6 Gaussian and rotation-invariant;
  the HMT-style second moment) and `reverse-eckart-young`. **The two squared-spectral bounds,
  TW 8.1 and the HMT 10.6 form, are on different pages, though they bound the same
  quantity.**
- RSVD × Frobenius × tail: `randomized-svd-tail` (18), `randomized-svd-deviation-bound` (1),
  `etrsvd` (7), `early-truncation-pcp-bound` (1).
- RSVD × spectral × tail: `randomized-svd-tail` (TW 8.1 RSVD1) and
  `randomized-svd-deviation-bound` (HMT 10.8). Their docstrings say they are incomparable.
- GN × Frobenius × expectation over three results. Each of RBKI, RSI, NysBKI and NysSI is
  split into gapless and gapped results. That split is a legitimate facet (regime), but it is
  shown as two pages, not as a filter.
- **Authors already compare across these boundaries.** Docstrings contain 22 comparison
  pointers ("incomparable with `X`", "better when …"); 11 point at a declaration in another
  result.

### (c) Vocabulary

- **The same statistic has three names.** Titles say "expected" (6) and "average" (1, the HMT
  page). Bold names say expected (36), average (2), mean (8, partly for errors). Rates says
  "Expectation".
- **The squared forms have two names**: "Spectral, squared" on one page, "Second moment" on
  the other, in labels for bounds on the same quantity.
- **Tail statements have four names.** Titles say "tail" (12), "deviation" (2), "with high
  probability" (1); Rates mode says "High probability". The id `sketch-and-solve-ls` names a
  tail result after least squares; its sibling is `…-expected-error`.
- **Titles have four shapes**:
  - "The …": 121;
  - other noun phrase: 188;
  - "X: y": 23;
  - humanized ids: 18 ("Chebyshev extremal").

  RSVD alone shows "Randomized SVD: expected error", "The tail of the randomized SVD" and
  "Deviation bound for the Frobenius error of the randomized SVD".
- **"Error" vs "residual"** is used consistently by domain (approximation vs least squares and
  linear systems). Keep both, but let the error-measure facet say which norm.
- Exactly one title carries a source ("(HMT 10.6)"). It is the stopgap, and it is the only
  way a reader learns that the other page holds TW.

### (d) Results that mix algorithms, statistics, measures or laws

Of results with probabilistic members, 30 mix at least one facet: quantities 17, laws 14,
outputs 13, statistics 6, algorithms 2.

- `randomized-svd-tail`: 4 measures (Frobenius, spectral, Schatten, Gram form for every
  unitarily invariant norm), 12 laws, including interface-generic theorems ("any sketch with a
  subspace injection"), plus plain and truncated output.
- `randomized-svd-expected-error`: 4 measures, 2 laws, 2 outputs, and both first and second
  moments.
- `etrsvd`, `etgn`, `jl-moment-frobenius`, `intrinsic-matrix-bernstein`: expectation and tail
  bounds under one id. The ETRSVD dropdown reads "Expected error, Gaussian / Tail, CountSketch
  / …".
- `reverse-eckart-young` (RSVD and Nyström), `early-truncation-pcp-bound` (RSVD and GN): two
  algorithms.

Mixing is fine. It is what an algorithm page should do. The problem is that the only way to
navigate a mixed result is one linear dropdown.

### (e) Variant labels

- All 15 dropdowns have curated labels (commit 2778fc7). In 2 of them, 9 labels omit a facet
  that varies within the same dropdown:
  - in RSVD expected, "Truncated, Gaussian" and "Rotation-invariant" don't say Frobenius,
    while "Spectral, squared (TW 8.1)" doesn't say Gaussian;
  - in RSVD tail, "CountSketch" and "Sub-Gaussian" don't name a norm.
- "Truncated" means late truncation, but nothing says so; early truncation is a separate
  result.
- Labels mix three kinds of information (measure, law, source), in different orders on
  different pages.
- They are positional lists, so adding a form to the library breaks the explorer build until
  someone relabels. That is a safe failure, but recurring authoring work.

### (f) Other obstacles

- **Search** never returns a result member, since `buildIndex` skips declarations with a
  result id. "TW 8.1" and "Theorem 8.1" rank RBKI/RSI pages first and RSVD fifth or sixth.
  Even then, the reader lands on the Frobenius primary.
- **Graph**:
  - A result's node unions all its members (51 dependencies for RSVD expected error, 78 for
    RSVD tail).
  - The declaration-level graph is fixed on the overview; picking a variant does not move it.
  - Six declarations with two result ids attach to the first only.
- **Rates**:
  - 56 rows over 35 results; 72 of 499 probabilistic theorems are reachable.
  - All RSVD rows are expected squared Frobenius error.
  - 0 of 10 RSVD spectral theorems appear, since they have no asymptotic form.
  - 11 of 61 asymptotic pairs have no row: all RSVD, ETRSVD and sub-Gaussian tails,
    Hutch++ variance, and the three PCP sample sizes.
  - A row requires a hand summary and a hash, so coverage lags the library by construction.
- **Headlines that are not self-contained.** 20 result members, including the headline of
  `randomized-svd-tail`, open with "With the hypotheses of `X`". On a catalogue card or a
  table row they cannot be read alone.
- **Breadcrumbs** follow the primary's source module ("Low rank › Gaussian › The expected error
  of the Gaussian randomized SVD"), although 28 results span several modules.
- **Collections**: 6 results are listed in two groups. The Krylov and Low-rank collections both
  carry RBKI, which is intended but hand-maintained.

---

## 4. Alternative information architectures

### Where facet data can come from (shared by B and C)

The library names follow CONTRIBUTING §4: a name spells its conclusion, with `_of_<hypothesis>`
suffixes and Mathlib's measure-theory prefixes. Probabilistic bounds read like a grammar,
`[exists_forall_]<statistic>_<measure>_sub_[truncatedSVD_]<algorithm>[_sq]_<relation>_of_<law>`
(Appendix B). A second, independent source is each statement's library dependencies (`typeDeps`
in the extraction): `NLAlib.rsvd`, `NLAlib.gaussianMatrix`, `NLAlib.IsLeftUnitarilyInvariant`.

| Facet | Values (RSVD) | Source | Coverage on LowRank/Regression/Estimation members (218) |
|---|---|---|---|
| algorithm | RSVD, GN, Nyström, RBKI, RSI, NysBKI, NysSI, sketch-and-solve, Hutch++, … | algorithm definitions in `typeDeps`, refined by name (`rsvd_pow_mul` = RSI); value list = definitions already listed in collection groups | 213 (98%); name and `typeDeps` agree on all 210 where both apply |
| error measure | Frobenius, spectral, Schatten-p, nuclear, every UI norm (Gram form) | first norm head in the name | 209 (96%) |
| moment / power | E‖·‖ or E‖·‖² | `_sq` after the output | from the name |
| statistic | expectation, tail bound, variance, identity | prefix `integral_` / `measureReal_` / `measure_` / `variance_`; `_eq` | 100% of these prefixes |
| sketch law | Gaussian, Haar, rotation-invariant, sub-Gaussian, Rademacher, SRHT (±replacement), CountSketch, leverage / uniform sampling, "any sketch with P" | `_of_hasLaw_<law>`, `_of_isLeftUnitarilyInvariant`, interface namespace (`HasSubspaceInjection.`); cross-check `typeDeps` | 212 (97%); the rest are law-free (deterministic or any-law) |
| output | plain, late-truncated, early-truncated | `truncatedSVD_<alg>`, `IsBestRankApprox`, `earlyTruncated…` | from the name |
| regime | gapless, gapped | `singularGapRatio` | from the name |
| form | explicit, asymptotic | `exists_forall_` + `Asymptotic:` link | 100% |
| source | HMT 10.6, TW 8.1 (RSVD2), … | parsed citations (`ci`), short names from a key map | all cited members |
| comparisons | "incomparable with", "better when" | *Related* sentences that cite a declaration | 22 pointers today |

These stay correct as the library grows because they come from what authors already write.
The rest is explorer configuration:

- a short value map (token → label, e.g. `hasLaw_srht` → "SRHT");
- `facets.toml` overrides keyed by declaration name, for the 2–4% the grammar misses (e.g.
  `obliqueProjector` identities);
- a build warning listing unclassified probabilistic theorems, like the existing automatic
  "Other" group.

No docstring tag is needed. Library-side changes are optional and need the maintainer; see the
decisions in §5.

### A. Light: keep results, enforce a naming contract, merge

**Model.** One result per (algorithm, statistic):

- merge `randomized-svd-average-spectral-error` into `…-expected-error`;
- merge `…-deviation-bound` into `…-tail`.

Every member becomes a form. The dropdown gets a second selector for the error measure, and
labels are written to a fixed scheme, "E‖·‖₂², Gaussian · TW 8.1". Titles follow
"<Algorithm>: expected error / tail bounds / sample size". The build lints titles and labels
against a controlled vocabulary.

```
THEOREM  RSVD: expected error                       #r/randomized-svd-expected-error
also: HMT 10.5, HMT 10.6, TW 8.1 (RSVD2), TW 8.7   (absorbs …-average-spectral-error)
───────────────────────────────────────────────────────────────────────────────────────
Statement   Error [Spectral          ▾]   Variant [E‖·‖₂², Gaussian · TW 8.1      ▾]
                                                   E‖·‖₂,  Gaussian · HMT 10.6
                                                   E‖·‖₂,  rotation-invariant · HMT 10.6
                                                   E‖·‖₂², Gaussian · TW 8.1 (RSVD2)
                                                   E‖·‖₂², Gaussian · HMT 10.6 form
                                                   E‖·‖₂², late-truncated · Gaussian
  For a standard Gaussian n×ℓ test matrix X and k + 2 ≤ ℓ,
    E‖A − rsvd(A, X)‖₂² ≤ σ_k(A)² + k/(ℓ−k−1) · ‖A − ⟦A⟧_k‖_F²
  Incomparable with E‖·‖₂ (HMT 10.6): better for small k.
Formal statements (all 20) …
```

- **Pros:** small front-end change; ids and URLs mostly stay.
- **Cons:** you still compare by flipping a dropdown; T2 and T3 are still unanswered; the
  sketching-by-law view still cannot show RSVD bounds.
- **Authoring cost:** high and permanent. About 300 hand labels, re-curated on every library
  addition (unless they are generated from facets, which becomes C). Merges need either
  explorer-side `merge_into` entries or library retagging.

### B. Faceted bound catalogue

**Model.** The atomic unit is a **bound record**: one explicit theorem plus its asymptotic
companion, with the facets above. Pages are generated views over records:

- a **question view** (algorithm × measure × statistic), as a table with filters for the
  remaining facets;
- an **algorithm overview**: a matrix of measure × statistic with counts;
- a **law view** ("everything proved for SRHT"), giving Sketching its by-law browsing for
  free;
- a **source view** ("TW 2023": every theorem citing it, by theorem number).

Rates is the asymptotic-form view of the same records. Results survive only as aliases.

```
Low rank › RSVD › Spectral error › Expected            #q/rsvd/spectral/expected
Law [all ▾]  Output [all ▾]  Form [explicit ▾]                        6 bounds
┌───────┬──────────┬───────────────────────────────────────────────────┬──────────────┐
│ E of  │ Law      │ Bound  (k + 2 ≤ ℓ)                                │ Source       │
├───────┼──────────┼───────────────────────────────────────────────────┼──────────────┤
│ ‖·‖₂  │ Gaussian │ (1+√(k/(ℓ−k−1)))σ_k + e√((ℓ+k−1)/2)/(ℓ−k)·‖τ_k‖_F │ HMT 10.6 ◆   │
│ ‖·‖₂  │ rot.-inv.│ same bound                                        │ HMT 10.6     │
│ ‖·‖₂² │ Gaussian │ σ_k² + k/(ℓ−k−1)·‖τ_k‖_F²                         │ TW 8.1 RSVD2 ◆│
│ ‖·‖₂² │ Gaussian │ σ_k² + (σ_k√(k/(ℓ−k−1)) + c‖τ_k‖_F)² + σ_k²c²     │ HMT 10.6 form│
│ ‖·‖₂² │ Gaussian │ late-truncated output: σ_k² + k/(ℓ−k−1)·‖τ_k‖_F²  │ Gu 3.4       │
│ ‖·‖₂² │ Gaussian │ any best rank-k of the output: same bound         │ Gu 3.4       │
└───────┴──────────┴───────────────────────────────────────────────────┴──────────────┘
◆ incomparable (authors' note): TW better for small k / fast decay, HMT for large k / heavy tail
τ_k = A − ⟦A⟧_k.  Row ▸ opens statement, hypotheses, Lean, dependency graph of that theorem.
Same error, tail bounds (4) · Frobenius, expected (10) · No sample-size form yet
```

The Bound column is the docstring's display formula, extracted automatically; a row expands to
the full docstring.

- **Pros:** answers T1–T6 directly; stays correct automatically; one vocabulary, generated
  from facet values.
- **Cons:** the facets are thin for deterministic theory. Matrix (133 results), Krylov and
  Polynomial are named theorems ("Weyl's inequality", "Davis–Kahan") for which a table of
  facets is the wrong page. Losing the result page would lose identity, title and the curated
  collections there. It is also the largest front-end rewrite, and phone layouts need tables to
  collapse into cards.
- **Authoring cost:** low per theorem. About 200 lines of Python for inference and validation,
  about 500–700 lines of JavaScript for views, a ~30-entry value map, and a handful of
  overrides.

### C. Hybrid: facet index plus theorem pages (recommended)

**Model.** Keep the **Result** as the page for a named theorem or theorem family, with stable
ids, titles, collections and URLs. Add B's **bound records** and views, built for every theorem
with a statistic facet. Connect the two:

- **The result page shows a statements table, not a dropdown.** Every member is listed, grouped
  by error measure, with generated facet columns (moment, law, output, source). Selecting a
  row shows its statement and explicit/asymptotic toggle, and refocuses the graph.
  `variant_labels` and `extra_forms` become unnecessary for faceted results; keep them as
  optional overrides.
- **Each group header links to the question view** ("Compare all RSVD spectral expected bounds
  (6), across 3 results").
- **Algorithm overview pages** become the headline entries of collection groups.
- Law, source and Rates views as in B.

Result page (stage 1–2):

```
THEOREM  Randomized SVD: expected error            #r/randomized-svd-expected-error
17 statements · Gaussian, rotation-invariant · HMT 10.5, TW 8.1, TW 8.7
───────────────────────────────────────────────────────────────────────────────────────
Statements                                                       Form [explicit|O(·)]
 Frobenius                          compare all RSVD Frobenius expected bounds (10) →
   ● E‖·‖_F²  Gaussian            plain           HMT 10.5, TW 8.7      O(k/ε)
   ○ E‖·‖_F²  rotation-invariant  plain                                 O(k/ε)
   ○ E‖·‖_F²  Gaussian            late-truncated                        O(k/ε)
   ○ E‖·‖_F   Gaussian            plain (as printed)  HMT 10.5
   … 4 more
 Spectral                           compare all RSVD spectral expected bounds (6) →
   ○ E‖·‖₂²   Gaussian            plain           TW 8.1 (RSVD2)
   ○ E‖·‖₂²   Gaussian            late-truncated  Gu 3.4
   … 1 more
   ↳ also in "Randomized SVD: HMT 10.6": E‖·‖₂ Gaussian / rot.-inv., E‖·‖₂² HMT form
 Schatten p ≥ 2  ○ E‖·‖_{S_p}²  Gaussian  TW 8.1
 Every UI norm   ○ E Φ(EᴴE)     Gaussian, rotation-invariant  TW 8.1
───────────────────────────────────────────────────────────────────────────────────────
  There are absolute constants C, ε₀ > 0 such that … ℓ ≥ Ck/ε,
    E‖A − rsvd(A, X)‖_F² ≤ (1 + ε)‖A − ⟦A⟧_k‖_F²            [Explicit bound]
Graph (of the selected statement) · Notes · References
```

Algorithm overview (stage 2), the head of the "Randomized SVD" collection group:

```
RANDOMIZED SVD (RSVD)                          #a/rsvd     Low rank › Randomized SVD
rsvd(A, Ω) := P_{AΩ}A  ·  outputs: plain, late-truncated, early-truncated
                      Expected        Tail bound      Sample size (Rates)
  Frobenius           8  (+2 early)   16 (+5 early)   4 rows (+tails pending)
  Spectral            6               4               —
  Schatten p ≥ 2      1               1               —
  Every UI norm       2               6               —
Laws with a Frobenius tail bound: Gaussian · sub-Gaussian · CountSketch · SRHT ·
  leverage sampling · sampling w/o replacement · any OSI / subspace injection / JL-moment
Named theorems: HMT 10.5 · 10.6 · 10.7 · 10.8 · 11.2 · TW 8.1 (RSVD1, RSVD2) · TW 8.7
Shared theory: range-finder structural bound · truncation for free · …
```

Counts are from the inferred facets at a4f8773. Each number links to the question view.

- **Pros:**
  - fixes the RSVD case in stage 1 without moving any page;
  - keeps every URL and the library's `Result:` ids;
  - suits both deterministic theory (theorem pages, where the table just lists the
    members) and algorithm bounds (comparison views);
  - removes most per-form curation.
- **Cons:** two navigation layers to explain (theorem pages and comparison views). Facets on
  deterministic results stay sparse, but the table still lists every member, so (a) is fixed
  everywhere.
- **Authoring cost:** B's inference, plus a statements table instead of the dropdown.
  `results.toml` shrinks over time. Merging results becomes optional, not required.

---

## 5. Recommendation and migration

Adopt **C**. Stage it so that each step ships alone and leaves the site consistent.

| Stage | Ships | Changes | Library? |
|---|---|---|---|
| 0 | nothing visible | `build.py` infers facets per theorem from name + `typeDeps` + citations and emits them in `data.json`. Add a `facets.toml` value map and overrides, and a build warning listing unclassified probabilistic theorems. Commit the audit script and add facet tests. | no |
| 1 | **statements table** on every result page | Replace the Variant dropdown with the grouped table (all members, generated labels). The selected row drives the statement, the explicit/asymptotic toggle and the graph focus. `#d/<name>` selects that row. Search indexes members as hits, deep-linking to their row. `variant_labels`/`extra_forms` stay as overrides. | no |
| 2 | **comparison and algorithm views** | `#q/<alg>/<measure>/<statistic>` tables with remaining-facet filters. `#a/<alg>` overview pages, linked from collection groups. "Also in …" cross-result links in each table group. Phone layout: rows as cards. | no |
| 3 | **vocabulary and merges** | A controlled vocabulary for generated labels and for title overrides (decision 2). Optional explorer-side `merge_into` in `results.toml` (decision 3). A build lint on titles. Redirects for merged ids. | no; retagging is optional (decision 7) |
| 4 | **Rates from facets; Sources page** | Generate Rates family/guarantee/filter skeletons from the facets of every asymptotic pair. Curated `resources` + `statement_hash` remain a reviewed overlay. Pairs without one are listed as "summary pending" with the statement (decision 5). Add a Sources page for key papers (TW 2023, HMT 2011, Woodruff 2014, …) from citations, generalizing Books. | no |
| 5 | **library conventions** | Document the bound-name grammar (Appendix B) in CONTRIBUTING §4; ask for self-contained bound docstrings (no "With the hypotheses of `X`"). | yes, maintainer |

**`Result:` ids.** They stay what they are in the library: the literature-map keys and the
grouping authors choose. The explorer stops depending on a result's members sharing one
question, because comparison comes from facets. Any merge happens explorer-side, through an
alias in the existing `resultAlias` mechanism, which `showResult` already resolves. Library
retagging can follow at the maintainer's pace, or never.

**URLs.** Every existing route keeps working: `#r/<id>`, `#d/<name>`, `#m/<module>`,
`rates/#rate/<id>`, `books/#…`. A merged id redirects to its new page with the corresponding
row selected; the alias table records the target declaration. New routes are additive: `#q/…`,
`#a/…`, `#s/<bibkey>`, `#law/…`. Filter state goes in the query part (`?law=gaussian`), so
comparison views can be linked.

**Rates.** The page and its row URLs stay. Its curated content, resource summaries reviewed
against a hash, is the one thing facets cannot generate, so it becomes an overlay on generated
rows rather than the source of the rows. Existing `rates.toml` fields (`algorithm`, `variant`,
`sketch`, `norm`, `mode`) are checked against the inferred facets; disagreement fails the build,
which catches stale hand metadata. The 11 uncovered pairs appear as pending.

**What happens to the stopgap.** `extra_forms` in d58be0a is correct and can stay until stage 1.
After stage 1 the three RSVD entries are redundant and should be removed. The
"(HMT 10.6)" title can stay or become "Randomized SVD: expected spectral error, HMT 10.6"
under decision 2.

### Decisions for the maintainer

1. **Architecture**: C, or A (lighter, permanent label curation) or B (no result pages for
   bounds).
2. **Vocabulary**:
   - "expected error" everywhere, with "average" and "mean" retired for errors;
   - E‖·‖ vs E‖·‖² shown in symbols, not as "squared" or "second moment";
   - "tail bound" vs Rates' "high probability" for probability statements;
   - "late-truncated" instead of "truncated";
   - title shape: drop the leading "The" (121 titles; explorer override or library bold
     names?).
3. **Merges**:
   - merge `randomized-svd-average-spectral-error` into `randomized-svd-expected-error`;
   - merge `randomized-svd-deviation-bound` into `randomized-svd-tail`;
   - split `etrsvd` and `etgn` into expected vs tail;
   - or leave all ids as they are and rely on comparison views.
4. **Facet source of truth**: inference from names and dependencies plus explorer overrides (proposed), or
   a docstring tag in the library (more explicit, but every author has to write it).
5. **Rates coverage**: show asymptotic pairs without a reviewed summary as "pending", or keep
   them hidden until reviewed.
6. **Sources page** for papers next to Books, and which keys (proposal: the ten most cited).
7. **Library conventions** (other sessions own the Lean):
   - document the bound-name grammar in CONTRIBUTING §4, optionally with a CI check that the
     explorer's parser classifies every new bound;
   - require self-contained bound docstrings;
   - say whether `Result:` ids should eventually be retagged to match explorer merges.
8. **Scope beyond probability**: whether to extend facets to deterministic families, e.g. the
   norm facet for Davis–Kahan/Wedin variants, or the CG/MINRES/GMRES bound types. The
   statements table fixes their hidden members either way.

---

## Appendix A. Audit tables

### A.1 Results with the most unreachable members (top 15)

| result | title | unreachable / theorem members | forms |
|---|---|---|---|
| `randomized-svd-tail` | The tail of the randomized SVD | 19 / 29 | 7 |
| `randomized-nystrom-expected-error` | PSD Nyström: expected error | 15 / 23 | 4 |
| `randomized-nystrom-tail` | The tail of randomized Nyström | 12 / 13 | 0 |
| `generalized-nystrom-expected-error` | Generalized Nyström: expected error | 9 / 11 | 1 |
| `davis-kahan` | The Davis–Kahan sin Θ theorem | 9 / 10 | 0 |
| `etgn` | Early-truncated generalized Nyström | 8 / 10 | 1 |
| `randomized-svd-expected-error` | Randomized SVD: expected error | 8 / 17 | 6 |
| `gram-correspondence` | The Gram correspondence for block Krylov Nyström | 6 / 7 | 0 |
| `sketch-and-solve-ls` | Sketch-and-solve: relative residual with high probability | 6 / 10 | 2 |
| `sketch-and-solve-expected-error` | Sketch-and-solve: expected relative residual | 6 / 10 | 2 |
| `hutchpp-variance` | The exact variance of Hutch++ … | 5 / 7 | 1 |
| `filtered-range-finder-bound` | The filtered range finder in expectation | 5 / 6 | 0 |
| `reverse-eckart-young` | Reverse Eckart–Young for truncated Nyström | 5 / 6 | 0 |
| `range-finder-structural-bound` | The structural bound of the range finder | 5 / 6 | 0 |
| `etrsvd` | Early-truncated randomized SVD | 4 / 12 | 4 |

Totals: 350 results; 153 with more than one theorem member; 15 with a Variant dropdown, 23 with
exactly one form, 312 with none. Result sizes (members): 1: 194, 2: 81, 3: 31, 4: 18, 5–9: 16,
10+: 10.

### A.2 (algorithm, measure, statistic) cells split across results (all 13)

| algorithm | measure | statistic | results (members in cell) |
|---|---|---|---|
| GN | Frobenius | expectation | `etgn` (7), `generalized-nystrom-expected-error` (11), `tgn-expected-error` (4) |
| GN | Frobenius | tail | `etgn` (3), `early-truncation-pcp-bound` (1), `generalized-nystrom-tail` (5) |
| Hutch++ | trace | tail | `hutchpp-tail` (3), `hutchpp-relative-error` (2) |
| NysBKI | spectral | expectation | `nysbki-gapped-error` (2), `nysbki-gapless-error` (3) |
| NysSI | spectral | expectation | `nyssi-gapped-error` (2), `nyssi-gapless-error` (3) |
| Nyström | nuclear | expectation | `randomized-nystrom-expected-error` (12), `nystrom-two-eigenvalue-instance` (1) |
| Nyström | spectral | expectation | `randomized-nystrom-expected-error` (7), `reverse-eckart-young` (2) |
| RBKI | spectral | expectation | `rbki-gapped-error` (4), `rbki-gapless-error` (5) |
| RSI | spectral | expectation | `rsi-gapped-error` (4), `rsi-gapless-error` (5) |
| RSVD | Frobenius | expectation | `etrsvd` (3), `randomized-svd-expected-error` (11) |
| RSVD | Frobenius | tail | `randomized-svd-tail` (18), `randomized-svd-deviation-bound` (1), `etrsvd` (7), `early-truncation-pcp-bound` (1) |
| RSVD | spectral | expectation | `randomized-svd-expected-error` (2), `randomized-svd-average-spectral-error` (3), `reverse-eckart-young` (1) |
| RSVD | spectral | tail | `randomized-svd-tail` (3), `randomized-svd-deviation-bound` (1) |

### A.3 Every RSVD spectral-norm bound (plain and late-truncated output)

| E of / event | law | output | source | result | selectable today? |
|---|---|---|---|---|---|
| E‖·‖₂ | Gaussian | plain | HMT 10.6 | `…-average-spectral-error` | yes |
| E‖·‖₂ | rotation-invariant | plain | HMT 10.6 | `…-average-spectral-error` | yes |
| E‖·‖₂² | Gaussian | plain | TW 8.1 (RSVD2) | `…-expected-error` | yes, since d58be0a |
| E‖·‖₂² | Gaussian | plain | HMT 10.6 form (`_pinvSpecNormBound`) | `…-average-spectral-error` | yes |
| E‖·‖₂² | Gaussian | late-truncated | Gu 3.4; TW p. 42 | `…-expected-error` | no |
| E‖·‖₂² | Gaussian | any best rank-k of the output | Gu 3.4 | `…-expected-error` | no |
| tail of ‖·‖₂² | Gaussian | plain | TW 8.1 (RSVD1) | `…-tail` | yes |
| tail of ‖·‖₂² | Gaussian | late-truncated | | `…-tail` | no |
| tail of ‖·‖₂² | Gaussian | any best rank-k of the output | | `…-tail` | no |
| tail of ‖·‖₂ | Gaussian | plain | HMT 10.8 | `…-deviation-bound` | no (no forms) |
| tail of ‖·‖₂² | any subspace injection | plain | | `…-tail` | no |

These are eleven theorems on three pages, plus a combined spectral-and-Frobenius bound in
`reverse-eckart-young`. None is on Rates. The script's name-only count is 10: it misses the
two `IsBestRankApprox` forms and counts the `reverse-eckart-young` one.

### A.4 Vocabulary counts

| word | in result titles | in members' bold names |
|---|---|---|
| expected / expectation | 6 | 36 |
| average | 1 | 2 |
| mean | 2 (both non-error) | 8 |
| tail | 12 | 35 |
| deviation | 2 | 5 |
| high probability | 1 | 4 |

Rates' guarantee mode uses "Expectation" (31 rows) and "High probability" (19). Title sources:
docstring bold name 294, `results.toml` 38, humanized id 18.

### A.5 Results mixing facets (top 10 of 30)

| result | mixes |
|---|---|
| `randomized-svd-tail` (29 prob. members) | 4 measures, 12 laws, 2 outputs |
| `randomized-nystrom-expected-error` (23) | 5 measures, 2 laws, 2 outputs |
| `randomized-svd-expected-error` (17) | 4 measures, 2 laws, 2 outputs, both moments |
| `randomized-nystrom-tail` (13) | 4 measures, 4 laws, 2 outputs |
| `etrsvd` (12) | expectation + tail, 5 laws, 2 outputs |
| `etgn` (10) | expectation + identity + tail, 4 laws |
| `sketch-and-solve-expected-error` (10) | identities and bounds, 2 laws |
| `rbki-gapped-error`, `rsi-gapped-error` (9 each) | 3 measures, both moments, 2 outputs |
| `reverse-eckart-young` (4) | RSVD and Nyström |
| `early-truncation-pcp-bound` (2) | RSVD and GN |

## Appendix B. Bound-name grammar used for inference

```
[exists_forall_]                       asymptotic form (O(·)), with an Asymptotic: link
(integral | measureReal[_not] | measure | variance)_
                                       statistic: expectation | tail | tail | variance
[abs_ | norm_]
<measure>_                             frobNorm | specNorm | schattenNorm | nuclearNorm |
                                       matrixNorm[_conjTranspose_mul_self] (Gram form) | quadForm | trace
sub_[mul_][truncatedSVD_]              late truncation when truncatedSVD_ precedes the algorithm
<algorithm>                            rsvd | rsvd_pow_mul (RSI) | rsvd_aeval | earlyTruncatedRSVD |
                                       generalizedNystrom | earlyTruncatedGeneralizedNystrom | nystrom |
                                       nystrom_pow_mul (NysSI) | rbki | nystromBKI | sketchAndSolve | hutchpp |
                                       girardHutchinson
[_sq]                                  E‖·‖² (second moment) rather than E‖·‖
_(le | eq | gt_le | le_le | …)         bound, identity, or tail event
[_singularGapRatio | _one_add_mul | _mul_exp | …]  regime and bound shape
_of_<law>[_of_<hyp>…]                  hasLaw_gaussianMatrix | hasLaw_haarFrame | isLeftUnitarilyInvariant |
                                       isSubgaussianVector | hasLaw_countSketch | hasLaw_srht[WithReplacement] |
                                       hasLaw_samplingSketch[WithoutReplacement] | hasLaw_rademacherMatrix
Namespace prefix                       HasSubspaceInjection. | IsObliviousSubspaceInjection. | HasJLMoment. |
                                       HasProjectionCostPreserving. → "any sketch with property P"
```

Cross-checks:

- the algorithm and law must appear among the statement's `typeDeps`;
- `rates.toml` fields must agree with the inferred facets;
- the measure is the first norm in the name (the conclusion's left side). `typeDeps` also
  contains the norms of the right side, so it cannot supply the measure.

Known misses, which go in `facets.toml`:

- `IsBestRankApprox` forms without an algorithm token (`typeDeps` recovers them);
- `obliqueProjector` identities;
- two-norm sums in `reverse-eckart-young`;
- law-free Hutch++/Girard–Hutchinson tails.

## Appendix C. Reproducing the audit

The script and its outputs are in the session scratchpad (temporary; stage 0 proposes
committing the script as `scripts/audit_ia.py`):

```
/tmp/claude-1000/-home-tyler-Documents-NLA-lib/bfb769ef-6d07-45c0-88a2-1c5dcd237c2b/scratchpad/explore-audit/audit.py
python3 -I audit.py <site>/data.json ~/Documents/NLA-lib/explore > report.md   # also writes facets.json
```

It needs a site built from `feat/result-extra-forms` (d58be0a) and extraction a4f8773.
`cdp-run.mjs` in the same directory drove the browser checks: search queries, page heights and
section offsets on `#r/randomized-svd-expected-error` (panel 10,161 px; TW spectral section at
2,254 px; *Related* at 7,798 px), and the Low rank › RSVD group listing.
