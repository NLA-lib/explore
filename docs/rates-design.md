# Rates and algorithm-oriented exploration

The dated sections record successive changes. The latest section, **Regression Rates validation**, describes the current completed extension. Earlier dated sections record its preparation and preceding schema changes.

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
