// The NLA-lib explorer: a catalogue of NLAlib's results and definitions by topic, a search box,
// and a panel with the statement, the Lean, the source link and the dependency graph of one
// result. All data comes from data.json, which build.py writes from the library.
'use strict';

(async function () {
  const $ = (sel, el = document) => el.querySelector(sel);
  const esc = s => String(s ?? '').replace(/[&<>"']/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const h = (html) => { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstChild; };

  // the Books page is this app one directory down (books/index.html, written by build.py)
  const PAGE = document.body.dataset.page || 'main';
  const BASE = document.body.dataset.base || '';

  $(`.menu a[data-page="${PAGE}"]`)?.classList.add('here');

  let D;
  try {
    D = await (await fetch(BASE + 'data.json' + (document.body.dataset.version ? '?v=' + document.body.dataset.version : ''))).json();
  } catch (e) {
    $('#byline').textContent = 'The library data could not be loaded.';
    return;
  }

  // ------------------------------------------------------------------ indices

  const decls = D.decls;
  const byName = new Map(decls.map((d, i) => [d.n, i]));
  const DEF_KINDS = new Set(['def', 'abbrev', 'opaque', 'structure', 'class', 'inductive']);
  const isDef = d => DEF_KINDS.has(d.k);
  const isSupport = d => d.role === 'support';
  const overviewOf = r => r.overview ?? r.decls[0];
  const short = n => n.startsWith('NLAlib.') ? n.slice(7) : n;
  const topicById = new Map(D.topics.map(t => [t.id, t]));
  const subById = new Map(D.topics.flatMap(t => t.subs.map(s => [s.id, s])));

  // what each module lists on the main page: its results and definitions, in source order
  const moduleEntries = new Map();
  const moduleLemmas = new Map();
  for (const name of Object.keys(D.modules)) { moduleEntries.set(name, []); moduleLemmas.set(name, []); }
  const seenResult = new Set();
  decls.forEach((d, i) => {
    const list = moduleEntries.get(d.m);
    if (!list) return;
    if (d.r.length) {
      for (const rid of d.r) {
        if (!seenResult.has(rid) && D.results[rid].module === d.m) {
          seenResult.add(rid);
          list.push({ type: 'r', rid, line: d.l });
        }
      }
    } else if (isDef(d) && !isSupport(d)) {
      list.push({ type: 'd', i, line: d.l });
    } else {
      moduleLemmas.get(d.m).push(i);
    }
  });

  const resultTitle = rid => D.results[rid]?.title ?? rid;
  // a graph box is SVG text, so a title's maths is written out plainly: `$\chi^2$` is χ²
  const GREEK = { alpha: 'α', beta: 'β', gamma: 'γ', delta: 'δ', epsilon: 'ε', varepsilon: 'ε',
    theta: 'θ', Theta: 'Θ', kappa: 'κ', lambda: 'λ', mu: 'μ', sigma: 'σ', Sigma: 'Σ', chi: 'χ',
    psi: 'ψ', phi: 'φ', Phi: 'Φ', pi: 'π', omega: 'ω', sin: 'sin ', cos: 'cos ', log: 'log ', det: 'det ', tr: 'tr ',
    cdot: '·', Var: 'Var', operatorname: '' };
  const SUP = { 0: '⁰', 1: '¹', 2: '²', 3: '³', 4: '⁴', '+': '⁺', '-': '⁻', '*': '*', T: 'ᵀ', H: 'ᴴ' };
  const plainTex = t => t.replace(/\$([^$]*)\$/g, (_, m) => m
    .replace(/\\(?:mathbf|mathsf|mathrm|mathbb|operatorname|boldsymbol)\{([^{}]*)\}/g, '$1')
    .replace(/\\\|/g, '‖').replace(/\\([a-zA-Z]+)\s*/g, (c, w) => GREEK[w] ?? '')
    .replace(/\^\{?([0-9+\-*TH])\}?/g, (c, x) => SUP[x]).replace(/_\{?([^{}\s]+)\}?/g, (c, x) => x.replace(/\d/g, n => '₀₁₂₃₄₅₆₇₈₉'[n]))
    .replace(/[{}]/g, '').replace(/\s+/g, ' ').trim());
  // the statement rows of the result on screen, by declaration: the graph's 'm:' nodes
  let memberRows = { rid: null, rows: new Map() };
  const nodeLabel = key => {
    if (key.startsWith('r:')) return plainTex(resultTitle(key.slice(2))).replace(/`/g, '');
    if (key.startsWith('m:')) {
      const row = memberRows.rows.get(+key.slice(2));
      return row ? plainTex(row.l + (row.s ? ' · ' + row.s : '')).replace(/`/g, '') : short(decls[+key.slice(2)].n);
    }
    if (key.startsWith('d:')) return short(key.slice(2));
    return short(decls[+key.slice(2)].n);
  };
  const nodeRoute = key => {
    if (key.startsWith('r:')) return '#r/' + encodeURIComponent(key.slice(2));
    if (key.startsWith('m:')) return rowRoute(memberRows.rid, +key.slice(2));
    if (key.startsWith('d:')) return '#d/' + encodeURIComponent(key.slice(2));
    return '#d/' + encodeURIComponent(decls[+key.slice(2)].n);
  };
  const declRoute = i => '#d/' + encodeURIComponent(decls[i].n);
  // a result page with one statement of its table selected
  const rowRoute = (rid, i) => '#r/' + encodeURIComponent(rid) + '?s=' + encodeURIComponent(decls[i].n);
  const sourceUrl = (i) => {
    const d = decls[i];
    const path = D.modules[d.m]?.path;
    return `${D.repo}/blob/${D.ref}/${path}#L${d.l}-L${d.e}`;
  };

  // ------------------------------------------------------------------ markdown and maths

  function tex(src, display) {
    try {
      return katex.renderToString(normalizeProbability(src), { displayMode: display, throwOnError: false, output: 'html' });
    } catch (e) {
      return `<code>${esc(src)}</code>`;
    }
  }

  const typeset = src => {
    try {
      return katex.renderToString(normalizeProbability(src), { throwOnError: true, strict: 'ignore', output: 'html' });
    } catch (e) {
      return null;   // not valid TeX after all
    }
  };

  // A backticked span: a library name is a link, in code type even in a statement; informal
  // mathematics is typeset (math.js). In a statement (`lenient`) other Lean is typeset too, its
  // names upright; elsewhere Lean stays code.
  function codeSpan(text, lenient, bold) {
    const t = text.trim();
    const file = /^(NLAlib\/\S+)\.lean$/.exec(t);
    if (file && D.modules[file[1].replace(/\//g, '.')]) {
      return `<a href="#m/${encodeURIComponent(file[1].replace(/\//g, '.'))}"><code>${esc(t)}</code></a>`;
    }
    if (/^(docs|scripts)\/\S+\.(md|py|lean)$/.test(t)) {
      return `<a href="${D.repo}/blob/${D.ref}/${esc(t)}" target="_blank" rel="noopener"><code>${esc(t)}</code></a>`;
    }
    const i = byName.get(t) ?? byName.get('NLAlib.' + t);
    if (i !== undefined) {
      return `<a href="${declRoute(i)}"><code>${esc(t)}</code></a>`;
    }
    const src = codeToTex(text, lenient, bold);
    return (src !== null && typeset(src)) || `<code>${esc(text)}</code>`;
  }

  function inline(src, lenient, bold) {
    const slots = [];
    const short = [];       // whether each kept span is short enough never to need a break inside
    const keep = (html, len = 99) => { short.push(len <= 30); return `\u0000${slots.push(html) - 1}\u0000`; };
    let s = src.replace(/(`+)([\s\S]*?[^`])\1(?!`)|\$\$([\s\S]+?)\$\$|\$([^$\n]+?)\$/g,
      (m, ticks, code, display, math) =>
        code !== undefined ? keep(codeSpan(code, lenient, bold), code.length) :
        display !== undefined ? keep(tex(display, true)) : keep(tex(math, false), math.length));
    s = esc(s)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/(^|[^*\w])\*([^*\s](?:[^*]*[^*\s])?)\*(?!\*)/g, '$1<em>$2</em>')
      .replace(/\[([^\]]+)\]\((https?:[^)\s]+|(?![a-z][a-z0-9+.-]*:|\/\/)[\w.\/#-]+)\)/gi, '<a href="$2">$1</a>')
      .replace(/\[([A-Z][A-Za-z]+\d{4}[a-z]?)((?:,[^\]]*)?)\]/g, (m, key, rest) => {
        const b = D.bib[key];
        if (!b) return m;
        const label = esc(key) + rest;
        const title = esc(b.text);
        return b.url ? `<a class="cite" href="${esc(b.url)}" title="${title}">[${label}]</a>`
                     : `<span class="cite" title="${title}">[${label}]</span>`;
      });
    // punctuation after a short formula stays on its line: `… as m,` never breaks before the comma
    return s.replace(/\u0000(\d+)\u0000([.,;:!?)]*)/g, (m, k, punct) =>
      punct && short[+k] ? `<span class="nowrap">${slots[+k]}${punct}</span>` : slots[+k] + punct);
  }

  function md(src, opts = {}) {
    if (!src) return '';
    const inl = t => inline(t, opts.lenient, opts.bold);
    if (opts.inline) return inl(src);
    const out = [];
    const blocks = src.replace(/\r/g, '').split(/\n\s*\n/);
    for (const block of blocks) {
      const lines = block.split('\n');
      const head = /^(#{1,6})\s+(.*)$/.exec(lines[0]);
      if (head) {
        const lvl = Math.min(6, head[1].length + 2);
        out.push(`<h${lvl}>${inl(head[2])}</h${lvl}>`);
        lines.shift();
        if (!lines.length) continue;
      }
      if (/^\s*[*-]\s+/.test(lines[0])) {
        const items = [];
        for (const line of lines) {
          if (/^\s*[*-]\s+/.test(line)) items.push(line.replace(/^\s*[*-]\s+/, ''));
          else if (items.length) items[items.length - 1] += ' ' + line.trim();
        }
        out.push('<ul>' + items.map(t => `<li>${inl(t)}</li>`).join('') + '</ul>');
      } else if (/^```/.test(lines[0])) {
        out.push(`<pre class="lean">${esc(lines.filter(l => !/^```/.test(l)).join('\n'))}</pre>`);
      } else {
        out.push(`<p>${inl(lines.join(' '))}</p>`);
      }
    }
    return out.join('');
  }

  // the `Result:` line and the port provenance (CONTRIBUTING §6, items 3 and 4) are for maintainers
  const boldOf = i => new Set(decls[i].bv);
  const stmtHtml = (i, inline) => md(decls[i].stmt, { lenient: true, bold: boldOf(i), inline });
  const descHtml = i => md(decls[i].fs, { inline: true, bold: boldOf(i) });

  const stripResult = doc => (doc || '').replace(/^\s*Result:.*$/m, '')
    .replace(/^[ \t]*Asymptotic:[ \t]*(?:[^\n]+|\n[ \t]*[\w.]+)[ \t]*$/gm, '')
    .replace(/\s*Port(?:ed)? (?:of|from) `[^`]+`(?:`[^`]*`|[^`.])*\./g, '').trimEnd();

  // ------------------------------------------------------------------ Lean with links

  const KEYWORDS = new Set(['theorem', 'lemma', 'def', 'abbrev', 'structure', 'class', 'instance',
    'inductive', 'where', 'fun', 'let', 'have', 'show', 'by', 'noncomputable', 'protected',
    'Type', 'Prop', 'Sort', 'extends', 'opaque', 'axiom', 'if', 'then', 'else', 'match', 'with']);

  function resolve(tok, allowed) {
    const exact = byName.get(tok) ?? byName.get('NLAlib.' + tok);
    if (exact !== undefined) return exact;
    // dot notation on a variable (`hA.eigenvalue_le`): match the field among the deps
    const tail = /^[a-zα-ω]/.test(tok) && tok.includes('.') ? tok.slice(tok.indexOf('.') + 1) : null;
    for (const cand of [tok, tail]) {
      if (!cand) continue;
      let hit = null;
      for (const j of allowed) {
        if (decls[j].n.endsWith('.' + cand)) {
          if (hit !== null) return null;
          hit = j;
        }
      }
      if (hit !== null) return hit;
    }
    return null;
  }

  function leanHtml(text, self) {
    const allowed = self === undefined ? [] : decls[self].td;
    const re = /(--[^\n]*)|([\p{L}_][\p{L}\p{N}_'!?.₀-₉ₐ-ₜᵢ-ᵪ]*)|([\s\S])/gu;
    let out = '';
    for (const m of text.matchAll(re)) {
      if (m[1]) { out += `<span class="cmt">${esc(m[1])}</span>`; continue; }
      if (m[3] !== undefined) { out += esc(m[3]); continue; }
      let tok = m[2], trail = '';
      while (tok.endsWith('.')) { tok = tok.slice(0, -1); trail += '.'; }
      if (KEYWORDS.has(tok)) { out += `<span class="kw">${tok}</span>${trail}`; continue; }
      const j = resolve(tok, allowed);
      out += (j !== null && j !== self) ? `<a href="${declRoute(j)}">${esc(tok)}</a>${trail}` : esc(tok) + trail;
    }
    return out;
  }

  // ------------------------------------------------------------------ the catalogue

  const kindLabel = d => d.k === 'abbrev' || d.k === 'opaque' ? 'def' : d.k;
  const wip = d => d.s ? '<span class="wip">proof in progress</span>' : '';

  function entryHtml(e) {
    if (e.type === 'r') {
      const r = D.results[e.rid];
      const anyWip = r.decls.some(j => decls[j].s);
      return `<li><a class="entry-title" href="#r/${encodeURIComponent(e.rid)}">${md(r.title, { inline: true })}</a>` +
        (anyWip ? '<span class="wip">proof in progress</span>' : '') +
        `<span class="desc">${descHtml(overviewOf(r))}</span></li>`;
    }
    const d = decls[e.i];
    return `<li><a class="entry-title" href="${declRoute(e.i)}"><code>${esc(short(d.n))}</code></a>` +
      `<span class="kind">${kindLabel(d)}</span>${wip(d)}` +
      (d.fs ? `<span class="desc">${descHtml(e.i)}</span>` : '') + '</li>';
  }

  const rateFilters = {};
  const RATES = D.rates || { entries: [], families: [], guarantees: [], groups: [], norate: [] };
  const RATE_FACETS = [
    ['family', 'Family'], ['algorithm', 'Algorithm'], ['measure', 'Error measure'], ['stat_key', 'Statistic'],
    ['law', 'Law'], ['output', 'Output'], ['regime', 'Regime'], ['resource', 'Resource'], ['form', 'Form'],
    ['source', 'Source'], ['status', 'Status']];
  const RATE_COLUMN_TITLES = { law: 'Law', output: 'Output', regime: 'Regime', detail: 'Detail' };
  const openRates = new Set();
  const RATE_GENERATED = { algorithm: 1, measure: 1, stat_key: 1, law: 1, output: 1, regime: 1, form: 1 };
  const rateWordCache = new Map();

  // Topics and subtopics are <details>, closed at first; which are open survives a search.
  const openSections = new Set();

  function counts(modules) {
    let r = 0, d = 0;
    for (const m of modules) for (const e of moduleEntries.get(m)) e.type === 'r' ? r++ : d++;
    return [r && `${r} result${r > 1 ? 's' : ''}`, d && `${d} definition${d > 1 ? 's' : ''}`].filter(Boolean).join(', ');
  }

  function section(id, cls, heading, title, n, body) {
    return `<details class="${cls}" id="${esc(id)}"${openSections.has(id) ? ' open' : ''}>` +
      `<summary><${heading}>${esc(title)}<span class="n">${n}</span></${heading}></summary>${body}</details>`;
  }

  function moduleHtml(m) {
    const mod = D.modules[m];
    const entries = moduleEntries.get(m).slice().sort((a, b) => a.line - b.line);
    const nl = moduleLemmas.get(m).length;
    return `<div class="module"><a class="mtitle" href="#m/${encodeURIComponent(m)}">${md(mod.title, { inline: true })}</a>` +
      `<span class="count">${nl ? `<a href="#m/${encodeURIComponent(m)}">+${nl} supporting declaration${nl > 1 ? 's' : ''}</a>` : ''}</span></div>` +
      (entries.length ? `<ul class="entries">${entries.map(entryHtml).join('')}</ul>` : '');
  }

  // The shelves (task topics, in topics.toml order) come first; the remaining source folders sit
  // in a collapsed source browser below them.
  function renderCatalogue() {
    const shelves = D.shelves || [];
    const html = t => {
      const flat = t.subs.length === 1 && t.subs[0].title === t.title;
      const collection = (D.collections || []).find(c => c.topic === t.id);
      const sourceBody = t.subs.map(s => section(`s-${s.id}`, 'sub', 'h3', s.title, counts(s.modules), s.modules.map(moduleHtml).join(''))).join('');
      const collectionBody = collection ? (collection.description ? `<p class="topic-blurb">${md(collection.description, { inline: true })}</p>` : '') + collection.groups.map(g => section(`collection-${collection.id}-${g.id}`, 'sub', 'h3', g.title, '', `<ul class="entries">${g.entries.filter(e => e.type === 'r' ? D.results[e.rid] : decls[e.i]).map(entryHtml).join('')}</ul>`)).join('') + (!sourceBody ? '' : collection.modules === 'inline' ? sourceBody : `<details class="source-modules" id="source-modules-${esc(collection.id)}"${openSections.has(`source-modules-${collection.id}`) ? ' open' : ''}><summary>Browse source modules</summary>${sourceBody}</details>`) : '';
      const body = collection ? collectionBody : (t.blurb ? `<p class="topic-blurb">${md(t.blurb, { inline: true })}</p>` : '') +
        t.subs.map(s => {
          const inner = (s.blurb ? `<p class="sub-blurb">${md(s.blurb, { inline: true })}</p>` : '') +
            s.modules.map(moduleHtml).join('');
          return flat ? inner : section(`s-${s.id}`, 'sub', 'h3', s.title, counts(s.modules), inner);
        }).join('');
      const unique = collection && collection.modules !== 'inline' && new Set(collection.groups.flatMap(g => g.entries.map(e => e.type === 'r' ? 'r:' + e.rid : 'd:' + e.i)));
      const total = unique ? `${unique.size} entries` : counts(t.subs.flatMap(s => s.modules));
      return section(`t-${t.id}`, 'topic', 'h2', t.title, total, body);
    };
    const shelved = shelves.map(id => topicById.get(id)).filter(Boolean);
    const folders = D.topics.filter(t => !shelves.includes(t.id));
    $('#content').innerHTML = shelved.map(html).join('') + (!shelved.length ? folders.map(html).join('') : !folders.length ? '' :
      `<details class="source-modules source-browser" id="source-browser"${openSections.has('source-browser') ? ' open' : ''}><summary>Browse the other source folders</summary>` +
      `<p class="topic-blurb">The library's folders follow its import layers; the shelves above group the same results by task. Folders that are shelves are browsable inside their shelf.</p>${folders.map(html).join('')}</details>`);
  }

  $('#content').addEventListener('toggle', ev => {
    const d = ev.target;
    if (d.tagName === 'DETAILS' && d.id) d.open ? openSections.add(d.id) : openSections.delete(d.id);
  }, true);

  // links to a topic or subtopic (in the panel's breadcrumbs) open it and its parent, then scroll
  document.addEventListener('click', ev => {
    const a = ev.target.closest('[data-scroll]');
    if (!a) return;
    ev.preventDefault();
    if ($('#q').value) { $('#q').value = ''; runSearch(); }
    const target = document.getElementById(a.dataset.scroll);
    if (!target) { location.href = BASE || './'; return; }
    for (let d = target; d; d = d.parentElement?.closest('details')) d.open = true;
    if (window.matchMedia('(max-width: 1000px)').matches) closePanel();
    target?.scrollIntoView({ behavior: 'smooth' });
  });

  const nResults = Object.keys(D.results).length;
  const nDefs = decls.filter(isDef).length;
  const commit = D.commit ? `<a href="${D.repo}/tree/${D.commit}"><code>${D.commit.slice(0, 7)}</code></a>` : 'a local build';
  if (PAGE === 'rates') {
    initRates();
  } else if (PAGE === 'books') {
    renderBooks();
  } else {
    $('#byline').innerHTML = `${nResults} named results, ${nDefs} definitions and ${decls.length} declarations, ` +
      `from NLAlib at ${commit}${D.date ? ', ' + esc(D.date.slice(0, 10)) : ''}.`;
    renderCatalogue();
  }

  // ------------------------------------------------------------------ Rates comparisons

  // Rows are generated from every asymptotic pair of the library (build.py, rates_page); a
  // reviewed row carries its curated summary, a pending one its asymptotic statement. One table
  // per family, grouped by guarantee, in the look of a result page's statements table.

  // the facet values of a row, as strings; a family's own `filters` read the row's fields
  function rateValues(e, field) {
    const c = e.c || {};
    const v = field === 'family' ? e.family : field === 'status' ? e.status : field === 'resource' ? c.resources
      : field === 'source' ? c.sources : field in RATE_GENERATED ? c[field] : e[field];
    return v === undefined || v === null || v === '' ? [] : [].concat(v).map(String);
  }

  function rateMatches(e, field, want) {
    if (!want) return true;
    if (field === 'law' && want.startsWith('class:')) return e.c?.law_class === want.slice(6);
    return rateValues(e, field).includes(want);
  }

  function capital(s) { return s.charAt(0).toUpperCase() + s.slice(1); }
  function rateOptionLabel(field, v) {
    if (field === 'family') return RATES.families.find(f => f.id === v)?.title ?? v;
    if (field === 'algorithm') return RATES.algorithms?.[v] ?? v;
    if (field === 'stat_key') return RATES.statistics?.[v] ?? v;
    if (field === 'status') return { reviewed: 'Reviewed', pending: 'Pending review' }[v] ?? v;
    if (field === 'form') return { rate: 'Asymptotic rate', exact: 'Exact value' }[v] ?? v;
    return capital(v);
  }

  function rateOrder(field) {
    if (field === 'family') return RATES.families.map(f => f.id);
    if (field === 'algorithm') return RATES.families.flatMap(f => f.algorithms || []);
    if (field === 'stat_key') return Object.keys(RATES.statistics || {});
    if (field === 'resource') return RATES.resourceKinds || [];
    if (field === 'output') return ['plain', 'late-truncated', 'early-truncated'];
    if (field === 'regime') return ['gapless', 'gapped'];
    if (field === 'status') return ['reviewed', 'pending'];
    if (field === 'form') return ['rate', 'exact'];
    if (field === 'law') return (RATES.lawClasses || []).flatMap(([, laws]) => laws);
    return [];
  }

  function rateFields() {
    const family = RATES.families.find(f => f.id === rateFilters.family);
    return [...RATE_FACETS, ...(family?.filters || []).map(f => [f.field, f.label || f.field, f.order])];
  }

  function syncRateQuery() {
    const q = new URLSearchParams(Object.entries(rateFilters).filter(([, v]) => v));
    if ($('#q').value.trim()) q.set('q', $('#q').value.trim());
    const s = q.toString();
    history.replaceState(null, '', location.pathname + (s ? '?' + s : '') + location.hash);
  }

  function initRates() {
    document.title = 'NLA-lib Rates';
    $('h1').textContent = 'NLA-lib Rates';
    $('#intro').hidden = false;
    $('#intro').textContent = 'Compare the resources each algorithm needs for a target accuracy. Rows are generated ' +
      'from the library’s asymptotic theorems: reviewed rows carry a summary, pending rows the theorem as stated. ' +
      'An algorithm opens its statement on the result page; ▸ expands the statement here.';
    $('#q').placeholder = 'Search rates, algorithms, laws and guarantees';
    $('#q').setAttribute('aria-label', 'Search rates');
    $('#byline').innerHTML = `From NLAlib at ${commit}${D.date ? ', ' + esc(D.date.slice(0, 10)) : ''}.`;
    $('#searchbar').append(h('<div class="rate-filters" aria-label="Filter rates"></div>'));
    // filter state lives in the query string, so a comparison can be linked
    const params = new URLSearchParams(location.search);
    for (const [k, v] of params) if (k === 'q') $('#q').value = v; else rateFilters[k] = v;
    $('#content').addEventListener('click', rateClick);
    renderRates();
  }

  function renderRateFilters() {
    const box = $('.rate-filters');
    if (!box) return;
    const fields = rateFields();
    const allowed = new Set(fields.map(f => f[0]));
    for (const k of Object.keys(rateFilters)) if (!allowed.has(k) || !rateFilters[k]) delete rateFilters[k];
    box.replaceChildren();
    for (const [field, title, configured] of fields) {
      // the bounds without a rate form count too: "RSVD, spectral norm" is a choice with no rate yet
      const compatible = [...RATES.entries, ...(RATES.norate || [])].filter(e => fields.every(([o]) => o === field || rateMatches(e, o, rateFilters[o])));
      const values = [...new Set(compatible.flatMap(e => rateValues(e, field)))];
      const order = configured || rateOrder(field);
      const rank = v => { const i = order.indexOf(v); return i < 0 ? order.length : i; };
      values.sort((a, b) => rank(a) - rank(b) || a.localeCompare(b));
      const want = rateFilters[field];
      if (want && !values.includes(want) && !(field === 'law' && want.startsWith('class:'))) delete rateFilters[field];
      if (values.length < 2 && !rateFilters[field]) continue;
      const opt = v => `<option value="${esc(v)}"${rateFilters[field] === v ? ' selected' : ''}>${esc(rateOptionLabel(field, v))}</option>`;
      let options = values.map(opt).join('');
      if (field === 'law') {
        // laws by sketch class, as on the Sketching page; a class with several laws can be chosen whole
        const classOf = v => compatible.find(e => e.c?.law === v)?.c.law_class || 'Other';
        options = (RATES.lawClasses || [['Other', []]]).map(([cls]) => {
          const vs = values.filter(v => classOf(v) === cls);
          if (!vs.length) return '';
          const whole = `class:${cls}`;
          return `<optgroup label="${esc(cls)}">${vs.length > 1 ? `<option value="${esc(whole)}"${rateFilters.law === whole ? ' selected' : ''}>All ${esc(cls)} laws</option>` : ''}${vs.map(opt).join('')}</optgroup>`;
        }).join('');
      }
      const label = h(`<label>${esc(title)}<select data-field="${esc(field)}" aria-label="${esc(title)}"><option value="">All${field === 'family' ? ' families' : ''}</option>${options}</select></label>`);
      $('select', label).addEventListener('change', ev => {
        rateFilters[field] = ev.target.value;
        if (field === 'family') {
          // a family's own filters do not carry over to another family
          const own = new Set(RATE_FACETS.map(f => f[0]));
          for (const k of Object.keys(rateFilters)) if (!own.has(k)) delete rateFilters[k];
        }
        syncRateQuery();
        renderRates();
        [...document.querySelectorAll('.rate-filters select')].find(s => s.dataset.field === field)?.focus();
      });
      box.append(label);
    }
  }

  function rateSearchWords(text) {
    return String(text || '').replace(/\\(?:varepsilon|epsilon)\b/g, ' epsilon ')
      .replace(/[εϵ]/g, ' epsilon ').replace(/[δ]/g, ' delta ')
      .replace(/\\(?:mathbf|mathsf|mathrm|mathbb|operatorname|text|left|right|frac|sqrt)\b/g, ' ')
      .toLowerCase().match(/[\p{L}\p{N}]+/gu) || [];
  }

  function rateWords(e) {
    if (!rateWordCache.has(e)) {
      const family = RATES.families.find(f => f.id === e.family);
      const guarantee = RATES.guarantees.find(g => g.id === e.group);
      const group = RATES.groups.find(g => g.id === e.group);
      const c = e.c || {};
      const d = decls[e.overview];
      rateWordCache.set(e, rateSearchWords([family?.title, guarantee?.title, guarantee?.description, group?.title,
        c.algorithm, RATES.algorithms?.[c.algorithm], c.measure, c.law, c.output, c.regime, c.detail, c.source,
        ...(c.sources || []), e.label, ...(family?.filters || []).map(f => e[f.field]),
        ...(e.resources || []).flatMap(r => [r.label, r.bound, r.kind]), e.notes, short(d.n), d.nm,
        e.status === 'pending' ? 'pending ' + (d.stmt || '') : ''].join(' ')));
    }
    return rateWordCache.get(e);
  }

  function resetRates() {
    $('#q').value = '';
    for (const k of Object.keys(rateFilters)) delete rateFilters[k];
    syncRateQuery();
    renderRates();
  }

  // the result page with this row selected; an exact theorem without a Result id is its own page
  function rateRoute(e, i = e.overview) { return e.result ? rowRoute(e.result, i) : declRoute(i); }

  function rateColumns(f, rows) {
    // a plain output is no information where no row is truncated
    const value = (e, k) => (k === 'output' && e.c?.output === 'plain' ? '' : e.c?.[k] ?? '');
    const vary = k => new Set(rows.map(e => value(e, k))).size > 1;
    return [{ k: 'algorithm', t: f.subject_label || 'Algorithm' },
      ...['law', 'output', 'regime', 'detail'].filter(k => vary(k) || (k === 'detail' && rows.some(e => e.c?.detail)))
        .map(k => ({ k, t: RATE_COLUMN_TITLES[k] })),
      { k: 'stat', t: 'Statistic' }, { k: 'resources', t: f.resources_label || 'Resources' }, { k: 'source', t: 'Source' }];
  }

  function rateCell(e, k) {
    const c = e.c || {};
    if (k === 'algorithm') {
      const name = c.algorithm || short(decls[e.overview].n);
      const long = RATES.algorithms?.[c.algorithm];
      return `<a href="${BASE}${rateRoute(e)}" title="${esc((long ? long + ': ' : '') + 'open this statement on its result page')}">${esc(name)}</a>`;
    }
    if (k === 'resources') {
      if (e.status === 'pending') {
        return '<span class="pending-tag">pending review</span>' +
          `<div class="rate-pending-statement">${statementHtml(null, e.overview)}</div>`;
      }
      const notes = Array.isArray(e.notes) ? e.notes.join(' ') : e.notes;
      return (e.resources || []).map(r => `<div class="rate-resource"><span class="rate-res-label">${md(r.label, { inline: true })}:</span> ${md(r.bound, { inline: true })}</div>`).join('') +
        (notes ? `<p class="rate-caveat"><strong>${e.kind === 'exact' ? 'Hypotheses' : 'Parameters'}:</strong> ${md(notes, { inline: true })}</p>` : '');
    }
    return c[k] ? md(c[k], { inline: true }) : '';
  }

  function rateRowHtml(e, cols) {
    const open = openRates.has(e.id);
    return `<tr class="rate-row${e.status === 'pending' ? ' pending' : ''}${open ? ' on' : ''}" id="rate-row-${esc(e.id)}" data-rate="${esc(e.id)}">` +
      `<td class="pick"><button type="button" class="rate-toggle" aria-expanded="${open}" aria-controls="rate-detail-${esc(e.id)}" title="Show the theorem here">${open ? '▾' : '▸'}<span class="sr"> Show the theorem</span></button></td>` +
      cols.map(c => `<td class="c-${c.k}" data-label="${esc(c.t)}">${rateCell(e, c.k)}</td>`).join('') + '</tr>' +
      `<tr class="rate-theorem" id="rate-detail-${esc(e.id)}" data-rate="${esc(e.id)}"${open ? '' : ' hidden'}><td colspan="${cols.length + 1}"><div class="rate-expanded"></div></td></tr>`;
  }

  function definitionLink(i, label) {
    return Number.isInteger(i) && decls[i] ? `<a href="${BASE}${declRoute(i)}">${esc(label)}</a>` : '';
  }

  function rateGroupHtml(f, title, cols, rows, g) {
    const span = cols.length + 1;
    let head = `<span class="rate-group-title">${md(title, { inline: true })}</span>`;
    if (g && !g.pending) {
      const groupId = `rate-guarantee-${f.id}-${g.id}`;
      head += `<details class="rate-definitions" id="${esc(groupId)}"${openSections.has(groupId) ? ' open' : ''}><summary>Guarantee and definitions</summary>` +
        `<div class="guarantee-description">${md(g.description)}</div>${(g.definitions || []).map(d =>
          `<h4>${definitionLink(d.i, d.label || d.declaration)}</h4>${statementHtml(null, d.i)}`).join('')}</details>`;
    } else {
      head += ' <span class="pending-tag">generated, pending review</span>';
    }
    return `<tr class="rate-group"><th colspan="${span}" scope="colgroup">${head}</th></tr>` + rows.map(e => rateRowHtml(e, cols)).join('');
  }

  // explicit bounds of the family's algorithms with no asymptotic form: no rate to compare yet
  function norateFor(f, query) {
    const own = new Set(['family', 'algorithm', 'measure', 'stat_key', 'law', 'output', 'regime', 'source']);
    if (Object.entries(rateFilters).some(([k, v]) => v && !own.has(k))) return [];
    return (RATES.norate || []).filter(x => x.family === f.id &&
      Object.entries(rateFilters).every(([k, v]) => k === 'family' ? !v || v === f.id : rateMatches(x, k, v)) &&
      (!query.length || (() => {
        const d = decls[x.i];
        const words = rateSearchWords([...Object.values(x.c).flat(), RATES.algorithms?.[x.c.algorithm], short(d.n), d.nm].join(' '));
        return query.every(q => words.some(w => w.includes(q)));
      })()));
  }

  function norateHtml(f, list, open) {
    if (!list.length) return '';
    const id = `rate-norate-${f.id}`;
    const cells = new Map();
    for (const x of list) {
      const key = [x.c.algorithm, x.c.measure, x.c.stat].join('|');
      if (!cells.has(key)) cells.set(key, []);
      cells.get(key).push(x);
    }
    const link = x => {
      const c = x.c;
      const text = [c.law, c.output && c.output !== 'plain' ? c.output : null, c.regime, c.detail, c.source].filter(Boolean).join(' · ') || short(decls[x.i].n);
      return `<a href="${BASE}${rowRoute(x.result, x.i)}">${md(text, { inline: true })}</a>`;
    };
    return `<details class="rate-norate" id="${esc(id)}"${open || openSections.has(id) ? ' open' : ''}><summary>Bounds without a rate form <span class="rate-norate-n">(${list.length})</span></summary>` +
      '<p class="rate-norate-intro">Explicit bounds of these algorithms that have no asymptotic form in the library yet, so no resource to compare. Each link opens the statement on its result page.</p>' +
      '<ul>' + [...cells.values()].map(xs => `<li><span class="rate-norate-cell"><strong>${esc(xs[0].c.algorithm)}</strong>` +
        `${xs[0].c.measure ? ' · ' + esc(xs[0].c.measure) : ''} · ${md(xs[0].c.stat || '', { inline: true })}</span> ` +
        xs.map(link).join('<span class="sep"> · </span>') + '</li>').join('') + '</ul></details>';
  }

  function renderRates() {
    renderRateFilters();
    const query = rateSearchWords($('#q').value);
    const entries = RATES.entries.filter(e => Object.entries(rateFilters).every(([k, v]) => rateMatches(e, k, v)) &&
      query.every(q => rateWords(e).some(w => w.includes(q))));
    const n = s => entries.filter(s).length;
    const parts = [[n(e => e.status === 'reviewed' && e.kind !== 'exact'), 'reviewed rate', 'reviewed rates'],
      [n(e => e.status === 'pending'), 'pending review', 'pending review'], [n(e => e.kind === 'exact'), 'exact value', 'exact values']]
      .filter(([k]) => k).map(([k, one, many]) => `${k} ${k === 1 ? one : many}`);
    const sections = RATES.families.map(f => {
      const all = RATES.entries.filter(e => e.family === f.id);
      const rows = entries.filter(e => e.family === f.id);
      const norate = norateFor(f, query);
      if (!rows.length && !norate.length) return '';
      const cols = rateColumns(f, all);
      const notationId = `rate-notation-${f.id}`;
      const groups = [...RATES.guarantees.filter(g => g.family === f.id), ...RATES.groups.filter(g => g.family === f.id)]
        .map(g => [g, rows.filter(e => e.group === g.id)]).filter(([, rs]) => rs.length);
      const table = rows.length ? `<div class="rate-scroll"><table class="rates-table"><thead><tr><th class="pick" scope="col"><span class="sr">Show the theorem</span></th>` +
        cols.map(c => `<th scope="col" class="c-${c.k}">${esc(c.t)}</th>`).join('') + '</tr></thead><tbody>' +
        groups.map(([g, rs]) => rateGroupHtml(f, g.title, cols, rs, g)).join('') + '</tbody></table></div>' : '';
      return `<section class="rate-family" id="rate-family-${esc(f.id)}"><h2>${esc(f.title)}</h2>${f.description ? `<p class="topic-blurb">${md(f.description, { inline: true })}</p>` : ''}` +
        (f.notation ? `<details class="rate-notation" id="${esc(notationId)}"${openSections.has(notationId) ? ' open' : ''}><summary>Notation and assumptions</summary>${md(f.notation)}</details>` : '') +
        table + norateHtml(f, norate, !rows.length) + '</section>';
    }).join('');
    $('#content').innerHTML = entries.length || sections
      ? `<p class="searchnote">${entries.length ? `${entries.length} row${entries.length === 1 ? '' : 's'}${parts.length ? ': ' + parts.join(', ') : ''}. ` +
        'Resources, exact values and parameter caveats are stated per row; pending rows show the theorem as the library states it.'
        : 'No rate matches these filters; the bounds below have no asymptotic form yet.'}</p>` + sections
      : '<p class="empty">No rates match these filters.</p><button type="button" id="reset-rates">Reset filters and search</button>';
    $('#reset-rates')?.addEventListener('click', resetRates);
    for (const id of openRates) {
      const tr = document.getElementById('rate-detail-' + id);
      if (tr) drawRateDetail(tr);
    }
  }

  function rateById(id) { return RATES.entries.find(e => e.id === id); }

  function drawRateDetail(tr, explicit) {
    const e = rateById(tr.dataset.rate);
    const exact = e.kind === 'exact';
    const paired = !exact && e.explicit !== e.overview;
    // a pending row already shows its asymptotic statement, so it opens on the explicit one
    if (explicit === undefined) explicit = tr.dataset.explicit ? tr.dataset.explicit === '1' : e.status === 'pending' && paired;
    tr.dataset.explicit = explicit ? '1' : '0';
    const i = explicit && paired ? e.explicit : e.overview;
    const f = RATES.families.find(x => x.id === e.family) || {};
    const defs = [definitionLink(e.algorithm_definition_index, e.algorithm_definition_label || f.definition_label || 'Algorithm definition'),
      definitionLink(e.sketch_definition_index, 'Sketch definition')].filter(Boolean);
    const links = exact ? `<a href="${BASE}${declRoute(e.overview)}">Theorem</a>`
      : `<a href="${BASE}${declRoute(e.overview)}">Asymptotic theorem</a> · <a href="${BASE}${declRoute(e.explicit)}">Explicit theorem</a>`;
    $('.rate-expanded', tr).innerHTML = '<div class="rate-detail-bar">' +
      (paired ? `<button type="button" class="rate-explicit${explicit ? ' on' : ''}" aria-pressed="${explicit}">Explicit bound</button>` : '') +
      `<button type="button" class="rate-permalink" data-copy-rate="${esc(e.id)}">Copy link</button><span class="rate-copy-status" role="status"></span></div>` +
      statementHtml(null, i) +
      `<p class="rate-links"><a href="${BASE}${rateRoute(e, i)}">Result page</a> · ${links} · <a href="${sourceUrl(i)}" target="_blank" rel="noopener">Source ↗</a>` +
      (defs.length ? ' · ' + defs.join(' · ') : '') + '</p>' +
      (e.status === 'pending' ? '<p class="rate-pending-note">No reviewed summary yet: the row shows the asymptotic theorem as the library states it, and its cells are read from the declaration’s name.</p>' : '');
  }

  function toggleRate(id, open) {
    const row = document.getElementById('rate-row-' + id);
    const tr = document.getElementById('rate-detail-' + id);
    if (!row || !tr) return false;
    open ??= tr.hidden;
    tr.hidden = !open;
    row.classList.toggle('on', open);
    const b = $('.rate-toggle', row);
    b.setAttribute('aria-expanded', open);
    b.firstChild.textContent = open ? '▾' : '▸';
    if (open) { openRates.add(id); if (!$('.rate-expanded', tr).childNodes.length) drawRateDetail(tr); }
    else openRates.delete(id);
    return true;
  }

  async function rateClick(ev) {
    const copy = ev.target.closest('[data-copy-rate]');
    if (copy) {
      const e = rateById(copy.dataset.copyRate);
      // a pending row is linked by its declaration, which stays valid once it is reviewed
      const key = e.status === 'pending' ? e.theorem : e.id;
      const url = location.origin + location.pathname + '#rate/' + encodeURIComponent(key);
      const status = copy.nextElementSibling;
      try {
        await navigator.clipboard.writeText(url);
        status.textContent = 'Link copied';
      } catch (error) {
        status.innerHTML = `Copy this link: <a href="${esc(url)}">${esc(url)}</a>`;
      }
      return;
    }
    const explicit = ev.target.closest('.rate-explicit');
    if (explicit) {
      const tr = explicit.closest('tr.rate-theorem');
      drawRateDetail(tr, tr.dataset.explicit !== '1');
      $('.rate-explicit', tr)?.focus();
      return;
    }
    const row = ev.target.closest('tr.rate-row');
    if (row && (ev.target.closest('.rate-toggle') || !ev.target.closest('a, button, details, summary, input, select'))) {
      toggleRate(row.dataset.rate);
    }
  }

  // `#rate/<id>` (or `#rate/<declaration>`, the link of a pending row) and `#rate-row-<id>`
  function focusRate(key) {
    const bare = key.replace(/^NLAlib\./, '');
    const e = rateById(key) || RATES.entries.find(x => x.theorem === key || x.theorem.replace(/^NLAlib\./, '') === bare);
    if (!e) return;
    if (!document.getElementById('rate-row-' + e.id)) resetRates();
    toggleRate(e.id, true);
    // below the search bar, which stays at the top of the window
    const row = document.getElementById('rate-row-' + e.id);
    const bar = $('#searchbar');
    if (row) window.scrollTo({ top: row.getBoundingClientRect().top + window.scrollY - (bar && getComputedStyle(bar).position === 'sticky' ? bar.getBoundingClientRect().height : 0) - 12, behavior: 'smooth' });
  }

  // ------------------------------------------------------------------ the Books page

  // For each key book: its chapters, and in each section its numbered results with the library's
  // results and declarations citing them (`[Tropp2015, Theorem 6.1.1]`); those not cited are faint.
  function renderBooks() {
    document.title = 'NLA-lib Book Explorer';
    $('h1').textContent = 'NLA-lib Book Explorer';
    $('#searchbar').hidden = true;
    $('#intro').hidden = false;
    $('#intro').textContent = 'What NLAlib has from key books: every numbered result of each book, with ' +
      'the results of the library that cite it.';
    $('#byline').innerHTML = `From NLAlib at ${commit}${D.date ? ', ' + esc(D.date.slice(0, 10)) : ''}.`;
    const link = t => t.r !== undefined
      ? `<a href="#r/${encodeURIComponent(t.r)}">${md(resultTitle(t.r), { inline: true })}</a>`
      : `<a href="#d/${encodeURIComponent(t.d)}"><code>${esc(short(t.d))}</code></a>`;
    const links = refs => refs.map(link).join(', ');
    const item = it => {
      const has = it.refs.length > 0;
      return `<li class="bkitem${has ? '' : ' missing'}"><span class="bkno">${esc(it.k)} ${esc(it.n)}</span>` +
        (it.name ? ` <span class="entry-title">${esc(it.name)}</span>` : '') +
        `<span class="desc">${has ? (it.same ? `As ${esc(it.same)}: ` : '') + links(it.refs) : 'No library result cites it.'}</span></li>`;
    };
    $('#content').innerHTML = D.books.map(b => {
      const chapters = b.chapters.map(c => {
        const items = c.sections.flatMap(x => x.items);
        const n = items.filter(it => it.refs.length).length;
        const body = (c.refs.length ? `<p class="sub-blurb">Citing the chapter: ${links(c.refs)}</p>` : '') +
          c.sections.filter(x => x.items.length || x.refs.length).map(x =>
            `<div class="module"><span class="mtitle">${esc(x.n)} ${esc(x.title)}</span></div>` +
            '<ul class="entries">' + x.items.map(item).join('') +
            (x.refs.length ? `<li class="bkitem"><span class="bkno">§${esc(x.n)}</span>` +
              `<span class="desc">${links(x.refs)}</span></li>` : '') + '</ul>').join('');
        return section(`b-${b.key}-${c.n}`, 'sub', 'h3', `${c.n}. ${c.title}`,
          items.length ? `${n} of ${items.length}` : '', body);
      }).join('');
      // a book is collapsed like a topic, its count the numbered results the library cites
      return section(`b-${b.key}`, 'topic', 'h2', b.short, `${b.covered} of ${b.items} cited`,
        `<p class="topic-blurb">${esc(b.cite ?? b.key)}${b.url ? ` <a href="${esc(b.url)}" target="_blank" rel="noopener">link</a>` : ''}` +
        (b.general.length ? ` Cited as a whole by ${links(b.general)}.` : '') + '</p>' + chapters);
    }).join('');
  }

  // ------------------------------------------------------------------ search

  const STOP = new Set(('a an and are as at be by for from if in into is it its of on or that the then ' +
    'there this to with any every all each where which when its their than').split(' '));
  const stem = w => w.length > 4 && w.endsWith('ies') ? w.slice(0, -3) + 'y'
    : w.length > 3 && w.endsWith('s') && !w.endsWith('ss') ? w.slice(0, -1) : w;
  // LaTeX formatting commands are not words (`\mathbf{A}` is `A`); \lambda, \sigma, \det, … stay
  const LATEX_FORMAT = /\\(?:mathbf|mathsf|mathbb|mathrm|mathcal|boldsymbol|operatorname|text|left|right|big|Big|bigg|Bigg|begin|end|lvert|rvert|lVert|rVert|langle|rangle|quad|qquad|cdot|cdots|ldots|dots|le|ge|leq|geq|preceq|succeq|in|to|mapsto|frac|sqrt|sum|prod|int|limits|displaystyle)(?![a-zA-Z])|\{(?:b|p|v)?matrix\}/g;
  const tokenize = text => (text || '')
    .replace(LATEX_FORMAT, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2').replace(/([A-Z]+)([A-Z][a-z])/g, '$1 $2')
    // a theorem number (`8.1`, `10.6`) is one word, so "TW 8.1" finds Theorem 8.1 only
    .toLowerCase().match(/\d+(?:\.\d+)+|[\p{L}\p{N}]+/gu)?.filter(w => !STOP.has(w)).map(stem) ?? [];

  let index = null;
  function buildIndex() {
    const items = [];
    const add = (type, key, fields, prior) => {
      const toks = new Map();
      for (const [text, w] of fields) {
        for (const t of tokenize(text)) toks.set(t, Math.max(toks.get(t) || 0, w));
      }
      items.push({ type, key, toks, prior });
    };
    for (const [rid, r] of Object.entries(D.results)) {
      add('r', rid, [[r.title, 4], [r.aliases.join(' '), 4], [[rid, ...(r.merged || [])].join(' '), 3],
        [r.decls.map(j => short(decls[j].n)).join(' '), 2],
        [r.decls.map(j => stripResult(decls[j].doc)).join(' '), 1],
        [D.modules[r.module]?.title, 0.5]], 1.3);
      // each statement of a table is a hit of its own, found by its label, names and sources
      if ((r.rows || []).length > 1) r.rows.forEach((row, k) => {
        const ids = [...new Set([row.o, row.e])];
        add('s', rid + '|' + k, [[row.x, 4], [plainTex(row.l || ''), 3],
          [ids.map(j => decls[j].nm || '').join(' '), 3], [ids.map(j => short(decls[j].n)).join(' '), 2.5],
          [r.title, 1.5], [ids.map(j => stripResult(decls[j].doc)).join(' '), 1]], 1.3);
      });
    }
    decls.forEach((d, i) => {
      if (d.r.length) return;
      add(isDef(d) ? 'd' : 'l', i, [[short(d.n), isDef(d) ? 4 : 2.5], [stripResult(d.doc), 1],
        [D.modules[d.m]?.title, 0.5]], isDef(d) ? 1.2 : 0.75);
    });
    for (const [m, mod] of Object.entries(D.modules)) {
      add('m', m, [[mod.title, 3], [mod.summary, 1]], 0.9);
    }
    const df = new Map();
    for (const it of items) for (const t of it.toks.keys()) df.set(t, (df.get(t) || 0) + 1);
    const idf = new Map([...df].map(([t, n]) => [t, Math.log(1 + items.length / n)]));
    return { items, idf, vocab: [...df.keys()] };
  }

  const synonyms = Object.entries(D.synonyms || {}).map(([k, v]) => [k.toLowerCase(), [].concat(v)]);

  function search(q) {
    index ??= buildIndex();
    const words = tokenize(q);
    if (!words.length) return [];
    // one group per query word; synonyms of a phrase add alternatives to its words' groups
    const groups = words.map(w => new Set([w]));
    const ql = q.toLowerCase();
    for (const [phrase, exps] of synonyms) {
      if (!ql.includes(phrase)) continue;
      const pw = tokenize(phrase);
      const alts = exps.flatMap(tokenize);
      groups.forEach((g, k) => { if (pw.includes(words[k])) alts.forEach(a => g.add(a)); });
    }
    const matches = groups.map(g => {
      const hits = new Map();
      for (const alt of g) {
        for (const v of index.vocab) {
          const number = /\d\.\d/.test(alt);     // `8.1` is not a prefix of `8.12`
          const qlty = v === alt ? 1 : number ? 0 : (alt.length >= 3 && v.startsWith(alt)) ? 0.75
            : (v.length >= 4 && alt.startsWith(v)) ? 0.5 : 0;
          if (qlty > (hits.get(v) || 0)) hits.set(v, qlty);
        }
      }
      return hits;
    });
    const scored = [];
    for (const it of index.items) {
      let score = 0, covered = 0;
      for (const hits of matches) {
        let best = 0;
        for (const [v, qlty] of hits) {
          const w = it.toks.get(v);
          if (w) best = Math.max(best, w * qlty * index.idf.get(v));
        }
        if (best) { score += best; covered++; }
      }
      if (!covered) continue;
      score *= (covered / matches.length) ** 2 * it.prior;
      scored.push([score, it]);
    }
    scored.sort((a, b) => b[0] - a[0]);
    return scored.slice(0, 60).map(x => x[1]);
  }

  const statementOf = key => {
    const bar = key.lastIndexOf('|');
    const rid = key.slice(0, bar);
    return { rid, row: D.results[rid].rows[+key.slice(bar + 1)] };
  };
  const hitRoute = it => it.type === 'r' ? '#r/' + encodeURIComponent(it.key)
    : it.type === 's' ? (({ rid, row }) => rowRoute(rid, row.o))(statementOf(it.key))
    : it.type === 'm' ? '#m/' + encodeURIComponent(it.key) : declRoute(it.key);

  function hitHtml(it) {
    if (it.type === 's') {
      const { rid, row } = statementOf(it.key);
      return `<li><a class="entry-title" href="${hitRoute(it)}">${md(row.l || decls[row.e].nm || short(decls[row.e].n), { inline: true })}</a>` +
        `<span class="kind">statement</span><span class="desc">${md(D.results[rid].title, { inline: true })}` +
        `${row.s ? ' · ' + md(row.s, { inline: true }) : ''}</span></li>`;
    }
    if (it.type === 'r') {
      const r = D.results[it.key];
      return `<li><a class="entry-title" href="#r/${encodeURIComponent(it.key)}">${md(r.title, { inline: true })}</a>` +
        `<span class="kind">result</span><span class="desc">${descHtml(overviewOf(r))}` +
        ` <em>${md(D.modules[r.module]?.title || '', { inline: true })}</em></span></li>`;
    }
    if (it.type === 'm') {
      const mod = D.modules[it.key];
      return `<li><a class="entry-title" href="#m/${encodeURIComponent(it.key)}">${md(mod.title, { inline: true })}</a>` +
        `<span class="kind">file</span><span class="desc">${md(mod.summary, { inline: true })}</span></li>`;
    }
    const d = decls[it.key];
    return `<li><a class="entry-title" href="${declRoute(it.key)}"><code>${esc(short(d.n))}</code></a>` +
      `<span class="kind">${it.type === 'd' ? kindLabel(d) : 'lemma'}</span>${wip(d)}` +
      `<span class="desc">${descHtml(it.key)} <em>${md(D.modules[d.m]?.title || '', { inline: true })}</em></span></li>`;
  }

  let lastHits = [];
  function runSearch() {
    if (PAGE === 'rates') { renderRates(); return; }
    const q = $('#q').value.trim();
    if (!q) {
      renderCatalogue();
      return;
    }
    lastHits = search(q);
    $('#content').innerHTML = lastHits.length
      ? `<p class="searchnote">${lastHits.length === 60 ? 'Top 60 matches' : lastHits.length + ' matches'}; ` +
        'words are matched against names, docstrings, sources and file titles.</p>' +
        `<ul class="entries">${lastHits.map(hitHtml).join('')}</ul>`
      : '<p class="empty">Nothing matches.</p>';
  }

  let timer = null;
  $('#q').addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(runSearch, 90); });
  $('#q').addEventListener('keydown', ev => {
    if (ev.key === 'Enter' && lastHits.length) {
      location.hash = hitRoute(lastHits[0]);
    } else if (ev.key === 'Escape') {
      $('#q').value = '';
      runSearch();
    }
  });
  document.addEventListener('keydown', ev => {
    if (ev.key === '/' && document.activeElement !== $('#q')) { ev.preventDefault(); $('#q').focus(); }
    if (ev.key === 'Escape' && document.activeElement !== $('#q') && !$('#panel').hidden) closePanel();
  });

  // ------------------------------------------------------------------ dependency graph

  const measure = (() => {
    const ctx = document.createElement('canvas').getContext('2d');
    ctx.font = "13px 'Source Sans 3', sans-serif";
    return s => ctx.measureText(s).width;
  })();

  function fit(label, max) {
    if (measure(label) <= max) return label;
    let s = label;
    while (s.length > 1 && measure(s + '…') > max) s = s.slice(0, -1);
    return s + '…';
  }

  function neighbours(mode) {
    if (mode === 'nodes') {
      // a member of the result on screen is its own node; other declarations are their nodes
      const key = j => memberRows.rows.has(j) ? 'm:' + j
        : decls[j].r.length ? 'r:' + decls[j].r[0] : 'd:' + decls[j].n;
      const member = (k, field) => [...new Set((decls[+k.slice(2)][field] || []).map(key))];
      return { up: k => k.startsWith('m:') ? member(k, 'nu') : D.nodes[k]?.u ?? [],
               down: k => k.startsWith('m:') ? member(k, 'nb') : D.nodes[k]?.b ?? [] };
    }
    return {
      up: k => { const d = decls[+k.slice(2)]; return [...d.td, ...d.vd].map(j => 'i:' + j); },
      down: k => decls[+k.slice(2)].rd.map(j => 'i:' + j),
    };
  }

  function graphSvg(focus, mode, depth, expanded) {
    const { up, down } = neighbours(mode);
    const L1 = [...new Set(up(focus))].filter(k => k !== focus);
    const R1 = [...new Set(down(focus))].filter(k => k !== focus);
    const byLabel = (a, b) => nodeLabel(a).localeCompare(nodeLabel(b));
    L1.sort(byLabel); R1.sort(byLabel);
    const cols = [[focus]];
    const colNames = [''];
    if (L1.length) { cols.unshift(L1); colNames.unshift('uses'); }
    if (R1.length) { cols.push(R1); colNames.push('used by'); }
    if (depth > 1) {
      const near = new Set([focus, ...L1, ...R1]);
      const L2 = [...new Set(L1.flatMap(up))].filter(k => !near.has(k)).sort(byLabel);
      const R2 = [...new Set(R1.flatMap(down))].filter(k => !near.has(k)).sort(byLabel);
      if (L2.length) { cols.unshift(L2); colNames.unshift('uses, 2 steps'); }
      if (R2.length) { cols.push(R2); colNames.push('used by, 2 steps'); }
    }
    const CAP = 14, ROW = 26, BOX = 20, GAP = 46, PADX = 8, MAXW = 210, TOP = 22;
    const shown = cols.map((c, ci) => {
      const key = colNames[ci];
      if (expanded.has(key) || c.length <= CAP) return { nodes: c, more: 0 };
      return { nodes: c.slice(0, CAP - 1), more: c.length - CAP + 1 };
    });
    const widths = shown.map(c => Math.min(MAXW, Math.max(60, ...c.nodes.map(k => measure(nodeLabel(k)) + 2 * PADX))));
    const heights = shown.map(c => (c.nodes.length + (c.more ? 1 : 0)) * ROW);
    const H = Math.max(...heights) + TOP + 6;
    const pos = new Map();
    let x = 8;
    const parts = [];
    shown.forEach((c, ci) => {
      const w = widths[ci];
      const y0 = TOP + (H - TOP - heights[ci]) / 2;
      if (colNames[ci]) parts.push(`<text class="colhead" x="${x}" y="12">${esc(colNames[ci])}</text>`);
      c.nodes.forEach((k, r) => {
        const y = y0 + r * ROW;
        pos.set(k, { x, y, w });
        const label = nodeLabel(k);
        const cls = ['node', k === focus ? 'focus' : '', k.startsWith('d:') ? 'def' : '', k.startsWith('m:') ? 'member' : ''].join(' ');
        parts.push(`<g class="${cls}" data-key="${esc(k)}"><title>${esc(label)}</title>` +
          `<rect x="${x}" y="${y}" width="${w}" height="${BOX}" rx="2"></rect>` +
          `<text x="${x + PADX}" y="${y + 14}">${esc(fit(label, w - 2 * PADX))}</text></g>`);
      });
      if (c.more) {
        const y = y0 + c.nodes.length * ROW;
        parts.push(`<g class="node more" data-expand="${esc(colNames[ci])}"><rect x="${x}" y="${y}" width="${w}" height="${BOX}" rx="2"></rect>` +
          `<text x="${x + PADX}" y="${y + 14}">${c.more} more…</text></g>`);
      }
      x += w + GAP;
    });
    const W = x - GAP + 8;
    const edges = [];
    const edge = (a, b) => {
      const p = pos.get(a), q = pos.get(b);
      if (!p || !q || p.x >= q.x) return;
      const x1 = p.x + p.w, y1 = p.y + BOX / 2, x2 = q.x, y2 = q.y + BOX / 2, mx = (x1 + x2) / 2;
      edges.push(`<path class="edge" data-a="${esc(a)}" data-b="${esc(b)}" d="M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2 - 4},${y2}"></path>` +
        `<path class="edge" data-a="${esc(a)}" data-b="${esc(b)}" d="M${x2 - 4},${y2 - 3} L${x2},${y2} L${x2 - 4},${y2 + 3}"></path>`);
    };
    const colOf = new Map();
    shown.forEach((c, ci) => c.nodes.forEach(k => colOf.set(k, ci)));
    for (const k of pos.keys()) {
      for (const u of up(k)) if (pos.has(u) && colOf.get(u) === colOf.get(k) - 1) edge(u, k);
    }
    return `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${edges.join('')}${parts.join('')}</svg>`;
  }

  function graphSection(focus, modes, state = { mode: modes[0], depth: 1, expanded: new Set() }) {
    if (!modes.includes(state.mode)) state.mode = modes[0];
    const box = h('<div></div>');
    const draw = () => {
      const opts = (modes.length > 1 ? modes.map(m =>
        `<button data-mode="${m}" class="${state.mode === m ? 'on' : ''}">${m === 'nodes' ? 'results and definitions' : 'all declarations'}</button>`).join('') : '') +
        [1, 2].map(n => `<button data-depth="${n}" class="${state.depth === n ? 'on' : ''}">${n} step${n > 1 ? 's' : ''}</button>`).join('');
      const f = state.mode === 'nodes' ? focus[0] : focus[1];
      box.innerHTML = `<div class="label">Dependencies<span class="opts">${opts}</span></div>` +
        `<div class="graph">${graphSvg(f, state.mode, state.depth, state.expanded)}</div>` +
        `<div class="legend">${state.mode === 'nodes'
          ? 'Arrows run from a result or definition to those whose statements or proofs use it; helper lemmas are collapsed. Solid boxes are results, dashed boxes definitions' +
            (f.startsWith('m:') ? '; the dark box is the selected statement, shaded boxes are other statements of this result.' : '.')
          : 'Arrows run from a declaration to the declarations whose statements or proofs use it directly.'}</div>`;
    };
    box.addEventListener('click', ev => {
      const b = ev.target.closest('button');
      if (b) {
        if (b.dataset.mode) state.mode = b.dataset.mode;
        if (b.dataset.depth) state.depth = +b.dataset.depth;
        state.expanded.clear();
        draw();
        return;
      }
      const more = ev.target.closest('[data-expand]');
      if (more) { state.expanded.add(more.dataset.expand); draw(); return; }
      const g = ev.target.closest('.node[data-key]');
      if (g && !g.classList.contains('focus')) location.hash = nodeRoute(g.dataset.key);
    });
    box.addEventListener('mouseover', ev => {
      const g = ev.target.closest('.node[data-key]');
      box.querySelectorAll('path.edge').forEach(p =>
        p.classList.toggle('hot', !!g && (p.dataset.a === g.dataset.key || p.dataset.b === g.dataset.key)));
    });
    draw();
    return box;
  }

  // ------------------------------------------------------------------ the panel

  function crumbs(module) {
    const mod = D.modules[module];
    if (!mod) return '';
    const t = topicById.get(mod.topic), s = subById.get(mod.sub);
    return [t && `<a href="#" data-scroll="t-${esc(t.id)}">${esc(t.title)}</a>`,
      s && t && s.title !== t.title && `<a href="#" data-scroll="s-${esc(s.id)}">${esc(s.title)}</a>`,
      `<a href="#m/${encodeURIComponent(module)}">${md(mod.title, { inline: true })}</a>`].filter(Boolean).join(' › ');
  }

  function leanBlock(i) {
    const d = decls[i];
    const box = h('<div></div>');
    let view = 'st';
    const draw = () => {
      const text = view === 'st' ? (d.st || d.sig) : (d.sig || d.st);
      box.innerHTML = `<pre class="lean">${leanHtml(text || '', i)}</pre>`;
    };
    box.toggle = () => { view = view === 'st' ? 'sig' : 'st'; draw(); };
    draw();
    return box;
  }

  // One formal statement of a result: "In Lean" with the controls on the label, then the Lean.
  // A further one (`first` false) opens with its own name, if any, and its own "Statement".
  function declSection(i, opts = {}) {
    const d = decls[i];
    const sec = h(`<section class="decl${opts.first ? '' : ' form'}" id="decl-${i}"></section>`);
    if (!opts.first) {
      // the name, unless it is the title or the whole statement (`**The factor is unique.**`)
      if (d.nm && d.nm !== opts.title && d.stmt !== d.nm + '.')
        sec.insertAdjacentHTML('beforeend', `<h3 class="formname">${md(d.nm, { inline: true })}</h3>`);
      if (d.stmt) sec.insertAdjacentHTML('beforeend', '<div class="label">Statement</div>' + statementHtml(null, i));
    }
    const head = h(`<div class="label">In Lean<span class="opts">${wip(d)}` +
      `<button class="tog" title="Switch between the statement as written and as Lean elaborates it">elaborated</button>` +
      `<a class="srclink" href="${sourceUrl(i)}" target="_blank" rel="noopener">source ↗</a></span></div>`);
    sec.append(head);
    const lean = leanBlock(i);
    sec.append(lean);
    const tog = head.querySelector('.tog');
    tog.addEventListener('click', () => {
      lean.toggle();
      tog.classList.toggle('on');
    });
    return sec;
  }


  // shown above every References list: the library's statements are its own, not transcriptions
  const REFS_WARNING = 'This section is intended to assist you in finding related sources. ' +
    'The exact statements here may differ from those in the reference materials.';

  // Everything in the docstrings that is not the statement: pointers to other declarations,
  // proof sketches, and the sources with how their printed statements differ.
  function notesHtml(ids) {
    const many = ids.length > 1;
    const who = j => many ? `<code>${esc(short(decls[j].n))}</code>: ` : '';
    const rel = ids.flatMap(j => decls[j].rel.map(t => `<li>${who(j)}${md(t, { inline: true, bold: boldOf(j) })}</li>`));
    const notes = ids.flatMap(j => decls[j].no.map(t => `<li>${who(j)}${md(t, { inline: true, bold: boldOf(j) })}</li>`));
    const pf = ids.filter(j => decls[j].pf).map(j => `<li>${who(j)}${md(decls[j].pf, { inline: true, bold: boldOf(j) })}</li>`);
    const refs = new Map();
    for (const j of ids) {
      for (const [key, lab] of decls[j].ci) {
        if (!refs.has(key)) refs.set(key, { labels: new Set(), notes: new Set() });
        if (lab) refs.get(key).labels.add(lab);
      }
      const keys = [...new Set(decls[j].ci.map(c => c[0]))];
      for (const note of decls[j].cn) if (keys.length) refs.get(keys[keys.length - 1]).notes.add(md(note, { inline: true, bold: boldOf(j) }));
    }
    const refItems = [...refs].map(([key, r]) => {
      const b = D.bib[key];
      // a label already contained in another (`§0.8.7` in `§0.8.1 and §0.8.7`) is dropped
      const labels = [...r.labels].filter(l => ![...r.labels].some(o => o !== l && o.includes(l))).join('; ');
      return `<li><strong>${esc(key)}</strong>${labels ? ', ' + md(labels, { inline: true }) : ''}.` +
        (b ? ` ${esc(b.text)}${b.url ? ` <a href="${esc(b.url)}" target="_blank" rel="noopener">link</a>` : ''}` : '') +
        [...r.notes].map(n => `<div class="refnote">${n}</div>`).join('') + '</li>';
    });
    return (rel.length ? `<div class="label">Related</div><ul class="notes">${rel.join('')}</ul>` : '') +
      (notes.length ? `<div class="label">Notes</div><ul class="notes">${notes.join('')}</ul>` : '') +
      (pf.length ? `<div class="label">Proof sketch</div><ul class="notes">${pf.join('')}</ul>` : '') +
      (refItems.length ? `<div class="label">References</div><p class="refwarn">${REFS_WARNING}</p>` +
        `<ul class="refs">${refItems.join('')}</ul>` : '');
  }

  // the panel's heading: what kind of thing it is, above its name
  const KIND_NAMES = { def: 'Definition', abbrev: 'Definition', opaque: 'Definition',
    structure: 'Structure', class: 'Class', inductive: 'Inductive type', instance: 'Instance',
    theorem: 'Lemma' };
  const headHtml = (title, kind) =>
    `<div class="panelhead"><span class="kindtag">${kind}</span><h2>${title}</h2></div>`;

  function statementHtml(latex, i) {
    return `<div class="statement">${latex ? md(latex) : `<p>${stmtHtml(i, true)}</p>`}</div>`;
  }

  // A result page: its statements table (every member, labelled from its facets), and for the
  // selected statement its statement, explicit/asymptotic toggle, Lean, graph and notes.
  function showResult(rid, focusDecl) {
    const focusAlias = D.aliasFocus?.[rid];
    const asked = rid;
    rid = D.resultAlias?.[rid] ?? rid;
    const r = D.results[rid];
    if (!r) return showMissing();
    if (focusDecl === undefined && focusAlias !== undefined) focusDecl = focusAlias;
    // an old or merged id redirects: the address becomes the page it now lives on
    if (asked !== rid) history.replaceState(null, '', location.pathname + location.search +
      (focusDecl !== undefined ? rowRoute(rid, focusDecl) : '#r/' + encodeURIComponent(rid)));
    const rows = r.rows?.length ? r.rows : [{ o: overviewOf(r), e: r.explicit ?? overviewOf(r), c: {}, g: null, l: '' }];
    const cols = r.cols || [];
    memberRows = { rid, rows: new Map(rows.flatMap(row => [[row.o, row], [row.e, row]])) };
    let sel = Math.min(r.row ?? 0, rows.length - 1);
    let explicit = false;
    if (focusDecl !== undefined) {
      const k = rows.findIndex(x => x.o === focusDecl || x.e === focusDecl);
      if (k >= 0) { sel = k; explicit = rows[k].e === focusDecl && rows[k].o !== focusDecl; }
    }
    const nDecls = new Set(rows.flatMap(row => [row.o, row.e])).size;
    const body = $('#panelbody');
    body.innerHTML = headHtml(md(r.title, { inline: true }), 'Theorem') +
      `<div class="subtitle"><code>${esc(rid)}</code>${r.ids.map(x => `, <code>${esc(x)}</code>`).join('')}` +
      ` · ${rows.length > 1 ? `${rows.length} statements, ` : ''}${nDecls} formal statement${nDecls > 1 ? 's' : ''}` +
      `${(r.merged || []).length ? ' · includes ' + r.merged.map(x => `<code>${esc(x)}</code>`).join(', ') : ''}` +
      `${r.aliases.length ? ' · also known as ' + r.aliases.map(esc).join(', ') : ''}</div>`;

    let table = null;
    if (rows.length > 1) {
      const span = cols.length + 1;
      let group;
      const trs = rows.map((row, k) => {
        const head = row.g && row.g !== group ? `<tr class="stmt-group"><th colspan="${span}" scope="colgroup">${esc(row.g)}</th></tr>` : '';
        group = row.g;
        const label = plainTex(row.l || decls[row.e].nm || short(decls[row.e].n)).replace(/`/g, '');
        return head + `<tr class="stmt-row" data-k="${k}"><td class="pick"><input type="radio" name="stmt" value="${k}" aria-label="${esc(label)}"></td>` +
          cols.map(c => `<td class="c-${esc(c.k)}" data-label="${esc(c.t)}">${row.c[c.k] ? md(row.c[c.k], { inline: true }) : ''}</td>`).join('') + '</tr>';
      }).join('');
      table = h(`<section class="statements"><div class="label">Statements<span class="opts">${rows.length}</span></div>` +
        `<div class="stmt-scroll"><table class="stmt-table"><thead><tr><th class="pick" scope="col"><span class="sr">Selected</span></th>` +
        cols.map(c => `<th scope="col" class="c-${esc(c.k)}">${esc(c.t)}</th>`).join('') + `</tr></thead><tbody>${trs}</tbody></table></div></section>`);
      body.append(table);
      table.addEventListener('change', ev => {
        if (ev.target.name === 'stmt') select(+ev.target.value, false, true);
      });
      table.addEventListener('click', ev => {
        const tr = ev.target.closest('tr.stmt-row');
        if (tr && !ev.target.closest('a, input')) select(+tr.dataset.k, false, true);
      });
    }
    const graphState = { mode: 'nodes', depth: 1, expanded: new Set() };
    const detail = h('<div class="selection"></div>');
    body.append(detail);

    function select(k, keepExplicit, user) {
      if (k !== sel) { sel = k; if (!keepExplicit) explicit = false; }
      draw(user);
    }

    function draw(user) {
      const row = rows[sel];
      const paired = row.o !== row.e;
      const i = explicit && paired ? row.e : row.o;
      if (table) {
        for (const tr of table.querySelectorAll('tr.stmt-row')) {
          const on = +tr.dataset.k === sel;
          tr.classList.toggle('on', on);
          $('input', tr).checked = on;
        }
        if (user) history.replaceState(null, '', location.pathname + location.search + rowRoute(rid, i));
      }
      const d = decls[i];
      const name = d.nm && d.nm.replace(/^The (\S)/, (m, c) => c.toUpperCase());
      const latex = !paired && sel === (r.row ?? 0) && !r.forms?.length ? r.latex : null;
      detail.replaceChildren();
      const box = h('<section class="result-statement"></section>');
      box.innerHTML = '<div class="label">Statement<span class="opts">' +
        (paired ? `<button type="button" class="explicit-bound${explicit ? ' on' : ''}" aria-pressed="${explicit}">Explicit bound</button>` : '') +
        '</span></div>' +
        (rows.length > 1 && name && name !== r.title ? `<h3 class="formname">${md(name, { inline: true })}</h3>` : '') +
        `<div class="selected-statement" aria-live="polite">${statementHtml(latex, i)}</div>` +
        `<p class="statement-source"><a href="#decl-${i}" data-formal="${i}">View formal statement</a>` +
        (rows.length > 1 ? ` · <a href="${rowRoute(rid, i)}">Link to this statement</a>` : '') + '</p>';
      $('.explicit-bound', box)?.addEventListener('click', () => { explicit = !explicit; draw(true); });
      box.addEventListener('click', ev => {
        const a = ev.target.closest('[data-formal]');
        if (!a) return;
        ev.preventDefault();
        document.getElementById('decl-' + a.dataset.formal)?.scrollIntoView({ behavior: 'smooth' });
      });
      detail.append(box);
      const formal = paired ? [i, i === row.o ? row.e : row.o] : [i];
      formal.forEach((j, k) => detail.append(declSection(j, { title: r.title, first: k === 0 })));
      detail.append(graphSection([rows.length > 1 ? 'm:' + i : 'r:' + rid, 'i:' + i], ['nodes', 'decls'], graphState));
      detail.insertAdjacentHTML('beforeend', notesHtml(formal));
    }

    draw(false);
    openPanel(crumbs(r.module));
    if (table) {
      // the selected row in view inside the table's own scroll box, not the panel's
      const tr = table.querySelector('tr.stmt-row.on');
      const box = $('.stmt-scroll', table);
      if (tr && box.scrollHeight > box.clientHeight) box.scrollTop = tr.offsetTop - box.clientHeight / 3;
    }
  }

  function showDecl(name) {
    const i = byName.get(name);
    if (i === undefined) return showMissing();
    const d = decls[i];
    if (d.r.length) return showResult(d.r[0], i);
    const body = $('#panelbody');
    const def = isDef(d) && !isSupport(d);
    body.innerHTML = headHtml(`<code>${esc(short(d.n))}</code>`, KIND_NAMES[d.k] ?? d.k) +
      `<div class="subtitle">${md(D.modules[d.m]?.title || d.m, { inline: true })}</div>` +
      (d.stmt ? '<div class="label">Statement</div>' + statementHtml(null, i) : '');
    body.append(declSection(i, { first: true }));
    body.append(graphSection(def ? ['d:' + d.n, 'i:' + i] : [null, 'i:' + i], def ? ['nodes', 'decls'] : ['decls']));
    body.insertAdjacentHTML('beforeend', notesHtml([i]));
    openPanel(crumbs(d.m));
  }

  function showModule(name) {
    const mod = D.modules[name];
    if (!mod) return showMissing();
    const inMod = decls.map((d, i) => [d, i]).filter(([d]) => d.m === name);
    const item = ([d, i]) => `<li><a href="${declRoute(i)}"><code>${esc(short(d.n))}</code></a>` +
      `${d.r.length ? ` <em>${md(resultTitle(d.r[0]), { inline: true })}</em>` : ''}${wip(d)}` +
      (d.fs ? `<span class="desc">${descHtml(i)}</span>` : '') + '</li>';
    const results = inMod.filter(([d]) => d.r.length);
    const defs = inMod.filter(([d]) => !d.r.length && isDef(d) && !isSupport(d));
    const lemmas = inMod.filter(([d]) => !d.r.length && (!isDef(d) || isSupport(d)));
    $('#panelbody').innerHTML = headHtml(md(mod.title, { inline: true }), 'File') +
      `<div class="subtitle"><code>${esc(name)}</code> · <a href="${D.repo}/blob/${D.ref}/${mod.path}" target="_blank" rel="noopener">source ↗</a></div>` +
      (mod.summary ? `<div class="doc"><p>${md(mod.summary, { inline: true })}</p></div>` : '') +
      (results.length ? `<div class="label">Results</div><ul class="declist">${results.map(item).join('')}</ul>` : '') +
      (defs.length ? `<div class="label">Definitions</div><ul class="declist">${defs.map(item).join('')}</ul>` : '') +
      (lemmas.length ? `<div class="label">Supporting API</div><ul class="declist">${lemmas.map(item).join('')}</ul>` : '') +
      (mod.imports.length ? `<div class="label">Imports from the library</div><ul class="declist">${mod.imports.map(m =>
        D.modules[m] ? `<li><a href="#m/${encodeURIComponent(m)}">${md(D.modules[m].title, { inline: true })}</a> <code>${esc(m)}</code></li>` : '').join('')}</ul>` : '');
    openPanel(crumbs(name));
  }

  function showMissing() {
    $('#panelbody').innerHTML = '<h2>Not found</h2><p>Nothing in this version of the library has that name.</p>';
    openPanel('');
  }

  function openPanel(crumbHtml) {
    $('#crumbs').innerHTML = crumbHtml;
    $('#panel').hidden = false;
    document.body.classList.add('panel-open');
    $('#panelbody').scrollTop = 0;
  }

  function closePanel() {
    $('#panel').hidden = true;
    document.body.classList.remove('panel-open');
    if (location.hash) history.pushState(null, '', location.pathname + location.search);
  }

  $('#close').addEventListener('click', closePanel);
  $('#back').addEventListener('click', () => history.back());

  function route() {
    const rate = PAGE === 'rates' && /^#rate(?:\/|-row-)(.+)$/.exec(location.hash);
    if (rate) {
      $('#panel').hidden = true;
      document.body.classList.remove('panel-open');
      focusRate(decodeURIComponent(rate[1]));
      return;
    }
    // the notation and guarantee disclosures and the family sections are linkable too
    const anchor = PAGE === 'rates' && /^#rate-[\w-]+$/.test(location.hash) && document.getElementById(location.hash.slice(1));
    if (anchor) {
      if (anchor.tagName === 'DETAILS') anchor.open = true;
      anchor.scrollIntoView();
      return;
    }
    // a link to a book on the Books page (`books/#b-Tropp2015`) opens it
    const book = PAGE === 'books' && document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (book?.tagName === 'DETAILS') {
      book.open = true;
      book.scrollIntoView();
    }
    const m = /^#([rdm])\/([^?]+)(?:\?(.*))?$/.exec(location.hash);
    if (!m) {
      $('#panel').hidden = true;
      document.body.classList.remove('panel-open');
      return;
    }
    const arg = decodeURIComponent(m[2]);
    // `#r/<id>?s=<declaration>`: the result with that statement selected
    const picked = new URLSearchParams(m[3] || '').get('s');
    if (m[1] === 'r') showResult(arg, picked !== null ? byName.get(picked) : undefined);
    else if (m[1] === 'd') showDecl(arg);
    else showModule(arg);
  }
  window.addEventListener('hashchange', route);
  route();
})();
