import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_build import b, decl


class RatesTests(unittest.TestCase):
    def setUp(self):
        self.ds = [decl('N.exp', 'Explicit.\nResult: bound'),
                   decl('N.asym', 'O(k). <!-- hidden -->\nAsymptotic: N.exp', signature='sig')]
        doc = b.HTML_COMMENT.sub('', self.ds[1]['doc'])
        self.row = dict(id='rate', theorem='N.asym', family='family', algorithm='algorithm',
                        variant='variant', sketch='Gaussian', norm='Frobenius', mode='expectation',
                        guarantee='$1+\\varepsilon$', resources=[dict(label='columns', bound='$k/\\varepsilon$')],
                        statement_hash=hashlib.sha256(('sig\n' + doc).encode()).hexdigest())
        self.cfg = dict(families=[dict(id='family', title='Family', description='Description')], rates=[self.row])

    def render(self, config, ds=None):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'site'
            with patch.object(b, 'load_toml', side_effect=lambda name: config.get(name, {})):
                b.build(dict(decls=copy.deepcopy(ds or self.ds), modules=[dict(name='NLAlib.Test', path='NLAlib/Test.lean')]), {}, out)
            return json.loads((out / 'data.json').read_text()), (out / 'rates/index.html').read_text()

    def test_rates_resolution_hash_and_route(self):
        site, html = self.render({'rates.toml': self.cfg})
        row = site['rates']['entries'][0]
        self.assertEqual((row['overview'], row['explicit'], row['result']), (1, 0, 'bound'))
        self.assertNotIn('doc', row)
        self.assertIn('data-page="rates" data-base="../"', html)
        self.assertIn('<title>Rates', html)
        self.assertIn('../app.js', html)
        self.assertEqual(site['collections'], [])

    def test_rates_reject_invalid_metadata(self):
        for field, value in [('statement_hash', 'stale'), ('theorem', 'N.exp'),
                             ('theorem', 'missing'), ('family', 'missing'), ('algorithm', ''),
                             ('resources', []), ('resources', [dict(label='', bound='x')])]:
            cfg = copy.deepcopy(self.cfg)
            cfg['rates'][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.render({'rates.toml': cfg})
        for key in ('families', 'rates'):
            cfg = copy.deepcopy(self.cfg)
            cfg[key].append(copy.deepcopy(cfg[key][0]))
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                self.render({'rates.toml': cfg})
        for i in (0, 1):
            ds = copy.deepcopy(self.ds)
            ds[i]['sorry'] = True
            with self.assertRaisesRegex(ValueError, 'unproved'):
                self.render({'rates.toml': self.cfg}, ds)

    def test_preferred_primary_selects_matching_pair(self):
        ds = [decl('N.e1', 'Result: bound'), decl('N.e2', 'Result: bound'),
              decl('N.a1', 'Asymptotic: N.e1'), decl('N.a2', 'Asymptotic: N.e2')]
        site, _ = self.render({'results.toml': {'bound': {'primary': 'N.e2'}}}, ds)
        self.assertEqual((site['results']['bound']['overview'], site['results']['bound']['explicit']), (3, 1))
        for primary in ('missing', 'N.a1'):
            with self.assertRaisesRegex(ValueError, 'primary'):
                self.render({'results.toml': {'bound': {'primary': primary}}}, ds)

    def test_collections_validate_and_preserve_future_entries(self):
        ds = [dict(decl('N.e1', 'Result: bound'), module='NLAlib.LowRank.Test'),
              dict(decl('N.e2', 'Result: future'), module='NLAlib.LowRank.Test'),
              dict(decl('N.concept', kind='def'), module='NLAlib.LowRank.Test'),
              dict(decl('N.support', kind='def', explorerRole='support'), module='NLAlib.LowRank.Test')]
        cfg = {'collections': [dict(id='lowrank', title='Algorithms', description='Description', topic='LowRank',
                groups=[dict(id='a', title='A', results=['bound'], definitions=[]),
                        dict(id='b', title='B', results=['bound'], definitions=[])])]}
        # Direct helper keeps the fixture independent of unrelated topic TOML.
        index = {d['name']: i for i, d in enumerate(ds)}
        rs = {'bound': {'decls': [0]}, 'future': {'decls': [1]}}
        mods = {'NLAlib.LowRank.Test': {'topic': 'LowRank'}}
        out = b.collections_page(cfg, rs, ds, index, mods, {})
        self.assertEqual(out[0]['groups'][-1]['entries'], [{'type': 'r', 'rid': 'future'}, {'type': 'd', 'i': 2}])
        for key, values in [('results', ['missing']), ('definitions', ['N.e1'])]:
            bad = copy.deepcopy(cfg)
            bad['collections'][0]['groups'][0][key] = values
            with self.assertRaises(ValueError):
                b.collections_page(bad, rs, ds, index, mods, {})
        bad = copy.deepcopy(cfg)
        bad['collections'][0]['groups'][1]['id'] = 'a'
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            b.collections_page(bad, rs, ds, index, mods, {})

    def test_primary_unknown_group_or_nonmember_fails(self):
        ds = self.ds + [decl('N.outside')]
        for config in ({'missing': {'primary': 'N.exp'}},
                       {'bound': {'primary': 'N.outside'}},
                       {'bound': {'primary': ''}}, {'bound': {'primary': 5}}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                self.render({'results.toml': config}, ds)

    def test_collection_ambiguous_hidden_and_unsafe_config_fails(self):
        ds = [decl('N.concept', kind='def'), decl('N.support', kind='def', explorerRole='support')]
        index = {'N.concept': 0, 'N.support': 1}
        rs = {'bound': {'decls': [0]}}
        mods = {'NLAlib.Test': {'topic': 'LowRank'}}
        collection = dict(id='lowrank', title='Low rank', description='D', topic='LowRank',
                          groups=[dict(id='group', title='Group', results=['bound'], definitions=['N.concept'])])
        def check(c):
            return b.collections_page({'collections': c}, rs, ds, index, mods, {'alias': 'bound'})
        bad_cases = []
        bad = copy.deepcopy(collection); bad['topic'] = 'Unknown'; bad_cases.append([bad])
        other = copy.deepcopy(collection); other['id'] = 'second'; bad_cases.append([collection, other])
        bad = copy.deepcopy(collection); bad['id'] = 'bad"id'; bad_cases.append([bad])
        bad = copy.deepcopy(collection); bad['groups'][0]['results'] = ['bound', 'alias']; bad_cases.append([bad])
        bad = copy.deepcopy(collection); bad['groups'][0]['definitions'] *= 2; bad_cases.append([bad])
        bad = copy.deepcopy(collection); bad['groups'][0]['definitions'] = ['N.support']; bad_cases.append([bad])
        for case in bad_cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                check(case)
        # Shared declarations across different groups are intentional navigation affordances.
        valid = copy.deepcopy(collection)
        extra = copy.deepcopy(valid['groups'][0]); extra['id'] = 'second'
        valid['groups'].append(extra)
        self.assertEqual(len(check([valid])[0]['groups']), 2)

    def test_rate_ids_are_safe(self):
        for key in ('families', 'rates'):
            cfg = copy.deepcopy(self.cfg)
            cfg[key][0]['id'] = 'bad"id'
            with self.assertRaisesRegex(ValueError, 'unsafe id'):
                self.render({'rates.toml': cfg})


if __name__ == '__main__':
    unittest.main()
