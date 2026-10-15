# explore

The NLA-lib explorer, served at <https://nla-lib.org/explore/>: the definitions and named
results of [NLAlib](https://github.com/NLA-lib/NLAlib) by topic, a search box, and for each
result its statement, its Lean declarations with links to the source, and its dependencies
within the library.

Everything shown is generated from the library. Nothing here needs editing when NLAlib changes.

## How it updates

1. On every push, NLAlib's `explore` workflow builds the library, runs
   `scripts/Explore.lean` (every public declaration: kind, docstring, signature, source
   statement, line range, and the library declarations its statement and proof use), and
   publishes the result as `explore-data.json` on NLAlib's rolling `explore-data` release.
2. It then sends a `nlalib-updated` dispatch to this repository (needs the secret below), whose
   `deploy` workflow downloads the data and `references.bib`, runs `build.py`, and deploys
   `site/` to GitHub Pages. A daily scheduled run catches anything missed.

## What the explorer reads from NLAlib

- **Topics** are the library's directories: `NLAlib/<Layer>/<Subtopic>/<File>.lean`. Titles
  come from `topics.toml`, else from the directory name; each file's title is the `# Title` of
  its module docstring.
- **Results** are the `Result: <id>` lines of docstrings (CONTRIBUTING §6). Declarations with
  the same id are shown together as one result; its title is the bold name opening the first
  docstring (`**Weyl's inequality.**`), else the id.
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
- **Several statements of one result**: the declaration whose bold name is exactly the title
  leads and the rest follow as further forms; without one, those named "<title>, <qualifier>" are
  parallel forms, shown as equals under their qualifiers (`main` in `results.toml` overrides).
- **Key results** are marked 💥: in place of the dash in the topic lists and search results, in
  the panel's kind tag, and on the Books page beside each book item a key result cites. For now
  every named result is key (`key = false` in `results.toml` unmarks one).
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
| `results.toml` | optional title, aliases, LaTeX statement, leading declaration and key-result flag per result id |
| `synonyms.toml` | search synonyms (`pseudoinverse` → `pinv`) |
| `books.toml` | key books for the Books page: chapters, sections, numbered results (numbers and short names only) |

## Local build

```sh
# in NLAlib, after LEAN_NUM_THREADS=4 lake build NLAlib
EXPLORE_OUT=../explore/data/explore-data.json lake env lean -M 8000 scripts/Explore.lean
# here
python3 build.py --bib ../nlalib/docs/references.bib
python3 -m http.server -d site 8000     # http://localhost:8000
```

## One-time setup

- **Serving at nla-lib.org/explore.** The organisation site is the repository
  `NLA-lib/NLA-lib.github.io` (renamed from `nla-lib.org` on 2026-10-14), whose custom domain
  is `nla-lib.org`, so every other repository's Pages site appears under it. Enable Pages for
  this repository with source "GitHub Actions"; it is served at `nla-lib.org/explore/`.
- **Prompt updates.** Create a fine-grained token with *Contents: read and write* on
  `NLA-lib/explore` only and save it in NLAlib as the Actions secret `EXPLORE_DISPATCH_TOKEN`.
  Without it the site still updates once a day.
