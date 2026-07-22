# CURRENT TASK: WP-P1 — Auswertungskosten messbar und begrenzbar machen

**Language: Julia**

## Context

Der Regression-Volllauf wurde nach 40,5 Compute-Stunden bei 23/30 Zellen abgebrochen.
Eine Kostenanalyse aus `outputs/studies/regression/run.log` (alle 23 Zellen) ergab:

- Kosten pro Level explodieren mit der Stage: 21 s (Stage 1) → 170 → 443 → 482 → 878 s (Stage 5).
- **62 % der gesamten Rechenzeit (24,9 von 40,5 h) wurde in Stages oberhalb der jeweils
  erwarteten Stage verbracht** — also in Komplexität, die die Systeme nie gebraucht haben.
- Auf den teuersten Levels kostet ein einzelner Kandidat im Mittel ~619 s. Das liegt über dem
  Default-Wall-Clock-Limit des Optimierers (300 s), d. h. einzelne Fits laufen sicher ins Limit.
- Ein einzelnes Level (System 63, Level 16, Stage 4) kostete 3,4 h.

Zusätzlich wurde ein Reproduzierbarkeitsleck gefunden: `run_regression.jl` konstruiert den
`BFGSOptimizer` ohne `time_limit_s`, der Default ist ein **Wall-Clock-Limit**. Damit hängt die
Zahl der Optimierer-Iterationen von der Maschinenlast ab. Beleg: dieselbe Zelle
(System 26, Seed 123) lieferte unter v2.2 und unter der verhaltensgleichen v3.2-Brücke
unterschiedliche Losses (1.3916e-3 vs. 1.3713e-3), bei Laufzeiten von 13.352 s vs. 20.158 s.
Alle anderen 7 überlappenden Zellen sind bit-identisch.

Ziel dieses Work Packages ist **nicht**, den Suchalgorithmus zu ändern. Ziel ist, die Kosten
einer Kandidaten-Auswertung (a) reproduzierbar, (b) messbar und (c) nach oben begrenzbar zu
machen — als Grundlage für die eigentliche Entscheidung über das Bewertungsverfahren.

## Goal

1. Wall-Clock-Abhängigkeit aus dem Ergebnispfad entfernen (Determinismus).
2. Getrennte, explizit konfigurierbare Solver-/Optimierer-Budgets für *Bewertung während der
   Suche* vs. *finale Validierung* einführen — mit den heutigen Werten als Default, damit ohne
   ausdrückliche Aktivierung **kein** Verhalten sich ändert.
3. Instrumentierung: pro Level messen und protokollieren, wohin die Zeit geht.
4. Ein Mikro-Benchmark-Skript, das genau eine Zelle unter altem und neuem Budget vergleicht und
   Speedup sowie Ergebnisgleichheit berichtet.

## Files

- **Ändern:** `src/optimize/bfgs.jl`, `src/simulate/solve.jl`, `src/structure/evogrow.jl`,
  `studies/regression/run_regression.jl` (nur soweit für die Punkte unten nötig).
- **Neu:** ein Mikro-Benchmark-Skript unter `studies/profiling/`.
- **Nicht anfassen:** `src/structure/evogrow_v3.jl` (Verhalten der Lockstep-Brücke muss identisch
  bleiben), Systemliste, Seeds, Hyperparameter der Suche.

## Required Content

### 1. Determinismus: kein Wall-Clock im Ergebnispfad

Es darf kein Abbruchkriterium geben, dessen Auslösen von der Maschinenlast abhängt und das
das Ergebnis beeinflusst. Der Optimierer muss so konfigurierbar sein, dass sein Budget rein
deterministisch ist (Iterationszahl / Toleranzen), und `run_regression.jl` muss ihn genau so
konstruieren — explizit, nicht über Defaults.

Ein Wall-Clock-Limit darf weiterhin existieren, aber nur als **Notbremse**: wenn es greift, muss
das erkennbar sein (Zählung, Logeintrag, Kennzeichnung im Ergebnis), damit ein solcher Lauf nicht
stillschweigend als reguläres Ergebnis durchgeht. Wähle die Notbremse so, dass sie im
regulären Betrieb nicht greift.

Dokumentiere im Docstring, welche Parameter deterministisch sind und welche nicht.

### 2. Getrennte Budgets: Suche vs. finale Validierung

Heute wird während der Suche mit denselben Solver-Toleranzen und demselben Schritt-Limit
gerechnet wie bei der Endauswertung (`abstol/reltol = 1e-9`, `maxiters_solve = 10^6`). Eine
divergierende Kandidatenstruktur darf damit bis zu einer Million Solver-Schritte verbrennen.

Führe getrennte, explizit übergebbare Budgets ein für:
- **Screening/Bewertung während der Strukturmutation** (lose Toleranz, hartes Schritt-Limit,
  frühe Verwerfung divergierender oder nicht-endlicher Lösungen),
- **finale Validierung** (heutige Werte, unverändert).

Harte Anforderungen:
- Die neuen Parameter erhalten als **Default exakt die heutigen Werte**. Ohne ausdrückliche
  Aktivierung durch den Aufrufer darf sich kein einziges Ergebnis ändern.
- Eine Kandidatenstruktur, deren Simulation fehlschlägt, divergiert oder nicht-endliche Werte
  liefert, muss **billig** verworfen werden (früher Abbruch), nicht durchgerechnet.
- Verworfene Kandidaten müssen als solche gezählt werden (siehe Punkt 3), nicht stillschweigend
  als schlechter Loss durchlaufen.

### 3. Instrumentierung: wohin geht die Zeit

Pro Level messen und in `run.log` protokollieren (eine kompakte Zeile pro Level, keine Flut):
- Wall-Zeit des Levels und aktive Stage,
- Anzahl Parameter-Fits,
- Anzahl ODE-Solves,
- Anzahl verworfener/ungültiger Solves (divergiert, nicht-endlich, Schritt-Limit erreicht),
- Anzahl Fits, die in ein Iterations- oder Notbrems-Limit gelaufen sind,
- Zeitanteil Parameteroptimierung vs. Simulation.

Dieselben Größen pro Lauf aufsummiert in den Record von `history.jsonl` aufnehmen. Bestehende
Feldnamen und Werte dürfen sich **nicht** ändern; nur neue Felder ergänzen.

Beachte: neue Felder im Record sind unkritisch, eine Änderung metrik-relevanter Konfiguration
ändert dagegen den `config_fingerprint`. Das ist beabsichtigt und erwünscht — die bestehenden
23 Records unter Fingerprint `0c739d4e36ee6498` bleiben als Baseline v0 gültig und dürfen nicht
nachträglich umgeschrieben werden. Umgehe den Fingerprint-Wechsel nicht.

### 4. Mikro-Benchmark (Pflicht-Deliverable)

Ein Skript unter `studies/profiling/`, das **genau eine** Zelle rechnet — System 26, Seed 42,
Variante v2.2 — und zwar zweimal:

- **A:** heutige Budgets (Referenz),
- **B:** eingeschaltete Screening-Budgets aus Punkt 2.

Berichtet werden müssen für A und B jeweils: Wall-Zeit, Loss, `final_stage`, `pruned_match`,
sowie alle Zähler aus Punkt 3 — plus der Speedup B/A und eine klare Aussage, ob sich die
gefundene Struktur geändert hat.

Ausgabe nach `outputs/studies/profiling/profile_eval_cost/` (eigener Unterordner, nicht direkt
in den Elternordner). Das Skript darf **nicht** die volle Suite starten.

Wähle für B einen konservativen ersten Parametersatz und begründe die Wahl kurz im Skript-Header.
Falls B die Struktur verändert, ist das ein Ergebnis, kein Fehler — berichte es.

## Verification

1. Ohne Aktivierung der neuen Budgets ist eine schnelle Zelle (System 11, alle Seeds) **bit-identisch**
   zur Baseline v0 (Loss, `final_stage`, `pruned_match` gegen `history.jsonl` prüfen).
2. Das Wall-Clock-Limit beeinflusst das Ergebnis im Default-Pfad nicht mehr.
3. Der Mikro-Benchmark aus Punkt 4 läuft durch und liefert die geforderte A/B-Tabelle.
4. Die Zähler aus Punkt 3 sind plausibel (Anzahl Fits pro Level passt zu `pop_size` und
   `children_per_parent`).
5. Keine Änderung an Systemliste, Seeds, Suchhyperparametern oder an `evogrow_v3.jl`.

Führe **keine** vollständige Regression-Suite aus. Nenne im Abschlussbericht, welche Zellen du
tatsächlich gerechnet hast.

## Constraints

- Kein Eingriff in Wachstum, Selektion, Promotion oder Stopplogik. Dieses WP ändert nur, wie
  teuer und wie reproduzierbar eine Auswertung ist.
- Alle neuen Parameter defaulten auf heutiges Verhalten. Kein stilles Verhaltens-Delta.
- Bestehende Record-Felder, Metrikdefinitionen und die 23 Baseline-v0-Records bleiben unangetastet.
- Keine neuen Abhängigkeiten.
- **Ausdrücklich nicht Teil dieses WP** (nicht vorwegnehmen): ein ableitungsbasiertes
  Screening-Kriterium anstelle der Simulation, das Einschalten von `use_pretuning`,
  Parallelisierung, WP-v3.3, und der Python-Delta-Report WP-H2.
