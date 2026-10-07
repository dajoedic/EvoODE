# ODEBench End-to-End: SINDy, W-SINDy und Annihilator rein aus Trajektorien

**Entwurf vom 2026-10-07, noch nicht eingefroren.** Frage und Kriterien vom Nutzer (Chat vom 07.10.). Vom Nutzer
gewählt:

- beide Protokolle berichten;
- eine gemeinsame, datenbasierte Auswahlregel für alle drei Methoden, auch für den Annihilator;
- R² und Strukturtreffer als Kriterien, Generalisierung als zweite Metrik.

Die Ausarbeitung stammt von Claude. **Der Nutzer legt die Entscheidungsregel (§9) fest und friert das Dokument vor
dem ersten Lauf ein.**

**Warum ein neues Dokument:** Der Smoke-Test (`docs/ODEBENCH_SMOKE_TEST_RESULT.md`) gab dem Annihilator $f$ direkt
(Oracle-$f$), den Baselines nur verrauschte Trajektorien. Sein Testfehler-Vorsprung misst deshalb vor allem den
Eingabevorteil. Hier bekommen **alle drei Methoden exakt dieselben verrauschten Trajektorien** und nichts sonst. Das
Verdikt des Smoke-Tests bleibt stehen; dieses Dokument stellt eine neue Frage und deutet jenes nicht um.

**Was sich am Annihilator ändert:** Die Klassenauswahl über den $\chi^2$-Test (v3) setzt ein bekanntes $\sigma$ bei
unabhängigem Rauschen voraus. Geschätzte Ableitungen erfüllen das nicht. Deshalb wählt der Annihilator seine Klasse
hier mit derselben Validierungsregel wie die Baselines. $\chi^2$-Test, A1–A3 und `AMBIGUOUS` entfallen. Das ist eine
Variante der Methode, nicht Gate 2A v3.

## 1. Frage

Wie gut rekonstruieren und generalisieren SINDy, W-SINDy und der Annihilator ODEBench-Systeme, wenn alle drei nur
dieselben verrauschten Trajektorien sehen? Und wie oft treffen sie die Struktur?

## 2. Systeme, Daten, Rauschen

- **Systeme:** 3, 7, 19, 21 wie im Smoke-Test, aus `benchmarks/data/strogatz_extended.json`. Referenzklassen aus
  `experiments/annihilator_odebench_smoke/results/reference.json`.
- **Trajektorien:** die gespeicherten ODEBench-Lösungen der beiden Standard-Anfangsbedingungen AB1 und AB2,
  $t \in [0, 10]$, 512 Punkte.
- **Rauschen:** $\eta \in \{0;\ 0{,}01\}$, multiplikativ wie in ODEBench/ODEFormer: $x \to (1 + \xi)\,x$ mit
  $\xi \sim \mathcal N(0, \eta)$. Bei $\eta = 0$ eine Realisierung, bei $\eta = 0{,}01$ fünf (Seeds 70000–70004,
  neuer Bereich).
- **Gepaart:** Je (Seed, System) gibt es **eine** Rauschrealisierung je Trajektorie, die alle drei Methoden
  identisch bekommen. Im Smoke-Test hatten SINDy und W-SINDy getrennte Ströme; das wird hier behoben.
- **Bewertung** immer gegen die rauschfreie Wahrheit, integriert ab der wahren Anfangsbedingung.

## 3. Protokolle

**P1, ODEBench-Standard (literaturvergleichbar):**

- Gelernt wird aus **einer** Trajektorie, AB1 oder AB2, beide Richtungen getrennt.
- Rekonstruktion: R² auf der Lern-AB.
- Generalisierung: R² auf der anderen ODEBench-AB.
- Hinweis: Bei 1D-Systemen liegt die andere AB oft auf derselben Bahn, dann ist das nur eine Zeitverschiebung.

**P2, Extrapolation:**

- Gelernt wird aus **beiden** Trajektorien.
- Rekonstruktion: R² auf AB1 und AB2.
- Generalisierung: R² auf den drei neuen Test-AB aus `experiments/annihilator_odebench_smoke/results/setup.json`
  (mitte, oberhalb, unterhalb bzw. Ersatzregel). Das schließt echte Extrapolation außerhalb des Trainingsbereichs
  ein.

Je Realisierung und Methode gibt es also drei Fits: P1 aus AB1, P1 aus AB2 und P2.

## 4. Gemeinsame Auswahlregel (alle Methoden)

1. **Aufteilung:** Von jeder Lern-Trajektorie gehen die ersten 80 % der Zeit ($t \le 8$) in den Fit, die letzten
   20 % ($t > 8$) in die Validierung.
2. **Kandidaten:** je Methode eine feste Kandidatenliste (§5, §6). Jeder Kandidat wird auf dem Fit-Teil gefittet.
3. **Validierungsfehler:** Die Trajektorie wird mit $\hat f$ ab der wahren Lern-AB über $[0, 10]$ integriert. Der
   Fehler ist $\mathrm{NRMSE}_x = \mathrm{rms}(\hat x - \tilde x)/\mathrm{rms}(\tilde x)$ auf dem Validierungsteil,
   gegen die **verrauschten** Daten $\tilde x$, denn die Methode kennt die Wahrheit nicht. Bei P2 wird über beide
   Trajektorien gemittelt.
   - Gewählt wird hier NRMSE statt R², weil das Validierungsstück nahe am Gleichgewicht oft fast flach ist und R²
     dann instabil wird.
   - Scheitert die Integration, ist der Fehler $\infty$.
4. **Auswahl:** der Kandidat mit minimalem Validierungsfehler. Liegen zwei innerhalb eines relativen Abstands von
   $10^{-3}$, gewinnt der einfachere (weniger Terme bzw. kleineres $C$).
5. **Neu-Fit:** Der gewählte Kandidat wird auf der vollen Lernzeit $[0, 10]$ neu gefittet und bewertet.

## 5. Annihilator, end-to-end

1. **Ableitung:** dieselbe wie bei SINDy, `pysindy.SmoothedFiniteDifference()` mit Standardwerten, je Lern-Trajektorie
   auf den verrauschten $\tilde x$. Das ergibt Paare $(\tilde x_i, \hat{\dot x}_i)$.
2. **Gleichmäßiges Gitter:**
   - Die Paare werden nach $\tilde x$ sortiert, Paare mit gleichem $\tilde x$ gemittelt.
   - Danach linear auf 2000 gleichmäßige Punkte über $[\min \tilde x, \max \tilde x]$ der Lerndaten interpoliert.
   - Diese Domäne legt die $z$-Normierung wie in v3 fest.
3. **Kandidaten:** die Klassen in der v3-Ordnung $C = (r+1)(d+1)$ mit $C \le 12$, zusammen 18 Klassen von (1,0) bis
   (5,1). Darunter sind alle vier Referenzklassen: (3,0) mit $C = 4$, (3,1) mit $C = 8$, (2,2) mit $C = 9$.
4. **Je Klasse:**
   - Koeffizienten mit der v3-Schätzung (`WeightContext`, `aml_candidate` auf dem Fit-Teil der Proben wie in v3);
   - $\hat f$ über die Kette $L \to \hat f$ aus dem Smoke-Test (Basisintegration, Begrenzung an der Nullstelle des
     Leitkoeffizienten, Kleinste-Quadrate-Fit der $r$ Basisgewichte auf denselben 2000 Punkten).
   - Scheitert die Kette, wird der Kandidat verworfen.
5. Kein $\chi^2$-Test, keine A1–A3, kein Bootstrap.

## 6. SINDy und W-SINDy

- **Library** wie im Smoke-Test: $1, x, x^2, x^3, \log x, x\log x, e^{-x}, \sin x, \cos x$. Zulässig ist ein Term,
  wenn er auf allen verrauschten Lernzuständen endlich ist.
- **SINDy:** `SmoothedFiniteDifference()` mit Standardwerten.
- **W-SINDy:** `WeakPDELibrary(spatiotemporal_grid = t, K = 200)`, ohne Ableitungsschätzung.
- **Optimierer:** STLSQ mit `normalize_columns = True`.
- **Kandidaten:** das Schwellengitter aus dem Smoke-Test, 20 Werte geometrisch von $10^{-3}$ bis 1.
- **Auswahl** nach §4. Die AICc-Auswahl des Smoke-Tests entfällt, weil sie nachweislich zu dichten Modellen führte.

## 7. Metriken (berichtet)

- **R²** gegen die rauschfreie Wahrheit, integriert ab der wahren AB (ODEBench-Standard). Berichtet wird der Anteil
  mit $R^2 \ge 0{,}9$, dazu der Median.
  - Rekonstruktion: auf den Lern-AB.
  - Generalisierung: P1 auf der anderen ODEBench-AB, P2 auf den drei neuen Test-AB.
  - Scheiternde Integrationen zählen als $R^2 = -\infty$.
- **Strukturtreffer:**
  - Annihilator: gewählte Klasse = Referenzklasse;
  - Baselines: gewählte Termmenge = wahre Termmenge (3: $\{x, x^2\}$, 7: $\{x, x\log x\}$, 21: $\{1, x, e^{-x}\}$,
    19 nicht darstellbar).
  - Obermengen werden getrennt berichtet: beim Annihilator Klassen mit $n_{\text{exact}} > 0$, bei den Baselines
    `TRUE_PLUS`.
- **Zusätzlich:** $\mathrm{NRMSE}_x$, $\mathrm{NRMSE}_f$ auf der Lerndomäne, die gefundene Gleichung bzw. der
  Operator, gewählte Schwelle bzw. Klasse, Zählgrößen (Fits, Klassen, Integrationen). Laufzeit wird nur berichtet.

## 8. Plausibilitätsprüfungen vor dem Lauf (Stopp bei Fehlschlag)

1. **Auswahlregel auf synthetischen Daten:** Auf einer synthetischen 1D-ODE, die keines der vier Systeme ist, mit
   $\eta = 0$ wählen alle drei Methoden einen Kandidaten mit Validierungs-$\mathrm{NRMSE}_x < 10^{-3}$.
2. **Annihilator-Kette mit exaktem $\dot x$:** Für die vier Systeme mit **exakten** Ableitungen (statt geschätzter)
   liefert die Referenzklasse einen Validierungsfehler $< 10^{-4}$. Das prüft Gitter, Interpolation und Kette. Es
   ist keine Discovery, weil die Klasse vorgegeben ist.

## 9. Entscheidungsregel (Vorschlag, der Nutzer legt fest)

Ausgewertet wird $\eta = 0{,}01$, Mehrheit über die 5 Seeds je System.

- **Generalisierungserfolg** eines Systems für eine Methode: Anteil $R^2 \ge 0{,}9$ über alle
  Generalisierungstrajektorien (P1: 2, P2: 3, also 5 je Seed, 25 je System).
- **Weiter diskutieren** (ein echter Benchmark wird erwogen), nur wenn beides gilt:
  - **G:** Der Generalisierungserfolg des Annihilators ist auf mindestens 3 von 4 Systemen **mindestens so hoch**
    wie der der besten Baseline auf diesem System.
  - **S:** Die Strukturtreffer des Annihilators (Systeme mit Mehrheit der Seeds bei der Referenzklasse) sind
    **mindestens so viele** wie bei der besten Baseline.
- **Sonst: Idee #1 beenden.**

Rekonstruktion und NRMSE werden berichtet, entscheiden aber nicht. Keine Schwellenänderung nach dem Lauf.

## 10. Ablauf und Kosten

1. Code (Codex): neues Modul `experiments/annihilator_odebench_smoke/end2end.py` mit Tests. Es verwendet Katalog,
   Orakel, Kette $L \to \hat f$ und Metriken des Smoke-Tests wieder; v3 und die Smoke-Ergebnisse bleiben
   unverändert. Dazu kommen die Plausibilitätsprüfungen aus §8.
2. **Einfrieren** durch den Nutzer, einschließlich §9.
3. **Pilot:** $\eta = 0$, Systeme 7 und 3, alle Methoden, alle Protokolle. Erfasst werden nur Technik und Kosten,
   die Records zählen mit.
4. **Hauptlauf:** 4 Systeme × 6 Realisierungen × 3 Fits × 3 Methoden. Grob geschätzt dominiert der Annihilator mit
   18 Klassen je Fit; Hochrechnung nach dem Pilot, losgelöst mit `DONE`-Marker.
5. Auswertung, Ergebnis in §11 und `docs/ODEBENCH_END2END_RESULT.md`.

## 11. Ergebnis

*(nach dem Hauptlauf)*
