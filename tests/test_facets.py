"""Facet inference from declaration names, the statements table, merges and the vocabulary."""
import contextlib
import io
from pathlib import Path
import tomllib
import unittest

from test_build import BuildTests, b, decl


class Rendered(unittest.TestCase):
    render = BuildTests.render

facets = b.facets
ROOT = Path(__file__).resolve().parents[1]


class InferenceTests(unittest.TestCase):
    def test_outside_the_grammar(self):
        self.assertIsNone(facets.infer('NLAlib.eigenvalue_add_le'))
        self.assertIsNone(facets.infer('Matrix.IsHermitian.cgIterate_eq'))

    def test_expected_error(self):
        f = facets.infer('NLAlib.integral_frobNorm_sub_rsvd_sq_le_of_hasLaw_gaussianMatrix')
        self.assertEqual((f['statistic'], f['measure'], f['moment'], f['algorithm'], f['law'],
                          f['output'], f['form'], f['exact']),
                         ('expectation', 'frobenius', 2, 'RSVD', 'Gaussian', 'plain', 'explicit', False))
        f = facets.infer('NLAlib.integral_specNorm_sub_rsvd_le_of_isLeftUnitarilyInvariant')
        self.assertEqual((f['measure'], f['moment'], f['law']), ('spectral', 1, 'rotation-invariant'))
        f = facets.infer('NLAlib.exists_forall_integral_frobNorm_sub_truncatedSVD_rsvd_sq_le_of_hasLaw_gaussianMatrix')
        self.assertEqual((f['form'], f['output']), ('asymptotic', 'late'))
        f = facets.infer('NLAlib.integral_frobNorm_sub_earlyTruncatedRSVD_sq_le_one_add_mul_of_hasLaw_gaussianMatrix')
        self.assertEqual((f['algorithm'], f['output'], f['details']), ('RSVD', 'early', ['(1 + ε) form']))
        f = facets.infer('NLAlib.integral_specNorm_sub_rsvd_pow_mul_sq_le_singularGapRatio_of_hasLaw_gaussianMatrix')
        self.assertEqual((f['algorithm'], f['regime']), ('RSI', 'gapped'))

    def test_tail_spellings(self):
        # the variants in the library today, and `measure_` beside `measureReal_`
        names = ['NLAlib.measureReal_not_frobNorm_sub_rsvd_sq_le_le_of_hasLaw_gaussianMatrix',
                 'NLAlib.measureReal_frobNorm_sub_rsvd_sq_gt_le_of_hasLaw_gaussianMatrix',
                 'NLAlib.measure_frobNorm_sub_rsvd_sq_gt_le_of_hasLaw_gaussianMatrix',
                 'NLAlib.measure_not_frobNorm_sub_rsvd_sq_le_le_of_hasLaw_gaussianMatrix',
                 'NLAlib.measureReal_frobNorm_sub_rsvd_sq_ge_le_of_hasLaw_gaussianMatrix']
        for name in names:
            with self.subTest(name=name):
                f = facets.infer(name)
                self.assertEqual((f['statistic'], f['measure'], f['moment'], f['algorithm'], f['law']),
                                 ('tail', 'frobenius', 2, 'RSVD', 'Gaussian'))
        f = facets.infer('NLAlib.measureReal_not_specNorm_sub_rsvd_le_le_of_hasLaw_gaussianMatrix')
        self.assertEqual((f['measure'], f['moment']), ('spectral', 1))

    def test_laws_interfaces_and_dependencies(self):
        f = facets.infer('NLAlib.HasSubspaceInjection.measure_frobNorm_sub_rsvd_sq_gt_le')
        self.assertEqual(f['law'], 'any subspace injection')
        f = facets.infer('NLAlib.measureReal_frobNorm_sub_rsvd_sq_gt_le_of_hasLaw_srhtWithReplacement')
        self.assertEqual(f['law'], 'SRHT, with replacement')
        f = facets.infer('NLAlib.measureReal_frobNorm_sub_rsvd_sq_gt_le_of_hasLaw_samplingSketchWithoutReplacement')
        self.assertEqual(f['law'], 'uniform sampling without replacement')
        # no algorithm in the name: the statement's dependencies supply it
        name = 'NLAlib.integral_specNorm_sub_sq_le_of_isBestRankApprox_of_hasLaw_gaussianMatrix'
        self.assertIsNone(facets.infer(name)['algorithm'])
        f = facets.infer(name, ['NLAlib.frobNorm', 'NLAlib.rsvd', 'NLAlib.truncatedSVD'])
        self.assertEqual((f['algorithm'], f['output']), ('RSVD', 'late'))
        self.assertIn('any best rank-k approximation of the output', f['details'])

    def test_measures(self):
        f = facets.infer('NLAlib.SymmetricGauge.integral_matrixNorm_conjTranspose_mul_self_sub_rsvd_le_of_hasLaw_gaussianMatrix')
        self.assertEqual(f['measure'], 'gram')
        self.assertIn(r'(\cdot)^{\mathsf H}(\cdot)', facets.statistic_tex(f))
        f = facets.infer('NLAlib.integral_specNorm_sub_truncatedSVD_rsvd_sq_add_frobNorm_sub_truncatedSVD_sq_le')
        self.assertEqual((f['measure'], f['moment']), ('spectral+frobenius', 2))
        f = facets.infer('NLAlib.measureReal_abs_hutchpp_sub_trace_ge_le')
        self.assertEqual((f['measure'], f['algorithm'], f['law']), ('abs', 'Hutch++', None))
        f = facets.infer('NLAlib.variance_hutchpp_of_hasLaw_gaussianMatrix')
        self.assertEqual((f['statistic'], f['exact']), ('variance', True))

    def test_statistic_formulas(self):
        tex = lambda n: facets.statistic_tex(facets.infer(n))
        self.assertEqual(tex('NLAlib.integral_frobNorm_sub_rsvd_sq_le_of_hasLaw_gaussianMatrix'),
                         r'$\mathbb{E}\|\cdot\|_{\mathsf F}^2$')
        self.assertEqual(tex('NLAlib.integral_specNorm_sub_rsvd_le_of_hasLaw_gaussianMatrix'),
                         r'$\mathbb{E}\|\cdot\|_2$')
        self.assertEqual(tex('NLAlib.measureReal_not_specNorm_sub_rsvd_sq_le_le_of_hasLaw_gaussianMatrix'),
                         r'$\mathbb{P}[\|\cdot\|_2^2 > t]$')
        self.assertTrue(tex('NLAlib.integral_frobNorm_sub_mul_sketchAndSolve_sq_of_hasLaw_gaussianMatrix')
                        .endswith('(exact)'))

    def test_overrides(self):
        f = facets.apply_override(facets.infer('NLAlib.HasSubspaceInjection.measure_frobNorm_sub_mul_sq_gt_le'),
                                  {'algorithm': 'RSVD', 'output': 'early', 'label': 'any projector'})
        self.assertEqual((f['algorithm'], f['output'], f['label'], f['law']),
                         ('RSVD', 'early', 'any projector', 'any subspace injection'))
        f = facets.apply_override(None, {'statistic': 'tail', 'measure': 'spectral'})
        self.assertEqual((f['statistic'], f['measure']), ('tail', 'spectral'))
        for bad in ({'colour': 'red'}, {'statistic': 'mean'}, {'output': 'truncated'}, {'measure': 'operator'}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                facets.apply_override(None, bad)

    def test_sources(self):
        self.assertEqual(facets.citation_short('TroppWebber2023', 'Theorem 8.1 (RSVD2)'), 'TW 8.1 (RSVD2)')
        self.assertEqual(facets.citation_short('HalkoMartinssonTropp2011', 'Theorem 10.6'), 'HMT 10.6')
        self.assertEqual(facets.citation_short('Woodruff2014', 'Lemma 48'), 'Woodruff Lemma 48')
        self.assertEqual(facets.citation_short('TroppWebber2023', 'Theorem 8.1', {'TroppWebber2023': 'T–W'}),
                         'T–W 8.1')
        text = facets.citation_search_text('TroppWebber2023', 'Theorem 8.1 (RSVD2)')
        for part in ('TW 8.1 (RSVD2)', 'Tropp–Webber 2023 Theorem 8.1 (RSVD2)', 'TroppWebber2023'):
            self.assertIn(part, text)

    def test_drop_article(self):
        self.assertEqual(facets.drop_article('The tail of the randomized SVD'), 'Tail of the randomized SVD')
        self.assertEqual(facets.drop_article('Theorem of Weyl'), 'Theorem of Weyl')
        self.assertEqual(facets.drop_article('The $\\chi^2$ tail'), '$\\chi^2$ tail')


RSVD = 'NLAlib.integral_{m}_sub_rsvd{sq}_le_of_{law}'


def bound(m='frobNorm', sq='_sq', law='hasLaw_gaussianMatrix', doc='', rid='rsvd'):
    return decl(RSVD.format(m=m, sq=sq, law=law), f'{doc}\nResult: {rid}')


class TableTests(Rendered):
    def test_every_member_is_a_row(self):
        ds = [bound(doc='**RSVD, Frobenius.** E ≤ … [TroppWebber2023, Theorem 8.7].'),
              bound(m='specNorm', doc='**RSVD, spectral.** E ≤ … [TroppWebber2023, Theorem 8.1 (RSVD2)].'),
              bound(m='specNorm', sq='', doc='**RSVD, spectral, as printed.** [HalkoMartinssonTropp2011, Theorem 10.6].'),
              bound(law='isLeftUnitarilyInvariant'),
              decl('NLAlib.exists_forall_integral_frobNorm_sub_rsvd_sq_le_of_hasLaw_gaussianMatrix',
                   'O(k/ε) suffices.\nAsymptotic: ' + RSVD.format(m='frobNorm', sq='_sq', law='hasLaw_gaussianMatrix'))]
        r = self.render(ds)['results']['rsvd']
        self.assertEqual(sorted((row['o'], row['e']) for row in r['rows']), [(1, 1), (2, 2), (3, 3), (4, 0)])
        self.assertEqual(r['rows'][r['row']], dict(r['rows'][r['row']], o=4, e=0))
        # grouped by measure, the headline's group first; the statistic is a formula
        self.assertEqual([row['g'] for row in r['rows']],
                         ['Frobenius norm', 'Frobenius norm', 'Spectral norm', 'Spectral norm'])
        self.assertEqual([c['k'] for c in r['cols']], ['stat', 'law', 'form', 'source'])
        spectral = [row for row in r['rows'] if row['g'] == 'Spectral norm']
        self.assertEqual([row['c']['stat'] for row in spectral],
                         [r'$\mathbb{E}\|\cdot\|_2^2$', r'$\mathbb{E}\|\cdot\|_2$'])
        self.assertEqual([row['c']['source'] for row in spectral], ['TW 8.1 (RSVD2)', 'HMT 10.6'])
        self.assertIn('TW 8.1 (RSVD2)', spectral[0]['x'])
        self.assertIn('Tropp–Webber 2023 Theorem 8.1 (RSVD2)', spectral[0]['x'])
        self.assertEqual(r['rows'][0]['c']['form'], r'explicit, $O(\cdot)$')
        self.assertIn('Spectral norm', spectral[0]['l'])

    def test_rows_alike_get_names(self):
        ds = [bound(doc='**RSVD, relative error.** A.'),
              decl('NLAlib.integral_frobNorm_sub_rsvd_sq_le_of_hasLaw_gaussianMatrix_of_x', '**RSVD, constant factor.** B.\nResult: rsvd')]
        r = self.render(ds)['results']['rsvd']
        self.assertEqual([row['c'].get('detail') for row in r['rows']], ['relative error', 'constant factor'])

    def test_deterministic_rows_by_name(self):
        ds = [decl('N.lower', '**Courant–Fischer, lower bound.** A.\nResult: cf'),
              decl('N.upper', '**Courant–Fischer, upper bound.** B.\nResult: cf'),
              decl('N.helper', 'C.\nResult: cf')]
        r = self.render(ds)['results']['cf']
        self.assertEqual(r['title'], 'Courant–Fischer')
        self.assertEqual([c['k'] for c in r['cols']], ['name'])
        self.assertEqual([row['c']['name'] for row in r['rows']], ['lower bound', 'upper bound', '`helper`'])

    def test_facets_toml(self):
        ds = [bound(), decl('NLAlib.integral_frobNorm_one_sub_obliqueProjector_mul_sq_of_hasLaw_gaussianMatrix', 'Result: rsvd')]
        cfg = {'facets.toml': {'overrides': {ds[1]['name']: {'algorithm': 'RSVD', 'label': 'projector form'}}}}
        site = self.render(ds, cfg)
        self.assertEqual(site['decls'][1]['fc']['algorithm'], 'RSVD')
        self.assertEqual(site['results']['rsvd']['rows'][1]['c']['detail'], 'projector form')
        with self.assertRaisesRegex(ValueError, 'override for unknown declaration'):
            self.render(ds, {'facets.toml': {'overrides': {'NLAlib.gone': {'label': 'x'}}}})

    def test_member_graph(self):
        ds = [decl('N.def', kind='def'), decl('N.helper', valueDeps=['N.def']),
              decl('N.a', 'Result: r', valueDeps=['N.helper']), decl('N.b', 'Result: r'),
              decl('N.user', 'Result: s', valueDeps=['N.a'])]
        site = self.render(ds)
        self.assertEqual((site['decls'][2]['nu'], site['decls'][2]['nb']), ([0], [4]))
        self.assertEqual((site['decls'][3]['nu'], site['decls'][3]['nb']), ([], []))
        self.assertEqual(site['nodes']['r:r']['u'], ['d:N.def'])


class MergeTests(Rendered):
    def decls(self):
        return [decl('N.e', '**Expected error.** A.\nResult: expected'),
                decl('N.hmt', '**Average spectral error.** B.\nResult: average'),
                decl('N.hmt2', '**Average spectral error, rotation-invariant.** C.\nResult: average'),
                decl('N.user', 'Result: other', valueDeps=['N.hmt'])]

    def test_merge_into(self):
        cfg = {'results.toml': {'average': {'merge_into': 'expected', 'aliases': ['HMT 10.6']}}}
        site = self.render(self.decls(), cfg)
        self.assertNotIn('average', site['results'])
        r = site['results']['expected']
        self.assertEqual(r['decls'], [0, 1, 2])
        self.assertEqual(r['merged'], ['average'])
        self.assertIn('HMT 10.6', r['aliases'])
        self.assertEqual(len(r['rows']), 3)
        self.assertEqual(site['resultAlias'], {'average': 'expected'})
        self.assertEqual(site['aliasFocus'], {'average': 1})
        self.assertEqual(site['decls'][1]['r'], ['expected'])
        self.assertEqual(site['nodes']['r:other']['u'], ['r:expected'])

    def test_merge_errors(self):
        for cfg, msg in [({'average': {'merge_into': 'missing'}}, 'must name another result'),
                         ({'average': {'merge_into': 'average'}}, 'must name another result'),
                         ({'gone': {'merge_into': 'expected'}}, 'unknown or alias'),
                         ({'average': {'merge_into': 'expected', 'title': 'X'}}, 'take only aliases'),
                         ({'average': {'merge_into': 'expected'}, 'expected': {'merge_into': 'other'}},
                          'itself merged')]:
            with self.subTest(cfg=cfg), self.assertRaisesRegex(ValueError, msg):
                self.render(self.decls(), {'results.toml': cfg})

    def test_titles_and_vocabulary(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            site = self.render([decl('N.x', '**The average error of X.** A.\nResult: x')])
        self.assertEqual(site['results']['x']['title'], 'Average error of X')
        self.assertIn('"average"', err.getvalue())
        self.assertEqual(b.vocabulary_issues('RSVD: tail bounds'), [])
        self.assertTrue(b.vocabulary_issues('Deviation bound for the error'))
        self.assertTrue(b.vocabulary_issues('Relative residual with high probability'))
        self.assertTrue(b.vocabulary_issues('Mean squared error'))
        self.assertEqual(b.vocabulary_issues('The inverse mean of a Beta matrix'), ['a leading "The"'])


class ConfigTests(unittest.TestCase):
    """The repository's own curation files follow the decisions."""

    def test_results_toml(self):
        cfg = tomllib.loads((ROOT / 'results.toml').read_text())
        for rid, entry in cfg.items():
            self.assertNotIn('variant_labels', entry, rid)
            if 'title' in entry:
                self.assertEqual(b.vocabulary_issues(entry['title']), [], rid)
        self.assertEqual(cfg['randomized-svd-average-spectral-error']['merge_into'], 'randomized-svd-expected-error')
        self.assertEqual(cfg['randomized-svd-deviation-bound']['merge_into'], 'randomized-svd-tail')

    def test_facets_toml(self):
        cfg = tomllib.loads((ROOT / 'facets.toml').read_text())
        self.assertLessEqual(set(cfg), {'sources', 'overrides'})
        for name, entry in cfg.get('overrides', {}).items():
            with self.subTest(name=name):
                facets.apply_override(facets.infer(name), entry)


del BuildTests, Rendered

if __name__ == '__main__':
    unittest.main()
