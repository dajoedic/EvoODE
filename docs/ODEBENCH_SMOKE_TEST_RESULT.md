# ODEBench-Smoke-Test – Ergebnis und Übergabe

**Stand: 2026-10-07 morgens.** Ergebnis des Smoke-Tests nach `docs/ODEBENCH_SMOKE_TEST.md` (v1) und
`docs/ODEBENCH_SMOKE_TEST_v2.md` (v2, eingefroren). Für den Nutzer und jede spätere Sitzung dieser Spur, als
Grundlage für den Abschluss von Idee #1. Die Vorgeschichte steht in `docs/REALITY_CHECK_DIRECT_REGRESSION_RESULT.md`.

## 1. Die Antwort

> **Sieht die Methode auf echten ODEBench-Systemen trotz der negativen Gate-2A-Ergebnisse praktisch noch
> interessant aus? Nein.**

**Verdikt nach der eingefrorenen Regel (v1 §9 mit v2-Änderung 2): Idee #1 beenden, ausgelöst durch Bedingung A.**
Ohne Rauschen identifiziert der Annihilator nur 2 von 4 Systemen exakt (Logistik 3 und SIR 21). Verlangt waren
mindestens 3. Gompertz (7), das ursprüngliche Motiv der Idee, und das rationale System 19 verfehlt er schon auf
exakten Daten. Bei 1 % Rauschen identifiziert er **0 von 4** Systemen exakt.

## 2. Ergebnistabelle

Struktur: rauschfrei je ein Lauf, bei 1 % fünf Seeds (60000–60004). Test-AB ist der Median von $\mathrm{NRMSE}_x$
über die drei Test-Anfangsbedingungen, bei 1 % zusätzlich über die Seeds. $\infty$ heißt, die Integration ist
gescheitert oder hat die Domäne von $\hat f$ verlassen.

| System | Rauschen | Annihilator Struktur | SINDy Struktur | W-SINDy Struktur | Annihilator Test-AB | SINDy Test-AB | W-SINDy Test-AB |
|---|---:|---|---|---|---:|---:|---:|
| 3 Logistik | 0 | **`CORRECT`** (3,0) | `TRUE_PLUS` (9 Terme) | `TRUE_PLUS` (9) | $6\cdot10^{-9}$ | $3\cdot10^{-6}$ | $8\cdot10^{-6}$ |
| 3 Logistik | 1 % | (3,0) 5/5, aber alle `AMBIGUOUS` (A1/A3) | `TRUE_PLUS` 5/5 (9) | `TRUE_PLUS` 5/5 (9) | $5{,}6\cdot10^{-4}$ | $9{,}2\cdot10^{-3}$ | $3{,}0\cdot10^{-3}$ |
| 7 Gompertz | 0 | `AMBIGUOUS` (1,3), Bootstrap 0,18 | `TRUE_PLUS` (9) | `TRUE_PLUS` (9) | $3{,}8\cdot10^{-4}$ | $3{,}9\cdot10^{-3}$ | $2{,}5\cdot10^{-3}$ |
| 7 Gompertz | 1 % | 3× `WRONG` (2,0), 2× `AMBIGUOUS` (1,1) | `TRUE_PLUS` 5/5 (8–9) | `TRUE_PLUS` 5/5 (5–9) | 0,39 | 0,72 | 0,68 |
| 19 Ernte | 0 | `AMBIGUOUS` (4,0), Bootstrap 0,10 | `SURROGATE` (9)¹ | `SURROGATE` (9)¹ | $8\cdot10^{-7}$ | $5\cdot10^{-5}$ | $6\cdot10^{-5}$ |
| 19 Ernte | 1 % | (3,0) 5/5, alle `AMBIGUOUS` (A1) | `SURROGATE` 5/5 (5)¹ | `SURROGATE` 5/5 (9)¹ | $4{,}4\cdot10^{-4}$ | $3{,}3\cdot10^{-3}$ | $7{,}4\cdot10^{-3}$ |
| 21 SIR | 0 | **`CORRECT`** (3,0) | `TRUE_PLUS` (7) | `TRUE_PLUS` (7) | $6\cdot10^{-9}$ | $1{,}5\cdot10^{-4}$ | $2{,}7\cdot10^{-4}$ |
| 21 SIR | 1 % | (3,0) 5/5, aber alle `AMBIGUOUS` (A1/A3) | `TRUE_PLUS` 5/5 (6) | `TRUE_PLUS` 5/5 (7) | $1{,}2\cdot10^{-3}$ | 0,11 | $\infty$ |

¹ System 19 ist mit der Baseline-Library nicht exakt darstellbar (v1 §6); dort ist nur `SURROGATE` möglich.

**Zählung `STRUCT_OK`** (nur exakte Struktur, v2):

| | rauschfrei | 1 % |
|---|---:|---:|
| Annihilator | 2/4 | 0/4 |
| SINDy | 0/4 | 0/4 |
| W-SINDy | 0/4 | 0/4 |

## 3. Die Entscheidungsregel im Einzelnen

| Bedingung | Inhalt | Wert | ausgelöst? |
|---|---|---|---|
| A | Annihilator rauschfrei < 3/4 `STRUCT_OK` | 2/4 | **ja** |
| B | Annihilator 1 % ≤ 2/4 **und** W-SINDy 1 % ≥ 3/4 | 0/4 und 0/4 | nein (W-SINDy-Teil nicht erfüllt) |
| C | ≥ 2 Systeme mit mehrheitlich `WRONG`, Trainingsfehler ≤ 0,05, Testfehler > 2 × W-SINDy | nur System 7 mehrheitlich `WRONG`; dort Test 0,39 gegen 0,68 | nein |
| weiter diskutieren | Annihilator 1 % ≥ 3/4 und konkurrenzfähige Generalisierung | 0/4 | nein |

**Ergebnis: beenden (Bedingung A).**

## 4. Gefundene Gleichungen

Der Annihilator gibt einen Operator $\hat L$ in $z = (x - \mu)/s$ aus. $\hat f$ ist die Kombination seiner
Basislösungen, numerisch, ohne geschlossene Form. Koeffizienten von $\hat L$ normiert, geordnet nach
$(D^k, z^j)$ wie in v3.

| System | wahr | Annihilator rauschfrei | Annihilator 1 % (Seed 60000) |
|---|---|---|---|
| 3 | $0.79\,x(1 - x/74.3)$, Klasse (3,0): $D^3$ | (3,0): $D^3$ exakt | (3,0) mit Störanteilen in $1, D, D^2$, `AMBIGUOUS` |
| 7 | $0.032\,x\log(2.29x)$, Klasse (3,1): $xD^3 + D^2$ | (1,3): erste Ordnung mit kubischen Koeffizienten, `AMBIGUOUS` | (1,1): erste Ordnung, `AMBIGUOUS`; Seeds 60002–04: (2,0), `WRONG` |
| 19 | $x(1-x) - 0.08x/(0.8+x)$, Klasse (2,2) | (4,0): konstante Koeffizienten, Surrogat, `AMBIGUOUS` | (3,0): konstante Koeffizienten, Surrogat, `AMBIGUOUS` |
| 21 | $1.2 - 0.2x - e^{-x}$, Klasse (3,0): $D^3 + D^2$ | (3,0): $D^3 + D^2$ exakt (in $z$: $0.363\,D_z^3 + 0.932\,D_z^2$, Verhältnis $= s = 2.57$) | (3,0) mit kleinen Störanteilen, `AMBIGUOUS` |

| System | SINDy rauschfrei | W-SINDy rauschfrei | SINDy 1 % (Seed 60000) | W-SINDy 1 % (Seed 60000) |
|---|---|---|---|---|
| 3 | alle 9 Terme, u. a. $0.823x - 0.0105x^2 - 6.37e^{-x}$ | alle 9, u. a. $-65.3\,e^{-x}$ | alle 9, Koeffizienten bis $6910\,e^{-x}$ | alle 9, bis $-4040\,e^{-x}$ |
| 7 | alle 9, u. a. $0.0377x + 0.0285\,x\log x$ | alle 9, ähnlich | 8 Terme, bis $-80.1\,e^{-x}$ | $\{x, x^2, x^3, \log x, x\log x\}$ |
| 19 | alle 9 (Surrogat) | alle 9 (Surrogat) | $\{x^3, \log x, x\log x, \sin x, \cos x\}$ | alle 9, bis $4840\,e^{-x}$ |
| 21 | $1.2 - 0.197x - 0.998e^{-x}$ + 4 Kleinstterme | $1.2 - 0.196x - 0.997e^{-x}$ + 4 Kleinstterme | 6 Terme, $3.06 - 1.46x - 2.53e^{-x} + \ldots$ | 7 Terme |

Vollständige Records: `experiments/annihilator_odebench_smoke/results_v2/records.jsonl`.

## 5. Was das bedeutet

### 5.1 Der Annihilator scheitert genau dort, wofür er gedacht war

- **Gompertz** ist nicht-polynomial mit $x$-abhängigem Koeffizienten im Operator ($xD^3 + D^2$), also genau der Fall,
  für den die Idee gedacht war. Schon **ohne Rauschen** findet die Suche ihn nicht. Sie bleibt bei (1,3) stehen,
  einer früheren Klasse, und markiert das wegen des instabilen Bootstraps (0,18) als `AMBIGUOUS`. Bei 1 % wählt sie
  in 3 von 5 Seeds **stabil** die falsche Klasse (2,0), mit Bootstrap 0,98–1,00. Das ist dasselbe Muster wie F4 in
  der Diagnose `AMBIGUOUS`: stabil falsch und mit voller Zuversicht.
- **System 19** (rational): rauschfrei (4,0), bei 1 % (3,0), beides Klassen mit konstanten Koeffizienten. Das
  Surrogatmuster aus F8 wiederholt sich.
- Die Erwartung aus v1 §11 („Gompertz wie F5, 19 wie F8“) hat sich bestätigt, für Gompertz sogar schon rauschfrei.

### 5.2 Wo er richtig liegt, kann er es bei Rauschen nicht bestätigen

Bei der Logistik und bei SIR wählt der Annihilator bei 1 % in **10 von 10** Seeds die richtige Klasse (3,0), mit
Bootstrap 1,0. Alle zehn Läufe sind aber `AMBIGUOUS`, weil A1 (mehrdimensionaler Fast-Nullraum) oder A3 (große
Koeffizientenunsicherheit) feuern. Die Abstentionsregeln schlagen also auch bei richtigen Antworten an. Nach v2 zählt
das nicht als exakte Identifikation. Zusammen mit 5.1 ergibt das: In den schweren Fällen falsch oder unentschieden,
in den leichten Fällen richtig, aber unentschieden.

### 5.3 Die Funktionsgüte ist gut, aber kein Beleg

$\hat f$ des Annihilators ist bei 1 % auf allen Systemen genau ($\mathrm{NRMSE}_f \approx 3$–$9\cdot10^{-4}$). Auf
3, 19 und 21 generalisiert es auf neue Anfangsbedingungen besser als SINDy und W-SINDy. **Das ist nach der
vorab festgelegten Fairnessregel kein Beleg für Überlegenheit:**

- Der Annihilator bekommt $f$ direkt auf 2000 gleichmäßigen Punkten (Oracle-$f$, nach v2 sogar ohne Trajektorien).
- Die Baselines müssen $\dot x$ aus 1024 verrauschten Trajektorienpunkten schätzen.

Unter diesen Bedingungen ist eine gute Funktionsgüte im Wesentlichen eine geglättete Regression auf exakten
Stützstellen.

### 5.4 Schwäche der Baseline-Seite (offen benannt)

SINDy und W-SINDy treffen die exakte Struktur **nie**:

- Die AICc-Auswahl über das Schwellengitter (v1 §6, von Claude festgelegt) wählt fast immer dichte Modelle mit 6–9
  Termen.
- Ohne Rauschen wird stets die kleinste Schwelle gewählt; bei 1 % entstehen teils riesige, sich gegenseitig
  aufhebende Koeffizienten.

Die Baselines sind damit als Strukturvergleich schwach, und Bedingung B konnte gar nicht auslösen. Das ändert das
Verdikt nicht: Bedingung A betrifft allein den Annihilator. Für jeden späteren Vergleich gilt aber: Eine
AICc-Auswahl auf einer kollinearen festen Library ist keine brauchbare Strukturbaseline.

### 5.5 Praktische Einsetzbarkeit

Der Pilot von v1 zeigte zusätzlich: Auf echten, ungleichmäßig verteilten Trajektorienpunkten verwirft die Methode
ohne neue Kalibrierung sogar den exakten Operator ($T \approx 5\cdot10^{14}$). Version 2 umging das nur, indem sie
dem Annihilator 2000 gleichmäßige Oracle-Punkte gab. Für echte Equation Discovery aus Trajektorien wäre die Methode
in dieser Form nicht einsetzbar.

## 6. Ablauf

| Schritt | Ergebnis |
|---|---|
| Spezifikation v1 | Entwurf `e8a1ba2`, eingefroren `b989271` |
| Umsetzung | WP-OB-A nicht abgenommen; die Baselines waren kein pysindy, trugen aber pysindy-Parameter, und $L \to \hat f$ war am Pol defekt. WP-OB-A2 behob das (`f177c8f`) |
| Pilot v1 | `NONE` auf exakten Daten; Ursache Trajektoriengitter gegen den $\tau$-Boden (v1 §12, `results/v1_pilot/`) |
| Spezifikation v2 | vom Nutzer gewählt: 2000 gleichmäßige Punkte, `STRUCT_OK` nur exakt (`a438a2a`) |
| Umsetzung v2 | WP-OB-B (`f3faa77`); Plausibilität: der exakte Operator besteht den v3-Test auf allen vier Systemen |
| Pilot v2 | 07.10. 00:07–01:27, technisch sauber |
| Hauptlauf v2 | 07.10. 01:27–03:49 auf dem Laptop, 72 Records, `DONE` |

Kosten (Zählgrößen): Der Annihilator prüfte 2–10 Klassen pro Lauf. Die Laufzeit lag zwischen 23 min (System 3,
rauschfrei) und 81 min (System 7, rauschfrei); bei 1 % 16–44 min (Gompertz mit 2–3 Klassen am kürzesten). SINDy brauchte etwa 2 s, W-SINDy etwa
20–100 s.

## 7. Gesamtbild der Spur

| Schritt | Ergebnis |
|---|---|
| Gate 2A v1 | eingefroren, an der Abnahme gescheitert, nie gelaufen |
| Gate 2A v2 | Stufe K gescheitert (FNS-Fehler) |
| Gate 2A v3, Anhang A | nicht bestanden |
| Gate 2A v3, Anhang B | K6 würde auslösen (F4, F5, F8 bei 1 % N1) |
| Diagnose `AMBIGUOUS` | negativ: 118/118 eindeutige N1-Antworten falsch |
| Reality-Check Stufe A | `STRONG_NEGATIVE`: die direkte Repräsentation löst dieselben Fälle in 60/60 |
| **ODEBench-Smoke-Test v2** | **beenden (A)**: rauschfrei 2/4, bei 1 % 0/4 exakt; Gompertz schon rauschfrei verfehlt |

Alle sechs Prüfungen zeigen dieselbe Grenze. Der Annihilator erkennt Funktionen mit konstanten Koeffizienten im
Operator (Exponentialpolynome), aber nicht die $x$-abhängigen Koeffizienten, die der Kern der Idee waren. Auch die
Abstention fängt das nicht verlässlich ab.

## 8. Nächste Schritte

1. **Abschluss von Idee #1 schreiben:** Abschlussabschnitt in `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md`, `CLAUDE.md`
   als abgeschlossen markieren. Kein ODEFormer, kein Gate 2B, kein eigenes Repository.
2. **Aufräumen** (Entscheidungen des Nutzers):
   - `PRACTICAL_ANNIHILATOR_BENCHMARK.md` zur Akte oder verwerfen;
   - die Reste der v2-Abnahme;
   - der Orion-Job `annihilator-diag-amb`;
   - die Temp-Ordner.

## 9. Wo die Daten liegen

| Pfad | Inhalt |
|---|---|
| `docs/ODEBENCH_SMOKE_TEST.md`, `docs/ODEBENCH_SMOKE_TEST_v2.md` | Spezifikationen v1 (mit Pilot-Befund in §12) und v2 (Ergebnis unten) |
| `experiments/annihilator_odebench_smoke/` | Code und Tests |
| `experiments/annihilator_odebench_smoke/results/` | v1: `setup.json`, `reference.json`, `sanity.json`, `v1_pilot/` mit Diagnose |
| `experiments/annihilator_odebench_smoke/results_v2/records.jsonl` | **72 Records**, Grundlage des Verdikts |
| `experiments/annihilator_odebench_smoke/results_v2/summary.{json,md}` | Entscheidung und Tabelle |
| `experiments/annihilator_odebench_smoke/results_v2/{run.log,main.out,main.err,pilot.*,DONE,sanity.json}` | Protokolle, Plausibilität |
| `codex/reports/REPORT_WP_OB_A.md`, `_A2.md`, `_B.md` | Umsetzungsberichte |
