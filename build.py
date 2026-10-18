#!/usr/bin/env python3
"""Build the NLA-lib explorer, a static site, from NLAlib's extracted data.

    python3 build.py [--data data/explore-data.json] [--bib PATH] [--out site]

Inputs:
  data/explore-data.json  written by NLAlib's scripts/Explore.lean (in CI, downloaded from the
                          rolling `explore-data` release of NLA-lib/NLAlib)
  --bib                   NLAlib's docs/references.bib at the same commit (optional)
  topics.toml             titles, order and blurbs for the library's directories (optional per
                          directory: a directory without an entry gets a title from its name)
  results.toml            per `Result:` id overrides: title, aliases, latex, primary,
                          variant_labels (all optional)
  synonyms.toml           search synonyms, mathematical words to library names
  books.toml              key books: chapters, sections and numbered results, for the Books page

Output: <out>/index.html, <out>/data.json and the static assets in web/.

Everything that can be read from the library is read from it; the three TOML files only add
what the Lean source does not say, and the build works with all three empty.
"""

import argparse
import json
import hashlib
import sys
import re
import shutil
import tomllib
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = 'https://github.com/NLA-lib/NLAlib'

DEF_KINDS = {'def', 'abbrev', 'opaque', 'structure', 'class', 'inductive'}
HTML_COMMENT = re.compile(r'<!--.*?-->', re.S)
ASYMPTOTIC_LINE = re.compile(r'^\s*Asymptotic:[ \t]*(?:\n[ \t]*)?([\w.]+)[ \t]*$', re.M)
RESULT_LINE = re.compile(r'^\s*Result:\s*(.+?)\s*$', re.M)
BOLD_NAME = re.compile(r'^\s*\*\*(.+?)\*\*')


def load_toml(name):
    p = ROOT / name
    return tomllib.loads(p.read_text()) if p.exists() else {}


def humanize(word):
    """`RandomMatrix` -> `Random matrix`, `SubGaussian` -> `Sub-Gaussian`."""
    word = word.replace('SubGaussian', 'Sub-Gaussian').replace('SubExponential', 'Sub-exponential')
    parts = re.findall(r'[A-Z][a-z]+(?:-[A-Z][a-z]+)?|[A-Z]+(?![a-z])|[a-z]+|\d+', word)
    if not parts:
        return word
    out = [parts[0]] + [p if '-' in p or p.isupper() else p.lower() for p in parts[1:]]
    return ' '.join(out)


def humanize_id(rid):
    s = rid.replace('-', ' ')
    return s[:1].upper() + s[1:]


def result_title(bold, rid, phrases=None):
    """A result's title from the names of its declarations: the name they share, else the part
    before the comma they share ("Courant–Fischer, lower bound" and "Courant–Fischer, upper
    bound" give "Courant–Fischer"), else the one closest to the id (its part before the comma when
    another name shares it), else a bold phrase opening a docstring, else the id."""
    names = list(bold)
    if not names:
        if phrases:
            p = phrases.most_common(1)[0][0]
            return p[:1].upper() + p[1:]
        return humanize_id(rid)
    if len(names) == 1:
        return names[0]
    heads = {n.split(',')[0].strip() for n in names}
    if len(heads) == 1:
        return heads.pop()
    # names that disagree: the one sharing most words with the id (`mirsky-inequality` picks
    # "Mirsky's theorem" over "Lidskii's inequality for singular values"), then the commonest
    words = set(rid.split('-'))
    def score(n):
        ws = {re.sub(r"'s$", '', w) for w in re.findall(r"[\w']+", n.lower())}
        return (len(words & ws), bold[n])
    best = max(names, key=score)
    head = best.split(',')[0].strip()
    return head if sum(n.split(',')[0].strip() == head for n in names) > 1 else best


def module_doc_parts(doc):
    """Title (`# ...`) and first paragraph of a module docstring."""
    if not doc:
        return None, ''
    title = None
    m = re.search(r'^#\s+(.+)$', doc, re.M)
    if m:
        title = m.group(1).strip()
        rest = doc[m.end():]
    else:
        rest = doc
    paras = [p.strip() for p in re.split(r'\n\s*\n', rest) if p.strip()]
    summary = next((p for p in paras if not p.startswith('#')), '')
    return title, ' '.join(summary.split())


CITE = re.compile(r'\[([A-Z][A-Za-z]+\d{4}[a-z]?)(?:,\s*([^\]]*))?\]')
# `([Key], Theorem 2.1` written with the label outside the brackets
CITE_OUTSIDE = re.compile(r'\(\[([A-Z][A-Za-z]+\d{4}[a-z]?)\],\s*((?:[A-Z][a-z]*\.?\s*[\dIVX][\w.]*|§\s*[\w.]+)'
                          r'(?:\s*(?:and|,)\s*(?:[A-Z][a-z]*\.?\s*)?[\dIVX§][\w.]*)*)')
PORT = re.compile(r'\s*Port(?:ed)? (?:of|from) `[^`]+`(?:`[^`]*`|[^`.])*\.')
PROVENANCE = re.compile(r"^Port\b|\bprototype\b|\bold library\b")
LIB_NAME = re.compile(r"^[\w.'₀-₉]+$")
# a sentence after the statement that is about the source, Mathlib, the prototype, Lean's
# conventions or the API, rather than about the mathematics: shown under Notes
REMARK = re.compile(r"\b(?:Mathlib|prototype|[Ss]ources?(?:'s)?|Lean's|junk|API|[Dd]esign|deviations?|"
                    r"[Pp]orted|[Rr]eplaces|[Mm]irrors|[Cc]onsumers|[Uu]se only|proof here|is proved|value proved)\b")


def is_source(text):
    """Whether a parenthetical names a source: a citation, or a theorem number or a year in prose
    (`Boucheron–Lugosi–Massart, Theorem 2.5`)."""
    return bool(CITE.search(text) or re.search(
        r'\b(?:Theorem|Lemma|Proposition|Corollary|Definition|Exercise|Example|Chapter|Section)\b|§|\b(?:1[89]|20)\d\d\b', text))


def strip_result_line(doc):
    return ASYMPTOTIC_LINE.sub('', RESULT_LINE.sub('', doc)).rstrip() if doc else doc


DISPLAY = re.compile(r'\$\$(.+?)\$\$((?:\s*[.,;:])*)', re.S)


def tidy_displays(text):
    """Punctuation after a displayed formula goes inside it, or it is left alone on the next line;
    marks left over once citations are removed (`$$ … .$$; .`) are dropped. In an `aligned`
    display the mark goes at the end of its last line."""
    def fix(m):
        body, after = m.group(1), re.sub(r'\s+', '', m.group(2))
        if not after or re.search(r'[.,;:]\s*(\\end\{aligned\})?\s*$', body):
            return f'$${body}$$'
        mark = after[-1] if after[-1] == '.' else after[0]
        if re.search(r'\\end\{aligned\}\s*$', body):
            body = re.sub(r'\s*\\end\{aligned\}\s*$', lambda e: f'\\,{mark} \\end{{aligned}}', body)
        else:
            body = body.rstrip() + f'\\,{mark}'
        return f'$${body}$$'
    return DISPLAY.sub(fix, text)


def sentences(text):
    """Split prose into sentences at '. ' (or ': ' before a capital is not a split), never inside
    backticks, dollars or brackets; a display ending in a full stop (`… c_i\\,.$$`) ends one too."""
    out, start, tick, dollar, display, depth = [], 0, False, False, False, 0
    skip = False
    for i, ch in enumerate(text):
        if skip:
            skip = False
            continue
        if ch == '`' and not (dollar or display):
            tick = not tick
        elif ch == '$' and not tick and text[i + 1:i + 2] == '$' and not dollar:
            skip = True
            display = not display
            if not display and re.search(r'\.\s*$', text[start:i]) and text[i + 2:i + 3] in ('', ' '):
                out.append(text[start:i + 2].strip())
                start = i + 2
        elif ch == '$' and not tick and not display:
            dollar = not dollar
        elif tick or dollar or display:
            continue
        elif ch in '([':
            depth += 1
        elif ch in ')]':
            depth = max(0, depth - 1)
        elif ch == '.' and depth == 0 and (i + 1 == len(text) or text[i + 1] == ' '):
            prev = text[max(0, i - 4):i]
            if prev.endswith(('e.g', 'i.e', 'cf', 'resp', 'Thm', 'Cor', 'Prop', 'Sec', 'Ex')):
                continue
            if text[max(0, i - 2):i].startswith('**') or text[i + 1:i + 3] == '**':
                continue
            out.append(text[start:i + 1].strip())
            start = i + 1
    if text[start:].strip():
        out.append(text[start:].strip())
    return [x for x in out if x]


def split_doc(doc, decl_names):
    """A docstring (CONTRIBUTING §6) in parts: its bold name, the statement, the citations with the
    note on how the printed statement differs, sentences pointing at other declarations, and a
    proof sketch. Each part is Markdown."""
    parts = {'name': None, 'stmt': '', 'cites': [], 'cnotes': [], 'rel': [], 'notes': [], 'proof': '',
             'bold': [], 'phrase': None}
    if not doc:
        return parts
    text = ' '.join(PORT.sub('', strip_result_line(doc)).split())
    # `([Key], Theorem 2.1)` is the citation `[Key, Theorem 2.1]`
    text = CITE_OUTSIDE.sub(r'([\1, \2]', text)
    # the name: `**Name.**`, `**Name**:`, `**Name**.`, `**Name**, variant.` or `**Name** (…):`, the
    # parenthesis an alternative name (kept) or a source (a citation); a bold phrase that is the
    # start of a sentence (`**The trace of f(A)** is ...`) stays, unbolded
    m = re.match(r'\*\*(.+?)\*\*(\s*\((?:[^()]|\([^()]*\))*\))?(,\s*[^`:.*()]{1,60}(?=[:.](?:\s|$)))?\s*([.:])?\s*',
                 text)
    if m:
        name = m.group(1).strip()
        parts['phrase'] = name.rstrip('.:')
        if name.endswith(('.', ':')) or m.group(4):
            paren = (m.group(2) or '').strip()
            if paren and is_source(paren[1:-1]):
                parts['cites'] += [(k, lab.strip()) for k, lab in CITE.findall(paren)] or [(paren[1:-1], '')]
                paren = ''
            parts['name'] = ' '.join(x for x in (name.rstrip('.:'), paren) if x) + (m.group(3) or '')
            text = text[m.end():]
        else:
            bold_end = text.index('**', 2) + 2
            first = sentences(text)[0]
            paren = (m.group(2) or '').strip()
            if len(first) < 70 and ',' not in first and '`' not in first[bold_end:]:
                parts['name'] = first.replace('**', '').rstrip('.')
                text = text[len(first):].strip()
            elif paren and not is_source(paren[1:-1]) and re.match(
                    r'(?:for|if|when|over|on|with)\b', text[m.end(2):].lstrip()):
                # `**Name** (alias) for f of class C¹, …`: the name and alias, then the statement
                parts['name'] = f"{name} {paren}"
                text = text[m.end(2):].strip()
            else:
                text = name + text[bold_end:]
    proof = re.search(r'(?:^|\s)(Proof(?: sketch)?:)', text)
    if proof:
        pf = re.sub(r'\s*(?:Easy|Medium|Hard)\.$', '', text[proof.end(1):].strip())
        parts['proof'] = re.sub(r'^[a-z]', lambda c: c.group(0).upper(), pf)
        text = text[:proof.start()].strip()

    def is_ref(span):
        span = span.strip()
        if re.match(r'(NLAlib|docs|scripts)/\S+\.(lean|md|py)$', span):
            return True                                   # a file of the repository
        if not LIB_NAME.match(span):
            # a lemma applied to arguments, a proof term: `foo_le hind fun i => this (h i)`
            head = span.split()[0]
            return ' ' in span and '_' in head.split('.')[-1] and is_ref(head)
        if '.' in span:
            return span.startswith('NLAlib.') or span in decl_names or '_' in span.split('.')[-1]
        # an unqualified lemma name (`hansonWrightConstant_pos`), not a subscript (`σ_min`)
        return bool(re.match(r'[^\W\d_]{2,}\w*_[a-zA-Z]', span)) or ('NLAlib.' + span) in decl_names and '_' in span

    stmt = []
    for sent in sentences(text):
        if PROVENANCE.search(sent):
            continue                                  # port bookkeeping, for maintainers only
        # a parenthesis inside the sentence that cites a source is about the source:
        # "… ≤ exp (v l² / 2) ([Wainwright2019, Definition 2.7], with `ν² = v`)."
        def lift_cite(m):
            if CITE.match(sent.lstrip()) or not CITE.search(m.group(1)):
                return m.group(0)
            parts['cites'].extend((k, lab.strip()) for k, lab in CITE.findall(m.group(1)))
            note = re.sub(r'^[\s;,.]+', '', CITE.sub('', m.group(1))).strip().rstrip('.')
            for clause in filter(None, (c.strip() for c in note.split(';'))):
                if is_source(clause):
                    parts['cites'].append((clause, ''))      # a source named in prose
                else:
                    parts['cnotes'].append(clause[0].upper() + clause[1:] + '.')
            return ''
        sent = re.sub(r'\s*\(((?:[^()`]|`[^`]*`)*)\)', lift_cite, sent)
        sent = re.sub(r'\s+([.;,:])', r'\1', sent)
        cites = CITE.findall(sent)
        if cites:
            parts['cites'] += [(k, lab.strip()) for k, lab in cites]
            rest = CITE.sub('', sent)
            if CITE.match(sent.lstrip()):
                # a sentence that opens with citations is about the sources: the remainder is
                # how they differ ("stated there over ℂ ...")
                note = re.sub(r'^[\s;,.]+', '', rest).strip()
                # clauses pointing at other declarations go to `rel`, the rest are source notes
                kept = []
                for clause in re.split(r';\s+(?=(?:[^`]*`[^`]*`)*[^`]*$)', note):
                    clause = clause.strip().rstrip('.').strip()
                    if not clause:
                        continue
                    if any(is_ref(c) for c in re.findall(r'`([^`]+)`', clause)):
                        parts['rel'].append(clause[0].upper() + clause[1:] + '.')
                    else:
                        kept.append(clause)
                if kept:
                    joined = '; '.join(kept)
                    parts['cnotes'].append(joined[0].upper() + joined[1:] + '.')
                continue
            sent = re.sub(r'\s+([.;,])', r'\1', re.sub(r'[;,]?\s*\.$', '.', rest.strip())).strip()
            if not sent or sent in '.;,':
                continue
        if any(is_ref(c) for c in re.findall(r'`([^`]+)`', sent)):
            # a parenthetical pointer is lifted out: "(equivalently for all, `NLAlib.foo`)"
            lifted = []
            def lift(m):
                if any(is_ref(c) for c in re.findall(r'`([^`]+)`', m.group(1))):
                    lifted.append(m.group(1)[0].upper() + m.group(1)[1:].rstrip('.') + '.')
                    return ''
                return m.group(0)
            rest = re.sub(r'\s*\(((?:[^()`]|`[^`]*`)*)\)', lift, sent)
            if lifted and not any(is_ref(c) for c in re.findall(r'`([^`]+)`', rest)):
                parts['rel'] += lifted
                sent = re.sub(r'\s+([.,;:])', r'\1', rest)
            elif stmt:
                parts['rel'].append(sent)
                continue
        if stmt and REMARK.search(sent):
            parts['notes'].append(sent)
            continue
        stmt.append(sent)
    # a docstring that is one bold sentence (`**The Cholesky factor is unique.**`) is its own statement
    parts['stmt'] = ' '.join(stmt) or (parts['name'] + '.' if parts['name'] else '') or (
        parts['rel'].pop(0) if parts['rel'] else '')
    parts['stmt'] = re.sub(r'^[a-z]', lambda c: c.group(0).upper(), parts['stmt'])
    parts['stmt'] = tidy_displays(parts['stmt'])
    parts['rel'] = [tidy_displays(t) for t in parts['rel']]
    parts['notes'] = [tidy_displays(t) for t in parts['notes']]
    # letters the prose introduces as matrices or vectors ("a standard Gaussian matrix `G : N × n`")
    parts['bold'] = sorted(set(re.findall(r'(?:matrix|matrices|vector|vectors|(?:entries|columns|rows) of)\s+`([A-Za-z])(?=[\s`:,])', text)))
    return parts


def binder_types(sig):
    """Every `names : type` in an elaborated signature, including the binders of `∀` and `∃` in
    the conclusion: a list of (names, type)."""
    out = []
    if not sig:
        return out
    stops = '({[⦃,∀∃λ'
    for m in re.finditer(r' : ', sig):
        # names: identifiers to the left, back to an opening bracket, a comma or a quantifier
        j = m.start()
        k = j
        while k > 0 and sig[k - 1] not in stops and sig[k - 1] not in ')}]⦄:':
            k -= 1
        names = sig[k:j].split()
        if not names or not all(re.fullmatch(r"[^\W\d][\w'₀-₉]*", n) for n in names):
            continue
        # type: to the right, up to a closing bracket or comma at depth 0
        depth, t = 0, m.end()
        while t < len(sig):
            c = sig[t]
            if c in '([{⦃':
                depth += 1
            elif c in ')]}⦄':
                if depth == 0:
                    break
                depth -= 1
            elif c == ',' and depth == 0:
                break
            t += 1
        out.append((names, ' '.join(sig[m.end():t].split())))
    return out


def is_matrix_or_vector(typ):
    segs = [t.strip() for t in re.split(r'\s+→\s+', typ)]
    while len(segs) > 1 and re.fullmatch(r"Ω'?|ℕ|ι|Fin \w+", segs[0]) and not (
            len(segs) == 2 and re.fullmatch(r'𝕜|ℝ|ℂ', segs[1])):
        segs = segs[1:]                       # random or indexed families
    last = segs[-1]
    matrix = re.match(r'(Matrix|↥?\(?Matrix\.unitaryGroup|↥?\(?Matrix\.orthogonalGroup)\b', last) and \
        not any('Matrix' in t for t in segs[:-1])
    vector = (len(segs) == 1 and re.match(r'(EuclideanSpace|WithLp 2)\b', last)) or (
        len(segs) == 2 and re.fullmatch(r"(?![Ωℝℂ𝕜])\w'?|ι|Fin \w+", segs[0]) and re.fullmatch(r'𝕜|ℝ|ℂ', last))
    return bool(matrix or vector)


# capital letters that are scalars by convention: dimension, constants (`E` and `P` as expectation
# and probability are recognised per occurrence in web/math.js)
NOT_BOLD = {'N', 'K', 'C', 'L'}


def bold_letters(sig, texts, prose_bold):
    """The single letters of a declaration shown in bold, as matrices or vectors: those the Lean
    binds to a matrix or vector type, those the prose calls a matrix or vector, and every other
    capital Latin letter in its maths, unless the Lean binds it to something else or it is a
    conventional scalar (`NOT_BOLD`, `P` written `P(…)` as a probability, and `E` in a statement
    about measures, the expectation)."""
    mat, other = set(), set()
    for names, typ in binder_types(sig):
        for v in names:
            base = re.sub(r"['₀-₉]+$", '', v)
            if re.fullmatch(r'[A-Za-z]', base):
                (mat if is_matrix_or_vector(typ) else other).add(base)
    spans = [sp for t in texts for sp in re.findall(r'`([^`]+)`', t or '')]
    caps = set()
    for sp in spans:
        for m in re.finditer(r'(?<![\w.\'])([A-Z])(?![a-zA-Z.])', sp):
            caps.add(m.group(1))
    # letters the maths uses as matrices: `pinv C`, `σ_i(C)`, `P_C`, `Lᴴ`, `‖C‖₂`
    used = {m.group(1) or m.group(2) or m.group(3) or m.group(4) for sp in spans for m in re.finditer(
        r"(?:pinv|specNorm|frobNorm|rangeProjector|singularValues|eigenvalue)\s+([A-Z])(?![\w.'])"
        r"|[σλ]_(?:\{[^}]*\}|\w+)\(([A-Z])\)|P_([A-Z])(?![\w.'])|(?<![\w.'])([A-Z])(?:ᴴ|ᵀ|⁺|†|‖₂|‖_F)", sp)}
    p_prob = all(re.search(r'(?<![\w.])P\(', sp) or not re.search(r'(?<![\w.])P(?![a-zA-Z])', sp) for sp in spans)
    # in a statement about measures or random variables, an unbound `E` is the expectation
    e_prob = bool(re.search(r'\bMeasure\b|MeasureSpace|∫|∂|Ω|\bHasLaw\b|IndepFun', sig or ''))
    auto = {c for c in caps if c not in other and c not in NOT_BOLD and not (c == 'P' and p_prob)
            and not (c == 'E' and e_prob)}
    # lowercase letters used as vectors: next to a matrix (`A x`, `xᴴ A`) or conjugate-transposed
    # (`xᴴ`), when the Lean does not bind them to something else
    caps_bold = mat | auto
    vec = set()
    for sp in spans:
        vec |= {m.group(2) for m in re.finditer(r'(?<![\w.])([A-Z])(?:ᴴ|ᵀ|⁻¹)?\s+([buvwxyz])(?![\w.(])', sp)
                if m.group(1) in caps_bold}
        vec |= set(re.findall(r'(?<![\w.])([buvwxyz])[ᴴᵀ]', sp))
    vec -= other
    return sorted((mat | set(prose_bold) | auto | used | vec) - (other - mat))


def first_sentence(doc):
    """The first sentence of a statement, for the one-line descriptions on the main page."""
    ss = sentences(' '.join((doc or '').split()))
    return ss[0] if ss else ''


ACCENTS = {"'": '\u0301', '`': '\u0300', '^': '\u0302', '"': '\u0308', '~': '\u0303', 'c': '\u0327', 'v': '\u030c'}


def tex_accents(s):
    """`in{\\'e}galit{\\'e}`, `\\"o`, `\\c{c}` -> the accented letters."""
    import unicodedata
    s = re.sub(r'\\([\'`^"~]|[cv](?=[{ ]))\s*\{?(\w)\}?', lambda m: unicodedata.normalize(
        'NFC', m.group(2) + ACCENTS[m.group(1)]), s)
    for cmd, ch in (('AA', 'Å'), ('aa', 'å'), ('ss', 'ß'), ('o', 'ø'), ('O', 'Ø'), ('l', 'ł')):
        s = re.sub(r'\\' + cmd + r'(?![a-zA-Z])\s?', ch, s)
    return s.replace('--', '–')


def parse_bib(path):
    """A minimal BibTeX reader: key -> {text, url}."""
    if not path or not Path(path).exists():
        return {}
    src = Path(path).read_text()
    out = {}
    for m in re.finditer(r'@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}', src, re.S):
        kind, key, body = m.groups()
        fields = {}
        for f in re.finditer(r'(\w+)\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}', body):
            fields[f.group(1).lower()] = re.sub(r'[{}]', '', tex_accents(' '.join(f.group(2).split())))
        authors = [a.strip() for a in fields.get('author', '').split(' and ') if a.strip()]
        names = []
        for a in authors:
            if ',' in a:
                last, first = [x.strip() for x in a.split(',', 1)]
                names.append(f'{first} {last}')
            else:
                names.append(a)
        who = ', '.join(names[:-1]) + (' and ' if len(names) > 1 else '') + (names[-1] if names else '')
        venue = fields.get('journal') or fields.get('booktitle') or fields.get('publisher') or ''
        if fields.get('series') and kind == 'book':
            venue = f"{fields['series']} {fields.get('volume', '')}".strip() + (f", {fields['publisher']}" if fields.get('publisher') else '')
        year = fields.get('year', '')
        if year and venue.endswith(year):
            year = ''                         # `booktitle = {Surveys in Combinatorics, 1989}`
        text = f"{who}. {fields.get('title', '')}. {venue}{', ' if venue and year else ''}{year}."
        url = fields.get('url') or (f"https://doi.org/{fields['doi']}" if fields.get('doi') else
                                    f"https://arxiv.org/abs/{fields['eprint']}" if fields.get('eprint') else None)
        out[key] = {'text': ' '.join(text.split()).replace(' .', '.'), 'url': url}
    return out


def topic_of(module, topics_cfg):
    """(topic, subtopic) path keys for a module: NLAlib.Matrix.Spectral.Weyl -> Matrix, Matrix/Spectral.
    A file directly under a layer goes to the subtopic topics.toml assigns it, else `<layer>/General`."""
    parts = module.split('.')[1:]
    if not parts:
        return None, None
    top = parts[0]
    if len(parts) == 1:
        return top, f'{top}/General'
    if len(parts) == 2:
        assign = topics_cfg.get(top, {}).get('assign', {})
        return top, f"{top}/{assign.get(parts[1], 'General')}"
    return top, f'{top}/{parts[1]}'


# a numbered result, `6.1.1`, or with Horn and Johnson's fourth level, `7.4.1.3`
ITEM_NO = re.compile(r'(?<![§(\d.])(\d+)\.(\d+)\.\d+(?:\.\d+)?(?![\d)]|\.\d)')


def book_refs(label, items, same):
    """What a citation label (`Theorem 6.1.1`, `§8.3 and §8.8`, `(2.1.28)`, `Problem 7.3.P7`,
    `chapter 4`) points at in a book: numbered results (`i`), sections (`s`) and chapters (`c`)."""
    refs = set()
    for m in re.finditer(r'§\s*(\d+)\.(\d+)', label):
        refs.add(('s', f'{m[1]}.{m[2]}'))
    for m in re.finditer(r'\((\d+)\.(\d+)\.\d+(?:\.\d+)?\)', label):   # an equation number
        refs.add(('s', f'{m[1]}.{m[2]}'))
    for m in re.finditer(r'\b(\d+)\.(\d+)\.P\d+', label):           # a problem, `Problem 7.3.P7`
        refs.add(('s', f'{m[1]}.{m[2]}'))
    for m in re.finditer(r'\b[Cc]hapters?\s+(\d+)', label):
        refs.add(('c', m[1]))
    for m in re.finditer(r'\b[Ss]ections?\s+(\d+)\.(\d+)', label):
        refs.add(('s', f'{m[1]}.{m[2]}'))
    for m in ITEM_NO.finditer(label):
        n = same.get(m[0], m[0])
        refs.add(('i', n) if n in items else ('s', f'{m[1]}.{m[2]}'))
    return refs


def books_page(cfg, bib, decls):
    """The Books page: for each book of books.toml, its chapters, sections and numbered results,
    each with the results and declarations of the library that cite it."""
    out = []
    for book in cfg.get('book', []):
        key, same = book['key'], book.get('same', {})
        items = {n for ch in book['chapter'] for _, n, _ in ch.get('items', [])}
        cites = defaultdict(list)                    # ('i' | 's' | 'c', number) -> targets
        for d in decls:
            target = {'r': d['r'][0]} if d['r'] else {'d': d['n']}
            for k, label in d['ci']:
                if k != key:
                    continue
                for ref in book_refs(label, items, same) or {('b', '')}:
                    if target not in cites[ref]:
                        cites[ref].append(target)
        chapters = []
        for ch in book['chapter']:
            secs = [{'n': n, 'title': t, 'refs': cites.get(('s', n), []), 'items': []}
                    for n, t in ch.get('sections', [])]
            for kind, n, name in ch.get('items', []):
                sec = next((x for x in secs if n.startswith(x['n'] + '.')), None)
                item = {'k': kind, 'n': n, 'name': name, 'refs': cites.get(('i', same.get(n, n)), []),
                        'same': same.get(n)}
                if sec:
                    sec['items'].append(item)
                else:
                    secs.append({'n': n, 'title': '', 'refs': [], 'items': [item]})
            chapters.append({'n': ch['n'], 'title': ch['title'], 'refs': cites.get(('c', str(ch['n'])), []),
                             'sections': secs})
        n_items = sum(len(x['items']) for c in chapters for x in c['sections'])
        n_cov = sum(1 for c in chapters for x in c['sections'] for it in x['items'] if it['refs'])
        out.append({'key': key, 'short': book.get('short', key), 'url': book.get('url'),
                    'cite': bib.get(key, {}).get('text'), 'chapters': chapters,
                    'general': cites.get(('b', ''), []), 'items': n_items, 'covered': n_cov})
    return out


def required_text(row, fields, label):
    for field in fields:
        if not isinstance(row.get(field), str) or not row[field].strip():
            raise ValueError(f'{label}: empty or invalid {field}')


def unique_ids(rows, label):
    seen = set()
    for row in rows:
        required_text(row, ['id'], label)
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', row['id']):
            raise ValueError(f'{label}: unsafe id {row["id"]}')
        if row['id'] in seen:
            raise ValueError(f'{label}: duplicate id {row["id"]}')
        seen.add(row['id'])
    return seen


def rates_page(cfg, decls, index, targets):
    families = cfg.get('families', [])
    family_ids = unique_ids(families, 'rate family')
    reserved_filters = {'id', 'ids', 'theorem', 'family', 'statement_hash', 'hash', 'resources',
                        'overview', 'explicit', 'result', 'guarantee', 'notes', 'kind',
                        'doc', 'signature', 'statement', 'source', 'title', 'description', 'filters',
                        'algorithm_definition', 'sketch_definition', 'algorithm_definition_index',
                        'sketch_definition_index', 'algorithm_definition_label'}
    family_filters = {}
    family_subjects = {}
    out_families = []
    for family in families:
        required_text(family, ['title', 'description'], 'rate family')
        for label in ('subject_label', 'definition_label', 'notation', 'resources_label'):
            if label in family:
                required_text(family, [label], f'rate family {family["id"]}')
        subject = family.get('subject_field', 'algorithm')
        if not isinstance(subject, str) or not re.fullmatch(r'[a-z][a-z0-9_]*', subject) or subject in reserved_filters:
            raise ValueError(f'rate family {family["id"]}: unsafe or reserved subject_field')
        family_subjects[family['id']] = subject
        filters = family.get('filters', [])
        if not isinstance(filters, list):
            raise ValueError(f'rate family {family["id"]}: filters must be a list')
        seen = set()
        for item in filters:
            if not isinstance(item, dict):
                raise ValueError(f'rate family {family["id"]}: invalid filter')
            required_text(item, ['field', 'label'], f'rate family {family["id"]} filter')
            if 'order' in item:
                order = item['order']
                if not isinstance(order, list) or any(not isinstance(v, str) or not v.strip() for v in order):
                    raise ValueError(f'rate family {family["id"]}: filter order must contain nonempty strings')
                if len(order) != len(set(order)):
                    raise ValueError(f'rate family {family["id"]}: duplicate filter order values')
            field = item['field']
            if not re.fullmatch(r'[a-z][a-z0-9_]*', field) or field in reserved_filters:
                raise ValueError(f'rate family {family["id"]}: unsafe or reserved filter field {field}')
            if field in seen:
                raise ValueError(f'rate family {family["id"]}: duplicate filter field {field}')
            seen.add(field)
        family_filters[family['id']] = filters
        out_families.append({**family, 'filters': filters, 'subject_field': subject})
    guarantees = cfg.get('guarantees', [])
    guarantee_ids = unique_ids(guarantees, 'rate guarantee')
    out_guarantees = []
    guarantee_family = {}
    for guarantee in guarantees:
        required_text(guarantee, ['family', 'title', 'description'], 'rate guarantee')
        if guarantee['family'] not in family_ids:
            raise ValueError(f'rate guarantee {guarantee["id"]}: unknown family')
        links = guarantee.get('definitions', [])
        if not isinstance(links, list):
            raise ValueError(f'rate guarantee {guarantee["id"]}: invalid definitions')
        resolved_links = []
        for link in links:
            if not isinstance(link, dict):
                raise ValueError(f'rate guarantee {guarantee["id"]}: invalid definition link')
            required_text(link, ['label', 'declaration'], 'rate guarantee definition')
            i = index.get(link['declaration'])
            if i is None or decls[i]['kind'] not in DEF_KINDS:
                raise ValueError(f'rate guarantee {guarantee["id"]}: unknown definition {link["declaration"]}')
            resolved_links.append({**link, 'i': i})
        guarantee_family[guarantee['id']] = guarantee['family']
        out_guarantees.append({**guarantee, 'definitions': resolved_links})
    entries = cfg.get('rates', [])
    unique_ids(entries, 'rate')
    # explicit theorems that have an asymptotic form: an exact row must not cite one
    paired = set(targets.values())
    out = []
    for rate in entries:
        required_text(rate, ['theorem', 'family', 'algorithm', 'guarantee', 'statement_hash'], f'rate {rate["id"]}')
        if 'notes' in rate and not isinstance(rate['notes'], str):
            raise ValueError(f'rate {rate["id"]}: invalid notes')
        if rate['family'] not in family_ids:
            raise ValueError(f'rate {rate["id"]}: unknown family {rate["family"]}')
        exact = 'kind' in rate
        if exact and rate['kind'] != 'exact':
            raise ValueError(f'rate {rate["id"]}: unknown kind {rate["kind"]!r}')
        for key, value in rate.items():
            if key != 'resources' and (not isinstance(value, str) or (key != 'notes' and not value.strip())):
                raise ValueError(f'rate {rate["id"]}: empty or invalid scalar metadata {key}')
        required_text(rate, [family_subjects[rate['family']],
                             *[f['field'] for f in family_filters[rate['family']]]],
                      f'rate {rate["id"]} configured filter')
        if rate['guarantee'] not in guarantee_ids:
            raise ValueError(f'rate {rate["id"]}: unknown guarantee {rate["guarantee"]}')
        if guarantee_family[rate['guarantee']] != rate['family']:
            raise ValueError(f'rate {rate["id"]}: guarantee family mismatch')
        if 'algorithm_definition_label' in rate and 'algorithm_definition' not in rate:
            raise ValueError(f'rate {rate["id"]}: algorithm_definition_label without algorithm_definition')
        definition_links = {}
        for field in ('algorithm_definition', 'sketch_definition'):
            if field in rate:
                linked = index.get(rate[field])
                if linked is None or decls[linked]['kind'] not in DEF_KINDS:
                    raise ValueError(f'rate {rate["id"]}: unknown definition {rate[field]}')
                definition_links[field + '_index'] = linked
        i = index.get(rate['theorem'])
        if exact:
            # an exact identity: one theorem, no asymptotic declaration on either side
            if i is None or decls[i]['kind'] != 'theorem':
                raise ValueError(f'rate {rate["id"]}: missing exact theorem {rate["theorem"]}')
            if i in targets or i in paired:
                raise ValueError(f'rate {rate["id"]}: exact row cites a theorem with an asymptotic pairing; '
                                 'use an asymptotic row')
            j = i
        else:
            if i is None or i not in targets:
                raise ValueError(f'rate {rate["id"]}: missing asymptotic theorem {rate["theorem"]}')
            j = targets[i]
        d = decls[i]
        if not exact and not d['_results']:
            raise ValueError(f'rate {rate["id"]}: missing result membership')
        if d.get('sorry') or decls[j].get('sorry'):
            raise ValueError(f'rate {rate["id"]}: unproved declaration')
        digest = hashlib.sha256((HTML_COMMENT.sub('', d.get('signature') or '') + '\n' +
                                HTML_COMMENT.sub('', d.get('doc') or '')).encode('utf-8')).hexdigest()
        if rate['statement_hash'] != digest:
            raise ValueError(f'rate {rate["id"]}: statement_hash mismatch; review curated mathematics')
        resources = rate.get('resources')
        if not isinstance(resources, list) or not resources:
            raise ValueError(f'rate {rate["id"]}: resources must be nonempty')
        for resource in resources:
            if not isinstance(resource, dict):
                raise ValueError(f'rate {rate["id"]}: invalid resource')
            required_text(resource, ['label', 'bound'], f'rate {rate["id"]} resource')
        out.append({**rate, **definition_links, 'overview': i, 'explicit': j,
                    'result': d['_results'][0] if d['_results'] else None})
    return {'families': out_families, 'guarantees': out_guarantees, 'entries': out}


def collections_page(cfg, results, decls, index, modules, aliases):
    collections = cfg.get('collections', [])
    unique_ids(collections, 'collection')
    out = []
    curated_results = {aliases.get(rid, rid) for c in collections for g in c.get('groups', [])
                       for rid in g.get('results', [])}
    curated_defs = {name for c in collections for g in c.get('groups', [])
                    for name in g.get('definitions', [])}
    seen_topics = set()
    for collection in collections:
        required_text(collection, ['title', 'description', 'topic'], 'collection')
        topic = collection['topic']
        if not re.fullmatch(r'[A-Z][A-Za-z0-9]*', topic):
            raise ValueError(f'collection {collection["id"]}: unsafe topic {topic}')
        if topic in seen_topics:
            raise ValueError(f'duplicate collection topic {topic}')
        seen_topics.add(topic)
        groups = collection.get('groups', [])
        unique_ids(groups, f'collection {collection["id"]} group')
        used_results, used_defs, rendered = set(), set(), []
        for group in groups:
            required_text(group, ['title'], 'collection group')
            entries = []
            group_results, group_defs = set(), set()
            for rid in group.get('results', []):
                rid = aliases.get(rid, rid)
                if rid not in results:
                    raise ValueError(f'collection {collection["id"]}: unknown result {rid}')
                if rid in group_results:
                    raise ValueError(f'collection group {group["id"]}: duplicate result {rid}')
                group_results.add(rid)
                entries.append({'type': 'r', 'rid': rid})
                used_results.add(rid)
            for name in group.get('definitions', []):
                i = index.get(name)
                if i is None or decls[i]['kind'] not in DEF_KINDS:
                    raise ValueError(f'collection {collection["id"]}: unknown definition {name}')
                if decls[i].get('explorerRole') == 'support':
                    raise ValueError(f'collection group {group["id"]}: support definition {name}')
                if i in group_defs:
                    raise ValueError(f'collection group {group["id"]}: duplicate definition {name}')
                group_defs.add(i)
                entries.append({'type': 'd', 'i': i})
                used_defs.add(i)
            rendered.append({**group, 'entries': entries})
        topic = collection['topic']
        matches = lambda d: modules.get(d['module'], {}).get('topic') == topic
        fallback = [{'type': 'r', 'rid': rid} for rid, r in results.items()
                    if rid not in curated_results and any(matches(decls[i]) for i in r['decls'])]
        fallback += [{'type': 'd', 'i': i} for i, d in enumerate(decls)
                     if matches(d) and d['kind'] in DEF_KINDS
                     and d.get('explorerRole') != 'support' and d['name'] not in curated_defs]
        if fallback:
            if any(g['id'] == 'other' for g in groups):
                raise ValueError(f'collection {collection["id"]}: reserved fallback group id other')
            rendered.append({'id': 'other', 'title': 'Other results and definitions', 'entries': fallback})
        out.append({**collection, 'groups': rendered})
    return out


def build(data, bib, out):
    topics_cfg = load_toml('topics.toml')
    results_cfg = load_toml('results.toml')
    synonyms = load_toml('synonyms.toml').get('synonyms', {})

    decls = data['decls']
    index = {d['name']: i for i, d in enumerate(decls)}
    # HTML comments in docstrings (NLAlib's value markers, `<!-- value NAME ... -->`) are invisible
    # in doc-gen4's Markdown; the explorer escapes HTML, so they are removed here
    for item in decls + data['modules']:
        if item.get('doc'):
            item['doc'] = HTML_COMMENT.sub('', item['doc'])

    # --- modules and the topic tree
    modules = {}
    tree = defaultdict(lambda: defaultdict(list))
    for m in data['modules']:
        title, summary = module_doc_parts(m.get('doc'))
        top, sub = topic_of(m['name'], topics_cfg)
        if top is None:
            continue
        modules[m['name']] = {'path': m['path'], 'title': title or humanize(m['name'].split('.')[-1]),
                              'summary': summary, 'topic': top, 'sub': sub,
                              'imports': m.get('imports', [])}
        tree[top][sub].append(m['name'])

    def cfg_for(key):
        node = topics_cfg
        for part in key.split('/'):
            node = node.get(part, {}) if isinstance(node, dict) else {}
        return node if isinstance(node, dict) else {}

    layer_order = topics_cfg.get('order', [])

    def top_rank(t):
        return (layer_order.index(t) if t in layer_order else len(layer_order), t)

    topics = []
    for top in sorted(tree, key=top_rank):
        tc = cfg_for(top)
        subs = []
        sub_order = tc.get('order', [])
        for sub in sorted(tree[top], key=lambda s: (s.split('/')[1] not in ('General', 'Basic'),
                                                    sub_order.index(s.split('/')[1]) if s.split('/')[1] in sub_order else len(sub_order),
                                                    s)):
            sc = cfg_for(sub)
            name = sub.split('/')[1]
            subs.append({'id': sub, 'title': sc.get('title', humanize(name)), 'blurb': sc.get('blurb', ''),
                         'modules': sorted(tree[top][sub])})
        topics.append({'id': top, 'title': tc.get('title', humanize(top)), 'blurb': tc.get('blurb', ''), 'subs': subs})

    # Resolve metadata before grouping: a corollary inherits all target result ids.
    targets = {}
    for i, d in enumerate(decls):
        matches = ASYMPTOTIC_LINE.findall(d.get('doc') or '')
        if len(re.findall(r'Asymptotic:', d.get('doc') or '')) != len(matches):
            raise ValueError(f"malformed Asymptotic metadata: {d['name']}")
        if len(matches) > 1:
            raise ValueError(f"multiple Asymptotic targets: {d['name']}")
        if matches:
            if matches[0] not in index:
                raise ValueError(f"unresolved Asymptotic target: {matches[0]}")
            targets[i] = index[matches[0]]
        result_lines = RESULT_LINE.findall(d.get('doc') or '')
        if len(re.findall(r'Result:', d.get('doc') or '')) != len(result_lines) or any(
                not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', part.strip())
                for line in result_lines for part in line.split(',')):
            raise ValueError(f"malformed Result metadata: {d['name']}")
        d['_results'] = list(dict.fromkeys(x.strip()
            for line in RESULT_LINE.findall(d.get('doc') or '')
            for x in line.split(',') if x.strip()))
    original_results = {i: list(d['_results']) for i, d in enumerate(decls)}
    resolved = set()

    def inherit(i, stack=()):
        if i in stack:
            raise ValueError(f"cyclic Asymptotic target: {decls[i]['name']}")
        if i in resolved:
            return
        if i in targets:
            j = targets[i]
            inherit(j, stack + (i,))
            decls[i]['_results'] = list(dict.fromkeys(
                decls[i]['_results'] + decls[j]['_results']))
        resolved.add(i)

    for i in range(len(decls)):
        inherit(i)
    for i in targets:
        if not decls[i]['_results']:
            raise ValueError(f"Asymptotic pair has no Result id: {decls[i]['name']} -> {decls[targets[i]]['name']}")
    results = {}
    for i, d in enumerate(decls):
        for rid in d['_results']:
            results.setdefault(rid, {'decls': [], 'bold': Counter(), 'phrase': Counter()})
            results[rid]['decls'].append(i)
            p = split_doc(d.get('doc'), index)
            d['_name'] = p['name']
            if rid not in original_results[i] or i in targets:
                continue
            if p['name']:
                results[rid]['bold'][p['name']] += 1
            elif p['phrase']:
                results[rid]['phrase'][p['phrase']] += 1

    # ids naming exactly the same declarations (`Result: schur-complement-psd, albert-theorem`)
    # are one result under the first id; the others are kept as aliases
    alias = {}
    by_decls = {}
    for rid, r in results.items():
        key = tuple(r['decls'])
        if key in by_decls:
            alias[rid] = by_decls[key]
        else:
            by_decls[key] = rid
    for rid, canon in alias.items():
        gone = results.pop(rid)
        results[canon]['bold'] += gone['bold']
        results[canon]['phrase'] += gone['phrase']
        results[canon].setdefault('ids', []).append(rid)
    for d in decls:
        d['_results'] = list(dict.fromkeys(alias.get(x, x) for x in d['_results']))

    for configured_id, cfg in results_cfg.items():
        for field in ('primary', 'variant_labels'):
            if field in cfg and configured_id not in results:
                raise ValueError(f'result {configured_id}: {field} configured for unknown or alias result')
    out_results = {}
    for rid, r in results.items():
        cfg = results_cfg.get(rid, {})
        title = cfg.get('title') or result_title(r['bold'], rid, r['phrase'])
        # the declaration the title names comes first: its statement is the result's
        named = lambda j: (decls[j].get('_name') or '').split(',')[0].strip() == title.split(',')[0].strip()
        r['decls'].sort(key=lambda j: not named(j))
        primary = next((j for j in r['decls']
                        if j not in targets and any(alias.get(x, x) == rid
                                                   for x in original_results[j])), r['decls'][0])
        if 'primary' in cfg:
            required_text(cfg, ['primary'], f'result {rid}')
            preferred = index.get(cfg['primary'])
            if preferred is None or preferred not in r['decls'] or preferred in targets:
                raise ValueError(f'result {rid}: primary must name an explicit member')
            primary = preferred
        forms = [{'overview': i, 'explicit': targets[i]}
                 for i in sorted(r['decls']) if i in targets]
        forms.sort(key=lambda f: f['explicit'] != primary)
        pair = forms[0] if forms else {'overview': primary, 'explicit': primary}
        out_results[rid] = {'title': title, 'aliases': cfg.get('aliases', []), 'latex': cfg.get('latex'),
                            'ids': r.get('ids', []), 'overview': pair['overview'],
                            'explicit': pair['explicit'], 'forms': forms,
                            'decls': r['decls'], 'module': decls[primary]['module']}
        if 'variant_labels' in cfg:
            # curated Variant dropdown labels, one per form in the built order above
            labels = cfg['variant_labels']
            if not isinstance(labels, list) or len(labels) != len(forms):
                raise ValueError(f'result {rid}: variant_labels must list one label per form '
                                 f'({len(forms)} forms)')
            if not all(isinstance(x, str) and x.strip() for x in labels):
                raise ValueError(f'result {rid}: variant_labels must be nonempty strings')
            out_results[rid]['variantLabels'] = [x.strip() for x in labels]

    # --- graph nodes: a result (all its declarations together) or a documented definition.
    # Every other declaration is a helper; dependencies are collapsed through helpers.
    def node_of(i):
        d = decls[i]
        if d['_results']:
            return 'r:' + d['_results'][0]
        if d.get('explorerRole') == 'support':
            return None
        if d['kind'] in DEF_KINDS:
            return 'd:' + d['name']
        return None

    direct = []
    for d in decls:
        deps = [index[n] for n in d.get('typeDeps', []) + d.get('valueDeps', []) if n in index]
        direct.append(deps)

    memo = {}

    def notable_deps(i, stack=()):
        if i in memo:
            return memo[i]
        acc = set()
        for j in direct[i]:
            if j == i or j in stack:
                continue
            nj = node_of(j)
            if nj:
                acc.add(nj)
            else:
                acc |= notable_deps(j, stack + (i,))
        memo[i] = acc
        return acc

    uses = defaultdict(set)
    for i in range(len(decls)):
        n = node_of(i)
        if n:
            uses[n] |= notable_deps(i)
    for n in list(uses):
        uses[n].discard(n)
    used_by = defaultdict(set)
    for n, us in uses.items():
        for u in us:
            used_by[u].add(n)

    # reverse direct dependencies, declaration level
    rdirect = defaultdict(set)
    for i, deps in enumerate(direct):
        for j in deps:
            if j != i:
                rdirect[j].add(i)

    out_decls = []
    for i, d in enumerate(decls):
        td = [index[n] for n in d.get('typeDeps', []) if n in index]
        vd = [index[n] for n in d.get('valueDeps', []) if n in index]
        p = split_doc(d.get('doc'), index)
        out_decls.append({
            'role': ('support' if d.get('explorerRole') == 'support' else
                     'concept' if d['kind'] in DEF_KINDS else 'lemma'),
            'n': d['name'], 'm': d['module'], 'k': d['kind'], 'l': d.get('line'), 'e': d.get('endLine'),
            'doc': d.get('doc'), 'sig': d.get('signature'), 'st': d.get('statement'),
            'r': d['_results'], 's': bool(d.get('sorry')), 'td': td, 'vd': vd,
            'rd': sorted(rdirect[i]), 'fs': first_sentence(p['stmt']),
            'nm': p['name'], 'stmt': p['stmt'], 'ci': p['cites'], 'cn': p['cnotes'],
            'rel': p['rel'], 'no': p['notes'], 'pf': p['proof'],
            'bv': bold_letters(d.get('signature'), [p['stmt'], *p['rel'], p['proof'], *p['cnotes']], p['bold']),
        })

    nodes = {n: {'u': sorted(uses.get(n, ())), 'b': sorted(used_by.get(n, ()))}
             for n in set(uses) | set(used_by)}

    cited = set()
    for d in decls:
        cited |= set(re.findall(r'\[([A-Z][A-Za-z]+\d{4}[a-z]?)[\],]', d.get('doc') or ''))
    for m in data['modules']:
        cited |= set(re.findall(r'\[([A-Z][A-Za-z]+\d{4}[a-z]?)[\],]', m.get('doc') or ''))

    collections = collections_page(load_toml('collections.toml'), out_results, decls, index, modules, alias)
    for collection in collections:
        if not any(t['id'] == collection['topic'] for t in topics):
            tc = cfg_for(collection['topic'])
            topics.append({'id': collection['topic'], 'title': tc.get('title', collection['title']),
                           'blurb': tc.get('blurb', collection['description']), 'subs': []})
    topics.sort(key=lambda t: top_rank(t['id']))
    site = {
        'commit': data.get('commit'), 'date': data.get('date'), 'repo': REPO,
        'ref': data.get('commit') or topics_cfg.get('ref', 'scaffold'),
        'topics': topics, 'modules': modules, 'results': out_results, 'decls': out_decls,
        'resultAlias': alias,
        'nodes': nodes, 'bib': {k: v for k, v in bib.items() if k in cited},
        'synonyms': synonyms,
        'rates': rates_page(load_toml('rates.toml'), decls, index, targets),
        'collections': collections,
        'books': books_page(load_toml('books.toml'), bib, out_decls),
    }

    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT / 'web', out)
    (out / 'data.json').write_text(json.dumps(site, ensure_ascii=False, separators=(',', ':')))
    page = cache_busted((ROOT / 'web' / 'index.html').read_text(), out)
    (out / 'index.html').write_text(page)
    # the Books page is the same app one directory down, at books/
    page = re.sub(r'(href|src)="(?!data:|https?:|#)([^"]+)"', r'\1="../\2"', page)
    page = page.replace('".././"', '"../"')
    page = page.replace('<body ', '<body data-page="books" data-base="../" ', 1)
    (out / 'books').mkdir()
    (out / 'books' / 'index.html').write_text(page)
    rates_html = page.replace('data-page="books"', 'data-page="rates"')
    rates_html = re.sub(r'<title>.*?</title>', '<title>Rates · NLAlib explorer</title>', rates_html, flags=re.S)
    (out / 'rates').mkdir()
    (out / 'rates' / 'index.html').write_text(rates_html)
    n_def = sum(1 for d in decls if d['kind'] in DEF_KINDS)
    print(f'{len(modules)} modules, {len(decls)} declarations, {len(out_results)} results, '
          f'{n_def} definitions -> {out}/ ({(out / "data.json").stat().st_size // 1024} KB data)')


def cache_busted(page, out):
    """Append a content hash to the page's local scripts, stylesheets and its data.json fetch.

    Browsers keep the previous deploy's app.js or data.json otherwise, and show stale text."""
    def version(name):
        return hashlib.sha256((out / name).read_bytes()).hexdigest()[:10]
    page = re.sub(r'(href|src)="((?:app|math)\.js|style\.css)"',
                  lambda m: f'{m[1]}="{m[2]}?v={version(m[2])}"', page)
    return page.replace('<body>', f'<body data-version="{version("data.json")}">', 1)


def whole_definitions(decls, src):
    """The data's `statement` stops at `:=`, which for a theorem leaves out only the proof; for a
    definition it leaves out the definition itself. Take a definition's whole text from the
    library source (its lines `line`..`endLine`, from where its statement starts), wherever the
    source agrees with the statement; elsewhere the statement stays as it is."""
    files, n = {}, 0
    for d in decls:
        if d['kind'] not in DEF_KINDS or not d.get('statement') or not d.get('line'):
            continue
        path = Path(src) / (d['module'].replace('.', '/') + '.lean')
        if path not in files:
            files[path] = path.read_text().split('\n') if path.exists() else None
        if not files[path]:
            continue
        text = '\n'.join(files[path][d['line'] - 1:d['endLine']]).rstrip()
        k = text.find(d['statement'].split('\n')[0].strip())
        if k >= 0 and text[k:].startswith(d['statement'].strip()[:40]) and len(text) - k > len(d['statement']):
            d['statement'] = text[k:]
            n += 1
    return n


def validate_sources(data, src):
    """Verify extraction-time bytes before trusting source line ranges, including tarballs."""
    hashes = data.get('sourceHashes')
    if hashes is None:
        print('warning: legacy data has no sourceHashes; skipping definition body enrichment',
              file=sys.stderr)
        return False
    expected = {m['path'] for m in data['modules']}
    if not isinstance(hashes, dict) or set(hashes) != expected:
        raise ValueError('sourceHashes must cover exactly all listed modules')
    for d in data.get('decls', []):
        path = d['module'].replace('.', '/') + '.lean'
        if path not in hashes:
            raise ValueError(f'sourceHashes missing declaration module: {path}')
    root = Path(src).resolve()
    for name, digest in hashes.items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or not path.parts or path.suffix != '.lean':
            raise ValueError(f'unsafe source path: {name}')
        full = (root / path).resolve()
        if not full.is_relative_to(root):
            raise ValueError(f'unsafe source path: {name}')
        if not full.is_file() or hashlib.sha256(full.read_bytes()).hexdigest() != digest:
            raise ValueError(f'source hash mismatch: {name}')
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--data', default=ROOT / 'data' / 'explore-data.json')
    ap.add_argument('--bib', default=None, help="NLAlib's docs/references.bib")
    ap.add_argument('--out', default=ROOT / 'site')
    ap.add_argument('--src', default=None,
                    help="an NLAlib checkout at the data's commit, for the bodies of definitions")
    a = ap.parse_args()
    data = json.loads(Path(a.data).read_text())
    if data.get('schema') != 1:
        raise SystemExit(f"unsupported data schema {data.get('schema')!r}")
    if a.src and validate_sources(data, a.src):
        print(f"{whole_definitions(data['decls'], a.src)} definitions given whole from {a.src}")
    build(data, parse_bib(a.bib), a.out)


if __name__ == '__main__':
    main()
