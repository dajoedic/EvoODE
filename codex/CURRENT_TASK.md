# CURRENT TASK: WP-P2.2c — Wiederverwendbarer Smoke-Test für die Screening-Variante, ausführen und berichten

**Language: Julia**

## Context

WP-P2.2b ist umgesetzt und reviewt (`7f52676`). Alle sechs Punkte sind korrekt behoben:
Feldkollision aufgelöst, Erschöpfung am Iterationslimit gemessen, Diagnose-Stichprobe abgelehnter
Kandidaten ohne Einfluss auf die Suche, `screen_k < pop_size` wird abgelehnt, Struct-Defaults
angeglichen, finaler Refit in den Summen, Abweichungen dokumentiert.

Offen ist etwas anderes: **Die Variante ist nie ausgeführt worden.** Die in WP-P2.2 und WP-P2.2b
geforderten Messzahlen wurden beide Male nicht geliefert, und im Repository liegen keine Artefakte
eines Verifikationslaufs. Statisch sieht der Code korrekt aus — ob er läuft und ob das Kriterium
taugt, ist unbekannt.

Dieses WP schließt die Lücke, und zwar so, dass die Prüfung **wiederholbar** wird statt einmalig.
Sie wird bei WP-v3.3 und bei jeder weiteren Änderung am Bewertungspfad erneut gebraucht.

## Goal

Ein Vergleichsskript unter `studies/debug/`, das auf billigen Systemen den bestehenden
Simulationspfad und die Screening-Variante gegeneinander laufen lässt und die entscheidenden
Kennzahlen ausgibt — plus die tatsächliche Ausführung und ein Bericht mit den gemessenen Zahlen.

## Required Content

### 1. Vergleichsskript

Ein neues Skript unter `studies/debug/`, das für jede Kombination aus

- System 3 (`Logistic growth`, 1D) und System 11 (`Critical slowing down`, 1D, `-u1^3`),
- Seed 42,
- Variante `evogrow_v2_2_stage_local` (Referenz) und der Screening-Variante,

einen Lauf ausführt. Systemdefinitionen aus `studies/regression/diagnostic_systems.jl`
wiederverwenden, nicht neu schreiben. Hyperparameter und `DiscoveryOptions` identisch zur
Regression-Konfiguration wählen, damit die Ergebnisse mit `history.jsonl` vergleichbar sind;
Abweichungen davon sind zu begründen.

Beide Systeme sind billig (Baseline v0: System 3 rund 5 Minuten bei 30 Leveln, System 11 unter
2 Sekunden). Das Skript darf **keine** anderen Systeme rechnen.

### 2. Auszugebende Kennzahlen

Pro Lauf mindestens: Laufzeit, simulierter Loss, `final_stage`, `pruned_match`,
`total_parameter_fits`, `total_ode_solves`, `total_simulation_time_s`.

Für die Screening-Variante zusätzlich: `screening_evals`, `invalid_screening_evals`,
`polished_candidates`, `polish_budget_exhausted`, `polish_convergence_failures`,
`rank_agreement_spearman`, `rejected_diagnostic_candidates`, `rejected_beats_best_selected`,
`screening_time_s`, `polish_time_s`, `rejected_diagnostic_time_s`, `final_refit_time_s`.

Als Gegenüberstellung je System: Laufzeitverhältnis Referenz zu Screening, und ob beide dieselbe
Struktur gefunden haben.

Ausgabe nach `outputs/studies/debug/<skript_slug>/` (eigener Unterordner, nicht direkt in den
Elternordner), zusätzlich lesbar auf die Konsole.

### 3. Ausführen und berichten

Das Skript ausführen und die Ergebnisse im Abschlussbericht **als Zahlen** wiedergeben. Der
Bericht muss diese vier Fragen ausdrücklich beantworten:

1. Läuft die Screening-Variante ohne Fehler durch?
2. Findet sie auf System 11 die korrekte Struktur (`-u1^3`)? Der Referenzpfad schafft das in
   1,7 Sekunden. Falls nein, ist das ein zentrales Ergebnis und ausführlich zu berichten — es
   würde bedeuten, dass das Ableitungsresiduum als Auswahlsignal nicht taugt.
3. Wie hoch ist der Anteil erschöpfter Polish-Budgets? Wird das Budget durchgängig ausgeschöpft,
   sind die Losses nicht mit dem Simulationspfad vergleichbar und die Kennzahl ist wertlos.
4. Wie fällt die Rangübereinstimmung aus, und wie oft hätte ein abgelehnter Kandidat den besten
   ausgewählten geschlagen?

Bleibt eine dieser Fragen unbeantwortet, gilt das WP als nicht erfüllt.

### 4. Bestehenden Pfad gegenprüfen

Zusätzlich bestätigen, dass der Referenzlauf auf System 3 Seed 42 weiterhin den Loss
`2.663641831768419e-10` bei `final_stage = 3` liefert und System 11 Seed 42 den Loss
`4.402192340718147e-15` bei `final_stage = 4` — beides aus Baseline v0
(`studies/regression/history.jsonl`, Fingerprint `0c739d4e36ee6498`). Abweichungen sind zu melden,
nicht zu glätten.

Hinweis: Baseline v0 lief mit 30 Leveln. Wähle im Skript dasselbe Level-Budget, sonst ist der
Vergleich nicht gültig.

## Constraints

- Nur System 3 und System 11. **Nicht** System 26, 31 oder 63.
- Keine Änderung an `src/`, an der Regression-Konfiguration oder am `config_fingerprint`.
- Kein Schreiben in `studies/regression/history.jsonl`.
- Keine neuen Abhängigkeiten.
- Nicht Teil dieses WP: WP-v3.3, WP-H2, Anpassungen am Screening-Kriterium selbst. Falls der Lauf
  ein Problem im Kriterium zeigt, ist es zu **berichten**, nicht zu beheben.
