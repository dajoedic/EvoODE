# CURRENT TASK: WP-T2 — Toleranz und Screening auf System 26 (dem Gate-1-System)

**Language: Julia**

## Context

Alle bisherigen Befunde zu Toleranz und Screening stammen von System 3 und System 11 — beide
eindimensional und exakt darstellbar. Die wissenschaftlich relevanten Systeme sind die gekoppelten.
System 26 (Lotka-Volterra, 2D) ist das System, an dem Gate 1 gescheitert ist: v2.2 fand
`du1 = 5,05·u1 − 3,87·u1·u2`, `du2 = 1,13·u1 − 1,80·u1²` — Terme komplett falsch, Loss ~1,4e-3,
Eskalation auf Stage 5 statt der erwarteten Stage 3.

Dieses WP prüft drei Dinge auf genau diesem System, mit einer scharfen, falsifizierbaren
Vorhersage.

### Die Vorhersage (Prüfstein für den Bericht)

Auf System 3 half die engere Toleranz (1e-6 → 1e-8), weil der Loss dort nahe der Schwelle
`loss_tol = 1e-8` operiert: Bei 1e-6 erreicht der Optimierer diese Schwelle nicht zuverlässig, es
gibt keinen Abbruch, die Suche eskaliert.

Auf System 26 liegt der Loss-Boden bei ~1,4e-3 — rund drei Größenordnungen **über** selbst der
1e-6-Toleranz. `loss_tol = 1e-8` kann dort nie feuern, unabhängig von der Toleranz, und die
Eskalation wird von der Plateau-Erkennung getrieben, nicht von der Loss-Schwelle.

**Vorhergesagt wird daher: Die engere Toleranz ändert `final_stage` und `stage_overshoot` auf
System 26 nicht (oder kaum). Der Overshoot ist hier algorithmisch, nicht numerisch.**

Der Bericht muss diese Vorhersage ausdrücklich bestätigen oder widerlegen — mit den gemessenen
Stage-Zahlen, nicht mit einer Interpretation.

## Goal

Ein **lauffertiges** Skript, das ein Experiment auf System 26, Seed 42, mit drei Bedingungen
definiert und die zur Prüfung der Vorhersage nötigen Zahlen ausgibt. Den mehrstündigen
System-26-Lauf startet ausschließlich der Betreiber extern — dieses WP liefert das Skript, führt es
aber nicht auf System 26 aus (siehe Verification).

## Files

- **Neu oder erweitern:** Ein Skript, das die drei Bedingungen rechnet. `studies/numerics/` ist der
  passende Ort; die Bedingungsdefinitionen und das Anker-Muster aus
  `studies/debug/compare_screening_variant.jl` sollen wiederverwendet werden, nicht neu geschrieben.
- **Nicht ändern:** `src/`, die Regression-Konfiguration, `config_fingerprint`.
- Nicht in `studies/regression/history.jsonl` schreiben. Ausgabe nach
  `outputs/studies/numerics/<skript_slug>/`.

## Required Content

### 1. Drei Bedingungen, System 26, Seed 42, 30 Level

- **R6** Referenzpfad (EvoGrow v2.2 stage_local, `use_pretuning = false`), Bewertungstoleranz
  **1e-6**.
- **R8** Referenzpfad, identisch, Bewertungstoleranz **1e-8**.
- **D8** Screening-Variante mit `screening_score = :nested_f` und `polish_start = :reference`
  (Bedingung D aus WP-P2.4), Bewertungstoleranz **1e-8**.

Level-Budget **30** — nicht 18. Der Overshoot ist der Untersuchungsgegenstand und muss sich
entfalten können; ein kleineres Budget würde ihn abschneiden. Alle übrigen Hyperparameter identisch
zur Regression-Konfiguration.

Erwartete Stage für System 26: **3**. `stage_overshoot = max(0, final_stage − 3)`.

### 2. Reihenfolge und Robustheit

Der Lauf dauert Stunden und wird extern gestartet. Reihenfolge nach steigender erwarteter Laufzeit:
**D8 zuerst** (billigste, laut WP-P2.4 auf System 3 rund Faktor 6 schneller), dann **R8**, dann
**R6** (laut Baseline v0 rund 3 Stunden). Nach **jeder** Bedingung sofort schreiben und flushen,
damit ein Abbruch höchstens die gerade laufende Bedingung kostet.

### 3. Ankerprüfung

**R6 muss Baseline v0 reproduzieren.** System 26, Seed 42, 30 Level, Toleranz 1e-6:
`loss = 0.001391623174905009`, `final_stage = 5`, `stage_overshoot = 2`, `pruned_match = false`
(aus `studies/regression/history.jsonl`, `config_fingerprint 0c739d4e36ee6498`). Weicht R6 davon
ab, ist der Aufbau fehlerhaft — melden, nicht glätten. Diese Prüfung ist wichtiger als die anderen
beiden Bedingungen: ohne bestätigten Anker ist nichts interpretierbar.

### 4. Metriken je Bedingung

`loss`, `final_stage`, `stage_overshoot`, `wasted_levels`, `pruned_match`, Laufzeit,
`total_parameter_fits`, `total_ode_solves`, Kosten pro Integration, sowie die gefundene Struktur
in lesbarer Form. Für D8 zusätzlich die Screening-Diagnostik (Rangübereinstimmung samt Zahl
auswertbarer Level, vom Gate abgelehnte Kinder, Abweichung der Auswahl vom reinen Residuen-Score,
Anteil erschöpfter Polish-Budgets).

Zusätzlich eine **Per-Stage-Kostenaufschlüsselung** je Bedingung (Levelzahl, Zeit, Zeit pro Level
pro Stage), im selben Zuschnitt wie die Baseline-Tabelle im Journal (`docs/projektjournal.md`,
Abschnitt 3.8). Damit ist ablesbar, wo die Zeit hingeht und ob sich das Kostenprofil zwischen den
Toleranzen verschiebt.

### 5. Ausgaben, aus denen später vier Fragen beantwortet werden

Das Skript muss so schreiben, dass **nach dem externen Lauf** diese vier Fragen aus den
Ausgabedateien beantwortbar sind. Das Beantworten selbst ist nicht Teil dieses WP (siehe
Verification) — das Skript muss die nötigen Zahlen nur vollständig ablegen:

1. **Reproduziert R6 den Baseline-v0-Anker?** (Die vier Werte neben den Baseline-v0-Werten.)
2. **Verändert die engere Toleranz den Overshoot?** R6 gegen R8: `final_stage`, `stage_overshoot`,
   `wasted_levels`, Laufzeit.
3. **Trägt Bedingung D auf einem gekoppelten System?** D8 gegen R8: Loss, `final_stage`,
   `pruned_match`, Laufzeit, Speedup, gefundene Struktur.
4. **Wo geht die Zeit hin?** Per-Stage-Aufschlüsselung, und die Kosten pro Integration je Toleranz.

## Verification

**Wichtig: Den eigentlichen System-26-Lauf NICHT selbst starten.** Dieser Lauf dauert Stunden und
wird ausschließlich extern vom Betreiber gestartet. Aufgabe dieses WP ist, das Skript
**lauffertig zu liefern**, nicht es auszuführen.

Zur Absicherung der Lauffähigkeit ist ausschließlich ein **billiger Smoke-Test** erlaubt: dasselbe
Skript einmal auf **System 3** (nicht 26) mit stark reduziertem Level-Budget (Richtwert 4 Level)
durchlaufen lassen, nur um zu bestätigen, dass alle drei Bedingungen ohne Fehler starten, die
Ausgabedateien korrekt geschrieben werden und die Anker-Logik greift. Diesen Smoke-Test-Zustand
danach wieder auf die Zielkonfiguration (System 26, Seed 42, 30 Level) zurückstellen und im
Abschlussbericht angeben, dass das geschehen ist.

Der Abschlussbericht nennt: dass das Skript lauffertig ist, was der Smoke-Test auf System 3 ergeben
hat, und den exakten Befehl, mit dem der Betreiber den System-26-Lauf startet. **Keine gemessenen
System-26-Zahlen** — die entstehen erst beim externen Lauf.

Grobe Kostenerwartung des späteren externen Laufs zur Einordnung im Skript-Header: D8 unter einer
Stunde, R8 offen (Teil der Messung), R6 rund 3 Stunden.

## Constraints

- Reine Messung. Kein Eingriff in `src/`, keine Konfigurationsumstellung, keine Fingerprint-Änderung.
- Der Referenzpfad bleibt verhaltensgleich; die R6-Ankerprüfung ist Teil der Verifikation.
- Trajektorienerzeugung bleibt bei `abstol = reltol = 1e-9`; variiert wird nur die
  Bewertungstoleranz.
- Keine neuen Abhängigkeiten.
- Nicht Teil dieses WP: dauerhafte Umstellung der Bewertungstoleranz im Regression-Runner, neue
  Baseline, WP-v3.3, Systeme 31/63.
