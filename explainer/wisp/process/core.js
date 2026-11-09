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

  const api = { LIB1, design, weakFit, differences, integral };
  if (typeof module === 'object' && module.exports) module.exports = api; else root.WispCore = api;
})(typeof self !== 'undefined' ? self : this);
