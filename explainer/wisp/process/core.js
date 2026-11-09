/* WISP process page: numerical core, shared by the page and the Node check (check_wisp_process.cjs).
   Mirrors build_design / WeakFit of the Python reference: trapezoid windows L in {1,2,4,8,16},
   unit-norm columns, orthogonal compression of [A | b], subset least squares on the compressed system. */
(function (root) {
  'use strict';
  const LIB1 = [u => 1, u => u, u => u * u, u => u * u * u, u => Math.sin(u), u => Math.cos(u)];

  function design(t, y, lengths = [1, 2, 4, 8, 16], lib = LIB1) {
    const phi = y.map(v => lib.map(f => f(v)));
    const p = lib.length, A = [], b = [], win = [];
    for (const L of lengths) for (let s = 0; s + L < t.length; s++) {
      const e = s + L, row = new Array(p).fill(0);
      for (let k = s; k < e; k++) {
        const h = (t[k + 1] - t[k]) / 2;
        for (let j = 0; j < p; j++) row[j] += h * (phi[k][j] + phi[k + 1][j]);
      }
      A.push(row); b.push(y[e] - y[s]); win.push([s, e]);
    }
    return { A, b, win, p };
  }

  // Householder QR of an m x n matrix (array of rows); returns the n x n upper block (rows of R).
  function qrR(M) {
    const m = M.length, n = M[0].length, R = M.map(r => r.slice());
    for (let k = 0; k < Math.min(m, n); k++) {
      let norm = 0;
      for (let i = k; i < m; i++) norm += R[i][k] * R[i][k];
      norm = Math.sqrt(norm);
      if (!norm) continue;
      const alpha = R[k][k] >= 0 ? -norm : norm;
      const v = new Array(m - k);
      for (let i = k; i < m; i++) v[i - k] = R[i][k];
      v[0] -= alpha;
      let vv = 0; for (const x of v) vv += x * x;
      if (!vv) continue;
      for (let j = k; j < n; j++) {
        let s = 0; for (let i = k; i < m; i++) s += v[i - k] * R[i][j];
        s = 2 * s / vv;
        for (let i = k; i < m; i++) R[i][j] -= s * v[i - k];
      }
    }
    return R.slice(0, n).map((r, i) => r.map((x, j) => (j < i ? 0 : x)));
  }

  function weakFit(A, b) {
    const p = A[0].length;
    const norms = Array.from({ length: p }, (_, j) => Math.sqrt(A.reduce((s, r) => s + r[j] * r[j], 0)));
    const R = qrR(A.map((r, i) => [...r.map((x, j) => x / (norms[j] || 1)), b[i]]));
    const bnorm2 = b.reduce((s, x) => s + x * x, 0);
    const cache = new Map();
    function solve(support) {
      const S = [...support].sort((a, c) => a - c), key = S.join(',');
      if (cache.has(key)) return cache.get(key);
      const rhs = R.map(r => r[p]);
      let out;
      if (!S.length) out = { coef: [], sse: rhs.reduce((s, x) => s + x * x, 0) };
      else {
        const Q = qrR(R.map((r, i) => [...S.map(j => r[j]), rhs[i]]));
        const k = S.length, z = new Array(k).fill(0);
        for (let i = k - 1; i >= 0; i--) {
          let s = Q[i][k];
          for (let j = i + 1; j < k; j++) s -= Q[i][j] * z[j];
          z[i] = Q[i][i] ? s / Q[i][i] : 0;
        }
        out = { coef: z.map((x, i) => x / (norms[S[i]] || 1)), sse: Q[k][k] * Q[k][k], terms: S };
      }
      cache.set(key, out);
      return out;
    }
    return { p, bnorm2, solve, sse: S => solve(S).sse };
  }

  // Finite differences of neighbouring observations (scene 03).
  const differences = (t, y, L = 1) => t.slice(0, t.length - L).map((_, i) => ({ t: (t[i] + t[i + L]) / 2, d: (y[i + L] - y[i]) / (t[i + L] - t[i]) }));

  // Trapezoid integral of f(u(t)) between two observation indices (scene 04), as in the design rows.
  function integral(t, y, s, e, f) {
    let v = 0;
    for (let k = s; k < e; k++) v += (t[k + 1] - t[k]) / 2 * (f(y[k]) + f(y[k + 1]));
    return v;
  }

  // The stop statistic of one candidate column j given support S, spelled out:
  // q = the part of column j that S cannot already produce, scaled to length 1 (one number per window);
  // z = q·b, so the SSE drops by exactly z² when j is added (Δ_actual);
  // every measurement i enters z with net weight w_i = Σ q over windows ending at i − Σ q over windows starting at i,
  // so under pure noise Var(z) = Σ w_i² σ̂_i² (Δ_noise), and ρ = z² / Var(z).
  function noiseTest(A, b, win, variance, S, j) {
    const n = A.length, k = S.length, g = A.map(r => r[j]);
    let r = g.slice();
    if (k) {
      const M = S.map(a => S.map(c2 => { let s = 0; for (let i = 0; i < n; i++) s += A[i][a] * A[i][c2]; return s; }));
      const rhs = S.map(a => { let s = 0; for (let i = 0; i < n; i++) s += A[i][a] * g[i]; return s; });
      for (let p = 0; p < k; p++) for (let a = 0; a < k; a++) { if (a === p) continue; const f = M[a][p] / M[p][p]; for (let c2 = 0; c2 < k; c2++) M[a][c2] -= f * M[p][c2]; rhs[a] -= f * rhs[p]; }
      const beta = rhs.map((v, p) => v / M[p][p]);
      r = g.map((x, i) => x - S.reduce((s, a, p) => s + beta[p] * A[i][a], 0));
    }
    const nr = Math.hypot(...r), q = r.map(x => x / nr);
    let z = 0; for (let i = 0; i < n; i++) z += q[i] * b[i];
    const w = new Array(variance.length).fill(0);
    win.forEach(([s, e], i) => { w[e] += q[i]; w[s] -= q[i]; });
    let v = 0; for (let i = 0; i < w.length; i++) v += w[i] * w[i] * variance[i];
    return { z, actual: z * z, noise: v, sd: Math.sqrt(v), ratio: z * z / v, w };
  }
  const api = { LIB1, design, weakFit, differences, integral, noiseTest };
  if (typeof module === 'object' && module.exports) module.exports = api; else root.WispCore = api;
})(typeof self !== 'undefined' ? self : this);
