# ODEBench-Smoke-Test: Annihilator end-to-end auf vier skalaren Systemen

**Eingefroren am 2026-10-06 vom Nutzer, vor dem ersten Discovery-Lauf.** Code: `f177c8f`. Werte aus `setup.json` und
`reference.json` lagen dabei vor. Auftrag und Entscheidungsregel vom Nutzer (Chat vom 06.10.). Vom Nutzer gewählt
sind die Systeme 7, 3, 21, 19, die 5 Realisierungen mit Mehrheitsregel bei 1 %, der Verzicht auf Variante B und
pysindy 2.1 als Baseline. Die Operationalisierung von §5 bis §9 hat Claude ausgearbeitet. Jede Änderung braucht ab
jetzt eine neue Version.

**Was das ist:** ein letzter Reality-Check vor dem Abschluss von Idee #1. Es ist **kein Gate 2A v4**, keine Reparatur
und kein Paper-Benchmark. Die Annihilator-Suche aus v3 bleibt unverändert.

## 1. Frage

Kann Annihilator-Guided Discovery auf wenigen echten ODEBench-ODEs $\dot x = f(x)$ eine brauchbare rechte Seite
$\hat f$ rekonstruieren? Und wie sieht das neben SINDy und W-SINDy aus?

## 2. Systeme

Ausgewählt vor jedem Ergebnis anhand des ODEBench-Katalogs (`benchmarks/data/strogatz_extended.json`). Die Systeme
40, 56 und 63 aus dem Entwicklungsset sind 2D, 3D und 4D, also nicht skalar. System 4 gehört zum verschlossenen
Prüfset und ist ausgeschlossen. Die Konstanten stammen aus ODEBench.

| ID | Rolle | $f(x)$ | erwartete minimale Annihilator-Klasse (vor Orakel) |
|---|---|---|---|
| 7 | Pflicht, nicht-polynomial | $0.032\,x\log(2.29\,x)$ (Gompertz) | (3,1): $x D^3 + D^2$, wie F5 |
| 3 | polynomiale Positivkontrolle | $0.79\,x(1 - x/74.3)$ (Logistik) | (3,0): $D^3$ |
| 21 | weitere nicht-polynomiale | $1.2 - 0.2x - e^{-x}$ (reduziertes SIR) | (3,0): $D^3 + D^2$ |
| 19 | strukturell schwieriger, darstellbar | $x(1-x) - 0.08\,x/(0.8 + x)$ (Logistik mit Ernte) | ≤ (4,1): $((0.8 + x) D + 4) D^3$; das Orakel liefert (2,2) |

Die tatsächliche Referenzklasse und $n_{\text{exact}}$ bestimmt die exakte Orakel-Logik aus v3 auf der
Trainingsdomäne (§3), **vor** jedem Discovery-Lauf. Sie wird in `reference.json` festgehalten.

## 3. Trajektorien und Anfangsbedingungen

- **Training:** die beiden Standard-Anfangsbedingungen von ODEBench je System, $t \in [0, 10]$, 512 gleichmäßige
  Zeitpunkte. Verwendet werden die in ODEBench gespeicherten Lösungen. Eine Plausibilitätsprüfung integriert sie
  mit dem eigenen Integrator nach (§8) und vergleicht.
- **Trainingsdomäne:** $[x_{\min}, x_{\max}]$ = Spannweite beider Trainingstrajektorien, $R = x_{\max} - x_{\min}$.
- **Test:** drei neue Anfangsbedingungen nach fester Regel, gleiches Zeitintervall und Gitter:
  - $x_{\text{mid}} = (x_{\min} + x_{\max})/2$. Sie liegt auf einem Trainingsorbit; im 1D-Fall ist das nur eine
    Zeitverschiebung, also ein Plausibilitätstest.
  - $x_{\text{hi}} = x_{\max} + R/4$: ein neues Regime oberhalb des Trainingsbereichs.
  - $x_{\text{lo}} = x_{\min} - R/4$, falls zulässig nach den `init_constraints` von ODEBench, sonst $x_{\min}/2$,
    falls $x_{\min} > 0$, sonst $x_{\max} + R/2$.
- Die konkreten Werte berechnet der Code aus den gespeicherten Lösungen. Sie werden vor dem ersten Discovery-Lauf
  in `setup.json` festgehalten. Die Ground-Truth-Testtrajektorien entstehen mit `solve_ivp`, LSODA,
  rtol $10^{-10}$, atol $10^{-12}$.

## 4. Rauschen und Wiederholungen

- $\eta \in \{0;\ 0{,}01\}$. Bei $\eta = 0$ gibt es eine Realisierung, bei $\eta = 0{,}01$ fünf (Seeds 60000–60004,
  neuer Bereich). Jede Methode bekommt je Seed unabhängige Zufallsströme, `default_rng([seed, system_id, kind])`.
- **Annihilator, Oracle-$f$ (Variante A):** Die $x_i$ sind die 1024 exakten Trainingszustände (2 × 512). Dazu kommt
  $f_i = f(x_i) + \eta\,\mathrm{rms}(f)\,\xi_i$, also das additive Rauschmodell aus Gate 2A, mit
  $\sigma = $ `sigma_eff` wie in v3. Das ist **absichtlich günstig** für die Methode.
- **SINDy und W-SINDy:** Sie bekommen die Trainingstrajektorien mit dem multiplikativen Rauschen aus ODEBench und
  ODEFormer, $x \to (1 + \xi)\,x$ mit $\xi \sim \mathcal N(0, \eta)$ (d'Ascoli et al., ODEFormer).
- Variante B (Ableitung aus $x(t)$ schätzen, dann Annihilator) wird **nicht** gerechnet (Nutzer). Begründung: Der
  $\chi^2$-Test setzt unabhängiges Rauschen mit bekanntem $\sigma$ auf $f$ voraus, geschätzte Ableitungen erfüllen
  das nicht.

## 5. Annihilator: von $L$ zu $\hat f$

- **Suche:** `full_search` aus v3 unverändert: Klassenordnung $(r+1)(d+1)$, $r, d \le 6$, A1/A2/A3,
  `boot_reps = 50`, $\ell_{\max} = 4$, $\tau = 3.386508\cdot10^{-7}$. Die Domäne ist die Trainingsdomäne mit
  $z = (x - \mu)/s$ wie in v3, die Punkte sind sortiert. Gleiche $x$-Werte bleiben erhalten (Trapezgewicht null).
- **Zustand** nach v3 (`NONE` > `AMBIGUOUS` > `CORRECT` > `TRUE_NOT_REF` > `WRONG`) gegen die Referenz aus §2.
- **Lösungsraum:** Zum gewählten Operator $\hat L$ (Koeffizienten in $z$) werden $r$ Basislösungen erzeugt. Dazu
  wird $\hat L y = 0$ mit `solve_ivp` (DOP853, rtol $10^{-10}$, atol $10^{-12}$, dichte Ausgabe) integriert, mit den
  Einheitsvektoren als Anfangswerten an dem Punkt $z_0$ der Trainingsdomäne, an dem der Leitkoeffizient betragsmäßig
  am größten ist. Integriert wird von $z_0$ in beide Richtungen über das Auswertungsintervall
  $[x_{\min} - 2R,\ x_{\max} + 10R]$, begrenzt durch die erste Nullstelle des Leitkoeffizienten.
- **Parameterfit:** $\hat f = \sum_{j=1}^{r} a_j y_j$, mit $a$ per Kleinste-Quadrate auf den verrauschten
  Trainingswerten $f_i$. Das sind $r$ Parameter, kein weiteres Vorwissen.
- **Nicht eindeutig möglich** (zählt als Ergebnis, wird nicht manuell gelöst):
  - der Zustand ist `NONE`;
  - eine Nullstelle des Leitkoeffizienten liegt in der Trainingsdomäne;
  - die Basisintegration scheitert.

  Dann gilt `FHAT_FAIL`. Bei `AMBIGUOUS` wird $\hat f$ trotzdem aus der gewählten Klasse gebildet und berichtet,
  strukturell zählt es aber nicht als korrekt.
- Verlässt eine integrierte Trajektorie das Intervall, auf dem $\hat f$ definiert ist, ist sie gescheitert
  (Fehler $= \infty$).

## 6. Baselines (pysindy 2.1)

- **Gemeinsame Library**, für beide Verfahren und alle Systeme gleich: $1, x, x^2, x^3, \log x, x\log x, e^{-x},
  \sin x, \cos x$. Ein Term ist zugelassen, wenn er auf allen verrauschten Trainingszuständen endlich ist; bei
  System 21 mit $x = 0$ fallen damit $\log x$ und $x\log x$ weg.
- **Darstellbarkeit der wahren Struktur:**
  - 3: $\{x, x^2\}$;
  - 7: $\{x, x\log x\}$, weil $c_0 x\log(c_1 x) = c_0\,x\log x + c_0\log c_1\,x$;
  - 21: $\{1, x, e^{-x}\}$;
  - 19: **nicht darstellbar**, weil der Term $x/(0.8 + x)$ eine unbekannte Konstante enthält. SINDy und W-SINDy
    können dort höchstens ein Surrogat finden. Das ist so beabsichtigt und wird berichtet.
- **SINDy:** Die Ableitung kommt aus `SmoothedFiniteDifference` mit pysindy-Standardwerten.
- **W-SINDy:** `WeakPDELibrary` mit derselben Library und `spatiotemporal_grid = t`, sonst pysindy-Standardwerte
  außer $K = 200$ Testfunktionen. Die tatsächlich verwendeten Werte nennt der Implementierungsbericht.
- **Auswahl** (für beide gleich, ohne Tuning pro System):
  - STLSQ mit `normalize_columns = True` über ein festes Schwellengitter, 20 Werte geometrisch von $10^{-3}$ bis 1;
  - gewählt wird das Modell mit minimalem AICc auf dem Regressionsresiduum (Mangan et al. 2017);
  - beide Trainingstrajektorien gehen gemeinsam in die Regression ein.

## 7. Kategorien

| Methode | exakt | Obermenge | falsch | unentschieden / keine |
|---|---|---|---|---|
| Annihilator | `CORRECT` | `TRUE_NOT_REF` | `WRONG` | `AMBIGUOUS`, `NONE`, `FHAT_FAIL` |
| SINDy, W-SINDy | `TRUE_STRUCTURE` | `TRUE_PLUS` | `SURROGATE` | `FAIL` |

**Strukturell korrekt** (`STRUCT_OK`) heißt: exakt oder Obermenge **und** $\mathrm{NRMSE}_f \le 0{,}05$ auf dem
Prüfgitter. Die Bedingung an $\mathrm{NRMSE}_f$ verhindert, dass eine aufgeblähte Obermenge mit schlechter
Funktionsgüte als „äquivalent“ zählt; sie gilt für alle Methoden gleich.

Bei $\eta = 0{,}01$ ist ein System `STRUCT_OK`, wenn das in mindestens 3 von 5 Seeds gilt.

## 8. Metriken

- $\mathrm{NRMSE}_f = \mathrm{rms}(\hat f - f)/\mathrm{rms}(f)$ auf 2000 gleichmäßigen Punkten der Trainingsdomäne.
- **Trajektorienfehler:** $\hat x(t)$ wird mit $\hat f$ integriert (LSODA, rtol $10^{-8}$, atol $10^{-10}$) und
  verglichen über $\mathrm{NRMSE}_x = \mathrm{rms}(\hat x - x)/\mathrm{rms}(x)$ auf den 512 Zeitpunkten, dazu
  $R^2$ (ODEBench-Standard, berichtet wird der Anteil mit $R^2 \ge 0{,}9$).
  - Training: die beiden Trainings-Anfangsbedingungen, verglichen mit der rauschfreien Wahrheit.
  - Test: die drei Anfangsbedingungen aus §3, je einzeln und als Median.
  - Ein Abbruch, ein Blow-up oder das Verlassen der $\hat f$-Domäne zählt als $\mathrm{NRMSE}_x = \infty$ und
    $R^2 = -\infty$.
- **Komplexität:** die gefundene Gleichung bzw. der Operator $\hat L$ mit $(r, d)$ und Koeffizienten, die Zahl der
  Terme.
- **Kosten:** Zählgrößen (Klassen, AML-Iterationen, Fits, Integrationen). Laufzeit wird berichtet, ist aber keine
  Evidenz.
- **Plausibilitätsprüfungen vor dem Lauf (Stopp bei Fehlschlag, keine Reparatur in dieser Version):**
  1. Die eigene Integration der Trainings-Anfangsbedingungen stimmt mit den ODEBench-Lösungen überein
     ($\mathrm{NRMSE}_x < 10^{-4}$). *Korrigiert am 06.10. vor dem Einfrieren:* Der Entwurf verlangte $10^{-6}$.
     Die gespeicherten ODEBench-Lösungen weichen aber bei jeder eigenen Toleranz (rtol $10^{-6}$ bis $10^{-10}$)
     gleichbleibend um $0{,}6$–$1{,}0\cdot10^{-5}$ ab. Sie sind selbst nur so genau. Die Prüfung soll nur zeigen,
     dass Gleichung und Konstanten richtig gelesen werden; ein Lesefehler ergäbe Abweichungen in Prozentgröße.
  2. Die Kette $L \to \hat f$ mit dem **exakten** Referenzoperator aus dem Orakel und exakten Daten reproduziert
     $f$ mit $\mathrm{NRMSE}_f < 10^{-6}$ auf allen vier Systemen. Geprüft wird **derselbe Codepfad wie im Lauf**,
     mit dem vollen Auswertungsintervall aus §5. Zusätzlich muss die Integration der Trainingstrajektorien mit
     diesem $\hat f$ gelingen.

## 9. Entscheidungsregel (wird mit dem Dokument eingefroren)

Gezählt wird über die 4 Systeme mit `STRUCT_OK` nach §7. „Median“ meint den Median über die Seeds, beim
Testfehler zusätzlich über die drei Test-Anfangsbedingungen.

**Idee #1 beenden**, wenn mindestens eine der folgenden Bedingungen gilt:

- **A:** Annihilator, $\eta = 0$: weniger als 3 von 4 Systemen `STRUCT_OK`.
- **B:** Annihilator, $\eta = 0{,}01$: höchstens 2 von 4 `STRUCT_OK`, **und** W-SINDy, $\eta = 0{,}01$: mindestens
  3 von 4 `STRUCT_OK`.
- **C:** Bei $\eta = 0{,}01$ gibt es mindestens 2 Systeme, auf denen alles Folgende gilt:
  - der Annihilator ist in der Mehrheit der Seeds `WRONG`;
  - sein medianer Trainings-$\mathrm{NRMSE}_x$ ist ≤ 0,05;
  - sein medianer Test-$\mathrm{NRMSE}_x$ ist mehr als doppelt so groß wie der von W-SINDy.

**Weiter diskutieren** nur, wenn **beide** Bedingungen gelten:

- Annihilator, $\eta = 0{,}01$: mindestens 3 von 4 `STRUCT_OK`.
- Auf mindestens 3 von 4 Systemen ist der mediane Test-$\mathrm{NRMSE}_x$ des Annihilators höchstens doppelt so
  groß wie der bessere von SINDy und W-SINDy.

Dann wird erst besprochen, ob ein Gate-2B- oder Paper-Benchmark sinnvoll ist. Kein ODEFormer davor.

**In jedem anderen Fall:** Idee #1 beenden. „Weiter diskutieren“ ist die einzige Ausnahme.

**Fairness** (steht so in jedem Ergebnisdokument):

- Der Annihilator bekommt $f$ direkt (Oracle-$f$), die Baselines arbeiten aus verrauschten Trajektorien. Schneidet
  der Annihilator trotzdem deutlich schlechter ab, ist das stark negativ. Schneidet er ähnlich oder besser ab, ist
  das **kein** Beleg für Überlegenheit.
- Umgekehrt enthält die Baseline-Library die wahren Terme für 3, 7 und 21, für 19 nicht.

Keine Schwellenänderung nach Sichtung der Ergebnisse. Kein Tuning pro System.

## 10. Ablauf und Kosten

1. Code (Codex): neuer Ordner `experiments/annihilator_odebench_smoke/`. Er importiert v3 nur lesend; das Orakel
   für die neuen Systeme ist eine Kopie der v3-Nullraumlogik, v3 bleibt unverändert. Dazu kommen Tests und die
   Plausibilitätsprüfungen aus §8. Danach entstehen `setup.json` (Domänen, Test-Anfangsbedingungen) und
   `reference.json` (Referenzklassen).
2. **Einfrieren dieses Dokuments durch den Nutzer**, nach Sicht auf `setup.json` und `reference.json`. Beide
   Dateien enthalten keine Discovery-Ergebnisse.
3. **Pilot:** $\eta = 0$ für 7 und 3, alle Methoden. Ziel ist nur, dass die Pipeline technisch läuft, und die
   Zählgrößen. Die Pilot-Records zählen im Hauptlauf mit; die Regel ist dann schon eingefroren.
4. **Hauptlauf:** 4 Systeme × (1 + 5) Realisierungen × 3 Methoden. Grobe Kosten für den Annihilator: 24
   `full_search`-Läufe mit Bootstrap. Den Laufort legen Claude und der Nutzer nach dem Pilot fest (Laptop mit
   mehreren Workern oder Orion).
5. Auswertung nach §9, Ergebnis in §12 und eine Übergabe in `docs/ODEBENCH_SMOKE_TEST_RESULT.md`. Zuoberst steht
   die Tabelle aus dem Auftrag, dazu die Gleichungen je System, die Fairness-Hinweise und genau eine Antwort auf die
   Frage, ob die Methode auf echten ODEBench-Systemen praktisch noch interessant aussieht (ja/nein).

## 11. Erwartung (vorab notiert, keine Schwelle)

Gompertz hat dieselbe Annihilator-Struktur wie F5, die in der Diagnose bei 1 % nie identifiziert wurde. System 19
ist rational mit verschobenem Pol wie F8. Erwartet wird deshalb, dass der Annihilator bei $\eta = 0$ die meisten
Systeme trifft, bei $\eta = 0{,}01$ aber an 7 und 19 scheitert, während die Baselines 3, 7 und 21 strukturell
treffen. Entscheidend ist allein §9.

## 12. Ergebnis

**Version 1 nicht aussagefähig, Hauptlauf nicht gestartet.** Der Pilot (06.10., $\eta = 0$, Systeme 7 und 3,
`results/v1_pilot/`) zeigte einen technischen Fehler im Versuchsaufbau.

- **Annihilator:** auf beiden rauschfreien Systemen `NONE`, alle 42 Klassen verworfen, auch bei der Logistik mit
  exaktem Annihilator $D^3$.
- **Diagnose** (`v1_pilot/diag_none.{py,out}`): Der exakte Referenzoperator wurde auf vier Punktgittern derselben
  Domäne getestet.

  | Punkte | Logistik (3,0): $T$ / kritischer Wert | Gompertz (3,1): $T$ / kritischer Wert |
  |---|---|---|
  | Trajektorie (1024 Punkte) | $4{,}6\cdot10^{14}$ / 273, verworfen | $4{,}8\cdot10^{14}$ / 219, verworfen |
  | gleichmäßig, 1024 Punkte | 12,5 / 285, besteht | 172 / 278, besteht |
  | gleichmäßig, 2000 Punkte | $7\cdot10^{-6}$ / 285, besteht | $4\cdot10^{-6}$ / 281, besteht |

  Die Trapezquadratur der schwachen Form ist auf Trajektoriengittern ungenau, weil dort große Lücken entstehen, wo
  die Dynamik schnell ist. Der numerische Boden $\tau$ wurde in v3 für 2000 gleichmäßige Punkte kalibriert. Das ist
  ein Fehler im Aufbau, kein Ergebnis über die Methode.
- **Zweiter Mangel in §7:** Ohne Rauschen wählt die AICc-Auswahl der Baselines die kleinste Schwelle, also alle
  9 Terme. Als Obermenge mit $\mathrm{NRMSE}_f \approx 10^{-5}$ zählt das nach §7 als `STRUCT_OK`, obwohl keine
  Struktur identifiziert wurde.
- **Kosten:** Der Pilot lief etwa 3 h für zwei Annihilator-Läufe ohne Bootstrap, weil die Suche alle 42 Klassen
  prüfte.

Die Fortsetzung braucht eine Version 2 dieses Dokuments. Die Entscheidung darüber liegt beim Nutzer.
