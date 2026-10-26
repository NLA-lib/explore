+++
title = "Stochastic Lanczos quadrature as averaged Gauss quadrature"
authors = ["NLA-lib"]
status = "draft"
date = "2026-10-26"
abstract = """Stochastic Lanczos quadrature (SLQ) estimates a spectral sum $\\operatorname{tr} f(\\mathbf{A})$, or the whole spectral density of $\\mathbf{A}$, by running a few Lanczos steps from each of $m$ random probes. NLAlib defines it as what it is mathematically: the Girard–Hutchinson estimator with each quadratic form replaced by the Gauss rule of the probe's spectral measure. This report explains how the library builds that identification from the theory of orthogonal polynomials, how the trace and spectral-density error bounds then split into a sampling term and a quadrature term, and how the Radau, Lobatto and minimax-error results sharpen the quadrature term."""
results = [
  "spectral-measure",
  "orthogonal-polynomial-recurrence",
  "orthogonal-polynomial-existence",
  "orthogonal-polynomial-zeros",
  "gauss-quadrature",
  "gauss-quadrature-uniqueness",
  "lanczos-orthogonal-polynomials",
  "lanczos-jacobi-matrix",
  "lanczos-gauss-quadrature",
  "golub-welsch",
  "stochastic-lanczos-quadrature-error",
  "stochastic-lanczos-quadrature-tail",
  "probe-spectral-measure-unbiased",
  "spectral-density-kolmogorov-tail",
  "spectral-density-lipschitz-tail",
  "gauss-quadrature-remainder",
  "gauss-radau-quadrature",
  "gauss-radau-remainder",
  "gauss-lobatto-quadrature",
  "gauss-lobatto-remainder",
  "gauss-radau-jacobi-matrix",
  "best-approximation-existence",
  "jackson-lipschitz",
  "bernstein-ellipse-approx",
]
declarations = [
  "NLAlib.spectralMeasure",
  "NLAlib.gaussQuadrature",
  "NLAlib.lanczosQuadrature",
  "NLAlib.slq",
  "NLAlib.probeSpectralMeasure",
  "NLAlib.slqMeasure",
  "NLAlib.minimaxError",
  "NLAlib.radauQuadrature",
  "NLAlib.lobattoQuadrature",
  "Matrix.IsHermitian.exists_re_quadForm_cfc_sub_re_star_dotProduct_lanczosFA_eq",
  "NLAlib.integral_radauQuadrature_le_re_quadForm_cfc_of_iteratedDeriv_nonneg",
  "NLAlib.re_quadForm_cfc_le_integral_radauQuadrature_of_iteratedDeriv_nonneg",
  "NLAlib.re_slq_le_re_girardHutchinson_cfc_of_iteratedDeriv_nonneg",
  "NLAlib.re_girardHutchinson_cfc_le_re_slq_of_iteratedDeriv_nonpos",
]
related = []

# the reviewed version of each cited statement ({{statement}}): build.py flags a change
[statements]
"Matrix.IsHermitian.lanczosQuadrature_eq_gaussQuadrature" = "f4c97e40d6b12c92c1dec77e92f8f32373ea491f070699f6ccd3e99e3a60da8c"
"NLAlib.spectralMeasure_jacobiMatrix" = "ceb6df6875be32f961528872234cb9ed98af5b81880b3abf8eb2fdbba407218c"
"Matrix.IsHermitian.norm_trace_cfc_sub_slq_le_of_isUniformApproxOn" = "0586ed6e1990ff460d22054b54989ec41155b55ba63a0dcf932a6cda54fdbb82"
"NLAlib.measureReal_abs_trace_cfc_sub_slq_ge_le_of_lipschitzOnWith" = "fb36da0082aa7e84ed2833e5fa8032bb7cd80ea0cdb613ef275ed36adbb6060c"
"NLAlib.measureReal_exists_abs_integral_empiricalSpectralMeasure_sub_integral_slqMeasure_gt_le" = "d8c2cd4a7070cac6e3a5032e686932d454fd22d8015c49e74477d9eb95f50ac2"
"NLAlib.re_slq_le_re_girardHutchinson_cfc_of_iteratedDeriv_nonneg" = "9b86dd30f86d3cd393bbe4a48fa1b75a77eb7957459512ff5d322bf516989351"
"Matrix.IsHermitian.norm_trace_cfc_sub_slq_le_of_continuousOn" = "eefe80cb78aec2feff9b57df650655f75e9906753c0448104804c75270a902cb"
+++

## Introduction

Many computations in data science and physics need a spectral sum $\operatorname{tr} f(\mathbf{A})$ of a large Hermitian matrix that is available only through products $\mathbf{x} \mapsto \mathbf{A}\mathbf{x}$: the log-determinant ($f = \log$), the number of eigenvalues in an interval ($f$ an indicator), the Estrada index ($f = \exp$), or the spectral density itself, the empirical spectral measure $\nu_{\mathbf{A}} = \lvert n\rvert^{-1}\sum_k \delta_{\lambda_k(\mathbf{A})}$ tested against a class of functions. Stochastic Lanczos quadrature combines two classical ideas [UbaruChenSaad2017, §3]. The Girard–Hutchinson estimator replaces the trace by an average of quadratic forms $\boldsymbol{\omega}_j^{\mathsf{H}}f(\mathbf{A})\boldsymbol{\omega}_j$ over random probes; and each quadratic form is an integral against a spectral measure, which $q$ steps of the Lanczos process approximate by Gauss quadrature [GolubMeurant2010, Ch. 6].

NLAlib takes the second idea as the definition. The estimate [[NLAlib.slq]] is

$$\mathsf{slq}(\mathbf{A}, f, \mathbf{\Omega}, q) = \frac{1}{m}\sum_{j=1}^m \int f\,d\,\mathsf{gaussQuadrature}(\mu_{\mathbf{A},\boldsymbol{\omega}_j}, q),$$

where $\mu_{\mathbf{A},\mathbf{b}}$ is the spectral measure of $\mathbf{A}$ and $\mathbf{b}$ ([[NLAlib.spectralMeasure]]: an atom at each eigenvalue $x$ of weight $\|\mathbf{P}_x\mathbf{b}\|^2$) and [[NLAlib.gaussQuadrature]] is the $q$-point Gauss rule of a measure, defined from its orthogonal polynomials with no reference to matrices. That SLQ is what the Lanczos algorithm computes is then a theorem, [[Matrix.IsHermitian.slq_eq_sum_lanczosFA]]. The payoff of this choice is that every error bound for SLQ becomes "a sampling error plus an average of Gauss-rule errors", and the Gauss-rule errors are statements about one measure on an interval, proved once and reused for Lanczos, SLQ, spectral densities and CG.

The material comes from four parts of the library: the structure theory of orthogonal polynomials and the Gauss rule; the identification of Lanczos with Gauss quadrature, including Golub–Welsch; SLQ for traces and for spectral densities; and the remainder theory (Gauss, Radau, Lobatto) and best-approximation restatements that refine the quadrature term.

## Main results

### Lanczos quadrature is Gauss quadrature

The rule that $q$ Lanczos steps from $\mathbf{b}$ produce, [[NLAlib.lanczosQuadrature]], is defined as the spectral measure of the compression of $\mathbf{A}$ to the Krylov space $\mathcal{K}_q(\mathbf{A}, \mathbf{b})$: atoms at the Ritz values. The first bridge identifies it with the Gauss rule of $\mu_{\mathbf{A},\mathbf{b}}$, for every $q$ and every Hermitian $\mathbf{A}$ over $\mathbb{R}$ or $\mathbb{C}$.

{{statement Matrix.IsHermitian.lanczosQuadrature_eq_gaussQuadrature}}

Around it, the library proves that the Lanczos vectors are the normalised orthogonal polynomials $\pi_j(\mathbf{A})\mathbf{b}$ of $\mu_{\mathbf{A},\mathbf{b}}$ ([[result:lanczos-orthogonal-polynomials]]) and that the Lanczos tridiagonal is the Jacobi matrix of $\mu_{\mathbf{A},\mathbf{b}}$ ([[result:lanczos-jacobi-matrix]]), both padded by zeros past the Krylov grade. Conversely, for an arbitrary finite measure on an interval, the Gauss rule is read off its Jacobi matrix.

{{statement NLAlib.spectralMeasure_jacobiMatrix}}

### Trace estimation

The error of SLQ splits exactly as the definition suggests: the Girard–Hutchinson error of the same probes, plus a quadrature term that depends only on how well $f$ is approximated by polynomials of degree below $2q$ on an interval containing the spectrum.

{{statement Matrix.IsHermitian.norm_trace_cfc_sub_slq_le_of_isUniformApproxOn}}

Specialisations replace $\varepsilon$ by a rate: $\pi L(a' - a)/(2q + 3)$ per unit of probe mass for $L$-Lipschitz $f$ with $q + 1$ steps ([[Matrix.IsHermitian.norm_trace_cfc_sub_slq_le_of_lipschitzOnWith]]), a geometric rate $4M/(\rho^{2q+1}(\rho - 1))$ for $f$ analytic and bounded by $M$ on a Bernstein ellipse ([[Matrix.IsHermitian.norm_trace_cfc_sub_slq_le_of_differentiableOn]]), and the best possible polynomial term $2E_{2q+1}(f; [a, a'])$ for continuous $f$ (below). With probes whose entries are independent, sub-Gaussian with variance proxy $c$ and of unit second moment, the sampling term has a Hanson–Wright tail; the quadrature term stays inside the event, since it is random through $\|\mathbf{\Omega}\|_{\mathsf{F}}^2$.

{{statement NLAlib.measureReal_abs_trace_cfc_sub_slq_ge_le_of_lipschitzOnWith}}

### Spectral densities

For densities the library works with two measures built from the same probes, each scaled by $1/(\lvert n\rvert m)$: the probe spectral measure [[NLAlib.probeSpectralMeasure]], the average of the probes' spectral measures, and the SLQ estimate [[NLAlib.slqMeasure]], the average of their Gauss rules. The first is the exact-quadrature limit of the second ([[Matrix.IsHermitian.slqMeasure_eq_probeSpectralMeasure_of_card_le]]), it is unbiased for $\nu_{\mathbf{A}}$ under isotropic probes ([[result:probe-spectral-measure-unbiased]]), and the two match their first $2q$ moments ([[NLAlib.matchesMoments_probeSpectralMeasure_slqMeasure]]). Note that [[NLAlib.slqMeasure]] is not itself the Gauss rule of the probe spectral measure: it has up to $mq$ nodes. The main density bound holds simultaneously for all $L$-Lipschitz test functions.

{{statement NLAlib.measureReal_exists_abs_integral_empiricalSpectralMeasure_sub_integral_slqMeasure_gt_le}}

The factor $\lvert n\rvert$ in the exponent means that for large matrices few probes are needed; the asymptotic form ([[NLAlib.exists_forall_measureReal_exists_abs_integral_empiricalSpectralMeasure_sub_integral_slqMeasure_gt_le]]) asks for $m \ge C c^2\log(2\lvert n\rvert/\delta)/(\lvert n\rvert\tau^2)$ probes. For probes $\sqrt{\lvert n\rvert}\,\mathbf{u}_j$ with $\mathbf{u}_j$ independent and uniform on the sphere, both measures have mass exactly one, the $\lvert f(b)\rvert$ term and the factor $1 + \tau$ disappear, the exponent becomes $-m(\lvert n\rvert + 2)\tau^2$ with no unknown constant, and the bound is of Wasserstein-1 type ([[NLAlib.measureReal_exists_abs_integral_empiricalSpectralMeasure_sub_integral_slqMeasure_gt_le_of_hasLaw_uniformSphereVector]]). A mass-normalised variant for sub-Gaussian probes is [[NLAlib.measureReal_exists_abs_integral_empiricalSpectralMeasure_sub_integral_smul_slqMeasure_gt_le]].

### The sign of the bias, and two-sided bounds

Because the Gauss remainder has a sign when the derivative of order $2q$ does, SLQ sits on a known side of the Girard–Hutchinson estimate of the same probes, for every test matrix.

{{statement NLAlib.re_slq_le_re_girardHutchinson_cfc_of_iteratedDeriv_nonneg}}

The reverse inequality holds when $f^{(2q)} \le 0$, for example $f = \log$ on $[a, a']$ with $a > 0$ ([[NLAlib.re_girardHutchinson_cfc_le_re_slq_of_iteratedDeriv_nonpos]]). For a single quadratic form $\mathbf{b}^{\mathsf{H}}f(\mathbf{A})\mathbf{b}$, the Gauss–Radau rules with a prescribed node at either end of $[a, a']$ and the Gauss–Lobatto rule with both give the other side, under sign conditions on $f^{(2q+1)}$ and $f^{(2q+2)}$ (see How the proofs work).

### Best approximation

Every bound above that is stated for an arbitrary approximating polynomial has a restatement in terms of the minimax error [[NLAlib.minimaxError]] $E_n(f; s)$, the error of best uniform approximation by polynomials of degree at most $n$. For SLQ this is the cleanest form of the quadrature term:

{{statement Matrix.IsHermitian.norm_trace_cfc_sub_slq_le_of_continuousOn}}

## How the proofs work

### From moments to the Gauss rule

The base layer is about a finite measure $\mu$ supported in an interval $[a, b]$. The monic orthogonal polynomials are defined by the Stieltjes procedure, so the three-term recurrence $\pi_{k+2} = (x - \alpha_{k+1})\pi_{k+1} - \beta_{k+1}\pi_k$ holds by definition ([[result:orthogonal-polynomial-recurrence]]) and orthogonality is the theorem ([[result:orthogonal-polynomial-existence]]); both hold for every $k$, degenerate measures included, which is what lets the matrix-level statements hold past the Krylov grade without case splits. When $\mu$ is positive definite up to degree $k$, $\pi_k$ has $k$ real zeros ([[result:orthogonal-polynomial-zeros]]), and the Gauss nodes are its distinct real zeros. The Gauss rule is the interpolatory rule at those nodes, with weights $\int\ell_x\,d\mu$ for the Lagrange basis polynomials $\ell_x$.

Exactness through degree $2k - 1$ is the usual division argument: write $p = \pi_k s + r$ with $\deg s, \deg r < k$; the first term integrates to zero against $\mu$ by orthogonality and vanishes at the nodes, and the interpolatory rule is exact on $r$ ([[NLAlib.IsOrthogonalPolynomial.integral_eval_eq_sum]], packaged as [[NLAlib.matchesMoments_gaussQuadrature]]). The other key fact is uniqueness: a finite measure carried by at most $k$ points that matches the first $2k$ moments of $\mu$ is the $k$-point Gauss rule ([[result:gauss-quadrature-uniqueness]]). Moment matching also transfers uniform approximation: if $\mu$ and $\nu$ on $[a, b]$ match $N$ moments and a polynomial of degree below $N$ is within $\varepsilon$ of $f$ there, then $\lvert\int f\,d\mu - \int f\,d\nu\rvert \le (\mu(\mathbb{R}) + \nu(\mathbb{R}))\varepsilon$ ([[NLAlib.MatchesMoments.abs_integral_sub_integral_le_of_isUniformApproxOn]]). With the Gauss rule's mass equal to $\mu(\mathbb{R})$, this gives the basic Gauss-rule error bound $2\varepsilon\,\mu(\mathbb{R})$ ([[NLAlib.abs_integral_sub_integral_gaussQuadrature_le_of_isUniformApproxOn]]), from which every quadrature term in this report descends.

### Lanczos is Gauss, by uniqueness

The proof of [[Matrix.IsHermitian.lanczosQuadrature_eq_gaussQuadrature]] does not go through the orthogonal polynomials at all. The integral of $f$ against the Lanczos rule is the Lanczos-FA quadratic form $\mathbf{b}^{\mathsf{H}}\mathsf{lanczosFA}(\mathbf{A}, f, \mathbf{b}, q)$, which is exact for polynomials of degree below $2q$ ([[Matrix.IsHermitian.star_dotProduct_lanczosFA_eval]]); this is the classical fact that Lanczos-FA itself is exact only through degree $q - 1$ but its quadratic form through degree $2q - 1$. So the Lanczos rule matches $2q$ moments of $\mu_{\mathbf{A},\mathbf{b}}$ ([[Matrix.IsHermitian.matchesMoments_lanczosQuadrature]]); it lives on the at most $q$ Ritz values; and uniqueness of the Gauss rule finishes the proof. The structural statements, that Lanczos vectors are orthogonal polynomials and the tridiagonal is the Jacobi matrix, are proved separately in the Lanczos-polynomial layer and are what identify the Ritz values with the Gauss nodes below the grade ([[NLAlib.HasOrthonormalCols.gaussNodes_spectralMeasure_eq]]).

Golub–Welsch ([[NLAlib.spectralMeasure_jacobiMatrix]]) is then obtained by running the matrix result backwards on a small model. Let $\nu$ be the $(k+1)$-point Gauss rule of $\mu$ and apply Lanczos to the diagonal matrix of its nodes, started from the vector of square-rooted weights. That matrix's spectral measure is $\nu$ itself, so its Lanczos rule is the Gauss rule of $\nu$, which is $\nu$ by uniqueness. Its Lanczos tridiagonal is the Jacobi matrix of $\nu$, and the Jacobi matrix depends only on the first $2k + 2$ moments ([[NLAlib.MatchesMoments.jacobiMatrix_eq]]), which $\nu$ shares with $\mu$. Reading the Lanczos rule off the tridiagonal, as the spectral measure of $(\mathbf{T}, \|\mathbf{b}\|\mathbf{e}_0)$ ([[Matrix.IsHermitian.lanczosQuadrature_succ_eq]]; with an eigendecomposition of $\mathbf{T}$ this is [[Matrix.IsHermitian.lanczosQuadrature_succ_eq_sum]]), gives the statement.

### SLQ for traces

Every SLQ trace bound is the corresponding single-vector Lanczos bound, applied probe by probe and averaged. The quadratic-form errors are $\le 2\varepsilon\|\boldsymbol{\omega}_j\|^2$ (uniform approximation), $\pi L(a' - a)\|\boldsymbol{\omega}_j\|^2/(2q + 3)$ for Lipschitz $f$ ([[Matrix.IsHermitian.norm_star_dotProduct_cfc_mulVec_sub_lanczosFA_le_of_lipschitzOnWith]], from Jackson's theorem in degree $2q + 1$ [ChenTrogdonUbaru2022, Appendix C, Theorem 38]) or the analytic rate; summing over $j$ turns $\sum_j\|\boldsymbol{\omega}_j\|^2$ into $\|\mathbf{\Omega}\|_{\mathsf{F}}^2$, and the triangle inequality against the Girard–Hutchinson estimate gives the split. The tails then need no new probability: on the event that the SLQ error exceeds $\tau$ plus the quadrature term, the Girard–Hutchinson error exceeds $\tau$, and the latter has the Hanson–Wright tail of [[result:girard-hutchinson-tail]]. This inclusion of events is also why no measurability of the SLQ estimate in the probes is required.

### SLQ for spectral densities

The density bound has three ingredients. First, the probe spectral measure of a set $S$ is a Girard–Hutchinson estimate of $\operatorname{tr}\mathbf{1}_S(\mathbf{A})/\lvert n\rvert$, the trace of a spectral projector divided by $\lvert n\rvert$ ([[NLAlib.probeSpectralMeasure_real]]). Its Frobenius and spectral norms are at most $\lvert n\rvert^{-1/2}$ and $\lvert n\rvert^{-1}$, so Hanson–Wright gives a tail with $m\lvert n\rvert$ in the exponent ([[NLAlib.measureReal_abs_empiricalSpectralMeasure_real_sub_probeSpectralMeasure_real_ge_le]]); a union bound over the at most $\lvert n\rvert$ eigenvalues controls the distribution functions everywhere ([[result:spectral-density-kolmogorov-tail]]). Second, a deterministic lemma converts closeness of distribution functions into closeness of integrals of Lipschitz functions, with the error $(\lvert f(b)\rvert + L(b - a))\tau$ ([[Matrix.IsHermitian.abs_integral_empiricalSpectralMeasure_sub_integral_probeSpectralMeasure_le]]); the same event bounds the random mass by $1 + \tau$. Third, the quadrature term between the probe measure and the SLQ measure is the Gauss-rule Lipschitz bound per probe, averaged ([[Matrix.IsHermitian.abs_integral_probeSpectralMeasure_sub_integral_slqMeasure_le_of_lipschitzOnWith]]). Because the event in the first step does not depend on $f$, the bound holds for all Lipschitz test functions at once.

For sphere probes the only change is in the first step. The squared norm of the projection of a uniform unit vector onto a $k$-dimensional subspace has a $\mathrm{Beta}(k/2, (n - k)/2)$ law ([[result:sphere-projection-beta]]), centred Beta laws are sub-Gaussian with proxy $1/(4(\alpha + \beta + 1))$ [MarchalArbel2017, Theorem 1] ([[result:beta-subgaussian]]), and Hoeffding's inequality for the $m$ independent probes gives the tail $2\exp(-m(n + 2)\tau^2)$ ([[result:sphere-projection-tail]]).

### Remainders, Radau and Lobatto, and the sign of the bias

The derivative form of the Gauss error,

$$\int f\,d\mu - \int f\,d\,\mathsf{gaussQuadrature}(\mu, k) = \frac{f^{(2k)}(\xi)}{(2k)!}\int\pi_k^2\,d\mu,\qquad \xi \in (a, b),$$

is proved through Hermite interpolation at the Gauss nodes, each node doubled ([[result:gauss-quadrature-remainder]]). The interpolant has degree below $2k$, so the rule integrates it exactly; the Hermite remainder is $f^{(2k)}(\xi_x)\pi_k(x)^2/(2k)!$; and a mean-value step for an integrand of one sign, which needs no measurability of $x \mapsto \xi_x$, collects it into a single $\xi$ ([[NLAlib.exists_integral_sub_integral_eval_eq]]). The hypotheses are $f$ continuous on $[a, b]$ and $C^{2k}$ on the open interval, so endpoint singularities are allowed. At the matrix level, $\int\pi_q^2\,d\mu_{\mathbf{A},\mathbf{b}} = \|\pi_q(\mathbf{A})\mathbf{b}\|^2$ ([[Matrix.IsHermitian.exists_re_quadForm_cfc_sub_re_star_dotProduct_lanczosFA_eq]]). When $f^{(2q)} \ge 0$ the remainder is nonnegative for each probe's spectral measure; summing over the probes is the whole proof of [[NLAlib.re_slq_le_re_girardHutchinson_cfc_of_iteratedDeriv_nonneg]].

The Gauss–Radau rule [[NLAlib.radauQuadrature]] with prescribed node $c \in \{a, b\}$ and $k$ free nodes is the interpolatory rule at $c$ and the Gauss nodes of the modified measure $\lvert x - c\rvert\,d\mu$; it is exact through degree $2k$ ([[result:gauss-radau-quadrature]]), and its remainder carries the factor $\int(x - c)\tilde\pi_k^2\,d\mu$, whose sign is fixed by the side on which $c$ lies ([[result:gauss-radau-remainder]]). The Lobatto rule [[NLAlib.lobattoQuadrature]] prescribes both endpoints, is exact through degree $2k + 1$ ([[result:gauss-lobatto-quadrature]]), and its remainder has the factor $\int(x - a)(x - b)\hat\pi_k^2\,d\mu \le 0$ ([[result:gauss-lobatto-remainder]]). For quadratic forms with $f^{(2q+1)} \ge 0$ on $(a, a')$, the left Radau rule is a lower bound ([[NLAlib.integral_radauQuadrature_le_re_quadForm_cfc_of_iteratedDeriv_nonneg]]) and the right Radau rule an upper bound ([[NLAlib.re_quadForm_cfc_le_integral_radauQuadrature_of_iteratedDeriv_nonneg]]); the signs reverse for $f^{(2q+1)} \le 0$ ([[NLAlib.re_quadForm_cfc_le_integral_radauQuadrature_of_iteratedDeriv_nonpos|left]], [[NLAlib.integral_radauQuadrature_le_re_quadForm_cfc_of_iteratedDeriv_nonpos|right]]), and the Lobatto rule bounds from above when $f^{(2q+2)} \ge 0$ ([[NLAlib.re_quadForm_cfc_le_integral_lobattoQuadrature_of_iteratedDeriv_nonneg]]) and from below when $f^{(2q+2)} \le 0$ ([[NLAlib.integral_lobattoQuadrature_le_re_quadForm_cfc_of_iteratedDeriv_nonpos]]). For $f(x) = 1/x$ on $[a, a']$ with $a > 0$, whose derivatives alternate in sign, these theorems and the Gauss remainder say that the Gauss and right Radau rules bound $\mathbf{b}^{\mathsf{H}}\mathbf{A}^{-1}\mathbf{b}$ from below and the left Radau and Lobatto rules from above [GolubMeurant2010, Ch. 6]. The Radau rule is also computable by Lanczos: below the grade it is $\|\mathbf{b}\|^2 f(\tilde{\mathbf{J}})_{0,0}$ for the Lanczos tridiagonal with its last diagonal entry modified ([[Matrix.IsHermitian.integral_radauQuadrature_spectralMeasure]]), through a Golub–Welsch theorem for the Radau Jacobi matrix ([[result:gauss-radau-jacobi-matrix]]) [Golub1973, §7].

### Minimax-error restatements

The restatements in terms of $E_n(f; s)$ all follow one pattern. A best approximation exists for continuous $f$ on a compact set ([[result:best-approximation-existence]]), so [[NLAlib.exists_degree_le_isUniformApproxOn_minimaxError]] produces a polynomial of degree at most $2q + 1$ within $E_{2q+1}(f; [a, a'])$ of $f$, which is fed to the uniform-approximation version of the bound with $q + 1$ Gauss nodes. This is how the Gauss rule ([[NLAlib.abs_integral_sub_integral_gaussQuadrature_le_of_continuousOn]]), the Lanczos quadratic form ([[Matrix.IsHermitian.norm_star_dotProduct_cfc_mulVec_sub_lanczosFA_le_of_continuousOn]]) and SLQ, in error and in tail form ([[NLAlib.measureReal_abs_trace_cfc_sub_slq_ge_le_of_continuousOn]]), are stated with $E_{2q+1}$. In the other direction, Jackson's theorem ([[result:jackson-lipschitz]]) and the Bernstein-ellipse bound ([[result:bernstein-ellipse-approx]]) are stated as upper bounds on $E_N$, so any concrete rate composes with the minimax forms.

## How the results fit together

{{diagram}}

The dependency picture has three layers. At the bottom are statements about a single finite measure on an interval: orthogonal polynomials, the Gauss rule with its exactness, uniqueness and error bounds, the remainders, and the Radau and Lobatto rules. None of them mentions a matrix. The middle layer is the bridge [[NLAlib.integral_spectralMeasure]], $\int f\,d\mu_{\mathbf{A},\mathbf{b}} = \operatorname{Re}\mathbf{b}^{\mathsf{H}}f(\mathbf{A})\mathbf{b}$, together with Lanczos = Gauss and Golub–Welsch: it turns each measure statement into a statement about quadratic forms and Lanczos. The top layer averages over probes. The trace estimator [[NLAlib.slq]] and the density estimator [[NLAlib.slqMeasure]] are both averages of the same Gauss rules, so their bounds share the quadrature term, and differ in the sampling term: Girard–Hutchinson for $f(\mathbf{A})$ for traces, Girard–Hutchinson for the spectral projectors $\mathbf{1}_S(\mathbf{A})/\lvert n\rvert$, uniformly over $S$, for densities.

Two structural choices make the layers compose. First, the measure-level theorems are total: the Gauss rule is defined for every $k$, and past the number of support points it is the measure itself, so Lanczos statements hold at and past the Krylov grade, where Lanczos terminates. Second, the probe spectral measure is the exact-quadrature limit of the SLQ measure, so each density bound is a sampling bound for the probe measure plus a quadrature bound between the two, and the quadrature bound is deterministic.

## What is not covered

- **Bias in expectation.** The sign results compare SLQ with Girard–Hutchinson for every test matrix; there is no statement of $\lvert\operatorname{tr} f(\mathbf{A}) - \mathbb{E}\,\mathsf{slq}\rvert$, which would need measurability of the Gauss rule of $\mu_{\mathbf{A},\mathbf{b}}$ in $\mathbf{b}$.
- **Two-sided SLQ.** The Radau and Lobatto bounds are proved for one quadratic form at a time. There is no Radau or Lobatto variant of the SLQ estimator, and so no two-sided SLQ bound per probe. The Lobatto rule has no Jacobi-matrix (Golub–Welsch) form yet, so unlike the Radau rule it is not shown to be computable from Lanczos output.
- **Variance and mean-square error.** The trace results are tail bounds with the Hanson–Wright constant; there is no exact variance or mean-square error of SLQ.
- **Other probe laws and other test classes.** The density tails cover independent sub-Gaussian entries and independent sphere probes; Haar-frame (orthonormal, dependent) probes are covered by unbiasedness only. Density bounds for analytic test functions, and the kernel polynomial method, are not stated.
- **Finite precision.** Everything is in exact arithmetic. Lanczos in floating point loses orthogonality, and the identification with Gauss quadrature, as well as every bound here, assumes exact Lanczos.
- **Sharper rates.** The Lipschitz quadrature term $\pi L(b - a)/(2q + 3)$ comes from Jackson's theorem with an explicit constant; the library does not claim it is optimal, and the comparison with the constants of [ChenTrogdonUbaru2021] and [ChenTrogdonUbaru2025] is left to the literature pass. Several citation locators in the underlying docstrings are still marked to be checked.
