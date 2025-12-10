# src/structure.jl

############################
# Basisfunktionen & Struktur
############################

"""
Eine Basisfunktion ϕ(u, t), z.B. u₁, u₂, u₁², u₁*u₂, ...
"""
struct BasisTerm
    name::String
    func::Function   # (u, t) -> Float64
end

const BasisLibrary = Vector{BasisTerm}

"""
StructureSpec beschreibt, welche Basis-Terme in welcher Gleichung aktiv sind.

active_idxs[k] = Vektor von Indizes in der BasisLibrary
                 für die k-te Zustandsgleichung.
"""
struct StructureSpec
    active_idxs::Vector{Vector{Int}}  # Länge = dim, jede Komponente: Indizes
end

"""
    default_basis_library(dim)

Erzeugt eine einfache Basisbibliothek für `dim`-dimensionale Systeme.
Für dim=2 z.B.:

  u1, u2, u1^2, u2^2, u1*u2
"""
function default_basis_library(dim::Int)::BasisLibrary
    terms = BasisLibrary()

    # lineare Terme u_i
    for i in 1:dim
        push!(terms, BasisTerm("u$i", (u, t) -> u[i]))
    end

    # quadratische Terme u_i^2
    for i in 1:dim
        push!(terms, BasisTerm("u$i^2", (u, t) -> u[i]^2))
    end

    # Kreuzterm u1*u2 für dim >= 2
    if dim >= 2
        push!(terms, BasisTerm("u1*u2", (u, t) -> u[1] * u[2]))
    end

    return terms
end

"""
    build_model(structure, basis) -> (f!, n_params)

Erzeugt eine ODE-Funktion f!(du, u, p, t) basierend auf der Struktur.

du[k] = Σ_j p[idx] * ϕ_j(u, t)
  über alle ϕ_j, die in active_idxs[k] stehen.
"""
function build_model(structure::StructureSpec, basis::BasisLibrary)
    # Gesamtzahl der Parameter = Summe aller aktiven Terme
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

"""
Erzeugt eine zufällige Struktur:
für jede Gleichung werden zwischen 1 und max_terms_per_eq Basisfunktionen
zufällig ausgewählt.
"""
function random_structure(dim::Int, basis::BasisLibrary, max_terms_per_eq::Int)
    active = Vector{Vector{Int}}(undef, dim)
    n_basis = length(basis)

    for k in 1:dim
        n_terms = rand(1:max_terms_per_eq)
        active[k] = sort(unique(rand(1:n_basis, n_terms)))
    end

    return StructureSpec(active)
end

############################
# Individuals & EvoGrow
############################

"""
Ein Individuum in der Population:

- structure: welche Basisfunktionen in welcher Gleichung aktiv sind
- params: gefittete Parameter
- loss: Daten-Fit (MSE)
- objective: loss + λ * (#Parameter) oder ähnliches
"""
mutable struct Individual
    structure::StructureSpec
    params::Vector{Float64}
    loss::Float64
    objective::Float64
end

abstract type AbstractSearchStrategy end

"""
EvoGrow-Strategie:

- pop_size: Größe der Population
- n_levels: Anzahl Wachstumsstufen
- children_per_parent: wie viele Kinder pro Eltern-Individuum
- max_terms_per_eq: maximale Anzahl aktiver Basisfunktionen pro Gleichung
- λ: Regularisierung für Komplexität (z.B. J = loss + λ * n_params)
"""
struct EvoGrow <: AbstractSearchStrategy
    pop_size::Int
    n_levels::Int
    children_per_parent::Int
    max_terms_per_eq::Int
    λ::Float64
end

"""
Initialisiert eine Population sehr einfacher Modelle.
Hier: jede Gleichung hat genau 1 Basisfunktion.
"""
function init_population(strategy::EvoGrow,
                         dim::Int,
                         basis::BasisLibrary)::Vector{Individual}
    pop = Vector{Individual}()
    for _ in 1:strategy.pop_size
        # Jede Gleichung: 1 zufälliger Term
        active = Vector{Vector{Int}}(undef, dim)
        n_basis = length(basis)
        for k in 1:dim
            active[k] = [rand(1:n_basis)]
        end
        structure = StructureSpec(active)
        push!(pop, Individual(structure, Float64[], Inf, Inf))
    end
    return pop
end

"""
Bewertet ein Individuum:
- baut aus der Struktur ein Modell
- fitten Parameter
- setzt loss und objective = loss + λ * (#Parameter)
"""
function evaluate!(ind::Individual,
                   basis::BasisLibrary,
                   traj::Trajectory;
                   λ::Float64,
                   maxiters::Int)

    f!, n_params = build_model(ind.structure, basis)
    res = fit_parameters(f!, traj, n_params; maxiters = maxiters)

    ind.params    = res.p
    ind.loss      = res.loss
    ind.objective = res.loss + λ * length(res.p)

    return ind
end

"""
Erzeugt Kinder, indem für eine Gleichung ein zusätzlicher Term hinzugefügt wird
(sofern noch Platz ist und es noch ungenutzte Basisfunktionen gibt).
"""
function expand(ind::Individual,
                basis::BasisLibrary;
                n_children::Int,
                max_terms_per_eq::Int)

    children = Individual[]
    dim = length(ind.structure.active_idxs)
    n_basis = length(basis)

    for _ in 1:n_children
        # Struktur kopieren
        new_idxs = [copy(v) for v in ind.structure.active_idxs]

        # zufällige Gleichung wählen
        k = rand(1:dim)

        existing = new_idxs[k]
        candidates = setdiff(1:n_basis, existing)

        if !isempty(candidates) && length(existing) < max_terms_per_eq
            j = rand(candidates)
            push!(new_idxs[k], j)
        end

        new_struct = StructureSpec(new_idxs)
        push!(children, Individual(new_struct, Float64[], Inf, Inf))
    end

    return children
end

"""
    search_structure(strategy::EvoGrow, traj, basis; maxiters=300)

EvoGrow-Hauptloop:

- Initialpopulation einfacher Modelle
- L Level von:
    - Eltern evaluieren
    - Kinder (=erweiterte Strukturen) erzeugen
    - Kinder evaluieren
    - Eltern+Kinder sortieren und beste pop_size behalten
- Gibt bestes Modell (Struktur + Params) zurück.
"""

function search_structure(strategy::EvoGrow,
                          traj::Trajectory,
                          basis::BasisLibrary;
                          maxiters::Int = 300)

    dim = size(traj.x, 2)
    pop = init_population(strategy, dim, basis)

    prev_best_J = Inf

    for level in 1:strategy.n_levels
        println("\nLevel $level")

        # Eltern evaluieren
        for ind in pop
            if !isfinite(ind.objective)
                evaluate!(ind, basis, traj; λ = strategy.λ, maxiters = maxiters)
            end
        end

        # Kinder erzeugen
        children = Individual[]
        for ind in pop
            append!(children,
                    expand(ind, basis;
                           n_children = strategy.children_per_parent,
                           max_terms_per_eq = strategy.max_terms_per_eq))
        end

        # Kinder evaluieren
        for child in children
            evaluate!(child, basis, traj; λ = strategy.λ, maxiters = maxiters)
        end

        # Selektion
        all_inds = vcat(pop, children)
        sort!(all_inds, by = ind -> ind.objective)
        pop = all_inds[1:strategy.pop_size]

        # ---- Logging BESTES MODELL DIESES LEVELS ----
        best = pop[1]
        println("  Best J: ", best.objective,
                " | loss=", best.loss,
                " | n_params=", length(best.params))

        println("  Struktur:")
        p = best.params
        idx = 1
        for eq_index in 1:length(best.structure.active_idxs)
            active_terms = best.structure.active_idxs[eq_index]
            terms_with_params = String[]
            for term_idx in active_terms
                coef = p[idx]
                name = basis[term_idx].name
                push!(terms_with_params, "($(round(coef, digits=4)))*$name")
                idx += 1
            end
            println("    du_$eq_index = " * join(terms_with_params, " + "))
        end

        # ---- EARLY STOPPING ----
        # 1) Perfekter Fit: loss extrem klein
        if best.loss < 1e-8
            println("  -> Loss < 1e-8, Modell ist 'perfekt genug'. Stoppe EvoGrow nach Level $level.")
            break
        end

        # 2) Kaum Verbesserung in J gegenüber vorherigem Level
        improvement = prev_best_J - best.objective
        if prev_best_J < Inf && improvement < 1e-4
            println("  -> Keine signifikante Verbesserung (ΔJ = $(round(improvement, digits=6))). Stoppe nach Level $level.")
            break
        end

        prev_best_J = best.objective
    end

    best = pop[1]
    return (structure = best.structure,
            params    = best.params,
            loss      = best.loss,
            objective = best.objective,
            basis     = basis)
end
