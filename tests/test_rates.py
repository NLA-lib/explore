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
                        guarantee='relative-error', resources=[dict(label='columns', bound='$k/\\varepsilon$')],
                        statement_hash=hashlib.sha256(('sig\n' + doc).encode()).hexdigest())
        self.cfg = dict(guarantees=[dict(id='relative-error', family='family', title='Relative error', description='$1+\\varepsilon$', definitions=[])], families=[dict(id='family', title='Family', description='Description')], rates=[self.row])

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
        bad = copy.deepcopy(collection); bad['topic'] = 'bad/topic'; bad_cases.append([bad])
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

    def test_family_filters_allow_custom_scalar_without_norm_or_sketch(self):
        cfg = copy.deepcopy(self.cfg)
        family = cfg['families'][0]
        family['filters'] = [dict(field='preconditioner', label='Preconditioner')]
        row = cfg['rates'][0]
        for field in ('norm', 'mode', 'variant', 'sketch'):
            del row[field]
        row['preconditioner'] = 'Diagonal'
        site, _ = self.render({'rates.toml': cfg})
        self.assertEqual(site['rates']['families'][0]['filters'], family['filters'])
        self.assertEqual(site['rates']['entries'][0]['preconditioner'], 'Diagonal')
        self.assertNotIn('norm', site['rates']['entries'][0])
        for bad_value in (None, '', [], 3):
            bad = copy.deepcopy(cfg)
            if bad_value is None:
                del bad['rates'][0]['preconditioner']
            else:
                bad['rates'][0]['preconditioner'] = bad_value
            with self.subTest(value=bad_value), self.assertRaises(ValueError):
                self.render({'rates.toml': bad})

    def test_family_filters_validate_schema_and_do_not_infer(self):
        site, _ = self.render({'rates.toml': self.cfg})
        self.assertEqual(site['rates']['families'][0]['filters'], [])
        cases = [[dict(field='algorithm', label='')],
                 [dict(field='preconditioner', label='P')] * 2,
                 [dict(field='bad-field', label='P')],
                 [dict(field='Algorithm', label='P')], 'algorithm']
        cases += [[dict(field=field, label='P')] for field in
                  ('id', 'theorem', 'family', 'statement_hash', 'resources', 'overview',
                   'explicit', 'result', 'guarantee', 'notes', 'hash')]
        for filters in cases:
            bad = copy.deepcopy(self.cfg)
            bad['families'][0]['filters'] = filters
            with self.subTest(filters=filters), self.assertRaises(ValueError):
                self.render({'rates.toml': bad})
        # Optional display attributes still must be nonempty strings when supplied.
        for field in ('norm', 'mode', 'variant', 'sketch'):
            bad = copy.deepcopy(self.cfg)
            bad['rates'][0][field] = ''
            with self.assertRaises(ValueError):
                self.render({'rates.toml': bad})

    def test_filter_order_is_optional_generic_and_unique(self):
        cfg = copy.deepcopy(self.cfg)
        facet = dict(field='sketch_category', label='Sketch',
                     order=['Gaussian', 'Haar', 'Sparse', 'Trig', 'Other'])
        cfg['families'][0]['filters'] = [facet]
        cfg['rates'][0]['sketch_category'] = 'Gaussian'
        site, _ = self.render({'rates.toml': cfg})
        self.assertEqual(site['rates']['families'][0]['filters'][0]['order'], facet['order'])
        # Unused ordered values and new values are both allowed across future families.
        cfg['rates'][0]['sketch_category'] = 'New distribution'
        self.render({'rates.toml': cfg})
        for order in ('Gaussian', [''], [' '], [3], ['Gaussian', 'Gaussian']):
            bad = copy.deepcopy(cfg)
            bad['families'][0]['filters'][0]['order'] = order
            with self.subTest(order=order), self.assertRaisesRegex(ValueError, 'order'):
                self.render({'rates.toml': bad})

    def test_metadata_survives_physical_module_reorganization(self):
        old_module = 'NLAlib.Sketching.Gaussian.Haar'
        new_module = 'NLAlib.Sketching.Haar.Embedding'
        ds = copy.deepcopy(self.ds)
        ds += [decl('N.new_result', 'Result: future'), decl('N.futureConcept', kind='def')]
        for i, d in enumerate(ds):
            d.update(module=old_module, line=10 + i, endLine=11 + i)
        config = {
            'rates.toml': self.cfg,
            'results.toml': {'bound': {'primary': 'N.exp'}},
            'collections.toml': {'collections': [dict(
                id='sketching', title='Sketching', description='D', topic='Sketching',
                groups=[dict(id='haar', title='Haar', results=['bound'], definitions=[])])]},
        }
        def build_at(module, declarations):
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / 'site'
                data = dict(decls=copy.deepcopy(declarations), modules=[dict(
                    name=module, path=module.replace('.', '/') + '.lean')])
                with patch.object(b, 'load_toml', side_effect=lambda name: config.get(name, {})):
                    b.build(data, {}, out)
                return json.loads((out / 'data.json').read_text())
        before = build_at(old_module, ds)
        moved = copy.deepcopy(ds)
        for d in moved:
            d.update(module=new_module, line=d['line'] + 100, endLine=d['endLine'] + 100)
        after = build_at(new_module, moved)
        # Stable declaration identity and doc/signature hash preserve curated metadata.
        self.assertEqual(before['rates'], after['rates'])
        self.assertEqual(before['collections'], after['collections'])
        for site in (before, after):
            result = site['results']['bound']
            self.assertEqual(site['decls'][result['explicit']]['n'], 'N.exp')
            self.assertEqual(site['decls'][result['overview']]['n'], 'N.asym')
            self.assertEqual(site['collections'][0]['groups'][-1]['entries'], [
                {'type': 'r', 'rid': 'future'}, {'type': 'd', 'i': 3}])
        self.assertNotIn(old_module, after['modules'])
        self.assertEqual(after['modules'][new_module]['path'], 'NLAlib/Sketching/Haar/Embedding.lean')
        self.assertEqual(after['results']['bound']['module'], new_module)
        self.assertEqual([d['m'] for d in after['decls']], [new_module] * 4)
        self.assertEqual([d['l'] for d in after['decls']], [110, 111, 112, 113])
        self.assertEqual([d['e'] for d in after['decls']], [111, 112, 113, 114])

    def test_shared_guarantees_and_definition_links_resolve(self):
        cfg = copy.deepcopy(self.cfg)
        cfg['guarantees'][0]['definitions'] = [dict(label='Interface', declaration='N.interface')]
        cfg['rates'][0].update(algorithm_definition='N.interface', sketch_definition='N.sketch')
        ds = self.ds + [decl('N.interface', kind='structure'), decl('N.sketch', kind='def')]
        site, _ = self.render({'rates.toml': cfg}, ds)
        self.assertEqual(site['rates']['guarantees'][0]['definitions'][0]['i'], 2)
        self.assertEqual(site['rates']['entries'][0]['algorithm_definition_index'], 2)
        self.assertEqual(site['rates']['entries'][0]['sketch_definition_index'], 3)
        self.assertEqual(site['rates']['entries'][0]['guarantee'], 'relative-error')
        bad_cases = []
        bad = copy.deepcopy(cfg); bad['rates'][0]['guarantee'] = 'unknown'; bad_cases.append(bad)
        bad = copy.deepcopy(cfg); bad['guarantees'].append(copy.deepcopy(bad['guarantees'][0])); bad_cases.append(bad)
        bad = copy.deepcopy(cfg); bad['guarantees'][0]['family'] = 'missing'; bad_cases.append(bad)
        bad = copy.deepcopy(cfg)
        bad['families'].append(dict(id='other', title='Other', description='D'))
        bad['guarantees'][0]['family'] = 'other'; bad_cases.append(bad)
        for field in ('algorithm_definition', 'sketch_definition'):
            bad = copy.deepcopy(cfg); bad['rates'][0][field] = 'missing'; bad_cases.append(bad)
        for name in ('missing', 'N.exp'):
            bad = copy.deepcopy(cfg); bad['guarantees'][0]['definitions'][0]['declaration'] = name; bad_cases.append(bad)
        # a per-row label for the algorithm definition link: nonempty, reserved, and needs the link
        labelled = copy.deepcopy(cfg); labelled['rates'][0]['algorithm_definition_label'] = 'Isotropy'
        site, _ = self.render({'rates.toml': labelled}, ds)
        self.assertEqual(site['rates']['entries'][0]['algorithm_definition_label'], 'Isotropy')
        for value in ('', 3):
            bad = copy.deepcopy(labelled); bad['rates'][0]['algorithm_definition_label'] = value; bad_cases.append(bad)
        bad = copy.deepcopy(labelled); del bad['rates'][0]['algorithm_definition']; bad_cases.append(bad)
        bad = copy.deepcopy(cfg); bad['families'][0]['filters'] = [dict(field='algorithm_definition_label', label='L')]
        bad_cases.append(bad)
        for bad in bad_cases:
            with self.subTest(config=bad), self.assertRaises(ValueError):
                self.render({'rates.toml': bad}, ds)

    def test_curated_peer_topic_is_independent_of_source_paths(self):
        ds = [dict(decl('N.solve', 'Result: solve'), module='NLAlib.Sketching.Gaussian.Haar'),
              dict(decl('N.new', 'Result: future'), module='NLAlib.Sketching.Gaussian.Haar'),
              dict(decl('N.algorithm', kind='def'), module='NLAlib.Sketching.Gaussian.Haar')]
        cfg = {'collections': [
            dict(id='regression', topic='Regression', title='Regression', description='Solvers',
                 groups=[dict(id='solve', title='Solve', results=['solve'], definitions=['N.algorithm'])]),
            dict(id='sketching', topic='Sketching', title='Sketching', description='Sketches', groups=[])]}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'site'
            config = {'collections.toml': cfg, 'topics.toml': {'order': ['Regression', 'Sketching']}}
            with patch.object(b, 'load_toml', side_effect=lambda name: config.get(name, {})):
                b.build(dict(decls=ds, modules=[dict(name='NLAlib.Sketching.Gaussian.Haar',
                    path='NLAlib/Sketching/Gaussian/Haar.lean')]), {}, out)
            site = json.loads((out / 'data.json').read_text())
        self.assertEqual([t['id'] for t in site['topics']], ['Regression', 'Sketching'])
        self.assertEqual(site['topics'][0]['subs'], [])
        self.assertEqual(site['collections'][1]['groups'][0]['entries'], [{'type': 'r', 'rid': 'future'}])
        self.assertEqual(site['collections'][0]['groups'][0]['entries'],
                         [{'type': 'r', 'rid': 'solve'}, {'type': 'd', 'i': 2}])

    def test_shelf_sources_route_new_results_to_one_shelf(self):
        mod = lambda name, module: dict(decl(name, f'Result: {name[2:]}'), module=module)
        ds = [mod('N.cg', 'NLAlib.Krylov.LinearSystems.CG'), mod('N.lanczos', 'NLAlib.Krylov.Processes.Lanczos'),
              mod('N.sharp', 'NLAlib.Krylov.LinearSystems.WorstCase'), mod('N.loose', 'NLAlib.ForMathlib.Misc')]
        index = {d['name']: i for i, d in enumerate(ds)}
        rs = {d['name'][2:]: {'decls': [i]} for i, d in enumerate(ds)}
        shelf = lambda topic, sources: dict(id=topic.lower(), topic=topic, title=topic, description='D',
                                            sources=sources, groups=[])
        cfg = {'collections': [shelf('LinearSystems', ['NLAlib.Krylov.LinearSystems']),
                               shelf('Eigenvalues', ['NLAlib.Krylov']),
                               shelf('LowerBounds', ['NLAlib.Krylov.LinearSystems.WorstCase'])]}
        out = b.collections_page(cfg, rs, ds, index, {}, {})
        other = {c['topic']: [e['rid'] for g in c['groups'] for e in g['entries']] for c in out}
        # the longest matching prefix wins; a module under no prefix is on no shelf
        self.assertEqual(other, {'LinearSystems': ['cg'], 'Eigenvalues': ['lanczos'], 'LowerBounds': ['sharp']})
        bad = copy.deepcopy(cfg); bad['collections'][0]['sources'] = 'NLAlib.Krylov'
        with self.assertRaisesRegex(ValueError, 'sources'):
            b.collections_page(bad, rs, ds, index, {}, {})
        # shelves must name topics, and the site lists them in order
        for shelves, ok in ((['Eigenvalues', 'LinearSystems'], True), (['Missing'], False), (['Eigenvalues'] * 2, False)):
            config = {'collections.toml': cfg, 'topics.toml': {'shelves': shelves}}
            with self.subTest(shelves=shelves), tempfile.TemporaryDirectory() as tmp, \
                    patch.object(b, 'load_toml', side_effect=lambda name: config.get(name, {})):
                data = dict(decls=copy.deepcopy(ds), modules=[dict(name='NLAlib.Krylov.Processes.Lanczos', path='x.lean')])
                if ok:
                    b.build(data, {}, Path(tmp) / 'site')
                    self.assertEqual(json.loads((Path(tmp) / 'site/data.json').read_text())['shelves'], shelves)
                else:
                    with self.assertRaisesRegex(ValueError, 'shelves'):
                        b.build(data, {}, Path(tmp) / 'site')

    def test_family_subject_is_configured_scalar_and_labels_are_nonempty(self):
        cfg = copy.deepcopy(self.cfg)
        cfg['families'][0].update(subject_field='preconditioner', subject_label='Preconditioner',
                                  definition_label='Definition', notation='Let $p>0$.')
        cfg['rates'][0]['preconditioner'] = 'Diagonal'
        site, _ = self.render({'rates.toml': cfg})
        self.assertEqual(site['rates']['families'][0]['subject_field'], 'preconditioner')
        self.assertEqual(site['rates']['entries'][0]['preconditioner'], 'Diagonal')
        site, _ = self.render({'rates.toml': self.cfg})
        self.assertEqual(site['rates']['families'][0]['subject_field'], 'algorithm')
        for subject in ('bad-key', 'resources', 'theorem', '', 3):
            bad = copy.deepcopy(cfg); bad['families'][0]['subject_field'] = subject
            with self.subTest(subject=subject), self.assertRaises(ValueError):
                self.render({'rates.toml': bad})
        bad = copy.deepcopy(cfg); del bad['rates'][0]['preconditioner']
        with self.assertRaises(ValueError):
            self.render({'rates.toml': bad})
        for field in ('subject_label', 'definition_label', 'notation'):
            for value in ('', 3):
                bad = copy.deepcopy(cfg); bad['families'][0][field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.render({'rates.toml': bad})

    def exact_fixture(self):
        """An exact identity beside the asymptotic pair: one theorem, hashed like any row."""
        ds = self.ds + [decl('N.identity', 'Var = 2. <!-- value two 2 -->', signature='isig')]
        digest = lambda sig, doc: hashlib.sha256((sig + '\n' + b.HTML_COMMENT.sub('', doc)).encode()).hexdigest()
        cfg = copy.deepcopy(self.cfg)
        cfg['families'][0]['resources_label'] = 'Exact value'
        cfg['rates'].append(dict(id='identity', kind='exact', theorem='N.identity', family='family',
                                 algorithm='estimator', guarantee='relative-error',
                                 resources=[dict(label='Variance', bound='$2$')],
                                 statement_hash=digest('isig', ds[2]['doc'])))
        return ds, cfg, digest

    def test_exact_rows_cite_one_theorem_without_asymptotic_pairing(self):
        ds, cfg, digest = self.exact_fixture()
        site, _ = self.render({'rates.toml': cfg}, ds)
        asym, exact = site['rates']['entries']
        self.assertNotIn('kind', asym)
        self.assertEqual((asym['overview'], asym['explicit']), (1, 0))
        self.assertEqual((exact['kind'], exact['overview'], exact['explicit']), ('exact', 2, 2))
        self.assertEqual(site['rates']['families'][0]['resources_label'], 'Exact value')
        # an exact identity needs no Result id; one is recorded when present
        self.assertIsNone(exact['result'])
        ds[2]['doc'] += '\nResult: identity-result'
        cfg['rates'][1]['statement_hash'] = digest('isig', ds[2]['doc'])
        site, _ = self.render({'rates.toml': cfg}, ds)
        self.assertEqual(site['rates']['entries'][1]['result'], 'identity-result')
        # the hash still guards the summary
        bad = copy.deepcopy(cfg); bad['rates'][1]['statement_hash'] = 'stale'
        with self.assertRaisesRegex(ValueError, 'statement_hash'):
            self.render({'rates.toml': bad}, ds)

    def test_lower_rows_pair_with_a_reviewed_rate(self):
        ds, cfg, digest = self.exact_fixture()
        cfg['rates'][1].update(id='lower', kind='lower', pairs_with='rate')
        site, _ = self.render({'rates.toml': cfg}, ds)
        upper, lower = site['rates']['entries']
        self.assertEqual((lower['kind'], lower['overview'], lower['explicit']), ('lower', 2, 2))
        self.assertEqual((lower['c']['form'], upper['c']['form']), ('lower', 'rate'))
        self.assertEqual(upper['lower'], ['lower'])
        # pairs_with names a reviewed rate row of the family, and is allowed only on a lower row
        for change in (dict(pairs_with='missing'), dict(pairs_with='lower')):
            bad = copy.deepcopy(cfg); bad['rates'][1].update(change)
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'reviewed rate row'):
                self.render({'rates.toml': bad}, ds)
        bad = copy.deepcopy(cfg); bad['rates'][0]['pairs_with'] = 'lower'
        with self.assertRaisesRegex(ValueError, 'pairs_with'):
            self.render({'rates.toml': bad}, ds)
        # an unpaired lower bound is still a row of its own: no back-link on any rate
        unpaired = copy.deepcopy(cfg); del unpaired['rates'][1]['pairs_with']
        site, _ = self.render({'rates.toml': unpaired}, ds)
        upper, lower = site['rates']['entries']
        self.assertNotIn('lower', upper)
        self.assertEqual((lower['kind'], lower['c']['form']), ('lower', 'lower'))
        self.assertNotIn('pairs_with', lower)

    def test_paired_lower_bound_merges_into_its_rate_row(self):
        # the Rates page shows a paired lower bound in its rate's row (app.js: the rate row lists
        # `lower`, the lower entry is hidden by its `pairs_with`); its tightness is the indicator
        ds, cfg, digest = self.exact_fixture()
        cfg['rates'][1].update(id='lower', kind='lower', pairs_with='rate', tightness='gap')
        site, _ = self.render({'rates.toml': cfg}, ds)
        upper, lower = site['rates']['entries']
        self.assertEqual((upper['lower'], lower['pairs_with'], lower['tightness']), (['lower'], 'rate', 'gap'))
        # the lower theorem is the row's second statement, so it is no "bound without a rate form"
        self.assertNotIn(lower['overview'], [x['i'] for x in site['rates'].get('norate', [])])
        # a lower theorem without a Result id may name its result (its link)
        self.assertIsNone(lower['result'])
        named = copy.deepcopy(cfg); named['rates'][1]['result'] = 'bound'
        site, _ = self.render({'rates.toml': named}, ds)
        self.assertEqual(site['rates']['entries'][1]['result'], 'bound')
        for rows, k in (([1], 'missing'), ([0], 'bound')):
            bad = copy.deepcopy(cfg); bad['rates'][rows[0]]['result'] = k
            with self.subTest(row=rows[0], result=k), self.assertRaisesRegex(ValueError, 'result names'):
                self.render({'rates.toml': bad}, ds)
        # tightness is tight or gap, and only on a paired lower row
        for change, drop in ((dict(tightness='close'), None), ({}, 'pairs_with')):
            bad = copy.deepcopy(cfg); bad['rates'][1].update(change)
            if drop:
                del bad['rates'][1][drop]
            with self.subTest(change=change, drop=drop), self.assertRaisesRegex(ValueError, 'tightness'):
                self.render({'rates.toml': bad}, ds)

    def test_exact_rows_reject_pairings_and_unknown_kinds(self):
        ds, cfg, digest = self.exact_fixture()
        for theorem, sig, i in (('N.asym', 'sig', 1), ('N.exp', '', 0)):
            # an asymptotic declaration, or an explicit theorem that has one, is not exact
            bad = copy.deepcopy(cfg)
            bad['rates'][1].update(theorem=theorem, statement_hash=digest(sig, ds[i]['doc']))
            with self.subTest(theorem=theorem), self.assertRaisesRegex(ValueError, 'asymptotic pairing'):
                self.render({'rates.toml': bad}, ds)
        for theorem in ('missing', 'N.concept'):
            bad = copy.deepcopy(cfg); bad['rates'][1]['theorem'] = theorem
            with self.subTest(theorem=theorem), self.assertRaisesRegex(ValueError, 'missing exact theorem'):
                self.render({'rates.toml': bad}, ds + [decl('N.concept', kind='def')])
        for kind in ('asymptotic', 'Exact', ''):
            bad = copy.deepcopy(cfg); bad['rates'][1]['kind'] = kind
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'kind'):
                self.render({'rates.toml': bad}, ds)
        # rows without `kind` keep the paired contract: an untagged plain theorem is rejected
        bad = copy.deepcopy(cfg); del bad['rates'][1]['kind']
        with self.assertRaisesRegex(ValueError, 'missing asymptotic theorem'):
            self.render({'rates.toml': bad}, ds)
        bad = copy.deepcopy(ds); bad[2]['sorry'] = True
        with self.assertRaisesRegex(ValueError, 'unproved'):
            self.render({'rates.toml': cfg}, bad)
        bad = copy.deepcopy(cfg); bad['families'][0]['filters'] = [dict(field='kind', label='Kind')]
        with self.assertRaisesRegex(ValueError, 'reserved'):
            self.render({'rates.toml': bad}, ds)
        for value in ('', 3):
            bad = copy.deepcopy(cfg); bad['families'][0]['resources_label'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.render({'rates.toml': bad}, ds)


if __name__ == '__main__':
    unittest.main()
