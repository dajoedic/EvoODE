# EvoODE – Evolutionary Discovery of ODE Systems (Julia)

`EvoODE` ist ein Julia-Package für die datengetriebene Identifikation
von Differentialgleichungen.  
Der Algorithmus kombiniert:

- **Struktursuche** (z. B. evolutionär, populationsbasiert)
- **Parameteroptimierung** (mittels `DifferentialEquations.jl` + `Optimization.jl`)
- **Flexible ODE-Modelle** (later: Basisfunktionen, Masken, Symbolik)

Das Projekt befindet sich aktuell im **MVP-Prototyp-Stadium**:
Wir laden reale ODE-Systeme aus der *Strogatz*-Datenbank
und fitten einfache Modellstrukturen.

---

## 🚀 Projektstruktur

```
EvoODE/
 ├── Project.toml
 ├── Manifest.toml
 ├── README.md
 ├── src/
 │     ├── EvoODE.jl
 │     ├── data.jl
 │     ├── model.jl
 │     ├── loss.jl
 │     ├── optimize.jl
 │     └── utils.jl
 ├── data/
 │     └── strogatz_extended.json
 └── main_mvp.jl
```

---

## 🧩 Installation (lokale Entwicklung)

```bash
cd path/to/EvoODE
julia
```

```julia
using Pkg
Pkg.activate(".")
Pkg.instantiate()
```

Danach:

```julia
include("main_mvp.jl")
```

---

## 📦 Module Overview

### `Trajectory`

```julia
Trajectory(t::Vector{Float64}, x::Matrix{Float64})
```

---

### `SystemData`

```julia
SystemData(id, eq, eq_description, dim, traj)
```

---

### Datensatz laden

```julia
systems = load_2d_systems("data/strogatz_extended.json"; n = 5)
```

---

### Einfaches Modell

```julia
f! = make_model()
```

---

### Parameter optimieren

```julia
result = fit_parameters(f!, traj; maxiters = 300)
result.p
result.loss
```

---

## 🚧 TODO / Roadmap

- [x] Daten laden
- [x] Einfaches Modell
- [x] Parameteroptimierung
- [ ] Struktursuche
- [ ] Evolutionärer Algorithmus
- [ ] Symbolische Ausgabe
- [ ] Benchmarking

---

## 📄 Lizenz

Noch offen.
