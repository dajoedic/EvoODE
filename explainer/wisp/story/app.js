// WISP story: page navigation (one statement per page) and three stages (lv, wisp, results).
(() => {
'use strict';
const D = window.DATA, LV = D.lv, PAGES = window.PAGES, UI = window.UI;
const $ = s => document.querySelector(s);
const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const store = {get(k) {try {return localStorage.getItem(k);} catch (e) {return null;}},
               set(k, v) {try {localStorage.setItem(k, v);} catch (e) {}}};
let lang = store.get('wisp-story-lang') || ((navigator.language || 'de').toLowerCase().startsWith('de') ? 'de' : 'en');
const T = () => UI[lang];

// ---------------------------------------------------------------- numbers
const nf = (x, d = 2) => new Intl.NumberFormat(lang === 'de' ? 'de-DE' : 'en-US',
  {minimumFractionDigits: d, maximumFractionDigits: d}).format(x);
const pct = (a, n) => nf(100 * a / n, 0) + ' %';
const termName = i => LV.terms[i - 1];
const eqName = e => e === 1 ? 'H' : 'F';
const species = e => e === 1 ? 'hare' : 'fox';

function facts() {
  const R = D.results.strata, best = Math.max(...LV.stop.eqs.flat().map(b => b.ratio));
  const w = LV.candidates[LV.winner];
  return {
    n_obs: nf(LV.t.length, 0), noise: nf(100 * LV.sigma, 0) + ' %', n_combos: nf(2 ** 24, 0),
    threshold: nf(LV.stop.threshold, 1), best_ratio: nf(best, 1), gen_r2: nf(w.gen, 4),
    ic1_h: nf(LV.truth.ic1[0], 1), ic1_f: nf(LV.truth.ic1[1], 1), ic2_h: nf(LV.truth.ic2[0], 1), ic2_f: nf(LV.truth.ic2[1], 2),
    n_systems: nf(D.results.meta.n_systems_dim12, 0),
    dim3_struct: pct(...R.dim3_exact.wisp.structure), dim3_gen: pct(...R.dim3_exact.wisp.generalization),
    dim3_ws_struct: pct(...R.dim3_exact.wsindy.structure), dim3_ws_gen: pct(...R.dim3_exact.wsindy.generalization),
    hint: T().hint + ' <kbd>↓</kbd>'
  };
}
const fill = html => {const f = facts(); return html.replace(/\{(\w+)\}/g, (m, k) => k in f ? f[k] : m);};

// ---------------------------------------------------------------- LV model (truth) with RK4
const C0 = LV.truth.constants; // a, b, c, d: dH = aH - bHF, dF = -cF + dHF
function lvRhs(p, h, f) {return [p[0] * h - p[1] * h * f, -p[2] * f + p[3] * h * f];}
function integrate(p, x0, tEnd, dt = 0.005) {
  const n = Math.round(tEnd / dt), H = new Float64Array(n + 1), F = new Float64Array(n + 1);
  let h = x0[0], f = x0[1]; H[0] = h; F[0] = f;
  for (let i = 1; i <= n; i++) {
    const k1 = lvRhs(p, h, f), k2 = lvRhs(p, h + dt / 2 * k1[0], f + dt / 2 * k1[1]);
    const k3 = lvRhs(p, h + dt / 2 * k2[0], f + dt / 2 * k2[1]), k4 = lvRhs(p, h + dt * k3[0], f + dt * k3[1]);
    h += dt / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]); f += dt / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]);
    H[i] = h; F[i] = f;
  }
  return {dt, n, H, F, at(t) {const i = Math.min(n, Math.max(0, Math.round(t / dt))); return [H[i], F[i]];}};
}
// Part A illustrates the same equation from a calmer start; the measured meadow (IC 1) appears from the 'data' page on.
const ILLU = [1.0, 0.6], TEND = 10, BASE = integrate(C0, ILLU, TEND);
let ALT = null; // trajectory with a changed hare growth rate (equation page)

// ---------------------------------------------------------------- svg helpers
function svgIn(el) {
  el.innerHTML = '';
  const w = Math.max(240, el.clientWidth), h = Math.max(120, el.clientHeight);
  const svg = d3.select(el).append('svg').attr('viewBox', `0 0 ${w} ${h}`).attr('preserveAspectRatio', 'xMidYMid meet');
  return {svg, w, h};
}
function frame(el, {x, y, xl, yl, m = {l: 44, r: 12, t: 8, b: 30}, ylog = false, xTicks = 6, yTicks = 4}) {
  const {svg, w, h} = svgIn(el);
  const X = d3.scaleLinear(x, [m.l, w - m.r]);
  const Y = (ylog ? d3.scaleLog() : d3.scaleLinear()).domain(y).range([h - m.b, m.t]).clamp(ylog);
  svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${h - m.b})`).call(d3.axisBottom(X).ticks(xTicks).tickSizeOuter(0).tickFormat(v => nf(v, Number.isInteger(v) ? 0 : 1)));
  svg.append('g').attr('class', 'axis').attr('transform', `translate(${m.l},0)`).call(
    (ylog ? d3.axisLeft(Y).ticks(4, v => v >= 1 ? nf(v, 0) : nf(v, 1)) : d3.axisLeft(Y).ticks(yTicks).tickFormat(v => nf(v, Number.isInteger(v) ? 0 : 1))).tickSizeOuter(0));
  if (xl) svg.append('text').attr('x', w - m.r).attr('y', h - m.b - 5).attr('text-anchor', 'end').text(xl);
  if (yl) svg.append('text').attr('x', m.l + 4).attr('y', m.t + 10).text(yl);
  return {svg, X, Y, w, h, m};
}
const lineGen = (X, Y, xs) => d3.line().defined(v => Number.isFinite(v)).x((v, i) => X(xs[i])).y(v => Y(v));
const legend = (el, items) => {el.innerHTML = items.map(([cls, color, label]) =>
  `<span><i class="${cls}" style="border-color:${color};background:${cls === 'dot' ? color : 'none'}"></i>${label}</span>`).join('');};
const V = name => `var(--${name})`;

// ================================================================ stage: Lotka-Volterra (part A)
const lvStage = (() => {
  let step = null, raf = 0, last = 0, t = 0, pauseUntil = 0;
  const SPEED = 0.42, SCALE = 8; // model time units per second; symbols per model unit
  const animals = []; let meadow = null;

  // -- meadow ---------------------------------------------------------------
  const HARE = 'M-8,-6a8,5.5 0 1,0 16,0a8,5.5 0 1,0 -16,0M3.5,-11a3.6,3.6 0 1,0 7.2,0a3.6,3.6 0 1,0 -7.2,0' +
    'M5,-13c-1.6,-5 -1,-9 0.6,-9.4c1.3,0.2 1,4.5 0.4,9.6zM7.6,-13c0.2,-5.2 1.6,-8.6 3,-8.6c1.2,0.6 -0.2,4.6 -1.8,8.8z';
  const FOX = 'M-10,-7a10,4.6 0 1,0 20,0a10,4.6 0 1,0 -20,0M7,-10l10,2.6l-9,3.4zM8,-10l1.4,-5l2.6,4.4zM11,-9.4l2.2,-4.4l1.4,4.6z' +
    'M-9,-8c-6,-3 -12,-2 -16,1c5,2.4 11,2.6 16,0.6zM-6,-4l-1,5h1.6l1,-5zM5,-4l1,5h1.6l-0.6,-5z';
  function buildMeadow() {
    const el = $('#meadow'); el.innerHTML = '';
    const svg = d3.select(el).append('svg').attr('viewBox', '0 0 800 330').attr('preserveAspectRatio', 'xMidYMid slice').style('overflow', 'hidden');
    svg.append('rect').attr('width', 800).attr('height', 330).style('fill', V('sky'));
    svg.append('circle').attr('cx', 668).attr('cy', 62).attr('r', 30).style('fill', V('sun'));
    svg.append('path').attr('d', 'M0,170 C120,110 230,120 330,150 C440,180 520,100 640,112 C720,120 770,140 800,150 L800,330 L0,330Z').style('fill', V('hill'));
    svg.append('path').attr('d', 'M0,200 C140,170 260,190 400,182 C560,172 660,196 800,186 L800,330 L0,330Z').style('fill', V('hill2'));
    svg.append('rect').attr('y', 214).attr('width', 800).attr('height', 120).style('fill', V('grass'));
    [[70, 190, 1], [150, 178, .8], [560, 168, .9], [742, 186, 1.1], [610, 180, .7]].forEach(([x, y, s]) => {
      const g = svg.append('g').attr('transform', `translate(${x},${y}) scale(${s})`);
      g.append('rect').attr('x', -3).attr('y', -6).attr('width', 6).attr('height', 26).style('fill', V('trunk'));
      g.append('circle').attr('cy', -18).attr('r', 18).style('fill', V('tree'));
      g.append('circle').attr('cx', -10).attr('cy', -8).attr('r', 12).style('fill', V('tree'));
      g.append('circle').attr('cx', 10).attr('cy', -9).attr('r', 13).style('fill', V('tree'));
    });
    for (let i = 0; i < 70; i++) {
      const x = (i * 97) % 800, y = 222 + (i * 53) % 100;
      svg.append('path').attr('d', `M${x},${y}l2,-7M${x + 3},${y}l-1,-6`).style('stroke', V('hill2')).style('stroke-width', 1.3);
    }
    meadow = svg.append('g');
    animals.length = 0;
  }
  function spawn(kind, near) {
    const a = {kind, x: near ? Math.min(750, Math.max(50, near.x + (Math.random() - .5) * 120)) : 60 + Math.random() * 680,
      y: near ? Math.min(318, Math.max(232, near.y + (Math.random() - .5) * 50)) : 236 + Math.random() * 80,
      vx: (Math.random() - .5) * 30, vy: (Math.random() - .5) * 6, phase: Math.random() * 6, born: performance.now(), dying: 0};
    a.el = meadow.append('path').attr('d', kind === 'hare' ? HARE : FOX).style('fill', V(kind));
    animals.push(a); return a;
  }
  function syncAnimals(h, f, now) {
    for (const [kind, target] of [['hare', Math.round(h * SCALE)], ['fox', Math.round(f * SCALE)]]) {
      const alive = animals.filter(a => a.kind === kind && !a.dying);
      if (alive.length < target) {const burst = target - alive.length > 3; for (let i = alive.length; i < target; i++) spawn(kind, alive.length && !burst ? alive[i % alive.length] : null);}
      else if (alive.length > target) {
        let victims = alive.slice(0, alive.length - target);
        if (kind === 'hare') { // hares near a fox go first: the fox ate them
          const foxes = animals.filter(a => a.kind === 'fox' && !a.dying);
          const dist = a => foxes.length ? Math.min(...foxes.map(b => Math.hypot(a.x - b.x, a.y - b.y))) : 0;
          victims = alive.slice().sort((p, q) => dist(p) - dist(q)).slice(0, alive.length - target);
        }
        victims.forEach(a => {a.dying = now;});
      }
    }
  }
  function moveAnimals(dt, now) {
    const foxes = animals.filter(a => a.kind === 'fox' && !a.dying), hares = animals.filter(a => a.kind === 'hare' && !a.dying);
    for (let i = animals.length - 1; i >= 0; i--) {
      const a = animals[i];
      if (a.dying && now - a.dying > 600) {a.el.remove(); animals.splice(i, 1); continue;}
      let ax = (Math.random() - .5) * 70, ay = (Math.random() - .5) * 20;
      for (const b of animals) { // keep a little distance from every other animal
        if (b === a || b.dying) continue;
        const dx = a.x - b.x, dy = (a.y - b.y) * 2.5, d = Math.hypot(dx, dy);
        if (d < 34 && d > 0.01) {ax += dx / d * (34 - d) * 3; ay += dy / d * (34 - d) * 0.8;}
      }
      if (a.kind === 'fox' && hares.length) { // each fox stalks its own hare for a while
        if (!a.prey || a.prey.dying || !animals.includes(a.prey) || now > (a.switchAt || 0)) {
          a.prey = hares[Math.floor(Math.random() * hares.length)]; a.switchAt = now + 2500 + Math.random() * 3000;}
        const n = a.prey;
        ax += Math.sign(n.x - a.x) * 14; ay += Math.sign(n.y - a.y) * 4;
      } else if (a.kind === 'hare' && foxes.length) {
        const n = foxes.reduce((b, c) => Math.hypot(c.x - a.x, c.y - a.y) < Math.hypot(b.x - a.x, b.y - a.y) ? c : b);
        if (Math.hypot(n.x - a.x, n.y - a.y) < 60) {ax -= Math.sign(n.x - a.x) * 40; ay -= Math.sign(n.y - a.y) * 8;}
      }
      a.vx = Math.max(-46, Math.min(46, a.vx * 0.97 + ax * dt)); a.vy = Math.max(-10, Math.min(10, a.vy * 0.95 + ay * dt));
      a.x += a.vx * dt; a.y += a.vy * dt;
      if (a.x < 40 || a.x > 760) a.vx = -a.vx; if (a.y < 232 || a.y > 320) a.vy = -a.vy;
      for (const b of animals) {
        if (b === a || b.dying) continue;
        const dx = a.x - b.x, dy = (a.y - b.y) * 2, d = Math.hypot(dx, dy);
        if (d < 32 && d > 0.01) {a.x += dx / d * (32 - d) * 0.3; a.y += dy / d * (32 - d) * 0.08;}
      }
      a.x = Math.max(40, Math.min(760, a.x)); a.y = Math.max(232, Math.min(320, a.y));
      a.phase += dt * (a.kind === 'hare' ? 9 : 6);
      const hop = a.kind === 'hare' ? -Math.abs(Math.sin(a.phase)) * 4 : 0;
      const grow = Math.min(1, (now - a.born) / 450), fade = a.dying ? Math.max(0, 1 - (now - a.dying) / 600) : 1;
      const s = (a.kind === 'hare' ? 1.15 : 1.25) * (0.6 + 0.4 * grow) * (0.4 + 0.6 * fade) * (0.8 + (a.y - 232) / 88 * 0.4);
      a.el.attr('transform', `translate(${a.x.toFixed(1)},${(a.y + hop).toFixed(1)}) scale(${(a.vx < 0 ? -s : s).toFixed(3)},${s.toFixed(3)})`)
        .style('opacity', fade * grow);
    }
  }

  // -- bottom series ----------------------------------------------------------
  let series = null;
  function drawSeries() {
    const el = $('#series');
    const yMax = step === 'data' ? 10 : step === 'equation' && ALT ? Math.max(4, d3.max(ALT.H), d3.max(ALT.F)) : 4;
    series = frame(el, {x: [0, TEND], y: [0, yMax], xl: T().time, m: {l: 34, r: 10, t: 6, b: 26}});
    const {svg, X, Y} = series;
    const ts = Array.from({length: BASE.n + 1}, (_, i) => i * BASE.dt);
    series.ts = ts;
    series.base = svg.append('g');
    if (step === 'data') {
      const t = LV.t;
      svg.append('path').attr('d', lineGen(X, Y, t)(LV.clean1.H)).style('stroke', V('truth')).style('fill', 'none').style('stroke-width', 1).style('opacity', .9);
      svg.append('path').attr('d', lineGen(X, Y, t)(LV.clean1.F)).style('stroke', V('truth')).style('fill', 'none').style('stroke-width', 1).style('opacity', .9);
      for (const [k, c] of [['H', 'hare'], ['F', 'fox']]) {
        svg.append('g').selectAll('circle').data(LV.obs[k]).join('circle').attr('cx', (v, i) => X(t[i])).attr('cy', v => Y(v))
          .attr('r', 1.7).style('fill', V(c)).style('opacity', 0).transition().delay((v, i) => reduced ? 0 : i * 1.5).duration(300).style('opacity', .75);
      }
      legend($('#series-legend'), [['dot', V('hare'), T().hare + ' · ' + T().measured], ['dot', V('fox'), T().fox + ' · ' + T().measured], ['', V('truth'), T().truth],
        ['', 'transparent', (lang === 'de' ? 'Start ' : 'start ') + nf(LV.truth.ic1[0], 1) + ' / ' + nf(LV.truth.ic1[1], 1)]]);
      return;
    }
    if (step === 'equation' && ALT) {
      for (const [arr, c] of [[BASE.H, 'hare'], [BASE.F, 'fox']]) series.base.append('path').attr('d', lineGen(X, Y, ts)(Array.from(arr)))
        .style('stroke', V(c)).style('fill', 'none').style('stroke-width', 1.2).style('stroke-dasharray', '4 4').style('opacity', .55);
    }
    series.hPath = svg.append('path').style('stroke', V('hare')).style('fill', 'none').style('stroke-width', 2.2);
    series.fPath = svg.append('path').style('stroke', V('fox')).style('fill', 'none').style('stroke-width', 2.2);
    series.hDot = svg.append('circle').attr('r', 4.5).style('fill', V('hare'));
    series.fDot = svg.append('circle').attr('r', 4.5).style('fill', V('fox'));
    const items = [['', V('hare'), T().hare], ['', V('fox'), T().fox]];
    if (step === 'equation' && ALT) items.push(['dash', V('muted'), lang === 'de' ? 'vorher' : 'before']);
    legend($('#series-legend'), items);
  }
  function updateSeries(tNow) {
    if (!series || !series.hPath) return;
    const traj = step === 'equation' && ALT ? ALT : BASE, i = Math.min(traj.n, Math.round(tNow / traj.dt));
    const {X, Y, ts} = series, k = Math.max(2, i + 1);
    series.hPath.attr('d', lineGen(X, Y, ts)(Array.from(traj.H.subarray(0, k))));
    series.fPath.attr('d', lineGen(X, Y, ts)(Array.from(traj.F.subarray(0, k))));
    series.hDot.attr('cx', X(tNow)).attr('cy', Y(traj.H[i])); series.fDot.attr('cx', X(tNow)).attr('cy', Y(traj.F[i]));
  }

  // -- phase plane --------------------------------------------------------------
  let phase = null;
  function drawPhase() {
    $('#phase-title').textContent = lang === 'de' ? 'Jeder Zustand hat eine Richtung' : 'Every state has a direction';
    phase = frame($('#phase'), {x: [0, 4.2], y: [0, 3.4], xl: (lang === 'de' ? 'Hasen' : 'Hares') + ' H', yl: (lang === 'de' ? 'Füchse' : 'Foxes') + ' F'});
    const {svg, X, Y} = phase;
    const g = svg.append('g');
    for (let hi = 0; hi < 15; hi++) for (let fi = 0; fi < 11; fi++) {
      const h = 0.2 + hi * 0.27, f = 0.15 + fi * 0.3, [dh, df] = lvRhs(C0, h, f);
      const px = X(h), py = Y(f), vx = X(h + dh) - px, vy = Y(f + df) - py, L = Math.hypot(vx, vy) || 1;
      const len = 5 + 9 * Math.min(1, Math.log1p(Math.hypot(dh, df)) / 2.5), ux = vx / L * len, uy = vy / L * len;
      g.append('path').attr('d', `M${px - ux / 2},${py - uy / 2}l${ux},${uy}`).style('stroke', V('muted')).style('stroke-width', 1).style('opacity', .55)
        .attr('marker-end', 'url(#arrow)');
    }
    svg.append('defs').append('marker').attr('id', 'arrow').attr('viewBox', '0 0 6 6').attr('refX', 5).attr('refY', 3).attr('markerWidth', 5).attr('markerHeight', 5)
      .attr('orient', 'auto').append('path').attr('d', 'M0,0L6,3L0,6Z').style('fill', V('muted'));
    const pts = Array.from({length: BASE.n + 1}, (_, i) => [BASE.H[i], BASE.F[i]]);
    phase.orbit = svg.append('path').attr('d', d3.line().x(p => X(p[0])).y(p => Y(p[1]))(pts)).style('stroke', V('accent')).style('fill', 'none').style('stroke-width', 1.6).style('opacity', .35);
    phase.trail = svg.append('path').style('stroke', V('accent')).style('fill', 'none').style('stroke-width', 2.4);
    phase.dot = svg.append('circle').attr('r', 6).style('fill', V('ink'));
    phase.tan = svg.append('path').style('stroke', V('ink')).style('stroke-width', 2.2).attr('marker-end', 'url(#arrow)');
    phase.pts = pts;
  }
  function updatePhase(tNow) {
    if (!phase) return;
    const i = Math.min(BASE.n, Math.round(tNow / BASE.dt)), [h, f] = [BASE.H[i], BASE.F[i]], {X, Y} = phase;
    const from = Math.max(0, i - 260);
    phase.trail.attr('d', d3.line().x(p => X(p[0])).y(p => Y(p[1]))(phase.pts.slice(from, i + 1)));
    phase.dot.attr('cx', X(h)).attr('cy', Y(f));
    const [dh, df] = lvRhs(C0, h, f), vx = X(h + dh) - X(h), vy = Y(f + df) - Y(f), L = Math.hypot(vx, vy) || 1;
    phase.tan.attr('d', `M${X(h)},${Y(f)}l${vx / L * 34},${vy / L * 34}`);
  }

  // -- equation card --------------------------------------------------------------
  let growth = C0[0];
  const SENT = {de: ['Hasen vermehren sich', 'Füchse fressen Hasen', 'Füchse sterben ohne Futter', 'Füchse vermehren sich durch Fressen'],
                en: ['hares multiply', 'foxes eat hares', 'foxes die without food', 'foxes multiply by eating']};
  function drawEquation() {
    const c = [growth, C0[1], C0[2], C0[3]];
    $('#eq-card').innerHTML =
      `<div><span class="lhs h">dH/dt</span> = <span class="term h" data-term="0">${nf(c[0], 2)}·H</span> − <span class="term h" data-term="1">${nf(c[1], 2)}·H·F</span></div>` +
      `<div><span class="lhs f">dF/dt</span> = −<span class="term f" data-term="2">${nf(c[2], 1)}·F</span> + <span class="term f" data-term="3">${nf(c[3], 2)}·H·F</span></div>`;
    $('#eq-caption').textContent = lang === 'de' ? 'Fahre über einen Term.' : 'Hover over a term.';
    const ctl = $('#eq-controls');
    ctl.innerHTML = `<label>${lang === 'de' ? 'Vermehrung der Hasen' : 'Hare growth'} <input type="range" id="growth" min="0.8" max="2.8" step="0.01" value="${growth}"></label>` +
      `<output id="growth-out">${nf(growth, 2)}</output><button type="button" id="growth-reset">${lang === 'de' ? 'Zurück auf 1,84' : 'Back to 1.84'}</button>`;
    $('#growth').addEventListener('input', e => {growth = +e.target.value; $('#growth-out').textContent = nf(growth, 2);
      ALT = Math.abs(growth - C0[0]) < 1e-9 ? null : integrate([growth, C0[1], C0[2], C0[3]], ILLU, TEND);
      document.querySelectorAll('#eq-card .term[data-term="0"]').forEach(s => {s.textContent = nf(growth, 2) + '·H';});
      drawSeries(); updateSeries(TEND); t = TEND;});
    $('#growth-reset').addEventListener('click', () => {growth = C0[0]; ALT = null; drawEquation(); drawSeries(); t = 0;});
  }
  document.addEventListener('mouseover', e => {
    const s = e.target.closest('.term[data-term]'); if (!s) return;
    const k = +s.dataset.term;
    document.querySelectorAll('.term[data-term]').forEach(x => x.classList.toggle('lit', +x.dataset.term === k));
    const cap = $('#eq-caption'); if (cap) cap.textContent = SENT[lang][k];
  });

  // -- slope (inverse problem) ------------------------------------------------------
  function drawSlope() {
    $('#slope-title').textContent = lang === 'de' ? 'Steigung der Hasenkurve' : 'Slope of the hare curve';
    const t = LV.t, H = LV.obs.H, F = LV.clean1.F, Hc = LV.clean1.H;
    const trueSlope = Hc.map((h, i) => C0[0] * h - C0[1] * h * F[i]);
    const fd = H.slice(1).map((h, i) => (h - H[i]) / (t[i + 1] - t[i]));
    const lim = 1.15 * d3.max(trueSlope.map(Math.abs));
    const fr = frame($('#slope'), {x: [0, TEND], y: [-lim * 2.2, lim * 2.2], xl: T().time, m: {l: 40, r: 10, t: 6, b: 26}});
    const {svg, X, Y} = fr;
    svg.append('g').selectAll('circle').data(fd).join('circle').attr('cx', (v, i) => X((t[i] + t[i + 1]) / 2))
      .attr('cy', v => Y(Math.max(-lim * 2.2, Math.min(lim * 2.2, v)))).attr('r', 1.6).style('fill', V('hare')).style('opacity', .55);
    svg.append('path').attr('d', lineGen(X, Y, t)(trueSlope)).style('stroke', V('ink')).style('stroke-width', 1.8).style('fill', 'none');
    legend($('#slope-legend'), [['', V('ink'), lang === 'de' ? 'wahre Steigung' : 'true slope'],
      ['dot', V('hare'), lang === 'de' ? 'aus zwei Nachbarpunkten geschätzt' : 'estimated from two neighbours']]);
  }

  // -- loop ---------------------------------------------------------------------
  function loop(now) {
    raf = requestAnimationFrame(loop);
    const dt = Math.min(0.05, (now - (last || now)) / 1000); last = now;
    if (step === 'data') return;
    if (now > pauseUntil) {
      t += dt * SPEED;
      if (t > TEND) {t = 0; pauseUntil = now + 1200; if (step === 'meadow') {animals.forEach(a => a.el.remove()); animals.length = 0;}}
    }
    const traj = step === 'equation' && ALT ? ALT : BASE, [h, f] = traj.at(t);
    if (step === 'meadow') {
      syncAnimals(h, f, now); moveAnimals(dt, now);
      $('#counts').innerHTML = `<span class="h">${T().hare}</span> <b>${animals.filter(a => a.kind === 'hare' && !a.dying).length}</b> &nbsp; ` +
        `<span class="f">${T().fox}</span> <b>${animals.filter(a => a.kind === 'fox' && !a.dying).length}</b>`;
    }
    if (step === 'phase') updatePhase(t);
    updateSeries(t);
  }
  function show(s) {
    const prev = step; step = s;
    ['meadow', 'phase', 'equation', 'slope'].forEach(k => $('#sub-' + k).classList.toggle('on', k === (s === 'data' ? 'slope' : s)));
    if (s === 'meadow') {if (!meadow || prev === null) buildMeadow();}
    if (s === 'phase') drawPhase();
    if (s === 'equation') drawEquation();
    if (s === 'data') drawSlope();
    if (s !== 'equation') ALT = null;
    if (prev !== s && (s === 'meadow' || prev === 'data' || prev === null)) t = 0;
    drawSeries();
    if (s === 'data') {cancelAnimationFrame(raf); raf = 0;}
    else if (!raf) {last = 0; raf = requestAnimationFrame(loop);}
    if (reduced && s !== 'data') {t = TEND * 0.999; updateSeries(t); if (s === 'phase') updatePhase(t);}
  }
  function hide() {cancelAnimationFrame(raf); raf = 0; step = null;}
  function redraw() {const s = step; step = null; if (s) show(s);}
  return {show, hide, redraw};
})();

// ================================================================ stage: WISP in action (part B)
const wispStage = (() => {
  let step = null, sel = {grow: 1, prune: 4, stop: 5, weak: 4};
  const P = LV.path, W = LV.candidates[LV.winner];
  const lhs = e => `<span class="lhs ${e === 1 ? 'h' : 'f'}">d${eqName(e)}/dt =</span>`;
  function eqRow(e, terms, coefs) {
    const chips = terms.length ? terms.map((idx, j) => `<span class="chip" style="color:${V(species(e))}">` +
      (coefs ? `<span class="c">${nf(coefs[j], 3)}</span>` : '') + termName(idx) + '</span>').join('')
      : `<span class="empty">${lang === 'de' ? 'noch leer' : 'still empty'}</span>`;
    return lhs(e) + `<div class="rhs">${chips}</div>`;
  }
  function setEq(support, coefs) {
    const key = JSON.stringify([support, coefs ? 1 : 0, lang]);
    const el = $('#wisp-eq'); if (el.dataset.key === key) return; el.dataset.key = key;
    let c1 = null, c2 = null;
    if (coefs) {c1 = coefs.slice(0, support[0].length); c2 = coefs.slice(support[0].length);}
    el.innerHTML = eqRow(1, support[0], c1) + eqRow(2, support[1], c2);
  }
  const stepButtons = (labels, active, onPick) => `<div class="steps"><span class="label">${T().step}</span>` +
    labels.map((l, i) => `<button type="button" data-pick="${i + 1}" aria-pressed="${i + 1 === active}">${l}</button>`).join('') + '</div>';
  function wire(el, key, redraw) {
    el.querySelectorAll('[data-pick]').forEach(b => b.addEventListener('click', () => {sel[key] = +b.dataset.pick; redraw();}));
  }

  function blocks() {
    setEq([[], []]);
    const el = $('#w-blocks');
    el.innerHTML = [1, 2].map(e => `<div class="panel-title">${lang === 'de' ? 'Bausteine für' : 'Blocks for'} d${eqName(e)}/dt</div>` +
      `<div class="tiles">${LV.terms.map(n => `<div class="tile">${n}</div>`).join('')}</div>`).join('') +
      `<p class="small">${lang === 'de' ? '2 Gleichungen × 12 Bausteine: jeder kann drin sein oder nicht.' : '2 equations × 12 blocks: each can be in or out.'}</p>`;
  }

  function weak() {
    setEq([[], []]);
    const el = $('#w-weak'), wins = LV.windows, w = wins[sel.weak - 1];
    el.innerHTML = `<div class="panel-title">${lang === 'de' ? 'Hasen: Messpunkte und ein Fenster' : 'Hares: measurements and one window'}</div>` +
      `<div class="box" id="weak-top" style="flex:.8"></div>` +
      `<div class="controls"><label>${lang === 'de' ? 'Fensterlänge' : 'Window length'} <input type="range" id="win" min="1" max="${wins.length}" step="1" value="${sel.weak}"></label>` +
      `<output>${w} ${lang === 'de' ? (w === 1 ? 'Messabstand' : 'Messabstände') : (w === 1 ? 'sampling gap' : 'sampling gaps')}</output></div>` +
      `<div class="legend" id="weak-legend"></div><div class="box" id="weak-bot"></div>`;
    el.querySelector('#win').addEventListener('input', e => {sel.weak = +e.target.value; weak();});
    const t = LV.t, H = LV.obs.H, Hc = LV.clean1.H, F = LV.clean1.F, n = t.length;
    // top: data with one window and the area under the true right-hand side
    const top = frame($('#weak-top'), {x: [0, TEND], y: [0, 10], m: {l: 34, r: 10, t: 4, b: 22}});
    const i0 = 205, i1 = Math.min(n - 1, i0 + w);
    const rhs = Hc.map((h, i) => C0[0] * h - C0[1] * h * F[i]);
    top.svg.append('rect').attr('x', top.X(t[i0])).attr('width', Math.max(2, top.X(t[i1]) - top.X(t[i0]))).attr('y', top.m.t).attr('height', top.h - top.m.t - top.m.b)
      .style('fill', V('accent')).style('opacity', .16);
    top.svg.append('g').selectAll('circle').data(H).join('circle').attr('cx', (v, i) => top.X(t[i])).attr('cy', v => top.Y(v)).attr('r', 1.5)
      .style('fill', V('hare')).style('opacity', (v, i) => i === i0 || i === i1 ? 1 : .45);
    [i0, i1].forEach(i => top.svg.append('circle').attr('cx', top.X(t[i])).attr('cy', top.Y(H[i])).attr('r', 4.5).style('fill', 'none').style('stroke', V('ink')).style('stroke-width', 1.5));
    // bottom: slope estimates from neighbours vs window change / window length
    const fd = H.slice(1).map((h, i) => (h - H[i]) / (t[i + 1] - t[i]));
    const win = []; for (let i = 0; i + w < n; i++) win.push([(t[i] + t[i + w]) / 2, (H[i + w] - H[i]) / (t[i + w] - t[i])]);
    const lim = 2.4 * d3.max(rhs.map(Math.abs));
    const bot = frame($('#weak-bot'), {x: [0, TEND], y: [-lim, lim], xl: T().time, m: {l: 40, r: 10, t: 6, b: 26}});
    const clip = v => Math.max(-lim, Math.min(lim, v));
    if (w > 1) bot.svg.append('g').selectAll('circle').data(fd).join('circle').attr('cx', (v, i) => bot.X((t[i] + t[i + 1]) / 2)).attr('cy', v => bot.Y(clip(v)))
      .attr('r', 1.4).style('fill', V('muted')).style('opacity', .3);
    bot.svg.append('g').selectAll('circle').data(win).join('circle').attr('cx', p => bot.X(p[0])).attr('cy', p => bot.Y(clip(p[1])))
      .attr('r', 1.8).style('fill', V('hare')).style('opacity', .8);
    bot.svg.append('path').attr('d', lineGen(bot.X, bot.Y, t)(rhs)).style('stroke', V('ink')).style('stroke-width', 1.6).style('fill', 'none');
    // spread of each estimate around the truth (shown, not claimed elsewhere)
    const interp = x => {const j = Math.min(n - 2, Math.max(0, d3.bisectLeft(t, x) - 1)), u = (x - t[j]) / (t[j + 1] - t[j]); return rhs[j] * (1 - u) + rhs[j + 1] * u;};
    const sd = arr => Math.sqrt(d3.mean(arr.map(([x, v]) => (v - interp(x)) ** 2)));
    const sFd = sd(fd.map((v, i) => [(t[i] + t[i + 1]) / 2, v])), sWin = sd(win);
    legend($('#weak-legend'), [['', V('ink'), lang === 'de' ? 'wahre Steigung' : 'true slope'],
      ...(w > 1 ? [['dot', V('muted'), (lang === 'de' ? 'Nachbarpunkte, Streuung ' : 'neighbours, spread ') + nf(sFd, 1)]] : []),
      ['dot', V('hare'), (lang === 'de' ? `Fenster über ${w} ${w === 1 ? 'Messabstand' : 'Messabstände'}, Streuung ` : `window over ${w} gap${w === 1 ? '' : 's'}, spread `) + nf(sWin, 1)]]);
  }

  function grow() {
    const s = sel.grow, p = P[s - 1];
    setEq(p.support);
    const el = $('#w-grow');
    el.innerHTML = stepButtons(P.map((_, i) => String(i + 1)), s) +
      `<div class="panel-title" style="margin-top:8px">${lang === 'de' ? 'Wie viel vom Restfehler würde jeder freie Baustein zusätzlich erklären?' : 'How much of the remaining error would each free block explain in addition?'}</div>` +
      `<div class="box" id="grow-plot"></div><p class="small" id="grow-note"></p>`;
    wire(el, 'grow', grow);
    const before = s > 1 ? P[s - 2].support : [[], []];
    const items = [];
    for (const e of [1, 2]) for (let idx = 1; idx <= 12; idx++) {
      const g = p.gains.find(q => q.eq === e && q.idx === idx);
      items.push({e, idx, gain: g ? g.gain : null, used: before[e - 1].includes(idx), pick: p.add.eq === e && p.add.idx === idx});
    }
    const {svg, w, h} = svgIn($('#grow-plot')), m = {l: 30, r: 8, t: 10, b: 44};
    const X = d3.scaleBand(items.map((_, i) => i), [m.l, w - m.r]).paddingInner(.25);
    const Y = d3.scaleLinear([0, 1], [h - m.b, m.t]);
    svg.append('g').attr('class', 'axis').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(Y).ticks(4).tickFormat(v => nf(100 * v, 0) + '%').tickSizeOuter(0));
    svg.selectAll('rect.b').data(items).join('rect').attr('class', 'b').attr('x', (d, i) => X(i)).attr('width', X.bandwidth())
      .attr('y', Y(0)).attr('height', 0).style('fill', d => d.pick ? V(species(d.e)) : V('line'))
      .transition().duration(reduced ? 0 : 600).attr('y', d => Y(d.gain || 0)).attr('height', d => Y(0) - Y(d.gain || 0));
    svg.selectAll('text.l').data(items).join('text').attr('class', 'l').attr('transform', (d, i) => `translate(${X(i) + X.bandwidth() / 2},${h - m.b + 8}) rotate(-60)`)
      .attr('text-anchor', 'end').attr('dy', '.35em').style('font-size', '10px').style('fill', d => d.pick ? V(species(d.e)) : V('muted'))
      .style('font-weight', d => d.pick ? 700 : 400).text(d => d.used ? '✓ ' + termName(d.idx) : termName(d.idx));
    [1, 2].forEach(e => {const x0 = X((e - 1) * 12), x1 = X(e * 12 - 1) + X.bandwidth();
      svg.append('text').attr('x', (x0 + x1) / 2).attr('y', h - 2).attr('text-anchor', 'middle').style('fill', V(species(e))).style('font-weight', 650).text(`d${eqName(e)}/dt`);});
    $('#grow-note').innerHTML = (lang === 'de' ? `Schritt ${s}: <b>${termName(p.add.idx)}</b> kommt in d${eqName(p.add.eq)}/dt und erklärt ${nf(100 * p.add.gain, 0)}&#8239;% des Restfehlers. ✓ = schon drin.`
      : `Step ${s}: <b>${termName(p.add.idx)}</b> joins d${eqName(p.add.eq)}/dt and explains ${nf(100 * p.add.gain, 0)}&#8239;% of the remaining error. ✓ = already in.`);
  }

  function prune() {
    const s = sel.prune, p = P[s - 1];
    setEq(p.support);
    const el = $('#w-prune');
    el.innerHTML = stepButtons(P.map((_, i) => String(i + 1)), s) +
      `<div class="panel-title" style="margin-top:8px">${lang === 'de' ? 'Wie stark stiege der Fehler, wenn man den Baustein wieder herausnähme?' : 'How much would the error rise if the block were taken out again?'}</div>` +
      `<div class="box" id="prune-plot"></div><p class="small" id="prune-note"></p>`;
    wire(el, 'prune', prune);
    const thr = LV.backward_fraction * p.add.gain, items = p.checks;
    const {svg, w, h} = svgIn($('#prune-plot')), m = {l: 90, r: 50, t: 10, b: 26};
    const Y = d3.scaleBand(items.map((_, i) => i), [m.t + 18, Math.min(h - m.b, m.t + 18 + items.length * 62)]).paddingInner(.3);
    const X = d3.scaleLinear([0, 1], [m.l, w - m.r]);
    svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${Y.range()[1] + 4})`).call(d3.axisBottom(X).ticks(5).tickFormat(v => nf(100 * v, 0) + '%').tickSizeOuter(0));
    svg.selectAll('rect').data(items).join('rect').attr('x', X(0)).attr('y', (d, i) => Y(i)).attr('height', Y.bandwidth()).attr('width', 0)
      .style('fill', d => d.out ? V('warn') : V(species(d.eq))).transition().duration(reduced ? 0 : 600).attr('width', d => X(d.cost) - X(0));
    svg.selectAll('text.n').data(items).join('text').attr('class', 'n').attr('x', m.l - 8).attr('y', (d, i) => Y(i) + Y.bandwidth() / 2).attr('dy', '.35em')
      .attr('text-anchor', 'end').style('fill', d => V(species(d.eq))).style('font-weight', 650).text(d => `${termName(d.idx)} · d${eqName(d.eq)}/dt`);
    svg.append('line').attr('x1', X(thr)).attr('x2', X(thr)).attr('y1', m.t + 12).attr('y2', Y.range()[1] + 4).style('stroke', V('ink')).style('stroke-width', 1.5).style('stroke-dasharray', '4 3');
    svg.append('text').attr('x', X(thr)).attr('y', m.t + 6).attr('text-anchor', 'middle').style('fill', V('ink')).text(lang === 'de' ? 'Hälfte des letzten Gewinns' : 'half of the last gain');
    $('#prune-note').textContent = p.removed ? '' : (lang === 'de' ? 'Alle Balken liegen rechts der Linie: nichts fliegt raus.' : 'Every bar lies right of the line: nothing is thrown out.');
  }

  function stop() {
    const s = sel.stop, last = s > P.length;
    const tests = last ? LV.stop.eqs : P[s - 1].tests;
    setEq(last ? P[P.length - 1].support : (s > 1 ? P[s - 2].support : [[], []]));
    const el = $('#w-stop');
    el.innerHTML = stepButtons([...P.map((_, i) => (lang === 'de' ? 'vor ' : 'before ') + (i + 1)), lang === 'de' ? 'Ende' : 'end'], s) +
      `<div class="panel-title" style="margin-top:8px">${lang === 'de' ? 'Gewinn jedes freien Bausteins geteilt durch den Gewinn eines Rauschbausteins' : 'Gain of each free block divided by the gain of a noise block'}</div>` +
      `<div class="box" id="stop-plot"></div><p class="small" id="stop-note"></p>`;
    wire(el, 'stop', stop);
    const items = [];
    tests.forEach((eq, e) => eq.forEach(b => items.push({e: e + 1, idx: b.idx, ratio: b.ratio})));
    const {svg, w, h} = svgIn($('#stop-plot')), m = {l: 44, r: 8, t: 10, b: 44};
    const X = d3.scaleBand(items.map((_, i) => i), [m.l, w - m.r]).paddingInner(.25);
    const Y = d3.scaleLog([0.1, 1e5], [h - m.b, m.t]).clamp(true);
    svg.append('g').attr('class', 'axis').attr('transform', `translate(${m.l},0)`).call(d3.axisLeft(Y).tickValues([0.1, 1, 10, 100, 1000, 1e4, 1e5]).tickFormat(v => nf(v, v < 1 ? 1 : 0)).tickSizeOuter(0));
    const thr = LV.stop.threshold;
    svg.selectAll('rect').data(items).join('rect').attr('x', (d, i) => X(i)).attr('width', X.bandwidth()).attr('y', Y(0.1)).attr('height', 0)
      .style('fill', d => d.ratio > thr ? V(species(d.e)) : V('line')).transition().duration(reduced ? 0 : 600)
      .attr('y', d => Y(Math.max(0.1, d.ratio))).attr('height', d => Y(0.1) - Y(Math.max(0.1, d.ratio)));
    svg.selectAll('text.l').data(items).join('text').attr('class', 'l').attr('transform', (d, i) => `translate(${X(i) + X.bandwidth() / 2},${h - m.b + 8}) rotate(-60)`)
      .attr('text-anchor', 'end').attr('dy', '.35em').style('font-size', '10px').text(d => termName(d.idx));
    svg.append('line').attr('x1', m.l).attr('x2', w - m.r).attr('y1', Y(thr)).attr('y2', Y(thr)).style('stroke', V('ink')).style('stroke-dasharray', '4 3').style('stroke-width', 1.5);
    svg.append('text').attr('x', w - m.r).attr('y', Y(thr) - 5).attr('text-anchor', 'end').style('fill', V('ink')).text((lang === 'de' ? 'Schwelle ' : 'threshold ') + nf(thr, 1));
    const split = items.findIndex(d => d.e === 2);
    if (split > 0) [1, 2].forEach(e => {const a = items.findIndex(d => d.e === e), b = items.length - 1 - [...items].reverse().findIndex(d => d.e === e);
      svg.append('text').attr('x', (X(a) + X(b) + X.bandwidth()) / 2).attr('y', h - 2).attr('text-anchor', 'middle').style('fill', V(species(e))).style('font-weight', 650).text(`d${eqName(e)}/dt`);});
    const passing = items.filter(d => d.ratio > thr).length;
    $('#stop-note').textContent = passing ? (lang === 'de' ? `${passing} Bausteine liegen über der Schwelle: weiter.` : `${passing} blocks lie above the threshold: continue.`)
      : (lang === 'de' ? 'Kein Baustein liegt über der Schwelle: beide Gleichungen hören auf.' : 'No block lies above the threshold: both equations stop.');
  }

  function plotPair(el, H, F, {obs = true, truth = null, pred = false} = {}) {
    const fr = frame(el, {x: [0, TEND], y: [0, 10.5], m: {l: 24, r: 4, t: 4, b: 18}, xTicks: 3, yTicks: 2});
    const {svg, X, Y} = fr, t = LV.t;
    if (obs) for (const [k, c] of [['H', 'hare'], ['F', 'fox']]) svg.append('g').selectAll('circle').data(LV.obs[k].filter((_, i) => i % 2 === 0))
      .join('circle').attr('cx', (v, i) => X(t[2 * i])).attr('cy', v => Y(Math.min(10.5, v))).attr('r', 1).style('fill', V(c)).style('opacity', .35);
    if (truth) for (const k of ['H', 'F']) svg.append('path').attr('d', lineGen(X, Y, t)(truth[k])).style('stroke', V('truth')).style('stroke-width', 3.5).style('fill', 'none').style('opacity', .5);
    for (const [arr, c] of [[H, 'hare'], [F, 'fox']]) {
      const path = svg.append('path').attr('d', lineGen(X, Y, t)(arr.map(v => Number.isFinite(v) ? Math.max(-0.5, Math.min(11, v)) : NaN)))
        .style('stroke', V(c)).style('stroke-width', 1.8).style('fill', 'none');
      if (!reduced) {const L = path.node().getTotalLength(); path.attr('stroke-dasharray', `${L} ${L}`).attr('stroke-dashoffset', L).transition().duration(1400).ease(d3.easeCubicOut).attr('stroke-dashoffset', 0);}
    }
    return fr;
  }
  const supportLabel = c => c.support.map((eq, e) => `d${eqName(e + 1)}: ${eq.length ? eq.map(termName).join(', ') : '–'}`).join(' · ');

  function fit() {
    setEq(P[P.length - 1].support);
    const el = $('#w-fit');
    el.innerHTML = `<div class="legend"><span><i class="dot" style="background:${V('hare')}"></i>${T().measured}</span><span><i style="border-color:${V('hare')}"></i><i style="border-color:${V('fox')}"></i>${lang === 'de' ? 'simulierter Kandidat' : 'simulated candidate'}</span></div>` +
      `<div class="cands">${LV.candidates.map((c, i) => `<div class="cand" id="cand-${i}"><div class="head"><b>${lang === 'de' ? 'Kandidat' : 'Candidate'} ${i + 1}</b><span>R² ${nf(c.train, 3)}</span></div>` +
        `<div class="small">${supportLabel(c)}</div><div class="box"></div></div>`).join('')}</div>`;
    LV.candidates.forEach((c, i) => plotPair(document.querySelector(`#cand-${i} .box`), c.fit.H, c.fit.F));
  }

  function bic() {
    setEq(W.support, W.params);
    const el = $('#w-bic');
    el.innerHTML = `<div class="panel-title">BIC = N · log(MSE) + ${lang === 'de' ? 'Bausteine' : 'blocks'} · log(N) — ${lang === 'de' ? 'kleiner ist besser' : 'smaller is better'}</div><div class="box" id="bic-plot"></div>`;
    const c = LV.candidates, {svg, w, h} = svgIn($('#bic-plot')), m = {l: 160, r: 60, t: 10, b: 26};
    const lo = Math.min(0, d3.min(c, d => d.bic)), hi = Math.max(0, d3.max(c, d => d.bic));
    const X = d3.scaleLinear([lo, hi], [m.l, w - m.r]).nice();
    const Y = d3.scaleBand(c.map((_, i) => i), [m.t, Math.min(h - m.b, m.t + c.length * 52)]).paddingInner(.3);
    svg.append('g').attr('class', 'axis').attr('transform', `translate(0,${Y.range()[1] + 4})`).call(d3.axisBottom(X).ticks(5).tickFormat(v => nf(v, 0)).tickSizeOuter(0));
    svg.selectAll('rect').data(c).join('rect').attr('y', (d, i) => Y(i)).attr('height', Y.bandwidth()).attr('x', X(0)).attr('width', 0)
      .style('fill', (d, i) => i === LV.winner ? V('accent') : V('line')).transition().duration(reduced ? 0 : 700)
      .attr('x', d => X(Math.min(0, d.bic))).attr('width', d => Math.abs(X(d.bic) - X(0)));
    svg.selectAll('text.n').data(c).join('text').attr('class', 'n').attr('x', m.l - 8).attr('y', (d, i) => Y(i) + Y.bandwidth() / 2).attr('dy', '.35em').attr('text-anchor', 'end')
      .style('font-weight', (d, i) => i === LV.winner ? 700 : 400).style('fill', V('ink')).text((d, i) => `${lang === 'de' ? 'Kandidat' : 'Candidate'} ${i + 1} · ${d.k} ${lang === 'de' ? (d.k === 1 ? 'Baustein' : 'Bausteine') : (d.k === 1 ? 'block' : 'blocks')}`);
    svg.selectAll('text.v').data(c).join('text').attr('class', 'v').attr('y', (d, i) => Y(i) + Y.bandwidth() / 2).attr('dy', '.35em')
      .attr('x', d => d.bic < 0 ? X(d.bic) + 8 : X(d.bic) + 6).attr('text-anchor', 'start').style('fill', d => d.bic < 0 ? '#fff' : V('muted')).style('font-weight', d => d.bic < 0 ? 700 : 400).text(d => nf(d.bic, 0));
    svg.append('line').attr('x1', X(0)).attr('x2', X(0)).attr('y1', m.t - 4).attr('y2', Y.range()[1] + 4).style('stroke', V('muted'));
    // coefficient table in the text column
    const tbl = document.getElementById('coef-table');
    if (tbl) {
      const truth = [[C0[0], -C0[1]], [-C0[2], C0[3]]];
      let j = 0; const rows = [];
      W.support.forEach((eq, e) => eq.forEach((idx, k) => {rows.push(`<tr><td><span class="${e ? 'f' : 'h'}">d${eqName(e + 1)}/dt</span> · ${termName(idx)}</td><td>${nf(W.params[j++], 3)}</td><td>${nf(truth[e][k], 2)}</td></tr>`);}));
      rows.push(`<tr><td>${lang === 'de' ? 'Startwert' : 'start'} H, F</td><td>${nf(W.ic[0], 2)} / ${nf(W.ic[1], 2)}</td><td>${nf(LV.truth.ic1[0], 1)} / ${nf(LV.truth.ic1[1], 1)}</td></tr>`);
      tbl.innerHTML = `<table class="coef"><tr><th></th><th>${lang === 'de' ? 'gefunden' : 'found'}</th><th>${lang === 'de' ? 'wahr' : 'true'}</th></tr>${rows.join('')}</table>`;
    }
  }

  function test() {
    setEq(W.support, W.params);
    const el = $('#w-test');
    el.innerHTML = `<div class="panel-title">${lang === 'de' ? 'Neuer Startwert, nie gesehen' : 'New starting point, never seen'}: H = ${nf(LV.truth.ic2[0], 1)}, F = ${nf(LV.truth.ic2[1], 2)}</div>` +
      `<div class="legend"><span><i style="border-color:${V('truth')};border-top-width:4px"></i>${T().truth}</span><span><i style="border-color:${V('hare')}"></i>${lang === 'de' ? 'Vorhersage Hasen' : 'prediction hares'}</span><span><i style="border-color:${V('fox')}"></i>${lang === 'de' ? 'Vorhersage Füchse' : 'prediction foxes'}</span></div>` +
      `<div class="box" id="test-plot"></div><p class="small">R² = ${nf(W.gen, 4)}</p>`;
    const fr = plotPair($('#test-plot'), W.pred.H, W.pred.F, {obs: false, truth: LV.clean2});
    fr.svg.selectAll('.axis text').style('font-size', '11px');
  }

  function why() {
    setEq(W.support, W.params);
    const row = (label, sup, note) => `<div class="prow"><span class="plabel">${label}</span><span class="pchips">${[0, 1].map(e => `<span class="peq" style="color:${V(species(e + 1))}">d${eqName(e + 1)}: ${sup[e].length ? sup[e].map(termName).join(' + ') : '∅'}</span>`).join('')}</span><span class="pnote">${note}</span></div>`;
    const pathRows = row(lang === 'de' ? 'Start' : 'start', [[], []], '') + P.map((p, i) => row((lang === 'de' ? 'Schritt ' : 'step ') + (i + 1), p.support, '+ ' + termName(p.add.idx))).join('') +
      row(lang === 'de' ? 'Stopp' : 'stop', P[P.length - 1].support, (lang === 'de' ? 'bester Rest ' : 'best rest ') + nf(Math.max(...LV.stop.eqs.flat().map(b => b.ratio)), 1) + ' < ' + nf(LV.stop.threshold, 1));
    $('#w-why').innerHTML = `<div class="panel-title">${lang === 'de' ? 'Der ganze Pfad' : 'The whole path'}</div><div class="ppath">${pathRows}</div><div class="summary">` +
      `<div class="s"><b>${lang === 'de' ? 'Daten' : 'Data'}</b><span class="big">${nf(LV.t.length, 0)}</span><span>${lang === 'de' ? `Messpunkte je Art, ${nf(100 * LV.sigma, 0)} % Rauschen` : `measurements per species, ${nf(100 * LV.sigma, 0)} % noise`}</span></div>` +
      `<div class="s"><b>${lang === 'de' ? 'Möglich' : 'Possible'}</b><span class="big">${nf(2 ** 24 / 1e6, 1)}&nbsp;${lang === 'de' ? 'Mio.' : 'M'}</span><span>${lang === 'de' ? 'Gleichungspaare aus dem Baukasten' : 'equation pairs from the box'}</span></div>` +
      `<div class="s"><b>${lang === 'de' ? 'Simuliert' : 'Simulated'}</b><span class="big">${LV.candidates.length}</span><span>${lang === 'de' ? 'Kandidaten vom Pfad' : 'candidates from the path'}</span></div>` +
      `<div class="s"><b>${lang === 'de' ? 'Gewonnen' : 'Winner'}</b><span class="big">R² ${nf(W.gen, 4)}</span><span>${lang === 'de' ? 'von einem nie gesehenen Startwert' : 'from a never-seen starting point'}</span></div></div>`;
  }

  const views = {blocks, weak, grow, prune, stop, fit, bic, test, why};
  function show(s) {
    step = s;
    Object.keys(views).forEach(k => $('#w-' + k).classList.toggle('on', k === s));
    views[s]();
  }
  return {show, hide() {step = null;}, redraw() {if (step) {$('#wisp-eq').dataset.key = ''; show(step);}}};
})();

// ================================================================ stage: results (part C)
const resultsStage = (() => {
  let step = null;
  const METHODS = [['wisp', 'WISP'], ['wsindy', 'WSINDy'], ['weak_sindy', 'Weak-SINDy'], ['sindy', 'SINDy'], ['e_sindy', 'E-SINDy']];
  const PANELS = [['dim1_exact', 1, true], ['dim1_surrogate', 1, false], ['dim2_exact', 2, true], ['dim2_surrogate', 2, false], ['dim3_exact', 3, true]];
  function show(s) {
    step = s;
    const R = D.results.strata, el = $('#r-rates');
    const title = (dim, exact) => lang === 'de'
      ? `${dim} ${dim === 1 ? 'Größe' : 'Größen'} · ${exact ? 'Wahrheit im Baukasten' : 'Wahrheit nicht im Baukasten'}`
      : `${dim} variable${dim === 1 ? '' : 's'} · ${exact ? 'truth in the box' : 'truth not in the box'}`;
    const bar = (v, wisp) => v ? `<div class="bar${wisp ? ' wisp' : ''}"><span style="width:0" data-w="${100 * v[0] / v[1]}"></span><em>${nf(100 * v[0] / v[1], 0)}&#8239;%</em></div>`
      : `<div class="bar na"><em>–</em></div>`;
    el.innerHTML = `<div class="res-grid">${PANELS.map(([key, dim, exact]) => {
      const B = R[key], n = B.wisp.generalization[1];
      const dimmed = s === 'limits' ? key !== 'dim3_exact' : key === 'dim3_exact';
      return `<div class="res" style="opacity:${dimmed ? .28 : 1};transition:opacity .5s${key === 'dim3_exact' ? ';grid-column:1/-1' : ''}">` +
        `<h4>${title(dim, exact)}</h4><div class="n">${nf(n, 0)} ${lang === 'de' ? 'Läufe' : 'runs'}${key === 'dim3_exact' ? (lang === 'de' ? ' (Stichprobe)' : ' (sample)') : ''}</div>` +
        `<div class="bars"><span></span><span class="hd">${lang === 'de' ? 'Struktur richtig' : 'right structure'}</span><span class="hd">${lang === 'de' ? 'Vorhersage R² > 0,9' : 'prediction R² > 0.9'}</span>` +
        METHODS.map(([m, label]) => `<span style="${m === 'wisp' ? 'font-weight:700;color:var(--accent)' : ''}">${label}</span>${bar(exact ? B[m]?.structure : null, m === 'wisp')}${bar(B[m]?.generalization, m === 'wisp')}`).join('') +
        `</div></div>`;
    }).join('')}</div><p class="small" style="margin:8px 0 0">${lang === 'de' ? 'Vorläufig (Q8), 1 % und 5 % Rauschen, gleichmäßig und unregelmäßig gemessen, zusammengefasst. – = nicht definiert, weil die Wahrheit nicht im Baukasten liegt.'
      : 'Preliminary (Q8), 1 % and 5 % noise, regular and irregular sampling, pooled. – = undefined because the truth is not in the box.'}</p>`;
    requestAnimationFrame(() => el.querySelectorAll('.bar span[data-w]').forEach(s => {s.style.width = s.dataset.w + '%';}));
  }
  return {show, hide() {step = null;}, redraw() {if (step) show(step);}};
})();

// ================================================================ pages and navigation
const STAGES = {lv: lvStage, wisp: wispStage, results: resultsStage};
const track = $('#track'), pagesEl = $('#pages'), dots = $('#dots');
let index = 0, current = null, lockUntil = 0, lastWheel = 0, acc = 0;

function buildPages() {
  track.innerHTML = PAGES.map(p => `<section class="page" id="p-${p.id}" data-part="${p.part}"><div class="inner">${fill(p[lang])}</div></section>`).join('');
  dots.innerHTML = PAGES.map((p, i) => `<a href="#p-${p.id}" class="${i && PAGES[i - 1].part !== p.part ? 'gap' : ''}" title="${p.id}" aria-label="${i + 1}"></a>`).join('');
  document.documentElement.lang = lang;
  $('#lang-de').setAttribute('aria-pressed', lang === 'de'); $('#lang-en').setAttribute('aria-pressed', lang === 'en');
  document.title = lang === 'de' ? 'WISP erklärt' : 'WISP explained';
}
function place(animate) {
  const h = track.firstElementChild.offsetHeight;
  track.style.transition = animate && !reduced ? '' : 'none';
  track.style.transform = `translateY(${-index * h}px)`;
  if (!animate) {void track.offsetHeight; track.style.transition = '';}
}
function go(i, animate = true) {
  i = Math.max(0, Math.min(PAGES.length - 1, i));
  const p = PAGES[i], changed = i !== index || current === null;
  index = i; place(animate);
  $('#progress').style.width = (100 * (i + 1) / PAGES.length) + '%';
  $('#part-label').textContent = T().parts[p.part];
  dots.querySelectorAll('a').forEach((a, j) => {if (j === i) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');});
  try {history.replaceState(null, '', '#p-' + p.id);} catch (e) {}
  if (!changed) return;
  if (current && current !== p.scene) STAGES[current].hide();
  document.querySelectorAll('.layer').forEach(l => l.classList.toggle('on', l.id === 'layer-' + p.scene));
  current = p.scene;
  STAGES[p.scene].show(p.step);
  lockUntil = performance.now() + (reduced ? 150 : 760);
  track.querySelectorAll('.page .inner').forEach((el, j) => {if (j === i) el.scrollTop = 0;});
}
function canScroll(target, dy) {
  const el = target.closest && target.closest('.page .inner, .res-grid');
  return el && el.scrollHeight > el.clientHeight + 1 && (dy > 0 ? el.scrollTop + el.clientHeight < el.scrollHeight - 1 : el.scrollTop > 0);
}
window.addEventListener('wheel', e => {
  if (canScroll(e.target, e.deltaY)) return;
  e.preventDefault();
  const now = performance.now();
  if (now - lastWheel > 220) acc = 0; // a new gesture
  lastWheel = now;
  if (now < lockUntil) {lockUntil = Math.max(lockUntil, now + 160); return;} // swallow inertia
  acc += e.deltaY;
  if (Math.abs(acc) > 45) {go(index + Math.sign(acc)); acc = 0;}
}, {passive: false});
window.addEventListener('keydown', e => {
  if (e.target.closest('input, select, textarea')) return;
  const k = e.key, next = ['ArrowDown', 'PageDown', ' '].includes(k), prev = ['ArrowUp', 'PageUp'].includes(k);
  if (next || prev) {e.preventDefault(); if (performance.now() >= lockUntil - 400) go(index + (next ? 1 : -1));}
  if (k === 'Home') go(0); if (k === 'End') go(PAGES.length - 1);
});
let touch = null;
window.addEventListener('touchstart', e => {touch = e.target.closest('input[type=range], button, select') ? null : {y: e.touches[0].clientY, x: e.touches[0].clientX, t: e.target};}, {passive: true});
window.addEventListener('touchend', e => {
  if (!touch) return;
  const dy = touch.y - e.changedTouches[0].clientY, dx = touch.x - e.changedTouches[0].clientX;
  if (Math.abs(dy) > 50 && Math.abs(dy) > Math.abs(dx) && !canScroll(touch.t, dy)) go(index + Math.sign(dy));
  touch = null;
});
dots.addEventListener('click', e => {const a = e.target.closest('a'); if (!a) return; e.preventDefault(); go([...dots.children].indexOf(a));});
function setLang(l) {
  lang = l; store.set('wisp-story-lang', l);
  buildPages(); place(false);
  $('#part-label').textContent = T().parts[PAGES[index].part];
  dots.querySelectorAll('a')[index].setAttribute('aria-current', 'page');
  STAGES[current].redraw();
}
$('#lang-de').addEventListener('click', () => setLang('de'));
$('#lang-en').addEventListener('click', () => setLang('en'));
let resizeTimer = 0;
window.addEventListener('resize', () => {clearTimeout(resizeTimer); resizeTimer = setTimeout(() => {place(false); STAGES[current].redraw();}, 150);});
window.matchMedia('(prefers-color-scheme: dark)').addEventListener?.('change', () => STAGES[current].redraw());

buildPages();
const start = Math.max(0, PAGES.findIndex(p => '#p-' + p.id === location.hash));
current = null; index = start; go(start, false);
window.WISP_STORY = {go, get index() {return index;}, pages: PAGES};
})();
