// Docstrings write informal mathematics in backticks with Unicode (`σ_{i+j}(A + B) ≤ σ_i(A) + σ_j(B)`,
// `‖A⁻¹‖₂`), and Lean in backticks too (`singularValues A k`). `codeToTex` turns the first kind into
// LaTeX for KaTeX and returns null for the second, which stays code. A span counts as mathematics when
// every word in it is a single letter or a standard operator name; any Lean name (camelCase,
// snake_case, dotted) or Lean syntax keeps it as code.
'use strict';

(function (root) {
  const OPS = {
    log: '\\log ', exp: '\\exp ', sin: '\\sin ', cos: '\\cos ', tan: '\\tan ', max: '\\max ', min: '\\min ',
    sup: '\\sup ', inf: '\\inf ', det: '\\det ', dim: '\\dim ', ker: '\\ker ', lim: '\\lim ', arg: '\\arg ',
    tr: '\\operatorname{tr}', rank: '\\operatorname{rank}', card: '\\operatorname{card}',
    diag: '\\operatorname{diag}', re: '\\operatorname{Re}', im: '\\operatorname{Im}',
    span: '\\operatorname{span}', range: '\\operatorname{range}', sign: '\\operatorname{sign}',
    sgn: '\\operatorname{sgn}', conj: '\\overline', Var: '\\operatorname{Var}',
    Ent: '\\operatorname{Ent}', Pr: '\\Pr ', vol: '\\operatorname{vol}', poly: '\\operatorname{poly}',
  };
  const SYMBOLS = {
    '‖': '\\|', '≤': '\\le ', '≥': '\\ge ', '≠': '\\ne ', '∈': '\\in ', '∉': '\\notin ',
    '→': '\\to ', '↦': '\\mapsto ', '∞': '\\infty ', '·': '\\cdot ', '•': '\\cdot ', '⬝ᵥ': '\\cdot ',
    '⟨': '\\langle ', '⟩': '\\rangle ', '≈': '\\approx ', '≔': '\\coloneqq ', '⇑': '\\Uparrow ', '⊓': '\\sqcap ', '⊔': '\\sqcup ', '⊤': '\\top ', '∘': '\\circ ', '⊆': '\\subseteq ',
    '⊂': '\\subset ', '∩': '\\cap ', '∪': '\\cup ', '×': '\\times ', '⊗': '\\otimes ', '⊙': '\\odot ',
    '≺': '\\prec ', '≼': '\\preceq ', '∀': '\\forall ', '∃': '\\exists ', '¬': '\\neg ', '∧': '\\wedge ',
    '∨': '\\vee ', '↔': '\\leftrightarrow ', '⇒': '\\Rightarrow ', '±': '\\pm ', '∣': '\\mid ',
    'ℝ': '\\mathbb{R}', 'ℂ': '\\mathbb{C}', 'ℕ': '\\mathbb{N}', 'ℤ': '\\mathbb{Z}', 'ℚ': '\\mathbb{Q}',
    '𝕜': '\\Bbbk', 'ᴴ': '^{\\mathsf{H}}', 'ᵀ': '^{\\mathsf{T}}', '†': '^{\\dagger}', '⁻¹': '^{-1}',
    '²': '^{2}', '³': '^{3}', '⁴': '^{4}', '∑': '\\sum ', '∏': '\\prod ', '∫': '\\int ', '∂': '\\partial ',
    '∇': '\\nabla ', '≪': '\\ll ', '≫': '\\gg ', '∖': '\\setminus ', '∅': '\\emptyset ', '⊥': '\\perp ',
    '∥': '\\parallel ', 'ℓ': '\\ell ', '𝔼': '\\mathbb{E}', 'ℙ': '\\mathbb{P}', '…': '\\dots ', '⌈': '\\lceil ', '⌉': '\\rceil ',
    '⌊': '\\lfloor ', '⌋': '\\rfloor ', '*ᵥ': '\\,', 'ᵥ*': '\\,', '√': '\\surd ',
  };
  const SUP = { 'ᴴ': '\\mathsf{H}', 'ᵀ': '\\mathsf{T}', '†': '\\dagger', '⁺': '+', '⁻': '-', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁰': '0', 'ᵏ': 'k', 'ⁿ': 'n', 'ᵐ': 'm', 'ⁱ': 'i', 'ʳ': 'r', 'ᵗ': 't', '⁽': '(', '⁾': ')' };
  const SUB = { '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4', '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9', 'ᵢ': 'i', 'ⱼ': 'j', 'ₖ': 'k', 'ₙ': 'n', 'ₐ': 'a', 'ₘ': 'm', 'ₓ': 'x', 'ₗ': 'l', 'ₚ': 'p', 'ₛ': 's', 'ₜ': 't', '₊': '+', '₋': '-' };
  const LEAN = /=>|:=|\bfun\b|\bif\b|\bthen\b|\belse\b|\bby\b|\.lean|\bNLAlib\b|@|\$|\\|^\s*$|\p{L}{2,}_\p{L}{2,}/u;

  // tokens: words, numbers, sub/superscript runs, multi-char symbols, single chars
  const TOKEN = /([\p{Ll}\p{Lu}\p{Lo}][\p{Ll}\p{Lu}\p{Lo}\p{Nd}]*'*(?:_(?:\{[^}]*\}|[\p{Ll}\p{Lu}\p{Lo}\p{Nd}]+))?(?:[_.][\p{L}\p{Nd}₀-₉][\p{L}\p{Nd}₀-₉']*)*[₀-₉]*)|(\d+(?:\.\d+)?)|([₀-₉ᵢⱼₖₙₐₘₓₗₚₛₜ₊₋]+)|(\*ᵥ|ᵥ\*|⬝ᵥ)|([ᴴᵀ†⁺⁻¹²³⁴⁰ᵏⁿᵐⁱʳᵗ⁽⁾]+)|(_(?:\{[^}]*\}|[\p{Ll}\p{Lu}\p{Lo}\p{Nd}]+[₀-₉]*))|(\s+)|([\s\S])/gu;

  // `lenient`: also accept Lean, typesetting each Lean name upright (\operatorname{eigenvalue} A k),
  // for statements, which are set entirely in KaTeX's font
  const texName = w => `\\operatorname{${w.replace(/_/g, '\\_').replace(/[₀-₉]/g, c => SUB[c])}}`;

  // `bold`: the single-letter variables that are matrices or vectors, set in \mathbf
  // Lean constructions with a standard notation: name -> [arity, (args, raw) => TeX]. An argument
  // is a parenthesised group or one token (`Bᴴ`, `A₁`, `0`); `raw[i]` says it was a group.
  const CONSTRUCTS = {
    fromBlocks: [4, a => `\\begin{bmatrix}${a[0]} & ${a[1]} \\\\ ${a[2]} & ${a[3]}\\end{bmatrix}`],
    fromCols: [2, a => `\\begin{bmatrix}${a[0]} & ${a[1]}\\end{bmatrix}`],
    fromRows: [2, a => `\\begin{bmatrix}${a[0]} \\\\ ${a[1]}\\end{bmatrix}`],
    pinv: [1, (a, g) => g[0] ? `(${a[0]})^{+}` : `{${a[0]}}^{+}`],
    diagonal: [1, a => `\\operatorname{diag}(${a[0]})`],
    specNorm: [1, a => `\\|${a[0]}\\|_{2}`],
    frobNorm: [1, a => `\\|${a[0]}\\|_{\\mathsf{F}}`],
    conditionNumber: [1, a => `\\kappa(${a[0]})`],
    eigenvalue: [2, a => `\\lambda_{${a[1]}}(${a[0]})`],
    singularValues: [2, a => `\\sigma_{${a[1]}}(${a[0]})`],
    rangeProjector: [1, a => `\\mathbf{P}_{${a[0]}}`],
    conj: [1, a => `\\overline{${a[0]}}`],
    'Fintype.card': [1, a => `\\lvert ${a[0]}\\rvert`],
    'CFC.sqrt': [1, (a, g) => g[0] ? `(${a[0]})^{1/2}` : `{${a[0]}}^{1/2}`],
    quadForm: [2, (a, g) => `${g[1] ? `(${a[1]})` : `{${a[1]}}`}^{\\mathsf{H}}${a[0]}${g[1] ? `(${a[1]})` : a[1]}`],
    nuclearNorm: [1, a => `\\|${a[0]}\\|_{*}`],
    kyFanNorm: [2, a => `\\|${a[1]}\\|_{(${a[0]})}`],
    schattenNorm: [2, a => `\\|${a[1]}\\|_{S_{${a[0]}}}`],
    // the continuous functional calculus is application, `cfc f A` = f(A); `star` conjugates
    cfc: [2, (a, g) => `${g[0] ? `(${a[0]})` : a[0]}(${a[1]})`],
    star: [1, a => `\\overline{${a[0]}}`],
    // a standard basis vector, `Pi.single i 1` = e_i
    'Pi.single': [2, a => `${a[1] === '1' ? '' : a[1] + '\\,'}\\mathbf{e}_{${a[0]}}`],
    // Lean's two-argument `min a b`, `max a b`
    min: [2, a => `\\min(${a[0]}, ${a[1]})`],
    max: [2, a => `\\max(${a[0]}, ${a[1]})`],
  };
  const CONSTRUCT = new RegExp(`(?<![\\p{L}\\p{N}_.'])(?:Matrix\\.|NLAlib\\.)?(${Object.keys(CONSTRUCTS).map(k => k.replace('.', '\\.')).join('|')})(?![\\p{L}\\p{N}_.'])`, 'gu');
  const ARG_TOKEN = /^(?:[\p{L}][\p{L}\p{N}'_]*|\d+)(?:ᴴ|ᵀ|†|⁺|⁻¹|[₀-₉])*/u;

  // replace each construction by a private-use placeholder whose TeX is kept in `slots`
  function expand(src, lenient, bold, slots) {
    let out = '', pos = 0, m;
    const re = new RegExp(CONSTRUCT.source, 'gu');   // own state: arguments recurse
    while ((m = re.exec(src))) {
      const [arity, make] = CONSTRUCTS[m[1]];
      let p = m.index + m[0].length;
      const args = [], groups = [];
      for (let k = 0; k < arity; k++) {
        const ws = /^\s+/.exec(src.slice(p));
        if (!ws) break;
        p += ws[0].length;
        if (src[p] === '‖' && src.indexOf('‖', p + 1) > p) {      // a norm, `max ‖V₁‖ ‖V₂‖`
          const q = src.indexOf('‖', p + 1);
          args.push(src.slice(p, q + 1)); groups.push(false); p = q + 1;
        } else if (src[p] === '(') {
          let depth = 0, q = p;
          for (; q < src.length; q++) {
            if (src[q] === '(') depth++;
            else if (src[q] === ')' && --depth === 0) break;
          }
          if (q >= src.length) break;
          args.push(src.slice(p + 1, q)); groups.push(true); p = q + 1;
        } else {
          const t = ARG_TOKEN.exec(src.slice(p));
          if (!t || CONSTRUCTS[t[0]]) break;
          args.push(t[0]); groups.push(false); p += t[0].length;
        }
      }
      if (args.length < arity) continue;            // used as a name, not applied: leave it
      const texArgs = args.map(a => codeToTex(a, lenient, bold));
      if (texArgs.some(t => t === null)) continue;
      out += src.slice(pos, m.index) + String.fromCharCode(0xE000 + slots.length);
      slots.push(make(texArgs, groups));
      pos = p;
      re.lastIndex = p;
    }
    return entries(out + src.slice(pos), bold, slots);
  }

  // Entries: Lean applies a matrix or vector to its indices, `A i j`, `x i`; shown `A_{i,j}`,
  // `x_i`. Only for a letter in the bold set followed by one or two plain indices (single
  // lowercase letters that are not themselves vectors, or numerals), so `A x` stays a product.
  // `E` is left alone: it may be the expectation.
  const ENTRY = /(?<![\p{L}\p{N}_.'-])([A-DF-Za-z])((?:\s+(?:[a-z][₀-₉']*|\d+)(?![\p{Ll}\p{Lu}\p{Lo}\p{Nd}₀-₉_.'(\[^-])){1,2})(ᴴ|ᵀ|⁻¹|[²³⁴])?(?![\p{L}\p{N}_.'(\[^])/gu;
  const INDEX = /^(?:[ijkl][₀-₉']*|\d+)$/;
  function entries(src, bold, slots) {
    const keep = tex => String.fromCharCode(0xE000 + slots.push(tex) - 1);
    // accents written with combining marks: `v̂`, `x̃`, `x̄`
    src = src.replace(/(\p{L})([\u0302\u0303\u0304])/gu, (m, c, mark) => keep(
      `\\${{ '\u0302': 'hat', '\u0303': 'tilde', '\u0304': 'bar' }[mark]}{${bold && bold.has(c) ? `\\mathbf{${c}}` : c}}`));
    // words of prose inside the maths, `√(number of columns)`: upright text
    src = src.replace(/(?<![\p{L}\p{N}_.'])[a-z]{2,}(?:\s+[a-z]{2,})+(?![\p{L}\p{N}_.'])/gu, m =>
      m.split(/\s+/).some(w => OPS[w]) || !/\b(?:of|the|and|in|on|for|with|to)\b/.test(m) ? m : keep(`\\text{${m}}`));
    // Mathlib's extended nonnegative reals and nonnegative reals
    src = src.replace(/ℝ≥0∞/g, () => keep('[0,\\infty]')).replace(/ℝ≥0/g, () => keep('\\mathbb{R}_{\\ge 0}'));
    return src.replace(ENTRY, (m, v, idx, post, at) => {
      // not inside a braced sub- or superscript (`e^{s j}`), which is converted on its own
      const before = src.slice(0, at);
      if ((before.match(/\{/g) || []).length > (before.match(/\}/g) || []).length) return m;
      const ix = idx.trim().split(/\s+/);
      const isBold = !!bold && bold.has(v);
      // a vector or matrix with plain indices, or any other lowercase letter (not a function
      // name) indexed by i, j, k, l: `|x i|` in a gauge whose `x` is not declared a vector
      const plain = !isBold && /[a-eA-Z]|[m-z]/.test(v) && /[a-z]/.test(v) && !'fgh'.includes(v) &&
        ix.length === 1 && INDEX.test(ix[0]);
      if (!(isBold || plain) || ix.some(i => bold && bold.has(i.replace(/[₀-₉']+$/, '')))) return m;
      // a matrix's or vector's indices are index letters or numerals: `A x` is a product, not A_x
      if (isBold && ix.some(i => !/^(?:[ijklmnpqrst][₀-₉']*|\d+)$/.test(i))) return m;
      const sub = ix.map(i => i.replace(/[₀-₉]/g, c => '_{' + SUB[c] + '}')).join(',');
      const sup = post === 'ᴴ' ? '^{\\mathsf{H}}' : post === 'ᵀ' ? '^{\\mathsf{T}}' : post === '⁻¹' ? '^{-1}'
        : post ? `^{${SUP[post]}}` : '';
      slots.push(`${isBold ? `\\mathbf{${v}}` : v}_{${sub}}${sup}`);
      return String.fromCharCode(0xE000 + slots.length - 1);
    });
  }

  // `x ^ (1 / q)`: a parenthesised exponent is the whole superscript
  function caretGroups(src) {
    let i;
    while ((i = src.search(/\^\s*\(/)) >= 0) {
      const open = src.indexOf('(', i);
      let depth = 0, q = open;
      for (; q < src.length; q++) {
        if (src[q] === '(') depth++;
        else if (src[q] === ')' && --depth === 0) break;
      }
      if (q >= src.length) break;
      src = src.slice(0, i) + '^{' + src.slice(open + 1, q) + '}' + src.slice(q + 1);
    }
    return src;
  }

  function codeToTex(src, lenient = false, bold = null) {
    const slots = [];
    src = caretGroups(expand(src, lenient, bold, slots));
    if (/\.lean\b|\$|\\/.test(src) || src.length > 400) return null;
    if (!lenient && (LEAN.test(src) || src.length > 160)) return null;
    if (lenient) {
      src = src.replace(/\bfun\s+([^=]+?)\s*=>/g, '$1 ↦').replace(/=>/g, '⇒').replace(/:=/g, '≔');
    }
    // `∑ i < N, body` and `∑ i, body` put the binder under the sign
    let s = src.replace(/([∑∏⨆⨅])\s*([^,∑∏]{1,30}?),\s*/gu, (m, op, bind) => `${op}_{${/^[a-z](\s+[a-z])+$/.test(bind.trim()) ? bind.trim().split(/\s+/).join(',') : bind.trim()}} `);
    const out = [];
    let prevAtom = false;   // previous token was a letter/number/closing bracket (for spacing)
    let spaced = false;
    let prevOp = false;     // previous token was an operator name, which KaTeX spaces itself
    const braces = [];      // open braces: true for a script group, false for a set
    for (const m of s.matchAll(TOKEN)) {
      const [tok, word, num, subs, multi, sups, freeSub, space] = m;
      if (space !== undefined) { spaced = true; continue; }
      let tex, atom = false, opener = false, isOp = false;
      if (word !== undefined) {
        // a word, with an optional subscript: σ_i, σ_min, P_X, ‖·‖_F, λ_{i+j}
        // trailing subscript digits (`A₁`) and plain digits after one letter (`x2`) are maths
        const trail = (word.match(/[₀-₉]+$/) || [''])[0];
        const w = word.slice(0, word.length - trail.length);
        const trailTex = trail ? `_{${[...trail].map(c => SUB[c]).join('')}}` : '';
        if (/^\p{L}\d+$/u.test(w)) {
          if (spaced && prevAtom && !prevOp) out.push('\\,');
          out.push(w + trailTex);
          prevAtom = true; prevOp = false; spaced = false;
          continue;
        }
        const [named, sub] = w.split(/_(.*)/su);
        // expectation and probability: `E` with an operand after it (`E ‖G‖`, `≤ E σ_min(G)`,
        // `E [X]`, `E_ν g`), `P(…)`. A letter in the bold set is a matrix (`A + E`, `-E S`,
        // `(1 - P) Q`); without a bold set, only `E` and `P` opening a term are operators.
        if ((named === 'E' || named === 'P') && (sub === undefined || named === 'E') && !trail) {
          const mat = bold ? bold.has(named) : null;
          const rest = s.slice(m.index + tok.length);
          if (mat === false || (mat === null && !(prevAtom && !prevOp))) {
            if (named === 'E' ? /^\[|^\s+(?=\S)(?![+\-=≤≥<>,;)\]}·*\/^_•⁻ᴴ])/.test(rest) : /^\(/.test(rest)) {
              let subTex = '';
              if (sub !== undefined) {
                subTex = codeToTex(sub.replace(/^\{(.*)\}$/s, '$1'), lenient, bold);
                if (subTex === null) return null;
                subTex = `_{${subTex}}`;
              }
              if (spaced && prevAtom) out.push('\\,');
              out.push(named === 'E' ? `\\mathbb{E}${subTex}\\,` : '\\mathbb{P}');
              prevAtom = true; prevOp = true; spaced = false;
              continue;
            }
          }
        }
        // a product of letters written together, one of them Greek: `Lθ`, `θx`, `2θc`; a Greek
        // letter with `min`/`max` is subscripted: `μmax`
        if (sub === undefined && /^\p{L}{2,}$/u.test(w) && /[α-ωΑ-Ωϑϕϵ]/u.test(w) && !OPS[w]) {
          const mm = /^([α-ωΑ-Ωϑϕϵ])(min|max)$/u.exec(w);
          const letters = mm ? null : [...w];
          if (mm || letters.length <= 3) {
            if (spaced && prevAtom && !prevOp) out.push('\\,');
            const letter = c => bold && bold.has(c) ? `\\mathbf{${c}}` : c;
            out.push((mm ? `${mm[1]}_{\\${mm[2]}}` : letters.map(letter).join('')) + trailTex);
            prevAtom = true; prevOp = false; spaced = false;
            continue;
          }
        }
        const base = named.replace(/'+$/, '');
        const primes = named.slice(base.length);
        const mathy = ([...base].length === 1 || OPS[base]) && !base.includes('.') &&
          (sub === undefined || /^(\{[^}]*\}|[\p{L}\p{Nd}]+)$/u.test(sub)) && !/[₀-₉]/.test(named);
        if (!mathy) {                                                   // a Lean name
          if (!lenient) return null;
          out.push(spaced && prevAtom ? '\\,' : '', texName(w) + trailTex);
          prevAtom = true; prevOp = true; spaced = false;
          continue;
        }
        tex = (OPS[base] ?? (SYMBOLS[base] ?? (bold && bold.has(base) ? `\\mathbf{${base}}` : base))) + primes;
        isOp = !!OPS[base];
        if (sub !== undefined) {
          const inner = sub.startsWith('{') ? sub.slice(1, -1) : sub;
          const innerTex = inner.length > 1 && /^\p{L}+$/u.test(inner)
            ? (OPS[inner] ?? `\\mathrm{${inner}}`) : codeToTex(inner, lenient, bold);
          if (innerTex === null) return null;
          tex += `_{${innerTex}}`;
        }
        tex += trailTex;
        atom = true;
      } else if (num !== undefined) {
        tex = num; atom = true;
      } else if (subs !== undefined) {
        tex = `_{${[...subs].map(c => SUB[c]).join('')}}`;
        atom = prevAtom;                                  // `Aᵢ Kᵢ` is still a product
      } else if (sups !== undefined) {
        const parts = sups.replace(/⁻¹/g, '\u0001').split('').map(c => c === '\u0001' ? '-1' : SUP[c]);
        tex = `^{${parts.join('')}}`;
        atom = true;
      } else if (freeSub !== undefined) {
        const inner = freeSub.slice(1).replace(/^\{(.*)\}$/s, '$1');
        const innerTex = inner.length > 1 && /^\p{L}+$/u.test(inner) ? (OPS[inner] ?? `\\mathrm{${inner}}`) : codeToTex(inner, lenient, bold);
        if (innerTex === null) return null;
        // the Frobenius norm's subscript is a name, not a variable: ‖A‖_F
        tex = inner === 'F' && /\\\|$/.test(out[out.length - 1] || '') ? '_{\\mathsf{F}}' : `_{${innerTex}}`;
        atom = true;
      } else if (multi !== undefined) {
        tex = SYMBOLS[multi];
      } else {
        const c = tok;
        if ('_#%&~'.includes(c)) {
          if (!lenient) return null;
          out.push(c === '~' ? '\\sim ' : '\\' + c);
          prevAtom = false; spaced = false;
          continue;
        }
        const code = c.charCodeAt(0) - 0xE000;
        atom = c === ')' || c === ']' || c === '|';
        opener = c === '(' || c === '[';
        if (code >= 0 && code < slots.length) { tex = slots[code]; atom = true; }
        // a brace after `^` or `_` groups a script; any other is a set brace, `{x | x ≤ c}`
        else if (c === '{') { const g = /[\^_]$/.test(out[out.length - 1] || ''); braces.push(g); tex = g ? '{' : '\\{'; }
        else if (c === '}') tex = braces.pop() === false ? '\\}' : '}';
        else if (c === '*') tex = '\\,';
        else if (SYMBOLS[c] !== undefined) tex = SYMBOLS[c];
        else if (SUB[c]) tex = `_{${SUB[c]}}`;
        else if (/[\p{L}\p{N}]/u.test(c)) { if (!lenient) return null; tex = `\\text{${c}}`; }
        else tex = c;
      }
      // Lean application `κ ε`, `X u t`: a space between two atoms becomes a thin space
      if (spaced && prevAtom && atom && !prevOp && sups === undefined && freeSub === undefined) out.push('\\,');
      out.push(tex);
      prevAtom = atom;
      prevOp = isOp;
      spaced = false;
    }
    // `√x`, `√(…)`: \surd is a fine rendering on its own; prefer \sqrt for a parenthesised argument
    // adjacent scripts merge: `_{ψ}_{2}` -> `_{ψ2}`
    const G = '((?:[^{}]|\\{[^{}]*\\})*)';
    let tex = out.join('');
    for (const c of ['_', '\\^']) {
      tex = tex.replace(new RegExp(`${c}\\{${G}\\}${c}\\{${G}\\}`, 'g'), (m, a, b) => `${m[0]}{${a}${b}}`);
    }
    return sqrt(tex);
  }

  // `\surd (…)` -> `\sqrt{…}` with balanced brackets, `\surd x` -> `\sqrt{x}`
  function sqrt(tex) {
    let i;
    while ((i = tex.indexOf('\\surd ')) >= 0) {
      const j = i + 6;
      let k = j, arg;
      if (tex[j] === '(') {
        let depth = 0;
        for (k = j; k < tex.length; k++) {
          if (tex[k] === '(') depth++;
          else if (tex[k] === ')' && --depth === 0) break;
        }
        if (k >= tex.length) return tex.replace(/\\surd /g, '\\surd{}');
        arg = tex.slice(j + 1, k);
        k++;
      } else {
        const m = /^(?:\\[a-zA-Z]+(?:\{[^}]*\})? ?|[^\\\s])/.exec(tex.slice(j));
        if (!m) return tex.replace(/\\surd /g, '\\surd{}');
        arg = m[0];
        k = j + arg.length;
      }
      tex = tex.slice(0, i) + `\\sqrt{${arg}}` + tex.slice(k);
    }
    return tex;
  }

  root.codeToTex = codeToTex;
  if (typeof module !== 'undefined') module.exports = { codeToTex };
})(typeof window !== 'undefined' ? window : globalThis);
