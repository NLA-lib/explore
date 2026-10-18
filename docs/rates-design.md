# Rates and algorithm-oriented exploration

The dated sections record successive changes. The latest sections, **Exact rows: trace estimation (2026-10-18)** with its two dated follow-ups, describe the current completed extension. Earlier dated sections record its predecessors, preparation and preceding schema changes.

Approved 2026-10-16. Presentation only; no mathematical declarations or import paths change.
The library checkout has ongoing Lean development, so implementation and validation use its
published extraction at 50a4bf4616fdb8968f0d0169bd3a34519d7de2dc. All edits belong to the
explorer; the organisation homepage receives only the new navigation link.

## Data and presentation

`rates.toml` has an ordered list of families and theorem-specific comparison rows. The initial
families are embeddings/sketch properties and one- and two-pass low-rank approximation. Family
labels, subject-column labels and resource lists are data, so future algorithm families do not
require another navigation page or a proliferation of table columns. Curated summaries retain
norm powers, probability quantifiers, normalization and domain restrictions. Full statement views
reuse the exact source docstring and its existing explicit/asymptotic relationship.

Each row resolves to two proved declarations and a result page. A hash of its asymptotic signature
and docstring forces a review after a statement change; this check cannot establish the mathematical
correctness of the human summary. Hashes exclude HTML comments (including value markers). The
catalogue has no inferred runtime, pass-count, or unproved rate. Source metadata is curated here
for this pass to avoid edits to Lean files currently owned by another agent.

`collections.toml` gives results and definitions a browsing location independent of their source
module. Result IDs and declaration routes are unchanged. Shared results may occur in several
collections; unclassified new results and concepts in a configured topic stay visible in an
automatic fallback group. Module browsing and source breadcrumbs remain available. Explicit
preferred declarations in `results.toml` choose the headline and paired overview deliberately.

## Validation contract

Builds reject invalid references, stale rate hashes, unproved or unpaired rates, invalid preferred
declarations, duplicate entries within a group and duplicate collections for the same topic.
Absent configuration remains supported. Tests cover metadata resolution, source navigation,
source-preserving grouping, browser filtering and statement toggles. Every initial rate is checked
against the published theorem, including each row's domain and normalization.

Read-back: the early-truncated GN entry averages over two independent standard Gaussian matrices,
with range size O(k/epsilon squared) and co-range size O(k/epsilon), and bounds expected squared
Frobenius error by (1+epsilon) times the optimal squared rank-k error. The conditional-on-range
identity remains available among the result's formal statements. JL rows concern one fixed vector;
subspace rows concern all vectors in a fixed subspace, not all subspaces simultaneously.

No prototype dispositions change and no library ledger/status edits or Lean builds are required.

## Validation read-back (2026-10-16)

The published snapshot builds with 28 Rates entries (17 sketch properties, 11 low-rank), two
families and four algorithm/theory groups. All 21 LowRank result IDs are covered. Fifteen backend
regression tests pass, including future-entry fallback and invalid metadata rejection. JavaScript
syntax and whitespace checks pass. An independent mathematical review checked every comparison
against the published theorem and its hypothesis interfaces.

Chrome exercised all 28 asymptotic/explicit pairs, their exact declaration and commit-pinned
source links, combined filters, search, empty-state reset, rate deep links, the GN headline,
source breadcrumbs and Books navigation. Viewport widths 800, 390 and 320 have no page overflow;
no browser or KaTeX errors occurred. Desktop and mobile screenshots were inspected. Detailed
logs and screenshots are in `/tmp/nlalib-rates-*` in the implementation session.

No Lean source, library extraction workflow, port status or ledger file was edited. The initial
metadata covers the published snapshot; future asymptotic results need a reviewed Rates entry.
Collections automatically retain new topic results while awaiting classification. Rates hashes
intentionally require review when an existing rate theorem's signature or prose changes.

## Family filters, sketch classes and probability notation (2026-10-16)

Each family declares its own ordered filter schema. The all-families view only exposes Family
and search; a selected family supplies its field labels and option order. Options come from
compatible rows in that family; constant fields are hidden. Family changes clear dependent
selections. Arbitrary scalar metadata, such as a future preconditioner field, works without new
frontend code. Norm, probability mode, sketch and variant are optional row fields: families that
do not use them need no placeholder. Build validation checks every configured filter against
its family's rows, while allowing an ordering list to include currently absent options.

Sketch browsing uses Gaussian, Haar, Sparse, Trig and Other, with separate shared theory. The same
classes are filter values on Rates. Trig is the requested presentation label for Fourier/Hadamard
transforms such as SRHT. Other includes row sampling, dense Rademacher sketches and distribution
classes such as sub-Gaussian or general rotation-invariant laws; it does not claim those classes
are disjoint mathematical sets. A theorem for a general invariant law stays in Other rather than
being presented as a Haar-only result. Distribution-specific variants retain their exact names.

Displayed probabilities use mathbb P and square event brackets. Rates rows explicitly state
success or failure events. The renderer converts recognized older probability operators and round
event delimiters, retaining nested event expressions, conditioning and delimiter sizes. It does
not rewrite plain matrix P, text/code or malformed input. All 72 probability math spans in the
published snapshot were audited: 64 changed typography, none retained a recognized round event
delimiter, and all rendered successfully. Lean source remains untouched; CONTRIBUTING §6 records
the convention for newly written docstrings.

## Preparing the source-library reorganization

A source reorganization is worthwhile: Haar, Rademacher and general sub-Gaussian results should
not be filed under Gaussian. The following is a migration direction, not a proof-stage design:

| Current home | Recommended topic home |
|---|---|
| Sketching/Gaussian/Haar and HaarEmbedding | Sketching/Haar, by JL and embedding topic |
| Sketching/Gaussian/Rademacher | Sketching/Rademacher |
| Sketching/Gaussian/SubGaussian | Sketching/SubGaussian |
| Sketching/Gaussian/LeastSquares | Separate law-specific facts into their Gaussian and Haar homes; review shared identities by mathematical subject |
| Sketching/Structured | Retain Structured for Fourier/Hadamard transform sketches |
| Sketching/Sampling, Sparse, Properties | Retain these mathematical topics |

"Trig" and "Other" are browse labels, not proposed permanent Lean directory names. A later source
move should preserve declaration namespaces and Result IDs wherever only placement changes.
Presentation metadata uses these stable names rather than module paths. Source links are rebuilt
from each extraction's module paths and line ranges. No module names are embedded in a Rates row
or collection membership; only the top-level topic controls automatic unclassified-result discovery.

A permanent regression moves a configured theorem from Sketching/Gaussian/Haar to
Sketching/Haar/Embedding and shifts its lines. It checks unchanged Rates hashes and resolution,
headline selection, collection membership and fallback discovery, while source paths and lines
follow the new module. Renaming a public declaration is a separate API change and requires updating
its explicit metadata references; a file move alone does not.

Follow-up validation: 19 backend regressions pass, including custom family fields, optional
norm/sketch metadata, filter order and module relocation. Dependency-free Node probability tests
pass; CI runs them. Chrome checks all 28 explicit views, family switching, compatible filter
options, ordering of the five sketch classes, reset/deep-link behavior, a synthetic future solver
family with a preconditioner filter and no norm or sketch, and 800/390/320-pixel layouts. The
six Sketching browse sections are present. Browser and probability rendering checks pass.


## Shared guarantees and Regression (2026-10-16)

The comparison hierarchy is family → guarantee → distribution/algorithm. `rates.toml` now
owns seven ordered guarantees: distributional JL, oblivious and fixed-subspace embedding,
oblivious and fixed-subspace injection, expected squared Frobenius relative error, and expected
nuclear relative error for PSD matrices. Each row references a guarantee ID in its own family.
The compact mathematical heading is always visible; the complete guarantee and its formal
definitions appear once in a disclosure. Per-row resources and parameter restrictions stay
visible. The family can choose which scalar field names a row (`subject_field`, default
`algorithm`), so sketch-property comparisons lead with the distribution rather than repeating
the guarantee on each row. Existing family-dependent filters remain configurable.

OSI is square-integrable entries together with E[SᴴS] = I and the lower-tail property on every
fixed subspace of dimension at most d. Leverage-dependent sampling results that conclude only
`HasSubspaceInjection` are grouped separately; they are not presented as OSI. The distinction
between fixed-subspace embedding and OSE is likewise explicit. All displayed probabilities
retain mathbb P and square brackets. Low-rank guarantees distinguish expected squared Frobenius
error from expected nuclear error; output-rank restrictions remain in each row.

Guarantees link to their property definitions. Rows have direct algorithm/property and sketch
links resolved from declaration names; distribution classes link to their defining interface.
The former ambiguous `Link` was a row permalink. `Copy link` now copies that same stable rate
URL, reports success accessibly, and shows a copyable URL when clipboard access is unavailable.

Regression is an Explorer peer of Sketching and Low-rank, organized into sketch-and-solve,
sketch-and-precondition, and least-squares foundations. Its collection links existing Result IDs
and definitions, including Matrix foundations that retain their mathematical home. Explicit
classification elsewhere suppresses automatic fallback duplication; intentional cross-links
remain possible. A configured collection may introduce a topic before the corresponding source
directory exists. This lets the same Explorer metadata work before and after the separate library
migration to `NLAlib.Regression.{Embedding,Oblique,Oblivious,SketchAndSolve}`. Module navigation
and source URLs still come from the actual extraction, without path overrides. At that checkpoint there were no regression asymptotic corollaries, so no Regression rate rows
were added until the subsequent proof stage described below.

The current published extraction is dc71a3c26ae48e78b7741e3218f188aede15a988. All 28 existing
Rates theorem hashes are unchanged and validate against it. The source migration preserves
all mathematical declarations; its design and Lean checks are recorded separately in the
library's `docs/design/Regression-Organization.md`. The earlier proposed split of the mixed
Gaussian/Haar least-squares module is superseded by its whole-file move to Regression.

Validation for this follow-up: 22 Python regression tests, the Node probability-formatting tests,
JavaScript syntax checks and a complete build against the current published extraction pass.
Chrome checked all 28 explicit/asymptotic views, all seven shared guarantees and their definition
links, clipboard success and denied-access fallback, family-dependent filters and custom fields,
search/reset/deep links, and Regression as a peer collection. Rates and expanded Regression have
no page overflow at 320, 390 and 800 pixels; long catalogue equations scroll within the reading
column. Screenshots were inspected. Independent placement and implementation reviews approved.

## Regression Rates preparation (2026-10-16)

The staged Regression family reuses the existing family → guarantee → rows layout. It leads
with the sketch and configures sketch class, sketch and guarantee mode as its facets. All
planned rows use squared Frobenius residual error, so a norm facet would add no choice. The
algorithm definition is `NLAlib.sketchAndSolve`; sketch-definition links will identify the exact
Gaussian, Haar or CountSketch object used by each proved statement.

The common comparison quantity is
$\operatorname{OPT}_{\mathrm{LS}}^2=\min_{\mathbf{Y}}\|\mathbf{B}-\mathbf{A}\mathbf{Y}\|_{\mathsf{F}}^2
=\|(\mathbf{I}-\mathbf{A}\mathbf{A}^{+})\mathbf{B}\|_{\mathsf{F}}^2$,
with fixed real inputs and $\widehat{\mathbf{X}}=(\mathbf{S}\mathbf{A})^{+}\mathbf{S}\mathbf{B}$.
One shared guarantee bounds the expectation of the squared residual by
$(1+\varepsilon)\operatorname{OPT}_{\mathrm{LS}}^2$; a second bounds that residual with probability
at least $1-\delta$. Input quantifiers are per fixed pair, with randomness over the sketch.
Visible row notes will carry the exact theorem's rank restrictions, parameter domains,
normalization and Haar ambient-size cap.

Preparation checkpoint (now completed): the family and two guarantees were drafted using existing
algorithm and least-squares definitions. The four new rows were held back until their signatures,
proofs and fresh extraction were complete. No placeholder hashes or result primaries were used.
Their resource rates were then read from the completed statements; the final validation is below.

Deployment order is a dependency of this change. Merge the library theorem changes first and
wait for the rolling `explore-data` release to publish their fresh extraction, commit and source
hash manifest. Then review all four asymptotic/explicit pairs and their parameter conditions,
record their signature/docstring hashes, and merge/deploy the explorer metadata. Strict
reference, proved-pair, source-fingerprint and rate-hash validation stays enabled throughout.
Explorer unit tests can pass on a metadata PR before the new library release exists; they do
not establish that a deployment build against the currently published extraction will succeed.
A local integration preview may use the final uncommitted extraction and its matching source
bytes, but publication must wait for the library release. Its public source links become accurate
only after extraction records the committed source revision.


### Locked Regression row plan

The approved library note `Regression-Rates.md` fixed the four rows below before implementation. Here
$r=\operatorname{rank}\mathbf{A}$, $s$ is the sketch row count and the stated resources are
sufficient thresholds. Their active metadata and hashes were added only after proof completion and fresh extraction.

| Planned row id | Sketch / mode | Sketch rows $s$ | Visible conditions |
| --- | --- | --- | --- |
| `regression-expected-gaussian` | Gaussian / Expectation | $O((r+1)/\varepsilon)$ | Real inputs; unnormalized standard Gaussian sketch; sufficiently small positive epsilon; rank deficiency allowed. |
| `regression-expected-haar` | Haar / Expectation | $O((r+1)/\varepsilon)$ | Real inputs; sketch is the adjoint of a Haar frame; $s\le m$; sufficiently small positive epsilon. |
| `regression-high-prob-gaussian` | Gaussian / High probability | $O((r+1)/(\varepsilon\delta))$ | Real inputs; unnormalized standard Gaussian sketch; $0<\delta\le1/2$; second-moment sufficient rate. |
| `regression-high-prob-countsketch` | CountSketch / High probability | $O(((r+1)^2+(r+1)/\varepsilon)/\delta)$ | Real or complex inputs; unscaled one-sign-per-column sketch; $\delta>0$; sufficiently small positive epsilon. |

The expected asymptotic names are
`NLAlib.exists_forall_integral_frobNorm_sub_mul_sketchAndSolve_sq_le_of_hasLaw_gaussianMatrix`
and `NLAlib.exists_forall_integral_frobNorm_sub_mul_sketchAndSolve_sq_le_of_hasLaw_haarFrame`.
Their explicit names replace `exists_forall_integral` by `integral` and `_sq_le_of_` by
`_sq_le_one_add_mul_of_`. Their existing Result id remains `sketch-and-solve-expected-error`.
The intended primary is
`NLAlib.integral_frobNorm_sub_mul_sketchAndSolve_sq_le_one_add_mul_of_hasLaw_gaussianMatrix`.

The high-probability asymptotic names are
`NLAlib.exists_forall_measureReal_frobNorm_sub_mul_sketchAndSolve_sq_gt_le_of_hasLaw_gaussianMatrix`
and `NLAlib.exists_forall_measureReal_frobNorm_sub_mul_sketchAndSolve_sq_gt_le_of_hasLaw_countSketch`;
the explicit names omit `exists_forall_`. Their Result id remains `sketch-and-solve-ls`, with
the Gaussian explicit theorem as intended primary. Existing identities and generic forms stay
in both results. The strict failure event is residual squared **greater than**
$(1+\varepsilon)\operatorname{OPT}_{\mathrm{LS}}^2$, so its complementary success statement
uses a non-strict upper bound, including when the optimal residual vanishes.

These names and summaries were compared to the completed extracted signatures and proof status
in the final validation below. In particular, Gaussian probability normalization must not be inserted into the
algorithm shown by its theorem, and CountSketch's complex-field support must not be lost in a
family-wide real-only convention. A Gaussian logarithmic-in-failure rate is not claimed.


## Regression Rates validation

The four planned Regression rows are now populated from the completed extracted declarations.
There are 32 rows, nine shared guarantees and three families. Both regression Result groups use
the new Gaussian explicit relative-residual declaration as their preferred primary; their Haar,
CountSketch, exact-identity and generic formal statements remain accessible. The earlier
preparation statements about absent rows are superseded by this section.

Read-back from the final signatures: for every fixed real input pair, Gaussian sketch-and-solve
with $s\ge C(r+1)/\varepsilon$ bounds the expected **squared** Frobenius residual by
$(1+\varepsilon)$ times the optimal squared least-squares residual. Haar has the same sufficient
threshold using the adjoint frame and retains $s\le m$. The Gaussian high-probability theorem
uses an unnormalized standard Gaussian sketch and sufficient
$s\ge C(r+1)/(\varepsilon\delta)$, with $0<\delta\le1/2$. CountSketch is unscaled,
works over any `RCLike` field, and uses
$s\ge C((r+1)^2+(r+1)/\varepsilon)/\delta$ with $\delta>0$. All four use sufficiently
small positive epsilon, absolute constants before every dimension and input, arbitrary matrix
right-hand sides, and rank-plus-one thresholds that include rank zero. Both high-probability
statements bound the **strict** failure event above $(1+\varepsilon)$ times the optimum by
$\delta$. The earlier real-only wording applies to expectation and Gaussian rows; CountSketch
also permits complex inputs.

Validation used `/tmp/nlalib-regression-rates-explore.json` (301 listed modules, 3466 public
declarations) and matching extraction-time source bytes from NLAlib. The source manifest validated
before 167 definition bodies were enriched; the explorer displays 300 modules because the root
aggregator is not a topic module. All 28 previous Rates rows remain unchanged. Four new hashes
were computed from the fresh signature/docstring bytes, with only HTML comments removed, and the
strict builder accepted every pair and preferred primary. The final extraction records committed library revision
`b66e36e811709491eb8d5e5a54e891a3c173032d`; source fingerprints and the four theorem hashes remain unchanged from the
validated local snapshot. The preview was rebuilt with this committed revision so source links
identify the new theorem versions. Publish this library revision before explorer deployment.

All 22 Python regressions, Node probability tests and JavaScript syntax checks passed. Chrome
checked all 32 explicit/asymptotic row views, all nine guarantee groups and definition links,
Regression's four rows and expectation/high-probability filters (two each), and Gaussian/Haar/
CountSketch filters (two/one/one). Clipboard success/fallback, search/reset, hidden-row deep links,
custom family facets, existing collection/source breadcrumbs and Regression peer browsing passed.
Every family's expanded guarantees and notation, plus expanded Regression catalogue content,
stayed within the page at 320, 390 and 800 pixels; no browser or KaTeX errors were observed.
Desktop and expanded mobile Regression screenshots were inspected. No frontend or validation
changes were needed for the new family. Publication order remains library merge and fresh
rolling-release extraction first, explorer metadata merge and deployment second.


## Block Krylov and subspace iteration Rates (2026-10-18)

Maintainer request, for the block Krylov round: "add to the explorer rates page too". The scope
is low-rank approximation only; the Krylov linear-system solvers (CG, MINRES, GMRES) keep no
Rates rows, as requested earlier. A fourth family, `low-rank-krylov`, follows the existing
family → guarantee → rows layout with no frontend or validation change. Its resource is depth:
blocks $q$ for RBKI and block Krylov Nyström, power steps $p$ for subspace iteration and Nyström
subspace iteration; the notation records Tropp and Webber's product counts ($2q$, $2p+2$, $q$,
$p+1$). Facets are algorithm, spectral gap (Gapless/Gapped), variant (Basic/Late truncation) and
norm; sketch (standard Gaussian, unnormalized) and mode (expectation) are constant, so hidden.

Every row resolves to a proved `exists_forall_` corollary paired with its explicit theorem. Only
one existed (truncated RBKI, Musco–Musco form), so the library branch `krylov/block` adds
seventeen corollaries in the files of their explicit theorems (`LowRank/Gaussian/BlockKrylov.lean`,
`BlockKrylovGapless.lean`, `NystromBlockKrylov.lean`), recorded in the library's
`docs/design/Krylov-Block.md`. Each concludes relative error $1+\varepsilon$ in its theorem's own
norm and power, with absolute constants before every dimension and $0<\varepsilon\le\varepsilon_0$:

| Guarantee | Rows (algorithm · gap · variant) | Sufficient depth |
| --- | --- | --- |
| $\mathbb{E}\lVert\mathbf{A}-\widehat{\mathbf{A}}\rVert_2^2\le(1+\varepsilon)\sigma_r^2$ | RBKI gapless basic (TW 9.1) | $q=O(\log(n+1)/\sqrt{\varepsilon})$ |
| same | RBKI gapless late (MM ε-form) | $q=O(\log(n/\varepsilon)/\sqrt{\varepsilon})$ |
| same | RSI gapless basic (TW 9.1) | $p=O(\log(n+1)/\varepsilon)$ |
| same | RSI gapless late (MM ε-form) | $p=O(\log(n/\varepsilon)/\varepsilon)$ |
| same | RBKI gapped basic, late (TW 9.2) | $q=O(\log(n/\varepsilon)/\sqrt{\gamma})$ |
| same | RSI gapped basic, late (TW 9.2) | $p=O(\log(n/\varepsilon)/\gamma)$ |
| $\mathbb{E}\lVert\mathbf{A}-\widehat{\mathbf{A}}\rVert_{\mathsf{F}}^2\le(1+\varepsilon)\lVert\mathbf{A}-\llbracket\mathbf{A}\rrbracket_r\rVert_{\mathsf{F}}^2$ | RBKI, RSI gapped basic, late | as the gapped spectral rows |
| $\mathbb{E}\lVert\mathbf{H}-\widehat{\mathbf{H}}\rVert_2\le(1+\varepsilon)\sigma_r(\mathbf{H})$ | NysBKI, NysSI gapless basic (TW 9.1, Nyström-native) | as RBKI, RSI gapless basic |
| same | NysBKI, NysSI gapped basic | as RBKI, RSI gapped |
| $\mathbb{E}\lVert\mathbf{H}-\llbracket\widehat{\mathbf{H}}\rrbracket_r\rVert_*\le(1+\varepsilon)\lVert\mathbf{H}-\llbracket\mathbf{H}\rrbracket_r\rVert_*$ | NysBKI, NysSI gapped late | as RBKI, RSI gapped |

Read-back. All inputs are real and fixed before the draw; the test matrix is $n\times\ell$
standard Gaussian with $\ell\ge r+2$; expectations are of the squared error for general
matrices and of the unsquared spectral or trace error for Nyström. Singular values are indexed
from $0$, so $\sigma_r$ is the best rank-$r$ spectral error. Gapped rows take a head of $r\ge1$
singular values, a tail index $r\le t\le\ell-2$, and
$\gamma=(\sigma_{r-1}-\sigma_t)/(\sigma_{r-1}+\sigma_t)>0$ (the corollaries assume
`0 < singularGapRatio A h t`, since at $\gamma=0$ Lean's $x/0=0$ would make the threshold
vacuous); Nyström gaps use the eigenvalues of $\mathbf{H}$. Tails are bounded through the
dimension, $\tfrac{t}{\ell-t-1}\|\mathbf{A}-\llbracket\mathbf{A}\rrbracket_t\|_{\mathsf{F}}^2\le
n^2\sigma_r^2$, which is where $\log n$ enters; $n$ is the number of columns. The Tropp–Webber
gapless forms bound the tail ratio by $1+n^2$, so they need no $\log(1/\varepsilon)$, and their
corollaries drop the explicit theorems' $\sigma_r>0$ (at $\sigma_r=0$ the $(1+\varepsilon)$ form
gives error $0$); the $\log(n+1)$ is literal, not a rewritten $\log n$. The untruncated
Musco–Musco forms are dominated in rate by these and have no row. Not proved, so absent: gapless
Frobenius bounds (MM Theorem 11), gapless truncated Nyström, and spectral truncated Nyström. No
probability rows: every theorem is in expectation. Output ranks in the notes ($\le q\ell$,
$\le\ell$, $\le r$) come from the definitions, not from the rate theorems.

Presentation. Result titles (`results.toml`) name each Result id by algorithm and regime, since
the first declaration's bold name covered only one form; primaries are the Tropp–Webber
statements (Theorem 9.1 for gapless, the spectral Theorem 9.2 line for gapped). The low-rank
collection is retitled "Randomized low-rank approximation" (id unchanged) and gains groups
"Randomized block Krylov and subspace iteration" and "Block Krylov and subspace iteration Nyström",
which absorb the round's ten previously unclassified LowRank results and two definitions;
`generalized-nystrom-tail`, also unclassified, joins Generalized Nyström. The Krylov collection
lists `blockKrylovMatrix` and `blockKrylovSpace` with the Krylov spaces and cross-lists RBKI and
NysBKI in a last group. The Sketching fallback group (projection-cost-preserving results) is
unchanged and outside this pass.

Validation used a local extraction of `krylov/block` at 5fd9e14 (now c04601b, below), which contains the corollaries
(352 modules, 4043 declarations), with matching source bytes; the strict builder accepted all 50
rows (18 new; the 32 earlier hashes unchanged), every preferred primary and every collection
reference, with no LowRank or Krylov fallback group left. All 162 math spans of the new family,
guarantees and rows render under KaTeX. The 22 Python tests, Node probability tests and
JavaScript syntax checks pass. No browser pass was made in this session. Deployment order as
before: merge the library corollaries and wait for the rolling `explore-data` release (the
header comment of `rates.toml` names the reviewed revision), then merge the explorer metadata.

Review follow-up (2026-10-18). An independent review against 5fd9e14 found no mathematical errors;
its readability flags are applied in curated text only (statement hashes unchanged). Gapless
late-truncation rows say their $\log(1/\varepsilon)$ comes from the Musco–Musco proof, not from
truncation; Tropp–Webber gapless rows say their explicit theorems assume $\sigma_r>0$ (and $q\ge2$
for RBKI and NysBKI) while the asymptotic forms do not; RSI and NysSI rows name their powered test
matrix beside the `rsvd`/`nystrom` link; the notation states $\ell\ge t+2$ for gapped rows and that
this family writes the target rank $r$ where the one- and two-pass family writes $k$. All four
gapless results carry the Tropp–Webber and Musco–Musco aliases, and `filtered-range-finder-bound`,
a general filtered range-finder bound, moves to Shared approximation theory.

## Block size and depth as separate resources (2026-10-18)

Maintainer: "for these there is the block size and the iteration depth. this isn't clear in the
rates page". Each block Krylov and subspace iteration row now lists two resources, in order: block
size $\ell$ (the theorem's threshold, $\ell=r+2$ for gapless rows and $\ell=t+2$ for the tail index
$t\ge r$ on gapped rows) and depth (blocks $q$ or power steps $p$, the asymptotic threshold). The
block size conditions moved out of the row notes, and the family description says that only the
depth grows with $1/\varepsilon$. No theorem, pairing or statement hash changed.

## Variant labels and algorithm abbreviations (2026-10-18)

Maintainer: the result page's Variant dropdown labelled each form by its explicit declaration's
full bold name ("The gapped bound for randomized block Krylov iteration, Frobenius norm"), which
is hard to scan. `results.toml` now takes an optional `variant_labels` list per result, aligned
with the built forms (primary's form first, then extraction order); `build.py` rejects a list
whose length differs from the number of forms or that contains an empty or non-string label, and
rejects the field on an unknown or alias id. The labels reach the site as `variantLabels`, and
`web/app.js` uses them when present, falling back to the bold name otherwise. Every result with
more than one form (14) has labels naming only the differing part: norm, truncation, test-matrix
class, or sampling with replacement.

Collection group titles now carry the algorithm abbreviations: "Randomized SVD (RSVD) / range
finder", "Generalized Nyström (GN)", "Block Krylov and subspace iteration (RBKI, RSI)", "Nyström
block Krylov and subspace iteration (NysBKI, NysSI)" and, in Krylov methods, "Randomized block
Krylov (RBKI, NysBKI)", since that group also holds the NysBKI results. Group ids are unchanged.

## Self-contained docstrings re-reviewed (2026-10-18)

Library commit c04601b on `krylov/block` rewrote the docstrings of `LowRank/Gaussian/BlockKrylov.lean`,
`BlockKrylovGapless.lean`, `NystromBlockKrylov.lean`, `Filter.lean` and `LowRank/Structural/Filter.lean`
to state every hypothesis and bound in full, with no statement, name or proof changed. The
statement hash covers the asymptotic theorem's docstring, so nine gapped rows failed the build:
`rbki-gapped-frobenius`, `rbki-gapped-late-spectral`, `rbki-gapped-late-frobenius`,
`rsi-gapped-frobenius`, `rsi-gapped-late-spectral`, `rsi-gapped-late-frobenius`,
`nyssi-gapped-spectral`, `nyssi-gapped-late-nuclear` and `nysbki-gapped-late-nuclear`. Each row's
guarantee, resources and notes were compared with the new docstrings of its asymptotic and
explicit declarations (Gaussian $n\times\ell$ test matrix, head $r=h+1$, tail index $t\ge r$
with $t+2\le\ell$, $\gamma>0$, $0<\varepsilon\le\varepsilon_0$, depth $C\log(n/\varepsilon)/\sqrt\gamma$
or $C\log(n/\varepsilon)/\gamma$, and the stated relative bound); all agree, so only the nine
hashes changed and the other 41 rows are untouched. The `rates.toml` header now names c04601b. In
the same pass `build.py` gained `cache_busted`: the built pages reference `app.js`, `math.js` and
`style.css` with a `?v=` content hash, and `<body data-version>` carries the hash of `data.json`,
which `web/app.js` appends when fetching it, so a deploy is not shadowed by cached assets.

## Exact rows: trace estimation (2026-10-18)

Maintainer: "make an entry in the rates section with the exact variance of the various quadratic
form type stuff." These are identities, not sufficient rates, so the contract gains one row kind.
A row with `kind = 'exact'` cites a single proved theorem in `theorem` and pairs no asymptotic
form: `build.py` rejects an exact row whose theorem is an asymptotic declaration or the
`Asymptotic:` target of one (that statement belongs in an ordinary paired row), a missing or
non-theorem declaration, an unproved one and any other `kind` value. Its `statement_hash` is
computed exactly as before, over that theorem's signature and docstring, so a statement change
still forces review. Its resources carry the value (label "Variance" or "Second moment", bound the
formula). A Result id is recorded when present but not required: the Haar frame estimator theorem
has none at f1d3e75. Rows without `kind` are unchanged, including the result-membership check.
`kind` is a reserved field. A family may set `resources_label` (here "Exact value") for the value
column. In `web/app.js` an exact row's expanded view has no "Explicit bound" toggle and links one
"Theorem"; its notes are headed "Hypotheses"; the count line says rows rather than rates.

The `trace-estimation` family ("Trace estimation") leads with the probe and filters by probe class
(Real, Real or complex) and probe law. Its notation states the estimator
$\operatorname{tr}(\mathbf{\Omega}^{\mathsf{H}}\mathbf{A}\mathbf{\Omega})/m$, the probe
normalizations (independent $\mathcal N(0,1)$ entries, random signs, independent coordinates with
fourth moment $m_4$, spheres of radius $\sqrt n$, the Haar frame scaled to $\sqrt n\,\mathbf{Q}$, i.e. the estimator
$(n/k)\operatorname{tr}(\mathbf{Q}^{\mathsf{T}}\mathbf{A}\mathbf{Q})$), and the convention for
general $\mathbf{A}$. Two guarantees group the rows: one probe, and several probes.

| Row | Exact value | Theorem |
| --- | --- | --- |
| Real Gaussian | $\operatorname{Var}=2\|\mathbf{A}\|_{\mathsf{F}}^2$ | `variance_quadForm_of_hasLaw_gaussianVector` |
| Rademacher | $\operatorname{Var}=2(\|\mathbf{A}\|_{\mathsf{F}}^2-\sum_i a_{ii}^2)$ | `variance_quadForm_of_hasLaw_rademacherVector` |
| Independent coordinates, fourth moment $m_4$ | $\operatorname{Var}=2\|\mathbf{A}\|_{\mathsf{F}}^2+(m_4-3)\sum_i a_{ii}^2$ | `variance_quadForm_of_isHermitian` |
| Real sphere, radius $\sqrt n$ | $\operatorname{Var}=\frac{2n}{n+2}(\|\mathbf{A}\|_{\mathsf{F}}^2-(\operatorname{tr}\mathbf{A})^2/n)$ | `variance_quadForm_sqrt_smul_of_hasLaw_uniformSphereVector` |
| Haar frame, $k$ probes | $\operatorname{Var}=\frac{2n(n-k)}{k(n-1)(n+2)}(\|\mathbf{A}\|_{\mathsf{F}}^2-(\operatorname{tr}\mathbf{A})^2/n)$ | `variance_girardHutchinson_sqrt_smul_of_hasLaw_haarFrame` |
| $m$ independent probes | $\mathbb{E}\lvert\cdot-\operatorname{tr}\mathbf{A}\rvert^2=v/m$ | `integral_norm_girardHutchinson_sub_trace_sq` |

Read-back against f1d3e75. The real single-probe theorems and the Haar frame theorem assume real
symmetric $\mathbf{A}$ and state `Var`. The rows say so. For the real Gaussian, Rademacher and
sphere probes the notes name the `_hermitianPart` companions, which hold for every real
$\mathbf{A}$ with $\|\mathbf{H}\|_{\mathsf{F}}$, $\mathbf{H}=\frac12(\mathbf{A}+\mathbf{A}^{\mathsf{T}})$,
in place of $\|\mathbf{A}\|_{\mathsf{F}}$; the diagonal and trace stay those of $\mathbf{A}$. No
such companion exists for the Haar frame estimator. Its notes instead name the compression
theorems for $\operatorname{tr}(\mathbf{Q}^{\mathsf{T}}\mathbf{A}\mathbf{Q})$ (symmetric and
`_hermitianPart`), whose factor $2k(n-k)/((n-1)n(n+2))$ times $(n/k)^2$ is the row's. That row
also needs $1\le k\le n$ and $n\ge2$. The $m$-probe theorem is over any `RCLike` field and states
the second moment $\int\lvert\cdot-\operatorname{tr}\mathbf{A}\rvert^2$, not `variance`, with
hypotheses: independent isotropic columns, square-integrable single-probe estimates, and a
common single-probe second moment $v$. The notes name the real `Var` form
`variance_girardHutchinson`. There is no Probability collection, so `collections.toml` is
unchanged. `results.toml` titles the three single-probe Result ids "Girard–Hutchinson variance: …
probe". Before this change the f1d3e75 extraction did not build: commit 0f5af31 adds a third
`randomized-svd-tail` form, the constant-factor sub-Gaussian range finder. Its `variant_labels`
gain "Sub-Gaussian, constant factor". That form has no Rates row.

Validation: a local extraction of `probability/trace-estimation` at f1d3e75 (354 modules, 4095
declarations) builds with 58 rows (8 new; the 50 earlier hashes unchanged), against both the live
checkout and a `git archive` of f1d3e75 as `--src`. 29 Python tests pass (two new: exact-row
resolution, hashing and optional Result id; rejection of paired theorems, unknown kinds, a
`kind` filter and an invalid `resources_label`). The Node probability tests and the JavaScript
syntax check pass. All 159 math spans of the family, guarantees, rows and cited statements render
under KaTeX. No browser pass was made. Deployment: merge the library branch and wait for the
rolling `explore-data` release, then merge this metadata.

## Complex probes withdrawn (2026-10-18)

Maintainer: "Let's actually remove the complex distributions for now until we think about this
more carefully. use girardHutchinson". The complex Gaussian, Steinhaus and complex sphere rows,
their result titles and the Complex filter value are removed with their library definitions. The
open question is the complex Gaussian's normalization: the random-matrix convention
$\mathrm{CN}(0,1)$ with $\mathbb{E}\lvert z\rvert^2=1$ against Mathlib's `stdGaussian ℂ` with
$\mathbb{E}\lvert z\rvert^2=2$. The withdrawn rows cited
`integral_norm_quadForm_sub_trace_sq_of_hasLaw_complexGaussianVector`,
`integral_norm_quadForm_sub_trace_sq_of_hasLaw_steinhausVector` and
`integral_norm_quadForm_sqrt_smul_sub_trace_sq_of_hasLaw_complexUniformSphereVector` (library
commit 2a4a254 withdraws the laws). The family then had five rows; the $m$-probe row still allows
complex isotropic probes, and the notation says no complex probe law is in the library yet.

## Trace estimation review follow-ups (2026-10-18)

An independent review of the real, Haar frame and $m$-probe rows against f1d3e75 found no
mathematical errors. Its follow-ups, applied against library commit 24b5d47 (2a4a254 withdraws the
complex laws; 24b5d47 adds a Hutch++ statement skeleton with `sorry`, which has no row):

- Rate search also matches the family's subject field (`e[family.subject_field]`, here the probe),
  so "orthonormal", "radius" and "independent coordinates" find their rows.
- A row may set `algorithm_definition_label`, overriding the family's `definition_label` for its
  definition link; `build.py` requires `algorithm_definition` beside it and reserves the field.
  The $m$-probe row labels its `NLAlib.IsIsotropic` link "Isotropy", a property rather than a law.
- The Rademacher row's notes state its optimality among real probes with independent coordinates
  in $L^4$, each of mean $0$, variance $1$ and the same fourth moment
  (`variance_quadForm_of_hasLaw_rademacherVector_le`, an inequality, hence notes only).
- New exact row **Independent coordinates, fourth moment $m_4$** (probe law "Independent
  coordinates", between Rademacher and Sphere in the filter order) cites
  `variance_quadForm_of_isHermitian`: for independent real coordinates in $L^4$ with mean $0$,
  variance $1$ and common fourth moment $m_4$, and real symmetric $\mathbf{A}$,
  $\operatorname{Var}(\boldsymbol{\omega}^{\mathsf{T}}\mathbf{A}\boldsymbol{\omega})=2\|\mathbf{A}\|_{\mathsf{F}}^2+(m_4-3)\sum_i a_{ii}^2$.
  It has no Result id and no definition link (no probe law is involved).
- The one-probe guarantee now states the real form $\boldsymbol{\omega}^{\mathsf{T}}\mathbf{A}\boldsymbol{\omega}$,
  since every one-probe row is real; README and the trace section above drop the withdrawn complex
  rows.

No existing `statement_hash` changed: the build at 24b5d47 reports no mismatch, so the
Moments.lean docstring edits in 2a4a254 do not touch the cited theorems. Validation: the 24b5d47
extraction (354 modules, 4098 declarations) builds with 56 rows, six in this family; 29 Python
tests pass (the definition-link test covers the row label), the Node probability tests and the
JavaScript syntax check pass, and all 250 math spans of the family, guarantees, rows and the 13
cited statements render under KaTeX. No browser pass was made.

Re-checked 2026-10-18 against library commit a4f8773 (Hutch++ proved, no `sorry` in the library):
the strict build accepts every row with no statement-hash change.
