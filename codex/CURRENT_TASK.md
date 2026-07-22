# CURRENT TASK: WP-T1 — Rauschgrenze der Solver-Toleranz im Bewertungspfad

**Language: Julia**

## Context

Aus WP-P2.3 stammt ein unaufgeklärter Befund: Der finale Refit der Screening-Variante auf System 3
kehrte nach **5 Loss-Auswertungen** mit `retcode = Success` zurück, ohne den Loss von 3,24e-8 zu
verbessern — obwohl bei identischer Struktur nachweislich 2,66e-10 erreichbar ist.

Vermutung: Der Bewertungspfad simuliert mit `abstol = reltol = 1e-6`
(`BFGSOptimizer`-Default, so auch im Regression-Runner gesetzt). Finite-Differenzen-Gradienten
einer Größe, die nur auf etwa 1e-6 genau berechnet wird, sind Rauschen, sobald die Größe selbst in
der Nähe dieser Schranke liegt. Der Optimierer sähe dann keinen Abstieg mehr und meldete
Konvergenz.

Die Frage reicht weit über die Screening-Spur hinaus. System 11 meldet in Baseline v0 einen Loss
von **4,402192340718147e-15**. Das entspricht einem mittleren Fehler von rund 6,6e-8 pro Punkt —
deutlich unterhalb der Genauigkeit, mit der der Solver diese Trajektorie überhaupt berechnet.
Diese Zahl steht in Baseline v0, in der Phase-A-Auswertung und in jeder heutigen
Regressionsprüfung. Ist sie numerisches Rauschen, betrifft das die Belastbarkeit der berichteten
Losses im gesamten Projekt sowie die Frage, ob `loss_tol = 1e-8` als Abbruchkriterium überhaupt
sinnvoll definiert ist.

Dieses WP klärt das, bevor die Screening-Spur weiter getestet wird (WP-P2.4). Grund: Wenn die
Vermutung zutrifft, könnte das gesamte beobachtete Versagen der Screening-Variante auf System 3 ein
Toleranz-Artefakt sein — und ein Test des Auswahlkriteriums unter unkontrolliertem Confounder wäre
wertlos.

## Goal

Ein Diagnose-Experiment, das drei Fragen mit Zahlen beantwortet:

- **F1:** Setzt die Solver-Toleranz eine Rauschgrenze, unterhalb derer der Parameter-Optimierer
  nicht mehr verbessern kann?
- **F2:** Sind berichtete Losses unterhalb der Solver-Genauigkeit belastbar?
- **F3:** Was kostet höhere Genauigkeit an Laufzeit und Integrationen?

## Files

- **Neu:** ein Skript unter `studies/numerics/` (neues Themenverzeichnis).
- Ausgabe nach `outputs/studies/numerics/<skript_slug>/` (eigener Unterordner).
- **Nicht ändern:** `src/`, `studies/regression/run_regression.jl`, die Regression-Konfiguration.
  Es wird nichts repariert, nur gemessen.
- Nicht in `studies/regression/history.jsonl` schreiben.

## Required Content

### Systeme und Strukturen

System 3 (`Logistic growth`) und System 11 (`Critical slowing down`), Definitionen aus
`studies/regression/diagnostic_systems.jl`. Trajektorien wie dort erzeugt.

Verwendet wird jeweils die **bekannte korrekte Struktur** (aus `expected_active_idxs`), nicht eine
gesuchte. Es geht um numerisches Verhalten bei fester Struktur, nicht um Strukturfindung.

### Toleranzraster

`abstol = reltol` ∈ {1e-5, 1e-6, 1e-8, 1e-10, 1e-12}.

1e-6 ist der heutige Default des Bewertungspfads. 1e-5 ist der Wert, den die
WP-P1b-Screening-Budgets setzen — er gehört ins Raster, damit wir wissen, was diese Wahl gekostet
hat. Die Trajektorienerzeugung selbst bleibt unverändert bei 1e-9.

### Teil A — Belastbarkeit der berichteten Losses (F2)

Ohne Optimierer. Für jede Toleranz die Struktur mit den **wahren** Parametern simulieren und den
Loss gegen die Referenztrajektorie berechnen (System 3: `0.79*u1 - 0.0106*u1^2`; System 11:
`-u1^3`; wahre Werte aus `diagnostic_systems.jl` ableiten, nicht raten).

Dieser Wert ist der bestmögliche erreichbare Loss bei dieser Toleranz. Liegt er bei 1e-6 zum
Beispiel bei 1e-10, dann ist jeder berichtete Loss unterhalb von 1e-10 bei dieser Toleranz nicht
interpretierbar.

Zusätzlich ausweisen: den in Baseline v0 berichteten Loss (System 3: `2.663641831768419e-10`,
System 11: `4.402192340718147e-15`) neben dem so bestimmten Boden, damit die Einordnung unmittelbar
ablesbar ist.

### Teil B — Rauschgrenze des Optimierers (F1)

Für jede Toleranz `fit_parameters` mit der Regression-Konfiguration (`maxiters = 200`) auf der
festen korrekten Struktur laufen lassen, ausgehend von **drei** Startpunkten:

1. dem heutigen Standardstart des Bewertungspfads,
2. dem Least-Squares-Warmstart aus `pretune_parameters`,
3. den wahren Parametern, leicht gestört (Größenordnung 1 % relativ).

Startpunkt 3 ist der schärfste Test: von dort aus muss ein funktionierender Optimierer den Loss
messbar senken. Tut er es bei 1e-6 nicht und bei 1e-10 doch, ist die Vermutung bestätigt.

Je Kombination protokollieren: erreichter Loss, Zahl der Loss-Auswertungen, Retcode, Laufzeit,
Zahl der Integrationen. Alle Zähler existieren bereits im Rückgabe-Meta von `fit_parameters`.

**Falsifizierbare Vorhersage:** Bei 1e-6 bleibt der Warmstart nahe seinem Ausgangswert stehen und
meldet `Success` nach wenigen Auswertungen; bei 1e-10 verbessert er sich deutlich. Tritt das nicht
ein, ist die Vermutung widerlegt — dann ist das das Ergebnis und so zu berichten.

### Teil C — Preis der Genauigkeit (F3)

Je Toleranz Laufzeit und Zahl der Integrationen ausweisen, sowohl für einen einzelnen Fit als auch
hochgerechnet auf einen typischen Suchlauf (Größenordnung genügt: Baseline v0 rechnete rund 20
Parameter-Fits pro Level).

### Bericht

Der Abschlussbericht muss F1, F2 und F3 ausdrücklich und mit Zahlen beantworten, und zusätzlich
eine klare Aussage dazu enthalten, ob die in Baseline v0 berichteten Losses für System 3 und
System 11 belastbar sind. Kein Beschönigen in beide Richtungen: Bestätigung der Vermutung ist
ebenso ein Ergebnis wie ihre Widerlegung.

## Verification

Nur System 3 und System 11. **Nicht** System 26, 31 oder 63. Es werden keine Struktursuchen
gerechnet, nur einzelne Fits bei fester Struktur — die Laufzeit liegt damit im Minutenbereich, auch
bei den engsten Toleranzen.

Das Skript ausführen und die Ergebnisse als Zahlen berichten, nicht als „läuft durch".

## Constraints

- Reine Messung. Es wird nichts repariert und keine Konfiguration umgestellt; Konsequenzen werden
  danach getrennt entschieden.
- Kein Eingriff in `src/`, keine Änderung an `config_fingerprint`-relevanter Konfiguration.
- Trajektorienerzeugung bleibt bei `abstol = reltol = 1e-9`; variiert wird ausschließlich die
  Toleranz im Bewertungspfad.
- Keine neuen Abhängigkeiten.
- Nicht Teil dieses WP: WP-P2.4 (harter Penalty), WP-v3.3, Änderungen an der Screening-Variante.
