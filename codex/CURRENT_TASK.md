# WP-N37 — Stufe 3 (System 41), B-03 (Grenzen-Orakel dim 3/4), Kappen-Vorabprüfung, §9.6-Auswertung
**Language: Julia** (Teile B und C sind Python)

Der Nutzer hat am 2026-10-02 die Tore S2 und B2 geöffnet. Dieses Paket baut alles, was für die
nächsten beiden Orion-Läufe und ihre Auswertung fehlt. Es besteht aus vier unabhängigen Teilen.
Grundlage: `docs/paper1_phaseC_benchmark_plan.md` §9.4a (Stufe 3), §9.4b (ungekappter Arm) und §9.6
(C-8). **Es gibt keine harten Zeit-Cuts:** kein `activeDeadlineSeconds`, kein `timeout`. Stattdessen
steht in jedem Manifestkopf die erwartete Laufzeit.

## Teil A — Manifest Stufe 3: System 41, gekappt

Neue Datei `k8s/phase_c_robustness_stage3_orion_job.yaml`. Vorlage ist
`k8s/phase_c_robustness_stage2_orion_job.yaml` (Bootstrap, Smoke, indizierter Lauf). Unterschiede:

- `--stage2-systems 41` statt `18,24`. Es bleiben beide Bedingungen (0,01; 0) und (0,05; 0,5), Seed
  42, IC 1, Realisierung 1, `clamp_val 10`. Das ergibt **2 Zellen** plus den Smoke auf System 1.
- Eigene Job-Namen, Labels (`…-robustness-stage3…`) und eigene Ausgabebasis
  `/outputs/phase_c_robustness_stage3_<COMMIT_SHA>`. Nichts darf mit Stufe 2 kollidieren.
- Kopfkommentar: Zweck, Backlog R-06, erwartete Laufzeit. Der C-1-Zelle von System 41 (Seed 42,
  IC 1) lief 24 von 30 Leveln, 6,53 M Loss-Evals, 11,3 h. In Stufe 2 lag der Rauschfaktor bei
  0,7–1,0, wo C-1 schon viele Level lief (System 18), und bei 13,7, wo C-1 nach 2 Leveln stoppte
  (System 24). Erwartet sind deshalb **etwa 8–17 h je Zelle**. Claude meldet sich beim Nutzer, wenn
  eine Zelle deutlich über 24 h kommt.

Dazu eine zweite, **getrennte** Datei `k8s/phase_c_robustness_stage3_uncapped_job.yaml`: derselbe
Aufbau, aber über `select_phase_c_stage2_manifest.jl --variant evogrow_v2_2_stage_local
--condition uncapped`. Eigene Job-Namen und eigene Ausgabebasis
`/outputs/phase_c_robustness_stage3_uncapped_<COMMIT_SHA>`, kein Smoke nötig. Sie wird **nur**
angewendet, wenn Teil D für System 41 unter Rauschen eine endliche Kappe < 5 zeigt. Das steht im
Kopfkommentar, mit Verweis auf `DIARY.md` 2026-10-02 (ohne endliche Kappe ist der Arm per
Konstruktion identisch).

Falls `select_phase_c_stage2_manifest.jl` dafür eine Änderung braucht: Sie muss für die
Stufe-2-Aufrufe ein byte-identisches Ergebnis liefern.

## Teil B — B-03: Eingabe und Manifest

1. `analysis/scripts/aggregate/prepare_phasec_b02_oracle_input.py` bekommt eine Option für die
   Dimensionen, zum Beispiel `--dims 3,4`. **Der Standard bleibt dim ≤ 2 und muss byte-identisch zu
   heute bleiben.** Prüfung: Ein Lauf ohne die neue Option ergibt dieselbe SHA-256 wie
   `outputs/phase_c_c8_oracle_b02_input/history.jsonl`. Die erwartete Systemzahl hängt an der Wahl:
   21 für dim ≤ 2, **9 für dim 3/4** (52, 54, 55, 56, 57, 58, 59, 61, 63, Quelle `phase_c_support.json`).
   Bei dim 3/4 sind es 54 Records (9 × 3 Seeds × 2 IC). Die Prüfung bleibt hart.
2. Neue Datei `k8s/phase_c_c8_oracle_b03_job.yaml`: Vorlage `k8s/phase_c_c8_oracle_b02_job.yaml`,
   drei Jobs für die Grenzen 10 / 1000 / Inf, Eingabe `/outputs/phase_c_c8_oracle_b03_<COMMIT_SHA>/input/history.jsonl`,
   Ausgabe `…/bound_<b>`, **18 Shards je Grenze**. Eigene Namen und Labels. Kopfkommentar mit
   Zweck (Backlog B-03, Tor B3) und dem Platzhalter `Expected runtime: TODO(Claude) from --estimate-cost`.
   Claude trägt den Wert nach der Kostenschätzung ein.
3. `SCRIPTS.md`: einen Abschnitt für Stufe 3 und B-03 mit Vorbereitung, Apply, Fortschritt und
   Einsammeln. **Neu:** Eingesammelt wird direkt vom lokal gemounteten NFS
   (`S:\BigDataOrion\data-science\joedicke\…`, in Git Bash `/s/BigDataOrion/…`). Auch der Upload
   der Eingabe kann dorthin kopiert werden, statt per `oc cp`.

## Teil C — Auswertungsskript für §9.6

Neues Skript `analysis/scripts/aggregate/aggregate_c8_oracle_bounds.py` mit Test unter
`analysis/tests/`. Konventionen: `analysis/CONVENTIONS.md`.

Eingabe: ein oder mehrere Verzeichnisse je Grenze mit `shard_*/results.jsonl` (B-02 und später
B-03, auch beide zusammen), dazu die C-5-Referenz `outputs/wp_n3_oracle_refit_phase_c/`. Ausgabe in
ein eigenes Verzeichnis, als CSV und als Markdown:

1. **Kontrolle:** Grenze 10 gegen C-5 je `cell_key`. Verglichen werden `reference_loss`,
   `reference_coefficients`, `reference_r2` und `reference_fit_meta.loss_evals`, verlangt ist
   Gleichheit. Jede Abweichung bricht ab (Exit ≠ 0).
2. **Stabilitätskriterien wörtlich nach §9.6**, je Grenze, auf `reference_fit_meta`:
   - harter Fehler: `result_valid == false` oder ein nicht endlicher `reference_loss`;
   - Strafe: `reference_loss >= 1e6`;
   - Aufwand: Median und q95 von `loss_evals`.

   Dazu die Deltas gegen Grenze 10 mit den Schwellen 2 Pp, 5 Pp und 1,5 sowie der Befund
   „vergleichbar stabil: ja/nein“. Ausgewertet wird auf der **Gate-Menge**: die Systeme, die unter
   allen drei Grenzen machbar sind, also alle exakten Systeme außer 54–59. Die Klassifikation kommt
   aus den vorhandenen Daten (`phase_c_support.json` oder die Kennzeichnung im C-5-Orakel), nicht
   aus einer fest kodierten Liste. Ist die Gate-Menge unvollständig (nur B-02 da), steht das
   sichtbar im Kopf: „vorläufig, n = 126 von 144“. 54–59 werden getrennt berichtet.
3. **Berichtet, aber nicht als Tor:** Anteil der Fits mit `diverged_solves > 0` oder
   `nonfinite_solves > 0`, R² > 0,9 (beide Aggregationen, falls beide Felder im Record stehen;
   sonst nur die vorhandene und ein Hinweis), Struktur-Treffer, Retry-Rate. Dazu je System und
   je Zelle die Änderung gegen Grenze 10: geänderte Fits, Loss besser/schlechter, R²-Kippungen.

**Abnahme Teil C auf den B-02-Daten** (`outputs/phase_c_c8_oracle_b02_5dd1df8/bound_{10,1000,Inf}`):
Die Kontrolle besteht 126/126. Harte Fehler 0/0/0, Strafen 2/2/2, Median `loss_evals`
743,5 / 1093 / 1197, R² > 0,9 (über `reference_r2`) 72 / 83 / 83, geänderte Fits gegen Grenze 10
86 / 86. Befund: 1000 vergleichbar stabil, Inf nicht (Verhältnis 1,61). Diese Zahlen hat Claude
vorab mit einem Wegwerf-Skript ermittelt. Wenn dein Skript davon abweicht, nicht anpassen, sondern
im Report begründen.

## Teil D — suchfreie Kappen-Vorabprüfung

Neues Skript `studies/regression/print_phase_c_stage_caps.jl`. Es nimmt eine Phase-C-Manifest-CSV
und Zeilenindizes. Je Zeile baut es **exakt die Daten, die `run_batch_cell.jl` bekäme**: dieselbe
Funktionskette, Rauschen und Ausdünnung über `apply_phase_c_data_condition`, dieselbe Basis und
dieselben Kappen-Einstellungen. Darauf ruft es dieselbe Kappenschätzung auf wie der Suchpfad. Es
gibt `system_id`, Bedingung und `stage_caps` aus. Keine Suche, kein Fit. Wiederverwenden statt
nachbauen, und keine Änderung an `src/`.

Abnahme (führt Claude aus, siehe unten):
- Stufe-2-Zeilen (`outputs/stage2/s0.01_r0/manifest.csv` und `…/s0.05_r0.5/manifest.csv`, Systeme
  17, 18, 24): alle `nothing`, wie in den Records.
- Saubere C-1-Zeilen für System 17, 18 und 24 (Seed 42, IC 1): `[2]`, `[4]`, `[nothing, nothing]`.

## Verboten

`src/` ändern. Den Kampagnen-, Such- oder Fitpfad ändern. Kontrollen abschwächen. Bestehende
Manifeste ändern. `activeDeadlineSeconds` oder `timeout` irgendwo einfügen. Julia-Läufe über einen
Smoke hinaus. Git. `codex/CURRENT_TASK.md` bearbeiten. Kein `oc`, kein Push.

## Abnahme gesamt

- Teil B.1: Die Byte-Identität für dim ≤ 2 ist geprüft (Python, das kannst du selbst), und die
  dim-3/4-Eingabe mit 54 Records ist erzeugt unter `outputs/phase_c_c8_oracle_b03_input/history.jsonl`.
- Teil C: Test grün, B-02-Zahlen wie oben oder begründete Abweichung.
- Report `codex/reports/REPORT_WP_N37.md` mit den Befehlen, die Claude ausführen soll (Teil D, die
  Kostenschätzung für B-03 und gegebenenfalls ein Smoke von Teil A), je mit Zweck, Dauer und
  Pass-Kriterium.
- `STATUS.md` nach Protokoll. Wegen Julia vermutlich `blocked` (*Umgebung, nicht Sache*), wenn alles
  andere fertig ist.
