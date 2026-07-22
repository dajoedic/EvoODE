# CURRENT TASK: WP-P2.1 — Design-Notiz „Ableitungsbasiertes Screening"

**Language: Julia** (Deliverable ist ein Dokument, kein Code — siehe Constraints)

## Context

Der Mikro-Benchmark auf System 26 (Seed 42, v2.2, 18 Level, je 370 Parameter-Fits) hat den
Kostentreiber quantifiziert:

| | Referenz | Screening-Budgets |
|---|---|---|
| Laufzeit | 3222,6 s | 1189,8 s |
| ODE-Solves | 1.741.484 | 2.488.973 |
| Kosten pro Solve | 1,763 ms | 0,409 ms |
| **Solve-Anteil an Laufzeit** | **95 %** | 86 % |
| Overhead ohne Solve | 153 s | 166 s |

Solver-Tuning hat 2,71x gebracht und ist damit ausgereizt — mehr als den Solve-Anteil kann es
nicht heben. Der gesamte Overhead außerhalb der Integration beträgt 153 s bei 3222 s Laufzeit.
**Ein Screening ohne Integration in der Suchschleife hat auf dieser Zelle eine Obergrenze von
~21x.** Pro Parameter-Fit fallen derzeit rund 4.700 bis 7.300 vollständige Integrationen an.

Die Maschinerie existiert bereits: `src/optimize/pretune.jl` schätzt Ableitungen per finiter
Differenzen, baut eine Design-Matrix aus den aktiven Basistermen und löst das lineare System.
Sie wird bisher ausschließlich als Warmstart benutzt — und im Regression-Config über
`USE_PRETUNING = false` gar nicht.

Das ist **keine** Performance-Optimierung. Es ändert das Kriterium, nach dem Strukturen bewertet
und ausgewählt werden, und damit den Suchprozess selbst. Deshalb zuerst eine Design-Notiz, analog
zu WP-v3.1, bevor eine Zeile Code entsteht.

## Goal

Eine Design-Notiz `docs/evogrow_screening_design.md`, die festlegt, wie ein ableitungsbasiertes
Screening-Kriterium in EvoODE aussehen soll, welche Teile der Pipeline weiterhin simulieren
müssen, und welche wissenschaftlichen Konsequenzen das hat.

Das Deliverable ist das Dokument. Es wird **nichts implementiert**.

## Required Content

Die Notiz muss folgende Abschnitte enthalten. Wo eine Frage nicht entscheidbar ist, muss sie als
offene Entscheidung benannt werden — nicht stillschweigend beantwortet.

### 1. Motivation und Messlage
Die Zahlen oben, korrekt eingeordnet: was gemessen wurde (eine Zelle, ein Seed), was daraus folgt
und was nicht.

### 2. Das Kriterium
Was genau als Screening-Score berechnet wird. Wie die Ableitungen aus den Daten geschätzt werden,
wie die Design-Matrix aus den aktiven Basistermen entsteht, und warum das Problem für eine in den
Parametern lineare Basis in geschlossener Form lösbar ist. Verhältnis zum bestehenden
`pretune.jl`: was wiederverwendbar ist und was fehlt.

### 3. Zweistufige Auswertung
Welcher Teil der Suche mit dem billigen Kriterium arbeitet und welcher weiterhin simuliert.
Mindestens zu klären:
- Werden alle Kandidaten gescreent und nur die besten k simuliert, oder wird gar nicht mehr
  simuliert außer am Ende?
- Nach welchem Kriterium wird k gewählt?
- Werden die Parameter des Endkandidaten auf voller Genauigkeit nachgefittet? (Heute geschieht das
  nicht: `discover()` refittet nur bei Parameteranzahl-Mismatch.)

### 4. Konsequenzen für Stopplogik, Plateau-Erkennung und Stage-Promotion
Das ist der kritische Abschnitt. Plateau-Erkennung, Loss-Toleranz und Stage-Promotion arbeiten
heute alle auf dem **Simulations-Loss**. Wenn die Suchschleife auf einem Ableitungsresiduum
bewertet, muss festgelegt werden, welches Signal diese Entscheidungen künftig trägt — und was
das für die Vergleichbarkeit mit der bisherigen Stopplogik bedeutet.

Relevanter Befund aus dem v0-Log, der hier einzuarbeiten ist: in **allen 13 Zellen, die über
Level 18 hinausliefen, war der Loss bei Level 18 bereits identisch zum Endergebnis**. Die Suche
lief dennoch bis Level 26–29 weiter, weil Plateau-Erkennung Stage-Promotion auslöst statt
Terminierung. 15,8 von 40,5 Stunden wurden nach Level 18 ohne jede Loss-Verbesserung verbraucht.
Die Notiz muss adressieren, ob und wie ein Screening-Kriterium diese Situation verändert.

### 5. Wo Simulation unverzichtbar bleibt
Begründung, an welchen Stellen ein Ableitungsresiduum das Simulationsverhalten nicht ersetzen
kann (u. a. Stabilität über die Trajektorie, Fehlerakkumulation, Divergenz), und wie die Notiz
sicherstellt, dass das Endergebnis weiterhin auf simuliertem Loss bewertet wird.

### 6. Schwächen und Risiken
Insbesondere Rauschempfindlichkeit finiter Differenzen, Abhängigkeit von der Abtastdichte, und
der Fall, dass Ableitungsresiduum und Simulations-Loss unterschiedliche Strukturen bevorzugen.
Benenne konkret, welche Beobachtung den Ansatz **falsifizieren** würde.

### 7. Verhältnis zum wissenschaftlichen Beitrag
CLAUDE.md positioniert EvoODE gegen SINDy (feste Bibliothek, Ableitungs-Regression) und GP
(globale Suche). Ein ableitungsbasiertes Screening rückt die Bewertung näher an SINDy. Die Notiz
muss explizit adressieren, ob und warum der Beitrag — strukturiertes inkrementelles Wachstum mit
Stage-Kontrolle — davon unberührt bleibt, und wie das in Paper 1 dargestellt würde.

### 8. Vergleichbarkeit und Migrationspfad
Was mit Baseline v0 (`studies/regression/history.jsonl`, Fingerprint `0c739d4e36ee6498`) und den
bestehenden Ergebnissen passiert. Welche Läufe neu gerechnet werden müssten und in welcher
Reihenfolge. Ob das Screening als Variante neben dem Simulationspfad bestehen bleibt oder ihn
ersetzt.

### 9. Offene Entscheidungen
Nummerierte Liste dessen, was diese Notiz **nicht** entscheidet und wer bzw. welche Messung es
entscheiden muss.

## Verification

Kein Code, keine Läufe. Prüfe stattdessen:
1. Alle neun Abschnitte sind vorhanden und inhaltlich gefüllt.
2. Die zitierten Zahlen stimmen mit `outputs/studies/profiling/profile_eval_cost/summary.json`
   und dem DIARY-Eintrag vom 2026-07-22 überein.
3. Abschnitt 4 und Abschnitt 7 nehmen jeweils eine klare Position ein oder benennen die
   Entscheidung ausdrücklich als offen — kein Ausweichen.

## Constraints

- **Kein Code.** Keine Änderung an `src/`, `studies/`, `benchmarks/`, `experiments/`. Einziges
  Artefakt ist `docs/evogrow_screening_design.md`.
- Keine Änderung an Konfiguration, Metriken oder `config_fingerprint`.
- Das Level-Budget der Regression-Suite bleibt bei 30. Eine Kürzung würde `final_stage`,
  `stage_overshoot` und `wasted_levels` verändern und damit genau das Overshoot-Phänomen
  wegschneiden, das v3 beheben soll. Nicht anfassen.
- Keine Vorwegnahme von WP-v3.3, WP-H2 oder der Implementierung selbst.
