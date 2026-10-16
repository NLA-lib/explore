# Rates and algorithm-oriented exploration

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
