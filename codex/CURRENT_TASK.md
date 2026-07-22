# CURRENT TASK: WP-P2.2 — Ableitungsbasiertes Screening als eigene Variante implementieren

**Language: Julia**

## Context

Die Design-Notiz `docs/evogrow_screening_design.md` (WP-P2.1) ist abgenommen. Das Review hat sie
um ein Kostenmodell ergänzt, das die Architektur festlegt. Grundlage sind die gemessenen Werte aus
`outputs/studies/profiling/profile_eval_cost/summary.json`, Fall A (System 26, Seed 42, 18 Level):

```
370 Parameter-Fits über 18 Level     = 20,6 Fits pro Level
4.707 ODE-Solves pro Fit             (bei maxiters = 200)
  -> 23,5 Solves pro BFGS-Iteration
1,763 ms pro Solve
  -> 41,5 ms pro BFGS-Iteration
  -> 170,9 s pro Level (heutiger Pfad)
```

Der Speedup entsteht **nicht** durch das Screening als solches, sondern dadurch, dass die
geschlossene Least-Squares-Lösung auf Ableitungsresiduen die rund 200 BFGS-Iterationen pro
Kandidat ersetzt. Das ist die Kernaussage und muss in der Implementierung sichtbar sein.

Reines Screening ohne jede Simulation wäre am billigsten, hat aber ein Problem: Parameter aus dem
Ableitungs-LS sind **nicht** für das Simulationsziel optimiert. Der simulierte Loss einer korrekten
Struktur kann damit schlecht aussehen, und die bestehenden Schwellen (`plateau_tol = 1e-4`,
`loss_tol = 1e-8`) sind auf BFGS-optimierte Losses kalibriert. Ein reiner LS-Pfad würde die
Stopplogik unbrauchbar machen.

Lösung: ein **begrenztes Nachpolieren** der ausgewählten Kandidaten. Kostenmodell pro Level:

| k | Polish-Iterationen | Kosten/Level | Solve-Faktor |
|---|---|---|---|
| 10 | 0 | 0,02 s | (Stopplogik kaputt) |
| 10 | 10 | 4,2 s | 41x |
| 10 | 20 | 8,3 s | 21x |
| 5 | 20 | 4,2 s | 41x |
| 10 | 50 | 20,8 s | 8x |

Realistische Gesamterwartung nach Abzug des Overhead-Bodens (153 s im Referenzlauf): **etwa
10–15x** auf dieser Zelle, nicht die 21x der theoretischen Untergrenze.

## Goal

Eine neue Struktursuch-Variante, die Kandidaten über ein Ableitungsresiduum in geschlossener Form
bewertet, nur eine kleine Auswahl mit begrenztem Budget nachpoliert und simuliert, und alle
Auswahl-, Plateau- und Promotionsentscheidungen weiterhin auf dem **simulierten** Loss trifft.

Der bestehende Simulationspfad bleibt vollständig unberührt und weiterhin lauffähig.

## Files

- **Neu:** eine eigene Datei unter `src/structure/` für die neue Variante, registriert in
  `src/EvoODE.jl`.
- **Erweitern, ohne Verhalten zu ändern:** `src/optimize/pretune.jl` (siehe Punkt 2).
- **Nicht anfassen:** `src/structure/evogrow.jl`, `src/structure/evogrow_v3.jl`,
  `src/structure/gp.jl`, `src/core/stopping.jl`, `src/core/discover.jl`, die Regression-
  Konfiguration und Baseline v0.

## Required Content

### 1. Eigene Variante, kein Ersatz

Die neue Variante wird als eigener Strukturtyp implementiert, parallel zu `EvoGrow`. Wachstum,
Selektion, Stage-Progression und Stopplogik folgen dem Verhalten von `EvoGrow` v2.2; **einzig die
Kandidatenbewertung ändert sich**. Vorhandene Hilfsfunktionen sind wiederzuverwenden statt zu
duplizieren, wo das ohne Verhaltensänderung an `EvoGrow` möglich ist.

### 2. Screening-Score in `pretune.jl`

`pretune.jl` liefert heute nur einen Warmstart-Vektor. Ergänze eine Funktion, die für eine gegebene
Struktur zusätzlich das **Ableitungsresiduum** und Diagnostik zurückgibt: die gefitteten
LS-Parameter, den Residuenwert, und ein Gültigkeitsflag.

Kritisch: `pretune_parameters` gibt heute `zeros(n)` zurück, sobald **eine** Gleichung
nicht-endliche Werte oder `norm > 1e6` liefert. Als Warmstart harmlos, als Screening-Score
inakzeptabel — ein entarteter Kandidat bekäme damit stillschweigend die Bewertung „alle Parameter
null" statt als ungültig zu gelten. Der neue Pfad muss solche Fälle **explizit als ungültig
markieren** und zählen.

Das bestehende Verhalten von `pretune_parameters` selbst darf sich nicht ändern; andere Aufrufer
verlassen sich darauf.

### 3. Ablauf pro Level

Pro Level:

1. Alle Kandidaten (Eltern und Kinder) über den Screening-Score bewerten. Keine Simulation,
   kein BFGS.
2. Die besten `k` nach Screening-Score auswählen. Der aktuelle Beste (Incumbent) wird **immer**
   mit ausgewählt, unabhängig von seinem Screening-Rang, damit die Population nie ihren Anker
   verliert.
3. Nur diese ausgewählten Kandidaten mit einem **begrenzten** Optimierer-Budget nachpolieren,
   ausgehend von den LS-Parametern als Startwert.
4. Für die nachpolierten Kandidaten den simulierten Loss und das Suchziel wie bisher berechnen.
5. Nur nachpolierte, simulierte Kandidaten dürfen in die Population übernommen werden. Die
   übrigen werden verworfen.

`k` und das Polish-Budget sind konfigurierbare Felder der neuen Variante. Defaults: `k = pop_size`,
Polish-Budget deutlich kleiner als `BFGSOptimizer.maxiters` (Richtwert 20 Iterationen). Begründe
die gewählten Defaults im Docstring unter Bezug auf das Kostenmodell oben.

### 4. Vergleichbarkeit der Loss-Skala

Das Polish-Budget existiert genau deshalb, damit die berichteten Losses auf derselben Skala liegen
wie im Simulationspfad. Diese Annahme muss überprüfbar sein: der Lauf muss protokollieren, wie
viele der ausgewählten Kandidaten ihr Polish-Budget ausgeschöpft haben. Ein durchgängiges
Ausschöpfen bedeutet, dass das Budget zu klein ist und die Losses nicht vergleichbar sind.

### 5. Stopplogik und Stage-Promotion unverändert

Plateau-Erkennung, Loss-Toleranz und Stage-Promotion arbeiten weiterhin ausschließlich auf dem
**simulierten** Loss der ausgewählten Kandidaten. Das Ableitungsresiduum darf ausschließlich zur
Vorauswahl dienen und keine dieser Entscheidungen beeinflussen. Diese Trennung ist der Kern der
Design-Notiz (Abschnitt 4) und darf nicht aufgeweicht werden.

### 6. Finales Ergebnis auf voller Genauigkeit

Die final gewählte Struktur wird einmal mit dem vollen Optimierer-Budget nachgefittet und wie
bisher simuliert validiert. Der berichtete `loss` in `DiscoveryResult` muss weiterhin ein
simulierter Loss auf voller Genauigkeit sein. Kosten: ein Fit pro Lauf, vernachlässigbar.

### 7. Instrumentierung

Die Zähler aus WP-P1/P1b bleiben erhalten und werden weitergereicht. Zusätzlich pro Level und
aggregiert pro Lauf:

- Anzahl Screening-Bewertungen,
- Anzahl ungültiger Screening-Bewertungen (Punkt 2),
- Anzahl nachpolierter Kandidaten,
- Anzahl Kandidaten, die das Polish-Budget ausgeschöpft haben,
- Zeitanteil Screening vs. Polish vs. Simulation,
- **Rangübereinstimmung**: unter den ausgewählten und simulierten Kandidaten die Übereinstimmung
  zwischen der Rangfolge nach Screening-Score und der Rangfolge nach simuliertem Loss.

Der letzte Punkt ist die Messgröße für das zentrale Risiko der Methode (Abschnitt 6 der
Design-Notiz: Zielkonflikt zwischen Ableitungsresiduum und Simulations-Loss). Ohne ihn lässt sich
nicht beurteilen, ob die Vorauswahl gute Kandidaten verwirft. Wähle ein geeignetes Rangmaß und
begründe die Wahl kurz im Docstring.

### 8. Records und Fingerprint

Die neue Variante ist eine zusätzliche Variante im Regression-Runner, nicht ein Ersatz einer
bestehenden. Neue Felder im Record sind zu ergänzen; bestehende Feldnamen und Werte bleiben
unverändert. Dass sich der `config_fingerprint` durch die neue Variante ändert, ist beabsichtigt.
Baseline v0 unter Fingerprint `0c739d4e36ee6498` bleibt unangetastet.

## Verification

Nur billige Zellen rechnen. **Kein** Volllauf, **nicht** System 26, 31 oder 63.

1. Der bestehende Simulationspfad ist unverändert: System 11, alle drei Seeds, v2.2 **und** v3
   liefern weiterhin bit-identische Werte zu Baseline v0 (Loss, `final_stage`, `pruned_match`).
2. Die neue Variante läuft auf System 3 und System 11 durch und liefert einen simulierten Loss auf
   voller Genauigkeit.
3. Auf System 11 (exakt darstellbar, `-u1^3`) findet die neue Variante die korrekte Struktur.
   Falls nicht, ist das ein zentrales Ergebnis und ausführlich zu berichten, nicht zu übergehen.
4. Die Zähler aus Punkt 7 sind gefüllt und plausibel; insbesondere ist zu berichten, wie viele
   Kandidaten das Polish-Budget ausgeschöpft haben und wie gut die Rangübereinstimmung ist.
5. Berichte die gemessene Laufzeit der neuen Variante gegen den Simulationspfad auf denselben
   Zellen — mit Zahlen, nicht mit „läuft schneller".

## Constraints

- Der bestehende Simulationspfad bleibt vollständig funktionsfähig und verhaltensgleich.
- Plateau, Stopplogik und Promotion laufen ausschließlich auf simuliertem Loss.
- Der berichtete `loss` bleibt ein simulierter Loss auf voller Genauigkeit.
- Bestehende Record-Felder, Metrikdefinitionen und Baseline v0 bleiben unangetastet.
- Level-Budget der Regression-Suite bleibt bei 30.
- Keine neuen Abhängigkeiten.
- Nicht Teil dieses WP: `use_pretuning` im Regression-Config umstellen, WP-v3.3, WP-H2,
  Parallelisierung, Anwendung des Screenings auf `GPStructureSearch`.
