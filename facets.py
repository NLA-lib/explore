"""Facets of NLAlib's probabilistic bounds, read from declaration names.

The library names a theorem after its conclusion (CONTRIBUTING §4), so a bound on a randomized
algorithm reads like a sentence of a small grammar:

    [exists_forall_] (integral | measureReal[_not] | measure[_not] | variance) _
        [abs_ | norm_] <measure> _sub_ [truncatedSVD_] <algorithm> [_sq]
        _(le | lt | ge | gt | eq) [_le] [_<shape>] _of_<law> [_of_<hypothesis> ...]

with an interface namespace (`HasSubspaceInjection.`) standing for "any sketch with that
property". `infer` turns a name into a facet record: statistic, moment, error measure,
algorithm, sketch law, output, regime and details. It returns None for a name outside the
grammar (deterministic theory), which is shown by its docstring name instead.

The grammar is deliberately loose where the library has variants today, so a later naming
cleanup does not break it: tails are recognised as `measureReal_not_X_le_le`,
`measureReal_X_gt_le`, `measureReal_X_ge_le` and the same with `measure_`; `_sq` counts
anywhere before the first relation; the algorithm may come from the statement's dependencies
when the name does not spell it (`…_of_isBestRankApprox`).

`facets.toml` (explorer configuration) overrides any facet of a named declaration, sets its
table label, and gives short names for citation keys.
"""

import re

# ------------------------------------------------------------------ value maps (token -> label)
# Order matters: longer or more specific tokens first.

# (name token, algorithm label, output implied by the token)
ALGORITHMS = [
    ('earlyTruncatedGeneralizedNystrom', 'GN', 'early'),
    ('earlyTruncatedRSVD', 'RSVD', 'early'),
    ('generalizedNystrom', 'GN', None),
    ('nystromBKI', 'NysBKI', None),
    ('nystrom_pow_mul', 'NysSI', None),
    ('nystrom', 'Nyström', None),
    ('rsvd_pow_mul', 'RSI', None),
    ('rsvd_aeval', 'filtered RSVD', None),
    ('rbki', 'RBKI', None),
    ('rsvd', 'RSVD', None),
    ('sketchAndSolve', 'sketch-and-solve', None),
    ('hutchpp', 'Hutch++', None),
    ('girardHutchinson', 'Girard–Hutchinson', None),
]
# the algorithm's definition among a statement's dependencies, when the name does not say
ALGORITHM_DEFS = {
    'NLAlib.earlyTruncatedGeneralizedNystrom': ('GN', 'early'),
    'NLAlib.earlyTruncatedRSVD': ('RSVD', 'early'),
    'NLAlib.generalizedNystrom': ('GN', None),
    'NLAlib.nystromBKI': ('NysBKI', None),
    'NLAlib.nystrom': ('Nyström', None),
    'NLAlib.rbki': ('RBKI', None),
    'NLAlib.rsvd': ('RSVD', None),
    'NLAlib.sketchAndSolve': ('sketch-and-solve', None),
    'NLAlib.hutchpp': ('Hutch++', None),
    'NLAlib.girardHutchinson': ('Girard–Hutchinson', None),
}

# (name token, key, label, TeX of the norm of an error `·`); the label is what a table group
# heading says, the TeX goes into the statistic's formula
MEASURES = [
    ('matrixNorm_conjTranspose_mul_self', 'gram', 'Every unitarily invariant norm, Gram form',
     r'\|(\cdot)^{\mathsf H}(\cdot)\|_\Phi'),
    ('matrixNorm', 'ui', 'Every unitarily invariant norm', r'\|\cdot\|_\Phi'),
    ('frobNorm', 'frobenius', 'Frobenius norm', r'\|\cdot\|_{\mathsf F}'),
    ('specNorm', 'spectral', 'Spectral norm', r'\|\cdot\|_2'),
    ('schattenNorm', 'schatten', 'Schatten norms', r'\|\cdot\|_{S_p}'),
    ('nuclearNorm', 'nuclear', 'Nuclear norm', r'\|\cdot\|_*'),
    ('kyFanNorm', 'kyfan', 'Ky Fan norms', r'\|\cdot\|_{(k)}'),
    ('quadForm', 'quadform', 'Quadratic form', None),
    ('trace', 'trace', 'Trace', None),
    ('norm', 'vector', 'Vector norm', r'\|\cdot\|'),
]
# the order of a statements table's groups
MEASURE_ORDER = ['frobenius', 'spectral', 'schatten', 'nuclear', 'kyfan', 'ui', 'gram', 'vector', 'abs',
                 'quadform', 'trace']

# sketch or probe laws, as `_of_<token>` hypotheses
LAWS = [
    ('hasLaw_gaussianMatrix', 'Gaussian'), ('hasLaw_gaussianVector', 'Gaussian'),
    ('hasGaussianLaw', 'Gaussian'), ('isLeftUnitarilyInvariant', 'rotation-invariant'),
    ('hasLaw_haarFrame', 'Haar'), ('hasLaw_countSketch', 'CountSketch'),
    ('isSubgaussianVector', 'sub-Gaussian'),
    ('hasLaw_srhtWithReplacement', 'SRHT, with replacement'), ('hasLaw_srht', 'SRHT'),
    ('hasLaw_samplingSketchWithoutReplacement', 'uniform sampling without replacement'),
    ('hasLaw_samplingSketch', 'leverage-score sampling'),
    ('hasLaw_rademacherMatrix', 'Rademacher'), ('hasLaw_rademacherVector', 'Rademacher'),
    ('hasLaw_uniformSphereVector', 'uniform on the sphere'),
    ('hasLaw_uniformOn_injective', 'sampling without replacement'),
]
LAW_ORDER = list(dict.fromkeys(lab for _, lab in LAWS))
# an interface namespace: the theorem holds for any sketch with the property
INTERFACES = {
    'HasSubspaceInjection': 'any subspace injection',
    'IsObliviousSubspaceInjection': 'any OSI',
    'HasJLMoment': 'any sketch with JL moments',
    'HasProjectionCostPreserving': 'any PCP sketch',
    'HasJLProperty': 'any JL sketch',
    'IsIsotropic': 'any isotropic probe',
    'IsSubgaussianVector': 'sub-Gaussian',
}

OUTPUTS = {'plain': 'plain', 'late': 'late-truncated', 'early': 'early-truncated'}
OUTPUT_ORDER = ['plain', 'late', 'early']

# tokens anywhere in the name that qualify a bound beyond the facets above
DETAILS = [
    ('isBestRankApprox', 'any best rank-k approximation of the output'),
    ('pinvSpecNormBound', 'HMT 10.6 form'),
    ('of_rank_le', 'low-rank input, sharp'),
    ('of_specNorm_le', 'bounded sketch'),
]

# the shape of a bound, as the words after the conclusion's last relation spell it
SHAPES = {
    'add': 'additive form',
    'one_add_mul': '(1 + ε) form',
    'one_add_sq_mul': '(1 + ε) form',
    'mul': 'constant factor',
}

RELATIONS = ('le', 'lt', 'ge', 'gt', 'eq')
STATISTIC_ORDER = ['expectation', 'tail', 'variance']

PREFIX = re.compile(r'(exists_forall_)?(integral|measureReal|measure|variance)(_not)?(?:_|$)(.*)$')


def _has(token, text):
    return re.search(r'(?:^|_)' + re.escape(token) + r'(?:_|$)', text) is not None


def _measure_in(part):
    """The first error measure named in a part of a name, with whether it is squared there."""
    hits = []
    for tok, key, _, _ in MEASURES:
        m = re.search(r'(?:^|_)' + re.escape(tok) + r'(?:_|$)', part)
        if m:
            hits.append((m.start(), -len(tok), key))
    if not hits:
        return None
    return min(hits)[2]


def infer(name, type_deps=()):
    """The facets of a probabilistic theorem, from its full name (and the names its statement
    uses); None when the name does not follow the bound grammar."""
    parts = name.split('.')
    short = parts[-1]
    namespaces = parts[:-1]
    m = PREFIX.match(short)
    if not m:
        return None
    asym, stat, negated, rest = m.groups()
    # the conclusion is what precedes the first hypothesis, `_of_…`
    head = re.split(r'_of_', rest, maxsplit=1)[0]
    words = head.split('_')
    rel_at = next((k for k, w in enumerate(words) if w in RELATIONS), len(words))
    relation = words[rel_at] if rel_at < len(words) else None
    before = words[:rel_at]
    f = {'form': 'asymptotic' if asym else 'explicit'}
    if stat == 'integral':
        f['statistic'] = 'expectation'
        f['exact'] = relation in (None, 'eq')
    elif stat == 'variance':
        f['statistic'] = 'variance'
        f['exact'] = relation in (None, 'eq')
    else:
        f['statistic'] = 'tail'
        f['exact'] = False
    # the error measure(s): the first norm of the conclusion; a sum `X_add_Y` names two
    conclusion = '_'.join(before)
    terms = re.split(r'_add_(?=(?:' + '|'.join(t for t, *_ in MEASURES) + r')(?:_|$))', conclusion)
    measures, moments = [], []
    if before[:1] == ['abs'] or re.search(
            r'(?:^|_)abs_(?:' + '|'.join(re.escape(t) for t, _, _ in ALGORITHMS) + r')_sub(?:_|$)', head):
        # `abs_hutchpp_sub_trace`: the absolute error of a scalar estimate, also when a scale
        # comes first (`mul_nuclearNorm_lt_abs_hutchpp_sub_trace`: ε‖A‖_* < |hutchpp − tr A|)
        measures, moments = ['abs'], [2 if _has('sq', conclusion) else 1]
    else:
        for term in terms:
            key = _measure_in(term)
            if key:
                measures.append(key)
                moments.append(2 if _has('sq', term) else 1)
    f['measure'] = '+'.join(measures) or None
    f['moment'] = moments[0] if len(set(moments)) == 1 else (max(moments) if moments else None)
    if f['statistic'] == 'variance':
        f['moment'] = None
    # algorithm and output
    alg = next(((tok, a, out) for tok, a, out in ALGORITHMS if _has(tok, rest)), None)
    out = None
    if alg:
        f['algorithm'], out = alg[1], alg[2]
    else:
        dep = next((ALGORITHM_DEFS[d] for d in type_deps if d in ALGORITHM_DEFS), None)
        f['algorithm'], out = (dep if dep else (None, None))
    if f['algorithm']:
        if out is None and ((alg and re.search(r'truncatedSVD_' + re.escape(alg[0]), rest)) or
                            _has('isBestRankApprox', rest) or
                            (not alg and _has('truncatedSVD', conclusion))):
            out = 'late'
        f['output'] = out or 'plain'
    else:
        f['output'] = None
    # law: a hypothesis token, else the interface namespace
    f['law'] = next((lab for tok, lab in LAWS if _has(tok, rest)), None)
    if not f['law']:
        f['law'] = next((INTERFACES[n] for n in reversed(namespaces) if n in INTERFACES), None)
    f['regime'] = 'gapped' if _has('singularGapRatio', rest) else None
    f['details'] = [lab for tok, lab in DETAILS if _has(tok, rest)]
    last = max((k for k, w in enumerate(words) if w in RELATIONS), default=None)
    if last is not None and '_'.join(words[last + 1:]) in SHAPES:
        f['details'].append(SHAPES['_'.join(words[last + 1:])])
    return f


# sketch properties, `[exists_forall_]<property>_of_<law>`: outside the bound grammar, but their
# asymptotic forms are sample-size rates (the Rates page)
PROPERTIES = [
    ('hasJLProperty', 'Distributional JL'),
    ('isObliviousSubspaceEmbedding', 'Oblivious subspace embedding'),
    ('hasSubspaceEmbedding', 'Subspace embedding'),
    ('isObliviousSubspaceInjection', 'Oblivious subspace injection'),
    ('hasSubspaceInjection', 'Subspace injection'),
    ('hasProjectionCostPreserving', 'Projection-cost preservation'),
]
PROPERTY_PREFIX = re.compile(r'(exists_forall_)?(' + '|'.join(t for t, _ in PROPERTIES) + r')(?:_of_(.*))?$')


def infer_property(name):
    """The facets of a sketch-property theorem (`exists_forall_hasJLProperty_of_hasLaw_srht`):
    the property stands in the algorithm's place and the statistic is a tail bound (a
    failure probability); None for any other name."""
    parts = name.split('.')
    m = PROPERTY_PREFIX.match(parts[-1])
    if not m:
        return None
    asym, token, rest = m.groups()
    rest = rest or ''
    law = next((lab for tok, lab in LAWS if _has(tok, rest)), None)
    if not law:
        law = next((INTERFACES[n] for n in reversed(parts[:-1]) if n in INTERFACES), None)
    return {'form': 'asymptotic' if asym else 'explicit', 'statistic': 'tail', 'exact': False,
            'measure': None, 'moment': None, 'algorithm': dict(PROPERTIES)[token], 'output': None,
            'law': law, 'regime': None, 'details': [], 'property': True}


def statistic_key(f):
    """The statistic without its norm, as the Rates filter offers it."""
    stat = (f or {}).get('statistic')
    if stat == 'expectation':
        return 'expectation-2' if f.get('moment') == 2 else 'expectation-1'
    return stat


# the statistic filter's options: formula first, then the approved words
STATISTIC_LABELS = {
    'expectation-2': 'E‖·‖² · expected error',
    'expectation-1': 'E‖·‖ · expected error',
    'tail': 'ℙ[·] · tail bound',
    'variance': 'Var · variance',
}
STATISTIC_WORDS = {'expectation': 'expected error', 'tail': 'tail bound', 'variance': 'variance'}


def apply_override(f, override):
    """A facets.toml entry on top of the inferred record (or on nothing, for a name outside the
    grammar). Unknown keys are an error."""
    allowed = {'statistic', 'moment', 'measure', 'algorithm', 'output', 'law', 'regime', 'details',
               'exact', 'label'}
    bad = set(override) - allowed
    if bad:
        raise ValueError(f'facets.toml: unknown facet keys {sorted(bad)}')
    out = dict(f or {'form': 'explicit', 'statistic': None, 'exact': False, 'measure': None,
                     'moment': None, 'algorithm': None, 'output': None, 'law': None,
                     'regime': None, 'details': []})
    for k, v in override.items():
        if k == 'details':
            v = [v] if isinstance(v, str) else list(v)
        out[k] = v
    if 'statistic' in override and override['statistic'] not in (*STATISTIC_ORDER, None):
        raise ValueError(f'facets.toml: unknown statistic {override["statistic"]!r}')
    if 'output' in override and override['output'] not in (*OUTPUTS, None):
        raise ValueError(f'facets.toml: unknown output {override["output"]!r}')
    if 'measure' in override and override['measure'] is not None:
        for key in str(override['measure']).split('+'):
            if key not in MEASURE_ORDER and key != 'abs':
                raise ValueError(f'facets.toml: unknown measure {key!r}')
    return out


# ------------------------------------------------------------------ labels

MEASURE_LABEL = {key: label for _, key, label, _ in MEASURES}
MEASURE_LABEL['abs'] = 'Absolute error'
NORM_TEX = {key: tex for _, key, _, tex in MEASURES}
NORM_TEX['abs'] = r'|\cdot|'


def measure_label(key):
    if not key:
        return None
    return ' + '.join(MEASURE_LABEL.get(k, k) for k in key.split('+')).replace(
        ' norm + ', ' + ').replace('norm +', '+')


def statistic_tex(f):
    """The statistic as a formula, in the approved vocabulary: E‖·‖² and E‖·‖ for expected
    errors, ℙ[‖·‖ > t] for tail bounds, Var for variances."""
    stat = f.get('statistic')
    if not stat:
        return None
    if f.get('property'):
        return r'$\mathbb{P}[\text{failure}]$'
    if stat == 'variance':
        return r'$\operatorname{Var}$' + (' (exact)' if f.get('exact') else '')
    keys = (f.get('measure') or '').split('+') if f.get('measure') else []
    sq = '^2' if f.get('moment') == 2 else ''
    norms = [NORM_TEX.get(k) for k in keys]
    if keys and all(norms):
        if keys[0] == 'gram':
            inner = norms[0]          # the Gram form is already quadratic in the error
        else:
            inner = ' + '.join(n + sq for n in norms)
    else:
        inner = None
    if stat == 'expectation':
        body = r'\mathbb{E}' + (('[' + inner + ']') if inner and len(keys) > 1 else (inner or ''))
        return f'${body}$' + (' (exact)' if f.get('exact') else '')
    return r'$\mathbb{P}[' + (inner or r'\cdot') + ' > t]$'


def source_short(key, overrides=None):
    """`TroppWebber2023` -> `TW`, `Woodruff2014` -> `Woodruff`; facets.toml may say otherwise."""
    if overrides and key in overrides:
        return overrides[key]
    names = re.findall(r'[A-Z][a-z]+', re.sub(r'\d{4}[a-z]?$', '', key))
    if len(names) >= 2:
        return ''.join(n[0] for n in names)
    return names[0] if names else key


def source_long(key):
    """`TroppWebber2023` -> `Tropp–Webber 2023`."""
    m = re.match(r'(.*?)(\d{4}[a-z]?)$', key)
    if not m:
        return key
    names = re.findall(r'[A-Z][a-z]+', m.group(1))
    return '–'.join(names) + ' ' + m.group(2)


def short_locator(label):
    """`Theorem 8.1 (RSVD2)` -> `8.1 (RSVD2)`; other locators stay as they are."""
    return re.sub(r'^(?:Theorem|Thm\.?)\s+(?=\d)', '', (label or '').strip())


def citation_short(key, label, overrides=None):
    s = source_short(key, overrides)
    loc = short_locator(label)
    return f'{s} {loc}'.strip()


def citation_search_text(key, label, overrides=None):
    """Every way a reader may type a citation: `TW 8.1 (RSVD2)`, `Tropp–Webber 2023 Theorem 8.1
    (RSVD2)`, `TroppWebber2023`."""
    return '; '.join(dict.fromkeys([citation_short(key, label, overrides),
                                    f'{source_long(key)} {label}'.strip(), key]))


# ------------------------------------------------------------------ the statements table

COLUMNS = [('algorithm', 'Algorithm'), ('stat', 'Statistic'), ('law', 'Law'), ('output', 'Output'),
           ('regime', 'Regime'), ('detail', 'Detail'), ('form', 'Asymptotic'), ('source', 'Source')]
ALWAYS = {'stat', 'source'}       # shown whenever a row has a value, even when constant
BIB_KEY = re.compile(r'^[A-Z][A-Za-z]+\d{4}[a-z]?$')


def drop_article(text):
    """Titles and names without a leading "The" (decision of 2026-10-19)."""
    if text and text.startswith('The ') and len(text) > 4:
        rest = text[4:]
        return rest[:1].upper() + rest[1:]
    return text


def _rank(value, order):
    return order.index(value) if value in order else len(order)


def statement_table(members, forms, primary, title, info, source_names=None):
    """The rows of a result's statements table: one per (asymptotic, explicit) pair and one per
    other member, with generated cells.

    `members` are the result's declaration indices in display order, `forms` its
    {overview, explicit} pairs, `primary` the headline explicit declaration. `info(i)` gives a
    declaration's `name`, `kind`, `facets` (or None), bold `label` (or None) and citations
    `cites` [(key, locator)]. Returns (rows, columns, default row index). A row is
    {o, e, g, c, l, x}: overview and explicit declaration, group heading, cells by column key,
    a plain one-line label and citation text for search.
    """
    covered = {k for f in forms for k in (f['overview'], f['explicit'])}
    pairs = [(f['overview'], f['explicit']) for f in forms]
    pairs += [(i, i) for i in members if i not in covered]
    order = {i: k for k, i in enumerate(members)}

    def facets_of(o, e):
        f = info(e)['facets'] or info(o)['facets']
        if f and info(e)['facets'] is None:
            f = dict(f, form='explicit')
        return f

    def sources(o, e):
        out = []
        for i in (e, o):
            for key, loc in info(i)['cites']:
                if BIB_KEY.match(key):
                    c = citation_short(key, loc, source_names)
                    if c not in out:
                        out.append(c)
            if out:
                break
        return out

    def search_text(o, e):
        seen = []
        for i in dict.fromkeys((e, o)):
            for key, loc in info(i)['cites']:
                t = citation_search_text(key, loc, source_names) if BIB_KEY.match(key) else key
                if t not in seen:
                    seen.append(t)
        return '; '.join(seen)

    # a docstring name without what the rows share: "…, Frobenius norm" of "X, Frobenius norm"
    names = {}
    for o, e in pairs:
        nm = drop_article(info(e)['label'] or info(o)['label'] or '')
        names[(o, e)] = nm
    heads = [n.split(',')[0].strip() for n in names.values() if n]

    def lean(i):
        return '`' + info(i)['name'].split('.')[-1] + '`'

    def remainder(o, e):
        nm = names[(o, e)]
        if not nm:
            return lean(e)
        head = nm.split(',')[0].strip()
        t = drop_article(title or '')
        t_head = t.split(':')[0].split(',')[0].strip()
        if t_head and nm.lower().startswith(t_head.lower()) and len(nm) > len(t_head) + 3:
            # "Early-truncated generalized Nyström with structured sketches" on that page
            rest = nm[len(t_head):].lstrip(' ,:;')
            return rest
        if nm != t and ',' in nm and (head == t.split(',')[0].strip() or heads.count(head) > 1):
            return nm.split(',', 1)[1].strip()
        return nm

    rows = []
    for o, e in pairs:
        f = facets_of(o, e)
        c = {}
        if f and f.get('statistic'):
            c['algorithm'] = f.get('algorithm')
            c['stat'] = statistic_tex(f)
            c['law'] = f.get('law')
            c['output'] = OUTPUTS.get(f.get('output')) if f.get('output') else None
            c['regime'] = f.get('regime')
            c['detail'] = '; '.join(f.get('details') or []) or None
        # an explicit bound with an asymptotic form; the toggle above the statement switches
        c['form'] = r'$O(\cdot)$' if o != e else None
        c['source'] = ', '.join(sources(o, e)[:2]) or None
        group = measure_label(f.get('measure')) if f and f.get('statistic') else None
        rows.append({'o': o, 'e': e, 'g': group, 'c': c, 'f': f if f and f.get('statistic') else None,
                     'name': remainder(o, e), 'override': (f or {}).get('label'),
                     'x': search_text(o, e)})
    # a shortened name that two rows share is given in full again
    for _ in range(2):
        count = {}
        for r in rows:
            count[r['name']] = count.get(r['name'], 0) + 1
        for r in rows:
            if count[r['name']] > 1:
                full = names[(r['o'], r['e'])]
                r['name'] = full if full and full != r['name'] else lean(r['e'])

    faceted = any(r['f'] for r in rows)
    groups = {r['g'] for r in rows}
    grouped = faceted and len(groups) > 1
    if grouped:
        for r in rows:
            r['g'] = r['g'] or 'Other statements'
    if not faceted:
        # deterministic theory: the rows are told apart by their docstring names
        for r in rows:
            r['c'] = {'name': r['override'] or r['name'], 'form': r['c']['form'],
                      'source': r['c']['source']}
        keys = ['name', 'form', 'source']
    else:
        for r in rows:
            if r['override'] or not r['f']:
                # a curated label, or a member outside the grammar: its name says what it is
                r['c']['detail'] = r['override'] or r['name']
        # rows the facets do not tell apart (whatever their sources) get their names as detail
        def key_of(r):
            return (r['g'],) + tuple(r['c'].get(k) for k, _ in COLUMNS if k not in ('form', 'source'))
        for attempt in range(2):
            seen = {}
            for r in rows:
                seen.setdefault(key_of(r), []).append(r)
            clash = [r for v in seen.values() if len(v) > 1 for r in v]
            for r in clash:
                extra = r['name'] if attempt == 0 else lean(r['e'])
                if extra != r['c'].get('detail'):
                    r['c']['detail'] = '; '.join(x for x in (r['c'].get('detail'), extra) if x)
        keys = [k for k, _ in COLUMNS]
    shown = []
    for key in keys:
        vals = [r['c'].get(key) for r in rows]
        if (key in ALWAYS or key == 'name') and any(vals) or len(set(vals)) > 1:
            shown.append(key)
    titles = dict(COLUMNS, name='Statement')
    columns = [{'k': k, 't': titles[k]} for k in shown]

    # order: the headline's group first, then by measure, statistic, law, output
    prim = next((r for r in rows if r['e'] == primary), rows[0])

    def sort_key(r):
        f = r['f'] or {}
        g_rank = (0 if r['g'] == prim['g'] else 1,
                  _rank((f.get('measure') or '').split('+')[0], MEASURE_ORDER)) if grouped else (0, 0)
        if not faceted:
            return (r is not prim, order.get(r['e'], len(order)))
        return g_rank + (r is not prim,
                         _rank(f.get('statistic'), STATISTIC_ORDER), -(f.get('moment') or 0),
                         _rank(f.get('law'), LAW_ORDER + list(INTERFACES.values())),
                         _rank(f.get('output'), OUTPUT_ORDER), bool(f.get('details')),
                         order.get(r['e'], len(order)))
    rows.sort(key=sort_key)

    def plain_label(r):
        """One line naming the statement on its own, for search hits: every facet it has."""
        f, c = r['f'], r['c']
        if not f:
            return c.get('name') or c.get('detail') or r['name']
        bits = [c.get('algorithm'), measure_label(f.get('measure')), c.get('stat'), c.get('law'),
                c.get('output') if f.get('output') != 'plain' else None, c.get('regime'), c.get('detail')]
        return ' · '.join(b for b in bits if b)

    out = []
    for r in rows:
        out.append({'o': r['o'], 'e': r['e'], 'g': r['g'] if grouped else None,
                    'c': {k: r['c'].get(k) for k in shown}, 'l': plain_label(r),
                    's': r['c'].get('source'), 'x': r['x']})
    default = next(k for k, r in enumerate(rows) if r is prim)
    return out, columns, default
