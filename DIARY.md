# EvoODE — Projekt-Tagebuch

Neueste Einträge zuerst. Aktueller Projektzustand: siehe `CLAUDE.md`.

---

## 2026-07-20

### WP-v3.2 umgesetzt und verifiziert

Codex hat `EvoGrowV3` implementiert (`src/structure/evogrow_v3.jl`, registriert/exportiert in `src/EvoODE.jl`). Pro-Gleichung-Stage-State (`eq_stages`, `eq_levels_in_stage`, `eq_plateau_histories`, `eq_stage_histories`), Promotion aber noch Lockstep-global über einen internen `EvoGrow`-Bridge, der die v2.2-Helfer (`_validate_policy`, `_init_population`, `_stage_progression_decision`) wiederverwendet. Meta ergänzt `eq_final_stages` + `eq_stage_histories` mit `final_stage = maximum(eq_stages)`. Saubere Seams (`_lockstep_stage_progression_decision`, `_apply_lockstep_stage_update!`) für WP-v3.4.

**Regressions-Äquivalenz selbst verifiziert** (Julia-Skript, System 3 1D + System 26 2D, Seeds 42/7): identische `active_idxs`, Loss-Differenz bit-genau 0.0, `eq_final_stages` lockstep-gleich, `maximum(eq)==final_stage`. v3.2 reproduziert v2.2 (`:stage_local`) exakt — der Refactor ist neutral. Nebenbefund als Baseline: v3.2 scheitert auf System 26 genau wie v2.2 (Loss ~0.038, nur lineare Terme), was WP-v3.4 heilen soll.

Anmerkung Tech-Debt: Die ~350-Zeilen-Hauptschleife ist eine Kopie des v2.2-Loops (unvermeidbar unter „evogrow.jl nicht anfassen"). Nach Gate 2 faktorisieren oder v2.2-Loop stilllegen.

<!-- 559d3b7 -->

### WP-v3.1 geliefert, WP-v3.2 beauftragt

Codex hat **WP-v3.1** umgesetzt: `docs/evogrow_v3_design.md` friert das v3-Design ein — pro-Gleichung-Stage-State (`eq_stages` statt globalem `current_stage`), Ableitungs-Residuum `r_k` als pro-Gleichung-Progress-Signal (auf beobachteter Trajektorie), Promotion-Regel mit Residuum-über-Ziel-Guard (bereits erklärte Gleichungen promoten nicht), gleichungs-bewusste Child-Generation, Warm-Start-Übernahme, neue pro-Gleichung-Metriken. Vier offene Fragen mit empfohlenen Auflösungen. Committet.

**WP-v3.2 als nächsten Codex-Task formuliert** (`codex/CURRENT_TASK.md`): neuer `EvoGrowV3`-Struct + gleichungsweiser Stage-State als lauffähiges Refactor. Bewusst enger Scope — Promotion bleibt vorerst Lockstep (alle Gleichungen gemeinsam), sodass `EvoGrowV3` v2.2 (`:stage_local`) exakt reproduziert. Das dient als **Regressions-Anker**: spätere Divergenz ist dann eindeutig den gleichungs-lokalen Mechanismen (WP-v3.3 Child-Generation, WP-v3.4 Residuum-Signal + pro-Gleichung-Promotion) zuzuordnen, nicht dem Refactor. Verifikation: Struktur-/Loss-Identität v3 vs. v2.2 auf System 3 und 26.

<!-- f9567b5, 10ef90f, 4f78d20 -->

### Status-Abgleich und Housekeeping

Statusprüfung der vier offenen Punkte aus den „Current Priorities". Ergebnis: CLAUDE.md war veraltet (Stand 2026-05-11), `PAPER_1.md` ist die aktuelle Wahrheit.

- **WP-0.1** (H4-Verdict → VACUOUS in `evaluate_hypotheses.py`): bereits erledigt, Commit `a199128` (2026-05-17). Die `vacuous`-Prüfung setzt das Verdict korrekt, das Freeze Memo schreibt „C3 cannot be evaluated".
- **WP-0.2** (Generalization-Pfad): bereits erledigt (2026-05-17). Config zeigt korrekt auf `debug_results/generalization_summary.csv`.
- **WP-v3.1** (Design Note `docs/evogrow_v3_design.md`): aktiver Codex-Task in `codex/CURRENT_TASK.md`, Deliverable noch nicht geschrieben. Das ist der reale aktuelle Arbeitspunkt.
- **Phase B**: nicht begonnen, erst nach Gate 2.

**CLAUDE.md synchronisiert:** „Current Priorities" und „Active WPs" auf Phase 2 / WP-v3.1 aktualisiert, erledigte WPs markiert. Fehl-Label korrigiert: der frühere „Phase 2"-Prioritätspunkt (R²/Protocol-Audit) ist laut `PAPER_1.md` eigentlich Phase 3.

**Untracked Runner committet:** `studies/phase1_diag/run_phase1_diag.jl` (WP-1.3-Diagnostik, Gate-1-Evidenz) war nie eingecheckt — jetzt nachgeholt.

<!-- 7f29a02, eae3e2c, e819afb -->

---

## 2026-05-30

### WP-1.3 Ergebnisse und Gate-1-Entscheidung

Phase-1-Diagnostik-Runs abgeschlossen: 15/15 JSON-Dateien in `outputs/studies/phase1_diag/`. Konfiguration: EvoGrow v2.2 stage_local, `use_pretuning=false`, `n_levels=30`, 3 Seeds je System.

**Kontrollsysteme:**

- System 3 (Logistic): `pruned_match=true` alle 3 Seeds, Loss ~7e-10. Stage-Overshoot 0–3 (Mindestbudget-Effekt). Fit-Qualität gut, kein Strukturproblem.
- System 11 (Cubic `du=-u³`): `pruned_match=true` alle 3 Seeds, Loss ~4e-15, Stage 4/4, Laufzeit ~1.3s. Metrik-Artefakt aus WP-1.2 vollständig geheilt — der Pruning-Fix funktioniert.

**Problemsysteme:**

- System 26 (Lotka-Volterra 2D): `pruned_match=false` alle 3 Seeds, Loss ~5e-4–1.4e-3, Stage 5/3, Laufzeit 2800–9400s. Gefundene Struktur: `du1 = (5.05)*u1 + (-3.87)*u1*u2`, `du2 = (1.13)*u1 + (-1.80)*u1^2` — Terme komplett falsch. Loss platzt in Stage 3 auf ~1e-3, danach keine Verbesserung trotz Eskalation bis Stage 5 (Trig-Terme nutzlos).
- System 31 (SIR 2D): Seed 42 erreicht Loss ~7e-11 (nahezu perfekt), aber `pruned_match=false` wegen Spurious-Term `0.0022*u1` — Pruning-Schwellenwert `1e-3 × max_coeff = 4e-4 < 0.0022`, Term überlebt. Seeds 123/7: Stage 5/3, Loss ~1e-4–7e-5, echter Fehler.
- System 63 (SEIR 4D): `pruned_match=false` alle 3 Seeds, Loss ~9e-4–1.8e-3, Stage 5/3, Laufzeit 11000–31000s. Konsistentes Scheitern.

**Strukturdiagnose:** Der systemweite Staging-Mechanismus von v2.2 zwingt alle Gleichungen gemeinsam in höhere Stages, sobald der globale Progress stagniert. Auf System 26 findet der Algorithmus in Stage 3 keine verwertbaren Cross-Terme, promotiert dann global zu Stage 4 (kubische Terme) und Stage 5 (Trig), obwohl keine Gleichung Trig-Terme benötigt. Das ist kein Metrik-Fehler — es ist eine echte algorithmische Schwäche des systemweiten Staging.

**Nebenbeobachtung System 31 Seed 42:** Pruning-Schwellenwert 1e-3 × max_coeff könnte für BFGS-konvergierte Modelle zu streng sein. Der Term 0.0022*u1 ist klein aber nicht null. Zu re-evaluieren nach v3-Validierung.

**Gate-1-Entscheidung: v2.2 ist NICHT paper-ready. Phase 2 (EvoGrow v3) wird ausgelöst.**

Begründung: Der Failure-Mode auf Systems 26 und 63 ist klar auf systemweites Staging zurückführbar, nicht auf Metrik-Fehler oder Parameter-Fitting. Das ist genau die Bedingung, unter der v3 (gleichungsweises Staging) motiviert ist.

WP-v3.1 (Design Note) als nächsten Codex-Task formuliert.

<!-- f5e7033 -->

---

## 2026-05-17

### Strategischer Pivot: Paper 1 Neufokus

Paper 1 wird kein Pretuning-Vergleichspaper. Pretuning wird für Paper 1 vollständig deaktiviert und als mögliches Follow-up-Paper zurückgestellt.

**Neue wissenschaftliche Kernfrage:**
> Ist inkrementelles, gestuftes Wachstum ein effektiver Suchmechanismus für interpretierbare ODE-Entdeckung — und wo hilft es, wo versagt es?

**Phase A Neubewertung:** H1/H3 PARTIAL war kein schlechtes Ergebnis, sondern ein diagnostisches Signal. System-weites Staging ist möglicherweise zu grob für mehrdimensionale Systeme (26, 31, 63). Das ist der algorithmische Befund, dem das Paper nachgehen muss.

**Neues Experiment-Design:** 63 ODEBench-Systeme × 1 finaler EvoGrow-Variant × 3 Seeds = 189 Runs. Keine externen Baselines in-house; publizierte ODEBench-Zahlen als Referenzkontext.

**Gate-Struktur eingeführt:**
- Gate 1: Ist v2.2 nach Metric-Repair paper-ready? (Phase 1 Diagnose)
- Gate 2 (nur falls nötig): Ist v3 (gleichungsweises Staging) paper-ready?

`PAPER_1.md` vollständig neu geschrieben. WP-0.2 als erledigt markiert.

<!-- fb549af -->

## 2026-05-11

### H1–H4 Auswertung und Freeze Memo (Step 2)

Codex hat `evaluate_hypotheses.py` implementiert und die formale Hypothesenauswertung auf `paper1_phaseA_v1` (300/300 Runs) durchgeführt. Ergebnisse ins Freeze Memo (`docs/paper1_freeze_memo_phaseA.md`) und Diagnostics JSON (`analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json`) geschrieben.

**Verdicts:**
- **H1** (Stage Overshoot Reduction): PARTIAL — korrekte Richtung nur auf System 54 (Lorenz), 1 von 6. Systeme 3, 11, 26, 31, 63 zeigen kein Signal oder falscher Trend. Ursache: Mindestbudget pro Stage erzwingt mehr Levels auf einfachen Systemen.
- **H2** (Competitive Recovery Quality): SUPPORTED — 7 von 8 Systemen kompetitiv (exact_match oder mean_loss). Nur System 11 nicht kompetitiv.
- **H3** (Wasted Levels Reduction): PARTIAL — korrekte Richtung nur auf Systemen 11 und 54, 2 von 6.
- **H4** (Usage Policy Effect): SUPPORTED (vakuös) — alle Policy-Varianten zeigen exact_match=0 auf Stage-≥3-Systemen, erwartete Ordnung `hard ≥ soft ≥ passive` daher nicht unterscheidbar.

**Design-Entscheidungen dokumentiert:**
- `exact_support_match` als striktes Binary-Metrik ohne Schwellenwert ist korrekt und bleibt unverändert
- System 11 (`du=-u³`): EvoGrow findet Struktur mit loss ~4e-15, aber growth-without-pruning akkumuliert Null-Terme → kein exact_match. Echter algorithmischer Mangel, kein Metrik-Fehler. Muss im Paper explizit genannt werden.
- Generalisierungsstudie: keine förderfähigen Zellen (n_exact_runs < 3), bleibt im Supplementary.

### Repo Readiness Review und Cleanup

Vollständiges Repo-Review vor nächster Implementierungsphase. Alle gefundenen Issues behoben:

- `codex/CURRENT_TASK.md`: abgeschlossenen Step-2-Task gelöscht, "Kein aktiver Task" gesetzt
- `CLAUDE.md`: veraltete Abschnitte (242/300 Befunde, Active Studies 2026-04-29, Current Priorities 2026-04-29, Known Gaps) auf aktuellen Stand 2026-05-11 gebracht
- `analysis/CONVENTIONS.md`: gebrochene Referenz `CURRENT_TASK_ANALYSIS.md` → `CURRENT_TASK.md` korrigiert (Datei existiert nicht)
- `docs/paper1_study_protocol.md`: als Phase-A-Archivdokument markiert, nicht mehr aktives Protokoll
- `analysis/configs/paper1_phaseA_v1.json`: Generalisierungspfad von `outputs/studies/generalization/` → `debug_results/` korrigiert (WP-0.2)

Abschließende Verifikation: `debug_results/generalization_summary.csv` und `generalization_detail.csv` existieren — WP-0.2 damit vollständig erledigt.

Offener Rest: WP-0.1 (H4-Claim-Korrektur in `evaluate_hypotheses.py`) — wird morgen als Codex-Task formuliert. Das ist der einzige noch ausstehende Punkt vor dem endgültigen Abschluss von Phase A.

<!-- b4c1cce, 5f5fc43 -->

### Strategische Neuausrichtung: Paper 1 Roadmap

ODEBench-Paper (d'Ascoli et al. 2023, 2310.05573) analysiert: EvoODE verwendet dieselben 63 Strogatz-Systeme mit identischen ICs (alle 8 exakten Systeme verifiziert). Baseline-Strategie: veröffentlichte ODEBench-Zahlen direkt zitieren (σ=0, ρ=0 Regime), R²-Metrik aus existierenden Trajektorien berechnen.

**Strategie:** EvoODE konkurriert nicht mit ODEFormer (50M Training-Beispiele, A100), sondern mit SINDy(poly) und PySR (~35–50% Accuracy bei σ=0). EvoGrow v3 (gleichungsweise gestufte Promotion) als nächste Variante geplant.

`PAPER_1.md` komplett ersetzt durch detaillierten Ausführungsplan: Phasen 0–5, WP-Aufschlüsselung, EvoGrow v3 Design-Spec, Risikoregister, eingefrorene Baselines.

`CLAUDE.md`: neuer Abschnitt "Paper 1 — Execution Roadmap" als Pointer auf `PAPER_1.md`.

---

## 2026-05-08

### paper1_phaseA_v1 vollständig abgeschlossen

`experiments/run_experiment.jl paper1_phaseA_v1` hat alle 300 Runs durchlaufen (300/300, alle `success=true`, 0 failed, 0 interrupted). Laufzeit ca. 4.5 Tage.

Aggregation: `julia experiments/aggregate.jl paper1_phaseA_v1` → `run_registry.csv` (300 Zeilen).
Python-Pipeline: `aggregate_run_registry.py` → `data/paper1_phaseA_v1/aggregate_by_variant_system.csv` (60 Zeilen, 6 Varianten × 10 Systeme, alle Zellen vollständig).

### Erste vollständige Auswertung: paper1_phaseA_v1

**Exact Match (Kernbefunde):**

- Systeme 2, 3, 24: alle EvoGrow-Varianten `exact_match=1.0`, GP auf System 24 `exact_match=0` (loss ~4.5e-3 vs. EvoGrow 5.4e-14 — dramatischer Unterschied auf simpelstem 2D-linearem System)
- System 11 (cubic, `du=-u³`): alle EvoGrow `exact_match=0` trotz loss ~4.4e-15 — Bug in `exact_support_match` vermutet; GP `exact_match=1.0`
- Systeme 26, 31, 54, 63: `exact_match=0` für alle Varianten — kein exakter Strukturfund auf Stage-3-Systemen

**Loss EvoGrow vs. GP (höherdimensionale Systeme):**

| System | Beste EvoGrow | GP | Faktor |
|--------|--------------|-----|--------|
| 31 SIR | 7.0e-05 | 0.314 | ~4.500× |
| 54 Lorenz | 7.4e-04 | 0.921 | ~1.200× |
| 26 Lotka-Volterra | 2.5e-04 | 2.98e-03 | ~12× |

GP versagt auf gekoppelten Systemen deutlich — stärkstes Argument für EvoGrow.

**Stage Overshoot (Kernhypothese):**

- **System 54 (Lorenz):** v1=+2, v2.1=+1.6, alle v2.2=0 Overshoot, 0 Wasted Levels → sauberste Bestätigung der Kernhypothese
- **System 3 (Logistic):** v1=0 (flache Basis, keine Stage-Promotions), alle v2.x=+3 Overshoot — v2.2_stage_local verschärft wasted_levels auf 12 durch Mindestbudget
- **Systeme 26, 31, 63:** alle Varianten +2 Overshoot — kein Differenzierungssignal

**Offene Fragen:**
- `exact_support_match`-Bug bei System 11 untersuchen (loss ~0 aber kein Match)
- Warum GP auf System 24 (harmonic oscillator) so schlecht?
- Für keine Stage-3-Systeme exact match → algorithmisches Problem oder Loss-Tol-Problem?
- Kein Run konvergiert auf `loss_tol=1e-8` außer System 2/24 → Stopp-Mechanismus greift nie als Loss-Stopp

### WP3: Frame Layout Redesign (search_animation.jl)

Zweispalten-Layout für `render_frame`: linke Spalte = Trajektorien-Subplots, rechte Spalte = Info-Panel (Loss, entdeckte Gleichungen, wahre Gleichungen, farbige Legende). Aktuelle Level-Kandidaten in Orange, Historie in Grau. `plot_title` über allen Subplots. `structure_to_string` Koeffizientenformat auf `%.3f` geändert.

---

## 2026-05-05

### WP11: CairoMakie-basiertes `render_frame` (Spec + Abhängigkeit)
`ac7658f`

Codex-Spec für WP11 geschrieben: vollständiger Neubau von `render_frame` auf Basis von CairoMakie statt Plots.jl. Ziel ist pixel-genaue Kontrolle über Layout und Typography für Publikationsqualität.

CairoMakie als Abhängigkeit in `Project.toml` aufgenommen. Bestehende `search_animation.jl` bleibt unverändert, bis WP11 implementiert ist.

---

## 2026-05-04

### Animationspipeline: WP4–WP8 (Live-Rendering, Layout, Typography)

**WP4 — Live-Frame-Rendering via `level_callback`** (`2e31f2e`):
`level_callback`-Hook in EvoGrow eingebaut, der am Ende jedes Levels aufgerufen wird. Frame wird direkt während des Runs gerendert und gespeichert — kein Post-Hoc-Rendering mehr nötig.

**WP5 — Horizontale Balken im Info-Panel** (`8e46613`):
Frame-Layout auf horizontale Balken pro Kandidat umgestellt (Trajektorie-Panel links, Loss-Rang-Balken rechts). Verbesserte Lesbarkeit auf Stage-Promotions-Grenzen.

**WP6 — Stage-Grammar-Anzeige in der Gleichungsleiste** (`92f892e`):
Aktuell freigeschaltete Stage-Terme werden in der Gleichungsanzeige farblich hervorgehoben. Neue Terme (neu in dieser Stage) vs. ältere Terme visuell unterscheidbar.

**WP7 — Typografie-Refaktor** (`a496f94`):
Schriftgrößen, Zeilenabstände und Gewichtungen vereinheitlicht. Koeffizientenformat auf `%.3g` geändert (keine führenden Nullen mehr). Gleichungszeilen kürzer und lesbarer.

**WP8 — Header/Meta-Verfeinerung** (`c0f12ca`):
Titel-Header zeigt: System-Name, Variante, Seed, aktueller Stage, Level-Fortschritt. Grau-Kandidaten-Alpha von 0.08 auf 0.18 erhöht (besser sichtbar ohne Ablenkung vom besten Kandidaten).

---

## 2026-05-03

### Animationspipeline für EvoGrow-Suchverlauf (WP1–WP3)
`2fa3e18`

Visualisierung des stufenweisen EvoGrow-Suchprozesses als animiertes Video:

**WP1 — Snapshot-Sammlung in `src/structure/evogrow.jl`:**
- `vis_history`-Feld in EvoGrow; sammelt Snapshots am Ende jedes Levels
- Jeder Snapshot enthält aktuelle Population (Kandidaten + Scores) und Stage-Info

**WP2 — Rendering in `src/plotting/search_animation.jl` + `studies/visualization/animate_search.jl`:**
- `search_animation.jl`: rendert pro Level ein PNG-Frame
- `animate_search.jl`: orchestriert Discovery → Frame-Rendering → optionaler ffmpeg-Export (MP4)

**WP3 — Frame-Layout:**
- Zweispaltig: links Trajektorie-Subplots (Ground Truth vs. Kandidaten), rechts Info-Panel
- Aktuelle Level-Kandidaten: orange; akkumulierte History: grau
- Info-Panel: Stage, Level, Loss, true Gleichungen, farbige Legende

---

## 2026-05-02

### `profile_init` — Ergebnisse ausgewertet
`72629a3`

- `docs/profile_init_results.md` + `docs/profile_init_convergence.png` angelegt
- Lorenz: Pretune klar besser auf allen 3 Seeds (~4× niedrigerer Loss, erreicht Stage 3 statt Stage 2)
- Lotka-Volterra: Pretune auf Mittelwert besser, auf Seed-Ebene gemischt — treibt Algorithmus in Stage 5 (Overshoot)
- Kritisch: alle 12 Runs enden mit `max_levels`, kein Run konvergiert → Level-Budget zu gering für belastbare Aussagen

---

## 2026-04-30

### `analysis/status.py` — Logdatei-Auswertung (WP4)
`90e70f5`

`status.py` um Auswertung der neuen `run.log`-Dateien (aus WP2) erweitert:

- `LOG_PATHS`-Dict: Skript → `run.log`-Pfad im jeweiligen OUT_DIR
- `read_log_markers()`: liest `=== Started/Finished at ===`-Marker aus Logdatei (letzte 500 Zeilen)
- `build_log_info()`: leitet ab ob letzter Run sauber beendet (`clean=True/False/None`)
- `print_known_scripts()`: zeigt Log-Zeile pro Skript (Start-/Endzeit, sauber/unterbrochen)
- WMI-Logik, Output-Timestamps und ETA-Berechnung vollständig erhalten

### Resume-Logik für `benchmark_evogrow.jl` (WP1) + Stdout-Logging (WP2)
`0c74f2d`

Benchmark konnte bisher nicht sicher gestoppt werden: `open(summary_file, "w")` überschrieb
die CSV bei jedem Start. Lösung:

- `seed`-Spalte in CSV eingeführt (Header + Row + Fehler-Record)
- `parse_csv_fields()`: korrekter CSV-Parser für Semikolon-Trenner mit Quote-Handling
- `load_done_set()`: liest existierende CSV und baut `Set{Tuple{String,Int,Int}}` aus `(variant_slug, id, seed)`
- `load_records_from_csv()`: lädt alle Rows für Aggregate nach Resume
- Hauptloop: Skip-Check vor jedem Run, Append-Mode wenn CSV existiert
- Einmalige Migration der bestehenden 140-Row-CSV: `seed`-Spalte per Positionszählung
  nachträglich eingetragen (Seeds-Reihenfolge ist deterministisch → sicher ableitbar)

### Repository-Strukturmigration (WP-R)
`706549f`

Alle drei laufenden Skripte gestoppt. Migration durchgeführt:

- `benchmarks/odeformer/` → `benchmarks/data/` (Datenpfade in beiden Benchmark-Skripten aktualisiert)
- `benchmarks/results/` → `outputs/benchmarks/` (OUT_DIR in `benchmark_evogrow.jl`)
- `generalization_study.jl` → `studies/generalization/`, OUT_DIR → `outputs/studies/generalization/`
- `profile_init.jl` → `studies/profiling/`, OUT_DIR → `outputs/studies/profiling/`
- `debug_single.jl` → `studies/debug/`, OUT_DIR → `outputs/studies/debug/`
- `.gitignore`: `outputs/` eingetragen
- Vorhandene Output-Daten nach `outputs/` kopiert (Resume-Kontinuität)
- `SCRIPTS.md` + `CLAUDE.md` aktualisiert

### Stdout-Logging in alle Skripte (WP2)
`0c74f2d`

Alle fünf Skripte schreiben jetzt `run.log` im jeweiligen OUT_DIR (Append-Modus):

- `=== Started at <ts> ===` / `=== Finished at <ts> ===` als Marker
- `log_println()` + `@logf`-Makro für formatierte Ausgaben
- Betrifft: `benchmark_evogrow.jl`, `studies/profiling/profile_init.jl`,
  `studies/generalization/generalization_study.jl`, `studies/debug/debug_single.jl`,
  `experiments/run_experiment.jl`
- Bestehender per-Run-Log-Mechanismus in `profile_init.jl` bleibt erhalten

---

## 2026-04-29

### `analysis/status.py` — Study Status Checker (Codex-Task)
`756b512`, `b94601f`

Ziel: Skript, das aus SCRIPTS.md alle bekannten Scripts extrahiert und prüft, welche davon gerade laufen.

**Technische Analyse (Windows/WMI):**

- `julia.exe`-Prozesse per PowerShell + WMI abfragbar
- Problem: Command Line von `julia.exe` enthält auf Windows oft keine Script-Argumente
- Wenn Parent-Prozess `julialauncher.exe` ist: Argumente im Parent sichtbar → Script identifizierbar
- Wenn Parent `cmd.exe` ist (auch wenn cmd noch offen): Argumente gehen verloren — gilt für alle über cmd gestarteten Skripte

**Lösung: Hybrid-Ansatz**

1. Prozessbaum: julialauncher.exe-Parent → Script-Name direkt lesbar
2. Output-File-Timestamp: wenn Output-Datei < 90 min alt und Orphan-Prozess läuft → `[LÄUFT?]`

**ETA-Schätzung:**

- Rate über letzte 20 Runs (nicht Gesamtlaufzeit) — robust gegen stuck runs
- Für Experiment-Runner: Rate aus `finished_at`-Timestamps der status.json-Dateien
- Für Benchmark: Rate aus `elapsed_s`-Spalte in summary.csv
- Stuck-Run-Erkennung wenn Run seit >2h im Status `running`

**Implementierung und Nachtrag:**

- `analysis/status.py` als standalone Python-Skript mit Standard Library umgesetzt
- `SCRIPTS.md` wird per Regex auf `julia <path>.jl`-Aufrufe in Codeblöcken geparst
- Output-Mapping hart codiert, aber ohne Experiment-ID-Hardcoding (`glob`-Patterns)
- Fortschritt/ETA implementiert für:
  - `experiments/run_experiment.jl`
  - `benchmarks/benchmark_evogrow.jl`
  - `profile_init.jl`
  - `generalization_study.jl`
- Stuck-Run-Warnung erkennt aktuell hängende `status.json`-Runs, z.B. alte Lorenz-Runs mit `status="running"`
- Fehler passiert: Datei war zunächst nur untracked und wurde dadurch bei Workspace-Cleanup/Refresh entfernt
- Fix: `analysis/status.py` aus der implementierten Version wiederhergestellt und mit `b94601f` committed, damit sie nicht erneut verloren geht

---

## 2026-04-28

### Experiment-Runner: zweiter Lorenz-3D-Run hängt
`57c4ff3`

Run `54_evogrow_v1_seed7` (Lorenz periodic, EvoGrow v1, Seed 7) läuft seit 2026-04-28T07:46 ohne Fortschritt.
Ursache: Run wurde mit Git-Hash `04f458a7` generiert — **vor** der BFGS-Timeout-Implementierung.
Der neue Timeout greift nicht rückwirkend auf Runs mit altem Config-Hash.

Experiment-Runner: 234 → 242/300 Runs abgeschlossen.
Benchmark `benchmark_evogrow.jl`: ~93 → ~128/300 Runs (~43%).
`profile_init.jl`: weiterhin hängend auf Level 11, Stage 2, Lorenz 3D, Seed 42 — Daten bereits vorhanden.

---

## 2026-04-27

### BFGS-Timeout implementiert (`src/optimize/bfgs.jl`)
`59d6c16`

**Motivation**: `profile_init.jl` hängt seit 48+ Stunden auf einem einzelnen BFGS-Call (Lorenz 3D, Stage 2). `maxiters` begrenzt nur Iterationen, nicht Wall-Clock-Zeit.

**Umsetzung:**
- `time_limit_s::Float64 = 300.0` zu `BFGSOptimizer` ergänzt
- `time_limit = opt.time_limit_s` an beide `Optimization.solve`-Aufrufe (BFGS + Nelder-Mead Fallback) übergeben
- Bei Timeout gibt Optim.jl das beste bisher gefundene Ergebnis zurück — kein Absturz, kein NaN
- Logging: `log_warn("BFGS hit time_limit", ...)` wenn `retcode != Success`

**Parameterwahl**: 300s ist ~100× der medianen per-Call-Zeit (ca. 2–3s), greift bei normalen Runs nie.

### Paper 1 Reproducibility Protocol dokumentiert
`844bbe4`

Vollständige Dokumentation der Paper-1-Konfiguration direkt aus dem Code abgeleitet:
- alle 6 Varianten mit Slug, Basis, Progressions- und Usage-Mode
- alle 10 Benchmark-Systeme (exakt/Surrogate) mit IDs und True-Struktur
- sämtliche Hyperparameter explizit
- Seeds, Metriken, Execution-Loop, Output-Artefakte, Aggregationsregeln, Freeze-Klausel

Dabei 5 Diskrepanzen zwischen Dokumentation und Codebasis gefunden und behoben:
1. `EvoGrow`-Struct fehlte `progression`, `usage`, `use_pretuning`
2. `test.jl` und `test_evogrow_v2_lotka.jl` im Dateibaum, existieren nicht mehr
3. `run_odebench.jl` als Root-Datei angegeben, liegt in `benchmarks/`
4. `src/optimize/pretune.jl` existiert und wird genutzt, war undokumentiert
5. `experiments/` fehlte komplett im Dateibaum

### Experiment-Status (Stichtag 27.04.)

| Skript | Status |
|--------|--------|
| `experiments/run_experiment.jl paper1_phaseA_v1` | läuft — 234/300, ~6–7h Restlaufzeit |
| `benchmarks/benchmark_evogrow.jl` | läuft — 93/300, ~27–40h Restlaufzeit |
| `generalization_study.jl` | fertig (Output-CSVs vorhanden, 24.04.) |
| `profile_init.jl` | hängt seit 2 Tagen — Level 11, Stage 2, Lorenz 3D, Seed 42 |

---

## 2026-04-26

### Repository-Housekeeping
`1f9c643`

- `benchmarks/odeformer/results/` entfernt: alte Ergebnisdateien ohne reproduzierbaren Kontext
- `.gitignore` um `benchmarks/odeformer/results/` ergänzt

### Analyse-Pipeline für Paper 1 angelegt
`6eab0cf`, `ea3cc44`, `053d717`, `c1f51ef`, `0f8e677`, `8c1152d`, `d983abf`

- `analysis/` als dedizierter Bereich für Python-Auswertung angelegt
- `analysis/CONVENTIONS.md`: Architektur- und Regelwerk für die Python-Analyse
- `analysis/utils/`: `io.py`, `metrics.py`, `style.py` (Variant-Farben und Labels)
- `analysis/scripts/aggregate/aggregate_run_registry.py`: liest `run_registry.csv`, schreibt `aggregate_by_variant_system.csv`
- `analysis/scripts/plot/plot_exact_match_rates.py`: Exact-Match-Rate-Plot
- `analysis/scripts/plot/plot_stage_overshoot.py`: Stage-Overshoot-Plot (GP ausgeschlossen)
- `analysis/scripts/plot/table_main_results.py`: LaTeX-Tabelle Main Results

### Paper-1-Protokoll eingefroren (`docs/paper1_study_protocol.md`)
`2e65d57`, `9ca633a`, `c810703`

Core Goal: Paper 1 untersucht staged growth als Mechanismus zur kontrollierten Komplexitätssteigerung — nicht "bestes ODE-Discovery-System".

Hypothesen:
- H1: Stage-local v2.2 zeigt niedrigeren `mean_stage_overshoot` als v2.1 und v1
- H2: v2.2 liefert kompetitive `exact_match_rate` bei niedrigerem Complexity-Efficiency-Cost
- H3: `mean_wasted_levels` nur zwischen EvoGrow-Varianten; GP ausgeschlossen
- H4: usage-policy comparison (`hard`, `soft`, `passive`) als sekundäre Hypothese

Evidenzregeln:
- Surrogate-Systeme nicht für `exact_support_match` oder H1–H4-Strukturaussagen
- Systeme 2 und 24 (expected_stage=1) aus H1/H3/H4 ausgeschlossen
- No post-hoc cherry-picking; keine neuen Runs nach Ergebnisinspektion

### Variant-Slug vereinheitlicht
`9d25f44`

`evogrow_v2_2_stage_local` überall standardisiert: `benchmark_evogrow.jl`, Analyse-Skripte, `style.py`, Dokumentation.

### Logging: Datum im Timestamp ergänzt
`035e354`

`src/utils/logging.jl`: Timestamp-Format von `HH:MM:SS` auf `yyyy-mm-dd HH:MM:SS` erweitert.
Grund: über Nacht laufende Skripte erzeugen sonst Logs ohne Datumszuordnung.

---

## 2026-04-23

### Bugs gefunden und gefixt
`d27b697`

**Bug 1: `PolynomialBasis` fehlte kubischer Term für System 11**
- `evogrow_v1` nutzte `PolynomialBasis` (nur bis Grad 2), System 11 (Critical slowing down) erwartet `u1^3`
- Entscheidung: `evogrow_v1` auf `default_staged_polynomial_basis` umgestellt — gleicher Suchraum wie alle anderen Varianten, alles sofort entsperrt

**Bug 2: `log_exception` speicherte `DataType` statt `String`**
- `merged[:exception_type] = typeof(err)` schlug fehl weil `Dict{Symbol,String}` keinen `DataType` akzeptiert
- Fix: `string(typeof(err))` in `src/utils/logging.jl`

### Generalisierungsstudie geplant und implementiert (`generalization_study.jl`)
`f30af7c`

Frage: Wenn EvoODE auf Parametersatz A die korrekte Struktur findet — passt diese Struktur nach reinem Parameter-Refit auch auf ungesehene Parametersätze B–E derselben ODE-Familie?

- 3 Systeme (Logistic growth, Lotka-Volterra, SIR), je 5 Parametersätze (1 Train + 4 Test)
- 2 Varianten (evogrow_v2_2_stage_local, gp_baseline), 3 Seeds
- Baseline: frischer Discovery direkt auf Testtrajektorie
- Output: `debug_results/generalization_study/generalization_summary.csv`, `generalization_detail.csv`

### Erste Experiment-Befunde (paper1_phaseA_v1, ~40/300 Runs)

Bisher abgeschlossen: System 2 (Population growth) und System 3 (Logistic growth).

- Alle Runs: `success=true`, `exact_support_match=true`
- Loss ist deterministisch: identisch über alle Seeds (Pretuning + BFGS konvergiert immer ins gleiche Minimum)
- **Stage Overshoot:**
  - `evogrow_v2_1` (global plateau): mittlerer Overshoot 1.5 auf System 3 (expected_stage=2, landet in Stage 3–4)
  - Alle v2.2-Varianten (stage_local): Overshoot 0 — bleiben korrekt in Stage 2
  - Direkte Bestätigung der Kernhypothese

---

## 2026-04-22

### Pretuning (OLS Warm-Start)
`c4fad8a`

- `src/optimize/pretune.jl`: Ableitung per finite Differenzen, Design-Matrix aus Basistermen, OLS-Lösung als BFGS-Startwert
- `use_pretuning::Bool`-Flag in `EvoGrow`
- `level_log` um `elapsed_s`-Feld erweitert

### Experiment-Infrastruktur (WP-E1 bis WP-E3)
`c4fad8a`

- `experiments/generate_manifest.jl`: erzeugt Experiment-Verzeichnis, `manifest.json`, alle per-Run `config.json` + `status.json`
- `experiments/run_experiment.jl`: sequentieller Runner mit robustem Fehlerhandling, atomaren Writes, restart-fähig
- `experiments/aggregate.jl`: leitet `run_registry.csv` aus per-Run-Ordnern ab, idempotent
- Per-Run-Dateiprotokoll: `config.json` (immutable), `status.json` (non-atomic), `result.json` + `metrics.json` (atomar via tmp→rename)

### Debug- und Profiling-Skripte
`c4fad8a`

- `debug_single.jl`: Einzelrun auf Lotka-Volterra mit verbose Logging und PNG-Output
- `profile_init.jl`: Vergleich random vs. pretune Initialisierung auf Lotka-Volterra + Lorenz, 3 Seeds

### Experiment gestartet

`paper1_phaseA_v1`: 10 Systeme × 6 Varianten × 5 Seeds = 300 Runs, exploratory

---

## 2026-04-21

### EvoGrow v2.2 (stage_local)
`224714d`

- `StageProgressionPolicy` mit Modus `:stage_local` und `min_levels_per_stage`
- `StageUsagePolicy` mit Modi `:hard`, `:soft`, `:passive` und `new_term_bias_prob`
- Stage-lokale Plateau-Detektion mit Mindestbudget pro Stage
- Benchmark-Matrix: 10 Systeme × 6 Varianten × 5 Seeds vollständig

---

## 2026-04-20

### Projekt-Fundament
`84f94e8`, `4d8bd2e`, `f5e1d9c`, `a811927`

- Core stabilisiert: EvoGrow und GP laufen sauber mit konsistentem Loss (`discover()` end-to-end)
- Benchmark-Infrastruktur angelegt: 10-System-Suite, erste Varianten
- Housekeeping: Stubs gefixt, Docstrings, Interface-Bereinigung

---
