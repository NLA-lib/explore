# Algorithm pages

Proposal, 2026-10-29, for the maintainer's decision (decision sheet `Algorithm-Pages`). Scope:
explorer presentation, explorer curation files, and library metadata conventions (docstring tags,
extraction, a proposal format for cost targets). No mathematical statement, proof or approved rule
of NLAlib changes. Evidence: library extraction c4b429b (5568 declarations, 452 result ids),
explorer main at cc62023, the library's `docs/design/Computation.md` (F1, F9, F12),
`docs/targets.toml` and CONTRIBUTING §5.5, §6 and §11. The numbers in §2 come from a dry run of the
proposed attachment rule over that extraction (§10 says how to rerun it).

Maintainer decisions this note builds on (2026-10-29):

- every method with a mathematical definition gets an algorithm page eventually;
- a program is not required for an algorithm page; it is one optional level;
- algorithm pages are separate from result pages, and link both ways with result, definition,
  shelf and Rates pages.

## Summary

The story of one algorithm is spread over several kinds of declaration: its mathematical
definition (often two: what it computes, `cgIterate`, and the recurrence that computes it,
`cgState`), a program in the computation model (`hutchppProg`, `gramSchmidtProg`), cost targets
about the program's registered tree (five today, all Hutch++ and Gram–Schmidt), guarantees in exact
arithmetic (result pages and Rates rows), guarantees in finite precision (the Lanczos local-error
model; the CG chain is still in the scaffold), and lower bounds. The explorer shows the results one
by one and has no place where these meet.

Recommended:

1. **Source of truth**: a library docstring tag `Algorithm: <id>` on the definitions and programs
   of an algorithm (like `Result:` on theorems), plus an explorer overlay `algorithms.toml` for
   titles, families, variants and the Rates facet label, keyed by the id (like `results.toml`).
2. **Results attach automatically**: by a fixed precedence (curated, then result-id prefix, then the
   Rates facet, then the statement's dependencies on tagged declarations). Results that involve
   several algorithms and match no prefix are listed on each, as "also involve". Nothing is
   removed from shelves.
3. **Pages**: `#a/<id>` in the main app, a panel like `#r/<id>`; an index at `algorithms/`, one table
   per family. Variants (PCG of CG) are separate pages linked by `variant_of`; programs and access
   models (oracle, dense, COO) are sections of one page, not separate algorithms.
4. **Pseudo-code**: NumPy emitted from the registered tree when there is one; otherwise, or in
   addition, a hand-written block in the docstring. The build writes a one-line provenance under
   every listing; nothing is shown without one.
5. **Status ladder**: six rungs computed from the data, shown as a plain table on each page and as
   columns of the index, and written to `site/algorithms/ladder.json` as a work queue.
6. **Precision facet**: inferred from the statement's dependencies on a short list of
   precision-model constants in `facets.toml`; a Rates column and filter that appear only when the
   value varies, as the other generated columns do.
7. **Cost targets in batches**: agents write proposal files; a checker prints them as the registry
   would; the maintainer approves a round once through a decision sheet and applies it. Q3, E3 and
   E4 are unchanged.

First slice: CG (with PCG as its variant), Lanczos, Hutch++, randomized SVD, sketch-and-solve,
Gram–Schmidt. These cover every rung that exists today.

## 1. What is an algorithm (source of truth)

### Options

| | (a) library tag + explorer overlay | (b) curated `algorithms.toml` only | (c) inferred |
|---|---|---|---|
| where the membership lives | `Algorithm: cg` in the docstring of `cgState`, `cgIterate`, later `cgProg` | `definitions = ["NLAlib.cgState", …]` in explore | bold names of definitions, facets |
| who writes it | the agent that writes the definition, in the same diff | an explorer curator, after the fact | nobody |
| drift on a rename or move | none (the tag moves with the docstring) | build failure until the toml is fixed (detected, like stale Rates rows) | none, but unstable |
| a new program or definition | appears on its page in the next deploy | invisible until curated | appears, maybe on the wrong page |
| scale (≈100+ algorithms, several declarations each) | one line per declaration, reviewed with the Lean | a few hundred curated names in one file | — |
| precision | exact | exact | poor: `galerkinInverse` has a bold name and is not an algorithm; `cgIterate` says of itself "not an algorithm" |

Inference (c) is ruled out: bold-named definitions include constructions (`galerkinInverse`,
`blockKrylovMatrix`) and named bounds, and the facet tables (`facets.ALGORITHMS`) cover only
the randomized low-rank and trace algorithms.

**Recommendation: (a).** It is the arrangement results already have (`Result:` in the library,
`results.toml` in the explorer), so it inherits its checks and its division of labour: the library
says what a declaration *is*, the explorer says how it is *shown*. It also makes the ladder a work
queue at the moment a definition is written, which (b) cannot.

### The tag

```lean
/-- The **Hestenes–Stiefel recurrence** (the conjugate gradient algorithm) from the start … 
[HestenesStiefel1952, (3:1)]; …
Algorithm: cg -/
def cgState …
```

- `Algorithm: <id>` on its own line, last, like `Result:`. Ids are kebab-case and follow the
  result-id prefixes already in use (`cg`, `pcg`, `lanczos`, `hutchpp`, `randomized-svd`,
  `sketch-and-solve`, `gram-schmidt`), so that the prefix rule of §2 works without configuration.
- Allowed on `def`, `abbrev`, `structure`, `inductive` declarations: mathematical definitions,
  recurrences, run models (`LanczosRun`) and programs (`hutchppProg`). Not on theorems: results
  attach by §2. Not on targets: a target names its trees in `docs/targets.toml`, and a tree's
  program carries the tag.
- An optional role in parentheses, `Algorithm: cg (specification)`, for the definition of *what*
  is computed when a separate recurrence computes it (`cgIterate`, `pcgIterate`,
  `pminresIterate`). Without a role a definition is shown as *definition*; a constant of type
  `Computation.Prog` or a builder whose `.compiled` is a registered tree is shown as *program*
  (the build reads that, the tag does not say it).
- Several definitions per algorithm are expected: `rsvd` and `earlyTruncatedRSVD`, `cgState` and
  `cgIterate`, `hutchpp` and `hutchppProg`. Output variants (late- and early-truncated) stay on one
  page, where the existing output facet separates their guarantees.
- A definition belongs to at most one algorithm. Shared building blocks (`galerkinInverse`,
  `gramSchmidtQ` inside Hutch++) are found through dependencies (§3, *Uses*), not tagged twice.

### The overlay, `algorithms.toml`

Everything optional, keyed by algorithm id; an id with no entry gets a page titled from the bold
name of its first definition, with no family (listed under *Other algorithms* on the index).

```toml
[[families]]
id = "krylov-linear-systems"
title = "Krylov solvers for Ax = b"
algorithms = ["cg", "pcg", "cgls", "minres", "pminres", "gmres"]

[cg]
title = "Conjugate gradient (CG)"
aliases = ["Hestenes–Stiefel", "HSCG"]
variants = ["pcg", "cgls"]            # shown on CG's page; each lists `variant_of = "cg"` back
result_prefixes = ["cg"]               # default: [id]
results = []                           # attach a result the rules of §2 miss
not_results = []                       # detach one they place wrongly
definitions = []                       # bootstrap only: names not yet tagged in the library

[randomized-svd]
title = "Randomized SVD (RSVD)"
facet = "RSVD"                         # the Rates algorithm facet value (facets.ALGORITHMS)
result_prefixes = ["randomized-svd", "rsvd", "etrsvd"]
```

- `facet` ties a page to its Rates rows. It replaces `rates.toml` `[algorithm_names]` (the
  filter label becomes the algorithm's title) and, once the tags exist, `facets.ALGORITHM_DEFS`
  (the definition-to-facet map is then tags + `facet`). The name-token grammar in `facets.py` stays.
- Checks, all failing the build and listed together as today: an unknown id, a family listing an
  id twice or in two families, `variant_of` without the reverse `variants` entry, a `facet` that
  no row has, a `results`/`not_results` id that does not exist, a `definitions` name that does not
  exist, and a `definitions` name that also carries the tag (the toml entry is then stale).
- The library's R3 check (an id or declaration the explorer names must exist) is extended to
  `algorithms.toml`, as it covers `results.toml` and `collections.toml`.

## 2. How results attach

A result (a `Result:` id) is placed on an algorithm page by the first rule that applies:

1. **curated**: `results` / `not_results` of the algorithm in `algorithms.toml`;
2. **result-id prefix**: the id equals an algorithm's id or starts with one of its
   `result_prefixes` followed by `-` (`cg-chebyshev-bound`, `minres-lanczos`, `hutchpp-program`);
   the longest prefix wins (`pcg-` before `cg-`);
3. **Rates facet**: the algorithm facet of its declarations (`facets.infer`, or a `facets.toml`
   override) maps to exactly one algorithm (`rsvd_pow_mul` reads as RSI, not RSVD);
4. **statement dependency**: the statements (`typeDeps`, not proofs) of its declarations reach
   tagged declarations of exactly one algorithm.

A result whose statements reach tagged declarations of several algorithms and that rules 1–3 do not
settle is listed on each of them under **Results that also involve this algorithm**, and in the
build's attachment report. A result the rules place on one algorithm and whose statement also
reaches another is listed there under the same heading (`cg-lanczos` is CG's, and is listed on
Lanczos). A result that reaches no tagged declaration is unchanged: it stays on its shelves and
in its folder, with no algorithm. No result is removed from a shelf or a collection.

Dry run on c4b429b with fourteen algorithms tagged by hand (CG, PCG, Lanczos with `LanczosRun`,
Hutch++ with its program and targets, Gram–Schmidt with its program and target, RSVD, RSI (facet
only), GN, RBKI, sketch-and-solve, sketch-and-precondition, Lanczos-FA, MINRES, GMRES) and the
prefixes `rsvd`/`etrsvd` for RSVD, `gn`/`etgn`/`tgn` for GN and `pminres` for MINRES:

- 120 result ids reach a tagged declaration. Rules 2 and 4 place 117; three stay ambiguous and go
  to *also involve* on both pages (`gram-correspondence`: RSVD and RBKI; `perturbed-truncation`
  and `early-truncation-pcp-bound`: RSVD and GN).
- Rule 4 alone would put ten results on the wrong page: eight unpreconditioned `minres-*` results
  on GMRES (MINRES of a Hermitian matrix is stated as `gmresIterate`) and `rsi-gapless-error`,
  `rsi-gapped-error` on RSVD (their statements mention `rsvd`). Rule 2 moves all ten, and settles
  fourteen results that reach two or three algorithms (`cg-lanczos` to CG, `hutchpp-tail` to
  Hutch++, `sketch-and-precondition-realisation` to sketch-and-precondition).
- 32 *also involve* entries result, eleven of them MINRES results on GMRES's page, which is the
  honest reading of their statements.
- CG gets 18 results, three of them sharpness (`cg-chebyshev-sharp`, `cg-spectrum-minimax-sharp`,
  `cg-near-optimality-lower-bound`); Lanczos 14, ten in finite precision; Hutch++ 8, four of them
  cost targets; Gram–Schmidt 2 (`gram-schmidt-program`, `haar-frame-gram-schmidt`). No curated
  entry was needed.

The curated lists are for exceptions. The build prints a note when more than a handful of
`results` entries for one algorithm would have been placed by rule 2 or 4 anyway.

## 3. Page structure and links

### URLs

- `#a/<id>` opens an algorithm page in the main app's panel, like `#r/<id>`, `#d/<name>` and
  `#m/<module>`; it works on every page of the app (`books/`, `rates/`, `algorithms/`).
- `algorithms/` is the index: the same app one directory down, as `books/` and `rates/` are, with
  a nav link beside them.
- `#a/<id>?s=<section>` scrolls to a section (`cost`, `exact`, `finite-precision`, `sharpness`),
  so the index's ladder cells link into pages.
- An algorithm id that is renamed keeps working through `aliases_of = ["old-id"]` in the overlay,
  as `merge_into` keeps result ids working.

### The algorithm page

In this order; a section with nothing in it is omitted, except the ladder, which shows every rung.

1. **Title**, aliases, the first sentence of the first definition as description; *Variant of
   [CG]* or *Variants: [PCG], [CGLS]*; the shelves that hold its definitions or results (links to
   the shelf groups); family.
2. **Definition**: each tagged definition, shown whole as definitions are today, with its role
   (*specification*, *definition*, *run model*) and a link to `#d/<name>`. The theorem relating
   two of them (`cg-recurrence`: the recurrence computes the specification) is listed here.
3. **Pseudo-code**, with its provenance line (§4).
4. **Status**: the ladder (§5).
5. **Cost**: one row per registered target about a program of the algorithm: access model
   (matrix-free; matrix-free with draws; stored entries, dense; stored entries, COO), the count and
   memory as the target states them (with the docstring of the count definition, `hutchppCount`),
   the `precomputed` flag next to the cost (F12, Q5), the review date from the registry, and a
   link to the proof (the `Result:` theorem whose type is the target). The emitted code of each
   tree is a collapsed listing here.
6. **Guarantees in exact arithmetic**: the algorithm's Rates rows, rendered by the Rates table
   code filtered to `facet` (reviewed and pending, with ▸ as on the Rates page and a link to the
   filtered page `rates/?algorithm=<facet>`); then its other results, one line each (title and
   first sentence), grouped by error measure where `facets.py` has one and otherwise in source
   order.
7. **Guarantees in finite precision**: results whose precision facet (§6) is not exact, with the
   model named in each line.
8. **Lower bounds and sharpness**: results that are lower bounds: `kind = 'lower'` rows of
   `rates.toml`, results whose declarations are in `NLAlib.LowerBounds`, and ids ending in
   `-sharp` or `-lower-bound`; the overlay can add others with `sharpness = [...]`.
9. **Results that also involve this algorithm** (§2).
10. **Uses / used by**: the algorithms whose tagged declarations the definitions and programs use
    (the definition of Hutch++ uses RSVD and Girard–Hutchinson) and the reverse. Read from `valueDeps`
    of tagged declarations.
11. **Lean**: every tagged declaration with its source link, and the module pages.

### Links back

- **Result page**: under the title, *Algorithm: [CG]* for the algorithm it is placed on, and
  *Also involves: [Lanczos]* for the others.
- **Definition page** (`#d/cgState`): *Algorithm: [CG]*. A module page marks tagged declarations
  the same way.
- **Shelf**: a collection group whose definitions include a tagged declaration shows *Algorithm:
  [CG]* after its title. No collection changes; `collections.toml` may later list algorithm ids in
  groups (`algorithms = ["cg", "pcg"]`), but that is not needed for the first slice.
- **Rates**: each family's description lists its algorithms as links to their pages; the expanded
  ▸ view of a row adds *Algorithm page* beside *Copy link*. The algorithm cell keeps opening the
  statement, as now.
- **Search**: algorithms are hits of their own (type `a`), found by title and aliases; a query that
  matches an algorithm lists it before its results.

### Families and variants

A **family** is presentation only: a group on the index page, in the order of `algorithms.toml`.
A **variant** is a separate algorithm with its own definitions and results, related by
`variant_of`: PCG, CGLS and the preconditioned MINRES are variants of CG and MINRES; early- and
late-truncated RSVD are *outputs* of RSVD (one page); RSI, RBKI, GN and Nyström are separate
algorithms in one family *Randomized low-rank approximation*, not variants of RSVD. Programs of the
same algorithm (the textbook HSCG program; dense, oracle and COO trees of Hutch++) are rows of the
Cost section of one page. A rule of thumb for curators: a variant has a different definition; an
output or an access model has the same definition.

### The index, `algorithms/`

One table per family: algorithm (link), then one column per rung of the ladder with the number of
declarations or results at that rung (a link to the section), then the shelf. Plain text; an empty
rung is a dash. Families in overlay order, *Other algorithms* last. A filter by rung ("has a cost
target", "has finite-precision guarantees") uses the query string, as the Rates filters do.

## 4. Pseudo-code

| source | when | shown as | provenance line (written by the build) |
|---|---|---|---|
| emitted | the algorithm has a program with a registered tree | NumPy from `NLAlibTools.NumPy`, collapsed under Cost and shown under Pseudo-code when there is no hand-written block | "Emitted from the registered tree `NLAlib.hutchppProg.compiled` by `NLAlibTools.NumPy`, an unverified translation; the cost targets above are about this tree." |
| hand-written, for a program | a fenced block in the program's docstring | the block | "Written by hand; the program it describes is `NLAlib.hutchppProg`." |
| hand-written, for a definition | a fenced block in a tagged definition's docstring | the block | "Written by hand from the definition `NLAlib.cgState`; not generated from or checked against it." |
| none | — | the definition's formula (section 2) only | — |

- The emitted listing is printed from the very tree the targets are about (F1, F11 step C). Its
  variables are de Bruijn levels (`b0`, `i1`), which is faithful but hard to read, so it is not the
  only listing a reader sees when a hand-written block exists. A later emitter option could take
  parameter names from the builder; that is a tools change, outside the checked library.
- Hand-written blocks live in the docstring, where they are reviewed with the Lean, not in the
  explorer. The convention (a ```` ```text ```` block after the statement and before the
  citation, on a tagged declaration only) is a new item of CONTRIBUTING §6; `check_refs.py`
  checks only its position.
- The provenance line is generated, never written in the docstring, so it cannot overstate. The
  build never calls hand-written pseudo-code "the algorithm" or the emitted code "pseudo-code".
- No marker beyond that line: no badges, no "verified" label.

## 5. The status ladder

Six rungs, each computed from the extraction and the registry, none curated:

| rung | present when |
|---|---|
| Definition | a tagged definition exists (always) |
| Program | a tagged program exists in NLAlib (by E4 it then has a registered tree named by a target) |
| Cost and output | a registered target about one of its trees has its proof (the target's postcondition states the output; its `cost` and `mem` the resources) |
| Exact guarantees | a result placed on it (§2) with precision *exact*, other than the cost targets and the sharpness results |
| Finite precision | a result placed on it with precision other than *exact* (§6) |
| Sharpness | a lower-bound or sharpness result placed on it (§3, item 8) |

The rungs are ordered as an algorithm usually matures, but they are independent: Lanczos has
finite-precision guarantees (through the local-error model `LanczosRun`) and no program in NLAlib;
Gram–Schmidt has a program and a cost target and almost no guarantees. The page shows a table with
one row per rung, the number present and links, never a progress bar or a percentage.

Only NLAlib is extracted, so statements in `NLAlibScaffold` (the CG program and bridge, the
Lanczos program, the CG finite-precision chain) are not counted. Showing them as *stated, not yet
proved* would need the extraction to include the scaffold; the explorer does not show unproved
statements today, and this note does not propose that.

`site/algorithms/ladder.json` lists, per algorithm, each rung with the declarations or results
present. The harness reads it as a work queue ("algorithms with exact guarantees and no
sharpness", "programs whose targets are not registered"); `build.py --ladder` prints the same as a
table. The build also lists, as a note, definitions that statements of placed results reach and
that look like algorithms (a facet algorithm with no tagged definition), so missing tags show up.

## 6. Precision as a facet

Today every Rates row is in exact arithmetic. Finite-precision statements in the library use one
of a few model constants, so the precision of a declaration can be read from its statement's
dependencies, as the algorithm facet is:

| value | the statement reaches |
|---|---|
| exact arithmetic | none of the below (default) |
| standard model, unit roundoff $u$ | `Computation.IsRelErrSem`, `Computation.MatrixFreeRounded`, `Computation.IsMatvecErr` |
| local-error model, $\varepsilon$ | `LanczosRun`, later the CG interfaces (`NormalizedLanczosData`, `CGRun`) when they reach NLAlib |

- The list is a `[precision]` table in `facets.toml` (constant → value), a handful of entries; a
  constant that no longer exists fails the build, like an override. No library tag is needed.
- The facet is `fc.precision` in `data.json`, used by the algorithm pages (§3, item 7), by result
  statements tables (a column when it varies within a result) and by Rates: a *Precision* column and
  filter generated like the others, so they are hidden while every row is exact.
- Rates rows need `Asymptotic:` pairs. The finite-precision results are explicit bounds
  (`k^3 ε κ^2 ≤ 10^{-5}` hypotheses, polynomial constants), so for now they appear under the
  family's *Bounds without a rate form*, and on algorithm pages.
- The `[generate] exclude_words` of `rates.toml` keeps linear-system solvers off Rates this round;
  CG's page therefore lists its guarantees as results, not Rates rows, until that decision changes.
  This note does not change it.

## 7. Library-side changes

| change | where | rule touched |
|---|---|---|
| `Algorithm: <id>` docstring tag, optional role | CONTRIBUTING §6 new item 4b; `check_refs.py` checks its format, position, kinds and that a declaration has at most one | new rule (A1–A3 in the checker's numbering); R1 unchanged (it is about `Result:`) |
| hand-written pseudo-code block on tagged declarations | CONTRIBUTING §6 | new docstring item; checked for position only |
| R3 covers `algorithms.toml` | `check_refs.py` | R3 extended |
| emitted NumPy of every registered tree in the extraction (`emitted: {tree: code}`) | `scripts/explore_data.sh` runs the emitter (`NLAlibTools`, outside the checked library) | none; the tools library stays unchecked |
| the registry read by the explorer | none: the deploy already has the source archive (`--src`), and the build reads `docs/targets.toml` from it | none |
| target proposals in batches | `docs/targets/proposals/`, a checker, CONTRIBUTING §5.5 and §11 paragraphs | none: Q3, E3, E4 unchanged (below) |
| topic titles for `Computation` and `Krylov/FinitePrecision` | explorer `topics.toml` (and a line in the library's layer notes) | none |

### Topics

`Computation` has 324 public declarations and no `topics.toml` entry; `Krylov/FinitePrecision`
is shown as "Finite precision" by default. Proposed: `[Computation]` with title "Computation
model", a blurb, and subtopics (Syntax and semantics; BLAS kernels; Access models and targets;
Rounding and error contracts), placed in `order` with the layer-0 folders (D7); `Krylov`
gets `FinitePrecision.title = "Finite precision"`. The Eigenvalues shelf gains a group *Lanczos
in finite precision* listing the Paige and Greenbaum results; a shelf for the computation model
itself is not proposed (it is infrastructure; the algorithm pages are where programs are read).

### Cost targets in batches

Per-program registration does not scale to a page per algorithm, but the protection of Q3 must not
loosen. Proposal: agents never touch the registry or `*Targets.lean` files; they write a proposal
file, a script prints it in the registry's own form, and the maintainer approves a whole round at
once.

`docs/targets/proposals/<round>.toml` (outside the protected paths):

```toml
round = "2026-11-a"
base = "36a8f18…"                      # NLAlib commit the proposals elaborate against
note = "docs/design/research/Krylov-CGRounding.md"
decision_sheet = "Targets-2026-11-a"   # one decision per target, recommended "approve"

[[target]]
name = "NLAlib.MatrixFreeCG"
file = "NLAlib/Krylov/LinearSystems/CGTargets.lean"
algorithm = "cg"
model = "MatrixFree"                   # MatrixFree | MatrixFreeProb | StoredEntries | MatrixFreeRounded
trees = ["NLAlib.cgProg.compiled"]
precomputed = []
summary = "q steps of Hestenes–Stiefel CG from x0 = 0: q + 1 oracle loads, ≤ c·N·q flops, 4N + O(1) cells; writes cgState A b 0 q's iterate."
lean = '''
def MatrixFreeCG : Prop :=
  ∀ (P ι : Type) [DecidableEq P] (p : P) (o : ι) (𝕜 : Type) [RCLike 𝕜],
    MatrixFree (𝕜 := 𝕜) p (cgProg.compiled p o) valid X inputs cost mem post
'''
```

- `scripts/Targets.lean --proposal <file>` elaborates each `lean` block in a scratch module at
  `base`, and prints what the registry would hold: the statement unfolded one level, the tree's
  normal form and the closure hash, plus the Q5 check on declared inputs. It writes
  `docs/targets/proposals/<round>.review.md`: per target, the agent's `summary`, then the printed
  statement, so the reviewer compares the two.
- A tier-1 review (Fable) checks each summary against its printed statement and the note, as for a
  skeleton. The maintainer then decides the round in one sheet: approve, return, or drop per target.
- On approval the maintainer (or a script he runs) writes the approved `lean` blocks into their
  `*Targets.lean` files, runs `TARGETS_UPDATE=1 lake env lean scripts/Targets.lean`, reviews the one
  registry diff and signs it with `sha256sum docs/targets.toml > docs/targets.approved`, in one
  commit that CODEOWNERS routes to him. Nothing about the binding layer changes.
- Until a program's targets are approved it stays in `NLAlibScaffold` (E4: every `<spec>Prog` in
  NLAlib has a registered target). The proposal file is the place where its intended targets are
  written down, so CG's and Lanczos's programs can be queued for the same round.
- CONTRIBUTING §5.5 gains a paragraph on proposals; §11's protected-path bullet adds "propose
  targets only in `docs/targets/proposals/`".

## 8. Rollout

1. **Library metadata**, one docstring-only diff: `Algorithm:` tags on the first slice's
   definitions and programs; the §6 items; `check_refs.py` rules; the emitter in the extraction.
   No statement changes, no ledger entries (documentation pass).
2. **Explorer, first slice**: `algorithms.toml` with CG (variant PCG), Lanczos, Hutch++, RSVD,
   sketch-and-solve and Gram–Schmidt; `build.py` computes `algorithms` (members, attachment,
   ladder, uses) into `data.json` and `ladder.json`; `app.js` renders `#a/<id>`, the index and the
   back links; the precision facet; the topic entries. Tests: attachment precedence, the overlay
   checks, the ladder on fixture data, the provenance lines. Until the tags are published, the
   slice runs on `definitions = [...]` bootstrap entries, which the build then reports as stale.
   This slice covers every rung: Hutch++ (definition, program, four targets, exact guarantees,
   pending Rates rows), Gram–Schmidt (program and target), Lanczos (finite precision), CG and
   RSVD (sharpness), sketch-and-solve (Rates rows with a paired lower bound).
3. **Read-back** by the maintainer of the six pages and the index; adjustments.
4. **Bulk**: a mechanical tagging pass over the library's algorithm definitions (expected 100+
   ids), in batches by folder, each reviewed against the attachment report: no result should
   move to *also involve* without a reason. The overlay grows families and titles only where the
   bold name is not enough.
5. **Targets**: the first proposal round (CG and Lanczos programs from the scaffold) under §7.

## 9. Decisions

The decision sheet `Algorithm-Pages` asks:

- AP1 source of truth (library tag + overlay; curated overlay only; inferred);
- AP2 attachment (automatic precedence with *also involve*; curated only; dependencies only);
- AP3 URLs and grouping (`#a/<id>` panel + `algorithms/` index, variants as pages; static pages per
  algorithm);
- AP4 pseudo-code (emitted + hand-written docstring blocks, generated provenance; emitted only;
  hand-written in the explorer);
- AP5 ladder (computed rungs from NLAlib only, `ladder.json`; also count scaffold statements);
- AP6 precision facet (inferred from model constants listed in `facets.toml`; a `Precision:` tag);
- AP7 target batches (proposal files and one approval per round; per-target registration as now).

## 10. Reproducing the dry run

The attachment figures of §2 come from a short script over the extraction: map each hand-picked
definition to its algorithm, collect the `Result:` ids of every declaration, and apply rule 4
(statement `typeDeps`) and then rule 2 (prefixes). It reads `explore-data.json` only; the
algorithm map is the fourteen algorithms of §2. It is not part of the build; the build's
attachment report replaces it.
