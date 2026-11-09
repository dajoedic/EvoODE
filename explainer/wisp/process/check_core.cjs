// Node check: the browser core reproduces the Python weak-space numbers of the logistic example.
const fs = require('fs'), path = require('path');
const C = require('./core.js');
const D = JSON.parse(fs.readFileSync(path.join(__dirname, 'data.json'), 'utf8')).logistic;
const t = D.t, y = D.y.map(r => r[0]);
const { A, b } = C.design(t, y);
let bad = 0;
const rel = (a, c) => Math.abs(a - c) / Math.max(Math.abs(c), 1e-300);
const check = (what, a, c, tol = 1e-8) => { if (!(rel(a, c) <= tol)) { bad++; console.log('MISMATCH', what, a, c); } };
check('windows', A.length, D.windows, 0);
D.window_rows.forEach((r, i) => { const k = D.window_rows.indexOf(r); });
const fit = C.weakFit(A, b);
check('bnorm2', fit.bnorm2, D.path.b_norm2[0]);
const idx = n => D.names.indexOf(n);
D.path.weak.forEach((st, i) => {
  const S = st[0].terms.map(idx), s = fit.solve(S);
  st[0].coefficients.forEach((c, j) => check(`state ${i} coef ${j}`, s.coef[j], c, 1e-7));
  check(`state ${i} sse`, s.sse, st[0].sse, 1e-7);
});
D.path.steps.forEach((step, i) => {
  const before = D.path.states[i][0].map(idx);
  step.gains.forEach(g => check(`step ${step.step} gain ${g.term}`, (fit.sse(before) - fit.sse([...before, idx(g.term)])) / fit.bnorm2, g.gain, 1e-6));
});
console.log(bad ? `${bad} mismatches` : 'core reproduces Python weak space: OK');
process.exit(bad ? 1 : 0);
