# WP-N38 — ODEFormer auf den C-6-Rauschdaten (R-09), zuerst auf den Stufenzellen
**Language: Python**

## Ziel

ODEFormer läuft auf **denselben exportierten Rausch-Trajektorien** wie EvoGrow, SINDy und
Weak-SINDy (Plan §9.4: ein Datensatz für alle Verfahren, Datenhash in jedem Record). Ausgewertet
wird gegen **saubere** Ziele, genau wie im SINDy-Rauschlauf (WP-N34). Vorerst laufen nur die
Stufenzellen. Das Raster entscheidet der Nutzer erst an Tor G.

Stufenzellen, alle mit IC 1 und Realisierung 1, je unter (σ 0,01; ρ 0) und (σ 0,05; ρ 0,5):

| System | Export-Index |
|---|---|
| 1 | `outputs/stage1/data_export/index.csv` |
| 17, 18, 24 | `outputs/stage2/data_export/index.csv` |
| 41 | `outputs/stage3/data_export/index.csv` |

Die Exporte enthalten zum Teil auch ρ = 0,5 bei σ 0,01 bzw. ρ 0 bei σ 0,05. Gerechnet werden
**alle Zeilen der Indizes**. Ausgewiesen werden die beiden Stufenbedingungen, die übrigen Zeilen
stehen getrennt daneben.

## Umsetzung

1. **Runner** `baselines/run_odeformer_noise.py`. Er liest einen oder mehrere Export-Indizes im
   Format, das `analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py` liest. Die
   Validierung und die Hash-Neuberechnung (`time_sha256`, `state_sha256`) übernimmst du von dort
   oder lagerst sie gemeinsam aus. Duplizieren ist nicht erlaubt.
2. **ODEFormer-Aufruf:** genau der Harness des Referenzrasters (`baselines/harness.py`,
   `baselines/run_odeformer_grid.py`). Dieselben vier Konfigurationen aus
   `baselines/configs/odeformer_grid.json` (beam 10/50 × opt/noopt), derselbe faithful-Modus mit
   ODEFormers eigenem 1-s-Integrationswächter und **drei Wiederholungen** wie im Referenzraster
   (ODEFormer ist nicht deterministisch, WP-N23/N24). ODEFormer bekommt nur das korrumpierte
   `(t, x)`. Unregelmäßige Raster (ρ = 0,5) gehen **mit ihrem echten Zeitvektor** hinein, ohne
   Interpolation. Was ODEFormer damit standardmäßig macht, wird aus dem Quelltext belegt und im
   Report zitiert. Scheitert eine Zelle, wird das als Fehler aufgezeichnet und nicht repariert.
3. **Saubere Auswertung** nach §9.4, identisch zu WP-N34: Rekonstruktion aus der sauberen
   Trainings-IC auf dem vollen sauberen 512er-Raster, Generalisierung aus der sauberen zweiten IC.
   R² arithmetisch und varianzgewichtet, Divergenzen/Nicht-Endliches als eigener Status.
   Strukturmetriken über die vorhandene kanonische Term-Expansion des Referenzrasters (roh und
   gepruned, wie dort), nur für exakte Systeme. Surrogate haben keinen Strukturtreffer.
4. **Ausgaben** unter `outputs/wp_n38_noise_odeformer/`: `details.csv` (eine Zeile je Zelle ×
   Konfiguration × Wiederholung, mit Datenhash, Gleichung, Status), `summary.csv` (je Zelle und
   Konfiguration: Median und Streuung über die Wiederholungen, Anteil R² > 0,9), `export_checks.csv`,
   und `comparison_with_robustness_stage_report.csv`, aufgebaut wie bei WP-N34. Dazu eine
   **gemeinsame Vergleichstabelle** je Stufenzelle: EvoGrow (Stufenberichte
   `outputs/phase_c_robustness_stage2_5dd1df8/robustness_stage_report/` und die lokalen Stufe-1/2-Berichte unter
   `outputs/stage{1,2}/*/report/`), SINDy/Weak-SINDy (`outputs/stage2/baselines/` und die WP-N34-Ausgabe) und
   ODEFormer. Spalten: beide Metriken (Struktur roh/gepruned, R² > 0,9 Rekonstruktion und
   Generalisierung, CLAUDE.md Design Principle 9) und Kosten als Zählgrößen, soweit vorhanden.
   Wo eine Quelle fehlt (System 41 ist noch nicht fertig), steht `missing`.
5. **Ausführungsumgebung:** Der Runner muss im **ODEFormer-Referenz-Image** laufen
   (`registry.gitlab.scch.at:443/joedicke/evoode/odeformer-reference:55e9c75…`, dasselbe wie im
   Referenzraster), und zwar mit dem Repo als Volume gemountet. So bleibt die Umgebung identisch,
   ohne dass ein neues Image gebaut werden muss. Schreib den genauen `docker run`-Befehl in den Report:
   ein Prozess, eine CPU, Thread-Variablen wie in `SCRIPTS.md` „ODEFormer-Raster auf Orion“. Prüfe,
   ob der Image-Einstiegspunkt oder der `PYTHONPATH` den gemounteten Code statt des eingebauten
   verwendet, und lass den Runner die effektive Code-Herkunft (Pfad, git-Hash des Mounts)
   in jeden Record schreiben.
6. **Kontrolle:** Derselbe Runner auf einer **sauberen** Zelle, System 1 IC 1 aus dem
   C-4/Referenzraster-Export (`outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export` oder
   wo das Referenzraster gelesen hat), muss dieselben Gleichungen und R²-Werte liefern wie das
   Referenzraster für dieselbe Zelle und Konfiguration. Wegen des Nicht-Determinismus gilt der
   Maßstab aus WP-N24 (`baselines/compare_odeformer_equivalence.py`). Das ist die harte Abnahme
   im Docker-Lauf.

## Verboten

ODEFormer-Konfigurationen, Beam-Größen, den Integrationswächter oder Wiederholungszahlen ändern
oder auswählen. Interpolieren. `src/`, Julia-Code, die bestehenden Referenzraster-Skripte im
Verhalten ändern (Refactoring nur, wenn das Referenzraster bit-gleich bleibt, mit Test). Neue
Images bauen. Git. `oc`. `codex/CURRENT_TASK.md` bearbeiten. **Kein lokaler ODEFormer-Lauf
außerhalb eines Smoke-Tests von höchstens einer Zelle und einer Konfiguration.** Den vollen
Stufenlauf startet Claude.

## Abnahme

- Tests unter `baselines/tests/` für Indexvalidierung, Hash-Prüfung, die saubere Auswertung
  (Rekonstruktion gegen Wahrheit ergibt bei der wahren Gleichung R² = 1) und den Vergleichs-Join.
- Report `codex/reports/REPORT_WP_N38.md` mit den Befehlen für Claude: Image-Pull, Kontrolle,
  voller Stufenlauf, Vergleichstabelle. Jeweils mit Zweck, erwarteter Dauer und Pass-Kriterium.
- `STATUS.md` nach Protokoll. Ist ohne Docker nur der Code fertig, ist der Status `done`, und der
  Report sagt, was offen ist.
