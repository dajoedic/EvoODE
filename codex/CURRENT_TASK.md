# WP-N12 — Roher und ausgedünnter Support getrennt im Record, mit benannter Definition

**Language: Julia**

## Warum

`docs/paper1_phaseC_benchmark_plan.md` §4a hält als bindende Folgerung fest: **Phase-C-Records
speichern rohen Support, ausgedünnten Support und Koeffizienten — alle drei.** Heute speichert der
Phase-B-Pfad zwei davon:

- `support_terms` — die **rohe** aktive Termmenge (`active_term_names`,
  `studies/regression/run_regression.jl:870`),
- `model_terms` — Terme **mit Koeffizienten** (seit WP-N1),
- `pruned_match` — ein **Bool**, aber **nicht** die ausgedünnte Termmenge selbst.

Der ausgedünnte Support ist damit **nicht rekonstruierbar**, und genau daran ist WP-N7 gescheitert:
Ausdünnen braucht Koeffizienten, Phase B speicherte keine, das Abnahmekriterium war prinzipiell
unerreichbar.

Warum das mehr als Buchhaltung ist: **40 der 110 Phase-B-Supporttreffer (36,4 %) entstehen
ausschließlich durch die Ausdünnungsregel**, auf dim 2 sind es 34 von 53 — also 64 % der Treffer.
Beide Zahlen müssen künftig nebeneinander berichtet werden, und dafür müssen beide im Record stehen.

Zweiter Grund, §4b: **ein Spaltenname trägt heute zwei Bedeutungen.**
`experiments/run_experiment.jl:405` schreibt den **rohen** Match nach `exact_support_match`,
`run_regression.jl` schreibt dort den **ausgedünnten**. Ein Join über diese Spalte vergleicht
verschiedene Größen. Der Record muss die Definition selbst benennen.

Das ist Arbeitspaket **B2** aus §2a des Phase-C-Plans.

## Was zu bauen ist

### 1. Die Ausdünnungsregel bekommt genau eine Implementierung

`support_match_pruned` (`studies/regression/diagnostic_systems.jl:183`) trägt die Regel
`max(1e-6, 1e-3 * max_abs)` **inline**. Für den neuen ausgedünnten Support wird dieselbe Regel
gebraucht.

**Schreibe sie nicht ein zweites Mal.** Ziehe sie in eine eigene, benannte Funktion, die je Gleichung
aus Termindizes und zugehörigen Parametern die **überlebenden** Termindizes liefert, und baue
`support_match_pruned` darauf um. Zwei Kopien einer eingefrorenen Konstante driften irgendwann
auseinander; die Regel ist eingefroren (WP-V1, WP-N2) und darf genau einmal im Code stehen.

Die Regel selbst wird **nicht geändert** — weder Schwelle noch Form.

### 2. Neue Felder im Record

`studies/regression/run_regression.jl` ergänzt:

| Feld | Inhalt |
|---|---|
| `pruned_support_terms` | die ausgedünnte Termmenge als Namen, je Gleichung — dieselbe Form wie `support_terms` |
| `exact_support_match_raw` | Bool: roher Support gleich wahrem Support; `nothing`, wenn kein wahrer Support existiert |
| `exact_support_match_pruned` | Bool: ausgedünnter Support gleich wahrem Support; `nothing` ebenso |
| `exact_support_match_definition` | fester Textwert, siehe Punkt 3 |

Den rohen Match berechnest du mit der **vorhandenen** `support_match`
(`studies/regression/diagnostic_systems.jl:171`), nicht mit einer neuen Implementierung.

**`pruned_match` bleibt unverändert bestehen**, gleicher Name, gleiche Bedeutung, gleiche Berechnung.
Die gesamte Phase-B-Auswertung hängt an diesem Namen. `exact_support_match_pruned` steht daneben und
muss im selben Record denselben Wert tragen.

### 3. Der Definitionsvermerk

Der Wert ist ein fester Text und wird vom bestehenden Python-Wächter
`analysis/utils/support_match_definition.py` erkannt. Dieser kennt die kanonischen Werte
`raw_support_terms_exact_match` und `pruned_support_terms_exact_match`.

Für den Phase-B-Pfad ist der korrekte Wert **`pruned_support_terms_exact_match`**, weil die
Registry-Spalte `exact_support_match` aus diesem Pfad aus `pruned_match` gefüllt wird. Lies den
Wächter, bevor du den Namen des Feldes und den Wert festlegst, damit beide Seiten zusammenpassen.

### 4. Nichtberechenbarkeit sauber führen

Für Surrogatsysteme existiert kein wahrer Support. Dort sind beide Match-Felder `nothing`, so wie
`pruned_match` es heute schon handhabt. `pruned_support_terms` ist dagegen **immer** berechenbar, weil
es nur Struktur und Koeffizienten braucht — es darf also auch bei Surrogaten nicht `nothing` sein.

## Verboten

- **Keinen langen Lauf starten.** Ein Smoke-Test auf einem kleinen System ist erlaubt.
- **Die Ausdünnungsschwelle nicht ändern.** Sie ist eingefroren; diese Aufgabe macht sie nur sichtbar.
- **`pruned_match` nicht umbenennen, nicht umdefinieren, nicht entfernen.**
- **`studies/regression/wp_n1_basis_probe.jl` nicht anfassen.** Dieses Skript rechnet **gerade jetzt**
  auf dem Cluster; jede Änderung würde die Identität des laufenden Datensatzes brechen.
- **`experiments/run_experiment.jl` nicht anfassen.** Der Phase-A-Pfad ist eingefroren.
- **Fingerprints und ihre Eingaben nicht anfassen:** `phase_b_fingerprint()`, `config_fingerprint()`,
  `stage_cap_behavior_fingerprint()`.

## Abnahme

Julia lässt sich hier nicht ausführen; melde `blocked`, Claude fährt die Abnahme.

Im Report brauche ich:

- wo die extrahierte Ausdünnungsregel jetzt liegt und welche Aufrufer sie benutzen,
- den gewählten Feldnamen und Wert des Definitionsvermerks, mit der Stelle im Python-Wächter, gegen
  die du ihn geprüft hast,
- die Liste der geänderten Dateien mit je einem Satz.

Claude prüft an einer realen Regressionszelle:

1. alle vier neuen Felder vorhanden und plausibel belegt,
2. `exact_support_match_pruned == pruned_match` im selben Record,
3. `pruned_support_terms` ist je Gleichung eine **Teilmenge** von `support_terms`,
4. alle übrigen Felder **bitgleich** gegen `HEAD`, insbesondere `loss`, `total_loss_evals`,
   `total_parameter_fits`, `total_ode_solves`, `r2`, `pruned_match`, `support_terms`,
5. die drei Fingerprints unverändert,
6. Tests grün.

Report nach `codex/reports/REPORT_WP_N12.md`.
