# CURRENT TASK: WP-P1b — Korrekturen an WP-P1 vor dem ersten Benchmark-Lauf

**Language: Julia**

## Context

WP-P1 ist umgesetzt (Instrumentierung, getrennte Budgets, Mikro-Benchmark). Das Review hat drei
blockierende Punkte gefunden, die vor dem ersten Benchmark-Lauf behoben werden müssen, plus zwei
Punkte, die stillschweigende Verhaltens- bzw. Reproduzierbarkeitslücken schließen.

Die Instrumentierung selbst ist in Ordnung und bleibt unverändert. Dieses WP korrigiert nur die
Punkte unten. Es ändert weiterhin nichts an Wachstum, Selektion, Promotion oder Stopplogik.

## Required Content

### 1. Screening-Budget muss auch für EvoGrowV3 gelten (blockierend)

`EvoGrowV3` hat kein `screening_optimizer`-Feld. `run_regression.jl` übergibt den Screening-
Optimizer an beide Varianten, bei v3 landet er auf einem ungenutzten Parameter und wird verworfen.
`EvoGrowV3` hat eine eigene Suchschleife und wertet immer mit dem Referenz-Optimizer aus.

Folgen: bei aktivierten Screening-Budgets laufen v2.2 und v3 unter unterschiedlichen Budgets, der
Anker-Vergleich zwischen beiden ist damit wertlos, und die v3-Records tragen trotzdem
`screening_budgets_active = true`.

Zu tun:
- `EvoGrowV3` bekommt dasselbe `screening_optimizer`-Feld mit demselben Default wie `EvoGrow`, und
  seine Suchschleife verwendet es für die Kandidatenbewertung nach demselben Muster wie `EvoGrow`.
  Das ist ein reiner Durchreich-Parameter; die frühere Vorgabe „evogrow_v3.jl nicht anfassen"
  bezog sich auf das Lockstep-*Verhalten* und wird hiermit für diesen Punkt aufgehoben.
- Die Lockstep-Äquivalenz muss erhalten bleiben: **ohne** gesetzten Screening-Optimizer muss v3
  sich exakt wie bisher verhalten.
- `EvoGrowV3` liefert dieselben Instrumentierungsfelder im Meta zurück wie `EvoGrow` (heute sind
  sie bei v3 alle `nothing`), damit beide Varianten vergleichbar protokolliert werden.
- Der Record darf `screening_budgets_active` **nicht** aus dem ENV-Flag ableiten, sondern muss den
  tatsächlichen Wert aus dem Meta der StrukturSuche übernehmen. Ist er dort nicht verfügbar, ist
  das ein Fehler und kein stiller Default.

### 2. Frühe Verwerfung über das richtige Solver-Primitiv (blockierend)

Die Verwerfung ist derzeit über `isoutofdomain` implementiert. Das ist ein
**Schritt-Ablehnungs**-Mechanismus: der Integrator verwirft den Schritt, verkleinert `dt` und
versucht erneut, bis `maxiters` oder `dtmin` erreicht ist. Es bricht nicht ab. Für divergierende
Kandidaten — genau den Zielfall — erhöht das die Kosten, statt sie zu senken.

Das Abbruch-Primitiv ist `unstable_check`; es beendet die Integration sofort. Sein Default prüft
bereits `any(!isfinite, u)`, die Nicht-endlich-Erkennung ist also ohnehin aktiv.

Zu tun:
- Die frühe Verwerfung auf `unstable_check` umstellen (sowohl in `bfgs.jl` als auch in
  `solve.jl`). `isoutofdomain` nicht mehr für diesen Zweck verwenden.
- Die Prüffunktion darf **nicht allozieren**. Die heutige Form erzeugt pro Aufruf zwei temporäre
  Arrays und läuft im Hot Path bei jedem Schritt. Formuliere sie elementweise.
- Der neue Anteil gegenüber dem Solver-Default ist ausschließlich die endliche Schranke
  (`divergence_limit`). Halte das im Docstring fest.
- Die Zählung der verworfenen Solves muss weiter funktionieren; ein durch `unstable_check`
  beendeter Solve muss als verworfen gezählt werden und nicht als regulärer Schritt-Limit-Fall.

### 3. Der Benchmark muss beschränkt und in dieser Reihenfolge laufen (blockierend)

Fall A des Mikro-Benchmarks ist System 26, Seed 42, 30 Level — die Zelle, die in Baseline v0 drei
Stunden brauchte, und zwar *mit* der 300-s-Bremse, die regelmäßig gegriffen hat. Mit
`time_limit_s = 86400`, `maxiters = 200` und `maxiters_solve = 10^6` existiert keine
deterministische Obergrenze für einen einzelnen Fit. A kann erheblich länger laufen als drei
Stunden.

Zu tun:
- Das Level-Budget des Benchmarks deutlich reduzieren (Richtwert: 12 Level statt 30) und als
  eigene Konstante im Skript führen, klar getrennt von der Regression-Konfiguration. Beide Fälle
  laufen mit demselben Budget, damit die Kosten pro Level direkt vergleichbar sind. Begründe die
  Wahl im Skript-Header: gemessen werden sollen Kosten pro Level, nicht Konvergenz.
- Fall B (Screening) zuerst rechnen, Fall A danach. B ist der billige Fall; wenn A entgleist, hat
  man das Screening-Ergebnis bereits auf der Platte.
- Zwischenergebnisse nach jedem Fall sofort schreiben und flushen, nicht erst am Ende beider
  Fälle. Ein Abbruch während A darf das B-Ergebnis nicht vernichten.
- Der Bericht muss zusätzlich die **beobachteten Retcode-Strings** von Optimierer und Solver
  ausgeben (siehe Punkt 5), sowie die Kosten pro Level für beide Fälle.

### 4. Kein stilles Verhaltens-Delta im Default-Pfad

`_predict_traj` und `simulate` geben inzwischen **unbedingt** NaN zurück, wenn die Lösung
nicht-endliche Werte enthält — auch bei `reject_nonfinite = false`. Vorher lief eine erfolgreiche
Lösung mit `Inf`-Einträgen durch (die vorhandene Prüfung greift nur bei NaN) und erzeugte einen
unendlichen Loss; jetzt wird sie als ungültig gewertet und bekommt die Penalty.

Zu tun: diese Prüfung an `reject_nonfinite` koppeln, sodass der Default-Pfad exakt das alte
Verhalten zeigt. Der Zähler für nicht-endliche Solves bleibt in beiden Fällen aktiv, damit
messbar ist, ob der Fall überhaupt auftritt.

### 5. Notbremse zuverlässig erkennen

Die Unterscheidung „Wall-Clock-Notbremse vs. Iterationslimit" erfolgt über Teilstring-Suche nach
`"time"` im Retcode. Liefert Optimization.jl bei einem Zeitabbruch einen anderen Retcode, wird ein
ausgelöster Bremseingriff still als Iterationslimit verbucht — genau der Fall, den WP-P1
ausschließen sollte.

Zu tun:
- Die Zuordnung gegen die tatsächlich auftretenden Retcodes absichern statt gegen Teilstrings zu
  raten. Ein Retcode, der sich keiner der bekannten Kategorien zuordnen lässt, muss als eigene
  Kategorie gezählt und protokolliert werden, nicht einer bestehenden zugeschlagen.
- Der heutige Zähler `optimizer_iteration_limit_hits` enthält faktisch auch echte
  Konvergenzfehler. Benenne die Kategorien so, dass sie das abbilden.
- Der Benchmark gibt die beobachteten Retcode-Strings aus, damit die Zuordnung einmal empirisch
  bestätigt werden kann.

### 6. Determinismus über den Regression-Runner hinaus (dokumentieren, nicht umstellen)

Der Struct-Default `time_limit_s = 300.0` ist unverändert; alle anderen Aufrufer
(`benchmarks/benchmark_evogrow.jl`, `experiments/run_experiment.jl`, die übrigen `studies/`)
konstruieren weiterhin ohne expliziten Wert und sind damit wall-clock-abhängig. Das betrifft auch
den in CLAUDE.md eingefrorenen Paper-1-Pfad.

Zu tun: **keine** Umstellung dieser Aufrufer in diesem WP. Stattdessen eine kurze Notiz in
`DIARY.md`, die den Zustand festhält, damit er vor dem Phase-B-Experiment entschieden wird.

## Verification

Rechne nur schnelle Zellen. **Kein** Volllauf, **kein** vollständiger Mikro-Benchmark auf System 26.

1. Ohne Screening-Budgets ist System 11 (alle drei Seeds) für **beide** Varianten bit-identisch zur
   Baseline v0 (`studies/regression/history.jsonl`, Fingerprint `0c739d4e36ee6498`): Loss,
   `final_stage`, `pruned_match`.
2. Mit aktivierten Screening-Budgets tragen v2.2- **und** v3-Records gefüllte Instrumentierungs-
   felder und `screening_budgets_active = true`; ohne Aktivierung `false`.
3. Ein künstlich divergierender Kandidat wird über `unstable_check` beendet und als verworfen
   gezählt — belege das mit den Zählern, nicht mit einer Behauptung.
4. Der Mikro-Benchmark läuft mit reduziertem Level-Budget auf einem **billigen** System (z. B.
   System 3) einmal durch und erzeugt vollständige Ausgabedateien inklusive Retcode-Strings.
   System 26 bleibt dem externen Lauf vorbehalten.

Nenne im Abschlussbericht, welche Zellen du tatsächlich gerechnet hast, und die beobachteten
Retcode-Strings.

## Constraints

- Kein Eingriff in Wachstum, Selektion, Promotion oder Stopplogik.
- Ohne aktivierte Screening-Budgets darf sich kein Ergebnis ändern — für v2.2 **und** v3.
- Bestehende Record-Felder, Metrikdefinitionen und die 23 Baseline-v0-Records bleiben unangetastet.
- Keine neuen Abhängigkeiten.
- Weiterhin nicht Teil dieses WP: ableitungsbasiertes Screening-Kriterium, `use_pretuning`,
  finaler Refit auf Referenz-Fidelity, Parallelisierung, WP-v3.3, WP-H2.
