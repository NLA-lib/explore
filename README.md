# explore

The NLA-lib explorer, served at <https://nla-lib.org/explore/>: the definitions and named
results of [NLAlib](https://github.com/NLA-lib/NLAlib) by topic, a search box, and for each
result its statement, its Lean declarations with links to the source, and its dependencies
within the library.

Statements and source links are generated from the library. Explorer collections and the Rates
comparison summaries are curated here and checked against the extracted declarations.

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

The [Rates page](https://nla-lib.org/explore/rates/) compares sufficient asymptotic requirements
by family, then shared guarantee, then distribution or algorithm. Each guarantee is stated once,
with its formula and definition links in an expandable section; rows show resources and conditions.
The filters are appropriate to each family. With all families selected, only the
family selector and search are shown. Selecting a family reveals its configured filters; options
are drawn from matching rows, and constant or irrelevant fields stay hidden. Its families
are **Embeddings and sketch properties**, **One- and two-pass low-rank approximation**,
**Block Krylov and subspace iteration**, **Regression** and **Trace estimation**. Families are configuration,
so other future families need no new page template.
A row is one exact theorem, not a whole Result group. Expand it for the theorem's own assumptions,
its explicit bound and links to the declaration and source. Expectations of squared norms remain
distinct from expected norms; JL, embedding and injection guarantees remain distinct.

Regression compares expected and high-probability squared Frobenius residual error against the
least-squares optimum, with sketch class, sketch and guarantee-mode filters. Gaussian and Haar
expectation rows require $O((r+1)/\varepsilon)$ sketch rows, where $r$ is the input rank. The
Gaussian high-probability row uses a second-moment sufficient rate
$O((r+1)/(\varepsilon\delta))$; CountSketch uses
$O(((r+1)^2+(r+1)/\varepsilon)/\delta)$ and supports complex inputs. Haar retains the ambient
size cap. Per-row notes and full theorem views give the exact domains and sketch conventions.

Block Krylov and subspace iteration compares depth (blocks $q$ or power steps $p$) for expected
relative error $1+\varepsilon$, with algorithm, spectral-gap, variant and norm filters. Gapless
rows need $O(\log(n+1)/\sqrt{\varepsilon})$ blocks for RBKI and NysBKI and $O(\log(n+1)/\varepsilon)$
power steps for RSI and NysSI (late-truncated RBKI and RSI: $\log(n/\varepsilon)$ for $\log(n+1)$);
gapped rows need $O(\log(n/\varepsilon)/\sqrt{\gamma})$ blocks or $O(\log(n/\varepsilon)/\gamma)$
power steps for a relative singular gap $\gamma>0$. No rates are listed for Krylov linear-system solvers.

Trace estimation lists exact values rather than rates: the variance of the Girard–Hutchinson
estimate for one real Gaussian, Rademacher or radius-$\sqrt{n}$ sphere probe, or one probe with
independent coordinates of fourth moment $m_4$, the Haar frame estimator
$(n/k)\operatorname{tr}(\mathbf{Q}^{\mathsf{T}}\mathbf{A}\mathbf{Q})$, and the second moment
$\mathbb{E}\lvert\cdot-\operatorname{tr}\mathbf{A}\rvert^2$ for $m$ independent isotropic probes
(single-probe value over $m$), with probe-class and probe-law filters.

`rates.toml` supplies ordered `families`, ordered `guarantees`, and comparison `rates`.
A guarantee has `id`, `family`, `title`, `description` and optional `definitions` links, each with
`label` and the full `declaration` name. A row references its guarantee by ID; cross-family
references fail validation. OSI includes isotropy and the lower-tail condition, and remains
separate from a fixed-subspace injection. The row's optional `algorithm_definition` and
`sketch_definition` names provide direct definition links. Each row names an asymptotic declaration,
uses its `Asymptotic:` target for the explicit view, and records a reviewed `statement_hash`.
The hash is SHA-256 of the extracted signature, a newline, and its full docstring, after removing
HTML comments from both. Changed wording or hypotheses fail the build until a reviewer checks the
summary against the updated theorem and records its hash. This is a change detector, not a proof
that the handwritten summary is correct. Proof-body changes alone do not require new metadata.
The source snapshot is the rolling release JSON, not a checkout with unfinished Lean work.

Each family declares `filters = [{field = "algorithm", label = "Property"}, ...]`. A filter can
use any nonempty scalar string field on its rows; optional `order` lists preferred option order.
For example, a future solver family can filter by preconditioner without adding JavaScript.
Embeddings expose property, sketch class, sketch and variant; low-rank approximation exposes
algorithm, variant, sketch class, sketch, norm and probability mode when there is a choice.
Changing family clears dependent selections. Sketch classes are Gaussian, Haar, Sparse, Trig and
Other; Trig includes Fourier/Hadamard transforms such as SRHT. General distribution classes and
row sampling are under Other. Matrix norms are not mandatory rate metadata.

To add a rate, choose or add a family and a shared guarantee, then record `id`, `theorem`, `family`, `algorithm`,
`guarantee`, a nonempty `resources` list of `{label, bound}`, and `statement_hash`.
`variant`, `sketch`, `norm`, `mode` and `notes` are optional; configured filter fields must be
present on every row of that family. Keep restrictions visible in the row or its family notation;
full statements come from Lean. Families can choose `subject_label`, `subject_field` (default
`algorithm`) and `definition_label` (default "Algorithm definition"); a row may override that
label with `algorithm_definition_label` (e.g. "Isotropy" for a property rather than a law). "Copy link" copies the
rate's stable URL. Resource lists can describe rows, columns, samples or iterations;
the display does not assume every family uses a pair of sketch sizes. No runtime or pass-count
claim is inferred from a theorem name. Only paired proved declarations can supply Rates entries,
except exact rows.

An **exact row** (`kind = 'exact'`) records an identity, not a rate. Its `theorem` is the one
proved theorem it cites; it must not be an asymptotic declaration nor the `Asymptotic:` target of
one (use an ordinary row then). Its `statement_hash` covers that theorem as above, its resources
carry the exact value (for example `{label = 'Variance', bound = '$2\|\mathbf{A}\|_{\mathsf{F}}^2$'}`),
and its expanded view has no explicit/asymptotic toggle. A Result id is recorded when the theorem
has one but is not required. Rows without `kind` keep the paired contract; any other `kind`
fails. A family may set `resources_label` (default "Resources") for its value column, e.g.
"Exact value".

`collections.toml` organizes the Explorer independently of Lean import paths. Low-rank results
are grouped under RSVD, generalized Nyström, PSD Nyström and shared theory. Each group references
existing result IDs and definition names, retaining canonical URLs. Newly extracted results in
a configured topic appear in an automatic additional group until classified. Source modules
remain available in a collapsed browser. Sketching has Gaussian, Haar, Sparse, Trig and Other
groups, plus shared theory. Regression is a peer topic with sketch-and-solve,
sketch-and-precondition and least-squares foundations. Collections can introduce a topic before
its source directory exists, so the presentation works across a module migration. Explicitly
classified results do not reappear in another collection's automatic fallback. A result may appear in more than
one group. File moves preserve Rates and collection references because they use declaration names
and result IDs; source paths and line numbers come from each fresh extraction. See
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
| `topics.toml` | titles, order and blurbs of topics and subtopics; where loose files go |
| `results.toml` | optional title, aliases, LaTeX statement, primary and `merge_into` per result id |
| `facets.py` | facets of a bound read from its name; the statements table of a result page |
| `facets.toml` | per-declaration facet overrides and short names of citation keys |
| `synonyms.toml` | search synonyms (`pseudoinverse` → `pinv`) |
| `rates.toml` | families and reviewed theorem-specific rate summaries |
| `collections.toml` | result and definition groupings independent of source modules |
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
