#!/usr/bin/env python3
"""Build the NLA-lib explorer, a static site, from NLAlib's extracted data.

    python3 build.py [--data data/explore-data.json] [--bib PATH] [--out site]

Inputs:
  data/explore-data.json  written by NLAlib's scripts/Explore.lean (in CI, downloaded from the
                          rolling `explore-data` release of NLA-lib/NLAlib)
  --bib                   NLAlib's docs/references.bib at the same commit (optional)
  topics.toml             titles, order and blurbs for the library's directories (optional per
                          directory: a directory without an entry gets a title from its name)
  results.toml            per `Result:` id overrides: title, aliases, latex (all optional)
  synonyms.toml           search synonyms, mathematical words to library names

Output: <out>/index.html, <out>/data.json and the static assets in web/.

Everything that can be read from the library is read from it; the three TOML files only add
what the Lean source does not say, and the build works with all three empty.
"""

import argparse
import json
import re
import shutil
import tomllib
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = 'https://github.com/NLA-lib/NLAlib'

DEF_KINDS = {'def', 'abbrev', 'opaque', 'structure', 'class', 'inductive'}
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
    return RESULT_LINE.sub('', doc).rstrip() if doc else doc


def sentences(text):
    """Split prose into sentences at '. ' (or ': ' before a capital is not a split), never inside
    backticks, dollars or brackets."""
    out, start, tick, dollar, depth = [], 0, False, False, 0
    for i, ch in enumerate(text):
        if ch == '`':
            tick = not tick
        elif ch == '$' and not tick:
            dollar = not dollar
        elif tick or dollar:
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
    return sorted((mat | set(prose_bold) | auto | used) - (other - mat))


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


def build(data, bib, out):
    topics_cfg = load_toml('topics.toml')
    results_cfg = load_toml('results.toml')
    synonyms = load_toml('synonyms.toml').get('synonyms', {})

    decls = data['decls']
    index = {d['name']: i for i, d in enumerate(decls)}

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

    # --- results, from the `Result:` lines of the docstrings
    results = {}
    for i, d in enumerate(decls):
        ids = []
        for line in RESULT_LINE.findall(d.get('doc') or ''):
            ids += [x.strip() for x in line.split(',') if x.strip()]
        d['_results'] = ids
        for rid in ids:
            results.setdefault(rid, {'decls': [], 'bold': Counter(), 'phrase': Counter()})
            results[rid]['decls'].append(i)
            p = split_doc(d.get('doc'), index)
            d['_name'] = p['name']
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

    out_results = {}
    for rid, r in results.items():
        cfg = results_cfg.get(rid, {})
        title = cfg.get('title') or result_title(r['bold'], rid, r['phrase'])
        # the declaration the title names comes first: its statement is the result's
        named = lambda j: (decls[j].get('_name') or '').split(',')[0].strip() == title.split(',')[0].strip()
        r['decls'].sort(key=lambda j: not named(j))
        primary = r['decls'][0]
        out_results[rid] = {'title': title, 'aliases': cfg.get('aliases', []), 'latex': cfg.get('latex'),
                            'ids': r.get('ids', []),
                            'decls': r['decls'], 'module': decls[primary]['module']}

    # --- graph nodes: a result (all its declarations together) or a documented definition.
    # Every other declaration is a helper; dependencies are collapsed through helpers.
    def node_of(i):
        d = decls[i]
        if d['_results']:
            return 'r:' + d['_results'][0]
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

    site = {
        'commit': data.get('commit'), 'date': data.get('date'), 'repo': REPO,
        'ref': data.get('commit') or topics_cfg.get('ref', 'scaffold'),
        'topics': topics, 'modules': modules, 'results': out_results, 'decls': out_decls,
        'resultAlias': alias,
        'nodes': nodes, 'bib': {k: v for k, v in bib.items() if k in cited},
        'synonyms': synonyms,
    }

    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT / 'web', out)
    (out / 'data.json').write_text(json.dumps(site, ensure_ascii=False, separators=(',', ':')))
    n_def = sum(1 for d in decls if d['kind'] in DEF_KINDS)
    print(f'{len(modules)} modules, {len(decls)} declarations, {len(out_results)} results, '
          f'{n_def} definitions -> {out}/ ({(out / "data.json").stat().st_size // 1024} KB data)')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--data', default=ROOT / 'data' / 'explore-data.json')
    ap.add_argument('--bib', default=None, help="NLAlib's docs/references.bib")
    ap.add_argument('--out', default=ROOT / 'site')
    a = ap.parse_args()
    data = json.loads(Path(a.data).read_text())
    if data.get('schema') != 1:
        raise SystemExit(f"unsupported data schema {data.get('schema')!r}")
    build(data, parse_bib(a.bib), a.out)


if __name__ == '__main__':
    main()
