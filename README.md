# explore

The NLA-lib explorer, served at <https://nla-lib.org/explore/>: the definitions and named
results of [NLAlib](https://github.com/NLA-lib/NLAlib) by topic, a search box, and for each
result its statement, its Lean declarations with links to the source, and its dependencies
within the library.

Statements, source links and the Rates rows are generated from the library. Explorer collections
and the reviewed Rates summaries are curated here and checked against the extracted declarations.

## How it updates

1. On every push, NLAlib's `explore` workflow builds the library, runs
   `scripts/explore_data.sh` (every public declaration: kind, docstring, signature, source
   statement, line range, presentation role, source hashes, and the library declarations its
   statement and proof use), and
   publishes the result as `explore-data.json` on NLAlib's rolling `explore-data` release.
2. It then sends a `nlalib-updated` dispatch to this repository (needs the secret below), whose
   `deploy` workflow downloads the data and `references.bib`, runs `build.py`, and deploys
   `site/` to GitHub Pages. A daily scheduled run catches anything missed.

## Rates and algorithm browsing

The [Rates page](https://nla-lib.org/explore/rates/) compares the resources (samples, block size,
depth, queries) each algorithm needs for a target accuracy. **Every asymptotic pair of the
library is a row**: each `exists_forall_` declaration with an `Asymptotic:` target, whether or not
anyone has reviewed it. Its cells come from the same facets as the statements tables of result
pages (`facets.py`, with `facets.toml` on top): algorithm, error measure, the statistic as a formula
($\mathbb{E}\|\cdot\|^2$, $\mathbb{E}\|\cdot\|$, $\mathbb{P}[\ldots]$ "tail bound", Var), sketch
law, output (plain, late-truncated, early-truncated), regime (gapless, gapped) and the source as a
short citation. Sketch-property corollaries (`exists_forall_hasJLProperty_of_…`,
`…isObliviousSubspaceEmbedding…`, `…hasProjectionCostPreserving…`, …) are read by a small property
grammar (`facets.infer_property`): the property takes the algorithm's place, the statistic is a
tail bound.

- A **reviewed** row has an entry in `rates.toml` (the overlay, below): its resources with their
  bounds, visible parameter caveats and definition links.
- A **pending** row has none yet. It is marked *pending review* and shows the asymptotic
  statement as the library states it, in a group named after its generated cell ("Frobenius norm ·
  tail bound $\mathbb{P}[\|\cdot\|_{\mathsf F}^2 > t]$").
- An **exact** row (`kind = 'exact'`) records an identity, for trace estimation.

The page has one table per family, in the look of the statements table: guarantee group rows
with their full statement and definitions in a disclosure, generated columns shown when they vary
within the family, faint sources. A row's algorithm opens the statement on its result page with
that row selected (`#r/<id>?s=<asymptotic declaration>`; `#d/<name>` for an exact theorem without
a Result id); `▸` expands the theorem in place, with the *Explicit bound* toggle, the declaration
and source links and *Copy link*. Each family ends with **Bounds without a rate form**: the explicit
probabilistic bounds of its algorithms that have no asymptotic form (for example the RSVD
spectral-norm bounds of HMT 10.6 and TW 8.1), by algorithm, error measure and statistic, each
linking to its statement. The filters are global and generated: family, algorithm, error measure,
statistic, law (grouped by the sketch classes Gaussian, Haar, Sparse, Trig, Other, a class with
several laws selectable whole), output, regime, resource, form (rate or exact value), source and
status (reviewed or pending). Options come from the rows compatible with the other choices, and a
filter with one option is hidden. Filter state and search are kept in the query string
(`rates/?algorithm=RSVD&stat_key=tail`), so a comparison can be linked.

URLs: `rates/#rate/<id>` expands and scrolls to a reviewed row; a pending row is linked as
`rates/#rate/<declaration>` (its *Copy link*), which keeps working after it is reviewed; the old
anchors `#rate-row-<id>`, `#rate-notation-<family>` and `#rate-guarantee-<family>-<guarantee>`
still work. The families are **Embeddings and sketch properties**, **One- and two-pass low-rank
approximation**, **Block Krylov and subspace iteration**, **Regression** and **Trace estimation**;
an asymptotic pair whose algorithm no family lists goes to a generated **Other asymptotic bounds**
family, so nothing new is dropped silently. Linear-system solvers have no rows this round.

Highlights. Regression: Gaussian and Haar expected-error rows need $O((r+1)/\varepsilon)$ sketch
rows ($r$ the input rank); the Gaussian tail bound $O((r+1)/(\varepsilon\delta))$, CountSketch
$O(((r+1)^2+(r+1)/\varepsilon)/\delta)$ over real or complex inputs. Block Krylov and subspace
iteration list two resources per row, the block size $\ell$ and the depth: gapless rows need
$O(\log(n+1)/\sqrt{\varepsilon})$ blocks for RBKI and NysBKI and $O(\log(n+1)/\varepsilon)$ power
steps for RSI and NysSI (late-truncated RBKI and RSI: $\log(n/\varepsilon)$ for $\log(n+1)$);
gapped rows need $O(\log(n/\varepsilon)/\sqrt{\gamma})$ blocks or $O(\log(n/\varepsilon)/\gamma)$
power steps for a relative singular gap $\gamma>0$. Trace estimation lists the exact variance of
the Girard–Hutchinson estimate for one real Gaussian, Rademacher or radius-$\sqrt{n}$ sphere probe,
one probe with independent coordinates of fourth moment $m_4$, the Haar frame estimator
$(n/k)\operatorname{tr}(\mathbf{Q}^{\mathsf{T}}\mathbf{A}\mathbf{Q})$, and
$\mathbb{E}\lvert\cdot-\operatorname{tr}\mathbf{A}\rvert^2$ for $m$ independent isotropic probes,
next to the (pending) Hutch++ sample sizes.

### `rates.toml`: the reviewed overlay

- `[[families]]`: `id`, `title`, `description`, optional `notation`, `subject_label` (the
  algorithm column's heading, e.g. "Property"), `definition_label`, `resources_label`, and
  `algorithms`, the algorithm facet values (`facets.ALGORITHMS`, or property labels) whose generated
  rows it holds. An algorithm in two families fails the build. Optional `filters` on custom row
  fields remain an extension point (none is configured); `subject_field` too.
- `[[guarantees]]`: `id`, `family`, `title`, `description`, optional `definitions` links
  (`label`, full `declaration`). Titles use the vocabulary: "expected error" with the formula,
  "tail bound", "late-truncated".
- `[[rates]]`: the reviewed entries, keyed by `theorem` (the asymptotic declaration, or for
  `kind = 'exact'` the one theorem cited) and `statement_hash`: `id` (the stable URL),
  `guarantee`, `resources` (`{label, bound, kind}` with `kind` one of `samples`, `block size`,
  `depth`, `queries`; omitted for an exact value), optional `notes`, `label` (a detail cell, e.g. an
  exact row's probe), `algorithm_definition`, `algorithm_definition_label` and
  `sketch_definition`. A row's family is its guarantee's; if its facets put its algorithm in
  another family the build fails. The hand facet fields of earlier versions (`algorithm`,
  `variant`, `sketch`, `sketch_category`, `norm`, `mode`, `gap`, `probe…`) are gone: the names say
  them.
- `[algorithm_names]` (filter labels such as "Randomized SVD (RSVD)"), `[law_classes]` (the
  sketch classes; other laws are "Other") and `[generate] exclude_words` (words of a Result id or
  module that keep a pair off the page; today the linear-system solvers).

The statement hash is SHA-256 of the extracted signature, a newline, and its full docstring, after
removing HTML comments from both. Changed wording or hypotheses fail the build until a reviewer
checks the summary against the updated theorem and records its hash; a stale hash, a missing,
unpaired or unproved declaration all fail. This is a change detector, not a proof that the
handwritten summary is correct. Proof-body changes alone do not require new metadata. To review a
pending row, add a `[[rates]]` entry with its `theorem`, a guarantee, resources and the hash; its
id becomes its URL, and the declaration link keeps working. An exact row's theorem must not be an
asymptotic declaration nor the `Asymptotic:` target of one, and its expanded view has no
explicit/asymptotic toggle; a Result id is recorded when it has one. No runtime or pass-count
claim is inferred from a theorem name. See
[docs/rates-design.md](docs/rates-design.md#rates-from-facets-2026-10-19).

The home page is organized by **task shelves**, not by source folder. `topics.toml` `shelves`
lists them in order: Solve Ax = b and least squares; Low-rank approximation; Sketches and
embeddings; Trace and spectral-density estimation; Matrix functions and quadrature; Polynomial
approximation; Eigenvalues and Krylov processes; Concentration and random matrices; Lower bounds
(matvec model); Matrix analysis. Each shelf is a collection in `collections.toml`, whose groups
list existing result IDs and definition names from any folder, keeping their canonical URLs; a
result may sit in several groups and shelves (CG is under Solve Ax = b, its worst cases also under
Lower bounds). A shelf may be a folder (LowRank, Sketching, Estimation, Polynomial, Matrix: its
source modules follow in a collapsed browser, or inline with `modules = "inline"`) or not
(LinearSystems, MatrixFunctions, Eigenvalues, Concentration, LowerBounds). The other folders
(Krylov, Probability, RandomMatrix, Regression, Solvers, ForMathlib) sit in a collapsed source
browser below the shelves; the folders follow NLAlib's import layers (`order`).

A collection's `sources` lists module prefixes (default: the folder named by its `topic`). A
result or definition that no group lists appears in the "Other results and definitions" group
of the collection whose prefix matches its module most specifically, so a new result lands on
exactly one shelf until it is classified (a new `NLAlib.Krylov.LinearSystems.WorstCase` result
goes to Lower bounds, not Solve Ax = b). Unknown result ids, definitions, shelves and malformed
prefixes fail the build, all listed together. Prefixes may name folders that do not exist yet,
so the presentation works across a module migration. File moves preserve Rates and collection
references because they use declaration names and result IDs; source paths and line numbers come
from each fresh extraction. See
[the migration direction](docs/rates-design.md#preparing-the-source-library-reorganization).

`results.toml` can set `primary` to an exact explicit declaration belonging to that result.
Its asymptotic counterpart becomes the overview. This makes headline choice independent of
source order; the conditional completion identity no longer titles early-truncated GN. A
configured primary without an asymptotic form is the headline too (RSVD tail bounds open at
Tropp–Webber's Gaussian Frobenius tail).

Probability formulas use `$\mathbb{P}[E]$` with square event brackets, including in displayed
success or failure bounds. `web/math.js` normalizes recognized legacy probability operators and
round event delimiters at rendering time, preserving event contents, conditional bars, subscripts
and delimiter sizing. Plain matrix `P`, prose/code, and unrecognized or malformed notation are
left unchanged. Raw extracted documentation and Lean source remain untouched. The library's
CONTRIBUTING §6 records the convention for future docstrings.

## Result pages: the statements table

A result page lists every member of the result in a **statements table**: one row per
(asymptotic, explicit) pair and one per other member. Selecting a row shows that statement, with
the *Explicit bound* toggle when it has an asymptotic form, its Lean, its own dependency graph
(the statement as a node; other statements of the result shaded) and its notes and references.
`#r/<id>` opens the headline row; `#r/<id>?s=<declaration>` opens the row holding that
declaration (its explicit side with the toggle on); `#d/<name>` of a member does the same.
Search lists each row of a multi-statement result as a hit of its own, found by its label, its
names and its citations (`TW 8.1`, `Tropp–Webber 2023 Theorem 8.1`, `TroppWebber2023`).

The cells are generated, not curated. `facets.py` reads a probabilistic bound's facets from its
name, following the library's naming (CONTRIBUTING §4) and the grammar in
[docs/explorer-redesign.md](docs/explorer-redesign.md#appendix-b-bound-name-grammar-used-for-inference):
statistic (`integral_`, `measureReal_`/`measure_` with or without `_not`, `variance_`), moment
(`_sq`), error measure (the first norm of the conclusion), algorithm (from the name, else from
the statement's dependencies), sketch law (`_of_hasLaw_…`, or an interface namespace such as
`HasSubspaceInjection.` for "any subspace injection"), output (plain, late-truncated,
early-truncated), regime and bound shape. Rows are grouped by error measure; the columns are the
facets that vary within the result, in the explorer's vocabulary: the statistic as a formula
($\mathbb{E}\|\cdot\|^2$, $\mathbb{E}\|\cdot\|$, $\mathbb{P}[\|\cdot\|^2 > t]$, Var), "tail bound",
"late-truncated", and the source as a short citation (`TW 8.1 (RSVD2)`, `HMT 10.6`). Rows the
facets do not tell apart get their docstring names as detail. A result outside the grammar
(deterministic theory) lists its members by their docstring names, without the shared head
(`Courant–Fischer, lower bound` is "lower bound").

`facets.toml` overrides facets per declaration name (`algorithm`, `measure`, `output`, `label`
for the detail cell, …) for the few names the grammar misses, and may give citation keys short
names; an override of an unknown declaration fails the build. The build prints a note listing
algorithm bounds without an error measure. Each declaration's facets are in `data.json` (`fc`),
each result's rows in `rows`/`cols`/`row`.

`results.toml` can fold a result into another, `merge_into = "<id>"`: its members join that
page and the old id stays an alias (`#r/<old id>` redirects there, selecting the statement that
headed the old result). A merged entry takes only `aliases`. Titles drop a leading "The" at build
time, and the build warns about words the vocabulary retires ("average" or "mean" for an error,
"with high probability", "deviation"). Positional `variant_labels` are retired; the build
rejects them.

## What the explorer reads from NLAlib

- **Topics** are the library's directories: `NLAlib/<Layer>/<Subtopic>/<File>.lean`. Titles
  come from `topics.toml`, else from the directory name; each file's title is the `# Title` of
  its module docstring.
- **Results** are the `Result: <id>` lines of docstrings (CONTRIBUTING §6). Declarations with
  the same id are shown together as one result; its title is the bold name opening the first
  docstring (`**Weyl's inequality.**`) without a leading "The", else the id.
- **Roles**: registered named numerical bounds carry `explorerRole: "support"` in raw data;
  output roles are `support`, `concept` (other definitions), and `lemma`. Support declarations
  stay searchable and available in source views; default dependency graphs collapse through them.
- **Asymptotic forms** use `Asymptotic: Full.explicit.name` (the name may be on the next
  line). Metadata is hidden from prose. Forms inherit the target’s result ids while keeping
  their own; unresolved targets, cycles and pairs without any result id fail the build.
  Each result exports `overview`,
  `explicit`, and every `{overview, explicit}` pair in `forms`. The default pair prefers the
  original primary explicit declaration, then extraction order. Paired views use mathematical
  statements parsed from their own docstrings, with Related, Notes and References below;
  legacy result LaTeX overrides are used only for unpaired results.
- **Definitions** are `def`, `abbrev`, `structure`, `class` and `inductive` declarations; every
  other theorem without a result id is a lemma, listed on its file's page.
- **Statements** are the docstrings, rendered as Markdown with `$…$` and `$$…$$` typeset by
  KaTeX (doc-gen4 reads the same syntax). Backticked spans written as informal Unicode maths
  (`` `‖A⁻¹‖₂ ≤ κ / σ_min(A)` ``) are converted to LaTeX and typeset too (`web/math.js`). In the
  sidebar the whole statement is set in KaTeX's font, Lean names in it upright
  (`eigenvalue A k`); in the one-line descriptions on the main page a span containing a Lean name
  stays code. Single-letter matrices and vectors are bold: those whose Lean binder is a matrix
  or vector (`A : Matrix m n 𝕜`, `x : n → 𝕜`, `G : Ω → Matrix …`) and those the prose introduces
  as "matrix `G`", and every other capital letter unless the Lean binds it to something else or
  it is a conventional scalar (`N`, `K`, `C`, `L`). `E` opening a term is the expectation
  $\mathbb{E}$ and `P(…)` the probability $\mathbb{P}$; `‖·‖_F` is written $\|\cdot\|_{\mathsf F}$.
  Lean constructions with a standard notation are typeset as such: `fromBlocks A B C D` as a
  2×2 block matrix, `fromCols`/`fromRows` as a row/column of blocks, `pinv A` as $A^+$,
  `diagonal`, `specNorm`, `frobNorm`, `pseudoConditionNumber`, `eigenvalue A k`, `singularValues A k`
  (`CONSTRUCTS` in `web/math.js`; an unapplied name stays a name).
  `results.toml` can supply a statement for a result whose docstrings have none.
- **Definitions are shown whole.** The data's statement of a declaration stops at `:=`, which
  hides only a theorem's proof but a definition's whole content; with `--src` (an NLAlib checkout
  at the data's commit, which the deploy downloads) a definition, structure or class is shown with
  its body or fields, read from its source lines. Extraction-time `sourceHashes` must cover
  every listed module, with safe relative paths and matching SHA-256 bytes under `--src`.
  A source archive works without Git. A mismatch fails; legacy data without hashes builds
  with a warning and skips body enrichment.
- **Docstrings are split** (`build.py`, `split_doc`) along CONTRIBUTING §6: the bold name becomes
  the declaration's label, citations and the remarks on how the source differs go to
  References, sentences pointing at other declarations go to Related, a `Proof:` paragraph goes
  to Proof sketch, port provenance is dropped, and what remains is the statement.
- **Books** (`books/`): for each book in `books.toml`, every numbered result, with the library
  results and declarations whose docstrings cite it (`[Tropp2015, Theorem 6.1.1]`; a citation
  of a section, `§6.6`, or an equation, `(2.1.28)`, is listed under its section). A numbered
  result no docstring cites is shown faint, so a wrong or missing citation shows up here too.
- **Dependencies** are the library declarations used in a declaration's statement or proof. The
  graph shows results and definitions, collapsing the helper lemmas between them; a toggle shows
  the raw declaration-level graph.

## Files

| File | |
|---|---|
| `build.py` | `data/explore-data.json` (+ `references.bib`) → `site/` |
| `web/` | the page: `index.html`, `app.js`, `style.css`, fonts, KaTeX 0.16.22 (MIT) |
| `topics.toml` | the shelf order (`shelves`); titles, layer order and blurbs of folders and subfolders; where loose files go |
| `results.toml` | optional title, aliases, LaTeX statement, primary and `merge_into` per result id |
| `facets.py` | facets of a bound read from its name (and of a sketch property); the statements table of a result page; the Rates cells |
| `facets.toml` | per-declaration facet overrides and short names of citation keys |
| `synonyms.toml` | search synonyms (`pseudoinverse` → `pinv`) |
| `rates.toml` | Rates families, guarantees and the reviewed overlay (summaries keyed by theorem and statement hash) |
| `collections.toml` | the shelves: result and definition groups independent of source modules, and the `sources` prefixes that place new results |
| `books.toml` | key books for the Books page: chapters, sections, numbered results (numbers and short names only) |

## Local build

When introducing the role and asymptotic metadata support, merge the corresponding NLAlib
docstring and extraction changes first, and wait for its Explore data publication to finish.
The new builder rejects malformed tags that older extractions could contain; the last
successfully deployed site remains available meanwhile. Rates metadata must match the published
snapshot; publish theorem updates before deploying their corresponding metadata changes.

```sh
# in NLAlib, after LEAN_NUM_THREADS=2 lake build NLAlib
bash scripts/explore_data.sh ../explore/data/explore-data.json
# here
python3 build.py --bib ../nlalib/docs/references.bib --src ../nlalib
python3 -m http.server -d site 8000     # http://localhost:8000
```

Regression Rates metadata references new library theorems. Merge those theorem
changes into NLAlib and wait for fresh rolling-release extraction before merging or deploying
explorer rows that reference them. Review each final asymptotic/explicit pair, row restrictions
and signature/docstring hash against that extraction. Passing explorer unit tests on a PR does
not establish compatibility with the currently published library data. Keep strict reference,
proved-pair, rate-hash and source-fingerprint validation enabled; local previews must use matching
extracted data and source bytes. See [the preparation status](docs/rates-design.md#regression-rates-preparation-2026-10-16).

Run metadata regressions with `python3 -m unittest discover -s tests -v` and check browser-script
syntax with `node --check web/app.js`. Run probability-rendering regressions with
`node tests/test_math.cjs`.

## One-time setup

- **Serving at nla-lib.org/explore.** The organisation site is the repository
  `NLA-lib/NLA-lib.github.io` (renamed from `nla-lib.org` on 2026-10-14), whose custom domain
  is `nla-lib.org`, so every other repository's Pages site appears under it. Enable Pages for
  this repository with source "GitHub Actions"; it is served at `nla-lib.org/explore/`.
- **Prompt updates.** Create a fine-grained token with *Contents: read and write* on
  `NLA-lib/explore` only and save it in NLAlib as the Actions secret `EXPLORE_DISPATCH_TOKEN`.
  Without it the site still updates once a day.
