/* WISP process page: 21 scenes + coupled part, following WISP_Visualisierungsbriefing_Prozess.md.
   Every number shown is either read from data.json (computed by build_wisp_process_data.py with the frozen
   Q6/Q7 functions and the Q9 C1000 refit records) or computed here by core.js, which the Node check
   verifies against those numbers. Hand-made numbers appear only in scenes 05 and 20b, labelled as such. */
(function () {
  'use strict';
  const D = window.WISP_DATA, C = window.WispCore;
  const L = D.logistic, LV = D.lv;
  const t = L.t, y = L.y.map(r => r[0]);
  const names = L.names, idx = n => names.indexOf(n);
  const W = C.design(t, y), FIT = C.weakFit(W.A, W.b);
  let lang = 'de';
  try { const s = localStorage.getItem('wisp-process-lang'); if (s === 'en' || s === 'de') lang = s; } catch (e) { /* storage blocked */ }

  /* ---------- formatting ---------- */
  const loc = () => (lang === 'de' ? 'de-DE' : 'en-US');
  const SUP = { '-': '⁻', 0: '⁰', 1: '¹', 2: '²', 3: '³', 4: '⁴', 5: '⁵', 6: '⁶', 7: '⁷', 8: '⁸', 9: '⁹' };
  function fmt(v, sig = 3) {
    if (v == null || !isFinite(v)) return '–';
    const a = Math.abs(v);
    if (a !== 0 && (a < 1e-3 || a >= 1e6)) {
      const e = Math.floor(Math.log10(a)), m = v / 10 ** e;
      return new Intl.NumberFormat(loc(), { maximumSignificantDigits: sig }).format(m) + '·10' + String(e).split('').map(c => SUP[c]).join('');
    }
    return new Intl.NumberFormat(loc(), { maximumSignificantDigits: sig, useGrouping: a >= 1e4 }).format(v);
  }
  const fx = (v, d = 2) => (v == null || !isFinite(v) ? '–' : new Intl.NumberFormat(loc(), { minimumFractionDigits: d, maximumFractionDigits: d, useGrouping: Math.abs(v) >= 1e4 }).format(v));
  const pct = (v, d = 1) => fx(100 * v, d) + ' %';
  const tr = (de, en) => (lang === 'de' ? de : en);
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');

  /* ---------- svg helpers ---------- */
  const NS = 'http://www.w3.org/2000/svg';
  function S(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs || {}) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function TX(parent, x, y0, text, attrs) { const e = S('text', Object.assign({ x, y: y0 }, attrs || {}), parent); e.textContent = text; return e; }
  function niceTicks(a, b, n = 5) {
    const span = b - a, raw = span / n, p = 10 ** Math.floor(Math.log10(raw)), f = raw / p;
    const step = (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * p, out = [];
    for (let v = Math.ceil(a / step) * step; v <= b + step * 1e-9; v += step) out.push(+v.toPrecision(12));
    return out;
  }
  function svgBox(fig, w, h) { return S('svg', { viewBox: `0 0 ${w} ${h}`, role: 'img' }, fig); }
  // A plot frame with linear x and linear or log y. Returns scales and the group to draw into.
  function frame(svg, o) {
    const m = Object.assign({ l: 52, r: 14, t: 14, b: 36 }, o.m || {});
    const x0 = o.x0 ?? 0, x1 = o.x1 ?? 1, logy = !!o.logy;
    const ly = v => (logy ? Math.log10(v) : v);
    const y0 = ly(o.y0), y1 = ly(o.y1), top = o.top ?? 0, H = o.h, Wd = o.w;
    const X = v => m.l + (v - x0) / (x1 - x0) * (Wd - m.l - m.r);
    const Y = v => top + m.t + (1 - (ly(v) - y0) / (y1 - y0)) * (H - m.t - m.b);
    const g = S('g', {}, svg), ax = S('g', { class: 'axis' }, g);
    const yt = o.yticks || (logy ? Array.from({ length: Math.floor(y1) - Math.ceil(y0) + 1 }, (_, i) => 10 ** (Math.ceil(y0) + i)) : niceTicks(o.y0, o.y1, o.ny || 4));
    for (const v of yt) {
      S('line', { x1: m.l, x2: Wd - m.r, y1: Y(v), y2: Y(v), class: 'grid' }, ax);
      TX(ax, m.l - 6, Y(v) + 4, o.yfmt ? o.yfmt(v) : fmt(v, 3), { 'text-anchor': 'end', 'font-size': 11.5, class: 'muted' });
    }
    if (!o.noX) for (const v of (o.xticks || niceTicks(x0, x1, o.nx || 5))) {
      S('line', { x1: X(v), x2: X(v), y1: top + H - m.b, y2: top + H - m.b + 4, stroke: 'var(--muted)' }, ax);
      TX(ax, X(v), top + H - m.b + 17, o.xfmt ? o.xfmt(v) : fmt(v, 3), { 'text-anchor': 'middle', 'font-size': 11.5, class: 'muted' });
    }
    S('line', { x1: m.l, x2: Wd - m.r, y1: top + H - m.b, y2: top + H - m.b, stroke: 'var(--muted)', 'stroke-width': .8 }, ax);
    if (o.xlabel) TX(ax, Wd - m.r, top + H - 4, o.xlabel, { 'text-anchor': 'end', 'font-size': 12, class: 'muted' });
    if (o.ylabel) TX(ax, m.l - 44, top + m.t - 4, o.ylabel, { 'font-size': 12, class: 'muted' });
    return { X, Y, g, m, W: Wd, H, top };
  }
  const pathD = pts => pts.filter(p => p && isFinite(p[0]) && isFinite(p[1])).map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(2) + ' ' + p[1].toFixed(2)).join('');
  function dots(g, P, xs, ys, attrs, kp = 'y', off = 0) { for (let i = 0; i < xs.length; i++) if (ys[i] != null) S('circle', Object.assign({ cx: P.X(xs[i]), cy: P.Y(ys[i]), r: 1.8, fill: 'var(--data)', 'fill-opacity': .75, 'data-k': kp + (i + off) }, attrs || {}), g); }
  function curve(g, P, xs, ys, attrs) { return S('path', Object.assign({ d: pathD(xs.map((x, i) => (ys[i] == null ? null : [P.X(x), P.Y(ys[i])]))), fill: 'none', stroke: 'var(--traj)', 'stroke-width': 2 }, attrs || {}), g); }
  // Horizontal bar chart on a log scale with an optional threshold line.
  function hbars(svg, rows, o) {
    const w = o.w || 520, rowH = o.rowH || 26, left = o.left || 70, right = o.right || 120, top = o.top || 26;
    const h = top + rows.length * rowH + 30;
    svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
    const lo = Math.log10(o.lo), hi = Math.log10(o.hi);
    const X = v => left + (Math.log10(Math.max(v, o.lo)) - lo) / (hi - lo) * (w - left - right);
    for (let e = Math.ceil(lo); e <= Math.floor(hi); e++) {
      S('line', { x1: X(10 ** e), x2: X(10 ** e), y1: top - 6, y2: top + rows.length * rowH, class: 'grid' }, svg);
      TX(svg, X(10 ** e), top + rows.length * rowH + 16, fmt(10 ** e, 1), { 'text-anchor': 'middle', 'font-size': 11, class: 'muted' });
    }
    if (o.axis) TX(svg, w - 4, top + rows.length * rowH + 28, o.axis, { 'text-anchor': 'end', 'font-size': 11.5, class: 'muted' });
    rows.forEach((r, i) => {
      const yy = top + i * rowH;
      TX(svg, left - 8, yy + rowH / 2 + 5, r.label, { 'text-anchor': 'end', 'font-size': 13.5, class: 'mono', 'data-k': 'bl:' + r.label });
      S('rect', { x: left, y: yy + 4, width: Math.max(1.5, X(r.v) - left), height: rowH - 9, rx: 2, fill: r.color || 'var(--lib)', 'fill-opacity': r.dim ? .35 : .9, 'data-k': 'bar:' + r.label }, svg);
      TX(svg, w - right + 10, yy + rowH / 2 + 5, r.text || fmt(r.v, 3), { 'font-size': 12.5, class: r.dim ? 'muted' : '', 'data-k': 'bv:' + r.label });
    });
    if (o.threshold != null) {
      S('line', { x1: X(o.threshold), x2: X(o.threshold), y1: top - 12, y2: top + rows.length * rowH, stroke: o.thColor || 'var(--ink)', 'stroke-width': 1.6, 'stroke-dasharray': '5 3' }, svg);
      TX(svg, X(o.threshold), top - 15, o.thLabel, { 'text-anchor': X(o.threshold) > w - 140 ? 'end' : 'middle', 'font-size': 12, 'font-weight': 600 });
    }
    return X;
  }
  const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
  const sup = s => s; // term names already carry unicode exponents

  /* ---------- model text ---------- */
  function eqText(terms, coefs, lhs = 'du/dt', digits = 4) {
    if (!terms.length) return lhs + ' = 0';
    return lhs + ' = ' + terms.map((n, i) => {
      const c = coefs ? fmt(Math.abs(coefs[i]), digits) : String.fromCharCode(97 + i);
      const sign = coefs ? (coefs[i] < 0 ? '− ' : i ? '+ ' : '') : (i ? '+ ' : '');
      return sign + c + (n === '1' ? '' : '·' + n);
    }).join(' ');
  }
  const setText = S0 => '{' + S0.join(', ') + '}';

  /* ---------- derived numbers used by several scenes ---------- */
  const P = L.path, steps = P.steps, states = P.states.map(s => s[0]), weak = P.weak.map(s => s[0]), stops = P.stops.map(s => s[0]);
  const noiseShare = stops[0].floor / P.b_norm2[0];
  const winner = L.candidates.find(c => c.id === L.winner);
  const truth = L.truth[0];

  /* ---------- scenes ---------- */
  const SC = [];
  const scene = d => SC.push(d);

  // 01
  scene({ id: 's01', part: 'weak', title: ['Die Ausgangsfrage', 'The starting question'],
    core: ['Wir sehen Messwerte eines Prozesses, aber nicht die Gleichung, die ihn antreibt.', 'We see measurements of a process, not the equation that drives it.'],
    text: [
      () => tr(`<p>Eine Bakterienkultur wird ${L.n}-mal gezählt, zwischen t = 0 und t = 10. Jeder Punkt ist eine Messung <span class="math">y(tᵢ)</span>. Die Messungen sind verrauscht: Jede weicht um einige Prozent vom wahren Zustand ab.</p>`,
        `<p>A bacterial culture is counted ${L.n} times between t = 0 and t = 10. Each dot is one measurement <span class="math">y(tᵢ)</span>. The measurements are noisy: each deviates from the true state by a few percent.</p>`),
      () => tr(`<p>Gesucht ist das Gesetz der Änderung: <span class="math">du/dt = f(u)</span>. Der Zustand <span class="math">u(t)</span> ist, was wir beobachten. Die Funktion <span class="math">f</span> sagt, wie schnell er sich in jedem Zustand ändert. Sie ist unbekannt, und sie ist das Ergebnis, das WISP liefern soll.</p>`,
        `<p>We are after the law of change: <span class="math">du/dt = f(u)</span>. The state <span class="math">u(t)</span> is what we observe. The function <span class="math">f</span> says how fast it changes in each state. It is unknown, and it is the result WISP is meant to deliver.</p>`)],
    draw(fig, k) {
      const svg = svgBox(fig, 520, 280), F = frame(svg, { w: 520, h: 280, x0: 0, x1: 10, y0: 0, y1: 80, xlabel: 't', ylabel: 'u' });
      dots(F.g, F, t, y);
      if (k >= 1) {
        const b = S('g', {}, F.g);
        S('rect', { x: 250, y: 150, width: 200, height: 54, rx: 6, fill: 'var(--panel)', stroke: 'var(--rule)' }, b);
        TX(b, 350, 174, 'du/dt = f(u) = ?', { 'text-anchor': 'middle', 'font-size': 17, class: 'mono', 'font-weight': 600 });
        TX(b, 350, 194, tr('gesucht', 'wanted'), { 'text-anchor': 'middle', 'font-size': 12, class: 'muted' });
      }
    }, steps: 2 });

  // 02
  scene({ id: 's02', part: 'weak', title: ['Eine Bibliothek möglicher Bausteine', 'A library of possible building blocks'],
    core: ['WISP sucht nicht frei nach Formeln. Es wählt aus einer festen Bibliothek.', 'WISP does not search freely for formulas. It chooses from a fixed library.'],
    text: [
      () => tr(`<p>Für eine Zustandsgröße enthält die Bibliothek sechs Bausteine: <span class="math">1, u, u², u³, sin u, cos u</span>. Jede Gleichung, die WISP finden kann, ist eine Summe einiger dieser Bausteine, jeder mit einer eigenen Zahl davor.</p>`,
        `<p>For one state variable the library holds six building blocks: <span class="math">1, u, u², u³, sin u, cos u</span>. Every equation WISP can find is a sum of some of them, each with its own number in front.</p>`),
      () => tr(`<p>Eine mögliche Gleichung ist <span class="math">du/dt = a·u + b·u²</span>. Zwei Dinge sind dabei zu klären: die <b>Struktur</b> (welche Bausteine sind dabei, hier <span class="math">{u, u²}</span>) und die <b>Koeffizienten</b> (wie stark wirkt jeder, hier <span class="math">a</span> und <span class="math">b</span>).</p>`,
        `<p>One possible equation is <span class="math">du/dt = a·u + b·u²</span>. Two things have to be settled: the <b>structure</b> (which blocks take part, here <span class="math">{u, u²}</span>) and the <b>coefficients</b> (how strongly each acts, here <span class="math">a</span> and <span class="math">b</span>).</p>`),
      () => tr(`<p>Nicht verwechseln: Zwei Bausteine in <b>einer</b> Gleichung sind etwas anderes als <b>zwei gekoppelte</b> Gleichungen. Gekoppelte Systeme kommen in Teil C. Bis dahin gibt es eine Zustandsgröße und eine Gleichung.</p>`,
        `<p>Do not confuse: two blocks in <b>one</b> equation are not the same as <b>two coupled</b> equations. Coupled systems come in part C. Until then there is one state variable and one equation.</p>`)],
    draw(fig, k) {
      fig.appendChild(el('div', 'shelf-label', tr('Bibliothek Θ', 'Library Θ')));
      const cards = el('div', 'cards');
      names.forEach(n => { const c = el('div', 'card lib' + (k >= 1 && (n === 'u' || n === 'u²') ? ' on' : ''), esc(n)); c.dataset.k = 'card:' + n; if (k >= 1 && (n === 'u' || n === 'u²')) c.appendChild(el('small', '', n === 'u' ? 'a' : 'b')); cards.appendChild(c); });
      fig.appendChild(cards);
      if (k >= 1) fig.appendChild(el('div', 'formula', 'du/dt = <span class="k-foba">a</span>·u + <span class="k-foba">b</span>·u²'));
      if (k >= 2) {
        fig.appendChild(el('div', 'formula wrap', tr('Eine Gleichung, zwei Bausteine:<br>du/dt = a·u + b·u²', 'One equation, two blocks:<br>du/dt = a·u + b·u²')));
        fig.appendChild(el('div', 'formula wrap', tr('Zwei gekoppelte Gleichungen (Teil C):<br>dx/dt = a·x − b·x·y<br>dy/dt = −c·y + d·x·y', 'Two coupled equations (part C):<br>dx/dt = a·x − b·x·y<br>dy/dt = −c·y + d·x·y')));
      }
    }, steps: 3 });

  // 03
  const d1 = C.differences(t, y, 1);
  scene({ id: 's03', part: 'weak', title: ['Warum nicht einfach ableiten?', 'Why not simply differentiate?'],
    core: ['Differenzenquotienten verstärken das Messrauschen.', 'Difference quotients amplify measurement noise.'],
    text: [
      () => tr(`<p>Die naheliegende Schätzung der Steigung ist <span class="math">[y(tᵢ₊₁) − y(tᵢ)] / Δt</span>. Hier ist <span class="math">Δt = ${fx(t[1] - t[0], 4)}</span>. Die Differenz zweier Messfehler wird durch dieses kleine <span class="math">Δt</span> geteilt und dadurch groß.</p>`,
        `<p>The obvious slope estimate is <span class="math">[y(tᵢ₊₁) − y(tᵢ)] / Δt</span>. Here <span class="math">Δt = ${fx(t[1] - t[0], 4)}</span>. The difference of two measurement errors is divided by this small <span class="math">Δt</span> and becomes large.</p>`),
      () => tr(`<p>Das Ergebnis unten ist zackig: die ${d1.length} Differenzenquotienten unserer Messreihe. Die Kurve oben ist glatt, ihre Steigung schwankt aber zwischen ${fmt(Math.min(...d1.map(p => p.d)), 2)} und ${fmt(Math.max(...d1.map(p => p.d)), 2)}. Mit solchen Steigungen eine Gleichung zu suchen heißt, Rauschen zu erklären.</p><p>WISP vermeidet die Ableitung ganz. Es verwendet eine Integralbeziehung: die Weak Form.</p>`,
        `<p>The result below is jagged: the ${d1.length} difference quotients of our series. The curve above is smooth, yet its slopes jump between ${fmt(Math.min(...d1.map(p => p.d)), 2)} and ${fmt(Math.max(...d1.map(p => p.d)), 2)}. Searching for an equation with these slopes means explaining noise.</p><p>WISP avoids the derivative altogether. It uses an integral relation: the weak form.</p>`)],
    draw(fig, k) {
      const svg = svgBox(fig, 520, 400);
      const A = frame(svg, { w: 520, h: 190, x0: 0, x1: 10, y0: 0, y1: 80, ylabel: 'u', noX: false });
      dots(A.g, A, t, y);
      if (k >= 1) {
        const lo = -150, hi = 150;
        const B = frame(svg, { w: 520, h: 200, top: 196, x0: 0, x1: 10, y0: lo, y1: hi, xlabel: 't', ylabel: 'Δy/Δt', ny: 4 });
        S('path', { d: pathD(d1.map(p => [B.X(p.t), B.Y(Math.max(lo, Math.min(hi, p.d)))])), fill: 'none', stroke: 'var(--bad)', 'stroke-width': 1 }, B.g);
      }
    }, steps: 2 });

  // 04
  const WS = 200, WE = 216;
  const dU = y[WE] - y[WS], I1 = C.integral(t, y, WS, WE, u => u), I2 = C.integral(t, y, WS, WE, u => u * u);
  const wFinal = weak[weak.length - 1];
  scene({ id: 's04', part: 'weak', title: ['Die Weak Form', 'The weak form'],
    core: ['Was zwischen zwei Zeitpunkten passiert ist, muss zu dem passen, was die Gleichung über diesen Zeitraum aufsummiert.', 'What happened between two times must match what the equation adds up over that interval.'],
    text: [
      () => tr(`<p>Wir nehmen ein Zeitfenster <span class="math">[tₐ, t_b]</span>, hier von Messung ${WS} bis ${WE}. Links steht die <b class="k-data">gemessene Änderung</b> <span class="math">y(t_b) − y(tₐ) = ${fmt(dU, 4)}</span>. Sie braucht nur die zwei Endpunkte, keine Ableitung.</p>`,
        `<p>Take a time window <span class="math">[tₐ, t_b]</span>, here from measurement ${WS} to ${WE}. On the left is the <b class="k-data">measured change</b> <span class="math">y(t_b) − y(tₐ) = ${fmt(dU, 4)}</span>. It needs only the two endpoints, no derivative.</p>`),
      () => tr(`<p>Rechts steht, was eine vorgeschlagene Gleichung über dasselbe Fenster vorhersagt. Für <span class="math">f(u) = a·u + b·u²</span> ist das <span class="math">a·∫u dt + b·∫u² dt</span>. Die Integrale sind <b class="k-lib">Flächen</b> unter den Bausteinen, berechnet aus den Messwerten mit der Trapezregel: <span class="math">∫u dt = ${fmt(I1, 4)}</span>, <span class="math">∫u² dt = ${fmt(I2, 4)}</span>.</p>`,
        `<p>On the right is what a proposed equation predicts over the same window. For <span class="math">f(u) = a·u + b·u²</span> that is <span class="math">a·∫u dt + b·∫u² dt</span>. The integrals are <b class="k-lib">areas</b> under the blocks, computed from the measurements with the trapezoid rule: <span class="math">∫u dt = ${fmt(I1, 4)}</span>, <span class="math">∫u² dt = ${fmt(I2, 4)}</span>.</p>`),
      () => tr(`<p>Mit den Koeffizienten, die WISP am Ende in der Weak Form findet (<span class="math">a = ${fmt(wFinal.coefficients[0], 4)}</span>, <span class="math">b = ${fmt(wFinal.coefficients[1], 4)}</span>), ergibt die rechte Seite ${fmt(wFinal.coefficients[0] * I1 + wFinal.coefficients[1] * I2, 4)}, gemessen wurde ${fmt(dU, 4)}. Das <span class="math">≈</span> steht für Messrauschen und Quadraturfehler. Allein das Rauschen der beiden Endpunkte hat hier eine Standardabweichung von etwa ${fmt(Math.sqrt(L.noise.variance[WS] + L.noise.variance[WE]), 2)} (Szene 15). Deshalb nutzt WISP nicht ein Fenster, sondern Tausende.</p><p>Wichtig: Das Integral über <span class="math">f(u(t))</span> beschreibt die <b>gesamte Änderung</b> im Fenster, nicht den Zustand selbst.</p>`,
        `<p>With the coefficients WISP finally finds in the weak form (<span class="math">a = ${fmt(wFinal.coefficients[0], 4)}</span>, <span class="math">b = ${fmt(wFinal.coefficients[1], 4)}</span>) the right-hand side gives ${fmt(wFinal.coefficients[0] * I1 + wFinal.coefficients[1] * I2, 4)}; the measurement says ${fmt(dU, 4)}. The <span class="math">≈</span> stands for measurement noise and quadrature error. The noise of the two endpoints alone has a standard deviation of about ${fmt(Math.sqrt(L.noise.variance[WS] + L.noise.variance[WE]), 2)} here (scene 15). That is why WISP uses thousands of windows, not one.</p><p>Note: the integral of <span class="math">f(u(t))</span> describes the <b>total change</b> within the window, not the state itself.</p>`)],
    draw(fig, k) {
      const svg = svgBox(fig, 520, k >= 1 ? 420 : 240);
      const ts = t.slice(WS - 30, WE + 31), ys = y.slice(WS - 30, WE + 31);
      const A = frame(svg, { w: 520, h: 230, x0: ts[0], x1: ts[ts.length - 1], y0: 20, y1: 60, ylabel: 'u', xlabel: 't' });
      S('rect', { x: A.X(t[WS]), y: A.m.t, width: A.X(t[WE]) - A.X(t[WS]), height: 230 - A.m.t - A.m.b, fill: 'var(--data-soft)' }, A.g);
      dots(A.g, A, ts, ys, { r: 2.6 }, 'y', WS - 30);
      for (const i of [WS, WE]) S('circle', { cx: A.X(t[i]), cy: A.Y(y[i]), r: 5, fill: 'none', stroke: 'var(--data)', 'stroke-width': 2 }, A.g);
      const xa = A.X(t[WE]) + 16;
      S('line', { x1: A.X(t[WS]), x2: xa, y1: A.Y(y[WS]), y2: A.Y(y[WS]), stroke: 'var(--data)', 'stroke-dasharray': '3 3' }, A.g);
      S('line', { x1: xa, x2: xa, y1: A.Y(y[WS]), y2: A.Y(y[WE]), stroke: 'var(--data)', 'stroke-width': 2.5 }, A.g);
      TX(A.g, xa + 6, (A.Y(y[WS]) + A.Y(y[WE])) / 2 + 4, 'Δy = ' + fmt(dU, 4), { 'font-size': 13, fill: 'var(--data)', 'font-weight': 600 });
      if (k >= 1) {
        const tw = t.slice(WS, WE + 1), uw = y.slice(WS, WE + 1);
        const B = frame(svg, { w: 520, h: 180, top: 236, x0: ts[0], x1: ts[ts.length - 1], y0: 0, y1: 60, ylabel: 'u(t)', ny: 3 });
        S('path', { d: pathD([[B.X(tw[0]), B.Y(0)], ...tw.map((x, i) => [B.X(x), B.Y(uw[i])]), [B.X(tw[tw.length - 1]), B.Y(0)]]) + 'Z', fill: 'var(--lib-soft)', stroke: 'var(--lib)' }, B.g);
        TX(B.g, (B.X(tw[0]) + B.X(tw[tw.length - 1])) / 2, B.Y(14), '∫u dt = ' + fmt(I1, 4), { 'text-anchor': 'middle', 'font-size': 13, fill: 'var(--lib)', 'font-weight': 600 });
        TX(B.g, 505, 270, tr('∫u² dt = ', '∫u² dt = ') + fmt(I2, 4), { 'text-anchor': 'end', 'font-size': 12.5, fill: 'var(--lib)' });
      }
      if (k >= 2) fig.appendChild(el('div', 'formula', `<span class="k-data">${fmt(dU, 4)}</span> ≈ ${fmt(wFinal.coefficients[0], 4)} · <span class="k-lib">${fmt(I1, 4)}</span> ${wFinal.coefficients[1] < 0 ? '−' : '+'} ${fmt(Math.abs(wFinal.coefficients[1]), 4)} · <span class="k-lib">${fmt(I2, 4)}</span> = ${fmt(wFinal.coefficients[0] * I1 + wFinal.coefficients[1] * I2, 4)}`));
    }, steps: 3 });

  // 05 (hand-made teaching example)
  const MINI = { t: [0, 1, 2, 3], x: [10, 12, 14, 16], win: [[0, 1], [1, 2], [0, 2]] };
  scene({ id: 's05', part: 'weak', title: ['Ein Mini-Beispiel zum Nachrechnen', 'A small example to check by hand'],
    core: ['Bevor eine Matrix kommt: woher die Zahlen stammen.', 'Before any matrix: where the numbers come from.'],
    text: [
      () => tr(`<p><b>Konstruiertes, rauschfreies Lehrbeispiel</b>, nicht aus den Bakteriendaten: vier Messwerte 10, 12, 14, 16 zu den Zeiten 0, 1, 2, 3. Vermuteter Baustein ist die Konstante: <span class="math">du/dt = c</span>.</p>`,
        `<p><b>Constructed, noise-free teaching example</b>, not from the bacteria data: four values 10, 12, 14, 16 at times 0, 1, 2, 3. The guessed block is the constant: <span class="math">du/dt = c</span>.</p>`),
      () => tr(`<p>Fenster [0, 1]: gemessene Änderung 12 − 10 = 2. Das Integral von 1 über die Länge 1 ist 1. Also <span class="math">2 ≈ c · 1</span>.</p>`, `<p>Window [0, 1]: measured change 12 − 10 = 2. The integral of 1 over length 1 is 1. So <span class="math">2 ≈ c · 1</span>.</p>`),
      () => tr(`<p>Fenster [1, 2]: wieder 14 − 12 = 2 und wieder <span class="math">2 ≈ c · 1</span>.</p>`, `<p>Window [1, 2]: again 14 − 12 = 2, again <span class="math">2 ≈ c · 1</span>.</p>`),
      () => tr(`<p>Fenster [0, 2]: 14 − 10 = 4, das Integral von 1 über die Länge 2 ist 2, also <span class="math">4 ≈ c · 2</span>. Alle drei Fenster sprechen für <b>c = 2</b>.</p>`, `<p>Window [0, 2]: 14 − 10 = 4, the integral of 1 over length 2 is 2, so <span class="math">4 ≈ c · 2</span>. All three windows point to <b>c = 2</b>.</p>`)],
    draw(fig, k) {
      const svg = svgBox(fig, 520, 250), F = frame(svg, { w: 520, h: 250, x0: -0.2, x1: 3.2, y0: 8, y1: 18, xticks: [0, 1, 2, 3], yticks: [10, 12, 14, 16], xlabel: 't', ylabel: 'x' });
      MINI.win.forEach((w, i) => {
        if (k < i + 1) return;
        const yy = F.Y(17.4) + i * 9 - 18;
        const on = k === i + 1;
        S('rect', { x: F.X(w[0]), y: F.m.t, width: F.X(w[1]) - F.X(w[0]), height: 250 - F.m.t - F.m.b, fill: on ? 'var(--data-soft)' : 'none' }, F.g);
        S('line', { x1: F.X(w[0]), x2: F.X(w[1]), y1: yy + 40, y2: yy + 40, stroke: 'var(--data)', 'stroke-width': on ? 3 : 1.5 }, F.g);
      });
      MINI.t.forEach((x, i) => { S('circle', { cx: F.X(x), cy: F.Y(MINI.x[i]), r: 5, fill: 'var(--data)' }, F.g); TX(F.g, F.X(x) + 8, F.Y(MINI.x[i]) + 4, MINI.x[i], { 'font-size': 13 }); });
      if (k >= 1) {
        const tb = el('div', 'tablewrap'), rows = MINI.win.slice(0, k).map(w => `<tr><td>[${w[0]}, ${w[1]}]</td><td class="b">${MINI.x[w[1]] - MINI.x[w[0]]}</td><td class="g">${w[1] - w[0]}</td><td>${(MINI.x[w[1]] - MINI.x[w[0]]) / (w[1] - w[0])}</td></tr>`).join('');
        tb.innerHTML = `<table class="ntab"><tr><th>${tr('Fenster', 'Window')}</th><th>Δx</th><th>∫1 dt</th><th>c = Δx / ∫1 dt</th></tr>${rows}</table>`;
        fig.appendChild(tb);
      }
    }, steps: 4 });

  // 06
  const counts = L.lengths.map(Lw => L.n - Lw);
  scene({ id: 's06', part: 'weak', title: ['Viele, überlappende Zeitfenster', 'Many overlapping windows'],
    core: ['WISP beurteilt einen Baustein nie an einem einzigen Fenster.', 'WISP never judges a block by a single window.'],
    text: [
      () => tr(`<p>WISP bildet Fenster der Längen <span class="math">L = 1, 2, 4, 8, 16</span>, gezählt in Messabständen. Für jede Länge beginnt an jedem möglichen Startpunkt ein Fenster, solange der Endpunkt noch existiert.</p>`, `<p>WISP forms windows of length <span class="math">L = 1, 2, 4, 8, 16</span>, counted in sampling steps. For each length a window starts at every possible index, as long as its endpoint exists.</p>`),
      () => tr(`<p>Bei ${L.n} Messungen sind das <span class="math">${counts.join(' + ')} = ${L.windows}</span> Fenster. Sie überlappen stark: Derselbe Messpunkt steckt in vielen Fenstern.</p><p>Die Integrale rechnet WISP mit der Trapezregel und mit den <b>wirklichen</b> Zeitabständen. Bei unregelmäßig verteilten Messzeiten wird kein gleichmäßiger Abstand unterstellt.</p>`,
        `<p>With ${L.n} measurements that makes <span class="math">${counts.join(' + ')} = ${L.windows}</span> windows. They overlap heavily: the same measurement sits in many windows.</p><p>WISP computes the integrals with the trapezoid rule and the <b>actual</b> time gaps. With irregular sampling no constant spacing is assumed.</p>`)],
    draw(fig, k) {
      const n0 = 34, svg = svgBox(fig, 520, 300), left = 60, X = i => left + i * (520 - left - 10) / n0;
      for (let i = 0; i <= n0; i++) S('circle', { cx: X(i), cy: 20, r: 2.6, fill: 'var(--data)' }, svg);
      TX(svg, left - 8, 24, tr('Messung', 'sample'), { 'text-anchor': 'end', 'font-size': 11.5, class: 'muted' });
      L.lengths.forEach((Lw, r) => {
        const top = 42 + r * 50;
        TX(svg, left - 8, top + 20, 'L = ' + Lw, { 'text-anchor': 'end', 'font-size': 13, class: 'mono' });
        if (k === 0 && r > 1) return;
        for (let s = 0; s < 4; s++) S('line', { x1: X(s) + 2, x2: X(s + Lw) - 2, y1: top + 6 + s * 9, y2: top + 6 + s * 9, stroke: 'var(--lib)', 'stroke-width': 4, 'stroke-linecap': 'round', 'stroke-opacity': .85 }, svg);
        TX(svg, X(4 + Lw) + 4, top + 33, '…', { 'font-size': 14, class: 'muted' });
        if (k >= 1) TX(svg, 516, top + 46, counts[r] + tr(' Fenster', ' windows'), { 'text-anchor': 'end', 'font-size': 11.5, class: 'muted' });
      });
      fig.appendChild(el('div', 'note', tr(`Ausschnitt: die ersten ${n0 + 1} von ${L.n} Messungen; je Länge sind die Fenster ab Start 0, 1, 2, 3 gezeichnet, es geht so weiter bis zum Ende der Messreihe.`, `Detail: the first ${n0 + 1} of ${L.n} measurements; for each length the windows starting at 0, 1, 2, 3 are drawn, and so on to the end of the series.`)));
    }, steps: 2 });

  // 07
  scene({ id: 's07', part: 'weak', title: ['Die Matrix G und der Vektor b', 'The matrix G and the vector b'],
    core: ['Die Tausenden Integrale werden zu einem linearen Regressionsproblem.', 'The thousands of integrals become one linear regression problem.'],
    text: [
      () => tr(`<p>Ordnet man die Fenster untereinander, entsteht <span class="math">b = G·ξ + ε</span>. <b class="k-data">b</b> enthält eine gemessene Änderung je Fenster. In <b class="k-lib">G</b> ist jede Zeile ein Fenster und jede Spalte ein Baustein; die Zelle enthält das Integral dieses Bausteins über dieses Fenster. <span class="math">ξ</span> sind die Koeffizienten, <span class="math">ε</span> die Abweichung.</p><p>Im Mini-Beispiel: <span class="math">b = [2, 2, 4]ᵀ</span>, <span class="math">G = [1, 1, 2]ᵀ</span>, <span class="math">ξ = [c]</span> mit <span class="math">c = 2</span>.</p>`,
        `<p>Stacking the windows gives <span class="math">b = G·ξ + ε</span>. <b class="k-data">b</b> holds one measured change per window. In <b class="k-lib">G</b> every row is a window and every column a block; each cell holds the integral of that block over that window. <span class="math">ξ</span> are the coefficients, <span class="math">ε</span> the deviation.</p><p>In the small example: <span class="math">b = [2, 2, 4]ᵀ</span>, <span class="math">G = [1, 1, 2]ᵀ</span>, <span class="math">ξ = [c]</span> with <span class="math">c = 2</span>.</p>`),
      () => tr(`<p>Für die Bakteriendaten hat G ${L.windows} Zeilen und ${names.length} Spalten. Rechts die ersten drei Fenster jeder Länge. Bei kurzen Fenstern ist die gemessene Änderung klein und vom Rauschen geprägt; ein Fenster der Länge 1 kann sogar eine Abnahme zeigen, obwohl die Kultur wächst.</p>`,
        `<p>For the bacteria data G has ${L.windows} rows and ${names.length} columns. On the right, the first three windows of each length. In short windows the measured change is small and dominated by noise; a window of length 1 can even show a decrease although the culture grows.</p>`)],
    draw(fig, k) {
      const tb = el('div', 'tablewrap');
      if (k === 0) tb.innerHTML = `<table class="ntab"><tr><th>${tr('Fenster', 'Window')}</th><th>b = Δx</th><th>G: 1</th></tr><tr><td>[0, 1]</td><td class="b">2</td><td class="g">1</td></tr><tr><td>[1, 2]</td><td class="b">2</td><td class="g">1</td></tr><tr><td>[0, 2]</td><td class="b">4</td><td class="g">2</td></tr></table>`;
      else tb.innerHTML = `<table class="ntab"><tr><th>L</th><th>${tr('Fenster', 'Window')}</th><th>b</th>${names.map(n => `<th>∫${esc(n)} dt</th>`).join('')}</tr>${L.window_rows.map(r => `<tr><td>${r.L}</td><td>[${r.start}, ${r.end}]</td><td class="b">${fmt(r.b, 3)}</td>${r.G.map(v => `<td class="g">${fmt(v, 3)}</td>`).join('')}</tr>`).join('')}<tr><td colspan="${3 + names.length}" style="text-align:center;color:var(--muted)">… ${tr('insgesamt', 'in total')} ${L.windows} ${tr('Zeilen', 'rows')}</td></tr></table>`;
      fig.appendChild(tb);
    }, steps: 2 });

  // 08 (interactive least squares)
  const ls = { on: new Set([idx('u')]) };
  const PRESET = [['u'], ['u', 'u²'], ['u²']];
  const b16 = W.b.map((v, i) => [v, i]).filter((_, i) => W.win[i][1] - W.win[i][0] === 16);
  scene({ id: 's08', part: 'weak', title: ['Least Squares: woher die Koeffizienten kommen', 'Least squares: where the coefficients come from'],
    core: ['Für jede Bausteinmenge S liefert lineare Least Squares die besten Koeffizienten, alle gemeinsam.', 'For every set of blocks S, linear least squares gives the best coefficients, all at once.'],
    text: [
      () => tr(`<p><span class="math">ξ̂_S = argmin ‖b − G_S ξ‖²</span>. <span class="math">G_S</span> enthält nur die Spalten der gewählten Bausteine. Mit nur <span class="math">u</span> gibt es einen Koeffizienten.</p><p>Die Grafik zeigt die Fenster der Länge 16: gemessene Änderung gegen Vorhersage <span class="math">G_S ξ̂</span>. Je näher die Punkte an der Diagonale liegen, desto besser.</p>`,
        `<p><span class="math">ξ̂_S = argmin ‖b − G_S ξ‖²</span>. <span class="math">G_S</span> holds only the columns of the chosen blocks. With <span class="math">u</span> alone there is one coefficient.</p><p>The plot shows the length-16 windows: measured change against prediction <span class="math">G_S ξ̂</span>. The closer the dots to the diagonal, the better.</p>`),
      () => tr(`<p>Kommt <span class="math">u²</span> dazu, werden <b>beide</b> Koeffizienten neu bestimmt. Der Koeffizient von <span class="math">u</span> bleibt nicht stehen, er ändert sich.</p>`, `<p>Adding <span class="math">u²</span> re-estimates <b>both</b> coefficients. The coefficient of <span class="math">u</span> does not stay put; it changes.</p>`),
      () => tr(`<p>Nimmt man <span class="math">u</span> wieder heraus, wird der Koeffizient von <span class="math">u²</span> erneut optimiert. Jede Änderung der Menge heißt: neu fitten.</p><p>Probieren Sie es selbst: Ein Klick auf einen Baustein schaltet ihn ein oder aus.</p><p class="note">„Erklärter Anteil“ ist <span class="math">1 − SSE/‖b‖²</span>. Er bleibt klein, weil die kurzen Fenster vor allem Rauschen messen: Nach der Rauschschätzung aus Szene 16 sind ${pct(noiseShare, 0)} von <span class="math">‖b‖²</span> Rauschen, das kein Baustein erklären kann.</p>`,
        `<p>Taking <span class="math">u</span> out again re-optimizes the coefficient of <span class="math">u²</span>. Every change of the set means: fit again.</p><p>Try it: clicking a block switches it on or off.</p><p class="note">“Explained share” is <span class="math">1 − SSE/‖b‖²</span>. It stays small because the short windows measure mostly noise: by the noise estimate of scene 16, ${pct(noiseShare, 0)} of <span class="math">‖b‖²</span> is noise that no block can explain.</p>`)],
    enter(k) { ls.on = new Set(PRESET[k].map(idx)); },
    draw(fig, k, redraw) {
      const cards = el('div', 'cards');
      names.forEach((n, j) => {
        const c = el('button', 'card toggle' + (ls.on.has(j) ? ' on' : ''), esc(n)); c.dataset.k = 'card:' + n;
        c.type = 'button'; c.setAttribute('aria-pressed', ls.on.has(j));
        c.onclick = () => { ls.on.has(j) ? ls.on.delete(j) : ls.on.add(j); redraw(); };
        cards.appendChild(c);
      });
      fig.appendChild(cards);
      const Sx = [...ls.on].sort((a, b) => a - b), sol = FIT.solve(Sx);
      fig.appendChild(el('div', 'formula', eqText(Sx.map(j => names[j]), sol.coef, 'du/dt', 4) + `<br><span class="muted" style="color:var(--muted)">${tr('erklärter Anteil', 'explained share')} = ${pct(1 - sol.sse / FIT.bnorm2, 2)}</span>`));
      const svg = svgBox(fig, 520, 280), F = frame(svg, { w: 520, h: 280, x0: -2, x1: 14, y0: -2, y1: 14, xlabel: tr('Vorhersage G_S ξ̂', 'prediction G_S ξ̂'), ylabel: 'b (L = 16)' });
      S('line', { x1: F.X(-2), y1: F.Y(-2), x2: F.X(14), y2: F.Y(14), stroke: 'var(--muted)', 'stroke-dasharray': '4 4' }, F.g);
      for (const [v, i] of b16) {
        const pred = Sx.reduce((s, j, q) => s + W.A[i][j] * sol.coef[q], 0);
        if (pred > -2 && pred < 14) S('circle', { cx: F.X(pred), cy: F.Y(Math.max(-2, Math.min(14, v))), r: 2, fill: 'var(--data)', 'fill-opacity': .6 }, F.g);
      }
    }, steps: 3 });

  // 09 forward
  scene({ id: 's09', part: 'weak', title: ['Forward: den nützlichsten Baustein hinzufügen', 'Forward: add the most useful block'],
    core: ['WISP beginnt leer und nimmt den Baustein, der den Weak-Form-Fehler am stärksten senkt.', 'WISP starts empty and takes the block that lowers the weak-form error the most.'],
    text: [
      () => tr(`<p>Für jeden noch freien Baustein <span class="math">j</span> wird das Modell mit <span class="math">j</span> neu gefittet und der <b>Gewinn</b> gemessen: <span class="math">g(j|S) = [SSE(S) − SSE(S ∪ {j})] / ‖b‖²</span>. Die Normierung macht Gewinne verschiedener Gleichungen vergleichbar (Teil C).</p><p>Im ersten Schritt gewinnt die Konstante <span class="math">1</span> mit ${fmt(steps[0].added.gain, 3)} vor <span class="math">u</span> mit ${fmt(steps[0].gains.find(g => g.term === 'u').gain, 3)}. Eine Konstante beschreibt die mittlere Steigung schon recht gut. Ob sie bleiben darf, prüft später der Rückwärtsschritt.</p>`,
        `<p>For every block <span class="math">j</span> not yet in the model, the model is refitted with <span class="math">j</span> and its <b>gain</b> measured: <span class="math">g(j|S) = [SSE(S) − SSE(S ∪ {j})] / ‖b‖²</span>. The normalization makes gains of different equations comparable (part C).</p><p>In the first step the constant <span class="math">1</span> wins with ${fmt(steps[0].added.gain, 3)}, ahead of <span class="math">u</span> with ${fmt(steps[0].gains.find(g => g.term === 'u').gain, 3)}. A constant already describes the average slope fairly well. Whether it may stay is checked later by the backward step.</p>`),
      () => tr(`<p>Zweiter Schritt, ausgehend von <span class="math">{1}</span>: Jeder übrige Baustein wird als Partner der Konstante getestet, jedes Mal mit neu bestimmten Koeffizienten. <span class="math">u³</span> gewinnt mit ${fmt(steps[1].added.gain, 3)}.</p><p>Die Reihenfolge ist streng gierig: Es wird immer der größte Gewinn genommen, nichts anderes.</p>`,
        `<p>Second step, starting from <span class="math">{1}</span>: every remaining block is tried as a partner of the constant, each time with re-estimated coefficients. <span class="math">u³</span> wins with ${fmt(steps[1].added.gain, 3)}.</p><p>The order is strictly greedy: the largest gain is taken, nothing else.</p>`)],
    draw(fig, k) {
      const st = steps[k], best = st.added.term;
      fig.appendChild(el('div', 'eqline', tr('aktuell S = ', 'current S = ') + setText(states[k]) + '  →  ' + tr('Kandidaten', 'candidates')));
      const svg = svgBox(fig, 520, 200);
      hbars(svg, st.gains.slice().sort((a, b) => b.gain - a.gain).map(g => ({ label: g.term, v: g.gain, color: g.term === best ? 'var(--foba)' : 'var(--lib)', dim: g.term !== best })), { lo: 1e-4, hi: 1, axis: tr('Gewinn g (log)', 'gain g (log)') });
    }, steps: 2 });

  // 10 backward
  const BW = [{ s: 2, c: 0 }, { s: 2, c: 1 }, { s: 3, c: 0 }, { s: 3, c: 1 }];
  scene({ id: 's10', part: 'weak', title: ['Backward: ist ein Baustein überflüssig geworden?', 'Backward: has a block become redundant?'],
    core: ['Nach jedem Forward-Schritt prüft WISP jeden aktiven Baustein: Was kostet es, ihn wegzulassen?', 'After every forward step WISP checks each active block: what does it cost to leave it out?'],
    text: [
      () => { const s = steps[2]; return tr(`<p>Dritter Schritt: <span class="math">u</span> kommt dazu, Gewinn ${fmt(s.added.gain, 3)}. Jetzt wird jeder aktive Baustein einmal weggelassen, der Rest neu gefittet und der Anstieg des normierten Fehlers gemessen. Entfernt wird der Baustein mit dem kleinsten Anstieg, <b>falls</b> dieser kleiner ist als <span class="math">ν</span> mal der letzte Gewinn, mit <span class="math">ν = ½</span>: hier also kleiner als ${fmt(L.nu * s.added.gain, 3)}.</p><p>Die Konstante kostet nur ${fmt(s.backward[0].removed.cost, 3)}. Sie fliegt raus.</p>`,
        `<p>Third step: <span class="math">u</span> comes in with gain ${fmt(s.added.gain, 3)}. Now each active block is left out once, the rest refitted, and the rise of the normalized error measured. The block with the smallest rise is removed <b>if</b> that rise is below <span class="math">ν</span> times the last gain, with <span class="math">ν = ½</span>: here below ${fmt(L.nu * s.added.gain, 3)}.</p><p>The constant costs only ${fmt(s.backward[0].removed.cost, 3)}. It goes.</p>`); },
      () => tr(`<p>Nach dem Entfernen wird erneut geprüft, bis nichts mehr entfernt werden darf. Ohne die Konstante sind <span class="math">u</span> und <span class="math">u³</span> beide teuer geworden: Beide bleiben. Neuer Stand: <span class="math">{u, u³}</span>.</p><p>Die Regel stammt aus dem FoBa-Algorithmus von Tong Zhang. Nach jedem Paar aus Hinzufügen und Entfernen bleibt mindestens die Hälfte des Gewinns als Verbesserung; der Pfad kann nicht im Kreis laufen.</p>`,
        `<p>After a removal the check is repeated until nothing more may go. Without the constant, <span class="math">u</span> and <span class="math">u³</span> have both become expensive: both stay. New state: <span class="math">{u, u³}</span>.</p><p>The rule comes from Tong Zhang's FoBa algorithm. After each add/remove pair at least half of the gain remains as improvement, so the path cannot run in circles.</p>`),
      () => { const s = steps[3]; return tr(`<p>Vierter Schritt: <span class="math">u²</span> kommt dazu, Gewinn ${fmt(s.added.gain, 3)}, Schwelle ${fmt(L.nu * s.added.gain, 3)}. <span class="math">u³</span> kostet jetzt nur noch ${fmt(s.backward[0].removed.cost, 3)}: <span class="math">u²</span> übernimmt seine Rolle, <span class="math">u³</span> fliegt raus.</p>`,
        `<p>Fourth step: <span class="math">u²</span> comes in, gain ${fmt(s.added.gain, 3)}, threshold ${fmt(L.nu * s.added.gain, 3)}. <span class="math">u³</span> now costs only ${fmt(s.backward[0].removed.cost, 3)}: <span class="math">u²</span> takes over its role, and <span class="math">u³</span> goes.</p>`); },
      () => tr(`<p>Erneute Prüfung: <span class="math">u</span> und <span class="math">u²</span> bleiben. Stand: <span class="math">{u, u²}</span>.</p><p>Wichtig: Backward verwendet <b>kein BIC</b>. Es prüft nur den Weak-Form-Fehler, und nach jeder Entfernung werden die Koeffizienten neu bestimmt.</p>`,
        `<p>Re-check: <span class="math">u</span> and <span class="math">u²</span> stay. State: <span class="math">{u, u²}</span>.</p><p>Note: backward uses <b>no BIC</b>. It only checks the weak-form error, and after each removal the coefficients are re-estimated.</p>`)],
    draw(fig, k) {
      const { s, c } = BW[k], st = steps[s], chk = st.backward[c], th = L.nu * st.added.gain;
      fig.appendChild(el('div', 'eqline', `+ ${st.added.term}  ·  ${tr('Gewinn', 'gain')} ${fmt(st.added.gain, 3)}  ·  ν·g = ${fmt(th, 3)}`));
      const svg = svgBox(fig, 520, 160);
      hbars(svg, chk.checks.map(x => ({ label: tr('ohne ', 'without ') + x.term, v: x.cost, color: x.qualifies ? 'var(--bad)' : 'var(--foba)', text: fmt(x.cost, 3) + (chk.removed && chk.removed.term === x.term ? tr(' → raus', ' → out') : tr(' → bleibt', ' → stays')) })), { lo: 1e-5, hi: 1, left: 100, threshold: th, thLabel: 'ν·g = ' + fmt(th, 3), axis: tr('Fehleranstieg beim Weglassen (log)', 'error rise when left out (log)') });
    }, steps: 4 });

  // 11 archive
  scene({ id: 's11', part: 'weak', title: ['Die Kandidatenliste', 'The candidate list'],
    core: ['Nach jeder vollständigen Forward-Backward-Runde wird der Stand des Modells festgehalten.', 'After every complete forward-backward round the model state is recorded.'],
    text: [
      () => tr(`<p>Jeder abgeschlossene Schritt hinterlässt einen Kandidaten: die Struktur nach Hinzufügen und Aufräumen, mit ihren Weak-Form-Koeffizienten. Zwischenzustände, die nur kurz getestet wurden, werden nicht gespeichert.</p>`, `<p>Every completed step leaves one candidate: the structure after adding and cleaning up, with its weak-form coefficients. States that were only tested briefly are not stored.</p>`),
      () => tr(`<p>Für die Bakteriendaten entstehen vier Kandidaten. Zweimal hat der Rückwärtsschritt aufgeräumt.</p><p>Der letzte Kandidat ist <b>nicht automatisch</b> der beste. Welcher gewinnt, entscheidet erst der Trajektorienraum (Szenen 19 und 20).</p>`, `<p>The bacteria data produce four candidates. Twice the backward step cleaned up.</p><p>The last candidate is <b>not automatically</b> the best. Which one wins is decided only in trajectory space (scenes 19 and 20).</p>`)],
    draw(fig, k) {
      const a = el('div', 'archive');
      steps.forEach((s, i) => {
        const rm = s.backward.filter(b => b.removed).map(b => '− ' + b.removed.term);
        const r = el('div', 'arch' + (k === 0 && i > 0 ? ' off' : '') + (k === 0 && i === 0 ? ' cur' : ''));
        r.innerHTML = `<span class="id">S${i + 1}</span><span class="eqline">${esc(setText(s.support[0]))}</span><span class="op"><span class="k-foba">+ ${esc(s.added.term)}</span>${rm.length ? ' <span class="k-bad">' + esc(rm.join(' ')) + '</span>' : ''}</span>`;
        a.appendChild(r);
      });
      fig.appendChild(a);
    }, steps: 2 });

  // 12 local polynomial
  const N = L.noise, fo = N.focus, fi = fo.index;
  scene({ id: 's12', part: 'weak', title: ['Rauschen schätzen: ein lokales Polynom', 'Estimating noise: a local polynomial'],
    core: ['Wie stark die Messungen rauschen, schätzt WISP aus den Daten selbst.', 'WISP estimates how noisy the measurements are from the data themselves.'],
    text: [
      () => tr(`<p>Damit WISP später entscheiden kann, wann es aufhört, muss es wissen, wie groß das Rauschen ist. Die wahre Gleichung kennt es dafür nicht.</p><p>Für jeden Messpunkt werden die <b>9</b> benachbarten Messungen genommen (am Rand verschoben). Hier für Messung ${fi}.</p>`,
        `<p>To decide later when to stop, WISP needs to know how large the noise is. It does not know the true equation for that.</p><p>For every measurement it takes the <b>9</b> neighbouring measurements (shifted at the edges). Here for measurement ${fi}.</p>`),
      () => tr(`<p>Durch diese neun Werte wird per Least Squares ein <b>Polynom dritten Grades</b> gelegt. Es ist nur ein lokales Hilfsmittel für die Rauschschätzung, nicht die gesuchte Gleichung.</p>`, `<p>A <b>cubic polynomial</b> is fitted through these nine values by least squares. It is only a local aid for the noise estimate, not the equation being sought.</p>`),
      () => tr(`<p>Der Restfehler am betrachteten Punkt ist <span class="math">rᵢ = yᵢ − Polynomᵢ = ${fmt(fo.r, 3)}</span>.</p>`, `<p>The residual at the focus point is <span class="math">rᵢ = yᵢ − polynomialᵢ = ${fmt(fo.r, 3)}</span>.</p>`)],
    draw(fig, k) {
      const a = fo.start - 6, b = fo.start + 15, ts = t.slice(a, b), ys = y.slice(a, b);
      const lo = Math.min(...ys) - 1, hi = Math.max(...ys) + 1;
      const svg = svgBox(fig, 520, 280), F = frame(svg, { w: 520, h: 280, x0: ts[0], x1: ts[ts.length - 1], y0: lo, y1: hi, xlabel: 't', ylabel: 'u' });
      S('rect', { x: F.X(t[fo.start]) - 4, y: F.m.t, width: F.X(t[fo.start + 8]) - F.X(t[fo.start]) + 8, height: 280 - F.m.t - F.m.b, fill: 'var(--noise-soft)' }, F.g);
      ts.forEach((x, i) => { const j = a + i, inW = j >= fo.start && j < fo.start + 9; S('circle', { cx: F.X(x), cy: F.Y(ys[i]), r: j === fi ? 5 : 3.2, fill: inW ? 'var(--data)' : 'var(--muted)', 'fill-opacity': inW ? 1 : .4 }, F.g); });
      if (k >= 1) curve(F.g, F, fo.poly_t, fo.poly, { stroke: 'var(--noise)' });
      if (k >= 2) {
        const pv = y[fi] - fo.r;
        S('line', { x1: F.X(t[fi]), x2: F.X(t[fi]), y1: F.Y(y[fi]), y2: F.Y(pv), stroke: 'var(--noise)', 'stroke-width': 2.5 }, F.g);
        TX(F.g, F.X(t[fi]) + 8, (F.Y(y[fi]) + F.Y(pv)) / 2 + 4, 'r = ' + fmt(fo.r, 3), { 'font-size': 13, fill: 'var(--noise)', 'font-weight': 600 });
      }
    }, steps: 3 });

  // 13 leverage
  scene({ id: 's13', part: 'weak', title: ['Leverage: warum der Abstand korrigiert wird', 'Leverage: why the residual is corrected'],
    core: ['Der Punkt hat die Kurve, an der sein Abstand gemessen wird, selbst mitgezogen.', 'The point has pulled the curve its residual is measured against.'],
    text: [
      () => tr(`<p>Das Polynom wurde mit dem betrachteten Punkt selbst gefittet. Es weicht ihm deshalb ein Stück entgegen, und <span class="math">rᵢ</span> fällt systematisch zu klein aus.</p><p>Wie stark, sagt der <b>Leverage</b> <span class="math">hᵢᵢ</span>. Er folgt aus der Geometrie der lokalen Regression: den Zeitpunkten der neun Messungen und der kubischen Basis. Mit dem Messfehler selbst hat er nichts zu tun. Hier ist <span class="math">hᵢᵢ = ${fmt(fo.h, 3)}</span>.</p>`,
        `<p>The polynomial was fitted with the focus point included. It therefore bends towards that point, and <span class="math">rᵢ</span> comes out systematically too small.</p><p>How much is given by the <b>leverage</b> <span class="math">hᵢᵢ</span>. It follows from the geometry of the local regression: the times of the nine measurements and the cubic basis. It has nothing to do with the measurement error itself. Here <span class="math">hᵢᵢ = ${fmt(fo.h, 3)}</span>.</p>`),
      () => tr(`<p>WISP verwendet das korrigierte Residuum <span class="math">rᵢ / √(1 − hᵢᵢ) = ${fmt(fo.r, 3)} / √(1 − ${fmt(fo.h, 3)}) = ${fmt(fo.corrected, 3)}</span>. Es hat im Mittel die Varianz des Messrauschens.</p><p>Weder der Messpunkt noch das Polynom werden dabei verschoben. Es wird nur gerechnet. Nicht verwechseln mit dem Leave-one-out-Residuum <span class="math">rᵢ/(1 − hᵢᵢ)</span>.</p>`,
        `<p>WISP uses the corrected residual <span class="math">rᵢ / √(1 − hᵢᵢ) = ${fmt(fo.r, 3)} / √(1 − ${fmt(fo.h, 3)}) = ${fmt(fo.corrected, 3)}</span>. On average it has the variance of the measurement noise.</p><p>Neither the point nor the polynomial is moved. It is arithmetic only. Not to be confused with the leave-one-out residual <span class="math">rᵢ/(1 − hᵢᵢ)</span>.</p>`)],
    draw(fig, k) {
      const svg = svgBox(fig, 520, 190), X0 = 160, sc = 160;
      const rows = [{ l: 'rᵢ', v: fo.r }, { l: 'rᵢ / √(1 − hᵢᵢ)', v: fo.corrected }];
      S('line', { x1: X0, x2: X0, y1: 20, y2: 150, stroke: 'var(--muted)' }, svg);
      rows.forEach((r, i) => {
        if (i === 1 && k < 1) return;
        const yy = 40 + i * 60, w = Math.abs(r.v) * sc;
        TX(svg, X0 - 10, yy + 18, r.l, { 'text-anchor': 'end', 'font-size': 14, class: 'mono' });
        S('rect', { x: r.v < 0 ? X0 - w : X0, y: yy, width: w, height: 28, fill: 'var(--noise)', 'fill-opacity': i ? .9 : .5 }, svg);
        TX(svg, X0 + 8 + (r.v > 0 ? w : 0), yy + 19, fmt(r.v, 3), { 'font-size': 13.5 });
      });
      TX(svg, 510, 180, 'hᵢᵢ = ' + fmt(fo.h, 3), { 'text-anchor': 'end', 'font-size': 13, class: 'mono' });
    }, steps: 2 });

  // 14 9 then 21
  scene({ id: 's14', part: 'weak', title: ['Erst 9, dann 21', 'First 9, then 21'],
    core: ['Zwei Nachbarschaften für zwei Aufgaben: 9 Messungen für ein Residuum, 21 Residuen für eine Varianz.', 'Two neighbourhoods, two jobs: 9 measurements per residual, 21 residuals per variance.'],
    text: [
      () => tr(`<p>Das Neunerfenster wandert über die ganze Messreihe und liefert <b>ein korrigiertes Residuum je Messung</b>. Das sind die ${L.n} Punkte rechts.</p>`, `<p>The nine-point window slides over the whole series and yields <b>one corrected residual per measurement</b>: the ${L.n} dots on the right.</p>`),
      () => tr(`<p>Danach wandert ein Fenster aus <b>21</b> Residuen darüber. Deren Quadrate werden gemittelt: <span class="math">σ̂ᵢ² = Mittel über 21 Werte von [rⱼ/√(1 − hⱼⱼ)]²</span>. Für Messung ${fi}: <span class="math">σ̂² = ${fmt(fo.variance, 3)}</span>, also eine Standardabweichung von <span class="math">${fmt(Math.sqrt(fo.variance), 3)}</span> in Einheiten von <span class="math">u</span>.</p>`,
        `<p>Then a window of <b>21</b> residuals slides over them, and their squares are averaged: <span class="math">σ̂ᵢ² = mean over 21 values of [rⱼ/√(1 − hⱼⱼ)]²</span>. For measurement ${fi}: <span class="math">σ̂² = ${fmt(fo.variance, 3)}</span>, a standard deviation of <span class="math">${fmt(Math.sqrt(fo.variance), 3)}</span> in units of <span class="math">u</span>.</p>`),
      () => tr(`<p>Das Ergebnis ist eine <b>Varianz je Messpunkt</b>, keine einzelne Zahl. Hier wächst sie mit der Kultur, weil das Messrauschen proportional zum Messwert ist.</p><p>9 und 21 sind feste Designentscheidungen, keine mathematisch zwingenden Konstanten.</p>`,
        `<p>The result is <b>one variance per measurement</b>, not a single number. Here it grows with the culture, because the noise is proportional to the measured value.</p><p>9 and 21 are fixed design choices, not mathematically forced constants.</p>`)],
    draw(fig, k) {
      const svg = svgBox(fig, 520, k >= 2 ? 400 : 220);
      const lim = 8;
      const A = frame(svg, { w: 520, h: 210, x0: 0, x1: 10, y0: -lim, y1: lim, ylabel: tr('korr. Residuum', 'corr. residual'), ny: 4 });
      if (k >= 1) { const [a, b] = fo.window21; S('rect', { x: A.X(t[a]), y: A.m.t, width: A.X(t[b - 1]) - A.X(t[a]), height: 210 - A.m.t - A.m.b, fill: 'var(--noise-soft)' }, A.g); }
      N.corrected.forEach((v, i) => S('circle', { cx: A.X(t[i]), cy: A.Y(Math.max(-lim, Math.min(lim, v))), r: 1.7, fill: 'var(--noise)', 'fill-opacity': .7 }, A.g));
      if (k >= 2) {
        const mx = Math.max(...N.variance) * 1.1;
        const B = frame(svg, { w: 520, h: 190, top: 210, x0: 0, x1: 10, y0: 0, y1: mx, xlabel: 't', ylabel: 'σ̂²', ny: 3 });
        curve(B.g, B, t, N.variance, { stroke: 'var(--noise)' });
        S('circle', { cx: B.X(t[fi]), cy: B.Y(fo.variance), r: 4, fill: 'var(--noise)' }, B.g);
      }
    }, steps: 3 });

  // 15 window noise
  const wn = L.window_noise;
  scene({ id: 's15', part: 'weak', title: ['Vom Punkt-Rauschen zum Fenster-Rauschen', 'From point noise to window noise'],
    core: ['Das Rauschen der Messwerte landet in b, denn b besteht aus Endpunktdifferenzen.', 'The noise of the measurements ends up in b, because b consists of endpoint differences.'],
    text: [
      () => tr(`<p>Das Fenster [${wn.start}, ${wn.end}] hat die gemessene Änderung <span class="math">y${sub(wn.end)} − y${sub(wn.start)}</span>. Beide Endpunkte tragen Rauschen mit den geschätzten Varianzen ${fmt(wn.var_start, 3)} und ${fmt(wn.var_end, 3)}.</p><p>Sind die beiden Fehler unabhängig, addieren sich die Varianzen: <span class="math">Var(b) = ${fmt(wn.var_start, 3)} + ${fmt(wn.var_end, 3)} = ${fmt(wn.var_b, 3)}</span>.</p>`,
        `<p>Window [${wn.start}, ${wn.end}] has the measured change <span class="math">y${sub(wn.end)} − y${sub(wn.start)}</span>. Both endpoints carry noise with estimated variances ${fmt(wn.var_start, 3)} and ${fmt(wn.var_end, 3)}.</p><p>If the two errors are independent, the variances add: <span class="math">Var(b) = ${fmt(wn.var_start, 3)} + ${fmt(wn.var_end, 3)} = ${fmt(wn.var_b, 3)}</span>.</p>`),
      () => tr(`<p>Aber Messung ${wn.end} ist zugleich Startpunkt des nächsten Fensters [${wn.end}, ${2 * wn.end - wn.start}]. Ihr Fehler steckt in beiden Differenzen, einmal mit Plus, einmal mit Minus. Die Fehler überlappender Fenster sind deshalb <b>korreliert</b>.</p><p>WISP fasst das in der Kovarianzmatrix <span class="math">C = D Σ Dᵀ</span> zusammen. <span class="math">Σ</span> enthält die Punktvarianzen, <span class="math">D</span> bildet Messwerte auf Endpunktdifferenzen ab. <span class="math">C</span> ist die Kovarianz der Zielwerte <span class="math">b</span>, nicht die ursprüngliche Punktvarianz.</p>`,
        `<p>But measurement ${wn.end} is also the start of the next window [${wn.end}, ${2 * wn.end - wn.start}]. Its error sits in both differences, once with a plus, once with a minus. The errors of overlapping windows are therefore <b>correlated</b>.</p><p>WISP collects this in the covariance matrix <span class="math">C = D Σ Dᵀ</span>. <span class="math">Σ</span> holds the point variances, <span class="math">D</span> maps measurements to endpoint differences. <span class="math">C</span> is the covariance of the targets <span class="math">b</span>, not the original point variance.</p>`)],
    draw(fig, k) {
      const svg = svgBox(fig, 520, 200), a = wn.start, e2 = 2 * wn.end - wn.start, X = i => 40 + (i - a + 1) * 440 / (e2 - a + 2);
      for (let i = a - 1; i <= e2 + 1; i++) { S('circle', { cx: X(i), cy: 110, r: i === a || i === wn.end || (k >= 1 && i === e2) ? 6 : 3, fill: 'var(--data)' }, svg); TX(svg, X(i), 136, i, { 'text-anchor': 'middle', 'font-size': 11, class: 'muted' }); }
      const arc = (i, j, yy, col, lab) => { S('path', { d: `M${X(i)} 100 C${X(i)} ${yy} ${X(j)} ${yy} ${X(j)} 100`, fill: 'none', stroke: col, 'stroke-width': 2.5 }, svg); TX(svg, (X(i) + X(j)) / 2, yy + 14, lab, { 'text-anchor': 'middle', 'font-size': 12.5, fill: col, 'font-weight': 600 }); };
      arc(a, wn.end, 30, 'var(--data)', 'b₁ = y' + sub(wn.end) + ' − y' + sub(a));
      if (k >= 1) { arc(wn.end, e2, 30, 'var(--lib)', 'b₂ = y' + sub(e2) + ' − y' + sub(wn.end)); TX(svg, X(wn.end), 170, tr('gemeinsamer Punkt → b₁, b₂ korreliert', 'shared point → b₁, b₂ correlated'), { 'text-anchor': 'middle', 'font-size': 12.5, fill: 'var(--noise)', 'font-weight': 600 }); }
      TX(svg, X(a), 160, 'σ̂² = ' + fmt(wn.var_start, 3), { 'text-anchor': 'middle', 'font-size': 11.5, fill: 'var(--noise)' });
      if (k < 1) TX(svg, X(wn.end), 160, 'σ̂² = ' + fmt(wn.var_end, 3), { 'text-anchor': 'middle', 'font-size': 11.5, fill: 'var(--noise)' });
    }, steps: 2 });
  function sub(n) { return String(n).split('').map(c => '₀₁₂₃₄₅₆₇₈₉'[+c]).join(''); }

  // 16 expected noise gain
  const S3 = stops[3], rU2 = S3.rows.find(r => r.term === 'u²');
  scene({ id: 's16', part: 'weak', title: ['Was Rauschen allein an Gewinn bringen würde', 'What noise alone would gain'],
    core: ['Jeder zusätzliche Baustein senkt den Fehler ein wenig, selbst wenn er nur Rauschen erklärt.', 'Every extra block lowers the error a little, even if it only explains noise.'],
    text: [
      () => tr(`<p>Eine neue Spalte in G kann zufällige Schwankungen in b nachzeichnen. Wie viel Fehlerreduktion das allein bringen würde, lässt sich aus <span class="math">C</span> berechnen: der <b>erwartete Gewinn allein durch Messrauschen</b>, <span class="math">Δ_noise</span>.</p><p>Beispiel: Stand <span class="math">S = {u, u³}</span>, Kandidat <span class="math">u²</span>. Erwartet durch Rauschen: <span class="math">Δ_noise = ${fmt(rU2.noise, 3)}</span>.</p>`,
        `<p>A new column in G can trace random fluctuations in b. How much error reduction that alone would bring can be computed from <span class="math">C</span>: the <b>expected gain from measurement noise alone</b>, <span class="math">Δ_noise</span>.</p><p>Example: state <span class="math">S = {u, u³}</span>, candidate <span class="math">u²</span>. Expected from noise: <span class="math">Δ_noise = ${fmt(rU2.noise, 3)}</span>.</p>`),
      () => tr(`<p>Tatsächlich senkt <span class="math">u²</span> die SSE um <span class="math">Δ_actual = ${fmt(rU2.actual, 3)}</span>, gut ${fmt(rU2.ratio, 3)}-mal so viel. Das ist mehr, als Rauschen erklären kann.</p><p><span class="math">Δ_noise</span> ist nicht einfach die Punktvarianz <span class="math">σ̂²</span>. Es hängt von den Varianzen, der Fensterstruktur und der Richtung ab, die der neue Baustein öffnet.</p>`,
        `<p>In fact <span class="math">u²</span> lowers the SSE by <span class="math">Δ_actual = ${fmt(rU2.actual, 3)}</span>, about ${fmt(rU2.ratio, 3)} times as much. That is more than noise can explain.</p><p><span class="math">Δ_noise</span> is not simply the point variance <span class="math">σ̂²</span>. It depends on the variances, the window structure and the direction the new block opens up.</p>`)],
    draw(fig, k) {
      const svg = svgBox(fig, 520, 140);
      const rows = [{ label: 'Δ_noise', v: rU2.noise, color: 'var(--noise)' }];
      if (k >= 1) rows.push({ label: 'Δ_actual', v: rU2.actual, color: 'var(--foba)' });
      hbars(svg, rows, { lo: 0.1, hi: 1000, left: 80, axis: tr('SSE-Reduktion (log)', 'SSE reduction (log)') });
      const d = el('details', 'deep');
      d.innerHTML = tr(`<summary>Vertiefung: die Formeln</summary><p><span class="math">Σ = diag(σ̂ᵢ²)</span>, <span class="math">C = D Σ Dᵀ</span>. Der erwartete Rest-Fehler bei richtiger Struktur ist <span class="math">F(S) = tr[(I − P_S) C]</span>, wobei <span class="math">P_S</span> auf die Spalten von <span class="math">G_S</span> projiziert.</p><p>Hier: <span class="math">F({u, u³}) = ${fx(S3.floor, 2)}</span> und <span class="math">F({u, u², u³}) = ${fx(S3.floor - rU2.noise, 2)}</span>. Die Differenz ist <span class="math">Δ_noise = ${fmt(rU2.noise, 3)}</span>.</p><p>Zum Vergleich ist <span class="math">‖b‖² = ${fx(P.b_norm2[0], 0)}</span> und <span class="math">F(∅) = ${fx(stops[0].floor, 0)}</span>: ${pct(noiseShare, 0)} der Zielwert-Energie ist erwartetes Rauschen.</p>`,
        `<summary>In depth: the formulas</summary><p><span class="math">Σ = diag(σ̂ᵢ²)</span>, <span class="math">C = D Σ Dᵀ</span>. The expected remaining error under a correct structure is <span class="math">F(S) = tr[(I − P_S) C]</span>, where <span class="math">P_S</span> projects onto the columns of <span class="math">G_S</span>.</p><p>Here: <span class="math">F({u, u³}) = ${fx(S3.floor, 2)}</span> and <span class="math">F({u, u², u³}) = ${fx(S3.floor - rU2.noise, 2)}</span>. The difference is <span class="math">Δ_noise = ${fmt(rU2.noise, 3)}</span>.</p><p>For comparison <span class="math">‖b‖² = ${fx(P.b_norm2[0], 0)}</span> and <span class="math">F(∅) = ${fx(stops[0].floor, 0)}</span>: ${pct(noiseShare, 0)} of the target energy is expected noise.</p>`);
      fig.appendChild(d);
    }, steps: 2 });

  // 17 stop
  scene({ id: 's17', part: 'weak', title: ['Das Stoppkriterium', 'The stopping rule'],
    core: ['Es zählt nicht, ob ein Baustein den Fehler senkt, sondern ob er deutlich mehr senkt, als Rauschen allein würde.', 'What counts is not whether a block lowers the error, but whether it lowers it clearly more than noise alone would.'],
    text: [0, 1, 2, 3, 4].map(i => () => {
      const st = stops[i], best = st.rows.reduce((a, b) => ((b.ratio ?? Infinity) > (a.ratio ?? Infinity) ? b : a));
      const head = tr(`<p>Für jeden freien Baustein: <span class="math">ρ = Δ_actual / Δ_noise</span>. Die Schwelle ist <span class="math">χ²₁;₀,₉₉ ≈ ${fmt(L.threshold, 4)}</span>. Die Gleichung stoppt, wenn <b>kein</b> freier Baustein sie erreicht.</p>`,
        `<p>For each free block: <span class="math">ρ = Δ_actual / Δ_noise</span>. The threshold is <span class="math">χ²₁;₀.₉₉ ≈ ${fmt(L.threshold, 4)}</span>. The equation stops when <b>no</b> free block reaches it.</p>`);
      const freed = st.rows.map(r => r.term).filter(tm => !states[i].includes(tm) && states.slice(0, i).some(s => s.includes(tm)));
      const back = freed.length ? tr(`<p class="note">${freed.map(esc).join(' und ')} ${freed.length > 1 ? 'sind' : 'ist'} wieder frei: Der Backward-Schritt hat ${freed.length > 1 ? 'sie' : 'ihn'} entfernt (Szene 10). Entfernte Bausteine dürfen später wieder hinzukommen und werden deshalb erneut geprüft.</p>`,
        `<p class="note">${freed.map(esc).join(' and ')} ${freed.length > 1 ? 'are' : 'is'} free again: the backward step removed ${freed.length > 1 ? 'them' : 'it'} (scene 10). Removed blocks may come back later, so they are tested again.</p>`) : '';
      if (!st.stops) return head + back + tr(`<p>Stand <span class="math">${setText(states[i])}</span>: ${esc(best.term)} erreicht ρ = ${fmt(best.ratio, 3)}. Es geht weiter. Welcher Baustein dann genommen wird, entscheidet weiter der Gewinn aus Szene 9, nicht ρ.</p>`,
        `<p>State <span class="math">${setText(states[i])}</span>: ${esc(best.term)} reaches ρ = ${fmt(best.ratio, 3)}. The path continues. Which block is then taken is still decided by the gain of scene 9, not by ρ.</p>`);
      return head + back + tr(`<p>Stand <span class="math">${setText(states[i])}</span>: Der beste freie Baustein, ${esc(best.term)}, erreicht nur ρ = ${fmt(best.ratio, 3)}. <b>Die Gleichung stoppt.</b></p><p class="note">Der Test ist eine Heuristik, keine exakt kalibrierte Signifikanzprüfung: Er berücksichtigt das Rauschen in b, nicht vollständig das in G, und die Fenster überlappen. Daneben gibt es technische Abbrüche (Fehler praktisch null, Bibliothek erschöpft, kein positiver Gewinn). Nach Backward-Schritten wird der Stopp neu geprüft.</p>`,
        `<p>State <span class="math">${setText(states[i])}</span>: the best free block, ${esc(best.term)}, reaches only ρ = ${fmt(best.ratio, 3)}. <b>The equation stops.</b></p><p class="note">The test is a heuristic, not an exactly calibrated significance test: it accounts for the noise in b but not fully for that in G, and the windows overlap. There are also technical ends (error practically zero, library exhausted, no positive gain). After backward steps the stop is re-checked.</p>`);
    }),
    draw(fig, k) {
      const st = stops[k];
      fig.appendChild(el('div', 'eqline', 'S = ' + setText(states[k]) + (st.stops ? tr('  →  Stopp', '  →  stop') : '')));
      const svg = svgBox(fig, 520, 200);
      hbars(svg, st.rows.map(r => ({ label: r.term, v: r.ratio ?? 1e5, color: r.passes ? 'var(--foba)' : 'var(--noise)', text: 'ρ = ' + fmt(r.ratio, 3) })), { lo: 0.01, hi: 1e5, threshold: L.threshold, thLabel: fmt(L.threshold, 4), axis: tr('ρ = Δ_actual / Δ_noise (log)', 'ρ = Δ_actual / Δ_noise (log)') });
    }, steps: 5 });

  // 18 path frozen
  scene({ id: 's18', part: 'weak', title: ['Der Pfad steht, die Kandidaten bleiben', 'The path is done, the candidates remain'],
    core: ['WISP hört auf, weil keine Erweiterung mehr überzeugt. Die gespeicherten Kandidaten gehen weiter.', 'WISP stops because no extension is convincing any more. The stored candidates move on.'],
    text: [
      () => tr(`<p>Jeder Kandidat besteht aus seiner Struktur und den Koeffizienten aus der Weak Form. Eine Entscheidung ist das noch nicht: Ein kleiner Weak-Form-Fehler heißt nicht, dass die Gleichung als ODE eine gute Kurve erzeugt.</p><p>Ab hier wechselt WISP den Arbeitsraum.</p>`,
        `<p>Each candidate consists of its structure and the weak-form coefficients. That is not yet a decision: a small weak-form error does not mean the equation produces a good curve when solved as an ODE.</p><p>From here WISP changes its working space.</p>`)],
    draw(fig) {
      const tb = el('div', 'tablewrap');
      tb.innerHTML = `<table class="ntab"><tr><th>${tr('Kandidat', 'Candidate')}</th><th>${tr('Weak-Form-Gleichung', 'Weak-form equation')}</th><th>${tr('erklärt', 'explained')}</th></tr>${weak.slice(1).map((w, i) => `<tr><td>S${i + 1}</td><td>${esc(eqText(w.terms, w.coefficients))}</td><td>${pct(w.share, 1)}</td></tr>`).join('')}</table>`;
      fig.appendChild(tb);
    }, steps: 1 });

  // 19 refit
  const rf = { c: 0 };
  scene({ id: 's19', part: 'traj', title: ['Trajectory Refit: jedes Modell wirklich simulieren', 'Trajectory refit: actually simulate every model'],
    core: ['Jeder Kandidat wird als ODE gelöst und mit den Messungen verglichen. Die Struktur bleibt fest, Koeffizienten und Startwert werden neu angepasst.', 'Each candidate is solved as an ODE and compared with the measurements. The structure stays fixed; coefficients and initial state are refitted.'],
    text: [
      () => tr(`<p>Gestartet wird mit den Weak-Form-Koeffizienten und der ersten Messung als Anfangswert (gestrichelt). Das ist die Kurve, die der Kandidat ohne weitere Anpassung erzeugt.</p>`, `<p>The start uses the weak-form coefficients and the first measurement as initial state (dashed). That is the curve the candidate produces without further fitting.</p>`),
      () => tr(`<p>Dann optimiert ein BFGS-Lauf Koeffizienten <b>und</b> Anfangswert gemeinsam, so dass die simulierte Kurve den Messungen möglichst nahe kommt: <span class="math">L(c, x̂₀) = (1/N) Σ ‖x_sim(tᵢ) − yᵢ‖²</span>, mit <span class="math">N = ${L.N}</span>. Die ODE wird dabei immer wieder numerisch gelöst. Der Anfangswert wird mitgeschätzt, weil auch die erste Messung verrauscht ist.</p><p>Das ist nicht dieselbe Regression wie in FoBa: Dort lineare Least Squares auf Integralen, hier nichtlineare Optimierung einer Simulation.</p>`,
        `<p>Then one BFGS run optimizes coefficients <b>and</b> initial state together, so that the simulated curve comes as close as possible to the measurements: <span class="math">L(c, x̂₀) = (1/N) Σ ‖x_sim(tᵢ) − yᵢ‖²</span>, with <span class="math">N = ${L.N}</span>. The ODE is solved numerically again and again. The initial state is estimated as well because the first measurement is noisy too.</p><p>This is not the regression of FoBa: there linear least squares on integrals, here nonlinear optimization of a simulation.</p>`)],
    draw(fig, k, redraw) {
      const tabs = el('div', 'tabs');
      L.candidates.forEach((c, i) => { const b = el('button', '', 'S' + (i + 1)); b.type = 'button'; b.setAttribute('aria-pressed', i === rf.c); b.onclick = () => { rf.c = i; redraw(); }; tabs.appendChild(b); });
      fig.appendChild(tabs);
      const c = L.candidates[rf.c], terms = c.support[0];
      const svg = svgBox(fig, 520, 260), F = frame(svg, { w: 520, h: 260, x0: 0, x1: 10, y0: 0, y1: 90, xlabel: 't', ylabel: 'u' });
      dots(F.g, F, t, y, { 'fill-opacity': .35 });
      curve(F.g, F, t, c.start_curve.map(r => (r[0] == null ? null : Math.max(-5, Math.min(95, r[0])))), { stroke: 'var(--traj)', 'stroke-dasharray': '6 4', 'stroke-width': 1.8, 'stroke-opacity': k >= 1 ? .5 : 1 });
      if (k >= 1) curve(F.g, F, t, c.fit_curve.map(r => r[0]), { stroke: 'var(--traj)', 'stroke-width': 2.6 });
      const lg = el('div', 'legend', `<span><i style="background:var(--data)"></i>${tr('Messungen', 'measurements')}</span><span><i style="background:var(--traj);opacity:.6"></i>${tr('Start (Weak Form, x₀ = erste Messung)', 'start (weak form, x₀ = first measurement)')}</span>${k >= 1 ? `<span><i style="background:var(--traj)"></i>${tr('nach Refit', 'after refit')}</span>` : ''}`);
      fig.appendChild(lg);
      const tb = el('div', 'tablewrap');
      tb.innerHTML = `<table class="ntab"><tr><th></th><th>Start</th>${k >= 1 ? '<th>Refit</th>' : ''}</tr>${terms.map((n, i) => `<tr><td>${tr('Koeff.', 'coef.')} ${esc(n)}</td><td>${fmt(c.weak[i], 4)}</td>${k >= 1 ? `<td>${fmt(c.params[i], 4)}</td>` : ''}</tr>`).join('')}<tr><td>x₀</td><td>${fmt(c.observed_x0[0], 4)}</td>${k >= 1 ? `<td>${fmt(c.x0[0], 4)}</td>` : ''}</tr><tr><td>${tr('mittl. quadr. Fehler L', 'mean squared error L')}</td><td>${fmt(c.start_mse, 4)}</td>${k >= 1 ? `<td>${fmt(c.mse, 4)}</td>` : ''}</tr></table>`;
      fig.appendChild(tb);
      if (k >= 1) fig.appendChild(el('div', 'note', tr(`${c.loss_evals} Auswertungen der Verlustfunktion, jede mit einer ODE-Lösung.`, `${c.loss_evals} loss evaluations, each with one ODE solve.`)));
    }, steps: 2 });

  // 20 BIC
  const lnN = Math.log(L.N);
  scene({ id: 's20', part: 'traj', title: ['BIC: Genauigkeit gegen Komplexität', 'BIC: accuracy against complexity'],
    core: ['Die am besten passende Kurve ist nicht automatisch das beste Modell. Zusätzliche Bausteine können Rauschen nachzeichnen.', 'The best-fitting curve is not automatically the best model. Extra blocks can trace noise.'],
    text: [
      () => tr(`<p><span class="math">BIC(S) = N·ln(L_S) + (|S| + d)·ln(N)</span>. <span class="math">L_S</span> ist der Trajektorienfehler nach dem Refit, <span class="math">|S|</span> die Zahl der Koeffizienten, <span class="math">d = ${L.dim}</span> die Zahl der mitgeschätzten Anfangswerte, <span class="math">N = ${L.N}</span>. Kleiner ist besser.</p><p>Erst der Passungsteil <span class="math">N·ln(L_S)</span>:</p>`,
        `<p><span class="math">BIC(S) = N·ln(L_S) + (|S| + d)·ln(N)</span>. <span class="math">L_S</span> is the trajectory error after the refit, <span class="math">|S|</span> the number of coefficients, <span class="math">d = ${L.dim}</span> the number of estimated initial states, <span class="math">N = ${L.N}</span>. Smaller is better.</p><p>First the fit part <span class="math">N·ln(L_S)</span>:</p>`),
      () => tr(`<p>Dann der Strafteil: je Parameter <span class="math">ln(${L.N}) = ${fmt(lnN, 4)}</span>.</p>`, `<p>Then the penalty: <span class="math">ln(${L.N}) = ${fmt(lnN, 4)}</span> per parameter.</p>`),
      () => tr(`<p>Die Summe entscheidet: <b>${setText(winner.support[0])}</b> hat das kleinste BIC. In diesem Beispiel ist das der letzte Kandidat des Pfads; das ist nicht garantiert. BIC wählt nur unter den erzeugten Kandidaten. Liegt die wahre Struktur nicht auf dem Pfad, kann BIC sie nicht erfinden.</p>`,
        `<p>The sum decides: <b>${setText(winner.support[0])}</b> has the smallest BIC. In this example it is the last candidate on the path; that is not guaranteed. BIC only chooses among the candidates produced. If the true structure is not on the path, BIC cannot invent it.</p>`),
      () => tr(`<p><b>Konstruiertes Rechenbeispiel</b> (nicht aus den Daten), wann der kleinere Kandidat gewinnt: <span class="math">N = 20, d = 1</span>. M3 passt etwas besser als M2 (SSE 11,8 statt 12,0), aber die winzige Verbesserung rechtfertigt den zusätzlichen Parameter nicht. M2 gewinnt.</p>`,
        `<p><b>Constructed example</b> (not from the data) of when the smaller candidate wins: <span class="math">N = 20, d = 1</span>. M3 fits slightly better than M2 (SSE 11.8 instead of 12.0), but the tiny improvement does not justify the extra parameter. M2 wins.</p>`)],
    draw(fig, k) {
      const tb = el('div', 'tablewrap');
      if (k < 3) {
        tb.innerHTML = `<table class="ntab"><tr><th>${tr('Kandidat', 'Candidate')}</th><th>|S|</th><th>L_S</th><th>N·ln L</th>${k >= 1 ? '<th>(|S|+d)·ln N</th>' : ''}${k >= 2 ? '<th>BIC</th>' : ''}</tr>${L.candidates.map((c, i) => `<tr class="${k >= 2 && c.id === L.winner ? 'win' : ''}"><td>S${i + 1} ${esc(setText(c.support[0]))}</td><td>${c.k}</td><td>${fmt(c.mse, 4)}</td><td>${fx(c.fit_term, 1)}</td>${k >= 1 ? `<td>${fx(c.penalty, 1)}</td>` : ''}${k >= 2 ? `<td>${fx(c.bic, 1)}</td>` : ''}</tr>`).join('')}</table>`;
        fig.appendChild(tb);
        if (k >= 2) {
          const svg = svgBox(fig, 520, 170);
          hbars(svg, L.candidates.map((c, i) => ({ label: 'S' + (i + 1), v: c.bic, color: c.id === L.winner ? 'var(--traj)' : 'var(--bic)', dim: c.id !== L.winner, text: fx(c.bic, 1) })), { lo: 100, hi: 1e4, left: 40, axis: 'BIC (log)' });
        }
      } else {
        const toy = [['M1', 1, 20.0], ['M2', 2, 12.0], ['M3', 3, 11.8]].map(([m, s, sse]) => ({ m, s, sse, bic: 20 * Math.log(sse / 20) + (s + 1) * Math.log(20) }));
        const best = toy.reduce((a, b) => (b.bic < a.bic ? b : a));
        tb.innerHTML = `<table class="ntab"><tr><th>${tr('Modell', 'Model')}</th><th>|S|</th><th>SSE</th><th>|S|+1</th><th>BIC</th></tr>${toy.map(r => `<tr class="${r === best ? 'win' : ''}"><td>${r.m}</td><td>${r.s}</td><td>${fx(r.sse, 1)}</td><td>${r.s + 1}</td><td>${fx(r.bic, 2)}</td></tr>`).join('')}</table>`;
        fig.appendChild(tb);
        fig.appendChild(el('div', 'formula', `M2: 20·ln(12/20) + 3·ln(20) ≈ ${fx(toy[1].bic, 2)}`));
      }
    }, steps: 4 });

  // 21 result
  scene({ id: 's21', part: 'traj', title: ['Das Ergebnis', 'The result'],
    core: ['WISP gibt eine ausgewählte, refittete Gleichung zurück: Struktur, Koeffizienten, geschätzter Anfangswert.', 'WISP returns one selected, refitted equation: structure, coefficients, estimated initial state.'],
    text: [
      () => tr(`<p>Die Koeffizienten stammen aus dem Trajectory Refit, die Größe des Modells hat das Trajektorien-BIC entschieden.</p><p>Erst jetzt ziehen wir zum Vergleich die wahre Gleichung heran, die das Benchmark-System erzeugt hat. WISP hat sie nie gesehen.</p>`,
        `<p>The coefficients come from the trajectory refit; the model size was decided by the trajectory BIC.</p><p>Only now do we bring in, for comparison, the true equation that generated the benchmark system. WISP never saw it.</p>`),
      () => tr(`<p>Aus dem echten, rauschfreien Anfangswert simuliert, deckt das Modell die wahre Kurve: <span class="math">R² = ${fmt(winner.recon_r2, 6)}</span>.</p>`, `<p>Simulated from the true, noise-free initial state, the model matches the true curve: <span class="math">R² = ${fmt(winner.recon_r2, 6)}</span>.</p>`),
      () => tr(`<p>Und aus einem <b>anderen</b> Anfangswert (u₀ = ${fmt(L.other[0][0], 3)}), den WISP nie gesehen hat: <span class="math">R² = ${fmt(winner.gen_r2, 6)}</span>. Diese Generalisierung ist eine eigene Prüfung in der Auswertung, kein Teil der Auswahl.</p>`,
        `<p>And from a <b>different</b> initial state (u₀ = ${fmt(L.other[0][0], 3)}) that WISP never saw: <span class="math">R² = ${fmt(winner.gen_r2, 6)}</span>. This generalization is a separate check in the evaluation, not part of the selection.</p>`)],
    draw(fig, k) {
      const terms = winner.support[0];
      fig.appendChild(el('div', 'formula', '<span class="k-traj">WISP</span>    ' + esc(eqText(terms, winner.params, 'du/dt', 4)) + `   u₀ = ${fmt(winner.x0[0], 4)}<br><span style="color:var(--muted)">${tr('Wahrheit', 'truth')}</span>   ` + esc(eqText(terms, terms.map(n => truth[n]), 'du/dt', 4)) + `   u₀ = ${fmt(L.clean[0][0], 4)}`));
      if (k >= 1) {
        const svg = svgBox(fig, 520, 250), F = frame(svg, { w: 520, h: 250, x0: 0, x1: 10, y0: 0, y1: 80, xlabel: 't', ylabel: 'u' });
        curve(F.g, F, t, L.clean.map(r => r[0]), { stroke: 'var(--muted)', 'stroke-width': 6, 'stroke-opacity': .35 });
        curve(F.g, F, t, winner.recon_curve.map(r => r[0]), { stroke: 'var(--traj)' });
        if (k >= 2) { curve(F.g, F, t, L.other.map(r => r[0]), { stroke: 'var(--muted)', 'stroke-width': 6, 'stroke-opacity': .35 }); curve(F.g, F, t, winner.gen_curve.map(r => r[0]), { stroke: 'var(--traj)', 'stroke-dasharray': '6 3' }); }
        fig.appendChild(el('div', 'legend', `<span><i style="background:var(--muted);opacity:.5"></i>${tr('wahre Kurve', 'true curve')}</span><span><i style="background:var(--traj)"></i>${tr('WISP-Modell', 'WISP model')}</span>${k >= 2 ? `<span><i style="background:var(--traj)"></i>${tr('gestrichelt: neuer Anfangswert', 'dashed: new initial state')}</span>` : ''}`));
      }
    }, steps: 3 });

  // C coupled
  const LP = LV.path, LS = LP.steps, lvWin = LV.candidates.find(c => c.id === LV.winner);
  const stopEq1 = LP.stops.findIndex(s => s[0].stops);
  scene({ id: 'c1', part: 'coupled', num: 'C', title: ['Zwei gekoppelte Gleichungen', 'Two coupled equations'],
    core: ['Der Ablauf bleibt derselbe. Neu ist, dass beide Gleichungen um denselben nächsten Schritt konkurrieren.', 'The procedure stays the same. What is new is that both equations compete for the same next step.'],
    text: [
      () => tr(`<p>Räuber-Beute-System (Lotka–Volterra, Benchmark-System 27): Beute <span class="math">x</span>, Räuber <span class="math">y</span>, ${LV.n} Messungen je Größe, 3 % Rauschen. Es gibt jetzt zwei Vektoren gemessener Änderungen, <span class="math">b_x</span> und <span class="math">b_y</span>. Die Bibliothek hat ${LV.names.length} Bausteine, darunter den Mischterm <span class="math">x·y</span>. Beide Gleichungen nutzen <b>dieselbe</b> Matrix G, jede hat ihre eigene Struktur.</p>`,
        `<p>Predator–prey system (Lotka–Volterra, benchmark system 27): prey <span class="math">x</span>, predator <span class="math">y</span>, ${LV.n} measurements each, 3 % noise. There are now two vectors of measured changes, <span class="math">b_x</span> and <span class="math">b_y</span>. The library has ${LV.names.length} blocks, including the mixed term <span class="math">x·y</span>. Both equations use the <b>same</b> matrix G; each has its own structure.</p>`),
      () => tr(`<p>Jeder Forward-Schritt wählt das beste <b>Paar (Gleichung, Baustein)</b> über beide Gleichungen. Dank der Normierung durch <span class="math">‖b_k‖²</span> sind die Gewinne vergleichbar. Backward prüft die aktiven Bausteine beider Gleichungen.</p><p>Der Pfad beginnt mit falschen Bausteinen (<span class="math">y³</span>, <span class="math">x³</span>, Kosinus). Ab Schritt 5 räumt Backward sie nach und nach weg. Gleichung 1 stoppt nach Schritt ${stopEq1}, Gleichung 2 wächst weiter. Im letzten Schritt kommt <span class="math">y</span> dazu, und drei falsche Bausteine fliegen nacheinander raus.</p>`,
        `<p>Each forward step picks the best <b>pair (equation, block)</b> across both equations. Thanks to the normalization by <span class="math">‖b_k‖²</span> the gains are comparable. Backward checks the active blocks of both equations.</p><p>The path starts with wrong blocks (<span class="math">y³</span>, <span class="math">x³</span>, cosines). From step 5 on, backward clears them away one by one. Equation 1 stops after step ${stopEq1}; equation 2 keeps growing. In the last step <span class="math">y</span> comes in, and three wrong blocks go one after another.</p>`),
      () => tr(`<p>Jeder Kandidat ist das <b>ganze</b> System zu einem Pfadzeitpunkt. Beim Refit wird das gekoppelte System gemeinsam integriert, weil <span class="math">x</span> und <span class="math">y</span> einander beeinflussen. Im BIC zählen alle Koeffizienten beider Gleichungen plus <span class="math">d = 2</span> Anfangswerte; <span class="math">N = ${LV.N}</span>.</p><p>Das BIC wählt Kandidat ${LV.candidates.indexOf(lvWin) + 1} von ${LV.candidates.length}.</p>`,
        `<p>Each candidate is the <b>whole</b> system at one point of the path. The refit integrates the coupled system jointly, because <span class="math">x</span> and <span class="math">y</span> affect each other. The BIC counts all coefficients of both equations plus <span class="math">d = 2</span> initial states; <span class="math">N = ${LV.N}</span>.</p><p>The BIC picks candidate ${LV.candidates.indexOf(lvWin) + 1} of ${LV.candidates.length}.</p>`),
      () => tr(`<p>Das Ergebnis neben der wahren Gleichung. Aus dem rauschfreien Anfangswert: <span class="math">R² = ${fmt(lvWin.recon_r2, 5)}</span>; aus dem anderen, nie gesehenen Anfangswert: <span class="math">R² = ${fmt(lvWin.gen_r2, 5)}</span>.</p><p>Nicht so vorstellen: Erst wird die x-Gleichung fertig gesucht, dann separat die y-Gleichung. Die Auswahl ist gemeinsam, die Simulation gekoppelt.</p>`,
        `<p>The result next to the true equation. From the noise-free initial state: <span class="math">R² = ${fmt(lvWin.recon_r2, 5)}</span>; from the other, never-seen initial state: <span class="math">R² = ${fmt(lvWin.gen_r2, 5)}</span>.</p><p>Do not picture it as: first the x equation is searched to the end, then the y equation separately. The selection is joint, the simulation coupled.</p>`)],
    draw(fig, k) {
      const lt = LV.t;
      if (k === 0) {
        const svg = svgBox(fig, 520, 260), F = frame(svg, { w: 520, h: 260, x0: 0, x1: 10, y0: 0, y1: 10, xlabel: 't', ylabel: 'x, y' });
        dots(F.g, F, lt, LV.y.map(r => r[0]), { fill: 'var(--data)' }, 'lx');
        dots(F.g, F, lt, LV.y.map(r => r[1]), { fill: 'var(--foba)' }, 'ly');
        fig.appendChild(el('div', 'legend', `<span><i style="background:var(--data)"></i>${tr('Beute x', 'prey x')}</span><span><i style="background:var(--foba)"></i>${tr('Räuber y', 'predator y')}</span>`));
        const sp = el('div', 'tablewrap');
        sp.innerHTML = `<table class="ntab split"><tr><th>${tr('Eine Zustandsgröße', 'One state variable')}</th><th style="text-align:left">${tr('Zwei gekoppelte', 'Two coupled')}</th></tr>${[[tr('ein b-Vektor', 'one b vector'), 'b_x, b_y'], [tr('eine Struktur', 'one structure'), tr('eine Struktur je Gleichung', 'one structure per equation')], [tr('Bausteine in u', 'blocks in u'), tr('Bausteine in x, y und x·y', 'blocks in x, y and x·y')], [tr('eine ODE', 'one ODE'), tr('gemeinsam simuliertes System', 'jointly simulated system')], [tr('ein Anfangswert', 'one initial state'), tr('zwei Anfangswerte', 'two initial states')]].map(r => `<tr><td style="font-family:var(--f-body)">${r[0]}</td><td style="text-align:left;font-family:var(--f-body)">${r[1]}</td></tr>`).join('')}</table>`;
        fig.appendChild(sp);
      } else if (k === 1) {
        const tb = el('div', 'tablewrap');
        tb.innerHTML = `<table class="ntab"><tr><th>${tr('Schritt', 'Step')}</th><th>${tr('hinzu', 'added')}</th><th>${tr('raus', 'removed')}</th><th style="text-align:left">dx/dt</th><th style="text-align:left">dy/dt</th></tr>${LS.map((s, i) => { const rm = s.backward.filter(b => b.removed).map(b => (b.removed.equation ? 'y: ' : 'x: ') + b.removed.term); return `<tr class="${rm.length ? 'hl' : ''}"><td>${s.step}${i + 1 >= stopEq1 ? ' <span title="eq 1 stopped" style="color:var(--muted)">■</span>' : ''}</td><td class="k-foba">${s.added.equation ? 'y' : 'x'}: ${esc(s.added.term)}</td><td class="k-bad">${esc(rm.join(', '))}</td><td style="text-align:left">${esc(setText(s.support[0]))}</td><td style="text-align:left">${esc(setText(s.support[1]))}</td></tr>`; }).join('')}</table>`;
        fig.appendChild(tb);
        fig.appendChild(el('div', 'note', tr(`■ Gleichung 1 hat die Stoppbedingung erreicht (ab Zustand ${stopEq1}). Markierte Zeilen: Backward hat entfernt.`, `■ equation 1 has met its stopping condition (from state ${stopEq1}). Marked rows: backward removed something.`)));
      } else if (k === 2) {
        const svg = svgBox(fig, 520, 280), mn = Math.min(...LV.candidates.map(c => c.bic)), mx = Math.max(...LV.candidates.map(c => c.bic));
        const F = frame(svg, { w: 520, h: 280, x0: 0.5, x1: LV.candidates.length + 0.5, y0: Math.floor(mn / 1000) * 1000, y1: Math.ceil(mx / 1000) * 1000, xticks: LV.candidates.map((_, i) => i + 1), xfmt: v => 'S' + v, ylabel: 'BIC', ny: 4 });
        LV.candidates.forEach((c, i) => { const y0 = F.Y(0), y1 = F.Y(c.bic); S('rect', { x: F.X(i + 1) - 14, y: Math.min(y0, y1), width: 28, height: Math.abs(y1 - y0), fill: c.id === LV.winner ? 'var(--traj)' : 'var(--bic)', 'fill-opacity': c.id === LV.winner ? 1 : .45 }, F.g); });
        S('line', { x1: F.X(.5), x2: F.X(LV.candidates.length + .5), y1: F.Y(0), y2: F.Y(0), stroke: 'var(--muted)' }, F.g);
      } else {
        const tn = LV.truth, p = lvWin.params, s = lvWin.support;
        let o = 0; const eqs = s.map((eq, e) => { const c = p.slice(o, o + eq.length); o += eq.length; return [eq, c, e]; });
        fig.appendChild(el('div', 'formula', eqs.map(([eq, c, e]) => '<span class="k-traj">WISP</span>   ' + esc(eqText(eq, c, e ? 'dy/dt' : 'dx/dt', 4))).join('<br>') + '<br>' + eqs.map(([eq, , e]) => `<span style="color:var(--muted)">${tr('Wahrheit', 'truth')}</span>   ` + esc(eqText(eq, eq.map(n => tn[e][n]), e ? 'dy/dt' : 'dx/dt', 4))).join('<br>')));
        const svg = svgBox(fig, 520, 240), F = frame(svg, { w: 520, h: 240, x0: 0, x1: 10, y0: 0, y1: 10, xlabel: 't', ylabel: 'x, y' });
        for (const j of [0, 1]) { curve(F.g, F, lt, LV.clean.map(r => r[j]), { stroke: 'var(--muted)', 'stroke-width': 6, 'stroke-opacity': .35 }); curve(F.g, F, lt, lvWin.recon_curve.map(r => r[j]), { stroke: j ? 'var(--foba)' : 'var(--data)' }); }
      }
    }, steps: 4 });

  /* ---------- morph: animate a figure from its previous state to the new one ----------
     Elements are paired by an explicit data-k key (data points, bars, cards) or, inside one scene, by their
     structural position. Paired SVG elements tween geometry and path data, paired HTML elements transition
     their class; new elements fade in, vanished ones fade out as ghosts. */
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const NUM = ['x', 'y', 'width', 'height', 'cx', 'cy', 'r', 'x1', 'x2', 'y1', 'y2', 'rx', 'opacity', 'fill-opacity', 'stroke-opacity', 'stroke-width'];
  const UNIT = new Set(['opacity', 'fill-opacity', 'stroke-opacity']);
  const NUMRE = /-?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?/gi;
  const ease = p => (p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
  function walk(root, fn) {
    const rec = (node, pk, ctx) => {
      const counts = {};
      for (const c of [...node.children]) {
        if (c.dataset && c.dataset.ghost) continue;
        const tag = c.tagName.toLowerCase(); counts[tag] = (counts[tag] || 0) + 1;
        const sk = pk + '/' + tag + counts[tag];
        rec(c, sk, fn(c, sk, c.getAttribute('data-k'), ctx));
      }
    };
    rec(root, '', true);
  }
  function snapshot(fig) {
    const S = new Map(), E = new Map(), base = fig.getBoundingClientRect();
    walk(fig, (c, sk, ek) => {
      const r = { el: c, tag: c.tagName.toLowerCase(), svg: c instanceof SVGElement, attrs: {}, cls: c.getAttribute('class') || '', text: c.children.length ? null : c.textContent, sk, ek };
      for (const a of c.attributes) r.attrs[a.name] = a.value;
      if (!r.svg && ek) { const b = c.getBoundingClientRect(); r.rect = [b.left - base.left, b.top - base.top]; }
      S.set(sk, r); if (ek) E.set(ek, r);
      return true;
    });
    return { S, E };
  }
  function pathTween(el, a, b) {
    if (a.replace(NUMRE, '#') !== b.replace(NUMRE, '#')) return null;
    const A = (a.match(NUMRE) || []).map(Number), B = (b.match(NUMRE) || []).map(Number), parts = b.split(NUMRE);
    return e => { let s = parts[0]; for (let i = 0; i < A.length; i++) s += (A[i] + (B[i] - A[i]) * e).toFixed(2) + parts[i + 1]; el.setAttribute('d', s); };
  }
  function morph(fig, snap, o = {}) {
    if (!snap || reduced.matches) return 0;
    const dur = o.dur || 700, delay = o.delay || 0, cross = !!o.cross;
    const sets = [], swaps = [], fades = [], flips = [], ghosts = [], newS = new Map(), newE = new Set(), oldGone = [];
    let paired = 0;
    const base = fig.getBoundingClientRect();
    walk(fig, (c, sk, ek, parentOk) => {
      const tag = c.tagName.toLowerCase(), isSvg = c instanceof SVGElement;
      newS.set(sk, c); if (ek) newE.add(ek);
      const old = ek ? snap.E.get(ek) : (cross ? null : snap.S.get(sk));
      if (!old || old.tag !== tag || (!ek && old.ek)) {
        // Across scenes only keyed elements pair; plain containers stay put so their keyed children can move.
        if (cross && !ek && (tag === 'svg' || tag === 'g' || tag === 'div')) return true;
        if (parentOk) fades.push(c);
        return false;
      }
      paired++;
      if (isSvg) {
        if (tag === 'svg' && old.attrs.viewBox && old.attrs.viewBox !== c.getAttribute('viewBox')) {
          const A = old.attrs.viewBox.split(/\s+/).map(Number), B = c.getAttribute('viewBox').split(/\s+/).map(Number);
          c.style.overflow = 'hidden';
          sets.push(e => { c.setAttribute('viewBox', A.map((v, i) => v + (B[i] - v) * e).join(' ')); if (e >= 1) c.style.overflow = ''; });
        }
        for (const a of NUM) {
          let nv = c.getAttribute(a), ov = old.attrs[a];
          if (nv == null && ov == null) continue;
          if (UNIT.has(a)) { nv = nv ?? '1'; ov = ov ?? '1'; } else if (nv == null || ov == null) continue;
          const A = parseFloat(ov), B = parseFloat(nv);
          if (A !== B && isFinite(A) && isFinite(B)) sets.push(e => c.setAttribute(a, A + (B - A) * e));
        }
        const od = old.attrs.d, nd = c.getAttribute('d');
        if (od != null && nd != null && od !== nd) {
          const f = pathTween(c, od, nd);
          if (f) sets.push(f); else { fades.push(c); if (!cross) oldGone.push(old); }
        }
        for (const a of ['fill', 'stroke']) {
          const nv = c.getAttribute(a), ov = old.attrs[a];
          if (nv && ov && nv !== ov) { c.setAttribute(a, ov); c.style.transition = `${a} ${dur}ms`; swaps.push(() => c.setAttribute(a, nv)); }
        }
      } else {
        const ncls = c.getAttribute('class') || '';
        if (ncls !== old.cls) { c.setAttribute('class', old.cls); swaps.push(() => c.setAttribute('class', ncls)); }
        if (cross && old.rect) flips.push([c, old.rect]);
      }
      if (old.text != null && !c.children.length && c.textContent !== old.text) fades.push(c);
      return true;
    });
    if (cross && paired < 3) return 0;
    // Old SVG elements without a partner fade out in place (same scene only), when their parent survived.
    if (!cross) {
      for (const [sk, r] of snap.S) {
        const kept = r.ek ? newE.has(r.ek) : (newS.has(sk) && newS.get(sk).tagName.toLowerCase() === r.tag && !newS.get(sk).getAttribute('data-k'));
        if (!kept) oldGone.push(r);
      }
      const goneKeys = new Set(oldGone.map(r => r.sk));
      for (const r of oldGone) {
        if (!r.svg) continue;
        const pk = r.sk.slice(0, r.sk.lastIndexOf('/'));
        if (!pk || goneKeys.has(pk)) continue;
        const host = newS.get(pk);
        if (!host || !(host instanceof SVGElement)) continue;
        const g = r.el.cloneNode(true); g.setAttribute('data-ghost', '1'); g.style.pointerEvents = 'none';
        host.appendChild(g); ghosts.push(g);
      }
    }
    if (fig._raf) cancelAnimationFrame(fig._raf);
    sets.forEach(f => f(0));
    const flipped = flips.map(([c, r]) => { const b = c.getBoundingClientRect(); return [c, r[0] - (b.left - base.left), r[1] - (b.top - base.top)]; });
    const opt = { duration: dur, delay, easing: 'cubic-bezier(.65,0,.35,1)', fill: 'backwards' };
    flipped.forEach(([c, dx, dy]) => { if (Math.abs(dx) + Math.abs(dy) > .5) c.animate([{ transform: `translate(${dx}px, ${dy}px)` }, { transform: 'none' }], opt); });
    fades.forEach(c => c.animate([{ opacity: 0, offset: 0 }], { duration: dur * .6, delay: delay + dur * .4, easing: 'ease-out', fill: 'backwards' }));
    ghosts.forEach(g => { const a = g.animate([{ opacity: 1 }, { opacity: 0 }], { duration: dur * .45, delay, fill: 'forwards' }); a.onfinish = () => g.remove(); });
    const t0 = performance.now() + delay;
    let swapped = false;
    const tick = now => {
      if (!swapped && now >= t0) { swapped = true; swaps.forEach(f => f()); }
      const p = Math.max(0, Math.min(1, (now - t0) / dur)), e = ease(p);
      sets.forEach(f => f(e));
      fig._raf = p < 1 ? requestAnimationFrame(tick) : 0;
    };
    fig._raf = requestAnimationFrame(tick);
    return paired;
  }

  /* ---------- page assembly ---------- */
  const OVER = {
    weak: [['01', 's01'], ['02', 's02'], ['03', 's03'], ['04', 's04'], ['05', 's05'], ['06', 's06'], ['07', 's07'], ['08', 's08'], ['09', 's09'], ['10', 's10'], ['11', 's11'], ['12', 's12'], ['13', 's13'], ['14', 's14'], ['15', 's15'], ['16', 's16'], ['17', 's17'], ['18', 's18']],
    traj: [['19', 's19'], ['20', 's20'], ['21', 's21'], ['C', 'c1']] };
  const titleOf = sc => sc.title[lang === 'de' ? 0 : 1];
  const where = document.getElementById('where');
  let deck = false, pageIdx = 0, pages = [], rail = null;
  const sceneOf = p => (p ? SC.find(s => s.sec === p) : null);
  function render() {
    document.documentElement.lang = lang;
    document.querySelectorAll('[data-i18n]').forEach(e => { e.innerHTML = I18N[lang][e.dataset.i18n]; });
    document.querySelectorAll('.lang button').forEach(b => b.setAttribute('aria-pressed', b.dataset.lang === lang));
    const ov = document.getElementById('overview'); ov.innerHTML = '';
    const z1 = el('div', 'zone weak', `<h2>${tr('Weak-Form-Raum', 'Weak-form space')}</h2><p>${tr('Lineare Regression auf Fenster-Integralen. Schnelle Strukturvorschläge, keine Ableitung der Messwerte, keine Simulation je Test.', 'Linear regression on window integrals. Fast structure proposals, no differentiation of the data, no simulation per test.')}</p>`);
    const z2 = el('div', 'zone traj', `<h2>${tr('Trajektorienraum', 'Trajectory space')}</h2><p>${tr('Echte ODE-Simulation, nichtlineare Anpassung, Auswahl nach Fehler und Komplexität.', 'Actual ODE simulation, nonlinear fitting, selection by error and complexity.')}</p>`);
    [[z1, OVER.weak], [z2, OVER.traj]].forEach(([z, list]) => { const ch = el('div', 'chips'); list.forEach(([n, id]) => { const sc = SC.find(s => s.id === id); const a = el('a', '', `<span>${n}</span>${esc(titleOf(sc))}`); a.href = '#' + id; ch.appendChild(a); }); z.appendChild(ch); });
    ov.append(z1, z2, el('div', 'flowline', tr('<b>Merksatz:</b> Die Weak Form erzeugt und ordnet plausible Strukturen. Die Simulation prüft ihre tatsächliche Dynamik. Das BIC entscheidet zwischen den refitteten Kandidaten.', '<b>In one line:</b> the weak form proposes and ranks plausible structures. Simulation tests their actual dynamics. The BIC decides between the refitted candidates.')));
    const host = document.getElementById('scenes'); host.innerHTML = '';
    SC.forEach((sc, i) => {
      sc.k = sc.k || 0;
      const sec = el('section', 'scene page'); sec.id = sc.id; sec.dataset.part = sc.part;
      const n = sc.num || String(i + 1).padStart(2, '0');
      const text = el('div', 'text', `<div class="snum">${n} · ${sc.part === 'weak' ? tr('Weak-Form-Raum', 'Weak-form space') : sc.part === 'traj' ? tr('Trajektorienraum', 'Trajectory space') : tr('Gekoppelte Systeme', 'Coupled systems')}</div><h3>${esc(titleOf(sc))}</h3><p class="core">${sc.core[lang === 'de' ? 0 : 1]}</p>`);
      text.dataset.scroll = '1';
      const st = el('div', 'steptext'); text.appendChild(st);
      const figWrap = el('div', 'figure'), fig = el('div', 'figbody'), ctr = el('div', 'controls');
      figWrap.dataset.scroll = '1';
      figWrap.append(fig, ctr);
      const prev = el('button', '', '← ' + tr('Zurück', 'Back')), next = el('button', '', tr('Weiter', 'Next') + ' →'), dts = el('div', 'dots'), lab = el('span', 'steplabel');
      prev.type = next.type = 'button';
      ctr.append(prev, next, dts, lab);
      // o.anim: morph from the current drawing; o.dir: +1/-1 slides the step text in; o.from: figure of the neighbouring scene.
      const show = (o = {}) => {
        const snap = o.from ? snapshot(o.from) : (o.anim ? snapshot(fig) : null);
        fig.innerHTML = '';
        const tx = sc.text[sc.k] || sc.text[sc.text.length - 1];
        st.innerHTML = typeof tx === 'function' ? tx() : tx;
        sc.draw(fig, sc.k, () => show({ anim: true }));
        if (snap) morph(fig, snap, { cross: !!o.from, delay: o.delay || 0, dur: o.from ? 900 : 700 });
        if (o.dir && !reduced.matches) st.animate([{ opacity: 0, transform: `translateY(${o.dir * 28}px)` }, { opacity: 1, transform: 'none' }], { duration: 520, easing: 'cubic-bezier(.2,.7,.2,1)' });
        prev.disabled = sc.k === 0; next.disabled = sc.k >= sc.steps - 1;
        dts.innerHTML = sc.steps > 1 ? Array.from({ length: sc.steps }, (_, j) => `<i class="${j === sc.k ? 'on' : ''}"></i>`).join('') : '';
        lab.textContent = sc.steps > 1 ? tr(`Schritt ${sc.k + 1} von ${sc.steps}`, `Step ${sc.k + 1} of ${sc.steps}`) : '';
        ctr.hidden = sc.steps <= 1;
        if (pages[pageIdx] === sec) chrome();
      };
      sc.fig = fig; sc.sec = sec;
      sc.setK = (k, o = {}) => { sc.k = Math.max(0, Math.min(sc.steps - 1, k)); if (sc.enter) sc.enter(sc.k); show(o); };
      sc.go = d => { const k = Math.max(0, Math.min(sc.steps - 1, sc.k + d)); if (k === sc.k) return false; sc.setK(k, { anim: true, dir: d }); return true; };
      prev.onclick = () => sc.go(-1); next.onclick = () => sc.go(1);
      sec.addEventListener('keydown', e => { if (deck || e.target.closest('input,details')) return; if (e.key === 'ArrowRight') { sc.go(1); e.preventDefault(); } if (e.key === 'ArrowLeft') { sc.go(-1); e.preventDefault(); } });
      sec.append(text, figWrap); host.appendChild(sec);
      show();
    });
    pages = [...document.querySelectorAll('.page')];
    buildRail();
  }

  /* ---------- deck: one full-screen page per scene, its steps inside, eased slides between pages ---------- */
  function buildRail() {
    if (rail) rail.remove();
    rail = el('nav', 'rail'); rail.setAttribute('aria-label', tr('Seiten', 'Pages'));
    pages.forEach((p, i) => {
      const a = el('a'); a.href = '#' + p.id;
      const sc = sceneOf(p);
      a.title = sc ? (sc.num || String(SC.indexOf(sc) + 1).padStart(2, '0')) + ' · ' + titleOf(sc) : ({ start: tr('Titel', 'Title'), 'overview-page': tr('Übersicht', 'Overview'), basis: tr('Grundlage', 'Basis') })[p.id];
      a.setAttribute('aria-label', a.title);
      a.addEventListener('click', e => { e.preventDefault(); goPage(i, 1); });
      rail.appendChild(a);
    });
    document.body.appendChild(rail);
  }
  function chrome() {
    const sc = sceneOf(pages[pageIdx]);
    where.innerHTML = I18N[lang].where + (sc ? ` · <b>${esc(titleOf(sc))}</b>` + (sc.steps > 1 ? ` <span class="pos">${sc.k + 1}/${sc.steps}</span>` : '') : '');
    if (rail) [...rail.children].forEach((a, i) => { if (i === pageIdx) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
  }
  const pageTop = p => p.getBoundingClientRect().top + window.scrollY;
  let anim = 0, busyUntil = 0;
  function slideTo(target, ms = 760) {
    cancelAnimationFrame(anim);
    const from = window.scrollY, start = performance.now(); busyUntil = start + ms;
    const frameFn = now => { const p = Math.min(1, (now - start) / ms); window.scrollTo(0, from + (target - from) * ease(p)); if (p < 1) anim = requestAnimationFrame(frameFn); };
    anim = requestAnimationFrame(frameFn);
  }
  function goPage(i, dir = 1, instant = false) {
    i = Math.max(0, Math.min(pages.length - 1, i));
    const from = pageIdx, tgt = pages[i], sc = sceneOf(tgt), before = sceneOf(pages[from]);
    if (sc && !instant && i !== from) {
      const neighbour = Math.abs(i - from) === 1 && before ? before.fig : null;
      sc.setK(dir > 0 ? 0 : sc.steps - 1, neighbour ? { from: neighbour, delay: 420 } : {});
    }
    pageIdx = i; chrome();
    try { history.replaceState(null, '', '#' + tgt.id); } catch (e) { /* sandboxed */ }
    if (deck) { if (instant || reduced.matches) { cancelAnimationFrame(anim); window.scrollTo(0, pageTop(tgt)); } else slideTo(pageTop(tgt)); }
    else if (!instant) tgt.scrollIntoView({ behavior: reduced.matches ? 'auto' : 'smooth' });
    else if (i > 0) tgt.scrollIntoView();
  }
  function step(d) {
    const sc = sceneOf(pages[pageIdx]);
    if (sc && sc.go(d)) return;
    if (pageIdx + d >= 0 && pageIdx + d < pages.length) goPage(pageIdx + d, d);
  }
  function setMode() {
    deck = window.innerWidth >= 860 && window.innerHeight >= 560 && !reduced.matches;
    document.documentElement.classList.toggle('deck', deck);
  }
  // Wheel and touch: one gesture, one step; a text or figure box that can still scroll scrolls first.
  function canScroll(target, d) {
    for (let n = target; n && n !== document.body; n = n.parentElement) {
      if (n.dataset && n.dataset.scroll && n.scrollHeight > n.clientHeight + 1 && ((d > 0 && n.scrollTop + n.clientHeight < n.scrollHeight - 1) || (d < 0 && n.scrollTop > 0))) return true;
      if (n.classList && n.classList.contains('tablewrap') && n.scrollWidth > n.clientWidth + 1 && d === 0) return true;
    }
    return false;
  }
  let lastWheel = -Infinity, wheelLock = 0;
  window.addEventListener('wheel', e => {
    if (!deck || e.ctrlKey) return;
    const raw = Math.abs(e.deltaY) >= Math.abs(e.deltaX) ? e.deltaY : 0;
    if (!raw) return; // horizontal wheel: leave to wide tables
    const d = Math.sign(raw);
    if (canScroll(e.target, d)) return;
    e.preventDefault();
    const now = performance.now(), quiet = now - lastWheel > 220; lastWheel = now;
    if (quiet && now >= wheelLock && now >= busyUntil && Math.abs(raw) > 2) { wheelLock = now + 650; step(d); }
  }, { passive: false });
  let touch = null;
  window.addEventListener('touchstart', e => { touch = deck && e.touches.length === 1 ? { x: e.touches[0].clientX, y: e.touches[0].clientY, t: e.target } : null; }, { passive: true });
  window.addEventListener('touchmove', e => { if (touch && !canScroll(touch.t, Math.sign(touch.y - e.touches[0].clientY))) e.preventDefault(); }, { passive: false });
  window.addEventListener('touchend', e => {
    if (!touch) return;
    const dy = touch.y - e.changedTouches[0].clientY, dx = touch.x - e.changedTouches[0].clientX;
    if (Math.abs(dy) > 60 && Math.abs(dy) > Math.abs(dx) && performance.now() >= busyUntil) step(Math.sign(dy));
    touch = null;
  });
  window.addEventListener('keydown', e => {
    if (!deck || e.altKey || e.ctrlKey || e.metaKey || e.target.closest('input,textarea,select')) return;
    const onButton = e.target.closest('button,summary,a');
    let d = 0;
    if (['ArrowDown', 'PageDown', 'ArrowRight'].includes(e.key) || (e.key === ' ' && !onButton && !e.shiftKey)) d = 1;
    if (['ArrowUp', 'PageUp', 'ArrowLeft'].includes(e.key) || (e.key === ' ' && !onButton && e.shiftKey)) d = -1;
    if (e.key === 'Home') { e.preventDefault(); goPage(0, 1); return; }
    if (e.key === 'End') { e.preventDefault(); goPage(pages.length - 1, 1); return; }
    if (!d) return;
    e.preventDefault();
    if (!e.repeat && performance.now() >= busyUntil) step(d);
  });
  document.addEventListener('click', e => {
    const a = e.target.closest('.chips a');
    if (!a) return;
    const i = pages.findIndex(p => '#' + p.id === a.getAttribute('href'));
    if (i < 0) return;
    e.preventDefault(); goPage(i, 1);
  });
  // Continuous mode (phones, short windows, reduced motion): native scrolling names the page in view.
  const obs = new IntersectionObserver(es => { if (deck) return; es.forEach(e => { if (e.isIntersecting) { const i = pages.indexOf(e.target); if (i >= 0) { pageIdx = i; chrome(); } } }); }, { rootMargin: '-45% 0px -50% 0px' });
  const watch = () => { obs.disconnect(); pages.forEach(p => obs.observe(p)); };
  window.addEventListener('hashchange', () => { const i = pages.findIndex(p => '#' + p.id === location.hash); if (i >= 0 && i !== pageIdx) goPage(i, 1); });
  let resizeT = 0;
  window.addEventListener('resize', () => { clearTimeout(resizeT); resizeT = setTimeout(() => { setMode(); goPage(pageIdx, 1, true); }, 120); });
  reduced.addEventListener('change', () => { setMode(); goPage(pageIdx, 1, true); });

  const I18N = {
    de: { eyebrow: 'WISP · Weak-form incremental structure pursuit', title: 'WISP Schritt für Schritt', motto: '„In der Weak Form die Struktur suchen; mit der simulierten Trajektorie entscheiden.“',
      lede: 'Wie WISP aus einer einzigen verrauschten Messreihe eine Differentialgleichung gewinnt, in 21 Szenen und einem Teil über gekoppelte Systeme. Jede Szene zeigt eine neue Operation und wird Schritt für Schritt aufgebaut. Alle Zahlen sind echte Rechnungen auf Benchmark-Daten (logistisches Wachstum, System 3, 3 % Rauschen), außer in den zwei als konstruiert markierten Lehrbeispielen.',
      hint: 'Weiter mit Mausrad, Pfeiltasten, Leertaste oder Wischen: ein Schritt pro Geste. Die Punkte rechts springen zu jeder Szene.',
      foot: 'Grundlage: Manuskriptentwurf vom 7. November 2026 und das Visualisierungsbriefing zum Prozess. Weak-Form-Pfad, Rauschschätzung und Stopp sind mit den eingefrorenen Q6/Q7-Funktionen gerechnet und im Browser nachgerechnet; Refit-Werte stammen aus den Q9-Läufen (Koeffizientengrenze 1000, Anfangswert mitgeschätzt). Kurven zur Darstellung sind mit SciPy (DOP853, 10⁻¹⁰) aus den gespeicherten Koeffizienten neu integriert.', where: 'WISP Schritt für Schritt' },
    en: { eyebrow: 'WISP · Weak-form incremental structure pursuit', title: 'WISP step by step', motto: '“Search for the structure in the weak form; decide with the simulated trajectory.”',
      lede: 'How WISP turns a single noisy time series into a differential equation, in 21 scenes and a part on coupled systems. Each scene introduces one new operation and is built up step by step. All numbers are real computations on benchmark data (logistic growth, system 3, 3 % noise), except in the two teaching examples marked as constructed.',
      hint: 'Advance with the mouse wheel, arrow keys, space bar or a swipe: one step per gesture. The dots on the right jump to any scene.',
      foot: 'Basis: manuscript draft of 7 November 2026 and the process visualization briefing. The weak-form path, noise estimate and stop are computed with the frozen Q6/Q7 functions and recomputed in the browser; refit values come from the Q9 runs (coefficient bound 1000, initial state estimated). Display curves are re-integrated with SciPy (DOP853, 10⁻¹⁰) from the stored coefficients.', where: 'WISP step by step' } };
  document.querySelectorAll('.lang button').forEach(b => b.addEventListener('click', () => {
    lang = b.dataset.lang; try { localStorage.setItem('wisp-process-lang', lang); } catch (e) { /* ignore */ }
    render(); watch(); goPage(pageIdx, 1, true);
  }));
  setMode();
  render(); watch();
  const startAt = location.hash ? pages.findIndex(p => '#' + p.id === location.hash) : 0;
  goPage(Math.max(0, startAt), 1, true);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => goPage(pageIdx, 1, true));
})();
