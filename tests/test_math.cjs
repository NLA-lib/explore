'use strict';
const assert = require('node:assert/strict');
const { codeToTex, normalizeProbability: normalize } = require('../web/math.js');
const cases = [
  [String.raw`\mathbb{P}(f(X) > t)`, String.raw`\mathbb{P}[f(X) > t]`],
  [String.raw`\mathbb{P}\bigl(\|f(X)\| > t\bigr)`, String.raw`\mathbb{P}\bigl[\|f(X)\| > t\bigr]`],
  [String.raw`\mathbb{P}_{\mu(\theta)}\left(X\in[0,1]\mid Y=f(Z)\right)`, String.raw`\mathbb{P}_{\mu(\theta)}\left[X\in[0,1]\mid Y=f(Z)\right]`],
  [String.raw`\Pr(\{x:f(x)>t\}\subseteq A)`, String.raw`\mathbb{P}[\{x:f(x)>t\}\subseteq A]`],
  [String.raw`\operatorname{Pr}^{\nu}_{\mu}[X>t]`, String.raw`\mathbb{P}^{\nu}_{\mu}[X>t]`],
  [String.raw`\Pr\Bigl(X>t\Bigr)`, String.raw`\mathbb{P}\Bigl[X>t\Bigr]`],
  [String.raw`\Pr(X>t)+\Pr[Y>t]`, String.raw`\mathbb{P}[X>t]+\mathbb{P}[Y>t]`],
  [String.raw`\Pr(\Pr(X)>t)`, String.raw`\mathbb{P}[\mathbb{P}[X]>t]`],
];
for (const [input, expected] of cases) {
  assert.equal(normalize(input), expected, input);
  assert.equal(normalize(expected), expected, 'idempotent: ' + expected);
}
for (const input of [
  String.raw`P(X) + P\mathbf{x}`, String.raw`\mathbf{P}(X)`,
  String.raw`\text{\Pr(X)} + \texttt{\mathbb{P}(X)}`,
  String.raw`\verb|\Pr(X)| + \verb*+\mathbb{P}(X)+`,
  String.raw`\Pr(X`, String.raw`\Pr\left(X\bigr)`, String.raw`\Pr(X]`,
  String.raw`\mathbb{P}_{\mu(X`, String.raw`\Pr\{X>t\}`,
  String.raw`\Pr X`, String.raw`\Prime(X)`, String.raw`\\Pr(X)`,
]) assert.equal(normalize(input), input, 'preserved: ' + input);
assert.equal(codeToTex('P(X ≥ t)'), String.raw`\mathbb{P}[X\ge t]`);
assert.equal(codeToTex('Pr(X ≥ t)'), String.raw`\mathbb{P} [X\ge t]`);
assert.equal(codeToTex('P(X)', false, new Set(['P'])), String.raw`\mathbf{P}(X)`);
assert.equal(globalThis.normalizeProbability, normalize);
assert.equal(globalThis.codeToTex, codeToTex);
console.log('Probability notation tests passed');
