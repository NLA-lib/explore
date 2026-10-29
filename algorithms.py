"""Algorithm pages (docs/design/algorithm-pages.md): which declarations make up an algorithm, which
results attach to it, its cost targets, its status ladder, and what it uses.

Membership comes from the library: a docstring line `Algorithm: <id>` or `Algorithm: <id> (<role>)`
on a definition or program (NLAlib CONTRIBUTING §6 item 4b). Presentation comes from
`algorithms.toml`: titles, aliases, families, variants, the Rates facet value, result-id prefixes
and the curated exceptions, keyed by the id.

A result (a `Result:` id) is placed on an algorithm page by the first rule that applies:

1. curated: `results` / `not_results` of the algorithm in algorithms.toml;
2. result-id prefix: the id equals an algorithm's id or starts with one of its `result_prefixes`
   followed by `-`; the longest prefix wins;
3. Rates facet: the algorithm facet of its declarations maps to exactly one algorithm;
4. statement dependency: its statements reach tagged declarations of exactly one algorithm.

A result whose statements reach several algorithms and that rules 1-3 do not settle is listed on
each as *also involve*, as is a result placed on one algorithm whose statements also reach
another. Two things keep a result off a page whose declarations it merely mentions: its facet
names an algorithm with no page yet (`rsvd_pow_mul` is RSI, not RSVD), or its id has one of the
`[unpaged] prefixes` of algorithms that have no page yet (`minres-lanczos`, `lanczos-fa-…`); such a
result is listed as *also involve* only. No result leaves its shelves.

Pure functions of the extraction, the overlay and the target registry; build.py calls
`build_algorithms` and writes the result into data.json and site/algorithms/ladder.json.
"""

import re
from collections import defaultdict

ALGORITHM_LINE = re.compile(r'^[ \t]*Algorithm:[ \t]*([a-z0-9]+(?:-[a-z0-9]+)*)(?:[ \t]+\(([a-z ]+)\))?[ \t]*$', re.M)
ALGORITHM_ANY = re.compile(r'\bAlgorithm:')
ROLES = ('specification', 'run model')
TAG_KINDS = {'def', 'abbrev', 'structure', 'inductive', 'opaque'}
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')

# the rungs of the status ladder (§5), in order: key, title, the page section it links to
RUNGS = [('definition', 'Definition', 'definition'), ('program', 'Program', 'definition'),
         ('cost', 'Cost and output', 'cost'), ('exact', 'Exact guarantees', 'exact'),
         ('finite-precision', 'Finite precision', 'finite-precision'),
         ('sharpness', 'Sharpness', 'sharpness')]

# access models of a target, read from its name (docs/design/Computation.md F12)
MODELS = [('MatrixFreeProb', 'matrix-free, with draws'), ('MatrixFreeRounded', 'matrix-free, rounded'),
          ('MatrixFree', 'matrix-free'), ('StoredEntriesDense', 'stored entries, dense'),
          ('StoredEntriesCoo', 'stored entries, COO'), ('StoredEntries', 'stored entries')]

EXACT = 'exact arithmetic'
OVERLAY_KEYS = {'title', 'aliases', 'variants', 'variant_of', 'result_prefixes', 'results', 'not_results',
                'definitions', 'facet', 'sharpness', 'aliases_of'}


def tag_of(doc):
    """(id, role) of a docstring's `Algorithm:` line, or None; ValueError on a malformed one."""
    if not doc or not ALGORITHM_ANY.search(doc):
        return None
    found = ALGORITHM_LINE.findall(doc)
    if len(found) != len(ALGORITHM_ANY.findall(doc)) or len(found) > 1:
        raise ValueError('malformed or repeated Algorithm tag')
    aid, role = found[0]
    if role and role not in ROLES:
        raise ValueError(f'unknown Algorithm role {role!r}')
    return aid, role or None


def strip_tag(doc):
    return ALGORITHM_LINE.sub('', doc) if doc else doc


def is_program(d):
    """A constant of type `Computation.Prog` or a `Computation.Builder` (a program builder)."""
    sig = d.get('signature') or ''
    tail = sig.rsplit(' : ', 1)[-1] if ' : ' in sig else sig
    return bool(re.search(r'\bComputation\.(?:Prog|Builder)\b', tail.split('\n')[-1] if tail else ''))


def model_of(name):
    short = name.split('.')[-1]
    return next((label for key, label in MODELS if short.startswith(key)), 'other access model')


def statement_reach(decls, index):
    """`reach(i)`: the declarations a statement of `i` mentions, through the statements of what it
    mentions (`typeDeps`), and the bodies of Prop-valued definitions (a target, a predicate),
    which are part of the statement. Proofs are never followed."""
    memo = {}

    def nexts(j):
        d = decls[j]
        out = list(d.get('typeDeps') or [])
        if d['kind'] in TAG_KINDS and re.search(r':\s*Prop\s*$', d.get('signature') or ''):
            out += d.get('valueDeps') or []
        return [index[n] for n in out if n in index]

    def reach(i):
        if i in memo:
            return memo[i]
        seen, stack = set(), [i]
        while stack:
            j = stack.pop()
            for k in nexts(j):
                if k not in seen and k != i:
                    seen.add(k)
                    if k in memo:
                        seen |= memo[k]
                    else:
                        stack.append(k)
        memo[i] = seen
        return seen
    return reach


def precision_of_factory(decls, index, table, reach=None):
    """`precision(i)`: the value of the first precision-model constant (facets.toml
    `[precision]`) a statement of `i` reaches, else exact arithmetic."""
    unknown = [n for n in table if n not in index]
    if unknown:
        raise ValueError('facets.toml [precision]: unknown constant(s) ' + ', '.join(unknown))
    reach = reach or statement_reach(decls, index)
    by_index = {index[n]: v for n, v in table.items()}

    def precision(i):
        hit = [by_index[j] for j in reach(i) if j in by_index]
        return sorted(set(hit))[0] if hit else EXACT
    return precision


def parse_overlay(cfg):
    families = cfg.get('families', [])
    entries = {k: v for k, v in cfg.items() if k not in ('families', 'unpaged') and isinstance(v, dict)}
    unpaged = cfg.get('unpaged', {}).get('prefixes', [])
    return families, entries, unpaged


def build_algorithms(cfg, decls, index, results, facet_of=lambda i: None, precision=lambda i: EXACT,
                     registry=None, rate_rows=(), lower_theorems=(), collections=(), result_alias=None,
                     reach=None):
    """The algorithms: {'algorithms': {id: page}, 'families': [...], 'ladder': {...},
    'report': [...], 'decl': {declaration index: id}}.

    `results`: {rid: {'decls': [i, ...], 'title': …}} after merges; `facet_of(i)` a declaration's
    facet record; `precision(i)` its precision value; `registry` docs/targets.toml as parsed
    TOML (or None); `rate_rows` the Rates entries (for the facet check); `lower_theorems` the
    declarations of `kind = 'lower'` Rates rows; `collections` the built shelves."""
    result_alias = result_alias or {}
    families, overlay, unpaged = parse_overlay(cfg)
    problems = []
    reach = reach or statement_reach(decls, index)

    # --- members: tags, then bootstrap `definitions`
    members = defaultdict(list)          # id -> [(i, role)]
    owner = {}
    for i, d in enumerate(decls):
        try:
            t = tag_of(d.get('doc'))
        except ValueError as e:
            problems.append(f'{d["name"]}: {e}')
            continue
        if not t:
            continue
        if d['kind'] not in TAG_KINDS:
            problems.append(f'{d["name"]}: an Algorithm tag on a {d["kind"]}')
            continue
        members[t[0]].append((i, t[1]))
        owner[i] = t[0]
    for aid, e in overlay.items():
        unknown = set(e) - OVERLAY_KEYS
        if unknown:
            problems.append(f'algorithms.toml [{aid}]: unknown key(s) {", ".join(sorted(unknown))}')
        if not SLUG.fullmatch(aid):
            problems.append(f'algorithms.toml: unsafe id {aid}')
        for name in e.get('definitions', []):
            i = index.get(name)
            if i is None:
                problems.append(f'algorithms.toml [{aid}]: unknown definition {name}')
            elif i in owner:
                problems.append(f'algorithms.toml [{aid}]: definition {name} carries the tag '
                                f'`Algorithm: {owner[i]}` (the bootstrap entry is stale)')
            else:
                members[aid].append((i, None))
                owner[i] = aid
    ids = sorted(members, key=lambda a: (a not in overlay, list(overlay).index(a) if a in overlay else 0, a))
    for aid in overlay:
        if aid not in members:
            problems.append(f'algorithms.toml: [{aid}] has no tagged declaration and no definitions')

    # --- families and variants
    family_of = {}
    for f in families:
        if not isinstance(f, dict) or not f.get('id') or not f.get('title'):
            problems.append('algorithms.toml: a family needs an id and a title')
            continue
        seen = set()
        for aid in f.get('algorithms', []):
            if aid in seen or aid in family_of:
                problems.append(f'algorithms.toml family {f["id"]}: {aid} listed twice or in two families')
            seen.add(aid)
            if aid not in members:
                problems.append(f'algorithms.toml family {f["id"]}: unknown algorithm {aid}')
            family_of[aid] = f['id']
    for aid, e in overlay.items():
        for v in e.get('variants', []):
            if overlay.get(v, {}).get('variant_of') != aid:
                problems.append(f'algorithms.toml [{aid}]: variant {v} has no `variant_of = "{aid}"`')
        parent = e.get('variant_of')
        if parent and aid not in overlay.get(parent, {}).get('variants', []):
            problems.append(f'algorithms.toml [{aid}]: variant_of {parent} without the reverse variants entry')
    alias_ids = {}
    for aid, e in overlay.items():
        for old in e.get('aliases_of', []):
            if old in members or old in alias_ids:
                problems.append(f'algorithms.toml [{aid}]: aliases_of {old} is in use')
            alias_ids[old] = aid

    # --- the Rates facet
    facet_algo = {}
    row_facets = {(r.get('c') or {}).get('algorithm') for r in rate_rows}
    for aid, e in overlay.items():
        if 'facet' in e:
            facet_algo[e['facet']] = aid
            if rate_rows and e['facet'] not in row_facets:
                problems.append(f'algorithms.toml [{aid}]: facet {e["facet"]!r} is on no Rates row')

    # --- attachment
    def canon(rid):
        return result_alias.get(rid, rid)
    curated, curated_not = defaultdict(set), defaultdict(set)
    for aid, e in overlay.items():
        for key, into in (('results', curated), ('not_results', curated_not)):
            for rid in e.get(key, []):
                if canon(rid) not in results:
                    problems.append(f'algorithms.toml [{aid}]: unknown result {rid} in {key}')
                into[canon(rid)].add(aid)
    prefixes = [(p, aid) for aid in ids for p in overlay.get(aid, {}).get('result_prefixes', [aid])]
    # the prefixes of algorithms with no page yet compete too: `lanczos-fa-cg` is Lanczos-FA's
    every = sorted(prefixes + [(p, None) for p in unpaged], key=lambda x: -len(x[0]))

    def by_prefix(rid, ps):
        return next((a for p, a in ps if rid == p or rid.startswith(p + '-')), None)

    def prefix_hit(rid):
        return next(((p, a) for p, a in every if rid == p or rid.startswith(p + '-')), None)

    placed, also, how = {}, defaultdict(set), {}
    reached = {}
    for rid, r in results.items():
        algs = set()
        for i in r['decls']:
            algs |= {owner[j] for j in reach(i) if j in owner}
            if i in owner:
                algs.add(owner[i])
        algs -= curated_not.get(rid, set())
        reached[rid] = algs
        fac = {(facet_of(i) or {}).get('algorithm') for i in r['decls']} - {None}
        choice, rule = None, None
        if rid in curated:
            choice = sorted(curated[rid])[0]
            rule = 'curated'
            if len(curated[rid]) > 1:
                problems.append(f'algorithms.toml: result {rid} curated on {", ".join(sorted(curated[rid]))}')
        elif (hit := prefix_hit(rid)) and hit[1] is None:
            rule = 'unpaged prefix'
        elif hit and hit[1] not in curated_not.get(rid, set()):
            choice, rule = hit[1], 'prefix'
        else:
            if len(fac) == 1:
                f = next(iter(fac))
                if f in facet_algo and facet_algo[f] not in curated_not.get(rid, set()):
                    choice, rule = facet_algo[f], 'facet'
                elif f not in facet_algo:
                    rule = 'facet without a page'
            if choice is None and rule is None and len(algs) == 1:
                choice, rule = next(iter(algs)), 'dependency'
        if choice:
            placed[rid] = choice
            how[rid] = rule
        for a in algs - ({choice} if choice else set()):
            also[a].add(rid)
        if not choice and algs:
            how[rid] = rule or 'several algorithms'

    # a note when curated entries repeat what the rules do anyway
    for aid in ids:
        mine = [rid for rid in overlay.get(aid, {}).get('results', []) if canon(rid) in results]
        redundant = [rid for rid in mine if by_prefix(canon(rid), prefixes) == aid or reached.get(canon(rid)) == {aid}]
        if len(redundant) > 3:
            problems.append(f'note: algorithms.toml [{aid}]: {len(redundant)} curated results the rules place anyway')

    # --- targets about the algorithm's programs, and their proofs
    programs = {i for aid in ids for i, role in members[aid] if is_program(decls[i])}
    prog_owner = {decls[i]['name']: owner[i] for i in programs}

    def program_of(name):
        for p, aid in prog_owner.items():
            if name == p or name.startswith(p + '.'):
                return aid
        return None
    proofs = {}
    for i, d in enumerate(decls):
        if d['kind'] == 'theorem':
            m = re.match(r'^\S+ : (\S+)$', (d.get('signature') or '').strip())
            if m:
                proofs.setdefault(m.group(1), i)
    cost = defaultdict(list)
    cost_results = set()
    for t in (registry or {}).get('target', []):
        ti = index.get(t['name'])
        names = list(t.get('trees', []))
        if ti is not None:
            names += decls[ti].get('valueDeps') or []
        algs = {program_of(n) for n in names} - {None}
        if not algs and ti is not None:
            # a target whose tree is built inside its statement: the program its trees come from
            algs = {owner[j] for j in reach(ti) if j in owner and j in programs}
        short = t['name'].split('.')[-1]
        proof = proofs.get(short)
        if proof is None:
            proof = proofs.get(t['name'])
        # the count definition the target states its cost with (`hutchppCount`), not the
        # model's own counts (`Computation.OpCount`, `Computation.substCount`)
        count = next((index[n] for n in (decls[ti].get('valueDeps') or []) if n in index and
                      re.fullmatch(r'[a-z]\w*Count', n.split('.')[-1]) and
                      not n.startswith('NLAlib.Computation.')), None) if ti is not None else None
        for aid in sorted(algs):
            rid = decls[proof]['_results'][0] if proof is not None and decls[proof]['_results'] else None
            cost[aid].append({'target': ti, 'name': t['name'], 'model': model_of(t['name']),
                              'trees': t.get('trees', []), 'precomputed': t.get('precomputed', []),
                              'reviewed': t.get('reviewed'), 'proof': proof, 'result': canon(rid) if rid else None,
                              'count': count})
            if rid:
                cost_results.add(canon(rid))

    # --- sections of the placed results
    lower = set(lower_theorems)

    def is_sharp(rid, aid):
        r = results[rid]
        return (rid.endswith('-sharp') or rid.endswith('-lower-bound') or
                rid in overlay.get(aid, {}).get('sharpness', []) or
                any(i in lower or decls[i]['module'].startswith('NLAlib.LowerBounds') for i in r['decls']))

    def result_precision(rid):
        vals = {precision(i) for i in results[rid]['decls']}
        return sorted(vals - {EXACT})[0] if vals - {EXACT} else EXACT

    pages = {}
    ladder = {}
    decl_alg = {i: owner[i] for i in owner}
    for aid in ids:
        e = overlay.get(aid, {})
        mem = sorted(members[aid], key=lambda x: (x[1] != 'specification', decls[x[0]]['module'], decls[x[0]].get('line') or 0))
        mine = sorted((rid for rid, a in placed.items() if a == aid), key=lambda rid: (
            decls[results[rid]['decls'][0]]['module'], decls[results[rid]['decls'][0]].get('line') or 0))
        roles = {i: role for i, role in mem}
        sec = {'relating': [], 'cost': [], 'exact': [], 'finite-precision': [], 'sharpness': []}
        fp_model = {}
        for rid in mine:
            if rid in cost_results:
                sec['cost'].append(rid)
            elif is_sharp(rid, aid):
                sec['sharpness'].append(rid)
            elif (p := result_precision(rid)) != EXACT:
                sec['finite-precision'].append(rid)
                fp_model[rid] = p
            elif any(roles.get(j) == 'specification' for i in results[rid]['decls'] for j in reach(i)) and \
                    any(j in roles and roles[j] != 'specification' for i in results[rid]['decls'] for j in reach(i)):
                sec['relating'].append(rid)
            else:
                sec['exact'].append(rid)
        progs = [i for i, _ in mem if i in programs]
        defs = [i for i, _ in mem if i not in programs]
        rows = cost.get(aid, [])
        proved = [c for c in rows if c['proof'] is not None]
        rung = {'definition': [decls[i]['name'] for i in defs],
                'program': [decls[i]['name'] for i in progs],
                'cost': [c['name'] for c in proved],
                'exact': sec['exact'] + sec['relating'],
                'finite-precision': sec['finite-precision'],
                'sharpness': sec['sharpness']}
        ladder[aid] = rung
        # uses: what its definitions and programs are built from, through untagged definitions
        uses = set()
        for i, _ in mem:
            stack, seen = [i], {i}
            while stack:
                j = stack.pop()
                for n in (decls[j].get('valueDeps') or []) + (decls[j].get('typeDeps') or []):
                    k = index.get(n)
                    if k is None or k in seen:
                        continue
                    seen.add(k)
                    if k in owner:
                        if owner[k] != aid:
                            uses.add(owner[k])
                    elif decls[k]['kind'] in TAG_KINDS and not decls[k].get('_results'):
                        stack.append(k)
        shelves = []
        for c in collections:
            for g in c.get('groups', []):
                hit = any((x['type'] == 'd' and owner.get(x['i']) == aid) or
                          (x['type'] == 'r' and placed.get(x['rid']) == aid) for x in g.get('entries', []))
                if hit:
                    shelves.append([c['id'], g['id'], g['title'], c['title']])
        # the description: the specification, else the definition that names the whole thing
        # (`The **Lanczos recurrence**`, not one step or coefficient of it), else the first
        # definition that is not a program or a structure
        plain = [i for i, _ in mem if decls[i]['kind'] != 'structure' and i not in programs]
        first = next((i for i, role in mem if role == 'specification'), None)
        if first is None:
            first = next((i for i in plain if re.match(r'\s*The \*\*', decls[i].get('doc') or '')),
                         plain[0] if plain else mem[0][0])
        pages[aid] = {
            'id': aid, 'title': e.get('title'), 'aliases': e.get('aliases', []), 'family': family_of.get(aid),
            'variant_of': e.get('variant_of'), 'variants': e.get('variants', []), 'facet': e.get('facet'),
            'first': first,
            'members': [{'i': i, 'role': 'program' if i in programs else role or 'definition'} for i, role in mem],
            'cost': rows, 'sections': sec, 'fp': fp_model,
            'also': sorted(also.get(aid, set()) - set(mine)),
            'uses': sorted(uses), 'shelves': shelves,
            'ladder': {k: len(v) for k, v in rung.items()},
        }
    for aid, p in pages.items():
        p['used_by'] = sorted(a for a, q in pages.items() if aid in q['uses'])
    out_families = [{'id': f['id'], 'title': f['title'], 'description': f.get('description', ''),
                     'algorithms': [a for a in f.get('algorithms', []) if a in pages]}
                    for f in families if isinstance(f, dict) and f.get('id')]
    rest = [a for a in ids if a not in family_of]
    if rest:
        out_families.append({'id': 'other', 'title': 'Other algorithms', 'description': '', 'algorithms': rest})
    report = {'placed': {rid: [a, how[rid]] for rid, a in sorted(placed.items())},
              'also': {rid: sorted(a for a in reached[rid] if a != placed.get(rid))
                       for rid in sorted(reached) if reached[rid] - {placed.get(rid)}},
              'unplaced': {rid: how.get(rid) for rid in sorted(reached) if reached[rid] and rid not in placed}}
    return {'algorithms': pages, 'families': out_families, 'ladder': ladder, 'report': report,
            'decl': decl_alg, 'aliases': alias_ids, 'placed': placed, 'problems': problems}


def ladder_table(alg, titles=None):
    """`build.py --ladder`: one line per algorithm, the number present at each rung."""
    titles = titles or {}
    head = ['algorithm'] + [t for _, t, _ in RUNGS]
    rows = [[titles.get(a) or a] + [str(len(r[k])) if r[k] else '-' for k, _, _ in RUNGS]
            for a, r in alg['ladder'].items()]
    w = [max(len(x[c]) for x in [head] + rows) for c in range(len(head))]
    return '\n'.join('  '.join(x[c].ljust(w[c]) for c in range(len(head))) for x in [head] + rows)
