"""Rates from facets: generated rows, the reviewed overlay and its hash, pending rows, exact rows
and the URLs (docs/rates-design.md, "Rates from facets")."""
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from test_build import b, decl

ROOT = Path(__file__).resolve().parents[1]
facets = b.facets

ASYM = 'NLAlib.exists_forall_integral_frobNorm_sub_rsvd_sq_le_of_hasLaw_gaussianMatrix'
EXP = 'NLAlib.integral_frobNorm_sub_rsvd_sq_le_one_add_mul_of_hasLaw_gaussianMatrix'
TAIL = 'NLAlib.exists_forall_measureReal_frobNorm_sub_rsvd_sq_gt_le_of_hasLaw_countSketch'
TAIL_EXP = 'NLAlib.measureReal_frobNorm_sub_rsvd_sq_gt_le_mul_of_hasLaw_countSketch'
SPEC = 'NLAlib.integral_specNorm_sub_rsvd_sq_le_of_hasLaw_gaussianMatrix'


def digest(d):
    return hashlib.sha256(b.HTML_COMMENT.sub('', d.get('signature') or '').encode()).hexdigest()


class RatesFromFacets(unittest.TestCase):
    def decls(self):
        return [decl(EXP, 'Explicit Frobenius. [TroppWebber2023, Theorem 8.7]\nResult: rsvd-expected', signature='e'),
                decl(ASYM, '$O(k/\\varepsilon)$ suffices. <!-- marker -->\nAsymptotic: ' + EXP, signature='a'),
                decl(TAIL_EXP, 'Explicit tail.\nResult: rsvd-tail'),
                decl(TAIL, 'There are absolute constants such that $\\ell \\ge Ck^2/\\delta$.\nAsymptotic: ' + TAIL_EXP),
                decl(SPEC, 'Spectral, no asymptotic form. [HalkoMartinssonTropp2011, Theorem 10.6]\nResult: rsvd-expected')]

    def config(self, ds):
        return {
            'families': [dict(id='low-rank', title='Low rank', description='D', algorithms=['RSVD', 'GN'],
                              subject_label='Algorithm')],
            'guarantees': [dict(id='expected-frobenius', family='low-rank', title='$(1+\\varepsilon)$ · expected error',
                                description='E')],
            'rates': [dict(id='rsvd-basic-gaussian', theorem=ASYM, guarantee='expected-frobenius',
                           resources=[dict(label='Range columns', bound='$O(k/\\varepsilon)$', kind='samples')],
                           notes='$k\\ge1$.', statement_hash=digest(ds[1]))],
        }

    def render(self, rates, ds=None, extra=None):
        ds = ds or self.decls()
        config = {'rates.toml': rates, **(extra or {})}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'site'
            with patch.object(b, 'load_toml', side_effect=lambda name: config.get(name, {})):
                b.build(dict(decls=copy.deepcopy(ds), modules=[dict(name='NLAlib.Test', path='NLAlib/Test.lean')]), {}, out)
            return json.loads((out / 'data.json').read_text())['rates']

    def test_every_pair_is_a_row_with_generated_cells(self):
        ds = self.decls()
        rates = self.render(self.config(ds), ds)
        by = {e['theorem']: e for e in rates['entries']}
        self.assertEqual(set(by), {ASYM, TAIL})
        reviewed, pending = by[ASYM], by[TAIL]
        self.assertEqual((reviewed['status'], reviewed['family'], reviewed['group']),
                         ('reviewed', 'low-rank', 'expected-frobenius'))
        c = reviewed['c']
        self.assertEqual((c['algorithm'], c['measure'], c['stat_key'], c['law'], c['output'], c['form']),
                         ('RSVD', 'Frobenius norm', 'expectation-2', 'Gaussian', 'plain', 'rate'))
        self.assertEqual(c['stat'], r'$\mathbb{E}\|\cdot\|_{\mathsf F}^2$')
        self.assertEqual((c['source'], c['sources'], c['resources']), ('TW 8.7', ['Tropp–Webber 2023'], ['samples']))
        self.assertEqual((reviewed['overview'], reviewed['explicit'], reviewed['result']), (1, 0, 'rsvd-expected'))
        # the vocabulary: the statistic as a formula, "tail bound", no "high probability"
        self.assertEqual(pending['c']['stat_key'], 'tail')
        self.assertEqual(facets.STATISTIC_LABELS['tail'], 'ℙ[·] · tail bound')

    def test_overlay_is_keyed_by_theorem_and_hash(self):
        ds = self.decls()
        cfg = self.config(ds)
        bad = copy.deepcopy(cfg); bad['rates'][0]['statement_hash'] = 'stale'
        with self.assertRaisesRegex(ValueError, 'statement_hash mismatch'):
            self.render(bad, ds)
        # the hash covers the signature only: a docstring edit keeps the row reviewed
        changed = copy.deepcopy(ds); changed[1]['doc'] = changed[1]['doc'].replace('suffices', 'is enough')
        self.assertEqual(self.render(cfg, changed)['entries'][0]['status'], 'reviewed')
        changed = copy.deepcopy(ds); changed[1]['signature'] = changed[1]['signature'] + ' '
        with self.assertRaisesRegex(ValueError, 'statement_hash mismatch'):
            self.render(cfg, changed)
        marker = copy.deepcopy(ds); marker[1]['doc'] = marker[1]['doc'].replace('marker', 'other marker')
        self.assertEqual(self.render(cfg, marker)['entries'][0]['status'], 'reviewed')
        for theorem in (EXP, 'NLAlib.missing'):
            bad = copy.deepcopy(cfg); bad['rates'][0]['theorem'] = theorem
            with self.subTest(theorem=theorem), self.assertRaisesRegex(ValueError, 'missing asymptotic theorem'):
                self.render(bad, ds)
        unproved = copy.deepcopy(ds); unproved[0]['sorry'] = True
        with self.assertRaisesRegex(ValueError, 'unproved'):
            self.render(cfg, unproved)
        # hand facet fields are gone: family and algorithm are optional, family follows the guarantee
        self.assertNotIn('algorithm', cfg['rates'][0])
        bad = copy.deepcopy(cfg); bad['rates'][0]['family'] = 'missing'
        with self.assertRaisesRegex(ValueError, 'unknown family'):
            self.render(bad, ds)

    def test_facets_and_guarantee_must_agree_on_the_family(self):
        ds = self.decls()
        cfg = self.config(ds)
        cfg['families'].append(dict(id='other', title='Other', description='D', algorithms=['RBKI']))
        cfg['guarantees'][0]['family'] = 'other'
        with self.assertRaisesRegex(ValueError, 'facets put it in family low-rank'):
            self.render(cfg, ds)
        bad = self.config(ds)
        bad['families'].append(dict(id='twice', title='Twice', description='D', algorithms=['RSVD']))
        with self.assertRaisesRegex(ValueError, 'already in family'):
            self.render(bad, ds)
        for algorithms in ('RSVD', [''], [3]):
            bad = self.config(ds); bad['families'][0]['algorithms'] = algorithms
            with self.subTest(algorithms=algorithms), self.assertRaisesRegex(ValueError, 'algorithms'):
                self.render(bad, ds)

    def test_resource_kinds(self):
        ds = self.decls()
        for resource in (dict(label='L', bound='b', kind='seconds'), dict(label='L', bound='b', extra='x')):
            bad = self.config(ds); bad['rates'][0]['resources'] = [resource]
            with self.subTest(resource=resource), self.assertRaises(ValueError):
                self.render(bad, ds)
        ok = self.config(ds)
        ok['rates'][0]['resources'] = [dict(label='Block size', bound='$r+2$', kind='block size'),
                                       dict(label='Depth', bound='$q$', kind='depth')]
        self.assertEqual(self.render(ok, ds)['entries'][0]['c']['resources'], ['block size', 'depth'])

    def test_pending_rows(self):
        ds = self.decls()
        rates = self.render(self.config(ds), ds)
        pending = next(e for e in rates['entries'] if e['status'] == 'pending')
        self.assertEqual((pending['family'], pending['overview'], pending['explicit'], pending['result']),
                         ('low-rank', 3, 2, 'rsvd-tail'))
        self.assertEqual(pending['id'], 'measurereal-frobnorm-sub-rsvd-sq-gt-le-of-haslaw-countsketch')
        self.assertNotIn('resources', pending)
        self.assertEqual(pending['c']['law'], 'CountSketch')
        group = next(g for g in rates['groups'] if g['id'] == pending['group'])
        self.assertEqual((group['family'], group['pending']), ('low-rank', True))
        self.assertTrue(group['title'].startswith('Frobenius norm · tail bound $\\mathbb{P}['))
        # a pair in no family goes to a generated family; exclusions and unproved pairs are left out
        cfg = self.config(ds); cfg['families'][0]['algorithms'] = ['GN']
        cfg['rates'] = []
        rates = self.render(cfg, ds)
        self.assertEqual({e['family'] for e in rates['entries']}, {'other-asymptotic'})
        self.assertEqual(rates['families'][-1]['id'], 'other-asymptotic')
        cfg = self.config(ds); cfg['generate'] = {'exclude_words': ['rsvd-tail']}
        self.assertEqual([e['theorem'] for e in self.render(cfg, ds)['entries']], [ASYM])
        unproved = copy.deepcopy(ds); unproved[3]['sorry'] = True
        self.assertEqual([e['theorem'] for e in self.render(self.config(ds), unproved)['entries']], [ASYM])
        for generate in ({'exclude_words': 'x'}, {'other': []}):
            bad = self.config(ds); bad['generate'] = generate
            with self.subTest(generate=generate), self.assertRaises(ValueError):
                self.render(bad, ds)

    def test_sketch_property_rows(self):
        f = facets.infer_property('NLAlib.exists_forall_isObliviousSubspaceEmbedding_of_hasLaw_srhtWithReplacement')
        self.assertEqual((f['algorithm'], f['law'], f['statistic'], f['form']),
                         ('Oblivious subspace embedding', 'SRHT, with replacement', 'tail', 'asymptotic'))
        self.assertEqual(facets.statistic_tex(f), r'$\mathbb{P}[\text{failure}]$')
        self.assertIsNone(facets.infer_property(ASYM))
        ds = [decl('NLAlib.hasJLProperty_of_hasLaw_gaussianMatrix', 'Result: jl'),
              decl('NLAlib.exists_forall_hasJLProperty_of_hasLaw_gaussianMatrix', 'Asymptotic: NLAlib.hasJLProperty_of_hasLaw_gaussianMatrix')]
        cfg = dict(families=[dict(id='embeddings', title='E', description='D', algorithms=['Distributional JL'])])
        e = self.render(cfg, ds)['entries'][0]
        self.assertEqual((e['family'], e['status'], e['c']['algorithm'], e['c']['law_class']),
                         ('embeddings', 'pending', 'Distributional JL', 'Other'))
        cfg['law_classes'] = {'Gaussian': ['Gaussian']}
        self.assertEqual(self.render(cfg, ds)['entries'][0]['c']['law_class'], 'Gaussian')

    def test_exact_rows_are_overlay_only(self):
        ds = self.decls() + [decl('NLAlib.variance_girardHutchinson_of_hasLaw_haarFrame', 'Var = 2.', signature='v')]
        cfg = self.config(ds)
        cfg['families'].append(dict(id='trace', title='Trace', description='D', algorithms=['Girard–Hutchinson'],
                                    resources_label='Exact value'))
        cfg['guarantees'].append(dict(id='probe', family='trace', title='One probe', description='D'))
        cfg['rates'].append(dict(id='trace-haar-frame', kind='exact', theorem=ds[5]['name'], guarantee='probe',
                                 label='Haar frame', resources=[dict(label='Variance', bound='$2$')],
                                 statement_hash=digest(ds[5])))
        rates = self.render(cfg, ds)
        exact = next(e for e in rates['entries'] if e.get('kind') == 'exact')
        self.assertEqual((exact['status'], exact['family'], exact['overview'], exact['explicit'], exact['result']),
                         ('reviewed', 'trace', 5, 5, None))
        self.assertEqual((exact['c']['form'], exact['c']['stat_key'], exact['c']['detail'], exact['c']['algorithm']),
                         ('exact', 'variance', 'Haar frame', 'Girard–Hutchinson'))
        self.assertEqual(sum(e['theorem'] == ds[5]['name'] for e in rates['entries']), 1)
        bad = copy.deepcopy(cfg); bad['rates'][1]['statement_hash'] = 'stale'
        with self.assertRaisesRegex(ValueError, 'statement_hash'):
            self.render(bad, ds)

    def test_bounds_without_a_rate_form(self):
        ds = self.decls()
        rates = self.render(self.config(ds), ds)
        self.assertEqual([(x['i'], x['result'], x['family']) for x in rates['norate']], [(4, 'rsvd-expected', 'low-rank')])
        self.assertEqual((rates['norate'][0]['c']['measure'], rates['norate'][0]['c']['source']),
                         ('Spectral norm', 'HMT 10.6'))

    def test_urls_stay(self):
        ds = self.decls()
        rates = self.render(self.config(ds), ds)
        ids = [e['id'] for e in rates['entries']]
        self.assertIn('rsvd-basic-gaussian', ids)
        self.assertEqual(len(ids), len(set(ids)))
        for e in rates['entries']:
            self.assertRegex(e['id'], r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
        # a pending id that collides with a reviewed id gets a suffix
        cfg = self.config(ds)
        cfg['rates'][0]['id'] = 'measurereal-frobnorm-sub-rsvd-sq-gt-le-of-haslaw-countsketch'
        ids = [e['id'] for e in self.render(cfg, ds)['entries']]
        self.assertEqual(ids[1], ids[0] + '-2')
        # the page routes `#rate/<id>`, `#rate/<declaration>` and `#rate-row-<id>`, and copies a
        # pending row's link by its declaration (web/app.js)
        app = (ROOT / 'web' / 'app.js').read_text()
        self.assertIn(r"/^#rate(?:\/|-row-)(.+)$/", app)
        self.assertIn("x.theorem === key", app)
        self.assertIn("e.status === 'pending' ? e.theorem : e.id", app)
        self.assertIn("id=\"rate-row-${esc(e.id)}\"", app)

    def test_repository_rates_toml(self):
        cfg = tomllib.loads((ROOT / 'rates.toml').read_text())
        retired = {'algorithm', 'variant', 'sketch', 'sketch_category', 'norm', 'mode', 'gap', 'probe',
                   'probe_class', 'probe_law', 'family'}
        for row in cfg['rates']:
            with self.subTest(row=row['id']):
                self.assertFalse(retired & set(row))
                if row.get('kind') != 'exact':
                    self.assertTrue(all(r.get('kind') in b.RESOURCE_KINDS for r in row['resources']))
        texts = [g['title'] for g in cfg['guarantees']] + [r['label'] for row in cfg['rates'] for r in row['resources']]
        for text in texts:
            self.assertNotRegex(text, r'(?i)high probability|\bexpectation\b|squared|second moment|average|late truncation')
        for family in cfg['families']:
            self.assertNotIn('filters', family)
            self.assertTrue(family['algorithms'])
        self.assertEqual(cfg['generate']['exclude_words'][:2], ['precondition', 'kaczmarz'])


class Inference(unittest.TestCase):
    def test_absolute_error_after_a_scale(self):
        f = facets.infer('NLAlib.measureReal_mul_nuclearNorm_lt_abs_hutchpp_sub_trace_le_of_isSubgaussianVector')
        self.assertEqual((f['measure'], f['algorithm'], f['statistic']), ('abs', 'Hutch++', 'tail'))
        self.assertEqual(facets.statistic_tex(f), r'$\mathbb{P}[|\cdot| > t]$')

    def test_statistic_keys(self):
        self.assertEqual(facets.statistic_key({'statistic': 'expectation', 'moment': 2}), 'expectation-2')
        self.assertEqual(facets.statistic_key({'statistic': 'expectation', 'moment': 1}), 'expectation-1')
        self.assertEqual(facets.statistic_key({'statistic': 'variance'}), 'variance')
        self.assertEqual(list(facets.STATISTIC_LABELS), ['expectation-2', 'expectation-1', 'tail', 'variance'])


if __name__ == '__main__':
    unittest.main()
