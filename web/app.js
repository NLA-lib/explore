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
    D = await (await fetch(BASE + 'data.json')).json();
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
    psi: 'ψ', phi: 'φ', pi: 'π', omega: 'ω', sin: 'sin ', cos: 'cos ', log: 'log ', det: 'det ', tr: 'tr ' };
  const SUP = { 0: '⁰', 1: '¹', 2: '²', 3: '³', 4: '⁴', '+': '⁺', '-': '⁻', '*': '*', T: 'ᵀ', H: 'ᴴ' };
  const plainTex = t => t.replace(/\$([^$]*)\$/g, (_, m) => m
    .replace(/\\(?:mathbf|mathsf|mathrm|operatorname|boldsymbol)\{([^{}]*)\}/g, '$1')
    .replace(/\\\|/g, '‖').replace(/\\([a-zA-Z]+)\s*/g, (c, w) => GREEK[w] ?? '')
    .replace(/\^\{?([0-9+\-*TH])\}?/g, (c, x) => SUP[x]).replace(/_\{?([^{}\s]+)\}?/g, (c, x) => x.replace(/\d/g, n => '₀₁₂₃₄₅₆₇₈₉'[n]))
    .replace(/[{}]/g, '').replace(/\s+/g, ' ').trim());
  const nodeLabel = key => {
    if (key.startsWith('r:')) return plainTex(resultTitle(key.slice(2))).replace(/`/g, '');
    if (key.startsWith('d:')) return short(key.slice(2));
    return short(decls[+key.slice(2)].n);
  };
  const nodeRoute = key => {
    if (key.startsWith('r:')) return '#r/' + encodeURIComponent(key.slice(2));
    if (key.startsWith('d:')) return '#d/' + encodeURIComponent(key.slice(2));
    return '#d/' + encodeURIComponent(decls[+key.slice(2)].n);
  };
  const declRoute = i => '#d/' + encodeURIComponent(decls[i].n);
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

  function renderCatalogue() {
    $('#content').innerHTML = D.topics.map(t => {
      const flat = t.subs.length === 1 && t.subs[0].title === t.title;
      const collection = (D.collections || []).find(c => c.topic === t.id);
      const sourceBody = t.subs.map(s => section(`s-${s.id}`, 'sub', 'h3', s.title, counts(s.modules), s.modules.map(moduleHtml).join(''))).join('');
      const collectionBody = collection ? (collection.description ? `<p class="topic-blurb">${md(collection.description, { inline: true })}</p>` : '') + collection.groups.map(g => section(`collection-${collection.id}-${g.id}`, 'sub', 'h3', g.title, '', `<ul class="entries">${g.entries.filter(e => e.type === 'r' ? D.results[e.rid] : decls[e.i]).map(entryHtml).join('')}</ul>`)).join('') + (sourceBody ? `<details class="source-modules" id="source-modules-${esc(collection.id)}"${openSections.has(`source-modules-${collection.id}`) ? ' open' : ''}><summary>Browse source modules</summary>${sourceBody}</details>` : '') : '';
      const body = collection ? collectionBody : (t.blurb ? `<p class="topic-blurb">${md(t.blurb, { inline: true })}</p>` : '') +
        t.subs.map(s => {
          const inner = (s.blurb ? `<p class="sub-blurb">${md(s.blurb, { inline: true })}</p>` : '') +
            s.modules.map(moduleHtml).join('');
          return flat ? inner : section(`s-${s.id}`, 'sub', 'h3', s.title, counts(s.modules), inner);
        }).join('');
      const unique = collection && new Set(collection.groups.flatMap(g => g.entries.map(e => e.type === 'r' ? 'r:' + e.rid : 'd:' + e.i)));
      const total = unique ? `${unique.size} entries` : counts(t.subs.flatMap(s => s.modules));
      return section(`t-${t.id}`, 'topic', 'h2', t.title, total, body);
    }).join('');
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

  function initRates() {
    document.title = 'NLA-lib Rates';
    $('h1').textContent = 'NLA-lib Rates';
    $('#intro').hidden = false;
    $('#intro').textContent = 'Compare guarantees and sample requirements. Expand a row for its precise theorem and hypotheses.';
    $('#q').placeholder = 'Search rates, algorithms, sketches and guarantees';
    $('#q').setAttribute('aria-label', 'Search rates');
    $('#byline').innerHTML = `From NLAlib at ${commit}${D.date ? ', ' + esc(D.date.slice(0, 10)) : ''}.`;
    $('#searchbar').append(h('<div class="rate-filters" aria-label="Filter rates"></div>'));
    renderRates();
  }

  function renderRateFilters() {
    const families = D.rates?.families || [];
    const family = families.find(f => f.id === rateFilters.family);
    const schema = family?.filters || [];
    const allowed = new Set(['family', ...schema.map(f => f.field)]);
    for (const key of Object.keys(rateFilters)) if (!allowed.has(key)) delete rateFilters[key];
    const filters = $('.rate-filters');
    if (!filters) return;
    filters.replaceChildren();
    const add = (field, title, values, names = {}) => {
      const label = h(`<label>${esc(title)}<select data-field="${esc(field)}" aria-label="${esc(title)}"><option value="">All${field === 'family' ? ' families' : ''}</option>${values.map(v =>
        `<option value="${esc(v)}"${rateFilters[field] === v ? ' selected' : ''}>${esc(names[v] || v)}</option>`).join('')}</select></label>`);
      $('select', label).addEventListener('change', ev => {
        const value = ev.target.value;
        if (field === 'family') for (const key of Object.keys(rateFilters)) delete rateFilters[key];
        rateFilters[field] = value;
        renderRates();
        [...document.querySelectorAll('.rate-filters select')].find(s => s.dataset.field === field)?.focus();
      });
      filters.append(label);
    };
    add('family', 'Family', families.map(f => f.id), Object.fromEntries(families.map(f => [f.id, f.title])));
    if (!family) return;
    const rows = (D.rates?.entries || []).filter(e => e.family === family.id);
    for (const facet of schema) {
      const compatible = rows.filter(e => schema.every(other => other.field === facet.field || !rateFilters[other.field] || e[other.field] === rateFilters[other.field]));
      const values = [...new Set(compatible.map(e => e[facet.field]).filter(v => v !== undefined && v !== null && v !== '').map(String))];
      if (facet.order) {
        const rank = value => { const i = facet.order.indexOf(value); return i < 0 ? facet.order.length : i; };
        values.sort((a, b) => rank(a) - rank(b));
      }
      if (rateFilters[facet.field] && !values.includes(rateFilters[facet.field])) delete rateFilters[facet.field];
      if (values.length > 1 || rateFilters[facet.field]) add(facet.field, facet.label || facet.field, values);
    }
  }

  function rateSearchWords(text) {
    return String(text || '').replace(/\\(?:varepsilon|epsilon)\b/g, ' epsilon ')
      .replace(/[εϵ]/g, ' epsilon ').replace(/[δ]/g, ' delta ')
      .replace(/\\(?:mathbf|mathsf|mathrm|mathbb|operatorname|text|left|right|frac|sqrt)\b/g, ' ')
      .toLowerCase().match(/[\p{L}\p{N}]+/gu) || [];
  }

  function resetRates() {
    $('#q').value = '';
    for (const k of Object.keys(rateFilters)) rateFilters[k] = '';
    renderRateFilters();
    renderRates();
  }

  function renderRates() {
    renderRateFilters();
    const query = rateSearchWords($('#q').value);
    const entries = (D.rates?.entries || []).filter(e => {
      if (!Object.entries(rateFilters).every(([k, v]) => !v || String(e[k]) === v)) return false;
      const family = D.rates.families.find(f => f.id === e.family);
      const guarantee = D.rates.guarantees?.find(g => g.id === e.guarantee && g.family === e.family);
      const words = rateSearchWords([e.algorithm, e.variant, e.sketch, e.norm, e.mode, guarantee?.title, guarantee?.description,
        ...(family?.filters || []).map(f => e[f.field]), ...e.resources.flatMap(r => [r.label, r.bound]), ...(Array.isArray(e.notes) ? e.notes : [e.notes]), family?.title].join(' '));
      return query.every(q => words.some(w => w.includes(q)));
    });
    const families = D.rates?.families || [];
    $('#content').innerHTML = entries.length ? `<p class="searchnote">${entries.length} rate${entries.length === 1 ? '' : 's'}. Resources and parameter caveats are stated per row.</p>` + families.map(f => {
      const rows = entries.filter(e => e.family === f.id);
      const subject = esc(f.subject_label || 'Method / sketch');
      if (!rows.length) return '';
      const notationId = `rate-notation-${f.id}`;
      const definitionLink = (i, label) => Number.isInteger(i) && decls[i]
        ? `<a href="${BASE}${declRoute(i)}">${esc(label)}</a>` : '';
      const groups = (D.rates.guarantees || []).filter(g => g.family === f.id && rows.some(e => e.guarantee === g.id));
      return `<section class="rate-family"><h2>${esc(f.title)}</h2>${f.description ? `<p class="topic-blurb">${md(f.description, { inline: true })}</p>` : ''}` +
        (f.notation ? `<details class="rate-notation" id="${esc(notationId)}"${openSections.has(notationId) ? ' open' : ''}><summary>Notation and assumptions</summary>${md(f.notation)}</details>` : '') + groups.map(g => {
          const groupId = `rate-guarantee-${f.id}-${g.id}`;
          const definitions = g.definitions || [];
          return `<section class="rate-guarantee"><h3>${md(g.title, { inline: true })}</h3>` +
            `<details class="rate-definitions" id="${esc(groupId)}"${openSections.has(groupId) ? ' open' : ''}><summary>Guarantee and definitions</summary><div class="guarantee-description">${md(g.description)}</div>${definitions.map(d =>
              `<h4>${definitionLink(d.i, d.label || d.declaration)}</h4>${statementHtml(null, d.i)}`).join('')}</details>` +
            `<table class="rates-table"><thead><tr><th scope="col">${subject}</th><th scope="col">Resources</th></tr></thead><tbody>` + rows.filter(e => e.guarantee === g.id).map(e => {
              const notes = Array.isArray(e.notes) ? e.notes.join(' ') : e.notes;
              return `<tr id="rate-row-${esc(e.id)}"><td data-label="${subject}"><strong>${esc(e[f.subject_field || 'algorithm'])}</strong>${e.variant && e.variant !== 'Standard' ? `<span class="rate-meta">${md(e.variant, { inline: true })}</span>` : ''}${e.sketch && f.subject_field !== 'sketch' ? `<span class="rate-meta">${esc(e.sketch)}</span>` : ''}` +
                `<span class="rate-definition-links">${[definitionLink(e.algorithm_definition_index, f.definition_label || 'Algorithm definition'), definitionLink(e.sketch_definition_index, 'Sketch definition')].filter(Boolean).join(' · ')}</span></td>` +
                `<td data-label="Resources">${e.resources.map(r => `<div class="rate-resource"><strong>${esc(r.label)}:</strong> ${md(r.bound, { inline: true })}</div>`).join('')}${notes ? `<p class="rate-caveat"><strong>Parameters:</strong> ${md(notes, { inline: true })}</p>` : ''}</td>` +
                `</tr><tr class="rate-theorem"><td colspan="2"><button type="button" class="rate-permalink" data-copy-rate="${esc(e.id)}">Copy link</button><span class="rate-copy-status" role="status"></span><details class="rate-detail" data-rate="${esc(e.id)}"><summary>View theorem</summary><div class="rate-expanded"></div></details></td></tr>`;
            }).join('') + '</tbody></table></section>';
        }).join('') + '</section>';
    }).join('') : '<p class="empty">No rates match these filters.</p><button type="button" id="reset-rates">Reset filters and search</button>';
    $('#reset-rates')?.addEventListener('click', resetRates);
    for (const button of document.querySelectorAll('[data-copy-rate]')) button.addEventListener('click', async () => {
      const url = new URL('#rate/' + encodeURIComponent(button.dataset.copyRate), location.href).href;
      const status = button.nextElementSibling;
      try {
        await navigator.clipboard.writeText(url);
        status.textContent = 'Link copied';
      } catch (error) {
        status.innerHTML = `Copy this link: <a href="${esc(url)}">${esc(url)}</a>`;
      }
    });
    for (const detail of document.querySelectorAll('.rate-detail')) {
      const e = entries.find(e => e.id === detail.dataset.rate);
      let explicit = false;
      const draw = () => {
        const i = explicit ? e.explicit : e.overview;
        $('.rate-expanded', detail).innerHTML = (e.explicit !== e.overview ? `<button type="button" class="rate-explicit${explicit ? ' on' : ''}" aria-pressed="${explicit}">Explicit bound</button>` : '') +
          statementHtml(null, i) + `<p class="rate-links"><a href="${BASE}${declRoute(e.overview)}">Asymptotic theorem</a> · <a href="${BASE}${declRoute(e.explicit)}">Explicit theorem</a> · <a href="${sourceUrl(i)}" target="_blank" rel="noopener">Source ↗</a></p>`;
        $('.rate-explicit', detail)?.addEventListener('click', () => { explicit = !explicit; draw(); });
      };
      detail.addEventListener('toggle', () => { if (detail.open && !$('.rate-expanded', detail).childNodes.length) draw(); });
    }
  }

  function focusRate(id) {
    let detail = [...document.querySelectorAll('.rate-detail')].find(d => d.dataset.rate === id);
    if (!detail && (D.rates?.entries || []).some(e => e.id === id)) {
      resetRates();
      detail = [...document.querySelectorAll('.rate-detail')].find(d => d.dataset.rate === id);
    }
    if (detail) { detail.open = true; document.getElementById('rate-row-' + id).scrollIntoView({ behavior: 'smooth', block: 'start' }); }
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
    .toLowerCase().split(/[^\p{L}\p{N}]+/u)
    .filter(w => w && !STOP.has(w)).map(stem);

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
      add('r', rid, [[r.title, 4], [r.aliases.join(' '), 4], [rid, 3],
        [r.decls.map(j => short(decls[j].n)).join(' '), 2],
        [r.decls.map(j => stripResult(decls[j].doc)).join(' '), 1],
        [D.modules[r.module]?.title, 0.5]], 1.3);
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
          const qlty = v === alt ? 1 : (alt.length >= 3 && v.startsWith(alt)) ? 0.75
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

  function hitHtml(it) {
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
        'words are matched against names, docstrings and file titles.</p>' +
        `<ul class="entries">${lastHits.map(hitHtml).join('')}</ul>`
      : '<p class="empty">Nothing matches.</p>';
  }

  let timer = null;
  $('#q').addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(runSearch, 90); });
  $('#q').addEventListener('keydown', ev => {
    if (ev.key === 'Enter' && lastHits.length) {
      const it = lastHits[0];
      location.hash = it.type === 'r' ? '#r/' + encodeURIComponent(it.key)
        : it.type === 'm' ? '#m/' + encodeURIComponent(it.key) : declRoute(it.key);
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
      return { up: k => D.nodes[k]?.u ?? [], down: k => D.nodes[k]?.b ?? [] };
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
        const cls = ['node', k === focus ? 'focus' : '', k.startsWith('d:') ? 'def' : ''].join(' ');
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

  function graphSection(focus, modes) {
    const state = { mode: modes[0], depth: 1, expanded: new Set() };
    const box = h('<div></div>');
    const draw = () => {
      const opts = (modes.length > 1 ? modes.map(m =>
        `<button data-mode="${m}" class="${state.mode === m ? 'on' : ''}">${m === 'nodes' ? 'results and definitions' : 'all declarations'}</button>`).join('') : '') +
        [1, 2].map(n => `<button data-depth="${n}" class="${state.depth === n ? 'on' : ''}">${n} step${n > 1 ? 's' : ''}</button>`).join('');
      const f = state.mode === 'nodes' ? focus[0] : focus[1];
      box.innerHTML = `<div class="label">Dependencies<span class="opts">${opts}</span></div>` +
        `<div class="graph">${graphSvg(f, state.mode, state.depth, state.expanded)}</div>` +
        `<div class="legend">${state.mode === 'nodes'
          ? 'Arrows run from a result or definition to those whose statements or proofs use it; helper lemmas are collapsed. Solid boxes are results, dashed boxes definitions.'
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
      (refItems.length ? `<div class="label">References</div><ul class="refs">${refItems.join('')}</ul>` : '');
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

  function showResult(rid, focusDecl) {
    rid = D.resultAlias?.[rid] ?? rid;
    const r = D.results[rid];
    if (!r) return showMissing();
    const overview = overviewOf(r);
    const forms = r.forms || [];
    // An asymptotic declaration may have an additional Result id of its own. Its target
    // still needs a formal section here without changing that target's result membership.
    const formalDecls = [...new Set([overview, ...r.decls, ...forms.flatMap(f => [f.overview, f.explicit])])];
    const body = $('#panelbody');
    body.innerHTML = headHtml(md(r.title, { inline: true }), 'Theorem') +
      `<div class="subtitle"><code>${esc(rid)}</code>${r.ids.map(x => `, <code>${esc(x)}</code>`).join('')} · ${formalDecls.length} formal statement${formalDecls.length > 1 ? 's' : ''}` +
      `${r.aliases.length ? ' · also known as ' + r.aliases.map(esc).join(', ') : ''}</div>`;
    if (forms.length) {
      // Each pair owns its parsed mathematical statement and hypotheses. Related pointers,
      // proof constants and citations stay in their sections below; no result override applies.
      let pair = Math.max(0, forms.findIndex(f => f.overview === overview));
      let explicit = false;
      const box = h('<section class="result-statement"></section>');
      const choices = forms.length > 1 ? `<label class="variant">Variant <select aria-label="Statement variant">${forms.map((f, k) =>
        `<option value="${k}"${k === pair ? ' selected' : ''}>${esc(plainTex(r.variantLabels?.[k] || decls[f.explicit].nm || short(decls[f.explicit].n)))}</option>`).join('')}</select></label>` : '';
      box.innerHTML = '<div class="label">Statement<span class="opts">' +
        '<button type="button" class="explicit-bound" aria-pressed="false">Explicit bound</button></span></div>' + choices +
        '<div class="selected-statement" aria-live="polite"></div>';
      const draw = () => {
        const i = explicit ? forms[pair].explicit : forms[pair].overview;
        $('.selected-statement', box).innerHTML = statementHtml(null, i) +
          `<p class="statement-source"><a href="#decl-${i}" data-formal="${i}">View formal statement</a></p>`;
        const button = $('.explicit-bound', box);
        button.setAttribute('aria-pressed', String(explicit));
        button.classList.toggle('on', explicit);
      };
      $('.explicit-bound', box).addEventListener('click', () => { explicit = !explicit; draw(); });
      $('select', box)?.addEventListener('change', ev => { pair = +ev.target.value; draw(); });
      box.addEventListener('click', ev => {
        const a = ev.target.closest('[data-formal]');
        if (!a) return;
        ev.preventDefault();
        document.getElementById('decl-' + a.dataset.formal)?.scrollIntoView({ behavior: 'smooth' });
      });
      draw();
      body.append(box);
    } else {
      body.insertAdjacentHTML('beforeend', '<div class="label">Statement</div>' + statementHtml(r.latex, overview));
    }
    formalDecls.forEach((j, k) => body.append(declSection(j, { title: r.title, first: k === 0 })));
    body.append(graphSection(['r:' + rid, 'i:' + (focusDecl ?? overview)], ['nodes', 'decls']));
    body.insertAdjacentHTML('beforeend', notesHtml(formalDecls));
    openPanel(crumbs(r.module));
    if (focusDecl !== undefined) document.getElementById('decl-' + focusDecl)?.scrollIntoView();
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
    if (PAGE === 'rates' && location.hash.startsWith('#rate/')) {
      $('#panel').hidden = true;
      document.body.classList.remove('panel-open');
      focusRate(decodeURIComponent(location.hash.slice(6)));
      return;
    }
    // a link to a book on the Books page (`books/#b-Tropp2015`) opens it
    const book = PAGE === 'books' && document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (book?.tagName === 'DETAILS') {
      book.open = true;
      book.scrollIntoView();
    }
    const m = /^#([rdm])\/(.+)$/.exec(location.hash);
    if (!m) {
      $('#panel').hidden = true;
      document.body.classList.remove('panel-open');
      return;
    }
    const arg = decodeURIComponent(m[2]);
    if (m[1] === 'r') showResult(arg);
    else if (m[1] === 'd') showDecl(arg);
    else showModule(arg);
  }
  window.addEventListener('hashchange', route);
  route();
})();
