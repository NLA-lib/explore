import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_build import b, decl

REPORT = '''+++
title = "Two results"
authors = ["A. Author"]
date = "2026-10-26"
status = "draft"
abstract = """How [[result:top]] follows from [[NLAlib.lemma]]."""
results = ["top", "old-base"]
declarations = ["NLAlib.concept"]
related = ["other"]

[statements]
"NLAlib.top" = "HASH"
+++
## Introduction

We prove [[result:top|the top bound]] from [[result:base]] and [[NLAlib.lemma]] [Key2020, §2];
see also [[report:other]]. A `[[not.a.link]]` in code and $[[1,2]]$ in maths are left alone.

{{statement NLAlib.top}}

{{diagram}}
'''

OTHER = '''+++
title = "Other"
abstract = "Another."
+++
Body.
'''


def decls():
    return [decl('N.concept', '**Concept.** A thing.', kind='def'),
            decl('NLAlib.lemma', 'Helper.', valueDeps=['NLAlib.base']),
            decl('NLAlib.base', '**Base.** Base bound.\nResult: base, old-base'),
            decl('NLAlib.top', '**Top.** Top bound.\nResult: top', signature='sig',
                 valueDeps=['NLAlib.lemma', 'N.concept'])]


def top_hash():
    return b.statement_hash(dict(signature='sig', doc='**Top.** Top bound.\nResult: top'))


class ReportTests(unittest.TestCase):
    def render(self, reports, ds=None, bib=None):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'site'
            with patch.object(b, 'load_toml', side_effect=lambda name: {}):
                b.build(dict(decls=copy.deepcopy(ds or decls()),
                             modules=[dict(name='NLAlib.Test', path='NLAlib/Test.lean')]), bib or {}, out, dict(reports))
            pages = {str(p.relative_to(out / 'reports')): p.read_text() for p in (out / 'reports').rglob('index.html')}
            return json.loads((out / 'data.json').read_text()), pages

    def good(self):
        return {'two-results': REPORT.replace('HASH', top_hash()).replace(
            'declarations = ["NLAlib.concept"]', 'declarations = ["N.concept"]'), 'other': OTHER}

    def test_front_matter_resolution_graph_and_pages(self):
        site, pages = self.render(self.good(), bib={'Key2020': dict(text='A paper.', url=None)})
        rep = next(r for r in site['reports'] if r['id'] == 'two-results')
        self.assertEqual(rep['title'], 'Two results')
        self.assertEqual(rep['results'], ['top', 'base'])         # an alias id names its result
        self.assertEqual(rep['declarations'], ['N.concept'])
        self.assertEqual((rep['stale'], rep['cites']), ([], ['Key2020']))
        self.assertTrue(rep['body'].startswith('## Introduction'))
        self.assertNotIn('+++', rep['body'])
        # base reaches top through the uncovered lemma; the concept is used by top directly
        self.assertEqual(rep['graph']['edges'], [['d:N.concept', 'r:top'], ['r:base', 'r:top']])
        self.assertEqual({n['k']: n['l'] for n in rep['graph']['nodes']},
                         {'r:top': 1, 'r:base': 0, 'd:N.concept': 0})
        self.assertIn('Key2020', site['bib'])                     # cited by a report only
        self.assertEqual(set(pages), {'index.html', 'two-results/index.html', 'other/index.html'})
        one = pages['two-results/index.html']
        self.assertIn('data-page="report" data-report="two-results" data-base="../../"', one)
        self.assertIn('<title>Two results · NLAlib explorer</title>', one)
        self.assertIn('src="../../app.js', one)
        self.assertIn('href="../../reports/" data-page="reports"', one)
        self.assertIn('data-page="reports" data-base="../"', pages['index.html'])

    def test_unknown_targets_fail_together(self):
        bad = self.good()['two-results'].replace('results = ["top", "old-base"]', 'results = ["top", "nope"]')
        bad = bad.replace('[[NLAlib.lemma]] [Key2020', '[[NLAlib.missing]] [[result:gone]] [[report:none]] [Nobody2001')
        bad = bad.replace('related = ["other"]', 'related = ["two-results"]')
        with self.assertRaises(ValueError) as e:
            self.render({'two-results': bad, 'other': OTHER}, bib={'Key2020': dict(text='A paper.', url=None)})
        for msg in ('unknown result nope', 'link to unknown declaration NLAlib.missing',
                    'unknown result gone', 'unknown report none', 'Nobody2001', 'related names an unknown report two-results'):
            self.assertIn(msg, str(e.exception))
        no_decl = self.good()['two-results'].replace('["N.concept"]', '["N.nothing"]')
        with self.assertRaisesRegex(ValueError, 'unknown declaration N.nothing'):
            self.render({'two-results': no_decl, 'other': OTHER})

    def test_statement_hash_flags_changes(self):
        stale = self.good()['two-results'].replace(top_hash(), 'old')
        site, _ = self.render({'two-results': stale, 'other': OTHER})
        rep = next(r for r in site['reports'] if r['id'] == 'two-results')
        self.assertEqual((rep['stale'], rep['unrecorded']), (['NLAlib.top'], []))
        missing = stale.replace('"NLAlib.top" = "old"\n', '')
        rep = next(r for r in self.render({'two-results': missing, 'other': OTHER})[0]['reports']
                   if r['id'] == 'two-results')
        self.assertEqual(rep['unrecorded'], ['NLAlib.top'])
        extra = self.good()['two-results'].replace('[statements]\n', '[statements]\n"NLAlib.base" = "x"\n')
        with self.assertRaisesRegex(ValueError, 'does not cite'):
            self.render({'two-results': extra, 'other': OTHER})
        sorry = decls(); sorry[3]['sorry'] = True
        with self.assertRaisesRegex(ValueError, 'unproved'):
            self.render(self.good(), ds=sorry)

    def test_syntax_guards(self):
        base = self.good()
        for body, msg in [('Text {{diagram}} inline.', 'paragraph of its own'),
                          ('{{figure x}}', 'unknown directive'),
                          ('{{statement}}', 'unknown directive'),
                          ('See [[thm:foo]].', 'unknown link kind thm'),
                          ('See [[NLAlib.top.', 'unmatched'),
                          ('{{ broken', 'malformed')]:
            with self.assertRaisesRegex(ValueError, msg):
                self.render({'other': OTHER, 'two-results': base['two-results'] + '\n' + body + '\n'})

    def test_front_matter_guards(self):
        for text, msg in [('No front matter.', 'missing'),
                          ('+++\ntitle = "x"\n+++\n', 'abstract'),
                          ('+++\ntitle = "x"\nabstract = "y"\nsummary = "z"\n+++\n', 'unknown front-matter field summary'),
                          ('+++\ntitle = "x"\nabstract = "y"\nresults = "top"\n+++\n', 'results must be a list'),
                          ('+++\ntitle = = "x"\n+++\n', 'front matter')]:
            with self.assertRaisesRegex(ValueError, msg):
                self.render({'r': text})
        with self.assertRaisesRegex(ValueError, 'unsafe file name'):
            self.render({'Bad_Name': OTHER})

    def test_no_reports(self):
        site, pages = self.render({})
        self.assertEqual(site['reports'], [])
        self.assertEqual(set(pages), {'index.html'})


if __name__ == '__main__':
    unittest.main()
