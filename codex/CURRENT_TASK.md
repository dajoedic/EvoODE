# WP-G1: Strukturgeneralisierungs-Studie

## Kontext

EvoODE entdeckt ODE-Strukturen aus Zeitreihendaten.
Bisher wurde immer nur auf denselben Daten evaluiert, auf denen auch trainiert wurde.

Diese Studie untersucht eine andere Frage:
Wenn EvoODE auf einer Trajektorie (Parametersatz A) die korrekte Struktur findet —
kann diese Struktur dann auf ungesehene Parametersätze (B, C, D, E) desselben Systems übertragen werden,
indem nur die Parameter neu optimiert werden?

Das ist ein Test auf mechanistische Korrektheit der gefundenen Struktur:
Eine korrekte Struktur sollte auf beliebige Parametrisierungen derselben ODE-Familie passen,
nachdem die Parameter neu gefittet wurden.

---

## Dateien, die vor jeder Implementierung vollständig zu lesen sind

- `src/core/discover.jl` — Pipeline-Überblick, DiscoveryResult-Felder
- `src/structure/interface.jl` — `build_rhs`-Interface
- `src/optimize/bfgs.jl` — wie der Optimizer intern aufgerufen wird
- `src/simulate/solve.jl` — `simulate`-Interface
- `src/loss/mse.jl` — `evaluate_loss`-Interface
- `src/basis/staged_polynomial.jl` — `default_staged_polynomial_basis`
- `benchmarks/benchmark_evogrow.jl` — wie Systeme und Trajektorien definiert sind
- `experiments/run_experiment.jl` — wie Algorithmen aus Konfiguration gebaut werden
- `profile_init.jl` — Referenz für den Skript-Aufbau (ähnlicher Scope)

---

## Was zu implementieren ist

### Neues Skript `generalization_study.jl` im Projektroot

Standalone-Skript, keine neuen Infrastruktur-Dateien.
Kein Manifest, kein formales Experiment.
Analoger Aufbau zu `profile_init.jl`.

---

### Schritt 1: Systeme und Parametervarianten definieren

Drei Systeme mit je fünf Parametersätzen (1 Training + 4 Test).
Jeder Parametersatz definiert vollständige ODE-Koeffizienten für dasselbe strukturelle Modell.

**System 1: Logistic growth (dim=1)**

Struktur: `du1 = r * u1 - k * u1^2`

Trainingsparameter: r=0.79, k=0.0106 (Originaldatensatz aus dem Benchmark)

Vier Testparametersätze mit variiertem r und k:
- r=0.50, k=0.008
- r=1.20, k=0.020
- r=0.60, k=0.015
- r=1.00, k=0.005

Trajektorie: u0=[10.0], tspan=(0.0, 10.0), T=100 Zeitpunkte, Solver Tsit5 mit abstol=1e-9, reltol=1e-9.

**System 2: Lotka-Volterra competition (dim=2)**

Struktur: `du1 = a*u1 - b*u1*u2`, `du2 = c*u1*u2 - d*u2`

Trainingsparameter: a=3.0, b=2.0, c=1.0, d=2.0 (Originaldatensatz)

Vier Testparametersätze:
- a=2.0, b=1.5, c=0.8, d=1.5
- a=4.0, b=2.5, c=1.5, d=2.5
- a=2.5, b=1.0, c=0.5, d=1.0
- a=3.5, b=3.0, c=2.0, d=3.0

Trajektorie: u0=[1.0, 1.0], tspan=(0.0, 5.0), T=100 Zeitpunkte.

**System 3: SIR model (dim=2)**

Struktur: `du1 = -beta*u1*u2`, `du2 = beta*u1*u2 - gamma*u2`

Trainingsparameter: beta=0.4, gamma=0.314 (Originaldatensatz)

Vier Testparametersätze:
- beta=0.2, gamma=0.1
- beta=0.6, gamma=0.5
- beta=0.3, gamma=0.2
- beta=0.8, gamma=0.6

Trajektorie: u0=[0.99, 0.01], tspan=(0.0, 30.0), T=100 Zeitpunkte.

---

### Schritt 2: Discovery-Konfiguration

Zwei Varianten werden verglichen:
- `evogrow_v2_2_stage_local`: EvoGrow mit stage_local-Progression, hard usage
- `gp_baseline`: GP-Baseline

Parameter für EvoGrow (identisch zu paper1_phaseA_v1):
pop_size=10, n_levels=20, children_per_parent=2, max_terms_per_eq=6, lambda=1e-3,
min_levels_per_stage=2, new_term_bias_prob=0.75, use_pretuning=true.

Parameter für GP (identisch zu paper1_phaseA_v1):
pop_size=10, n_generations=20, tournament_k=3, p_crossover=0.7, p_mutation=0.3,
max_terms_per_eq=6, init_min_terms=1, init_max_terms=2, lambda=1e-3.

DiscoveryOptions (identisch zu paper1_phaseA_v1):
min_levels=2, max_levels=50, loss_tol=1e-8, plateau_window=3, plateau_tol=1e-4.

Basis: `default_staged_polynomial_basis(dim)` für beide Varianten.

Seeds: drei Seeds — 42, 123, 7 — für den Discovery-Schritt auf der Trainingstrajektorie.

---

### Schritt 3: Parameter-Refit auf Testtrajektorien

Nach jedem Discovery-Run steht eine entdeckte Struktur (ein `StructureSpec`) zur Verfügung.

Für jeden der vier Testparametersätze:

1. Generiere Testtrajektorie mit dem entsprechenden Parametersatz (gleiche u0, tspan, T wie Training).
2. Baue den RHS aus der fixierten Struktur: `build_rhs(result.structure, basis)` liefert `f!` und `n_params`.
3. Optimiere nur die Parameter mit BFGS auf der Testtrajektorie.
   Startpunkt: Nullvektor (kein Pretuning im Refit-Schritt, damit der Vergleich sauber ist).
   Für die BFGS-Optimierung: `Optim.jl` direkt verwenden (ist bereits in den Dependencies).
   Die Zielfunktion ist: params → MSE zwischen simulierter Trajektorie und Testtrajektorie.
   Bei fehlgeschlagener Simulation (NaN): Verlust = Inf.
   maxiters=500 für den Refit (großzügiger als Discovery, da Struktur fixiert).
4. Evaluiere den finalen Refit-Loss.

Der Refit-Loss misst, wie gut die gefundene Struktur nach Parameteranpassung auf ungesehene Daten passt.

---

### Schritt 4: Baseline — Discovery direkt auf Testtrajektorie

Für jeden Testparametersatz: führe denselben Discovery-Run direkt auf der Testtrajektorie durch
(gleiche Variante, gleicher Seed).

Dieser "Fresh Discovery"-Loss ist die untere Schranke: was wäre möglich, wenn man immer direkt
auf den Testdaten trainiert?

---

### Schritt 5: Ergebnisse schreiben

Zwei CSV-Dateien in `debug_results/`:

**`generalization_summary.csv`** — eine Zeile pro (system, variant, seed):
- system_name, variant, seed
- train_loss (Discovery-Loss auf Trainingstrajektorie)
- train_exact_support_match (bool, falls berechenbar)
- mean_refit_loss (Mittelwert über die vier Testparametersätze)
- min_refit_loss, max_refit_loss
- mean_fresh_loss (Mittelwert des direkten Discovery auf Testtrajektorien)

**`generalization_detail.csv`** — eine Zeile pro (system, variant, seed, test_param_set):
- system_name, variant, seed, param_set_id (1–4)
- train_loss
- refit_loss (Refit mit fixierter Struktur)
- fresh_loss (direkte Discovery auf Testtrajektorie)
- refit_success (bool: refit_loss < 10 * train_loss, als einfache Heuristik)

Beide Dateien: Komma-separiert, Header in erster Zeile, leerer String für fehlende Werte.
Beide Dateien: vollständig überschrieben bei jedem Aufruf.
Logs: für jeden Discovery-Run ein Log in `debug_results/gen_<system>_<variant>_seed<N>_train.log`,
für jeden Fresh-Discovery-Run `gen_<system>_<variant>_seed<N>_test<M>.log`.

---

### Schritt 6: Stdout-Report

Am Ende:

```
=== Generalization Study ===
System: <name>
  Variant: <slug> | Seed: <N>
    train_loss:       <val>
    mean_refit_loss:  <val>
    mean_fresh_loss:  <val>
    refit_success:    <k>/4
  ...
```

---

## Was sich nicht ändern darf

- Alles in `src/`
- `experiments/`
- `benchmarks/`
- Alle bestehenden Ergebnis-Dateien

Das Skript schreibt ausschließlich in `debug_results/`.

---

## Abschlussbedingung

Codex führt aus:
```
julia generalization_study.jl
```

Und prüft danach:

1. `debug_results/generalization_summary.csv` existiert mit korrekter Zeilenanzahl.
   Erwartete Zeilen: 3 Systeme × 2 Varianten × 3 Seeds = 18 Datenzeilen + Header.
2. `debug_results/generalization_detail.csv` existiert.
   Erwartete Zeilen: 18 × 4 Testparametersätze = 72 Datenzeilen + Header.
3. Kein Run fehlt — auch fehlgeschlagene Runs haben eine Zeile.
4. refit_loss und fresh_loss sind beide vorhanden und sinnvoll (nicht alle NaN).
5. Der Stdout-Report erscheint vollständig.
