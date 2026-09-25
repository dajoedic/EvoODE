# WP-N25 — Die abgeleiteten C-5-Arme für Phase C lauffähig machen
**Language: Julia**

## Ausführung

Codex kann in dieser Umgebung kein Julia ausführen (`codex/CODEX_PROTOCOL.md`). Code und Tests
schreiben, dann mit `status: blocked` und dem Grund "Julia-Ausführung" melden; Claude führt Tests
und Rauchtest aus. **Nichts starten, was länger als 15 Minuten läuft.** Die eigentlichen C-5-Läufe
startet niemand in diesem Paket.

## Ausgangslage

Der C-5-Arm des Phase-C-Plans (`docs/paper1_phaseC_benchmark_plan.md`, §1a/§1b und §2) besteht aus
drei Skripten, die **keine neue Suche** machen, sondern die C-1-Records nachnutzen:

| Claim | Skript | Was es tut |
|---|---|---|
| Diag | `studies/regression/wp_n3_oracle_refit.jl` | Fit auf der wahren Struktur (`reference`) und auf gefundene ∩ wahre Terme (`oracle`) |
| Abl-3 | `studies/regression/wp_n4_multistart_refit.jl` | dasselbe mit k Parameterstarts, Kurve über k ∈ {1, 2, 3, 5, 10} |
| C | `studies/regression/wp_n5_ic_generalization.jl` | gespeichertes Modell von der ungesehenen Anfangsbedingung aus integrieren, beide Richtungen |

Alle drei sind für den WP-N1-Probe gebaut und passen an vier Stellen **nicht** zu Phase C:

1. **Systeme und Trajektorien.** Sie laden `phase_b_config.jl` und bauen Systeme aus
   `PHASE_B_SYSTEMS` mit `build_trajectory(system, ic_set)`. Phase C hat einen eigenen Pfad:
   `phase_c_systems()` in `studies/regression/phase_c_config.jl`, mit eigener
   Trajektorienerzeugung (`_phase_c_solution_trajectory`). Ob beide Pfade dieselben Zahlen liefern,
   ist nicht gezeigt, und das darf auch nicht vorausgesetzt werden.
2. **Wahrheit.** Sie lesen die wahre Struktur aus dem Record-Feld `wp_n1_expected_support_terms`.
   Das Feld gibt es in Phase-C-Records nicht. Die Phase-C-Wahrheit steht in
   `studies/regression/phase_c_support.json` (Lader: `load_phase_c_support()`), 30 exakt, 33
   Surrogat, Basis `staged_polynomial_basis_with_constant`.
3. **Eingabe.** Die Standardeingabe ist `outputs/wp_n1_dim1_probe/history.jsonl`. Die Phase-C-Records
   liegen als Einzeldateien pro Zelle vor und werden mit `studies/regression/merge_batch_records.jl`
   zu einer History zusammengeführt. Diese History enthält **drei Arme**: C-1 (gekappt,
   `use_pretuning = false`), C-2 (`evogrow_v2_2_stage_local`) und C-3 (gekappt, `use_pretuning = true`).
   C-5 gilt laut Plan **nur für C-1**.
4. **Laufzeit.** Der Plan nennt "< 50 Kernstunden" für C-5 zusammen. Das ist eine Schätzung, keine
   Messung. Abl-3 rechnet mit k = 10 zwei Fits pro Start über alle exakten C-1-Zellen, dim 3
   eingeschlossen. Nach `CLAUDE.md` läuft alles auf Orion, was nicht nachweislich unter 8 h
   bleibt. Dafür braucht es eine hergeleitete obere Schranke und eine Aufteilung in Shards.

Ein Phase-C-Record hat 93 Felder, darunter `basis_name`, `model_terms` (mit `term_index` und
`coefficient`), `u0`, `T`, `tspan`, `seed`, `initial_condition_set`, `system_id`, `variant`,
`use_pretuning`, `condition`, `representability`, `max_fit_attempts`, `git_hash`,
`config_fingerprint`, `stage_cap_behavior_fingerprint`, `total_parameter_fits`, `total_loss_evals`,
`total_parameter_optimization_time_s`. Beispiel: jede Datei `cell_*.jsonl` (ohne `.heartbeat`) unter
`outputs/phase_c_dryrun_2026-09-25/tasks/`, einer lokalen Kopie des Kampagnenstands vom 25.09.

## Was zu tun ist

1. **Phase-C-Modus für alle drei Skripte**, ausgewählt über ein explizites Argument
   (z. B. `--campaign paper1_phaseC_v1`). **Ohne das Argument bleibt das bisherige WP-N1-Verhalten
   bitgleich.** Das ist die Abnahme 1.
2. **Systeme und Trajektorien im Phase-C-Modus ausschließlich über `phase_c_systems()`**, also über
   denselben Pfad, den der Kampagnen-Runner benutzt hat. Jede Ausgabezeile trägt einen
   Trajektorien-Hash im Format von `studies/regression/phase_c_trajectory_hashes.jl`
   (`HASH_FORMAT`, gleiche Achsenordnung). Wo es einen Quell- und einen Ziel-IC gibt (WP-N5), zwei
   Hashes. Damit lässt sich die Identität zu den Trajektorien der Kampagne **per Hash** prüfen statt
   behaupten.
3. **Wahrheit im Phase-C-Modus aus `phase_c_support.json`.** Abbruch, wenn der `basis_name` im
   Record nicht mit dem `basis_name` der Support-Tabelle übereinstimmt. Surrogat-Systeme haben keine
   wahre Struktur: WP-N3 und WP-N4 überspringen sie **mit Zählung im Manifest**, WP-N5 braucht keine
   Wahrheit und rechnet alle 63 Systeme.
4. **Nur C-1.** Im Phase-C-Modus werden genau die Records mit `variant ==
   "evogrow_v2_2_stage_capped"` und `use_pretuning == false` verarbeitet. Alle anderen werden
   **gezählt und im Manifest ausgewiesen, nicht stillschweigend verworfen**. Abbruch, wenn die
   ausgewählten Records mehr als ein Identitätstripel tragen (`git_hash`, `config_fingerprint`,
   `stage_cap_behavior_fingerprint`), oder wenn eine Zelle (System, Seed, IC-Set) doppelt vorkommt.
5. **Optimierer im Phase-C-Modus = Phase-C-Konfiguration**, also die Konstanten, die in
   `phase_c_fingerprint()` eingehen, inklusive `BFGS_MAX_LOSS_EVALS` als Budget pro Fit. Damit ist
   jeder Fit per Konstruktion begrenzt. Zur Restart-Regel:
   - **WP-N3 (Diag)** fittet mit `max_fit_attempts = 3`, so wie die Kampagne. Die Diagnose misst,
     was der kanonische Optimierer auf der wahren Struktur schafft.
   - **WP-N4 (Abl-3)** macht jeden seiner k Starts als **einen** Versuch
     (`max_fit_attempts = 1`), weil das Skript k selbst variiert. Andernfalls würden sich zwei
     Mehrfachstart-Mechanismen überlagern.
   - Beide Festlegungen stehen im Manifest und im Fingerprint des jeweiligen Skripts.
6. **Aufteilung in Shards und Wiederaufnahme** für alle drei Skripte: `--shards N --shard-index i`
   teilt die ausgewählten Zellen deterministisch auf, sortiert nach dem Zellschlüssel und nicht nach
   Dateireihenfolge. Jeder Shard schreibt in eigene Dateien, die kein anderer Shard anfasst. Ein
   Neustart überspringt fertige Zellen. `--collect` führt die Shards zusammen und bricht ab, wenn
   eine Zelle fehlt oder doppelt ist. Die bestehenden Ausgabedateien (`cells.csv`,
   `metric_summary.csv` usw.) entstehen erst in `--collect` bzw. im Ein-Shard-Fall.
7. **Kostenschranke vor dem Lauf:** `--estimate-cost` rechnet nichts, sondern leitet aus den
   Eingabe-Records eine obere Schranke pro Zelle her:
   Anzahl Fits der Zelle × `BFGS_MAX_LOSS_EVALS` × gemessene Zeit pro Loss-Evaluation derselben
   Zelle in der Kampagne (`total_parameter_optimization_time_s / total_loss_evals`). Die Anzahl Fits
   pro Zelle ist bei WP-N3 2 × 3 Versuche, bei WP-N4 2 × k_max, bei WP-N5 null Fits und zwei
   Integrationen. Ausgabe: Schranke pro Zelle, Summe und Maximum pro Dimension, Gesamtsumme, teuerste
   Zelle. In der Ausgabe als **Planungsgröße** kennzeichnen, nicht als Evidenz (Designprinzip 7).
   Aus dieser Zahl wird entschieden, ob ein Lauf auf den Laptop darf.
8. **Rekonstruktionskontrolle in WP-N5 unverändert:** Das Modell wird vom **Trainings**-IC aus
   integriert und muss den gespeicherten Loss exakt treffen. Im Phase-C-Modus zählt das Manifest
   Treffer und Abweichungen. Eine Abweichung ungleich null wird pro Zelle ausgewiesen und nicht
   geglättet.
9. **Runbook:** In `SCRIPTS.md` fehlt die Phase-C-Auswertungskette ganz. Einen Abschnitt ergänzen,
   der der Reihe nach nennt: `merge_batch_records.jl` → `convert_campaign_history_to_run_registry.py`
   → `verify_campaign_registry.py --campaign paper1_phaseC_v1` → Strukturmetriken, Dreiwege-
   Repräsentierbarkeit, Cap-Ablation, Pretuning-Collapse, SINDy-Paarung → die drei C-5-Skripte im
   Phase-C-Modus, jeweils mit `--estimate-cost`, Shard-Aufruf und `--collect`. Nur Befehle und
   Zweck. Wo ein Argument unklar ist, `TODO(Claude)` statt zu raten.

## Verboten

- Keine Git-Operationen.
- **Nichts ändern, was in `phase_c_fingerprint()`, `stage_cap_behavior_fingerprint()` oder den
  Kampagnen-Runner eingeht**: `phase_c_config.jl`, `run_regression.jl`, `run_k8s_indexed_cell.jl`,
  `src/`. Die Kampagne läuft noch mit diesem Stand. Wenn ein Helfer von dort gebraucht wird, wird er
  aufgerufen, nicht verändert. Ist das unmöglich, `blocked` melden und nicht umbauen.
- Keine k8s-Manifeste in diesem Paket. Ob es welche braucht, entscheidet die Schranke aus Punkt 7.
- Nichts unter `analysis/data/` oder `experiments/` schreiben.
- Keine Trajektorien über `PHASE_B_SYSTEMS` im Phase-C-Modus, auch nicht als Rückfall.

## Abnahme (Claude führt aus)

1. **WP-N1-Verhalten bitgleich:** Jedes der drei Skripte liefert ohne `--campaign` auf
   `outputs/wp_n1_dim1_probe/history.jsonl` mit `--limit 4` dieselben `results.jsonl`-Zeilen wie
   der Stand vor dem Paket. Den genauen Befehl für den Vorher/Nachher-Vergleich in den Report
   schreiben.
2. **Hash-Identität:** Für eine dim-1- und eine dim-3-Zelle stimmen die Trajektorien-Hashes aus
   Punkt 2 mit `phase_c_trajectory_hashes.jl` für dasselbe System und denselben IC überein.
3. **Rauchtest im Phase-C-Modus** auf `outputs/phase_c_dryrun_2026-09-25/`: je Skript eine dim-1-
   Zelle über `--limit` bzw. einen Shard mit einer Zelle, dann `--collect`. WP-N5 meldet für diese
   Zelle Rekonstruktionsabweichung null.
4. `--estimate-cost` läuft für alle drei Skripte auf der zusammengeführten History und gibt die
   Tabelle aus Punkt 7 aus.
5. Neue Julia-Tests (pro Datei ausführbar, es gibt kein `runtests.jl`) für: Armfilter und
   Zählung, Abbruch bei gemischten Identitätstripeln, Abbruch bei doppelter Zelle, deterministische
   Shard-Aufteilung, `--collect` bricht bei fehlender Zelle ab, Basisabgleich mit der Support-Tabelle.
6. Report `codex/reports/REPORT_WP_N25.md` mit geänderten Dateien, neuen Argumenten, allen
   Befehlen für Abnahme 1–5 und einer Liste, **was nicht verifiziert** werden konnte.
