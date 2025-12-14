# EvoODE – Evolutionary ODE Discovery Prototype

EvoODE ist ein Julia-Prototyp für **Dynamikmodellierung und Strukturlernen** von gewöhnlichen Differentialgleichungen (ODEs) auf Basis von Zeitreihendaten.

Ziel:
- Gegebene Trajektoriendaten \(x(t)\) eines (klein)-dimensionalen dynamischen Systems,
- eine **Grammatik / Basisbibliothek** von möglichen rechten Seiten,
- und ein **evolutionärer, wachstumsbasierter Algorithmus (EvoGrow)**,  
  der schrittweise immer komplexere ODE-Strukturen erzeugt und bewertet.

Der Fokus liegt derzeit auf:
- 1D–3D Systemen (z.B. Strogatz- und Lotka–Volterra-Varianten, Pendel, Oszillator),
- **strukturierter Struktursuche** via EvoGrow,
- **Parameterfit** der gefundenen Strukturen mittels `DifferentialEquations.jl` + `Optimization.jl` (BFGS, FiniteDiff),
- verständlichen, leicht erweiterbaren Komponenten, die später in ein vollwertiges Julia-Package überführt werden können.

---

## Projektstruktur

```text
EvoODE/
├─ Project.toml          # Julia-Projekt, Dependencies
├─ Manifest.toml         # (optional) genaue Auflösung der Abhängigkeiten
├─ README.md             # Dieses Dokument
├─ data/
│   └─ strogatz_extended.json   # Beispiel-Systemsammlung (Strogatz + Erweiterungen)
├─ src/
│   ├─ EvoODE.jl         # Zentrales Modul: re-exportiert Untermodule / Funktionen
│   ├─ data.jl           # Laden & Vorverarbeiten der Systemdaten / Trajektorien
│   ├─ model.jl          # Modellbausteine: Basisfunktionen, Strukturrepräsentation, ODE-Funktionen
│   ├─ loss.jl           # Loss-Funktionen (z.B. MSE)
│   ├─ optimize.jl       # Parameterfit (BFGS + FiniteDiff, SciML-Stack)
│   └─ structure.jl      # Struktursuche-Strategien (RandomSearch, EvoGrow)
├─ main_structure.jl     # Struktursuche mit RandomSearch (Baseline)
└─ main_evogrow.jl       # Struktursuche mit EvoGrow (wachstumsbasiert)
```

---

## Abhängigkeiten

Die wichtigsten Julia-Packages (stehen alle in `Project.toml`):

- `DifferentialEquations.jl` – ODE-Löser
- `Optimization.jl` + `OptimizationOptimJL.jl` – Optimierung (BFGS, NelderMead, …)
- `DiffEqFlux.jl` (optional für spätere Erweiterungen / Neural ODEs)
- `JSON3.jl` – Laden der Systemdefinitionen und Trajektorien aus `strogatz_extended.json`
- `SciMLBase.jl`, `OrdinaryDiffEq.jl` – Teil des SciML-Stacks
- `Logging` – Log-Ausgaben / Warnungen im Code

---

## Installation & Setup

1. **Repository klonen** (oder lokal anlegen):

```bash
git clone <DEIN-REPO-URL> EvoODE
cd EvoODE
```

2. **Julia-Projekt aktivieren & Dependencies installieren**

Im Projekt-Root in die Julia-REPL gehen und:

```julia
using Pkg
Pkg.activate(".")
Pkg.instantiate()
```

Das installiert alle in `Project.toml` angegebenen Abhängigkeiten.

---

## Daten

Die Datei `data/strogatz_extended.json` enthält mehrere vordefinierte Systeme im „Strogatz-Stil“, z.B.:

- Harmonischer Oszillator (mit/ohne Dämpfung)
- Lotka–Volterra-Varianten
- Pendel
- weitere 2D-Systeme

Jedes System enthält:
- eine Beschreibung,
- die wahre ODE-Struktur (symbolisch),
- die Parameter,
- eine oder mehrere Trajektorien \((t, x(t))\).

Grob gesagt:  
`src/data.jl` lädt diese JSON-Definitionen, filtert je nach Dimension und System-ID, und baut daraus `Trajectory`-Objekte:

```julia
struct Trajectory
    t::Vector{Float64}
    x::Matrix{Float64}   # (T × dim)
end
```

---

## Kernkonzepte

### Basisbibliothek (implizite Grammatik)

In `src/structure.jl` existiert eine Funktion wie:

```julia
struct BasisTerm
    name::String
    func::Function   # (u, t) -> Float64
end

const BasisLibrary = Vector{BasisTerm}

function default_basis_library(dim::Int)::BasisLibrary
    terms = BasisLibrary()

    # Beispiel: lineare Terme u_i
    for i in 1:dim
        push!(terms, BasisTerm("u$i", (u, t) -> u[i]))
    end

    # Beispiel: quadratische Terme u_i^2
    for i in 1:dim
        push!(terms, BasisTerm("u$i^2", (u, t) -> u[i]^2))
    end

    # Beispiel: ein Cross-Term
    if dim >= 2
        push!(terms, BasisTerm("u1*u2", (u, t) -> u[1] * u[2]))
    end

    return terms
end
```

Diese Basisbibliothek definiert das **Alphabet** der erlaubten Terme in den ODEs.  
Alle Nichtlinearitäten sind in diesen `BasisTerm`s kodiert.

---

### Strukturrepräsentation

Eine ODE-Struktur wird durch Index-Sets über der Basis beschrieben:

```julia
struct StructureSpec
    active_idxs::Vector{Vector{Int}}
end
```

- Länge von `active_idxs` = Dimension des Systems `dim`
- `active_idxs[k]` = Liste von Basis-Term-Indizes, die in Gleichung `du_k/dt` vorkommen.

Beispiel (2D):

```julia
active_idxs = [
    [2],        # du1/dt nutzt nur basis[2]
    [1, 3]      # du2/dt nutzt basis[1] und basis[3]
]
```

---

### Modellbau

Aus Struktur + Basisbibliothek wird eine `f!(du, u, p, t)`-Funktion gebaut:

```julia
function build_model(structure::StructureSpec, basis::BasisLibrary)
    n_params = sum(length(idxs) for idxs in structure.active_idxs)

    function f!(du, u, p, t)
        idx = 1
        for k in 1:length(structure.active_idxs)
            acc = 0.0
            for j in structure.active_idxs[k]
                acc += p[idx] * basis[j].func(u, t)
                idx += 1
            end
            du[k] = acc
        end
    end

    return f!, n_params
end
```

Die Form der Gleichungen ist damit:

\[
\dot u_k = \sum_i p_i \, \phi_i(u, t)
\]

wobei \(\phi_i\) aus der Basisbibliothek kommen.

---

### Parameterfit

In `src/optimize.jl` wird für eine gegebene Struktur:

1. eine `ODEProblem` mit freiem Parametervektor `p` aufgesetzt,
2. ein Prädiktor `predict(p)` via `solve` definiert,
3. ein Loss `loss(p)` (z.B. MSE über Trajektorie) gebildet,
4. per `Optimization.jl` + `OptimizationOptimJL.BFGS()` (mit numerischen Gradienten) minimiert.

Die finale Signatur sieht ungefähr so aus:

```julia
(p = p_best, loss = best_loss) = fit_parameters(f!, traj, n_params; maxiters = 300)
```

Dabei ist `fit_parameters` robust implementiert:
- ODE-Solve in `try/catch`,
- NaNs und Divergenzen werden auf großen Loss gemappt,
- `mse_loss` ist defensiv gegen NaNs / falsche Shapes.

---

### Struktursuche (RandomSearch & EvoGrow)

In `src/structure.jl` sind zwei zentrale Strategien definiert:

1. **RandomSearch** – simple Baseline:
   - Strukturen zufällig aus der Basisbibliothek ziehen,
   - Parameterfit je Modell,
   - bestes Modell nach Loss / regularisiertem Objective auswählen.

2. **EvoGrow** – wachstumsbasierter, populationsorientierter Ansatz:
   - Start mit sehr einfachen Strukturen (wenige Terme),
   - Population von Individuen (=Strukturen + Parameter + Objective),
   - iterativ:
     - Parameter neu fitten,
     - Kinder erzeugen, indem pro Gleichung ein neuer Basis-Term zugeschaltet wird,
     - Selektion nach Objective \(J = \text{Loss} + \lambda \cdot \#\text{Parameter}\),
     - Logging der jeweils besten Struktur pro Level (inkl. Parametern).

---

## Wie führe ich das Projekt aus?

### 1. Environment aktivieren

Im Projekt-Root:

```bash
cd EvoODE
julia --project=.
```

In der Julia-REPL:

```julia
using Pkg
Pkg.instantiate()   # nur beim ersten Mal nötig
```

Danach kannst du die Skripte direkt mit `include` starten.

---

### 2. Struktursuche EvoGrow: Wachstumsbasierter Ansatz

`main_evogrow.jl`:

- Lädt wieder ein System (z.B. harmonischer Oszillator),
- erzeugt eine Basisbibliothek passend zur Dimension,
- initialisiert eine Population sehr einfacher Strukturen,
- führt **EvoGrow** aus:

Pro Level wird ausgegeben:

```text
Level 1
  Best J: ...
  loss = ...
  n_params = ...
  Struktur:
    du_1 = (c1)*u2 + (c2)*u1
    du_2 = (c3)*u1
```

Bei gut eingestelltem Basisraum findet EvoGrow z.B. für den harmonischen Oszillator:

```text
du_1 = (≈1.0)*u2
du_2 = (≈-2.1)*u1
```

Ausführung:

```bash
julia --project=. main_evogrow.jl
```

oder:

```julia
julia> include("main_evogrow.jl")
```

---

## Typischer Workflow

1. **MVP checken**  
   `main_mvp.jl` laufen lassen und prüfen, ob Parameterfit auf den bekannten Systemen gut funktioniert.

2. **RandomSearch ausprobieren**  
   `main_structure.jl` nutzen, um ein Gefühl für:
   - Qualität des Basisraums,
   - Numerik,
   - Regularisierung \(J = \text{Loss} + \lambda\cdot \#\text{Parameter}\)
   zu bekommen.

3. **EvoGrow laufen lassen**  
   `main_evogrow.jl` für:
   - harmonischen Oszillator,
   - gedämpften Oszillator,
   - Lotka–Volterra,
   - Pendel (ggf. Basisraum anpassen, z.B. `sin(u1)` hinzufügen).

4. **Iterativ verfeinern**  
   - Basisbibliothek erweitern (z.B. Polynomgrad, trigonometrische Funktionen),
   - EvoGrow-Hyperparameter tunen (`pop_size`, `n_levels`, `children_per_parent`, `λ`),
   - später: explizite `Grammar`-Struktur, alternative Suchstrategien, Multi-Start, etc.

---

## Ausblick

Geplante / mögliche Erweiterungen:

- Explizite Grammatik (`Grammar`-Typ) mit:
  - polynomialen, trigonometrischen, rationalen Termfamilien,
  - Konfig für maximale Ordnung / Anzahl Terme.
- Mehrere Suchstrategien:
  - klassische GP (Baumrepräsentation),
  - kombinierte EvoGrow+Pruning,
  - Bayesian / MCMC-Elemente.
- Integration von `DiffEqFlux.jl`:
  - Neural ODEs als Basisfunktionen,
  - hybride symbolisch–neurale Modelle.
- Benchmarking:
  - ODEBench / Strogatz-Katalog / eigene Use-Cases aus dem PhD-Projekt.

---

Wenn du dieses Projekt in einer neuen Umgebung startest, reicht es in der Regel:

```bash
git clone <repo>
cd EvoODE
julia --project=.
julia> using Pkg; Pkg.instantiate()
julia> include("main_mvp.jl")       # Parameterfit
julia> include("main_evogrow.jl")   # Struktursuche
```

Viel Spaß beim „EvoODEn“ 🚀
