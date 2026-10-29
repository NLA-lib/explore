"""Algorithm pages (algorithms.py): attachment precedence, the overlay checks, the ladder."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import algorithms as A  # noqa: E402
from test_build import b, decl  # noqa: E402


def lib(*ds):
    """Declarations as build.py hands them over: `_results` from their `Result:` lines."""
    out = []
    for k, d in enumerate(ds):
        d = {'typeDeps': [], 'valueDeps': [], 'line': k + 1, 'signature': d['name'] + ' : T', **d}
        d['_results'] = [x.strip() for line in A.re.findall(r'^\s*Result:\s*(.+)$', d['doc'] or '', A.re.M)
                         for x in line.split(',')]
        out.append(d)
    index = {d['name']: i for i, d in enumerate(out)}
    results = {}
    for i, d in enumerate(out):
        for rid in d['_results']:
            results.setdefault(rid, {'decls': []})['decls'].append(i)
    return out, index, results


def run(ds, cfg=None, **kw):
    decls, index, results = lib(*ds)
    return A.build_algorithms(cfg or {}, decls, index, results, **kw), decls


CG = [decl('N.cgState', 'The recurrence.\nAlgorithm: cg', kind='def'),
      decl('N.cgIterate', 'What it computes.\nAlgorithm: cg (specification)', kind='def'),
      decl('N.lanczosState', 'Lanczos.\nAlgorithm: lanczos', kind='def'),
      decl('N.rsvd', 'RSVD.\nAlgorithm: randomized-svd', kind='def')]


class TagTests(unittest.TestCase):
    def test_tag_of(self):
        self.assertEqual(A.tag_of('Text.\nAlgorithm: cg'), ('cg', None))
        self.assertEqual(A.tag_of('Text.\nAlgorithm: cg (specification)'), ('cg', 'specification'))
        self.assertIsNone(A.tag_of('No tag. An algorithm.'))
        for bad in ('Text. Algorithm: cg', 'Algorithm: CG', 'Algorithm: cg (program)', 'Algorithm: a\nAlgorithm: b'):
            with self.subTest(doc=bad), self.assertRaises(ValueError):
                A.tag_of(bad)

    def test_tag_on_a_theorem_fails(self):
        alg, _ = run([decl('N.t', 'A theorem.\nAlgorithm: cg')])
        self.assertTrue(any('on a theorem' in p for p in alg['problems']))

    def test_tag_hidden_from_prose(self):
        site = BuildRender().render([decl('N.cgState', 'The **CG recurrence**. Steps.\nAlgorithm: cg', kind='def')])
        self.assertNotIn('Algorithm', site['decls'][0]['stmt'])
        self.assertEqual(site['algorithms']['decl'], {'0': 'cg'})


class AttachmentTests(unittest.TestCase):
    def test_prefix_beats_dependency_and_also_involve(self):
        ds = CG + [decl('N.t1', 'Bound.\nResult: cg-bound', typeDeps=['N.cgIterate']),
                   decl('N.t2', 'Relation.\nResult: cg-lanczos', typeDeps=['N.cgIterate', 'N.lanczosState']),
                   decl('N.t3', 'Paige.\nResult: paige-bound', typeDeps=['N.lanczosState']),
                   decl('N.t4', 'Both.\nResult: shared-lemma', typeDeps=['N.cgIterate', 'N.lanczosState'])]
        alg, _ = run(ds)
        self.assertEqual(alg['placed'], {'cg-bound': 'cg', 'cg-lanczos': 'cg', 'paige-bound': 'lanczos'})
        self.assertEqual(alg['report']['placed']['paige-bound'], ['lanczos', 'dependency'])
        # placed on CG, also listed on Lanczos; settled by no rule, listed on both
        self.assertEqual(alg['algorithms']['lanczos']['also'], ['cg-lanczos', 'shared-lemma'])
        self.assertEqual(alg['algorithms']['cg']['also'], ['shared-lemma'])

    def test_longest_prefix_and_curated(self):
        ds = CG + [decl('N.p', 'P.\nAlgorithm: pcg', kind='def'),
                   decl('N.t1', 'B.\nResult: pcg-bound', typeDeps=['N.p', 'N.cgIterate']),
                   decl('N.t2', 'B.\nResult: odd-name', typeDeps=['N.cgIterate']),
                   decl('N.t3', 'B.\nResult: cg-misnamed', typeDeps=['N.lanczosState'])]
        cfg = {'cg': {'results': ['odd-name'], 'not_results': ['cg-misnamed']}}
        alg, _ = run(ds, cfg)
        self.assertEqual(alg['placed']['pcg-bound'], 'pcg')
        self.assertEqual(alg['report']['placed']['odd-name'], ['cg', 'curated'])
        self.assertEqual(alg['placed']['cg-misnamed'], 'lanczos')

    def test_facet_rule_and_facet_without_page(self):
        ds = CG + [decl('N.rsvd_pow', 'RSI.\nResult: subspace-iteration-error', typeDeps=['N.rsvd']),
                   decl('N.bound', 'RSVD.\nResult: some-bound', typeDeps=['N.rsvd', 'N.lanczosState'])]
        fac = {'N.rsvd_pow': {'algorithm': 'RSI'}, 'N.bound': {'algorithm': 'RSVD'}}
        decls, index, results = lib(*ds)
        alg = A.build_algorithms({'randomized-svd': {'facet': 'RSVD'}}, decls, index, results,
                                 facet_of=lambda i: fac.get(decls[i]['name']))
        # the facet settles a result that reaches two algorithms
        self.assertEqual(alg['report']['placed']['some-bound'], ['randomized-svd', 'facet'])
        # RSI has no page: the statement mentions rsvd, but it is not RSVD's result
        self.assertNotIn('subspace-iteration-error', alg['placed'])
        self.assertIn('subspace-iteration-error', alg['algorithms']['randomized-svd']['also'])

    def test_unpaged_prefix(self):
        ds = CG + [decl('N.m', 'M.\nResult: minres-lanczos', typeDeps=['N.lanczosState']),
                   decl('N.f', 'F.\nResult: lanczos-fa-bound', typeDeps=['N.lanczosState'])]
        alg, _ = run(ds, {'unpaged': {'prefixes': ['minres', 'lanczos-fa']}})
        self.assertEqual(alg['placed'], {})
        self.assertEqual(alg['algorithms']['lanczos']['also'], ['lanczos-fa-bound', 'minres-lanczos'])

    def test_statement_not_proof(self):
        ds = CG + [decl('N.t', 'T.\nResult: other-thing', valueDeps=['N.cgIterate'])]
        alg, _ = run(ds)
        self.assertEqual(alg['placed'], {})

    def test_through_prop_definitions(self):
        ds = CG + [decl('N.Target', 'A target.', kind='def', signature='N.Target : Prop', valueDeps=['N.cgState']),
                   decl('N.proof', 'Proof.\nResult: hscg-program', signature='N.proof : Target', typeDeps=['N.Target'])]
        alg, _ = run(ds)
        self.assertEqual(alg['placed'], {'hscg-program': 'cg'})


class OverlayTests(unittest.TestCase):
    def problems(self, cfg, ds=CG, **kw):
        alg, _ = run(ds, cfg, **kw)
        return ' | '.join(alg['problems'])

    def test_checks(self):
        self.assertIn('no tagged declaration', self.problems({'gmres': {'title': 'GMRES'}}))
        fam = [{'id': 'a', 'title': 'A', 'algorithms': ['cg', 'cg']}, {'id': 'b', 'title': 'B', 'algorithms': ['cg']}]
        self.assertIn('listed twice or in two families', self.problems({'families': fam}))
        self.assertIn('without the reverse', self.problems({'lanczos': {'variant_of': 'cg'}}))
        self.assertIn('has no `variant_of', self.problems({'cg': {'variants': ['lanczos']}}))
        self.assertIn('unknown result', self.problems({'cg': {'results': ['gone']}}))
        self.assertIn('unknown definition', self.problems({'cg': {'definitions': ['N.gone']}}))
        self.assertIn('bootstrap entry is stale', self.problems({'cg': {'definitions': ['N.cgState']}}))
        self.assertIn('on no Rates row', self.problems({'cg': {'facet': 'CG'}}, rate_rows=[{'c': {'algorithm': 'RSVD'}}]))
        self.assertIn('unknown key', self.problems({'cg': {'titel': 'x'}}))
        self.assertEqual(self.problems({'cg': {'title': 'CG', 'variants': ['lanczos']}, 'lanczos': {'variant_of': 'cg'}}), '')

    def test_bootstrap_definitions(self):
        ds = CG + [decl('N.gmresIterate', 'GMRES.', kind='def'),
                   decl('N.t', 'B.\nResult: gmres-bound', typeDeps=['N.gmresIterate'])]
        alg, _ = run(ds, {'gmres': {'definitions': ['N.gmresIterate']}})
        self.assertEqual(alg['placed'], {'gmres-bound': 'gmres'})

    def test_families_and_aliases(self):
        alg, _ = run(CG, {'families': [{'id': 'k', 'title': 'Krylov', 'algorithms': ['cg', 'lanczos']}],
                          'cg': {'aliases_of': ['hscg']}})
        self.assertEqual([f['algorithms'] for f in alg['families']], [['cg', 'lanczos'], ['randomized-svd']])
        self.assertEqual(alg['families'][1]['title'], 'Other algorithms')
        self.assertEqual(alg['aliases'], {'hscg': 'cg'})


PROG_SIG = 'N.gsProg {P : Type} (p : P) : Computation.Builder P ι VB VI Unit'


class LadderTests(unittest.TestCase):
    def fixture(self):
        return [decl('N.gsQ', 'Q factor.\nAlgorithm: gram-schmidt', kind='def'),
                decl('N.gsProg', 'Program.\nAlgorithm: gram-schmidt', kind='def', signature=PROG_SIG),
                decl('N.gsProg.compiled', 'Tree.', kind='def', signature='N.gsProg.compiled : Computation.Prog P ι 1 1',
                     valueDeps=['N.gsProg']),
                decl('N.gsCount', 'The count.', kind='def'),
                decl('N.MatrixFreeGs', 'Target.', kind='def', signature='N.MatrixFreeGs : Prop',
                     valueDeps=['N.gsProg.compiled', 'N.gsCount']),
                decl('N.matrixFreeGs', 'Proof.\nResult: gram-schmidt-program', signature='N.matrixFreeGs : MatrixFreeGs',
                     typeDeps=['N.MatrixFreeGs']),
                decl('N.exact', 'Orthonormal.\nResult: gram-schmidt-orthonormal', typeDeps=['N.gsQ']),
                decl('N.Run', 'A run.\nAlgorithm: lanczos (run model)', kind='structure'),
                decl('N.fp', 'Paige.\nResult: lanczos-paige', typeDeps=['N.Run']),
                decl('N.sharp', 'Sharp.\nResult: lanczos-sharp', typeDeps=['N.Run']),
                {**decl('N.lb', 'Lower.\nResult: lanczos-worst', typeDeps=['N.Run']), 'module': 'NLAlib.LowerBounds.K'}]

    def test_rungs(self):
        ds = self.fixture()
        decls, index, results = lib(*ds)
        registry = {'target': [{'name': 'N.MatrixFreeGs', 'trees': ['N.gsProg.compiled'], 'precomputed': [],
                                'reviewed': '2026-10-23'},
                               {'name': 'N.Unproved', 'trees': ['N.gsProg.compiled']}]}
        prec = A.precision_of_factory(decls, index, {'N.Run': 'local-error model'})
        alg = A.build_algorithms({}, decls, index, results, registry=registry, precision=prec)
        gs, lz = alg['ladder']['gram-schmidt'], alg['ladder']['lanczos']
        self.assertEqual(gs, {'definition': ['N.gsQ'], 'program': ['N.gsProg'], 'cost': ['N.MatrixFreeGs'],
                              'exact': ['gram-schmidt-orthonormal'], 'finite-precision': [], 'sharpness': []})
        self.assertEqual((lz['definition'], lz['program'], lz['cost'], lz['exact']), (['N.Run'], [], [], []))
        self.assertEqual(lz['finite-precision'], ['lanczos-paige'])
        self.assertEqual(sorted(lz['sharpness']), ['lanczos-sharp', 'lanczos-worst'])
        page = alg['algorithms']['gram-schmidt']
        cost = {c['name']: c for c in page['cost']}
        self.assertEqual(cost['N.MatrixFreeGs']['model'], 'matrix-free')
        self.assertEqual(cost['N.MatrixFreeGs']['count'], index['N.gsCount'])
        self.assertEqual(cost['N.MatrixFreeGs']['result'], 'gram-schmidt-program')
        self.assertIsNone(cost['N.Unproved']['proof'])
        self.assertEqual(page['sections']['cost'], ['gram-schmidt-program'])
        self.assertEqual(alg['algorithms']['lanczos']['fp'], {'lanczos-paige': 'local-error model'})
        self.assertEqual([m['role'] for m in page['members']], ['definition', 'program'])
        self.assertIn('lanczos', A.ladder_table(alg))

    def test_uses(self):
        ds = CG + [decl('N.hutchpp', 'H.\nAlgorithm: hutchpp', kind='def', valueDeps=['N.helper']),
                   decl('N.helper', 'A helper.', kind='def', valueDeps=['N.rsvd'])]
        alg, _ = run(ds)
        self.assertEqual(alg['algorithms']['hutchpp']['uses'], ['randomized-svd'])
        self.assertEqual(alg['algorithms']['randomized-svd']['used_by'], ['hutchpp'])

    def test_ladder_json_written(self):
        ds = [decl('N.cgState', 'The recurrence.\nAlgorithm: cg', kind='def'),
              decl('N.t', 'Bound.\nResult: cg-bound', typeDeps=['N.cgState'])]
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(b, 'load_toml', side_effect=lambda name: {}):
                b.build(dict(decls=ds, modules=[dict(name='NLAlib.Test', path='NLAlib/Test.lean')]), {}, Path(tmp) / 'site')
            ladder = json.loads((Path(tmp) / 'site/algorithms/ladder.json').read_text())
            self.assertEqual(ladder['algorithms']['cg']['rungs']['exact'], ['cg-bound'])
            self.assertTrue((Path(tmp) / 'site/algorithms/index.html').exists())
            report = json.loads((Path(tmp) / 'site/algorithms/attachment.json').read_text())
            self.assertEqual(report['placed']['cg-bound'], ['cg', 'prefix'])


class PrecisionTests(unittest.TestCase):
    def test_precision(self):
        ds = [decl('N.Sem', 'A semantics.', kind='def'), decl('N.Pred', 'P.', kind='def', signature='N.Pred : Prop', valueDeps=['N.Sem']),
              decl('N.a', 'A.', typeDeps=['N.Pred']), decl('N.b', 'B.'), decl('N.c', 'C.', valueDeps=['N.Sem'])]
        decls, index, _ = lib(*ds)
        prec = A.precision_of_factory(decls, index, {'N.Sem': 'standard model'})
        self.assertEqual([prec(i) for i in (2, 3, 4)], ['standard model', A.EXACT, A.EXACT])
        with self.assertRaises(ValueError):
            A.precision_of_factory(decls, index, {'N.Gone': 'x'})


class BuildRender:
    def render(self, ds, config=None):
        config = config or {}
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(b, 'load_toml', side_effect=lambda name: config.get(name, {})):
                b.build(dict(decls=ds, modules=[dict(name='NLAlib.Test', path='NLAlib/Test.lean')]), {}, Path(tmp) / 'site')
            return json.loads((Path(tmp) / 'site/data.json').read_text())


if __name__ == '__main__':
    unittest.main()
