// All words of the page live here: one entry per page, German and English side by side.
// {name} placeholders are filled from the recorded data (DATA.facts), formatted per language.
window.UI = {
  de: {brand: 'WISP', parts: {A: 'Teil 1 · Warum Gleichungen', B: 'Teil 2 · WISP in Aktion', C: 'Teil 3 · Wie oft klappt das?'},
    lang: 'Sprache', hint: 'Weiter mit Scrollen, Wischen oder', hare: 'Hasen', fox: 'Füchse', time: 'Zeit',
    measured: 'Messpunkte', truth: 'Wahrheit', model: 'Modell', step: 'Schritt', play: 'Abspielen', pause: 'Pause',
    restart: 'Neu starten'},
  en: {brand: 'WISP', parts: {A: 'Part 1 · Why equations', B: 'Part 2 · WISP in action', C: 'Part 3 · How often does it work?'},
    lang: 'Language', hint: 'Continue by scrolling, swiping or', hare: 'Hares', fox: 'Foxes', time: 'Time',
    measured: 'Measurements', truth: 'Truth', model: 'Model', step: 'Step', play: 'Play', pause: 'Pause',
    restart: 'Restart'}
};

window.PAGES = [
  // ---------------------------------------------------------------- Part A
  {id: 'meadow', part: 'A', scene: 'lv', step: 'meadow',
   de: `<div class="eyebrow">Ein Explorable über WISP</div>
<h1>Hasen, Füchse und eine Gleichung</h1>
<p class="deck">Auf einer Wiese leben <span class="h">Hasen</span> und <span class="f">Füchse</span>. Gibt es viele Hasen, finden die Füchse reichlich Futter und vermehren sich. Dann werden die Hasen knapp, die Füchse hungern, und die Hasen erholen sich. Und alles beginnt von vorn.</p>
<p>Rechts zählen wir mit. Die beiden Kurven schwingen, Runde um Runde, ohne dass jemand sie anstößt.</p>
<p class="hint">{hint}</p>`,
   en: `<div class="eyebrow">An explorable about WISP</div>
<h1>Hares, foxes and an equation</h1>
<p class="deck">A meadow is home to <span class="h">hares</span> and <span class="f">foxes</span>. With plenty of hares, the foxes find food and multiply. Then hares become scarce, the foxes starve, and the hares recover. And it all starts again.</p>
<p>On the right we keep count. The two curves swing, round after round, without anyone pushing them.</p>
<p class="hint">{hint}</p>`},

  {id: 'state', part: 'A', scene: 'lv', step: 'phase',
   de: `<h2>Der Zustand jetzt bestimmt die Änderung jetzt</h2>
<p>Zwei Zahlen beschreiben die Wiese vollständig: wie viele <span class="h">Hasen</span>, wie viele <span class="f">Füchse</span>. Jedes solche Paar ist ein Punkt im Bild rechts. Und zu jedem Punkt gehört eine Richtung, in die sich die Wiese gerade bewegt: die Pfeile.</p>
<p>Die Wiese folgt einfach den Pfeilen. So entsteht der Kreislauf. Das ist ein <b>dynamisches System</b>.</p>
<p>Pendel, Epidemien, chemische Reaktionen, Herzschlag, Klima: alle funktionieren nach diesem Prinzip. Wer die Pfeile kennt, kennt die Zukunft.</p>`,
   en: `<h2>The state now decides the change now</h2>
<p>Two numbers describe the meadow completely: how many <span class="h">hares</span>, how many <span class="f">foxes</span>. Each such pair is a point in the picture on the right. And every point comes with a direction in which the meadow is moving right now: the arrows.</p>
<p>The meadow simply follows the arrows. That is where the cycle comes from. This is a <b>dynamical system</b>.</p>
<p>Pendulums, epidemics, chemical reactions, heartbeats, climate: they all work this way. Know the arrows and you know the future.</p>`},

  {id: 'ode', part: 'A', scene: 'lv', step: 'equation',
   de: `<h2>Die Pfeile als Gleichung</h2>
<p>Alle Pfeile zusammen passen in zwei Zeilen mit vier Zahlen. Jeder Teil der Gleichung ist ein Satz:</p>
<p><span class="term h" data-term="0">Hasen vermehren sich</span>, <span class="term h" data-term="1">Füchse fressen Hasen</span>, <span class="term f" data-term="2">Füchse sterben ohne Futter</span>, <span class="term f" data-term="3">Füchse vermehren sich durch Fressen</span>.</p>
<p>So eine Gleichung heißt <b>gewöhnliche Differentialgleichung</b> (ODE). Sie ist kurz, sie erklärt, warum etwas passiert, und sie sagt jede Zukunft voraus.</p>
<p class="small">Probier den Regler rechts: Was passiert, wenn sich die Hasen schneller vermehren?</p>`,
   en: `<h2>The arrows as an equation</h2>
<p>All the arrows fit into two lines with four numbers. Every part of the equation is a sentence:</p>
<p><span class="term h" data-term="0">hares multiply</span>, <span class="term h" data-term="1">foxes eat hares</span>, <span class="term f" data-term="2">foxes die without food</span>, <span class="term f" data-term="3">foxes multiply by eating</span>.</p>
<p>Such an equation is called an <b>ordinary differential equation</b> (ODE). It is short, it explains why things happen, and it predicts any future.</p>
<p class="small">Try the slider on the right: what happens when hares multiply faster?</p>`},

  {id: 'inverse', part: 'A', scene: 'lv', step: 'data',
   de: `<h2>Die umgekehrte Frage</h2>
<p>In Wirklichkeit kennt niemand die Gleichung. Wir haben nur Zählungen, und die sind ungenau: hier <b>{n_obs}</b> Messungen mit <b>{noise}</b> Rauschen. Welche Gleichung steckt dahinter?</p>
<p>Zwei Dinge machen das schwer. Erstens die schiere Auswahl: Aus 12 möglichen Bausteinen je Zeile lassen sich <b>{n_combos}</b> verschiedene Gleichungspaare bauen.</p>
<p>Zweitens das Rauschen. Die Pfeile sind Steigungen. Schätzt man eine Steigung aus zwei benachbarten Messpunkten, wird das Rauschen durch den winzigen Abstand geteilt und rund 70-fach verstärkt (oben rechts).</p>`,
   en: `<h2>The reverse question</h2>
<p>In reality nobody knows the equation. All we have are counts, and they are imprecise: here <b>{n_obs}</b> measurements with <b>{noise}</b> noise. Which equation is behind them?</p>
<p>Two things make this hard. First, the sheer choice: from 12 possible building blocks per line one can build <b>{n_combos}</b> different pairs of equations.</p>
<p>Second, the noise. The arrows are slopes. Estimate a slope from two neighbouring measurements and the noise is divided by their tiny distance and amplified about 70-fold (top right).</p>`},

  // ---------------------------------------------------------------- Part B
  {id: 'blocks', part: 'B', scene: 'wisp', step: 'blocks',
   de: `<div class="eyebrow">WISP in Aktion</div>
<h2>Ein Baukasten und leere Gleichungen</h2>
<p>WISP bekommt nur die Messpunkte und einen Baukasten: 12 Bausteine je Gleichung, von der Konstanten 1 über <span class="h">H</span>, <span class="f">F</span> und ihre Produkte bis zu Sinus und Kosinus.</p>
<p>WISP weiß nicht, welche davon richtig sind. Es beginnt mit zwei leeren Gleichungen und baut sie Stein für Stein auf. Wie, zeigen die nächsten Seiten, und zwar am echten Lauf auf genau diesen {n_obs} Messpunkten.</p>
<p class="small">WISP steht für <i>Weak-form Incremental Structure Pursuit</i>.</p>`,
   en: `<div class="eyebrow">WISP in action</div>
<h2>A box of building blocks and empty equations</h2>
<p>WISP gets only the measurements and a box of building blocks: 12 per equation, from the constant 1 via <span class="h">H</span>, <span class="f">F</span> and their products to sine and cosine.</p>
<p>WISP does not know which of them are right. It starts with two empty equations and builds them up block by block. The next pages show how, using the real run on exactly these {n_obs} measurements.</p>
<p class="small">WISP stands for <i>Weak-form Incremental Structure Pursuit</i>.</p>`},

  {id: 'weak', part: 'B', scene: 'wisp', step: 'weak',
   de: `<h2>Trick 1: Fenster statt Steigungen</h2>
<p>WISP schätzt keine Steigungen. Es fragt stattdessen: Um wie viel hat sich die Zahl der Hasen über ein kurzes <b>Fenster</b> verändert? Diese Änderung muss genau der Fläche unter der rechten Seite der Gleichung entsprechen.</p>
<p>Der Unterschied zweier Messwerte wird durch nichts geteilt. Das Rauschen bleibt klein, und je länger das Fenster, desto ruhiger. Zieh am Regler.</p>
<div class="why"><b>Warum das funktioniert</b>Änderung = Fläche unter der Steigung: der Hauptsatz der Analysis. Man muss die Steigung nie kennen. Aus Fenstern über 1 bis 16 Messabstände wird ein großes <i>lineares</i> Gleichungssystem, das sich für jede Bausteinwahl in Millisekunden lösen lässt.</div>`,
   en: `<h2>Trick 1: windows instead of slopes</h2>
<p>WISP does not estimate slopes. Instead it asks: by how much did the number of hares change over a short <b>window</b>? That change must equal the area under the right-hand side of the equation.</p>
<p>The difference of two measurements is divided by nothing. The noise stays small, and the longer the window, the calmer. Drag the slider.</p>
<div class="why"><b>Why this works</b>Change = area under the slope: the fundamental theorem of calculus. You never need the slope itself. Windows over 1 to 16 sampling gaps turn into one large <i>linear</i> system that can be solved for any choice of blocks in milliseconds.</div>`},

  {id: 'grow', part: 'B', scene: 'wisp', step: 'grow',
   de: `<h2>Trick 2: Wachsen, Stein für Stein</h2>
<p>Für jeden freien Baustein rechnet WISP aus, wie viel vom verbleibenden Fehler er <i>zusätzlich</i> erklären würde. Der beste kommt in seine Gleichung. Dann wird neu gerechnet.</p>
<p>Klick dich rechts durch die vier Schritte. Zuerst landet <b>H·F</b> in beiden Gleichungen: Das Fressen erklärt am meisten. Danach <span class="f">F</span> bei den Füchsen und <span class="h">H</span> bei den Hasen.</p>
<div class="why"><b>Warum das funktioniert</b>Weil das Fenstersystem linear ist, ist jeder Probeschritt nur eine kleine Regression, kein Simulieren. 24 Bausteine probieren kostet fast nichts.</div>`,
   en: `<h2>Trick 2: grow, block by block</h2>
<p>For every free block WISP computes how much of the remaining error it would explain <i>in addition</i>. The best one joins its equation. Then everything is recomputed.</p>
<p>Click through the four steps on the right. First <b>H·F</b> lands in both equations: eating explains the most. Then <span class="f">F</span> for the foxes and <span class="h">H</span> for the hares.</p>
<div class="why"><b>Why this works</b>Because the window system is linear, every trial step is just a small regression, no simulation. Trying 24 blocks costs almost nothing.</div>`},

  {id: 'prune', part: 'B', scene: 'wisp', step: 'prune',
   de: `<h2>Aufräumen</h2>
<p>Gierig wachsen kann schiefgehen: Ein früher Baustein passt zunächst grob und wird später überflüssig. Deshalb prüft WISP nach jedem Schritt jeden schon gewählten Baustein: Wie stark stiege der Fehler, wenn man ihn wieder herausnähme?</p>
<p>Steigt er um weniger als die Hälfte dessen, was der neue Baustein gerade gebracht hat, fliegt der alte raus. Hier war nichts zu reparieren: Alle Balken liegen rechts der Linie.</p>
<div class="why"><b>Warum das funktioniert</b>Nach jedem Paar aus Hinzufügen und Entfernen ist der Fehler kleiner als vorher. Das Verfahren kann nicht im Kreis laufen (FoBa, Zhang 2011).</div>`,
   en: `<h2>Tidying up</h2>
<p>Greedy growth can go wrong: an early block fits roughly at first and becomes superfluous later. So after each step WISP checks every block already chosen: how much would the error rise if it were taken out again?</p>
<p>If it rises by less than half of what the new block just gained, the old one is thrown out. Here there was nothing to repair: every bar lies right of the line.</p>
<div class="why"><b>Why this works</b>After every pair of adding and removing, the error is smaller than before. The procedure cannot run in circles (FoBa, Zhang 2011).</div>`},

  {id: 'stop', part: 'B', scene: 'wisp', step: 'stop',
   de: `<h2>Aufhören, wenn nur noch Rauschen übrig ist</h2>
<p>Unter Rauschen hilft jeder weitere Baustein ein kleines bisschen, weil er das Rauschen nachzeichnet. WISP schätzt aus den Daten, wie viel ein reiner Rauschbaustein im Mittel erklären würde, und vergleicht jeden freien Baustein damit.</p>
<p>Solange einer mehr als <b>{threshold}</b>-mal so viel bringt, geht es weiter. Nach Schritt 4 schafft der beste freie Baustein nur noch <b>{best_ratio}</b>. Beide Gleichungen hören auf.</p>
<div class="why"><b>Warum das funktioniert</b>Ein nutzloser Baustein liegt in 99 von 100 Fällen unter {threshold}: die übliche Signifikanzschwelle der Statistik, nicht von uns eingestellt.</div>`,
   en: `<h2>Stop when only noise is left</h2>
<p>Under noise every further block helps a little, because it traces the noise. WISP estimates from the data how much a pure noise block would explain on average, and compares every free block with that.</p>
<p>As long as one brings more than <b>{threshold}</b> times as much, growth continues. After step 4 the best free block reaches only <b>{best_ratio}</b>. Both equations stop.</p>
<div class="why"><b>Why this works</b>A useless block stays below {threshold} in 99 out of 100 cases: the usual significance threshold of statistics, not tuned by us.</div>`},

  {id: 'fit', part: 'B', scene: 'wisp', step: 'fit',
   de: `<h2>Vier Kandidaten, jetzt wird simuliert</h2>
<p>Jeder Zwischenstand des Pfades ist ein Kandidat: vier Stück, statt {n_combos}. Erst jetzt wird gerechnet wie in der Wirklichkeit: Jeder Kandidat wird simuliert, und ein Optimierer sucht die Zahlen, mit denen die Kurve den Messpunkten am nächsten kommt.</p>
<p>Auch der Startwert der Kurve wird mitgeschätzt, denn der erste Messpunkt ist genauso verrauscht wie alle anderen.</p>
<div class="why"><b>Warum das funktioniert</b>Der Optimierer startet bei den Zahlen aus den Fenstern, also schon im richtigen Tal. Ein einziger Versuch je Kandidat reicht.</div>`,
   en: `<h2>Four candidates, now we simulate</h2>
<p>Every intermediate state of the path is a candidate: four of them, instead of {n_combos}. Only now do we compute the way reality works: each candidate is simulated, and an optimizer finds the numbers that bring its curve closest to the measurements.</p>
<p>The starting point of the curve is estimated too, because the first measurement is just as noisy as all the others.</p>
<div class="why"><b>Why this works</b>The optimizer starts from the numbers found with the windows, so it is already in the right valley. A single attempt per candidate is enough.</div>`},

  {id: 'bic', part: 'B', scene: 'wisp', step: 'bic',
   de: `<h2>Wählen: Genauigkeit gegen Größe</h2>
<p>Mehr Bausteine passen immer ein bisschen besser. Das <b>BIC</b> wägt ab: Gute Passung zählt, jeder Baustein kostet einen festen Preis. Kleiner ist besser.</p>
<p>Kandidat 4 gewinnt deutlich, mit genau den vier richtigen Bausteinen. Und die gefundenen Zahlen liegen nahe an der Wahrheit:</p>
<div id="coef-table"></div>
<p class="small">BIC: Schwarz 1978. Keine Stellschraube.</p>`,
   en: `<h2>Choosing: accuracy against size</h2>
<p>More blocks always fit a little better. The <b>BIC</b> weighs it up: a good fit counts, every block costs a fixed price. Smaller is better.</p>
<p>Candidate 4 wins clearly, with exactly the four right blocks. And the numbers it found are close to the truth:</p>
<div id="coef-table"></div>
<p class="small">BIC: Schwarz 1978. No tuning knob.</p>`},

  {id: 'test', part: 'B', scene: 'wisp', step: 'test',
   de: `<h2>Die Gegenprobe</h2>
<p>Eine Kurve nachzeichnen kann vieles. Hat WISP den <i>Mechanismus</i> gefunden, muss das Modell auch eine Wiese vorhersagen, die es nie gesehen hat.</p>
<p>Wir starten es bei {ic2_h} Hasen und {ic2_f} Füchsen statt bei {ic1_h} und {ic1_f}. Die Vorhersage trifft die wahre Kurve: <b>R² = {gen_r2}</b> (1 wäre perfekt).</p>
<p>Das ist der Unterschied zwischen Kurvenanpassen und Verstehen.</p>`,
   en: `<h2>The cross-check</h2>
<p>Many things can trace a curve. If WISP found the <i>mechanism</i>, the model must also predict a meadow it has never seen.</p>
<p>We start it at {ic2_h} hares and {ic2_f} foxes instead of {ic1_h} and {ic1_f}. The prediction matches the true curve: <b>R² = {gen_r2}</b> (1 would be perfect).</p>
<p>That is the difference between fitting a curve and understanding it.</p>`},

  {id: 'why', part: 'B', scene: 'wisp', step: 'why',
   de: `<h2>Warum es so gut klappt</h2>
<ol class="reasons">
<li><b>Fenster statt Steigungen.</b> Das Rauschen wird gemittelt, nicht verstärkt.</li>
<li><b>Suchen ist lineare Algebra.</b> Der Pfad kostet Millisekunden und liefert eine Handvoll Kandidaten. Die teure Simulation braucht es nur für diese.</li>
<li><b>Entschieden wird ehrlich.</b> An der simulierten Kurve, mit einem festen Preis für jeden Baustein, und jeder Schritt hat eine Regel aus der Literatur statt einer Stellschraube.</li>
</ol>`,
   en: `<h2>Why it works so well</h2>
<ol class="reasons">
<li><b>Windows instead of slopes.</b> Noise is averaged, not amplified.</li>
<li><b>Searching is linear algebra.</b> The path costs milliseconds and yields a handful of candidates. Only those need the expensive simulation.</li>
<li><b>The decision is honest.</b> Made on the simulated curve, with a fixed price per block, and every step follows a rule from the literature instead of a tuning knob.</li>
</ol>`},

  // ---------------------------------------------------------------- Part C
  {id: 'rates', part: 'C', scene: 'results', step: 'rates',
   de: `<div class="eyebrow">Wie oft klappt das?</div>
<h2>Nicht nur bei Hasen und Füchsen</h2>
<p>WISP lief auf allen {n_systems} Systemen mit einer oder zwei Größen aus dem Benchmark ODEBench, mit 1 % und 5 % Rauschen, gleichmäßig und unregelmäßig gemessen. Zum Vergleich die etablierten Verfahren SINDy, Weak-SINDy, E-SINDy und WSINDy auf denselben Daten und mit denselben Bausteinen; bei den SINDy-Varianten zählt jeweils die bessere von zwei Einstellungen.</p>
<p>Zwei Maße, immer beide: <b>richtige Bausteine gefunden</b> (wo die Wahrheit im Baukasten liegt) und <b>Vorhersage von einem neuen Startwert</b> mit R² über 0,9.</p>
<p class="small"><span class="tag">vorläufig</span> Zahlen aus dem letzten Testlauf (Q8, finale Einstellung). Der Endlauf über alle 63 Systeme rechnet gerade.</p>`,
   en: `<div class="eyebrow">How often does it work?</div>
<h2>Not just hares and foxes</h2>
<p>WISP ran on all {n_systems} systems with one or two variables of the ODEBench benchmark, at 1 % and 5 % noise, sampled regularly and irregularly. For comparison, the established methods SINDy, Weak-SINDy, E-SINDy and WSINDy on the same data and with the same building blocks; for the SINDy variants the better of two settings counts.</p>
<p>Two measures, always both: <b>right blocks found</b> (where the truth is in the box) and <b>prediction from a new starting point</b> with R² above 0.9.</p>
<p class="small"><span class="tag">preliminary</span> Numbers from the last test run (Q8, final setting). The final run over all 63 systems is computing right now.</p>`},

  {id: 'limits', part: 'C', scene: 'results', step: 'limits',
   de: `<h2>Wo es schwer wird</h2>
<p>Mit drei Größen wird es deutlich härter. In einer Stichprobe exakt darstellbarer Systeme findet WISP die Struktur in {dim3_struct} der Fälle, die Vorhersage gelingt in {dim3_gen}. SINDy, Weak-SINDy und E-SINDy liegen dort nahe null, WSINDy bei {dim3_ws_struct} und {dim3_ws_gen}.</p>
<p>Chaotische Systeme wie Lorenz sind die schwersten: Kleine Fehler wachsen exponentiell, die Simulation ist teuer, und eine Vorhersage von einem neuen Startwert ist prinzipiell nur kurz möglich.</p>
<p>Und eine Grenze, die kein Verfahren überwindet: Ein Baustein, dessen Beitrag kleiner ist als das Rauschen, steckt nicht in den Daten.</p>`,
   en: `<h2>Where it gets hard</h2>
<p>With three variables it gets much harder. On a sample of exactly representable systems WISP finds the structure in {dim3_struct} of cases, the prediction succeeds in {dim3_gen}. SINDy, Weak-SINDy and E-SINDy are close to zero there, WSINDy at {dim3_ws_struct} and {dim3_ws_gen}.</p>
<p>Chaotic systems like Lorenz are the hardest: small errors grow exponentially, simulation is expensive, and predicting from a new starting point is only possible for a short time in principle.</p>
<p>And one limit no method overcomes: a block whose contribution is smaller than the noise is simply not in the data.</p>`}
];
