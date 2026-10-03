# WP-N42 — C-6-Raster vorbereiten: Manifest (r ↔ Seed r), Kappen-Vorprüfung, Datenexport, Orion-Job
**Language: Julia** (plus YAML und ein kleines Python-Hilfsskript, wo es passt)

## Grundlage

Tor G ist entschieden, siehe `docs/paper1_phaseC_benchmark_plan.md` **§9.4c** (bitte zuerst lesen),
außerdem §9.4 und §9.4b. Kurz:

- EvoGrow, kanonischer gekappter Arm (`evogrow_v2_2_stage_capped`, `pretuning=false`, wie C-1), auf
  den **51 dim-1/2-Systemen**, Seeds wie C-1 (`PHASE_C_SEEDS`), beide IC-Sets, `clamp_val = 10`.
- **11 Bedingungen:** σ ∈ {0, 0.01, 0.02, 0.03, 0.04, 0.05} × ρ ∈ {0, 0.5} ohne (0, 0) → 3.366 Zellen.
- **Realisierung r ↔ Seed-Index r:** Der r-te Seed in `PHASE_C_SEEDS` sieht Realisierung r (1, 2, 3).
  Der Rauschstrom hängt nur von (System, IC, σ, ρ, r) ab, so wie es `apply_phase_c_data_condition`
  heute schon macht. Prüfen und zitieren.
- **Ungekappter Arm** (`evogrow_v2_2_stage_local`) nur für Zellen, deren suchfreie Kappe
  (`print_phase_c_stage_caps.jl`) in mindestens einer Gleichung endlich und < 5 ist.

## Umsetzung

1. **Manifest-Generator:** `generate_phase_c_manifest.jl` bekommt einen Modus für das Raster, z. B.
   `--c6-grid`. Er schreibt alle 3.366 gekappten Zeilen mit der Kopplung r ↔ Seed-Index und den
   üblichen Spalten (inkl. `noise_sigma`, `subsample_rho`, `noise_realization`, `clamp_val`). Die
   bisherigen Aufrufe bleiben **byte-identisch** (Test, insbesondere C-1/C-2 und die Stufen).
   Sortierung wie bei C-1: teure Zellen zuerst, damit lange Zellen früh starten. Die
   Kostenreihenfolge aus C-1 wiederverwenden (`indices_cost_desc`).
2. **Kappen-Vorprüfung im Massenbetrieb:** `print_phase_c_stage_caps.jl` (oder ein Wrapper) über
   alle 3.366 Zeilen, Ausgabe als CSV (Index, System, IC, Seed, σ, ρ, r, `stage_caps`, `has_finite_cap_lt5`).
   Daraus ein **zweites Manifest** für den ungekappten Arm: dieselben Zeilen mit
   `variant = evogrow_v2_2_stage_local`, `condition = uncapped`, nur wo `has_finite_cap_lt5`.
3. **Datenexport für die Baselines:** Ein Befehl, der mit `export_phase_c_data_conditions.jl` alle
   **63** Systeme × 2 IC × 12 Bedingungen (inkl. (0,0)) × 3 Realisierungen exportiert, mit
   Index-CSV wie bei den Stufen. Den Befehl in den Report schreiben, nicht ausführen.
   Platzbedarf vorab abschätzen und angeben (Platte C: muss über 30 GB frei bleiben).
4. **Orion-Job** `k8s/phase_c_c6_grid_job.yaml`: Muster wie `phase_c_c1_c2_campaign_job.yaml` bzw.
   die Stufen-Jobs. Indizierter Lauf über das gekappte Manifest und ein zweiter Job für das
   ungekappte. **Kein Bootstrap im Cluster**: Die Manifeste erzeugt Claude lokal und legt sie aufs
   NFS (so wie bei B-05), damit das Image `5dd1df8` reicht. `parallelism` als Platzhalter
   `<PARALLELISM>`, Claude setzt ihn nach Rücksprache. Kein `activeDeadlineSeconds`. Kopfkommentar mit
   Kostenmodell (Plan §9.4c: 25,4–35,1 Tsd. Kernstunden) und dem Hinweis, dass Zellen über 24 h ohne
   Cut laufen.
5. **Lokale Kontrolle:** Eine Zeile des Rastermanifests (System 1, IC 1, Seed-Index 1, σ 0,01, ρ 0)
   muss inhaltlich der Stufe-1-Zelle entsprechen (`outputs/stage1/s0.01_r0/manifest.csv`, Zeile 1,
   Realisierung 1). Ein Test prüft, dass Datenhash und Fingerprint gleich sind. Den Befehl für Claude
   in den Report.
6. `SCRIPTS.md`: Abschnitt C-6-Raster (Manifeste erzeugen, Vorprüfung, Upload aufs NFS, Apply,
   Fortschritt, Einsammeln).

## Verboten

`src/`, Such- oder Fitpfad, Policy, Konstanten ändern. Bestehende Manifeste ändern. Läufe über einen
Smoke hinaus. `activeDeadlineSeconds`/`timeout`. Git, `oc`, `codex/CURRENT_TASK.md` bearbeiten.

## Abnahme

Code und Tests geschrieben. Report `codex/reports/REPORT_WP_N42.md` mit allen Befehlen für Claude:
Manifest erzeugen, Vorprüfung, Kontrolle, Export, Upload. Jeweils mit Zweck, Dauer und
Pass-Kriterium. `STATUS.md` nach Protokoll.
