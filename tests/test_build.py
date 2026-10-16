import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('explore_build', Path(__file__).resolve().parents[1] / 'build.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def decl(name, doc='', kind='theorem', **kw):
    return dict(name=name, module='NLAlib.Test', kind=kind, doc=doc, **kw)


class BuildTests(unittest.TestCase):
    def render(self, ds):
        with tempfile.TemporaryDirectory() as tmp:
            b.build(dict(decls=ds, modules=[dict(name='NLAlib.Test', path='NLAlib/Test.lean')]), {}, Path(tmp) / 'site')
            return json.loads((Path(tmp) / 'site/data.json').read_text())

    def test_inherits_ids_and_removes_metadata(self):
        site = self.render([decl('N.exp', 'Explicit.\nResult: bound'),
                            decl('N.asym', 'O(k) suffices.\nAsymptotic:\nN.exp')])
        r = site['results']['bound']
        self.assertEqual((r['overview'], r['explicit']), (1, 0))
        self.assertEqual(r['forms'], [dict(overview=1, explicit=0)])
        self.assertEqual(site['decls'][1]['r'], ['bound'])
        self.assertNotIn('Asymptotic', site['decls'][1]['stmt'])
        self.assertNotIn('N.exp', site['decls'][1]['stmt'])

    def test_all_pairs_and_own_ids(self):
        site = self.render([decl('N.e1', '**Bound.** First.\nResult: bound'),
                            decl('N.e2', 'Second.\nResult: bound'),
                            decl('N.a2', 'Second O.\nAsymptotic: N.e2'),
                            decl('N.a1', 'First O.\nAsymptotic: N.e1\nResult: own')])
        r = site['results']['bound']
        self.assertEqual(r['forms'], [dict(overview=3, explicit=0), dict(overview=2, explicit=1)])
        self.assertEqual(r['overview'], 3)
        self.assertIn('own', site['decls'][3]['r'])
        self.assertEqual(site['results']['own']['explicit'], 0)

    def test_unresolved_and_cycle(self):
        for ds in ([decl('N.a', 'Asymptotic: N.missing')],
                   [decl('N.a', 'Asymptotic: N.b'), decl('N.b', 'Asymptotic: N.a')]):
            with self.assertRaises(ValueError):
                self.render(ds)

    def test_support_retained_graph_collapses(self):
        site = self.render([decl('N.concept', kind='def'),
                            decl('N.bound', kind='def', explorerRole='support', valueDeps=['N.concept']),
                            decl('N.result', 'Result: result', valueDeps=['N.bound'])])
        self.assertEqual([d['role'] for d in site['decls']], ['concept', 'support', 'lemma'])
        self.assertNotIn('d:N.bound', site['nodes'])
        self.assertEqual(site['nodes']['r:result']['u'], ['d:N.concept'])
        self.assertEqual(len(site['decls']), 3)

    def test_original_title_primary_and_aliases(self):
        site = self.render([decl('N.asym', '**Bound asymptotic.** O(k).\nAsymptotic: N.exp'),
                            decl('N.other', '**Other.** Other.\nResult: bound, alias'),
                            decl('N.exp', '**Bound explicit.** Explicit.\nResult: bound, alias')])
        # The established title and named primary come from the explicit declarations.
        self.assertEqual(site['results']['bound']['title'], 'Bound explicit')
        self.assertEqual(site['results']['bound']['explicit'], 2)
        self.assertEqual(site['resultAlias'], {'alias': 'bound'})
        self.assertEqual(site['decls'][0]['r'], ['bound'])
        site = self.render([decl('N.asym', '**Bound asymptotic.** O(k).\nAsymptotic: N.exp'),
                            decl('N.exp', '**Bound explicit.** Explicit.\nResult: bound')])
        self.assertEqual(site['results']['bound']['title'], 'Bound explicit')
        self.assertEqual(site['results']['bound']['overview'], 0)

    def test_malformed_metadata_fails(self):
        for tag in ('Asymptotic:', 'Asymptotic: N.exp extra',
                    'Prose. Asymptotic: N.exp', 'Result:', 'Prose Result: bound',
                    'Result: bound,', 'Result: invalid id'):
            with self.subTest(tag=tag), self.assertRaisesRegex(ValueError, 'malformed'):
                self.render([decl('N.exp'), decl('N.asym', tag)])

    def test_asymptotic_pair_requires_result_membership(self):
        with self.assertRaisesRegex(ValueError, 'Asymptotic pair has no Result id: N.asym -> N.exp'):
            self.render([decl('N.exp'), decl('N.asym', 'Asymptotic: N.exp')])
        # Either explicit membership or the asymptotic declaration's own id exposes the pair.
        for explicit_doc, asym_doc in (('Result: bound', 'Asymptotic: N.exp'),
                                       ('', 'Asymptotic: N.exp\nResult: bound')):
            site = self.render([decl('N.exp', explicit_doc), decl('N.asym', asym_doc)])
            self.assertEqual(site['results']['bound']['forms'], [dict(overview=1, explicit=0)])

    def test_source_hashes_and_legacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'NLAlib/Test.lean'
            p.parent.mkdir()
            p.write_text('def x := 1\n')
            data = dict(modules=[dict(path='NLAlib/Test.lean')], sourceHashes={
                'NLAlib/Test.lean': hashlib.sha256(p.read_bytes()).hexdigest()})
            self.assertTrue(b.validate_sources(data, tmp))
            p.write_text('def x := 2\n')
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                b.validate_sources(data, tmp)
            data['sourceHashes'] = {}
            with self.assertRaisesRegex(ValueError, 'cover'):
                b.validate_sources(data, tmp)
            data = dict(modules=[dict(path='../bad.lean')], sourceHashes={'../bad.lean': 'x'})
            with self.assertRaisesRegex(ValueError, 'unsafe'):
                b.validate_sources(data, tmp)
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertFalse(b.validate_sources({}, tmp))
            self.assertIn('skipping definition body enrichment', err.getvalue())


if __name__ == '__main__':
    unittest.main()
