# CLAUDE.md - EvoODE

Deutsche Lesefassung von `CLAUDE.md`.

Diese Datei beschreibt die Projektvision, Architektur, Roadmap, den aktuellen
Status und die Forschungsprioritäten von EvoODE. Die englische Originaldatei
bleibt die technische Source of Truth; diese Fassung ist zum leichteren Lesen
gedacht.

Ausnahme: `docs/paper1_study_protocol.md` ist ein bewusst eigenständiges
Begleitdokument für Paper 1. Es dupliziert einige Konfigurationen aus
`CLAUDE.md` (Systemliste, Hyperparameter, Varianten), damit es als
selbstständiges Supplement funktioniert. Beide Dokumente müssen bei
Konfigurationsänderungen manuell synchron gehalten werden.

## Zusammenarbeit

Alle Kommunikation mit dem User läuft auf **Deutsch**.
Code, Kommentare, Docstrings und Commit Messages bleiben auf **Englisch**.
Das gilt für Antworten, Reviews und Planungsdiskussionen.

## Was dieses Projekt ist

EvoODE ist ein Julia-Forschungsframework zur datengetriebenen Entdeckung
interpretierbarer ODE-Systeme aus Zeitreihendaten.

Es unterstützt sowohl skalare Systeme (1D) als auch gekoppelte mehrdimensionale
Systeme. Der Forschungsschwerpunkt liegt auf gekoppelten Systemen.

Die Kernidee:
Anstatt eine feste Bibliothek wie SINDy zu fitten oder global mit großen
zufälligen Strukturen wie GP zu suchen, startet EvoODE klein und lässt die
Modellstruktur schrittweise wachsen. Komplexität wird erst erhöht, wenn
einfachere Strukturen nicht ausreichen.

Das ist ein PhD-Forschungsprojekt. Wissenschaftliche Korrektheit,
Reproduzierbarkeit und klare Argumentation sind wichtiger als Geschwindigkeit
oder Feature-Menge. Jede Architekturentscheidung muss als Teil eines
Forschungsbeitrags verteidigbar sein.

## Vision

EvoODE ist eine Forschungsplattform zur Entdeckung interpretierbarer,
gekoppelter dynamischer Systeme aus Daten durch strukturiertes, iteratives
Wachstum.

Ziel ist nicht nur, ODEs zu fitten, sondern zu untersuchen, wie Modellstrukturen
konstruiert, erweitert, validiert und kontrolliert werden sollten.

## Kernidee

```text
Data -> Structure -> Parameters -> Simulation -> Evaluation -> Iteration
```

Leitprinzip: strukturiertes, iteratives Wachstum statt globaler Suche.

## PhD-Fokus

Effiziente und robuste Suchstrategien für interpretierbare Entdeckung gekoppelter
ODE-Systeme.

## Wissenschaftliche Positionierung und Beitrag

### Positionierung gegenüber Baselines

| Methode | Suchraum | Wachstumsstrategie | Komplexitätskontrolle |
|---------|----------|--------------------|------------------------|
| SINDy | Eingeschränkt: feste lineare Bibliothek | Keine, direkte Regression | L1-Sparsity |
| GP | Uneingeschränkt | Global: startet groß und zufällig | Parsimony Pressure |
| EvoODE | Uneingeschränkt | Inkrementell: startet minimal und wächst | Staged Grammar + Stopping Criterion |

### Wissenschaftliche Kernthesen

1. Klein zu starten und inkrementell zu wachsen kann effizienter sein als globale Suche.
2. Grammatik-gestuftes Freischalten von Komplexität kann verschwendete Suche reduzieren.
3. Das Stop- und Promotionskriterium kann als prinzipieller Mechanismus zur Komplexitätskontrolle dienen.

### Forschungsfragen

- Was ist das beste Stop- und Promotionskriterium?
- Wie sollte Struktur wachsen: termweise, gleichungsweise, gestuft, coupling-aware oder error-guided?
- Wie sollten Struktursuche und Parameteroptimierung gekoppelt werden?
- Wie sollten gekoppelte Systeme spezifisch behandelt werden?
- Wie sollten entdeckte Modelle evaluiert werden?
- Wie skaliert die Performance mit Rauschen, Sample-Dichte, Kopplungsstärke und Dimensionalität?

## Projektstruktur

```text
EvoODE/
|-- CLAUDE.md                              (Projekt-Masterdokument)
|-- DIARY.md                               (chronologisches Projekttagebuch)
|-- SCRIPTS.md                             (Runbook für Skripte)
|-- Project.toml
|-- Manifest.toml
|-- src/                                   (Julia-Framework)
|-- benchmarks/                            (explorative Direkt-Skripte)
|-- experiments/                           (formale manifest-basierte Paper-1-Runs)
|-- docs/
|   `-- paper1_study_protocol.md           (eigenständiges Paper-1-Protokoll)
|-- analysis/                              (Python-Analysepipeline)
|-- codex/                                 (Task-Dateien für AI-assistierte Arbeit)
|-- debug_single.jl                        (später nach studies/debug/)
|-- profile_init.jl                        (später nach studies/profiling/)
`-- generalization_study.jl                (später nach studies/generalization/)
```

`studies/` existiert noch nicht. Es wird später durch WP-R2 angelegt, siehe
`codex/PENDING_REPO_MIGRATION.md`.

### `benchmarks/` vs. `experiments/`

Diese Ordner erfüllen unterschiedliche Zwecke und dürfen nicht vermischt werden.

| | `benchmarks/` | `experiments/` |
|---|---|---|
| Ausführung | direktes `julia script.jl` | manifest-basierter Runner |
| Zweck | explorativ, qualitativ | formal, paper-grade |
| Reproduzierbarkeit | best effort | atomare Writes, vollständiges Status-Tracking |
| Fehlerbehandlung | per-run catch, Logs nach stdout | per-run `status.json`, `metrics.json` |
| Output | `benchmarks/results/` (gitignored) | `experiments/<id>/runs/` |

### `codex/`-Konvention

Zwei getrennte Task-Dateien bilden die Julia/Python-Trennung ab:

- `CURRENT_TASK.md` - aktive Aufgabe für Julia-/Algorithmus-/Infrastrukturarbeit
- `CURRENT_TASK_ANALYSIS.md` - aktive Aufgabe für Python-Analysearbeit

Beide enthalten `Kein aktiver Task`, wenn nichts offen ist.

### Siehe auch

- `SCRIPTS.md` - Runbook mit konkreten Befehlen
- `DIARY.md` - chronologisches Log von Designentscheidungen, Bugfixes und Implementierungsnotizen
- `analysis/CONVENTIONS.md` - Regeln für die Python-Analysepipeline

Die Modulstruktur ist absichtlich erweiterbar. Neue Suchalgorithmen, Basen,
Losses und Optimizer sollen über die jeweiligen Interfaces ergänzt und in
`src/EvoODE.jl` registriert werden. Algorithmusspezifische Sonderlogik gehört
nicht hart in `discover()`.

## Zentrale Typen

### `Trajectory`

```julia
struct Trajectory
    t::Vector{Float64}
    x::Matrix{Float64}   # shape: T x dim
end
```

- `dim = 1` für skalare ODEs, `dim > 1` für gekoppelte Systeme.
- Standard-Datencontainer der Pipeline.

### `StructureSpec`

```julia
struct StructureSpec
    active_idxs::Vector{Vector{Int}}
end
```

- `active_idxs[k]` enthält die aktiven Basistermindizes für Gleichung `k`.
- Die aktuelle Repräsentation ist indexbasiert und linear in Basistermen.
- Expression Trees sind eine spätere Erweiterung und noch nicht implementiert.

### `DiscoveryOptions`

Steuert gemeinsames, algorithmusunabhängiges Suchverhalten:

- RNG Seed und Verbosity
- minimale und maximale Levels
- absoluter Loss-Threshold
- Plateau-Erkennung und relative Plateau-Einstellungen

### `DiscoveryResult`

```julia
struct DiscoveryResult
    structure::Any
    params::Vector{Float64}
    loss::Float64
    objective::Float64
    meta::NamedTuple
end
```

- `loss` ist der validierte Loss auf der final simulierten Trajektorie.
- `objective` ist die Such-Objective aus der Struktursuche.
- `meta` enthält Diagnostik aus Suche, RHS-Building, Optimierung, Prediction und Checks.

## Core Pipeline

```text
discover(traj; structure, optimizer, basis, loss, options)
    |
    |-- 1. search_structure(strategy, traj, basis, loss, optimizer, options)
    |       -> structure, params, loss, objective, meta
    |
    |-- 2. build_rhs(structure, basis)
    |       -> f!, n_params, build_meta
    |
    |-- 3. simulate(f!, params, traj; ...)
    |       -> Yhat mit shape T x dim
    |
    `-- 4. evaluate_loss(loss, Yhat, traj.x)
            -> DiscoveryResult
```

Wichtig: `discover()` refittet Parameter nicht blind nach der Struktursuche.
Refit passiert nur, wenn die zurückgegebene Parameterzahl nicht zur gebauten RHS passt.

## Suchalgorithmen

### EvoGrow

EvoGrow ist der zentrale Forschungsalgorithmus.

```julia
Base.@kwdef struct EvoGrow <: AbstractStructureSearch
    pop_size::Int = 20
    n_levels::Int = 5
    children_per_parent::Int = 2
    max_terms_per_eq::Int = 5
    λ::Float64 = 1e-3
    progression::StageProgressionPolicy = StageProgressionPolicy()
    usage::StageUsagePolicy = StageUsagePolicy()
    use_pretuning::Bool = true
end
```

Ablauf:

1. Mit minimalen Strukturen starten.
2. Aktuelle Population evaluieren.
3. Kinder durch Strukturwachstum erzeugen.
4. Parameter fitten und Loss plus Komplexitätsstrafe bewerten.
5. Beste Population auswählen.
6. Gemeinsame Stopplogik nutzen: stoppen oder bei staged bases mehr Komplexität freischalten.

#### EvoGrow-Varianten

- v1: flaches Wachstum über alle verfügbaren Basisterme
- v2: gestufte Komplexitätsfreigabe
- v2.1: stage-aware child generation nach Stage-Unlock
- v2.2: stage-local progression mit Mindestbudget pro Stage und konfigurierbarer Usage Policy
- v3: geplantes gleichungsweises Wachstum
- v4: geplantes coupling-aware Wachstum

#### EvoGrow-v2.2-Design-Freeze

Paper 1 fokussiert auf staged growth als Mechanismus zur Komplexitätskontrolle.

Die v2.2-Richtung ist fixiert:

- jede Stage erhält ein Mindestbudget gemessen in Levels
- Plateau-Erkennung ist stage-local, nicht global
- Promotion erfordert ausreichende Stage-Erkundung plus Plateau plus Loss über Zielwert
- die globale Loss-Toleranz bleibt ein harter Stopp

#### Populationsverhalten bei Stage-Promotion

Bei Promotion von einer Stage zur nächsten wird die aktuelle Population unverändert
übernommen. Individuen aus früheren Stages laufen in der neuen Stage weiter und
können mit neu freigeschalteten Basistermen erweitert werden.

Das ist beabsichtigt: Der Warm-Start-Effekt erhält gute bisherige Strukturen und
vermeidet einen Neustart an jeder Stage-Grenze.

Akzeptiertes Risiko: Anchoring. Die Population kann zu stark an niedrigere Stages
gebunden bleiben und neue Terme zu wenig erkunden. Die Stage Usage Policy
(`hard`, `soft`, `passive`) soll genau dem entgegenwirken.

Ein Population Reset bei Promotion ist eine geplante spätere Variante und darf in
der aktuellen Phase nicht implementiert werden.

Zwei Designachsen müssen getrennt bleiben:

1. Stage Progression Policy: steuert, wann eine Stage behalten, promoted oder beendet wird.
2. Stage Usage Policy: steuert, wie stark neue Terme nach Unlock bevorzugt werden.

Die aktuelle v2.1-Baseline ist:

- staged term unlocking
- global plateau-driven promotion
- hard stage-aware child generation nach Unlock

Passive unlock-only ist nicht die Baseline, sondern eine separate Kontrollvariante.

Aktuelle v2.2-Usage-Policy-Vergleiche:

- `:hard`
- `:passive`
- `:soft`

Stage Progression und Stage Usage dürfen nicht wieder zu einem Mechanismus
zusammengezogen werden.

#### Aktuelle vorläufige Befunde (`paper1_phaseA_v1`, 40/300 Runs)

- System 2 (linear): alle Varianten finden die exakte Struktur; Loss ist über Seeds deterministisch.
- System 3 (logistic, `expected_stage=2`): `evogrow_v2_1` overshooted im Mittel um 1.5 Stages; alle v2.2-stage-local Varianten zeigen 0 Overshoot.
- Höherdimensionale Systeme (Lorenz, SEIR, Lotka-Volterra) waren zu diesem Zeitpunkt noch nicht vollständig.

### `GPStructureSearch`

Baseline-Genetic-Programming-Suche über die volle Basis.

- Tournament Selection
- per-equation Crossover
- Add/Remove/Replace Mutation
- keine staged complexity release

GP ist Vergleichsbaseline, nicht der zentrale Beitrag.

## Basis-Bibliotheken

### `PolynomialBasis`

Flache Basis, in der alle unterstützten Polynomterme sofort verfügbar sind.

### `StagedPolynomialBasis`

Default-Staged-Basis mit fünf Komplexitätsstufen:

1. lineare Terme
2. self-quadratic Terme
3. paarweise Cross-Terme
4. self-cubic Terme
5. trigonometrische Terme

Für nicht-gestufte Basen sind alle Terme von Anfang an verfügbar.

## Losses und Evaluation

Implementierter Loss:

- `MSELoss`: State-MSE auf simulierten Trajektorien

Genutzte oder geplante Evaluationsachsen:

- State MSE
- Derivative Loss
- Simulation Loss
- Complexity Penalty
- Validation Splits

## Optimizer

Implementiert:

- `BFGSOptimizer`: primärer Backend-Optimizer für Parameterfitting
- `DummyOptimizer`: Platzhalter für Tests und Smoke Checks

### Pretuning

`src/optimize/pretune.jl` implementiert einen Least-Squares-Warm-Start für die
Parameterinitialisierung. Ableitungen werden per finite differences geschätzt,
aus aktiven Basistermen wird eine Designmatrix gebaut, und das lineare System
liefert Startparameter für BFGS.

Das ist kein separater Optimizer und nicht Teil der öffentlichen API. Es wird
intern von EvoGrow und GPStructureSearch genutzt, wenn `use_pretuning = true`
(Default). Mit `use_pretuning = false` fällt EvoGrow auf Nullinitialisierung zurück.

Entfernt:

- Es gibt aktuell keinen öffentlichen Adam-Optimizer in der Paket-API.
- Adam soll nicht wieder eingeführt werden, solange er nicht implementiert und forschungsmotiviert ist.

## Stopplogik

Gemeinsam für alle Struktursuchalgorithmen über `should_stop()`:

1. hartes Maximum-Level-Limit
2. Minimum-Level-Guard
3. absoluter Loss-Threshold
4. absolute Plateau-Erkennung
5. relative Plateau-Erkennung

Bei EvoGrow kann Plateau eine Stage-Promotion auslösen statt Terminierung, wenn
weitere Stages verfügbar sind. Diese Stop- und Promotionslogik ist Teil des
Kernbeitrags und muss vorsichtig behandelt werden.

## Experiment-Infrastruktur

Die formale Paper-1-Schicht liegt in `experiments/` und ist getrennt vom
explorativen `benchmarks/`-Runner.

Skripte:

- `experiments/generate_manifest.jl`: erzeugt Experiment-Verzeichnis, `manifest.json` und alle per-run `config.json`/`status.json`
- `experiments/run_experiment.jl`: führt alle queued Runs sequentiell aus; einzelne Run-Crashes stoppen den Runner nicht
- `experiments/aggregate.jl`: scannt per-run Ordner und erzeugt `run_registry.csv`; idempotent

Per-run-Dateiprotokoll:

- `config.json`: immutable nach Erstellung
- `status.json`: wird bei Statuswechsel überschrieben, nicht atomar
- `result.json`: atomar geschrieben, nur bei `success=true`
- `metrics.json`: atomar geschrieben, bei Failure auch partial wenn möglich
- `log.txt`: append-only, mit Restart-Marker
- `summary.txt`: menschenlesbar, wird bei Abschluss überschrieben

Status-Semantik:

| Status | Bedeutung |
|--------|-----------|
| `queued` | noch nicht gestartet |
| `running` | gestartet; bei Prozessabbruch später als `interrupted` interpretierbar |
| `finished` | ohne Exception abgeschlossen; sagt nichts über Ergebnisqualität |
| `failed` | Exception wurde vom Runner gefangen |
| `interrupted` | nur vom Aggregator abgeleitet |

`success=true` bedeutet: Run abgeschlossen, finite Loss verfügbar, Result/Metrics geschrieben.
`success=false` bedeutet: Exception, all-NaN Output oder Write Failure.
`failure_reason` ist immer ein kontrollierter Enum.

`run_registry.csv` ist abgeleitet, nie primär. Es kann jederzeit aus den per-run
Ordnern neu erzeugt werden.

Ausführung:

```text
julia experiments/generate_manifest.jl
julia experiments/run_experiment.jl <experiment_id>
julia experiments/aggregate.jl <experiment_id>
```

Aktuelles Experiment:

- `paper1_phaseA_v1`: 10 Systeme x 6 Varianten x 5 Seeds = 300 Runs

## Benchmark-Daten und Skripte

Hauptdatensatz:

- `benchmarks/odeformer/strogatz_extended.json`
- erweiterter Strogatz-Benchmark aus dem ODEFormer-Kontext
- 63 Systeme: 23 skalar, 28 gekoppelt 2D, 10 gekoppelt 3D, 2 gekoppelt 4D

Benchmark-Skripte:

- `benchmarks/benchmark_evogrow.jl`
- `benchmarks/run_odebench.jl`

Rationale für Stage-Budget:

```text
effective_min = max(min_levels_per_stage, plateau_window + 1)
              = max(2, 4)
              = 4 Levels pro Stage
```

Daraus folgt:

- Stage 2: mindestens 4 Levels
- Stage 3: mindestens 8 Levels
- Stage 4: mindestens 12 Levels
- Stage 5: mindestens 16 Levels

`EVO_LEVELS = 20` reicht für alle Benchmark-Systeme. `EVO_LEVELS = 8`
(QUICK mode) reicht nur für Systeme bis Stage 1 oder 2.

## Aktueller Status

### Phase 1 - Stable Core

Status: DONE, abgeschlossen am 2026-04-20.

Core Pipeline, `discover()`, `GPStructureSearch`, EvoGrow-Baseline,
gemeinsame Stopplogik, strukturiertes Logging und Sanity Checks sind stabil.

### Phase 2 - EvoGrow-Varianten

Status: IN PROGRESS.

- v1: DONE, flaches termweises Wachstum
- v2: DONE, gestufte Komplexitätstiers
- v2.2: DONE, stage-local progression plus usage policies
- v3: NOT STARTED, geplantes equation-wise Wachstum
- v4: NOT STARTED, geplantes coupling-aware Wachstum

### Phase 3 - Benchmarking

Status: IN PROGRESS, gestartet am 2026-04-21.

Benchmark-Infrastruktur:

- 10 Systeme, exakte und surrogate Split
- 6 Varianten
- 5 Seeds pro `(variant, system)`
- Metriken: Loss, exact support match, final stage, overshoot, wasted levels, elapsed time

Geplante nächste Achsen:

- Rauschen
- Sampling-Dichte
- Kopplungsstärke
- Dimensionalität

### Phase 4 - Paper 1

Status: IN PROGRESS, gestartet am 2026-04-22.

Experiment-Infrastruktur WP-E1 bis WP-E3 ist fertig:

- Manifest-Generator
- sequentieller Runner
- Aggregator
- atomare per-run Writes
- `run_registry.csv` als abgeleitete Sicht

Aktives Experiment:

- `paper1_phaseA_v1`: 300 Runs, 10 Systeme x 6 Varianten x 5 Seeds

Zielrichtung:

- EvoGrow-Baselines vs. GP und perspektivisch SINDy
- einfache Systeme
- staged-growth-Konzept
- erste systematische Benchmark-Vergleiche

### Phase 5 - Advanced Methods

Status: NOT STARTED.

- Expression Trees
- error-guided growth
- backtracking
- hybrid search
- validation-based stage promotion
- multi-hypothesis models

## Aktive Studien (Stand 2026-04-23)

| Skript | These |
|--------|-------|
| `experiments/run_experiment.jl paper1_phaseA_v1` | Staged growth ist effizienter als flat growth und GP, gemessen über exact support recovery, stage overshoot und wasted levels. |
| `benchmarks/benchmark_evogrow.jl` | Explorative Cross-System-Frage: Findet EvoGrow über alle 10 Systeme zuverlässig korrekte Strukturen? |
| `profile_init.jl` | OLS-Warm-Start führt zu schnellerer Konvergenz und niedrigerem finalen Loss als random init. |
| `generalization_study.jl` | Eine strukturell korrekte Entdeckung generalisiert über Parameterregime, wenn nur Parameter refittet werden. |

## Aktuelle Prioritäten

Stand 2026-04-23:

1. Vier aktive Studien fertig laufen lassen.
2. `paper1_phaseA_v1` aggregieren.
3. `run_registry.csv` analysieren: exact recovery, stage progression, wasted levels.
4. `generalization_study` und `profile_init` auswerten.
5. Failure Cases identifizieren.
6. Paper-1-Experimentteil anhand echter Ergebnisse planen.

## Implementiert und funktionierend

- `discover()` end-to-end
- EvoGrow v1, v2.1, v2.2
- `StageProgressionPolicy`, `StageUsagePolicy`
- `GPStructureSearch`
- `PolynomialBasis`, `StagedPolynomialBasis`
- `MSELoss`
- `BFGSOptimizer`, `DummyOptimizer`
- Plotting und CSV Export
- Pretuning per Least-Squares-Derivative-Matching
- 10-System-Benchmark mit 6 Varianten und 5 Seeds
- Experiment-Infrastruktur bis `run_registry.csv`

## Bekannte Lücken

- `utils/checks.jl` ist noch fast ein Placeholder.
- Kein Train/Validation Split in Discovery.
- Keine Noise-Injection Utilities.
- `paper1_phaseA_v1` war am 2026-04-23 noch nicht vollständig analysiert.
- Kein systematischer Vergleich gegen GP und SINDy abgeschlossen.
- Expression Trees sind nicht implementiert.
- Test-/Environment-Ausführung muss noch aufgeräumt werden.
- Parameterzahlvalidierung vor Optimierung ist noch schwach.
- `simulate()` gibt bei Solve-Failures noch NaNs zurück und braucht stärkere Failure-Behandlung.

## Designprinzipien

1. Modular: jede Komponente ist hinter einem Interface austauschbar.
2. Reproduzierbar: stochastic behavior wird über `DiscoveryOptions.rng_seed` geseedet.
3. Interpretierbar: menschenlesbare Strukturrepräsentation bleibt erhalten.
4. Minimal: keine Features ohne direkte Forschungsmotivation.
5. Konsistentes Logging: Diagnostik läuft über gemeinsame Logging-Patterns.
6. Metadaten erhalten: Such- und Fit-Diagnostik nicht still verwerfen.

## System-Handling-Richtungen

- full-system discovery
- equation-wise discovery
- equation-wise discovery mit teacher forcing
- sequential discovery
- hybrid approaches

Das sind Forschungsrichtungen, nicht alles implementierte Features.

## Non-Goals

- aktuell keine GPU-Arbeit
- keine UI
- keine PDE-Erweiterung
- keine premature optimization
- keine unnötigen Dependencies

## Coding Conventions

- Julia only
- Ziel: Julia 1.11.5
- öffentliche API wird aus `src/EvoODE.jl` exportiert
- `Base.@kwdef` für structs mit Defaults
- ODE RHS-Funktionen bleiben in-place: `f!(du, u, params, t)`
- Parametervektoren bleiben `Vector{Float64}`
- Metadaten konsistent als `NamedTuple`
- modulare Interfaces statt Sonderlogik in Orchestration

## Leitregel

Jede Änderung muss eine Forschungshypothese unterstützen.
Wenn nicht benannt werden kann, welche Forschungsfrage eine Änderung adressiert,
soll sie nicht gemacht werden.

## Paper 1 - Reproducibility Protocol

### Scope

Dieser Abschnitt definiert das exakte experimentelle Setup für Paper 1.
Alle Konfigurationen sind fixiert. Jede Änderung erfordert einen neuen
Experimentblock mit neuer ID und expliziter Versionierung.

### Verglichene Methoden

| Label | Slug | Basis | Progression mode | Usage mode |
|-------|------|-------|------------------|------------|
| EvoGrow v1 (flat) | `evogrow_v1` | `StagedPolynomialBasis` (all terms) | `:global_plateau` | `:hard` |
| EvoGrow v2.1 baseline | `evogrow_v2_1` | `StagedPolynomialBasis` | `:global_plateau` | `:hard` |
| EvoGrow v2.2 progression-only | `evogrow_v2_2_stage_local` | `StagedPolynomialBasis` | `:stage_local` | `:hard` |
| EvoGrow v2.2 passive usage | `evogrow_v2_2_passive` | `StagedPolynomialBasis` | `:stage_local` | `:passive` |
| EvoGrow v2.2 soft usage | `evogrow_v2_2_soft` | `StagedPolynomialBasis` | `:stage_local` | `:soft` |
| GP baseline | `gp_baseline` | `StagedPolynomialBasis` (all terms) | N/A | N/A |

Hinweise:

- EvoGrow v1 nutzt die gleiche Termmenge wie GP, aber ohne staged release.
- v2.1 unterscheidet sich von v1 durch staged release und global plateau progression.
- v2.2 progression-only ändert gegenüber v2.1 nur `:stage_local`.
- Passive und soft teilen dieselbe progression, unterscheiden sich aber in usage mode.

### Benchmark-Datensatz

Der Benchmark besteht aus genau 10 Systemen aus
`benchmarks/odeformer/strogatz_extended.json`.

Exakte Systeme:

| ID | Name | Dim | Expected stage |
|----|------|-----|----------------|
| 2 | Population growth | 1 | 1 |
| 3 | Logistic growth | 1 | 2 |
| 11 | Critical slowing down | 1 | 4 |
| 24 | Harmonic oscillator | 2 | 1 |
| 26 | Lotka-Volterra competition | 2 | 3 |
| 31 | SIR model | 2 | 3 |
| 54 | Lorenz (periodic) | 3 | 3 |
| 63 | SEIR model | 4 | 3 |

Surrogate-Systeme:

| ID | Name | Dim | Expected stage | Hinweis |
|----|------|-----|----------------|---------|
| 23 | Overdamped pendulum | 1 | 5 | Constant offset außerhalb der Basis |
| 37 | Van der Pol oscillator | 2 | 4 | Cubic cross term außerhalb der Basis |

Exakte und surrogate Systeme dürfen nie in einer einzigen
Structure-Correctness-Metrik gemischt werden.

### Fixe Hyperparameter

EvoGrow:

```text
pop_size             = 10
n_levels             = 20
children_per_parent  = 2
max_terms_per_eq     = 6
λ                    = 1e-3
min_levels_per_stage = 2
new_term_bias_prob   = 0.75
```

GP:

```text
pop_size         = 10
n_generations    = 20
tournament_k     = 3
p_crossover      = 0.7
p_mutation       = 0.3
max_terms_per_eq = 6
init_min_terms   = 1
init_max_terms   = 2
λ                = 1e-3
```

Shared `DiscoveryOptions`:

```text
min_levels       = 2
max_levels       = 50
loss_tol         = 1e-8
plateau_window   = 3
plateau_tol      = 1e-4
plateau_relative = false
plateau_rtol     = 1e-3
```

Optimizer:

```text
BFGSOptimizer(maxiters = 200)
```

Seeds:

```julia
seeds = [42, 123, 7, 99, 17]
```

Gesamt: 6 Varianten x 10 Systeme x 5 Seeds = 300 Runs.

### Metriken

Per Run:

- `loss`
- `objective`
- `exact_support_match`
- `final_stage`
- `stage_overshoot`
- `wasted_levels`
- `total_loss_evals`
- `total_invalid_evals`
- `elapsed_s`

Aggregiert pro `(variant_slug, system_id)`:

- `mean_loss`
- `std_loss`
- `exact_match_rate`
- `mean_final_stage`
- `mean_wasted_levels`
- `mean_elapsed_s`
- `mean_invalid_evals`

Ein Run ist gültig, wenn `loss` nicht NaN ist.

### Ausführung

```text
julia benchmarks/benchmark_evogrow.jl
```

Full mode für Paper 1: keine Environment Flags.
Quick mode nur für Entwicklung: `QUICK=true julia benchmarks/benchmark_evogrow.jl`.

### Output-Artefakte

- `benchmarks/results/summary.csv`: per-run CSV
- `benchmarks/results/summary_aggregate.csv`: aggregierte CSV
- per-run Trajectory Plots
- per-run Convergence Plots
- per-run Prediction CSVs

### Aggregationsregeln

Aggregation gruppiert nach `(variant_slug, system_id)`.
`n_valid` ist die Anzahl nicht-NaN Loss Runs.
Alle Mittelwerte, Standardabweichungen und Raten werden nur über gültige Runs berechnet.

`exact_match_rate` ist nur für exakte Systeme sinnvoll und darf nicht für
Surrogate-Systeme berichtet werden.

### Versionierung und Freeze

Jeder Run speichert den Git-Hash. Vor Veröffentlichung muss geprüft werden, ob
alle Runs auf demselben Commit liefen.

Die Paper-1-Konfiguration ist fixiert. Änderungen an Systemauswahl,
Initialbedingungen, Hyperparametern, Seeds, Varianten oder Metriken erfordern
eine neue Experiment-ID, z.B. `paper1_phaseA_v2`.

Änderungen an Analyse-Skripten sind erlaubt, solange sie die Run-Ausführung und
die in `summary.csv` aufgezeichneten Werte nicht verändern.

